"""Check candidate serialization artifacts, never normalize or validate FIR semantics."""
import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import re
import struct

import rfc8785
from jsonschema import Draft7Validator

HERE = Path(__file__).resolve().parent
IMPLEMENTATIONS = {
    'external-python-rfc8785': 'review_p03.py',
    'independent-ecmascript-rfc8785': 'review_p03.cjs',
}
ARTIFACT_KEYS = ('input', 'canonical', 'normalized', 'model_canonical')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_artifact(directory, artifact):
    path = (directory / artifact['path']).resolve()
    if not path.is_relative_to(directory.resolve()):
        raise ValueError('Artifact path escapes catalog')
    raw = path.read_bytes()
    if sha(raw) != artifact['sha256']:
        raise ValueError('Artifact checksum mismatch: ' + artifact['path'])
    return raw


def load_catalog(directory):
    catalog = json.loads((directory / 'catalog.json').read_bytes())
    schema = json.loads((directory / 'catalog.schema.json').read_bytes())
    Draft7Validator.check_schema(schema)
    Draft7Validator(schema).validate(catalog)
    index = {c['id']: c for c in catalog['cases']}
    if len(index) != len(catalog['cases']):
        raise ValueError('Duplicate catalog IDs')
    for requirement, ids in catalog['coverage'].items():
        if not set(ids) <= index.keys():
            raise ValueError('Unknown coverage reference: ' + requirement)
        if not any(index[name]['stage'] != 'contract_only' for name in ids):
            raise ValueError('Coverage requires executable cases: ' + requirement)
    referenced = set()
    for case in catalog['cases']:
        for key in ARTIFACT_KEYS:
            if key in case:
                read_artifact(directory, case[key])
                referenced.add(case[key]['path'])
    physical = {p.relative_to(directory).as_posix()
                for folder in ('inputs', 'expected')
                for p in (directory / folder).rglob('*') if p.is_file()}
    if referenced != physical:
        raise ValueError('Unreferenced or missing fixture artifacts')
    return catalog


def load_json(raw):
    return json.loads(raw, parse_int=float, parse_float=float)


def provenance(directory, implementation):
    return {
        'report_version': 1,
        'catalog_sha256': sha((directory / 'catalog.json').read_bytes()),
        'catalog_schema_sha256': sha((directory / 'catalog.schema.json').read_bytes()),
        'evaluator_sha256': sha((directory / IMPLEMENTATIONS[implementation]).read_bytes()),
        'fixture_status': 'REVIEW_REQUIRED',
        'implementation': implementation,
    }


def review(directory=HERE):
    catalog = load_catalog(directory)
    rows = []
    for case in catalog['cases']:
        data = read_artifact(directory, case['input'])
        row = {'id': case['id'], 'stage': case['stage'], 'serialization': 'NOT_RUN',
               'fir_validation_normalization': 'NOT_RUN'}
        if case['stage'] != 'contract_only':
            # Artifact integrity is not a serialization rejection. In particular,
            # malformed UTF-8 must not masquerade as nonfinite rejection.
            if case['stage'] == 'binary64_jcs' and data != case['binary64_bits'].encode('ascii'):
                raise ValueError('Bit-pattern input mismatch')
            model_bytes = None
            try:
                if case['stage'] == 'binary64_jcs':
                    value = struct.unpack('>d', bytes.fromhex(case['binary64_bits']))[0]
                elif case['stage'] == 'fir_identity':
                    value = {'domain': 'fenix.fir', 'canonicalization_version': '0.1.0',
                             'model': load_json(read_artifact(directory, case['normalized']))}
                    model_bytes = rfc8785.dumps(value['model'])
                    if model_bytes != read_artifact(directory, case['model_canonical']):
                        raise ValueError('Model bytes mismatch')
                else:
                    value = load_json(data)
                output = rfc8785.dumps(value)
            except (rfc8785.CanonicalizationError, UnicodeError):
                if case['expected_outcome'] != 'reject':
                    raise
                row['serialization'] = 'REJECT_CONFIRMED'
            else:
                if case['expected_outcome'] != 'accept' or output != read_artifact(directory, case['canonical']):
                    raise ValueError('Unexpected serialization: ' + case['id'])
                row.update(serialization='PASS', canonical_hex=output.hex(), canonical_sha256=sha(output))
                if model_bytes is not None:
                    row.update(model_canonical_hex=model_bytes.hex(), model_canonical_sha256=sha(model_bytes))
        rows.append(row)
    return dict(provenance(directory, 'external-python-rfc8785'),
                runtime={'name': platform.python_implementation(), 'version': platform.python_version(),
                         'serializer': 'rfc8785', 'serializer_version': version('rfc8785')}, cases=rows)


