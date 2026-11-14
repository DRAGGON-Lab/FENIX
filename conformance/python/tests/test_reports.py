"""Fault injection: broken/incomplete reports must never count as parity."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from compare_reports import compare
from run_p01 import run


class TestReports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = run()

    def test_complete_report(self):
        self.assertEqual(compare(self.report, copy.deepcopy(self.report)), len(self.report['cases']))

    def test_missing_duplicate_and_wrong_catalog(self):
        for mutation in ('missing', 'duplicate', 'wrong catalog'):
            with self.subTest(mutation=mutation):
                other = copy.deepcopy(self.report)
                if mutation == 'missing':
                    other['cases'].pop()
                elif mutation == 'duplicate':
                    other['cases'].append(copy.deepcopy(other['cases'][0]))
                else:
                    other['catalog_sha256'] = '0' * 64
                with self.assertRaises(ValueError):
                    compare(self.report, other)

    def test_agreeing_wrong_categories_are_not_success(self):
        # Agreement alone is insufficient: both must match independent expectations.
        other = copy.deepcopy(self.report)
        rejection = next(c for c in other['cases'] if c['observed']['outcome'] == 'reject')
        rejection['observed']['category'] = 'INCORRECT'
        with self.assertRaises(ValueError):
            compare(other, copy.deepcopy(other))

    def test_failure_cannot_be_hidden_in_summary(self):
        other = copy.deepcopy(self.report)
        other['cases'][0]['passed'] = False
        with self.assertRaises(ValueError):
            compare(self.report, other)

    def test_boolean_flags_and_status_are_not_coerced(self):
        for mutation in ('summary', 'case', 'status'):
            with self.subTest(mutation=mutation):
                other = copy.deepcopy(self.report)
                if mutation == 'summary':
                    other['passed'] = 'false'
                elif mutation == 'case':
                    other['cases'][0]['passed'] = 'false'
                else:
                    other['fixture_status'] = 'APPROVED'
                with self.assertRaises(ValueError):
                    compare(self.report, other)
