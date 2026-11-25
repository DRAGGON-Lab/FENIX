"""Regression controls for independently specified analytical references."""

import copy
import unittest
from unittest.mock import patch

import reference


class TestReferences(unittest.TestCase):
    def test_analytical_catalog(self):
        rows, error = reference.verify()
        self.assertEqual(len(rows), 30)
        self.assertGreaterEqual(error, 0)

    def test_parameter_corruption_is_detected(self):
        original = reference.catalog()
        for index, key in (
            (0, "sender_export"),
            (5, "env_decay"),
            (9, "receiver_import"),
        ):
            with self.subTest(index=index, key=key):
                catalog = copy.deepcopy(original)
                catalog["cases"][index]["parameters"][key] += 1
                with (
                    patch.object(reference, "catalog", return_value=catalog),
                    self.assertRaisesRegex(ValueError, "declared ODE"),
                ):
                    reference.verify_laws()

    def test_initial_state_corruption_is_detected(self):
        catalog = copy.deepcopy(reference.catalog())
        catalog["cases"][0]["initial"][3] = 1
        with (
            patch.object(reference, "catalog", return_value=catalog),
            self.assertRaisesRegex(ValueError, "initial state"),
        ):
            reference.verify_laws()


if __name__ == "__main__":
    unittest.main()
