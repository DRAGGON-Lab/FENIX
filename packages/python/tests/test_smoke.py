"""Package-only checks, not scientific conformance tests."""

import unittest

import fenix


class TestScaffold(unittest.TestCase):
    def test_version(self):
        self.assertEqual(fenix.__version__, "0.0.0")

    def test_content_api_boundary(self):
        from fenix.bioir import DesignContent, ExperimentContent

        self.assertTrue(callable(DesignContent))
        self.assertTrue(callable(ExperimentContent))
        self.assertFalse(hasattr(fenix, "BioIR"))
        self.assertFalse(hasattr(fenix, "FIR"))


if __name__ == "__main__":
    unittest.main()
