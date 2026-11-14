"""Evidence failures must not become apparent conformance successes."""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from review_p03 import HERE, compare, read_artifact, review


def utf16_key(value):
    """Big-endian bytes compare as unsigned UTF-16 code units, without a BOM."""
    return value.encode('utf-16-be')


class DeclarationOrderingTests(unittest.TestCase):
    def test_utf16_comparator(self):
        # These are comparator probes, not new valid FIR identifiers.
        for earlier, later in (('amount_x', 'another_amount'),
                               ('\U00010000', '\ue000'),
                               ('\U0001f600', '\ufffd')):
            with self.subTest(earlier=earlier, later=later):
                self.assertLess(utf16_key(earlier), utf16_key(later))
                self.assertEqual(sorted([later, earlier], key=utf16_key), [earlier, later])
        self.assertGreater('\U00010000', '\ue000')  # Python code-point order differs.
        self.assertEqual(utf16_key(json.loads('"\\u0061mount_x"')), utf16_key('amount_x'))

    def test_expected_declaration_order(self):
        catalog = json.loads((HERE / 'catalog.json').read_text())
        inspected = set()
        for case in catalog['cases']:
            if case['stage'] != 'fir_identity':
                continue
            artifact = case['normalized']
            model = json.loads(read_artifact(HERE, artifact))
            inspected.add(artifact['path'])
            for collection, key in (('states', 'id'), ('parameters', 'id'),
                                    ('reactions', 'id'), ('observables', 'id'),
                                    ('equations', 'state'), ('assumptions', None)):
                keys = [item[key] if key else item for item in model[collection]]
                for left, right in zip(keys, keys[1:]):
                    with self.subTest(case=case['id'], artifact=artifact['path'],
                                      collection=collection, left=left, right=right):
                        self.assertLessEqual(utf16_key(left), utf16_key(right),
                                             f'Out-of-order keys: {left!r}, {right!r}')
        physical = {path.relative_to(HERE).as_posix()
                    for path in (HERE / 'expected').rglob('*.normalized.json')}
        self.assertSetEqual(inspected, physical,
                            'Every expected normalized artifact must be referenced and inspected')


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
