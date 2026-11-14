"""Read-only reconstruction of candidate preparation using exact rational arithmetic.

No FENIX/evaluator imports, transcendental functions or expectation-writing path.
The 401-term recurrence is the historical scratch calculation; exact rounding of
its enclosure replaces the scratch calculation's finite-precision decimal step.
"""
import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import sys

import jsonschema

ROOT = Path(__file__).resolve().parent


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def decode(bits):
    if not isinstance(bits, str) or re.fullmatch('[0-9a-f]{16}', bits) is None:
        raise ValueError('invalid binary64 encoding')
    value = struct.unpack('>d', bytes.fromhex(bits))[0]
    if not math.isfinite(value) or value < 0:
        raise ValueError('expected finite nonnegative input')
    return Fraction.from_float(value)


def enclosure(alpha, beta, x0, time):
    """Enclose the solution by the first omitted alternating Taylor term."""
    if min(alpha, beta, x0, time) < 0:
        raise ValueError('expected nonnegative input')
    z = beta * time
    factor = (alpha - beta * x0) * time
    if z >= 11 or abs(factor) >= 20000:
        raise ValueError('unsupported audit domain: require beta*t < 11 and |(alpha-beta*x0)*t| < 20000')
    term = total = Fraction(1)
    for n in range(1, 401):
        term *= -z / (n + 1)
        total += term
    center = x0 + factor * total
    # n=401 is omitted, with factorial denominator 402!. The subsequent
    # absolute term ratios are <= z/403 < 1, proving the alternating-tail bound.
    radius = abs(factor * term * z / 402)
    return center - radius, center + radius


def round_significant(value, digits):
    """Round an exact rational half-even, including ties and decade carries."""
    if value == 0:
        return Fraction(0)
    sign = -1 if value < 0 else 1
    value = abs(value)
    n, d = value.numerator, value.denominator
    # Estimate using bit lengths, then correct by exact comparisons. Avoid
    # converting enormous rational numerator/denominator integers to strings.
    k = (n.bit_length() - d.bit_length()) * 30103 // 100000
    while value < Fraction(10)**k:
        k -= 1
    while value >= Fraction(10)**(k + 1):
        k += 1
    quantum = Fraction(10)**(k - digits + 1)
    scaled = value / quantum
    q, remainder = divmod(scaled.numerator, scaled.denominator)
    if 2 * remainder > scaled.denominator or (2 * remainder == scaled.denominator and q % 2):
        q += 1
    return sign * q * quantum


def audit_catalog(path):
    raw = Path(path).read_bytes()
    catalog = json.loads(raw, object_pairs_hook=unique_object)
    schema = json.loads((ROOT / 'catalog.schema.json').read_text())
    try:
        jsonschema.Draft202012Validator(schema).validate(catalog)
    except jsonschema.ValidationError as exc:
        location = '/' + '/'.join(map(str, exc.absolute_path))
        raise ValueError(f'invalid catalog at {location}: {exc.message}') from exc
    seen_cases = set()
    results = []
    for case in catalog['cases']:
        cid = case['id']
        if cid in seen_cases:
            raise ValueError(f'{cid}: duplicate case ID')
        seen_cases.add(cid)
        seen_times = set()
        for sample in case['samples']:
            identity = f"{cid}/{sample['time_bits']}"
            try:
                a, b, x = [decode(case['parameters'][key]) for key in ('alpha', 'beta', 'x0')]
                t = decode(sample['time_bits'])
                if t in seen_times:
                    raise ValueError('duplicate numerical sample time')
                seen_times.add(t)
                lo, hi = enclosure(a, b, x, t)
                expected = Fraction(sample['expected'])
                if not round_significant(lo, 50) == expected == round_significant(hi, 50):
                    raise ValueError('enclosure does not round to fixed expectation')
            except ValueError as exc:
                raise ValueError(f'{identity}: {exc}') from exc
            results.append(identity)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=ROOT / 'catalog.json')
    args = parser.parse_args()
    try:
        results = audit_catalog(args.catalog)
        for identity in results:
            print(f'PASS: {identity}')
        print(f'PASS: {len(results)} samples; catalog_sha256={hashlib.sha256(args.catalog.read_bytes()).hexdigest()}; REVIEW_REQUIRED')
    except (ValueError, OSError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
