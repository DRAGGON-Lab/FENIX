"""Run P01 reference fixtures and emit a deterministic machine-readable report."""
import argparse
import hashlib
import sys
import json
import struct
from pathlib import Path

from p01 import ROOT, Rejection, evaluate
from jsonschema import Draft7Validator
import rfc8785


def run():
    directory = ROOT / 'conformance/bioir'
    raw = (directory / 'catalog.json').read_bytes()
    catalog = json.loads(raw)
    Draft7Validator(json.loads((directory / 'catalog.schema.json').read_text())).validate(catalog)
    if len({case['id'] for case in catalog['cases']}) != len(catalog['cases']):
        raise ValueError('Duplicate catalog IDs')
    results = []
    for case in catalog['cases']:
        if hashlib.sha256((directory / case['input']).read_bytes()).hexdigest() != case['input_sha256']:
            raise ValueError('Fixture input checksum mismatch: ' + case['id'])
        expected = case['expected']
        checks = True
        try:
            value = evaluate(case, directory)
            observed = {'outcome': 'accept'}
            if 'value' in expected:
                checks = value == expected['value']
                if isinstance(expected['value'], bool):
                    checks = checks and isinstance(value, bool)
            if 'canonical_utf8' in expected:
                observed['canonical_utf8'] = rfc8785.dumps(value).decode('utf-8')
                checks = checks and observed['canonical_utf8'] == expected['canonical_utf8']
            if 'binary64_bits' in expected:
                checks = struct.pack('>d', float(value)).hex() == expected['binary64_bits']
        except Rejection as error:
            observed = {'outcome': 'reject', 'category': error.category, 'path': error.path}
        passed = checks and all(observed.get(k) == v for k, v in expected.items()
                                if k in ('outcome', 'category', 'path'))
        results.append({'id': case['id'], 'passed': passed, 'observed': observed})
    return {'catalog_sha256': hashlib.sha256(raw).hexdigest(), 'runtime': sys.version.split()[0], 'catalog_version': catalog['catalog_version'], 'fixture_status': catalog['status'],
            'implementation': 'independent-python-reference',
            'passed': all(item['passed'] for item in results), 'cases': results}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    report = run()
    text = json.dumps(report, indent=2, sort_keys=True) + '\n'
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text)
    else:
        print(text, end='')
    print(f"{len(report['cases'])} P01 reference cases; fixture_status={report['fixture_status']}; passed={report['passed']}", file=sys.stderr)
    raise SystemExit(0 if report['passed'] else 1)
