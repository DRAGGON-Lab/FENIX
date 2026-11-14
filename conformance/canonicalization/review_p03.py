"""Check candidate serialization artifacts, never normalize or validate FIR semantics."""
import argparse
import hashlib
import json
from pathlib import Path

import rfc8785
from jsonschema import Draft7Validator

HERE = Path(__file__).resolve().parent


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


def load_json(raw):
    return json.loads(raw, parse_int=float, parse_float=float)


def review(directory=HERE):
    raw = (directory / 'catalog.json').read_bytes()
    catalog = json.loads(raw)
    schema = json.loads((directory / 'catalog.schema.json').read_text())
    Draft7Validator.check_schema(schema)
    Draft7Validator(schema).validate(catalog)
    if len({c['id'] for c in catalog['cases']}) != len(catalog['cases']):
        raise ValueError('Duplicate catalog IDs')
    rows = []
    for case in catalog['cases']:
        data = read_artifact(directory, case['input'])
        for key in ('canonical', 'normalized', 'model_canonical'):
            if key in case:
                read_artifact(directory, case[key])
        row = {'id': case['id'], 'serialization': 'NOT_RUN', 'fir_validation_normalization': 'NOT_RUN'}
        if case['stage'] != 'contract_only':
            try:
                if case['stage'] == 'binary64_jcs':
                    import struct
                    if data.decode() != case['binary64_bits']:
                        raise ValueError('Bit-pattern input mismatch')
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
                row.update(serialization='PASS', canonical_sha256=sha(output))
        rows.append(row)
    return {'catalog_sha256': sha(raw), 'fixture_status': catalog['status'],
            'implementation': 'external-python-rfc8785', 'cases': rows}


def compare(reports, directory=HERE):
    # Validate artifacts afresh, then require both reports to match all expected
    # statuses and digests; mutual agreement alone is insufficient.
    expected = review(directory)
    for report in reports:
        if report.get('catalog_sha256') != expected['catalog_sha256'] or report.get('fixture_status') != 'REVIEW_REQUIRED':
            raise ValueError('Stale catalog report')
        rows = report['cases']
        index = {r['id']: r for r in rows}
        if len(index) != len(rows) or set(index) != {r['id'] for r in expected['cases']}:
            raise ValueError('Incomplete or duplicate report cases')
        for row in expected['cases']:
            if index[row['id']] != row:
                raise ValueError('Report outcome/digest mismatch: ' + row['id'])
    if len({r['implementation'] for r in reports}) != 2:
        raise ValueError('Two distinct reference implementations required')


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
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, indent=2) + '\n')
        print(f"PASS: {len(report['cases'])} catalog entries inspected; FIR validation/normalization NOT RUN.")
