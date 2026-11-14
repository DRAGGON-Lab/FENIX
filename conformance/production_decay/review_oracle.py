"""Read-only analytical reference and report checker; independent of FENIX."""
from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_HALF_EVEN, localcontext, __libmpdec_version__
import hashlib
import json
import math
from pathlib import Path
import platform
import re
import struct
import sys

ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / 'catalog.json'
UNITS = {'alpha': 'molecule/s', 'beta': '1/s', 'x0': 'molecule',
         'time': 's', 'expected': 'molecule'}
IMPLEMENTATIONS = {
    'python-decimal': ((100, 200), 'decimal_digits', 'review_oracle.py'),
    'julia-bigfloat': ((512, 1024), 'bits', 'review_oracle.jl'),
}
EXPECTED = re.compile(r'(?:0|[1-9]\.[0-9]{49}E[+-][0-9]{1,4})\Z')
VALUE = re.compile(r'[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]{1,4})?\Z')


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=unique_object)


def fields(value, names, where):
    if not isinstance(value, dict) or set(value) != set(names):
        raise ValueError(f'{where}: expected fields {sorted(names)}')


def decode(bits: str) -> float:
    if not isinstance(bits, str) or re.fullmatch('[0-9a-f]{16}', bits) is None:
        raise ValueError(f'invalid binary64 encoding: {bits!r}')
    value = struct.unpack('>d', bytes.fromhex(bits))[0]
    if not math.isfinite(value) or value < 0:
        raise ValueError(f'expected finite nonnegative binary64: {bits}')
    return value


def load_catalog(path=CATALOG):
    catalog = read_json(path)
    fields(catalog, ('format', 'status', 'contract', 'units', 'cases'), 'catalog')
    if (catalog['format'] != 'production-decay-catalog-v1'
            or catalog['status'] not in ('REVIEW_REQUIRED', 'APPROVED')
            or catalog['contract'] != 'spec/fir/proposals/ADR-P02.md'
            or catalog['units'] != UNITS):
        raise ValueError('catalog format, review status, contract or units mismatch')
    if not isinstance(catalog['cases'], list) or not catalog['cases']:
        raise ValueError('catalog must contain cases')
    ids = set()
    for case in catalog['cases']:
        fields(case, ('id', 'rationale', 'parameters', 'samples'), 'case')
        cid = case['id']
        if not isinstance(cid, str) or re.fullmatch('[a-z][a-z0-9-]*', cid) is None or cid in ids:
            raise ValueError(f'invalid/duplicate case id: {cid!r}')
        ids.add(cid)
        if not isinstance(case['rationale'], str) or not case['rationale']:
            raise ValueError(f'{cid}: missing rationale')
        fields(case['parameters'], ('alpha', 'beta', 'x0'), cid)
        for value in case['parameters'].values():
            decode(value)
        if not isinstance(case['samples'], list) or not case['samples']:
            raise ValueError(f'{cid}: missing samples')
        times = set()
        for sample in case['samples']:
            fields(sample, ('time_bits', 'expected'), cid)
            t = decode(sample['time_bits'])
            if t in times:
                raise ValueError(f'{cid}: duplicate sample time')
            times.add(t)
            expected = sample['expected']
            if not isinstance(expected, str) or EXPECTED.fullmatch(expected) is None:
                raise ValueError(f'{cid}: expected 50-digit scientific decimal or explicit zero')
    return catalog


def evaluate(alpha: float, beta: float, x0: float, time: float, precision: int) -> Decimal:
    if any(not math.isfinite(v) or v < 0 for v in (alpha, beta, x0, time)):
        raise ValueError('evaluation requires finite nonnegative inputs')
    with localcontext() as ctx:
        ctx.prec = precision
        ctx.rounding = ROUND_HALF_EVEN
        a, b, x, t = map(Decimal.from_float, (alpha, beta, x0, time))
        if b == 0:
            return x + a * t
        exponential = (-b * t).exp()
        return x * exponential + (a / b) * (1 - exponential)


def round_significant(value: Decimal, digits: int) -> Decimal:
    if not value.is_finite() or value < 0:
        raise ValueError('expected finite nonnegative decimal')
    if value == 0:
        return Decimal(0)
    with localcontext() as ctx:
        ctx.prec = digits
        ctx.rounding = ROUND_HALF_EVEN
        return +value


def samples(catalog):
    return {(c['id'], s['time_bits']): Decimal(s['expected'])
            for c in catalog['cases'] for s in c['samples']}