def validate_runtime(implementation, runtime):
    if not isinstance(runtime, dict):
        raise ValueError('Missing runtime identity')
    if implementation == 'external-python-rfc8785':
        if (set(runtime) != {'name', 'version', 'serializer', 'serializer_version'}
                or runtime.get('name') != 'CPython' or runtime.get('serializer') != 'rfc8785'
                or runtime.get('serializer_version') != version('rfc8785')):
            raise ValueError('Invalid Python runtime identity')
    else:
        if (set(runtime) != {'name', 'version', 'engine', 'engine_version', 'serializer'}
                or runtime.get('name') != 'node' or runtime.get('engine') != 'v8'
                or runtime.get('serializer') != 'ECMAScript JSON.stringify'
                or not isinstance(runtime.get('engine_version'), str)
                or not re.fullmatch(r'\d+\.\d+\.\d+(?:[.\w-]*)', runtime['engine_version'])):
            raise ValueError('Invalid ECMAScript runtime identity')
    if not isinstance(runtime.get('version'), str) or not re.fullmatch(r'\d+\.\d+\.\d+', runtime['version']):
        raise ValueError('Invalid runtime version')


def compare(reports, directory=HERE):
    # Recheck fixed artifacts. Mutual agreement alone is insufficient.
    if len(reports) != 2 or {r.get('implementation') for r in reports} != set(IMPLEMENTATIONS):
        raise ValueError('Exactly the known Python and ECMAScript implementations required')
    expected = review(directory)
    for report in reports:
        implementation = report['implementation']
        metadata = provenance(directory, implementation)
        if (type(report.get('report_version')) is not int
                or set(report) != set(metadata) | {'runtime', 'cases'}
                or any(report.get(k) != v for k, v in metadata.items())):
            raise ValueError('Stale or invalid report provenance')
        validate_runtime(implementation, report['runtime'])
        rows = report['cases']
        index = {r['id']: r for r in rows}
        if len(index) != len(rows) or set(index) != {r['id'] for r in expected['cases']}:
            raise ValueError('Incomplete or duplicate report cases')
        for row in expected['cases']:
            if index[row['id']] != row:
                raise ValueError('Report stage/outcome/bytes/digest mismatch: ' + row['id'])


def write_report(destination, report, directory=HERE):
    target = destination.resolve()
    protected = [directory / name for name in ('catalog.json', 'catalog.schema.json', *IMPLEMENTATIONS.values())]
    protected += [p for folder in ('inputs', 'expected') for p in (directory / folder).rglob('*') if p.is_file()]
    if (any(target.is_relative_to((directory / folder).resolve()) for folder in ('inputs', 'expected'))
            or any(target == p.resolve() or (target.exists() and target.samefile(p)) for p in protected)):
        raise ValueError('Report output would overwrite protected catalog/source/fixture path')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path)
    parser.add_argument('--compare', nargs=2, type=Path)
    args = parser.parse_args()
    if args.compare:
        compare([json.loads(p.read_text()) for p in args.compare])
        print('PASS: independent candidate serialization reports match; FIR validation/normalization NOT RUN.')
    else:
        report = review()
        if args.report:
            write_report(args.report, report)
        print(f"PASS: {len(report['cases'])} catalog entries inspected; FIR validation/normalization NOT RUN.")
