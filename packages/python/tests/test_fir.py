"""Immutable FIR mathematics, normalization and identity; no solver claims."""

import dataclasses
import hashlib
import json
import unittest
from typing import Any

from fenix.fir import FIRDocument, FIRModel, FIRValidationError


def model() -> dict[str, Any]:
    def parameter(name: str) -> dict[str, str]:
        return {"op": "parameter", "id": name}

    loss = {
        "op": "multiply",
        "left": parameter("beta"),
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
            {"id": "alpha", "value": 10.0, "unit": "molecule/s"},
            {"id": "beta", "value": 0.1, "unit": "1/s"},
        ],
        "reactions": [
            {
                "id": "production",
                "stoichiometry": {"x": 1.0},
                "flux": parameter("alpha"),
            },
            {"id": "decay", "stoichiometry": {"x": -1.0}, "flux": loss},
        ],
        "equations": [
            {
                "state": "x",
                "unit": "molecule/s",
                "rhs": {"op": "subtract", "left": parameter("alpha"), "right": loss},
            }
        ],
        "observables": [
            {"id": "z", "state": "x", "unit": "molecule"},
            {"id": "a", "state": "x", "unit": "molecule"},
        ],
        "assumptions": [
            "single_representative_cell",
            "well_mixed",
            "fixed_volume",
            "constant_rates",
            "no_interventions",
        ],
        "capabilities": {"ode": True, "ssa": False},
    }


class TestFIR(unittest.TestCase):
    def test_normalization_copy_and_idempotence(self) -> None:
        raw = model()
        original = FIRModel.from_dict(raw)
        normalized = original.normalized()
        self.assertEqual(original.to_dict(), raw)
        self.assertEqual(normalized.to_dict()["observables"][0]["id"], "a")
        self.assertEqual(normalized.normalized(), normalized)
        for name in (
            "states",
            "parameters",
            "reactions",
            "equations",
            "observables",
            "assumptions",
        ):
            raw[name].reverse()
        permuted = FIRModel.from_dict(raw)
        self.assertEqual(original.digest, permuted.digest)
        self.assertEqual(
            original.canonical_model_bytes(), permuted.canonical_model_bytes()
        )
        self.assertNotEqual(
            original.to_dict()["observables"], permuted.to_dict()["observables"]
        )
        self.assertEqual(
            FIRModel.from_json(
                original.canonical_model_bytes()
            ).canonical_model_bytes(),
            original.canonical_model_bytes(),
        )

    def test_identity_scope_and_named_interface(self) -> None:
        raw = model()
        m = FIRModel.from_dict(raw)
        preimage = json.loads(m.identity_bytes())
        self.assertEqual(set(preimage), {"domain", "canonicalization_version", "model"})
        self.assertEqual(preimage["domain"], "fenix.fir")
        self.assertEqual(preimage["canonicalization_version"], "0.1.0")
        self.assertEqual(preimage["model"], m.normalized().to_dict())
        self.assertEqual(m.digest, hashlib.sha256(m.identity_bytes()).hexdigest())
        changed = model()
        changed["observables"][0]["id"] = "renamed"
        self.assertNotEqual(m.digest, FIRModel.from_dict(changed).digest)
        changed = model()
        changed["states"][0]["initial"] = 2.0
        self.assertNotEqual(m.digest, FIRModel.from_dict(changed).digest)
        a = FIRDocument.from_dict(
            {"model": raw, "provenance": {"compiler": {"name": "A", "version": "1"}}}
        )
        b = FIRDocument.from_dict(
            {"model": raw, "provenance": {"compiler": {"name": "B", "version": "2"}}}
        )
        self.assertEqual(a.digest, b.digest)
        self.assertNotEqual(a.to_dict(), b.to_dict())
        self.assertEqual(FIRDocument.from_json(a.to_json()).to_dict(), a.to_dict())

    def test_deep_immutability_and_fresh_serialization(self) -> None:
        raw = model()
        doc = FIRDocument.from_dict(
            {"model": raw, "provenance": {"compiler": {"name": "A", "version": "1"}}}
        )
        raw["states"][0]["initial"] = 999.0
        out = doc.to_dict()
        out["model"]["states"][0]["initial"] = 777.0
        out["provenance"]["compiler"]["name"] = "changed"
        self.assertEqual(doc.to_dict()["model"]["states"][0]["initial"], 0.5)
        self.assertEqual(doc.to_dict()["provenance"]["compiler"]["name"], "A")
        self.assertFalse(hasattr(doc, "__dict__"))
        self.assertFalse(hasattr(doc.model, "__dict__"))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            doc.model = None
        with self.assertRaises(TypeError):
            doc.provenance["compiler"]["name"] = "changed"
        with self.assertRaises(TypeError):
            FIRModel()
        with self.assertRaises(TypeError):
            FIRDocument()

    def test_native_numeric_policy_and_raw_p03(self) -> None:
        for value in (1, True, float("inf"), float("nan"), -1.0):
            raw = model()
            raw["parameters"][0]["value"] = value
            with self.subTest(value=value), self.assertRaises(FIRValidationError):
                FIRModel.from_dict(raw)
        for value in (-0.0, 5e-324, 9007199254740992.0):
            raw = model()
            raw["parameters"][0]["value"] = value
            m = FIRModel.from_dict(raw)
            self.assertEqual(
                FIRModel.from_json(m.canonical_model_bytes()).digest, m.digest
            )
        text = json.dumps(model()).replace("10.0", "9007199254740993")
        parsed = FIRModel.from_json(text)
        self.assertEqual(parsed.to_dict()["parameters"][0]["value"], 9007199254740992.0)

    def test_standalone_labels_require_existing_observables(self) -> None:
        raw = {
            "model": model(),
            "provenance": {"display_labels": {"observables": {"unknown": "label"}}},
        }
        with self.assertRaises(FIRValidationError) as caught:
            FIRDocument.from_dict(raw)
        self.assertEqual(
            (caught.exception.category, caught.exception.path),
            ("REFERENCE", "/provenance/display_labels/observables/unknown"),
        )
        raw["provenance"]["display_labels"]["observables"] = {"a": "é😀"}
        doc = FIRDocument.from_dict(raw)
        self.assertEqual(doc.digest, FIRDocument.from_dict({"model": model()}).digest)
        self.assertEqual(
            doc.to_dict()["provenance"]["display_labels"]["observables"]["a"], "é😀"
        )

    def test_capability_and_malformed_json(self) -> None:
        m = FIRModel.from_dict(model())
        self.assertIsNone(m.require_capability("ode"))
        for profile in ("ssa", "other"):
            with self.assertRaises(FIRValidationError) as caught:
                m.require_capability(profile)
            self.assertEqual(
                (caught.exception.category, caught.exception.path),
                ("UNSUPPORTED_PROFILE", "/profile"),
            )
        with self.assertRaises(FIRValidationError) as caught:
            FIRModel.from_json('{"x":1,"x":2}')
        self.assertEqual(
            (caught.exception.category, caught.exception.path), ("DUPLICATE_KEY", "/x")
        )


if __name__ == "__main__":
    unittest.main()
