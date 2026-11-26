"""Regression controls for independently specified analytical references."""

import copy
import json
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

    def test_complete_catalog_corruption_is_detected_before_evaluation(self):
        original = reference.catalog()

        def mutations(value, path=()):
            if isinstance(value, dict):
                for key, child in value.items():
                    yield path, "delete", key
                    yield from mutations(child, (*path, key))
                yield path, "extra", "unknown"
            elif isinstance(value, list):
                yield path, "truncate", None
                yield path, "duplicate", None
                yield path, "reverse", None
                for index, child in enumerate(value):
                    yield from mutations(child, (*path, index))
            else:
                alternatives = (
                    (value + 1, True, float(value))
                    if type(value) in (int, float)
                    else ("wrong",)
                )
                for replacement in alternatives:
                    if (
                        type(replacement) is float
                        and replacement == value
                        and not (
                            path[-1] == "hill_n" or path[-2] in ("populations", "times")
                        )
                    ):
                        continue
                    yield path, "replace", replacement

        for path, operation, value in mutations(original):
            candidate = copy.deepcopy(original)
            target = candidate
            for key in path[:-1] if operation == "replace" else path:
                target = target[key]
            if operation == "replace":
                target[path[-1]] = value
            elif operation == "delete":
                del target[value]
            elif operation == "extra":
                target[value] = 0
            elif operation == "truncate":
                target.pop()
            elif operation == "duplicate":
                target.append(copy.deepcopy(target[0]))
            else:
                target.reverse()
            if json.dumps(candidate) == json.dumps(original):
                continue
            with self.subTest(path=path, operation=operation, value=value):
                with (
                    patch.object(reference, "catalog", return_value=candidate),
                    patch.object(reference, "verify_laws") as laws,
                    patch.object(reference, "rows") as rows,
                    self.assertRaisesRegex(ValueError, "catalog"),
                ):
                    reference.verify()
                laws.assert_not_called()
                rows.assert_not_called()

    def test_trajectory_preserving_mutations_are_rejected(self):
        original = reference.catalog()
        candidates = []
        candidate = copy.deepcopy(original)
        candidate["cases"][0]["populations"] = [4, 5]
        candidates.append(candidate)
        candidate = copy.deepcopy(original)
        for key in ("sender_export", "sender_import"):
            candidate["cases"][0]["parameters"][key] *= 2
        candidates.append(candidate)
        candidate = copy.deepcopy(original)
        candidate["cases"][5]["volumes"][0] *= 2
        candidates.append(candidate)
        for candidate in candidates:
            with patch.object(reference, "catalog", return_value=candidate):
                # These mutations pass the former trajectory-only gate.
                reference.verify_laws()
                with self.assertRaisesRegex(ValueError, "catalog definition"):
                    reference.verify()

    def test_object_order_and_numeric_spellings_preserve_definitions(self):
        def reorder(value):
            if isinstance(value, dict):
                return {
                    key: reorder(child) for key, child in reversed(list(value.items()))
                }
            if isinstance(value, list):
                return [reorder(child) for child in value]
            return value

        candidate = json.loads(json.dumps(reorder(reference.catalog())))
        candidate["cases"][0]["initial"][0] = 4.0
        with patch.object(reference, "catalog", return_value=candidate):
            rows, _ = reference.verify()
        self.assertEqual(len(rows), 30)

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
