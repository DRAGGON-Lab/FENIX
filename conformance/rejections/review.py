"""Versioned rejection evidence and fail-closed cross-language comparison."""
import argparse
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import re
import sys
import tomllib

from reference import HERE, ROOT, load_catalog, observe, p01, sha

IMPLEMENTATIONS = {
    'independent-python-rejection-reference': [
        'conformance/rejections/reference.py', 'conformance/rejections/review.py', 'conformance/python/p01.py'],
    'independent-julia-rejection-reference': [
        'conformance/rejections/reference.jl', 'conformance/rejections/review.jl', 'conformance/julia/p01.jl'],
}
CONTRACTS = ['spec/bioir/proposals/ADR-P01.md', 'spec/fir/proposals/ADR-P02.md',
             'spec/canonicalization/proposals/ADR-P03.md']
SCHEMAS = ['spec/bioir/proposals/bioir-m0.schema.json', 'spec/fir/proposals/fir-m0.schema.json']
DEPENDENCIES = ['packages/python/pyproject.toml', 'packages/python/uv.lock',
                'conformance/julia/Project.toml', 'conformance/julia/Manifest.toml']
HISTORICAL = ['conformance/bioir/catalog.json', 'conformance/canonicalization/catalog.json']


def fingerprints(paths):
    return {path: sha((ROOT / path).read_bytes()) for path in paths}


def provenance(implementation):
    if implementation not in IMPLEMENTATIONS:
        raise ValueError('Unregistered implementation')
    return {
        'report_version': 1, 'implementation': implementation,
        'catalog_sha256': sha((HERE/'catalog.json').read_bytes()),
        'catalog_schema_sha256': sha((HERE/'catalog.schema.json').read_bytes()),
        'fixture_status': 'REVIEW_REQUIRED', 'catalog_version': '1.0.0',
        'evaluator_fingerprints': fingerprints(IMPLEMENTATIONS[implementation]),
        'schema_fingerprints': fingerprints(SCHEMAS),
        'contract_fingerprints': fingerprints(CONTRACTS),
        'dependency_fingerprints': fingerprints(DEPENDENCIES),
        'historical_catalog_fingerprints': fingerprints(HISTORICAL),
    }


def run():
    catalog = load_catalog()
    rows = []
    for case in catalog['cases']:
        observed = observe(case)
        rows.append({'id': case['id'], 'observed': observed, 'passed': observed == case['expected']})
    return dict(provenance('independent-python-rejection-reference'),
                runtime={'name': platform.python_implementation(), 'version': platform.python_version(),
                         'dependencies': {key: version(key) for key in ('jsonschema', 'rfc8785')}},
                passed=all(row['passed'] for row in rows), cases=rows)


def validate_runtime(implementation, runtime):
    if not isinstance(runtime, dict) or set(runtime) != {'name', 'version', 'dependencies'}:
        raise ValueError('Invalid runtime identity')
    if implementation == 'independent-python-rejection-reference':
        lock = tomllib.loads((ROOT/'packages/python/uv.lock').read_text())
        expected = {p['name']: p['version'] for p in lock['package'] if p['name'] in ('jsonschema', 'rfc8785')}
        name, pattern = 'CPython', r'3\.12\.\d+'
    else:
        manifest = tomllib.loads((ROOT/'conformance/julia/Manifest.toml').read_text())
        expected = {key: manifest['deps'][key][0]['version'] for key in ('JSON', 'JSONSchema')}
        name, pattern = 'julia', r'1\.10\.13'
    if (runtime['name'] != name or not isinstance(runtime['version'], str)
            or re.fullmatch(pattern, runtime['version']) is None or runtime['dependencies'] != expected):
        raise ValueError('Invalid runtime/dependency identity')


def compare(python, julia):
    catalog = load_catalog()
    if any(type(report.get('report_version')) is not int for report in (python, julia)):
        raise ValueError('Invalid report version type')
    expected = {c['id']: c['expected'] for c in catalog['cases']}
    for report, implementation in zip((python, julia), IMPLEMENTATIONS):
        for key, value in provenance(implementation).items():
            if report.get(key) != value:
                raise ValueError('Stale or invalid report provenance: ' + key)
        validate_runtime(implementation, report.get('runtime'))
        if report.get('passed') is not True or not isinstance(report.get('cases'), list):
            raise ValueError('Failing or missing report results')
        rows = report['cases']
        if (any(not isinstance(row, dict) or set(row) != {'id', 'passed', 'observed'} for row in rows)
                or any(not isinstance(row['id'], str) for row in rows)):
            raise ValueError('Invalid report row')
        indexed = {row['id']: row for row in rows}
        if len(indexed) != len(rows) or indexed.keys() != expected.keys():
            raise ValueError('Missing, duplicate or extra report cases')
        for id, fixed in expected.items():
            if indexed[id]['passed'] is not True or indexed[id]['observed'] != fixed:
                raise ValueError('Fixed expectation mismatch: ' + id)
    return len(expected)


def check_output(path):
    """Only artifacts/ or external reports; reject symlink and hardlink aliases."""
    target = Path(path).resolve()
    if target.is_relative_to(ROOT) and not target.is_relative_to(ROOT/'artifacts'):
        raise ValueError('Report would overwrite repository source')
    if target.exists():
        identity = (target.stat().st_dev, target.stat().st_ino)
        protected = set()
        ignored = {'.git', '.venv', 'venv', '__pycache__', 'artifacts', 'dist', 'build', '.julia', 'node_modules'}
        for folder, directories, files in os.walk(ROOT):
            directories[:] = [name for name in directories if name not in ignored]
            protected.update((Path(folder)/name).relative_to(ROOT).as_posix() for name in files)
        for relative in protected:
            stat = (ROOT/relative).stat()
            if identity == (stat.st_dev, stat.st_ino):
                raise ValueError('Report aliases a protected source, schema or fixture')
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--report', type=Path)
    mode.add_argument('--compare', nargs=2, type=Path, metavar=('PYTHON_REPORT', 'JULIA_REPORT'))
    args = parser.parse_args()
    if args.compare:
        reports = [p01.strict_parse(path.read_bytes()) for path in args.compare]
        count = compare(*reports)
        print(f'PASS: {count} fixed rejection-suite expectations matched by Python and Julia; PI acceptance pending.')
        return 0
    target = check_output(args.report) if args.report else None
    report = run()
    output = json.dumps(report, indent=2, sort_keys=True) + '\n'
    if target:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(output)
    else:
        print(output, end='')
    print(f"{len(report['cases'])} rejection-suite cases; passed={report['passed']}", file=sys.stderr)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
