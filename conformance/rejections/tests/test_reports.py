import copy
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import reference as ref
import review


class Reports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.python = review.run()
        # A simulated Julia envelope isolates comparison checks. Native execution is
        # separately required by CI; these tests do not claim independent evidence.
        cls.julia = copy.deepcopy(cls.python)
        cls.julia.update(review.provenance('independent-julia-rejection-reference'))
        cls.julia['runtime'] = {'name': 'julia', 'version': '1.10.13', 'dependencies': {'JSON': '1.13.4', 'JSONSchema': '1.6.0'}}

    def test_complete_reports(self):
        self.assertEqual(review.compare(self.python, self.julia), len(ref.load_catalog()['cases']))

    def test_report_corruption(self):
        changes = {
            'missing': lambda r: r['cases'].pop(),
            'duplicate': lambda r: r['cases'].append(copy.deepcopy(r['cases'][0])),
            'extra': lambda r: r['cases'].append({'id': 'unknown', 'passed': True, 'observed': {'outcome': 'accept'}}),
            'false_success': lambda r: r.update(passed=False),
            'row_failure': lambda r: r['cases'][0].update(passed=False),
            'unknown_implementation': lambda r: r.update(implementation='unknown'),
            'repeated_implementation': lambda r: r.update(implementation=self.python['implementation']),
            'stale_catalog': lambda r: r.update(catalog_sha256='0'*64),
            'stale_source': lambda r: r['evaluator_fingerprints'].update({'conformance/julia/p01.jl': '0'*64}),
            'stale_contract': lambda r: r['contract_fingerprints'].update({'spec/fir/proposals/ADR-P02.md': '0'*64}),
            'stale_dependencies': lambda r: r['dependency_fingerprints'].update({'conformance/julia/Manifest.toml': '0'*64}),
            'wrong_runtime': lambda r: r['runtime'].update(version='unknown'),
            'wrong_dependency_version': lambda r: r['runtime']['dependencies'].update(JSONSchema='0.0.0'),
            'wrong_report_version': lambda r: r.update(report_version=0),
            'boolean_report_version': lambda r: r.update(report_version=True),
            'wrong_schema': lambda r: r['schema_fingerprints'].update({'spec/fir/proposals/fir-m0.schema.json': '0'*64}),
            'stale_historical': lambda r: r['historical_catalog_fingerprints'].update({'conformance/bioir/catalog.json': '0'*64}),
        }
        for name, change in changes.items():
            with self.subTest(name=name):
                bad = copy.deepcopy(self.julia); change(bad)
                with self.assertRaises(ValueError): review.compare(self.python, bad)
        for key in ('stage', 'category', 'document', 'path', 'outcome'):
            with self.subTest(diagnostic=key):
                a, b = copy.deepcopy(self.python), copy.deepcopy(self.julia)
                for report in (a, b):
                    row = next(r for r in report['cases'] if r['observed']['outcome'] == 'reject')
                    row['observed'][key] = 'wrong'
                with self.assertRaises(ValueError): review.compare(a, b)
        a, b = copy.deepcopy(self.python), copy.deepcopy(self.julia)
        for report in (a, b):
            next(r for r in report['cases'] if r['observed']['outcome']=='reject')['observed'] = {'outcome':'accept'}
        with self.assertRaises(ValueError): review.compare(a, b)

    def test_output_paths_and_aliases(self):
        protected = ref.HERE / 'reference.py'
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            for name, make in [('symlink', os.symlink), ('hardlink', os.link)]:
                alias = folder / name; make(protected, alias)
                with self.subTest(alias=name), self.assertRaises(ValueError): review.check_output(alias)
            doc_alias = folder / 'document-hardlink'
            os.link(ref.ROOT/'docs/DEVELOPMENT_WORKFLOW.md', doc_alias)
            with self.assertRaises(ValueError): review.check_output(doc_alias)
            review.check_output(folder / 'new-report.json')
        for protected in (ref.HERE/'catalog.json', ref.HERE/'inputs/request-ode.input',
                          ref.ROOT/'spec/fir/proposals/fir-m0.schema.json', ref.ROOT/'packages/python/pyproject.toml'):
            with self.subTest(path=protected), self.assertRaises(ValueError): review.check_output(protected)
        review.check_output(ref.ROOT/'artifacts/rejections-python.json')


class CatalogIntegrity(unittest.TestCase):
    def test_corrupt_catalog_and_dependencies(self):
        original = ref.load_catalog()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            # Preserve the historical registration context without copying package envs.
            shutil.copytree(ref.ROOT/'conformance', root/'conformance', ignore=shutil.ignore_patterns('__pycache__'))
            shutil.copytree(ref.ROOT/'spec', root/'spec')
            directory = root/'conformance/rejections'
            def check(change):
                catalog = copy.deepcopy(original); change(catalog)
                (directory/'catalog.json').write_text(json.dumps(catalog))
                with self.assertRaises((ValueError, FileNotFoundError)): ref.load_catalog(directory, root)
            check(lambda c: c['cases'].append(c['cases'][0]))
            check(lambda c: c['coverage']['invalid-event'].append('unknown'))
            check(lambda c: c['coverage']['invalid-event'].append(c['coverage']['invalid-event'][0]))
            check(lambda c: c['cases'][0]['inputs']['primary'].update(sha256='0'*64))
            check(lambda c: c['cases'][0]['inputs']['primary'].update(path='../escape.input'))
            check(lambda c: c['cases'][0]['inputs']['primary'].update(path='/tmp/escape.input'))
            check(lambda c: c['coverage']['p03-contract-only'].pop())
            check(lambda c: c['coverage']['p02-examples'].pop())
            check(lambda c: next(x for x in c['cases'] if x['operation']=='producer')['inputs'].pop('design'))
            check(lambda c: c['cases'][0]['inputs'].update(request=c['cases'][0]['inputs']['primary']))
            (directory/'catalog.json').write_text(json.dumps(original))
            orphan = directory/'inputs/orphan.input'; orphan.write_text('{}')
            with self.assertRaises(ValueError): ref.load_catalog(directory, root)
            orphan.unlink()
            target = directory/'inputs/request-ode.input'; target.unlink()
            with self.assertRaises(FileNotFoundError): ref.load_catalog(directory, root)


class ApprovalStatus(unittest.TestCase):
    def test_supported_statuses_preserve_cases_and_report_status(self):
        from jsonschema import Draft7Validator
        from unittest.mock import patch
        catalog = ref.load_catalog()
        schema = json.loads((ref.HERE/'catalog.schema.json').read_bytes())
        original_cases = copy.deepcopy(catalog['cases'])
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            (folder/'catalog.schema.json').write_text(json.dumps(schema))
            for status in ('REVIEW_REQUIRED', 'APPROVED'):
                with self.subTest(status=status):
                    candidate = dict(catalog, status=status)
                    Draft7Validator(schema).validate(candidate)
                    (folder/'catalog.json').write_text(json.dumps(candidate))
                    with patch.object(review, 'HERE', folder):
                        self.assertEqual(review.provenance('independent-python-rejection-reference')['fixture_status'], status)
                    self.assertEqual(candidate['cases'], original_cases)
            invalid = dict(catalog, status='UNKNOWN')
            self.assertFalse(Draft7Validator(schema).is_valid(invalid))

    def test_report_catalog_status_disagreement(self):
        report = review.run()
        report['fixture_status'] = 'REVIEW_REQUIRED' if report['fixture_status'] == 'APPROVED' else 'APPROVED'
        with self.assertRaisesRegex(ValueError, 'fixture_status'):
            review.compare(report, {'report_version': 1})


if __name__ == '__main__': unittest.main()