def make_report(catalog_path=CATALOG):
    catalog = load_catalog(catalog_path)
    rows = []
    for precision in IMPLEMENTATIONS['python-decimal'][0]:
        for case in catalog['cases']:
            a, b, x = [decode(case['parameters'][key]) for key in ('alpha', 'beta', 'x0')]
            for sample in case['samples']:
                value = evaluate(a, b, x, decode(sample['time_bits']), precision)
                rows.append({'case_id': case['id'], 'time_bits': sample['time_bits'],
                             'precision': precision, 'value': str(value) if value else '0'})
    report = {'format': 'production-decay-report-v1', 'implementation': 'python-decimal',
              'runtime': {'python': platform.python_version(),
                          'implementation': platform.python_implementation(),
                          'libmpdec': __libmpdec_version__},
              'catalog_sha256': sha256(Path(catalog_path)),
              'evaluator_sha256': sha256(Path(__file__)),
              'precision_unit': 'decimal_digits', 'rows': rows}
    validate_report(report, catalog_path)
    return report


def validate_report(report, catalog_path=CATALOG):
    catalog = load_catalog(catalog_path)
    fields(report, ('format', 'implementation', 'runtime', 'catalog_sha256',
                    'evaluator_sha256', 'precision_unit', 'rows'), 'report')
    implementation = report['implementation']
    if not isinstance(implementation, str) or implementation not in IMPLEMENTATIONS:
        raise ValueError('unknown report implementation')
    precisions, unit, source = IMPLEMENTATIONS[implementation]
    if (report['format'] != 'production-decay-report-v1'
            or report['catalog_sha256'] != sha256(Path(catalog_path))
            or report['evaluator_sha256'] != sha256(ROOT / source)
            or report['precision_unit'] != unit):
        raise ValueError('stale report or incorrect format/precision unit')
    runtime = report['runtime']
    runtime_keys = ('python', 'implementation', 'libmpdec') if implementation == 'python-decimal' else ('julia', 'mpfr')
    fields(runtime, runtime_keys, 'runtime')
    if any(not isinstance(v, str) or not v for v in runtime.values()):
        raise ValueError('missing runtime identity')
    expected = samples(catalog)
    required = {(cid, tm, p) for cid, tm in expected for p in precisions}
    observed = {}
    if not isinstance(report['rows'], list):
        raise ValueError('rows must be an array')
    for row in report['rows']:
        fields(row, ('case_id', 'time_bits', 'precision', 'value'), 'report row')
        if (not isinstance(row['case_id'], str) or not isinstance(row['time_bits'], str)
                or type(row['precision']) is not int):
            raise ValueError('invalid row identity or precision')
        key = (row['case_id'], row['time_bits'], row['precision'])
        if key not in required or key in observed:
            raise ValueError(f'extra, altered or duplicate report row: {key}')
        raw = row['value']
        if not isinstance(raw, str) or len(raw) > 4096 or VALUE.fullmatch(raw) is None:
            raise ValueError(f'{key}: value must be a finite nonnegative decimal string')
        value = Decimal(raw)
        if round_significant(value, 50) != expected[key[:2]]:
            raise ValueError(f'{key}: computation does not round to fixed expectation')
        observed[key] = value
    if set(observed) != required:
        raise ValueError('incomplete sample/precision coverage')
    for cid, tm in expected:
        if len({round_significant(observed[cid, tm, p], 70) for p in precisions}) != 1:
            raise ValueError(f'{cid}/{tm}: precision runs disagree at 70 digits')
    return observed


def compare_reports(python_report, julia_report, catalog_path=CATALOG):
    if (python_report.get('implementation') != 'python-decimal'
            or julia_report.get('implementation') != 'julia-bigfloat'):
        raise ValueError('comparison requires distinct Python and Julia implementations, in that order')
    py = validate_report(python_report, catalog_path)
    jl = validate_report(julia_report, catalog_path)
    residuals = []
    with localcontext() as ctx:
        ctx.prec = 400
        for cid, tm in samples(load_catalog(catalog_path)):
            values = [py[cid, tm, p] for p in (100, 200)] + [jl[cid, tm, p] for p in (512, 1024)]
            if len({round_significant(value, 70) for value in values}) != 1:
                raise ValueError(f'{cid}/{tm}: independent computations disagree at 70 digits')
            residuals.append(max(values) - min(values))
    return {'status': 'PASS', 'samples': len(residuals), 'computations': 4 * len(residuals),
            'agreement_significant_digits': 70,
            'max_absolute_spread_molecule': str(max(residuals)),
            'fixture_status': load_catalog(catalog_path)['status']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--report', type=Path)
    group.add_argument('--compare', nargs=2, type=Path, metavar=('PYTHON_REPORT', 'JULIA_REPORT'))
    args = parser.parse_args()
    try:
        if args.compare:
            print(json.dumps(compare_reports(*(read_json(p) for p in args.compare)), indent=2))
        else:
            if args.report.resolve() in {CATALOG, ROOT / 'catalog.schema.json', Path(__file__).resolve(), ROOT / 'review_oracle.jl'}:
                raise ValueError('report destination must not overwrite reference inputs or evaluators')
            report = make_report()
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
            print(f'PASS: {len(report["rows"])} computations; fixture_status={load_catalog()["status"]}')
    except (ValueError, OSError, ArithmeticError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
