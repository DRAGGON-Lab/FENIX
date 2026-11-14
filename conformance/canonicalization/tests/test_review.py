"""Evidence failures must not become apparent conformance successes."""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from review_p03 import HERE, compare, read_artifact, review


class EvidenceTests(unittest.TestCase):
    def test_rejects_missing_duplicate_and_false_success_reports(self):
        expected = review()
        other = copy.deepcopy(expected)
        other['implementation'] = 'independent-test-report'
        compare([expected, other])
        for mutation in ('missing', 'duplicate', 'false-normalization', 'wrong-digest', 'stale'):
            bad = copy.deepcopy(other)
            if mutation == 'missing': bad['cases'].pop()
            elif mutation == 'duplicate': bad['cases'].append(bad['cases'][0])
            elif mutation == 'false-normalization': bad['cases'][0]['fir_validation_normalization'] = 'PASS'
            elif mutation == 'wrong-digest': bad['cases'][0]['canonical_sha256'] = '0' * 64
            else: bad['catalog_sha256'] = '0' * 64
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                compare([expected, bad])

    def test_checksum_and_path_failures(self):
        catalog = json.loads((HERE / 'catalog.json').read_text())
        wrong = dict(catalog['cases'][0]['input'], sha256='0' * 64)
        with self.assertRaises(ValueError): read_artifact(HERE, wrong)
        with self.assertRaises(ValueError): read_artifact(HERE, {'path': '../outside', 'sha256': '0' * 64})

    def test_identity_relations_are_declared_consistently(self):
        cases = {c['id']: c for c in json.loads((HERE / 'catalog.json').read_text())['cases']}
        digest = lambda name: cases[name]['canonical']['sha256']
        for name in ('fir-permuted', 'fir-labels', 'fir-standalone', 'fir-negative-zero', 'fir-numeric-spelling'):
            self.assertEqual(digest('fir-base'), digest(name))
        for name in ('fir-rate-change', 'fir-initial-five', 'fir-observable-rename'):
            self.assertNotEqual(digest('fir-base'), digest(name))
        self.assertNotEqual(digest('fir-base'), digest('domain-separation'))
        self.assertNotEqual(digest('fir-base'), digest('version-separation'))
        self.assertEqual(digest('fir-large-a'), digest('fir-large-b'))
        self.assertEqual(digest('fir-two-observables'), digest('fir-observables-permuted'))
