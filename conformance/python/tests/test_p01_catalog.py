"""Candidate expectations independently authored from P01, not validator output."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_p01 import run


class TestP01Catalog(unittest.TestCase):
    def test_catalog(self):
        report = run()
        for case in report['cases']:
            with self.subTest(case=case['id']):
                self.assertTrue(case['passed'], case['observed'])
