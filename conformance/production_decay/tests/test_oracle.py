"""Contract/invariant and evidence-corruption checks; no FENIX imports."""
import copy
from decimal import Decimal, localcontext
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
import jsonschema

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("oracle", ROOT / "review_oracle.py")
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)


def bits(value):
    return struct.pack(">d", value).hex()


def assert_monotonic(test, pairs, decreasing=False):
    values = [value for _, value in sorted(pairs, key=lambda pair: pair[0])]
    test.assertEqual(values, sorted(values, reverse=decreasing))


class OracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = oracle.load_catalog()
        cls.report = oracle.make_report()

    def test_complete_coverage_and_fixed_candidates(self):
        self.assertEqual(self.catalog['status'], 'APPROVED')
        jsonschema.Draft202012Validator.check_schema(oracle.read_json(ROOT / 'catalog.schema.json'))
        jsonschema.validate(self.catalog, oracle.read_json(ROOT / 'catalog.schema.json'))
        expected = {(c['id'], s['time_bits'], p)
                    for c in self.catalog['cases'] for s in c['samples']
                    for p in (100, 200)}
        rows = self.report['rows']
        self.assertEqual(len(rows), len(expected))
        self.assertEqual({(r['case_id'], r['time_bits'], r['precision'])
                          for r in rows}, expected)
        oracle.validate_report(self.report)

    def test_initial_zero_equilibrium_and_dyadic_linear_arithmetic(self):
        for precision in (100, 200):
            for case in self.catalog['cases']:
                a, b, x = [oracle.decode(case['parameters'][k])
                           for k in ('alpha', 'beta', 'x0')]
                self.assertEqual(oracle.evaluate(a, b, x, 0.0, precision),
                                 Decimal.from_float(x))
                for sample in case['samples']:
                    t = oracle.decode(sample['time_bits'])
                    value = oracle.evaluate(a, b, x, t, precision)
                    if a == 0 and x == 0:
                        self.assertEqual(value, 0)
                    if b > 0 and a == b * x:
                        self.assertEqual(value, Decimal.from_float(x))
                    if b == 0:
                        self.assertEqual(value, Decimal.from_float(x + a * t))

    def test_nonnegative_monotonic_and_equilibrium_bounds(self):
        for precision in (100, 200):
            with localcontext() as ctx:
                ctx.prec = precision
                for case in self.catalog['cases']:
                    original = copy.deepcopy(case['samples'])
                    for samples in (original, list(reversed(original)), original[1:] + original[:1]):
                        a, b, x = [oracle.decode(case['parameters'][k])
                                   for k in ('alpha', 'beta', 'x0')]
                        pairs = [(oracle.decode(s['time_bits']),
                                  oracle.evaluate(a, b, x, oracle.decode(s['time_bits']), precision))
                                 for s in samples]
                        values = [v for _, v in pairs]
                        self.assertTrue(all(v >= 0 for v in values))
                        q = Decimal.from_float(a) / Decimal.from_float(b) if b else None
                        increasing = not b or Decimal.from_float(x) <= q
                        assert_monotonic(self, pairs, decreasing=not increasing)
                        if b:
                            self.assertTrue(all(min(Decimal.from_float(x), q) <= v
                                                <= max(Decimal.from_float(x), q) for v in values))
                    self.assertEqual(case['samples'], original)

    def test_monotonic_check_rejects_wrong_time_value_association(self):
        with self.assertRaises(AssertionError):
            assert_monotonic(self, [(2, 1), (0, 0), (1, 2)])
        with self.assertRaises(AssertionError):
            assert_monotonic(self, [(2, 1), (0, 2), (1, 0)], decreasing=True)

    def test_small_decay_fixed_time_limit_and_bound(self):
        with localcontext() as ctx:
            ctx.prec = 200
            for t in (0.5, 1.0, 10.0):
                linear = Decimal('0.5') + 2 * Decimal.from_float(t)
                gaps = []
                for b in (2**-20, 2**-40):
                    gap = linear - oracle.evaluate(2.0, b, 0.5, t, 200)
                    bound = Decimal.from_float(b) * (Decimal('0.5') * Decimal.from_float(t)
                                                     + Decimal.from_float(t)**2)
                    self.assertGreater(gap, 0)
                    self.assertLessEqual(gap, bound)
                    gaps.append(gap)
                self.assertLess(gaps[1], gaps[0])

    def test_decimal_real_point_one_changes_reference(self):
        with localcontext() as ctx:
            ctx.prec = 200
            wrong = Decimal(100) * (1 - (-Decimal('0.1')).exp())
        case = next(c for c in self.catalog['cases'] if c['id'] == 'baseline-zero')
        sample = next(s for s in case['samples'] if s['time_bits'] == bits(1.0))
        self.assertNotEqual(oracle.round_significant(wrong, 50), Decimal(sample['expected']))
        broken = copy.deepcopy(self.report)
        for row in broken['rows']:
            if row['case_id'] == case['id'] and row['time_bits'] == sample['time_bits']:
                row['value'] = str(wrong)
        with self.assertRaises(ValueError):
            oracle.validate_report(broken)

    def test_half_even_significant_rounding(self):
        self.assertEqual(oracle.round_significant(Decimal('1.25'), 2), Decimal('1.2'))
        self.assertEqual(oracle.round_significant(Decimal('1.35'), 2), Decimal('1.4'))
        self.assertEqual(oracle.round_significant(Decimal('9.95'), 2), Decimal('10'))
        self.assertEqual(oracle.round_significant(Decimal('0'), 70), 0)

    def test_catalog_rejections(self):
        mutations = []
        for bad in ('x', '000000000000000', '3FB999999999999A',
                    bits(-1.0), bits(float('inf')), bits(float('nan'))):
            for field in ('alpha', 'beta', 'x0', 'time'):
                data = copy.deepcopy(self.catalog)
                target = data['cases'][0]
                if field == 'time':
                    target['samples'][0]['time_bits'] = bad
                else:
                    target['parameters'][field] = bad
                mutations.append(data)
        for bad in ('NaN', '-1', '1', '0.0', '1E+0', '1.234', '1e999999', 1):
            data = copy.deepcopy(self.catalog)
            data['cases'][0]['samples'][0]['expected'] = bad
            mutations.append(data)
        data = copy.deepcopy(self.catalog); data['units']['alpha'] = 'molecule/min'
        mutations.append(data)
        data = copy.deepcopy(self.catalog); data['cases'].append(copy.deepcopy(data['cases'][0]))
        mutations.append(data)
        data = copy.deepcopy(self.catalog); data['cases'][0]['samples'].append(copy.deepcopy(data['cases'][0]['samples'][0]))
        mutations.append(data)
        data = copy.deepcopy(self.catalog)
        duplicate_zero = copy.deepcopy(data['cases'][0]['samples'][0])
        duplicate_zero['time_bits'] = bits(-0.0)
        data['cases'][0]['samples'].append(duplicate_zero)
        mutations.append(data)
        data = copy.deepcopy(self.catalog); data['status'] = 'UNKNOWN'
        mutations.append(data)
        for index, data in enumerate(mutations):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 'catalog.json'; path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    oracle.load_catalog(path)

    def test_corrupt_expectation_is_not_rewritten(self):
        data = copy.deepcopy(self.catalog)
        data['cases'][0]['samples'][0]['expected'] = '1.' + '0'*49 + 'E+0'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'catalog.json'; path.write_text(json.dumps(data))
            before = path.read_bytes()
            with self.assertRaises(ValueError):
                oracle.make_report(path)
            self.assertEqual(path.read_bytes(), before)

    def test_report_rejections(self):
        mutations = []
        for key, value in (('catalog_sha256', '0'*64), ('evaluator_sha256', '0'*64),
                           ('precision_unit', 'bits'), ('implementation', 'other'),
                           ('runtime', {})):
            data = copy.deepcopy(self.report); data[key] = value; mutations.append(data)
        data = copy.deepcopy(self.report); data['rows'].pop(); mutations.append(data)
        data = copy.deepcopy(self.report); data['rows'].append(copy.deepcopy(data['rows'][0])); mutations.append(data)
        data = copy.deepcopy(self.report); data['rows'] = [r for r in data['rows'] if r['precision'] == 200]; mutations.append(data)
        for key, value in (('value', '1'), ('value', 'NaN'), ('value', '-1'),
                           ('value', 0), ('case_id', 'unknown'), ('precision', 512),
                           ('time_bits', bits(3.0))):
            data = copy.deepcopy(self.report); data['rows'][0][key] = value; mutations.append(data)
        for index, data in enumerate(mutations):
            with self.subTest(index=index), self.assertRaises(ValueError):
                oracle.validate_report(data)
        with self.assertRaises(ValueError):
            oracle.compare_reports(self.report, self.report)

    def transport_julia_report(self):
        # Synthetic transport fixture only; real Julia arithmetic is run separately.
        report = copy.deepcopy(self.report)
        report.update(implementation='julia-bigfloat', precision_unit='bits',
                      evaluator_sha256=oracle.sha256(ROOT / 'review_oracle.jl'),
                      runtime={'julia': 'test-transport', 'mpfr': 'test-transport'})
        for row in report['rows']:
            row['precision'] = {100: 512, 200: 1024}[row['precision']]
        return report

    def test_comparison_complete_coverage_and_precision_disagreement(self):
        julia = self.transport_julia_report()
        result = oracle.compare_reports(self.report, julia)
        count = sum(len(c['samples']) for c in self.catalog['cases'])
        self.assertEqual(result['samples'], count)
        self.assertEqual(result['computations'], 4 * count)
        mutations = []
        data = copy.deepcopy(julia); data['rows'].pop(); mutations.append(data)
        data = copy.deepcopy(julia); data['rows'].append(copy.deepcopy(data['rows'][0])); mutations.append(data)
        data = copy.deepcopy(julia); data['rows'] = [r for r in data['rows'] if r['precision'] == 1024]; mutations.append(data)
        data = copy.deepcopy(julia); data['catalog_sha256'] = '0'*64; mutations.append(data)
        # This changes the 61st digit but preserves every published expectation.
        data = copy.deepcopy(julia)
        with localcontext() as ctx:
            ctx.prec = 400
            for row in data['rows']:
                if row['case_id'] == 'baseline-zero' and row['time_bits'] == bits(1.0):
                    row['value'] = str(Decimal(row['value']) + Decimal('1e-60'))
        oracle.validate_report(data)  # Within-language stability and 50 digits still pass.
        mutations.append(data)
        data = copy.deepcopy(data)
        data['rows'][1]['value'] = julia['rows'][1]['value']
        with self.assertRaises(ValueError):
            oracle.validate_report(data)  # A single precision alteration must also fail.
        for index, data in enumerate(mutations):
            with self.subTest(index=index), self.assertRaises(ValueError):
                oracle.compare_reports(self.report, data)
        # Order of rows has no mathematical meaning.
        shuffled = copy.deepcopy(julia); shuffled['rows'].reverse()
        self.assertEqual(oracle.compare_reports(self.report, shuffled), result)

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'catalog.json'
            path.write_text('{"cases":[],"cases":[]}')
            with self.assertRaises(ValueError):
                oracle.load_catalog(path)


if __name__ == '__main__':
    unittest.main()
