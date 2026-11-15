"""Exact M0 mathematical validation regressions; no execution or algebra repair."""

import copy
import unittest

from fenix.bioir import BioIRValidationError
from fenix.bioir._json import parse_json
from fenix.fir._errors import FIRValidationError
from fenix.fir._validation import validate_envelope, validate_model


def model():
    alpha = {"op": "parameter", "id": "alpha"}
    decay = {
        "op": "multiply",
        "left": {"op": "parameter", "id": "beta"},
        "right": {"op": "state", "id": "x"},
    }
    return {
        "schema_version": "0.1.0",
        "time_unit": "s",
        "states": [
            {
                "id": "x",
                "quantity": "molecular_count",
                "scope": "representative_cell",
                "unit": "molecule",
                "initial": 0.5,
            }
        ],
        "parameters": [
            {"id": "alpha", "value": 0.0, "unit": "molecule/s"},
            {"id": "beta", "value": 0.0, "unit": "1/s"},
        ],
        "reactions": [
            {"id": "production", "stoichiometry": {"x": 1.0}, "flux": alpha},
            {"id": "decay", "stoichiometry": {"x": -1.0}, "flux": decay},
        ],
        "equations": [
            {
                "state": "x",
                "unit": "molecule/s",
                "rhs": {
                    "op": "subtract",
                    "left": copy.deepcopy(alpha),
                    "right": copy.deepcopy(decay),
                },
            }
        ],
        "observables": [],
        "assumptions": [
            "single_representative_cell",
            "well_mixed",
            "fixed_volume",
            "constant_rates",
            "no_interventions",
        ],
        "capabilities": {"ode": True, "ssa": False},
    }


class TestFIRValidation(unittest.TestCase):
    def test_positive_and_nonmutation(self):
        value = model()
        original = copy.deepcopy(value)
        validate_envelope({"model": value})
        self.assertEqual(value, original)
        value["parameters"].reverse()
        validate_model(value)

    def test_precise_roles_references_and_templates(self):
        for field, replacement, category, path in [
            ("unit", "molecule/s", "UNIT", "/model/parameters/1/unit"),
            ("value", -0.1, "SCHEMA", "/model/parameters/1/value"),
        ]:
            value = model()
            value["parameters"][1][field] = replacement
            with self.assertRaises(FIRValidationError) as got:
                validate_model(value)
            self.assertEqual(
                (got.exception.category, got.exception.path), (category, path)
            )
        value = model()
        value["reactions"][1]["flux"]["right"]["id"] = "missing"
        with self.assertRaises(FIRValidationError) as got:
            validate_model(value)
        self.assertEqual(got.exception.path, "/model/reactions/1/flux/right/id")
        value = model()
        (
            value["reactions"][1]["flux"]["left"],
            value["reactions"][1]["flux"]["right"],
        ) = (
            value["reactions"][1]["flux"]["right"],
            value["reactions"][1]["flux"]["left"],
        )
        with self.assertRaises(FIRValidationError) as got:
            validate_model(value)
        self.assertEqual(got.exception.category, "TEMPLATE")

    def test_programmatic_numbers_must_already_be_binary64(self):
        for value in (True, 1, "1", float("inf"), float("nan")):
            data = model()
            data["parameters"][0]["value"] = value
            with self.assertRaises(FIRValidationError):
                validate_model(data)

    def test_p03_numeric_policy_is_separate(self):
        self.assertIs(type(parse_json("1", numeric_policy="p03")), float)
        self.assertEqual(
            parse_json("9007199254740993", numeric_policy="p03"), 9007199254740992.0
        )
        with self.assertRaises(BioIRValidationError):
            parse_json("9007199254740993")
        with self.assertRaises(ValueError):
            parse_json("1", numeric_policy="guess")
