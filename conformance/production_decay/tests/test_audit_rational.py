"""Independent rational-audit invariants, corruption and read-only CLI tests."""
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('rational_audit', ROOT / 'audit_rational.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class RationalAuditTests(unittest.TestCase):
    def test_half_even_exact_rounding(self):
        for value, digits, expected in [(F(5, 4), 2, F(6, 5)), (F(27, 20), 2, F(7, 5)),
                                        (F(199, 20), 2, F(10)), (F(1, 800), 2, F(12, 10000)),
                                        (F(0), 50, F(0)), (F(-5, 4), 2, F(-6, 5))]:
            self.assertEqual(audit.round_significant(value, digits), expected)

    def test_enclosure_and_tail_index(self):
        # For z=1, the 401-term partial sum's next term is -1/402!.
        import math
        lo, hi = audit.enclosure(F(1), F(1), F(0), F(1))
        self.assertEqual(hi - lo, F(2, math.factorial(402)))
        for a, b, x, t, expected in [(0, 1, 0, 10, 0), (2, 0, F(1, 2), 10, F(41, 2)),
                                      (2, F(1, 2), 4, 20, 4), (2, 1, 3, 0, 3)]:
            self.assertEqual(audit.enclosure(*map(F, (a, b, x, t))), (expected, expected))

    def test_full_catalog_and_cli_never_write(self):
        catalog = json.loads((ROOT / 'catalog.json').read_text())
        count = sum(len(c['samples']) for c in catalog['cases'])
        self.assertEqual(len(audit.audit_catalog(ROOT / 'catalog.json')), count)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'catalog.json'
            path.write_text(json.dumps(catalog))
            before = path.read_bytes()
            result = subprocess.run([sys.executable, str(ROOT / 'audit_rational.py'), '--catalog', str(path)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(path.read_bytes(), before)
            catalog['cases'][0]['samples'][0]['expected'] = '1.' + '0'*49 + 'E+0'
            path.write_text(json.dumps(catalog)); before = path.read_bytes()
            result = subprocess.run([sys.executable, str(ROOT / 'audit_rational.py'), '--catalog', str(path)],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('baseline-zero/0000000000000000', result.stderr)
            self.assertEqual(path.read_bytes(), before)

    def test_bad_input_and_audit_domain(self):
        for raw in ('bad', 'bff0000000000000', '7ff0000000000000', '7ff8000000000000'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                audit.decode(raw)
        self.assertEqual(audit.decode(struct.pack('>d', 0.1).hex()), F.from_float(0.1))
        for params in ((1, 11, 0, 1), (20000, 0, 0, 1)):
            with self.assertRaisesRegex(ValueError, 'audit domain'):
                audit.enclosure(*map(F, params))
        catalog = json.loads((ROOT / 'catalog.json').read_text())
        catalog['units']['time'] = 'min'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'catalog.json'; path.write_text(json.dumps(catalog))
            with self.assertRaises(ValueError):
                audit.audit_catalog(path)
