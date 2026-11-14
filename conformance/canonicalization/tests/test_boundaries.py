"""Regressions for auditable reports and catalog boundaries (no native FIR work)."""
import copy
import hashlib
import os
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from review_p03 import HERE, compare, review


class BoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.python = review()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'node.json'
            subprocess.run(['node', str(HERE / 'review_p03.cjs'), '--report', str(output)],
                           check=True, capture_output=True)
            cls.node = json.loads(output.read_text())

    def test_report_bytes_and_provenance(self):
        for report in (self.python, self.node):
            self.assertEqual(report['report_version'], 1)
            for key in ('catalog_sha256', 'catalog_schema_sha256', 'evaluator_sha256'):
                self.assertRegex(report[key], '^[0-9a-f]{64}$')
            self.assertTrue(report['runtime']['version'])
            for row in report['cases']:
                self.assertIn(row['stage'], ('json_jcs', 'binary64_jcs', 'fir_identity', 'contract_only'))
                if row['serialization'] == 'PASS':
                    self.assertEqual(len(bytes.fromhex(row['canonical_hex'])) * 2, len(row['canonical_hex']))
                    if row['stage'] == 'fir_identity':
                        self.assertIn('model_canonical_hex', row)
                        self.assertIn('model_canonical_sha256', row)
                else:
                    self.assertFalse(any('canonical' in key for key in row))

    def test_comparator_mutations(self):
        compare([self.python, self.node])
        reordered = copy.deepcopy(self.node)
        reordered['cases'].reverse()
        compare([reordered, self.python])
        mutations = {
            'missing': lambda r: r['cases'].pop(),
            'duplicate': lambda r: r['cases'].append(r['cases'][0]),
            'extra': lambda r: r['cases'].append(dict(r['cases'][0], id='extra')),
            'hex': lambda r: r['cases'][0].update(canonical_hex='31'),
            'digest': lambda r: r['cases'][0].update(canonical_sha256='0' * 64),
            'stage': lambda r: r['cases'][0].update(stage='contract_only'),
            'normalization': lambda r: r['cases'][0].update(fir_validation_normalization='PASS'),
            'unknown-identity': lambda r: r.update(implementation='invented'),
            'repeated-identity': lambda r: r.update(implementation=self.python['implementation']),
            'version': lambda r: r.update(report_version=0),
            'boolean-version': lambda r: r.update(report_version=True),
            'runtime': lambda r: r.update(runtime={}),
            'runtime-name': lambda r: r['runtime'].update(name='CPython'),
            'runtime-version': lambda r: r['runtime'].update(version='unknown'),
            'status': lambda r: r.update(fixture_status='APPROVED'),
        }
        for key in ('catalog_sha256', 'catalog_schema_sha256', 'evaluator_sha256'):
            mutations[key] = lambda r, key=key: r.update({key: '0' * 64})
        for name, mutate in mutations.items():
            bad = copy.deepcopy(self.node)
            mutate(bad)
            with self.subTest(name=name), self.assertRaises(ValueError):
                compare([self.python, bad])
        for key in ('model_canonical_hex', 'model_canonical_sha256'):
            bad = copy.deepcopy(self.node)
            next(r for r in bad['cases'] if r.get('stage') == 'fir_identity')[key] = '00'
            with self.subTest(key=key), self.assertRaises(ValueError):
                compare([self.python, bad])
        for status in ('REJECT_CONFIRMED', 'NOT_RUN'):
            bad = copy.deepcopy(self.node)
            next(r for r in bad['cases'] if r['serialization'] == status)['canonical_hex'] = '30'
            with self.subTest(status=status), self.assertRaises(ValueError):
                compare([self.python, bad])
        agreed = copy.deepcopy([self.python, self.node])
        for report in agreed:
            report['cases'][0].update(canonical_hex='31', canonical_sha256='6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b')
        with self.assertRaises(ValueError): compare(agreed)

    def test_both_catalog_boundaries(self):
        def missing(c): del c['coverage']['signed-zero']
        def unknown(c): c['coverage']['signed-zero'] = ['unknown']
        def duplicate(c): c['coverage']['signed-zero'] *= 2
        def unexecuted(c): c['coverage']['signed-zero'] = ['underflow']
        def duplicate_id(c): c['cases'].append(c['cases'][0])
        def stage(c): c['cases'][0]['stage'] = 'unknown'
        def no_bytes(c): del c['cases'][0]['canonical']
        def reject_bytes(c): c['cases'][0]['expected_outcome'] = 'reject'
        def foreign_fields(c): c['cases'][0]['normalization_status'] = 'NOT_RUN'
        def false_normalization(c): next(x for x in c['cases'] if x['stage'] == 'fir_identity')['normalization_status'] = 'PASS'
        def contract_bytes(c): next(x for x in c['cases'] if x['stage'] == 'contract_only')['canonical'] = c['cases'][0]['canonical']
        def digest(c): c['cases'][0]['input']['sha256'] = '0' * 64
        def bit_mismatch(c): c['cases'][0]['binary64_bits'] = '8000000000000000'
        for mutate in (missing, unknown, duplicate, unexecuted, duplicate_id, stage, no_bytes,
                       reject_bytes, foreign_fields, false_normalization, contract_bytes, digest, bit_mismatch):
            with self.subTest(mutation=mutate.__name__), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp) / 'catalog'
                shutil.copytree(HERE, directory)
                catalog = json.loads((directory / 'catalog.json').read_text())
                mutate(catalog)
                (directory / 'catalog.json').write_text(json.dumps(catalog))
                with self.assertRaises(Exception): review(directory)
                result = subprocess.run(['node', str(directory / 'review_p03.cjs'), '--report', str(Path(tmp) / 'report.json')], capture_output=True)
                self.assertNotEqual(result.returncode, 0)

    def test_corrupt_and_orphan_artifacts(self):
        for relative in ('inputs/rfc-0000000000000000.input', 'expected/rfc-0000000000000000.canonical',
                         'inputs/orphan.input', 'expected/orphan.canonical'):
            with self.subTest(path=relative), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp) / 'catalog'
                shutil.copytree(HERE, directory)
                (directory / relative).write_bytes(b'wrong')
                with self.assertRaises(Exception): review(directory)
                result = subprocess.run(['node', str(directory / 'review_p03.cjs'), '--report', str(Path(tmp) / 'report.json')], capture_output=True)
                self.assertNotEqual(result.returncode, 0)

    def test_malformed_bit_artifact_cannot_confirm_nonfinite_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / 'catalog'
            shutil.copytree(HERE, directory)
            catalog = json.loads((directory / 'catalog.json').read_text())
            case = next(c for c in catalog['cases'] if c['id'] == 'rfc-fff0000000000000')
            data = bytes([255])
            (directory / case['input']['path']).write_bytes(data)
            case['input']['sha256'] = hashlib.sha256(data).hexdigest()
            (directory / 'catalog.json').write_text(json.dumps(catalog))
            with self.assertRaises(ValueError): review(directory)
            result = subprocess.run(['node', str(directory / 'review_p03.cjs'), '--report', str(Path(tmp) / 'report.json')], capture_output=True)
            self.assertNotEqual(result.returncode, 0)

    def test_rehashed_wrong_expectations_fail_direct_byte_comparison(self):
        for key in ('canonical', 'model_canonical'):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp) / 'catalog'
                shutil.copytree(HERE, directory)
                catalog = json.loads((directory / 'catalog.json').read_text())
                case = next(c for c in catalog['cases'] if c['stage'] == 'fir_identity')
                record = case[key]
                (directory / record['path']).write_bytes(b'1')
                record['sha256'] = hashlib.sha256(b'1').hexdigest()
                (directory / 'catalog.json').write_text(json.dumps(catalog))
                with self.assertRaises(ValueError): review(directory)
                result = subprocess.run(['node', str(directory / 'review_p03.cjs'), '--report', str(Path(tmp) / 'report.json')], capture_output=True)
                self.assertNotEqual(result.returncode, 0)

    def test_protected_outputs_and_symlinks(self):
        for executable in ('python', 'node'):
            with self.subTest(executable=executable), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp) / 'catalog'
                shutil.copytree(HERE, directory)
                command = [sys.executable, str(directory / 'review_p03.py')] if executable == 'python' else ['node', str(directory / 'review_p03.cjs')]
                for relative in ('catalog.json', 'catalog.schema.json', 'review_p03.py', 'review_p03.cjs',
                                 'inputs/rfc-0000000000000000.input', 'expected/fir-base.normalized.json',
                                 'expected/fir-base.model.canonical', 'expected/fir-base.canonical'):
                    target = directory / relative
                    before = target.read_bytes()
                    alias = Path(tmp) / 'alias'
                    alias.symlink_to(target)
                    for output in (target, alias):
                        result = subprocess.run(command + ['--report', str(output)], capture_output=True)
                        self.assertNotEqual(result.returncode, 0, str(output))
                        self.assertEqual(target.read_bytes(), before)
                    alias.unlink()
                hardlink = Path(tmp) / 'hardlink'
                target = directory / 'catalog.schema.json'
                before = target.read_bytes()
                os.link(target, hardlink)
                result = subprocess.run(command + ['--report', str(hardlink)], capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(target.read_bytes(), before)
                alias = Path(tmp) / 'directory-alias'
                alias.symlink_to(directory / 'expected', target_is_directory=True)
                result = subprocess.run(command + ['--report', str(alias / 'new.json')], capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((directory / 'expected/new.json').exists())
