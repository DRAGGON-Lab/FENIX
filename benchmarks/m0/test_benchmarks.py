"""Failure controls for independent sample and timing checks."""

import importlib.util
import math
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "m0_benchmark", Path(__file__).with_name("run.py")
)
BENCHMARK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BENCHMARK)


class BenchmarkChecks(unittest.TestCase):
    def test_catalog_projection_accepts_linear_values(self):
        BENCHMARK.validate_values("linear-production", [0.5, 1.5, 2.5, 20.5])

    def test_equal_but_incorrect_values_do_not_pass(self):
        with self.assertRaisesRegex(ValueError, "P04"):
            BENCHMARK.validate_values("linear-production", [0.5, 1.5, 2.5, 20.6])

    def test_invalid_samples_and_missing_rows_fail(self):
        for values in ([0.5], [math.nan] * 4, [math.inf] * 4, [-1e-320] * 4):
            with self.subTest(values=values), self.assertRaises(ValueError):
                BENCHMARK.validate_values("linear-production", values)

    def test_timing_validation_rejects_nonfinite_empty_and_negative(self):
        for samples in ([], [math.nan], [math.inf], [-0.1]):
            with self.subTest(samples=samples), self.assertRaises(ValueError):
                BENCHMARK.summary(samples)
        self.assertEqual(BENCHMARK.summary([0.0, 2.0, 1.0])["median"], 1.0)


if __name__ == "__main__":
    unittest.main()
