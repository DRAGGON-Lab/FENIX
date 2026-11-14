"""Fixed issue #16 expectations derived from RFC 8785 and ratified P03."""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from review_p03 import HERE, read_artifact, review


class VectorTests(unittest.TestCase):
    def test_fixed_new_vectors(self):
        cases = {c['id']: c for c in json.loads((HERE / 'catalog.json').read_text())['cases']}
        expected = {
            'raw-zero': ('0', '0'), 'raw-negative-zero': ('-0', '0'),
            'number-one': ('1', '1'), 'number-one-decimal': ('1.0', '1'), 'number-one-exponent': ('1e0', '1'),
            'exponent-minus-seven': ('1e-7', '1e-7'), 'exponent-minus-six': ('1e-6', '0.000001'),
            'exponent-twenty': ('1e20', '100000000000000000000'), 'exponent-twenty-one': ('1e21', '1e+21'),
            'boundary-below': ('9007199254740991', '9007199254740991'),
            'boundary-exact': ('9007199254740992', '9007199254740992'),
            'boundary-above-two': ('9007199254740994', '9007199254740994'),
            'escaped-composed': ('"\\u00e9"', '"é"'),
            'array-forward': ('[3,{"z":2,"a":1},1]', '[3,{"a":1,"z":2},1]'),
            'array-reversed': ('[1,{"z":2,"a":1},3]', '[1,{"a":1,"z":2},3]'),
            'nested-utf16-keys': ('{"outer":{"\ue000":1,"😀":2,"2":3,"10":4,"1":5}}',
                                  '{"outer":{"1":5,"10":4,"2":3,"😀":2,"\ue000":1}}'),
        }
        for name, (raw, canonical) in expected.items():
            with self.subTest(case=name):
                self.assertEqual(read_artifact(HERE, cases[name]['input']), raw.encode())
                self.assertEqual(read_artifact(HERE, cases[name]['canonical']), canonical.encode())
        negative_infinity = cases['rfc-fff0000000000000']
        self.assertEqual(negative_infinity['binary64_bits'], 'fff0000000000000')
        self.assertEqual(negative_infinity['expected_outcome'], 'reject')
        report = {r['id']: r for r in review()['cases']}
        for name, (_, canonical) in expected.items():
            self.assertEqual(report[name]['canonical_hex'], canonical.encode().hex())
        digest = lambda name: cases[name]['canonical']['sha256']
        self.assertEqual(digest('boundary-exact'), digest('large-rounding'))
        self.assertEqual(read_artifact(HERE, cases['large-rounding']['input']), b'9007199254740993')
        self.assertNotEqual(digest('array-forward'), digest('array-reversed'))
        self.assertEqual(digest('escaped-composed'), digest('composed'))
        self.assertNotEqual(digest('composed'), digest('decomposed'))
        self.assertEqual(sum(r['serialization'] == 'NOT_RUN' for r in report.values()), 17)

    def test_fixed_coverage(self):
        coverage = json.loads((HERE / 'catalog.json').read_text())['coverage']
        self.assertEqual(set(coverage), {'utf16-key-ordering', 'signed-zero', 'numeric-spelling',
                         'exponent-thresholds', 'subnormals', 'nonfinite-rejection',
                         'unicode-preservation', 'array-ordering', 'binary64-integer-boundary'})
        for key, names in {
            'utf16-key-ordering': ['unicode-order', 'nested-utf16-keys'],
            'signed-zero': ['raw-zero', 'raw-negative-zero', 'signed-zero'],
            'numeric-spelling': ['number-one', 'number-one-decimal', 'number-one-exponent'],
            'exponent-thresholds': ['exponent-minus-seven', 'exponent-minus-six', 'exponent-twenty', 'exponent-twenty-one'],
            'subnormals': ['rfc-0000000000000001', 'rfc-8000000000000001'],
            'nonfinite-rejection': ['rfc-7fffffffffffffff', 'rfc-7ff0000000000000', 'rfc-fff0000000000000'],
            'unicode-preservation': ['composed', 'decomposed', 'escapes', 'escaped-composed'],
            'array-ordering': ['array-forward', 'array-reversed'],
            'binary64-integer-boundary': ['boundary-below', 'boundary-exact', 'large-rounding', 'boundary-above-two'],
        }.items():
            self.assertEqual(coverage[key], names)
