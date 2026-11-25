"""Regression controls for independently specified analytical references."""

import copy
import unittest
from unittest.mock import patch

import reference


class TestReferences(unittest.TestCase):
    def test_parameter_unit_member_order_preserves_valid_metadata(self):
        catalog = copy.deepcopy(reference.catalog())
        catalog["parameter_units"] = dict(
            reversed(list(catalog["parameter_units"].items()))
        )
        with patch.object(reference, "catalog", return_value=catalog):
            rows, _ = reference.verify()
        self.assertEqual(len(rows), 30)

    def test_catalog_metadata_corruption_is_detected_before_evaluation(self):
        original = reference.catalog()
        mutations = [
            ("state_ids", list(reversed(original["state_ids"]))),
            ("state_ids", original["state_ids"][:-1]),
            ("time_unit", "min"),
            ("volumes_unit", "mL"),
            ("state_unit", "mol"),
        ]
        for parameter in original["parameter_units"]:
            units = original["parameter_units"].copy()
            units[parameter] = "incorrect"
            mutations.append(("parameter_units", units))
        units = original["parameter_units"].copy()
        units.pop("hill_n")
        mutations.extend(
            [
                ("parameter_units", units),
                ("parameter_units", {**original["parameter_units"], "unknown": "1"}),
            ]
        )
        for field in (
            "state_ids",
            "time_unit",
            "volumes_unit",
            "state_unit",
            "parameter_units",
        ):
            mutations.append((field, None))
        for field, value in mutations:
            with self.subTest(field=field, value=value):
                catalog = copy.deepcopy(original)
                if value is None:
                    catalog.pop(field)
                else:
                    catalog[field] = value
                with (
                    patch.object(reference, "catalog", return_value=catalog),
                    patch.object(reference, "verify_laws") as laws,
                    self.assertRaisesRegex(ValueError, "catalog metadata.*" + field),
                ):
                    reference.verify()
                laws.assert_not_called()

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
