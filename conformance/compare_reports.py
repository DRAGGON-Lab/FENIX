"""Compare independent reports with the checked-in catalog, never execute models."""
import argparse
import hashlib
import json
from pathlib import Path

DIRECTORY = Path(__file__).resolve().parent / 'bioir'


def compare(python, julia):
    catalog_bytes = (DIRECTORY / 'catalog.json').read_bytes()
    catalog = json.loads(catalog_bytes)
    digest = hashlib.sha256(catalog_bytes).hexdigest()
    expected = {case['id']: case for case in catalog['cases']}
    if len(expected) != len(catalog['cases']):
        raise ValueError('Duplicate catalog case IDs')
    indexed = []
    for report in (python, julia):
        if report.get('catalog_sha256') != digest:
            raise ValueError('Report was produced against different catalog bytes')
        if report.get('fixture_status') != catalog['status'] or report.get('catalog_version') != catalog['catalog_version']:
            raise ValueError('Report catalog status/version mismatch')
        if report.get('passed') is not True:
            raise ValueError('A native report contains failing cases')
        rows = {case['id']: case for case in report['cases']}
        if len(rows) != len(report['cases']) or rows.keys() != expected.keys():
            raise ValueError('Missing, duplicate or unexpected report cases')
        for id, case in expected.items():
            if rows[id]['passed'] is not True:
                raise ValueError(f'Failing case: {id}')
            for key in ('outcome', 'category', 'path', 'canonical_utf8'):
                if key in case['expected'] and rows[id]['observed'].get(key) != case['expected'][key]:
                    raise ValueError(f'Expected {key} mismatch: {id}')
        indexed.append(rows)
    for id in expected:
        for key in ('outcome', 'category', 'canonical_utf8'):
            if indexed[0][id]['observed'].get(key) != indexed[1][id]['observed'].get(key):
                raise ValueError(f'Cross-language {key} mismatch: {id}')
    return len(expected)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('python_report', type=Path)
    parser.add_argument('julia_report', type=Path)
    args = parser.parse_args()
    count = compare(json.loads(args.python_report.read_text()), json.loads(args.julia_report.read_text()))
    print(f'{count} candidate P01 fixtures matched independently in Python and Julia; fixture review remains required.')
