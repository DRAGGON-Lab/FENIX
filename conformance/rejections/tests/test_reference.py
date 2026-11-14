"""Contract-facing regressions; reference adapters are deliberately outside packages."""
import copy
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import reference as ref


class ReferenceTests(unittest.TestCase):
    def test_fixed_catalog_diagnostics(self):
        catalog = ref.load_catalog()
        for case in catalog['cases']:
            with self.subTest(case=case['id']):
                self.assertEqual(ref.observe(case), case['expected'])

    def test_binary64_policy_and_nested_paths(self):
        self.assertEqual(ref.parse(b'9007199254740993', 'P03'), 9007199254740992.0)
        for token, category in [(b'9007199254740993', 'INTEGER_RANGE'),
                                (b'1e400', 'NUMBER_RANGE'), (b'1e-400', 'NUMBER_UNDERFLOW')]:
            with self.subTest(token=token):
                policy = 'P01' if category == 'INTEGER_RANGE' else 'P03'
                with self.assertRaises(ref.Rejection) as error:
                    ref.parse(b'{"a/b~":[0,' + token + b']}', policy)
                self.assertEqual((error.exception.category, error.exception.path),
                                 (category, '/a~1b~0/1'))
        self.assertEqual(ref.parse(b'0e-999999', 'P03'), 0)
        self.assertEqual(ref.parse(b'5e-324', 'P03'), 5e-324)

    def test_validators_do_not_mutate_or_normalize(self):
        catalog = ref.load_catalog()
        for case in catalog['cases']:
            if case['expected']['outcome'] == 'accept' and case['operation'] in ('model', 'producer', 'capability'):
                doc = ref.parse(ref.read_artifact(case['inputs']['primary']), 'P03')
                before = copy.deepcopy(doc)
                ref.validate_model(doc)
                self.assertEqual(doc, before)
                self.assertEqual(json.dumps(doc), json.dumps(before))
                if case['operation'] == 'producer':
                    sources = {key: ref.parse(ref.read_artifact(case['inputs'][key]), 'P01')
                               for key in ('design', 'experiment')}
                    snapshots = copy.deepcopy(sources)
                    ref.validate_producer(doc, **sources)
                    self.assertEqual(doc, before)
                    self.assertEqual(sources, snapshots)

    def test_no_expression_repair(self):
        doc = json.loads((ref.ROOT / 'spec/fir/proposals/examples/production-decay.json').read_bytes())
        expression = doc['model']['reactions'][1]['flux']
        expression['left'], expression['right'] = expression['right'], expression['left']
        before = copy.deepcopy(doc)
        with self.assertRaises(ref.Rejection):
            ref.validate_model(doc)
        self.assertEqual(doc, before)


if __name__ == '__main__':
    unittest.main()
