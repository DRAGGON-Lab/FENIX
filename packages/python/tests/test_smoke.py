"""Package-only checks, not scientific conformance tests."""

import unittest

import fenix


class TestScaffold(unittest.TestCase):
    def test_version(self):
        self.assertEqual(fenix.__version__, "0.0.0")

    def test_no_modeling_api_yet(self):
        self.assertFalse(hasattr(fenix, "BioIR"))
        self.assertFalse(hasattr(fenix, "FIR"))


if __name__ == "__main__":
    unittest.main()
