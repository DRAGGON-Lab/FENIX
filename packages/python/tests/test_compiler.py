"""M0 compiler behavior against approved sources and mathematical references."""

import dataclasses
import hashlib
import json
import math
import unittest
from pathlib import Path

from test_bioir import design, experiment

from fenix.bioir import (
    BioIRValidationError,
    DesignDocument,
    ExperimentDocument,
    InitialCount,
    Metadata,
    Observable,
    ParameterAssignment,
    PortReference,
    Quantity,
)
from fenix.compiler import compile_experiment
from fenix.fir import FIRDocument, FIRValidationError

ROOT = Path(__file__).resolve().parents[3]


def committed(d=None, **changes):
    source = DesignDocument(content=design() if d is None else d)
    content = experiment(
        source_design=source.content, design=source.reference, **changes
    )
    return ExperimentDocument(content=content, source_design=source)


class TestCompiler(unittest.TestCase):
    def test_approved_source_pairs_match_mathematical_examples(self):
        catalog = json.loads(
            (ROOT / "conformance/rejections/catalog.json").read_bytes()
        )
        cases = [
            c
            for c in catalog["cases"]
            if c["operation"] == "producer" and c["expected"]["outcome"] == "accept"
        ]
        self.assertGreater(len(cases), 3)
        for case in cases:
            with self.subTest(case=case["id"]):
                inputs = case["inputs"]
                for artifact in inputs.values():
                    self.assertEqual(
                        hashlib.sha256(
                            (ROOT / artifact["path"]).read_bytes()
                        ).hexdigest(),
                        artifact["sha256"],
                    )
                source = DesignDocument.from_json(
                    (ROOT / inputs["design"]["path"]).read_bytes()
                )
                scenario = ExperimentDocument.from_json(
                    (ROOT / inputs["experiment"]["path"]).read_bytes(),
                    designs=(source,),
                )
                expected = json.loads((ROOT / inputs["primary"]["path"]).read_bytes())
                result = compile_experiment(scenario)
                # Declaration order is preserved by readers but irrelevant to P03
                # identity. Compare against the independent example's normalized model.
                reference = FIRDocument.from_json(
                    (ROOT / inputs["primary"]["path"]).read_bytes(),
                    design=source,
                    experiment=scenario,
                )
                self.assertEqual(
                    result.model.canonical_model_bytes(),
                    reference.model.canonical_model_bytes(),
                )
                self.assertEqual(result.digest, reference.digest)
                p = result.to_dict()["provenance"]
                self.assertEqual(p["design_digest"], source.digest)
                self.assertEqual(p["experiment_digest"], scenario.digest)
                self.assertEqual(
                    p["symbol_map"]["states"],
                    expected["provenance"]["symbol_map"]["states"],
                )
                self.assertEqual(
                    sorted(
                        p["symbol_map"]["parameters"],
                        key=lambda i: i["fir_parameter_id"],
                    ),
                    sorted(
                        expected["provenance"]["symbol_map"]["parameters"],
                        key=lambda i: i["fir_parameter_id"],
                    ),
                )

    def test_function_roles_bind_independently_of_names_and_order(self):
        d = design()
        names = {"alpha": "loss_name", "beta": "production_name"}
        renamed = dataclasses.replace(
            d,
            parameters=tuple(
                dataclasses.replace(p, id=names[p.id]) for p in d.parameters
            )[::-1],
            functions=tuple(
                dataclasses.replace(f, parameter=names[f.parameter], id="fn_" + f.id)
                for f in d.functions
            )[::-1],
        )
        base = committed()
        assignments = tuple(
            dataclasses.replace(a, parameter=names[a.parameter])
            for a in base.content.parameters
        )[::-1]
        result = compile_experiment(committed(renamed, parameters=assignments))
        self.assertEqual(result.digest, compile_experiment(base).digest)
        p = result.to_dict()["provenance"]["symbol_map"]["parameters"]
        by_id = {i["fir_parameter_id"]: i for i in p}
        self.assertEqual(by_id["alpha"]["bioir_parameter_id"], "loss_name")
        self.assertEqual(by_id["beta"]["bioir_parameter_id"], "production_name")

    def test_zero_fractional_empty_and_explicit_binary64(self):
        source = committed(
            parameters=(
                ParameterAssignment(
                    parameter="alpha", quantity=Quantity(value=-0.0, unit="molecule/s")
                ),
                ParameterAssignment(
                    parameter="beta", quantity=Quantity(value=0, unit="1/s")
                ),
            ),
            observables=(),
        )
        model = compile_experiment(source).model.to_dict()
        self.assertEqual(model["observables"], [])
        self.assertEqual(model["states"][0]["initial"], 0.5)
        self.assertIs(type(model["states"][0]["initial"]), float)
        params = {p["id"]: p["value"] for p in model["parameters"]}
        self.assertEqual(params, {"alpha": 0.0, "beta": 0.0})
        self.assertEqual(math.copysign(1, params["alpha"]), -1)
        self.assertTrue(all(type(v) is float for v in params.values()))
        self.assertTrue(
            all(type(r["stoichiometry"]["x"]) is float for r in model["reactions"])
        )
        self.assertEqual(model["capabilities"], {"ode": True, "ssa": False})

    def test_numeric_boundaries_and_volume_do_not_rescale_counts(self):
        initial = 1e20
        source = committed(
            parameters=(
                ParameterAssignment(
                    parameter="alpha",
                    quantity=Quantity(value=2**53 - 1, unit="molecule/s"),
                ),
                ParameterAssignment(
                    parameter="beta", quantity=Quantity(value=5e-324, unit="1/s")
                ),
            ),
            initial_counts=(
                InitialCount(
                    species="x", quantity=Quantity(value=initial, unit="molecule")
                ),
            ),
        )
        fir = compile_experiment(source)
        model = fir.model.to_dict()
        self.assertEqual(model["states"][0]["initial"], initial)
        self.assertEqual(
            {p["id"]: p["value"] for p in model["parameters"]},
            {"alpha": float(2**53 - 1), "beta": 5e-324},
        )
        d = source.source_design.content
        changed = dataclasses.replace(
            d,
            compartments=(
                dataclasses.replace(
                    d.compartments[0], volume=Quantity(value=2e-15, unit="L")
                ),
            ),
        )
        alternate = committed(
            changed,
            parameters=source.content.parameters,
            initial_counts=source.content.initial_counts,
        )
        self.assertEqual(fir.digest, compile_experiment(alternate).digest)

    def test_source_identity_and_author_metadata_are_nonsemantic(self):
        base = committed()
        source = base.source_design.with_metadata(Metadata(name="Author"))
        decorated = ExperimentDocument(
            content=base.content,
            source_design=source,
            metadata=Metadata(description="solver is not model data"),
        )
        a = compile_experiment(base)
        b = compile_experiment(decorated)
        self.assertEqual(a.digest, b.digest)
        text = b.to_json()
        self.assertNotIn("Author", text)
        self.assertNotIn("solver is not model data", text)
        d = dataclasses.replace(base.source_design.content, id="another_design")
        other = committed(d)
        c = compile_experiment(other)
        self.assertEqual(a.digest, c.digest)
        self.assertNotEqual(
            a.to_dict()["provenance"]["design_digest"],
            c.to_dict()["provenance"]["design_digest"],
        )

    def test_observable_id_is_semantic_and_outputs_are_fresh(self):
        base = committed()
        changed = committed(
            observables=(
                Observable(
                    id="renamed", target=PortReference(species="x", port="amount")
                ),
            )
        )
        a = compile_experiment(base)
        self.assertNotEqual(a.digest, compile_experiment(changed).digest)
        original = base.to_json()
        output = a.to_dict()
        output["model"]["states"][0]["initial"] = 900
        output["provenance"]["symbol_map"]["states"].clear()
        self.assertEqual(a.model.to_dict()["states"][0]["initial"], 0.5)
        self.assertEqual(base.to_json(), original)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            a.model = None

    def test_only_verified_exact_native_experiments_are_accepted(self):
        class DerivedExperiment(ExperimentDocument):
            pass

        base = committed()
        derived = DerivedExperiment(
            content=base.content, source_design=base.source_design
        )
        for value in (None, {}, base.content, base.to_dict(), derived):
            with self.subTest(value=type(value)):
                with self.assertRaises(FIRValidationError) as caught:
                    compile_experiment(value)
                self.assertEqual(
                    (caught.exception.category, caught.exception.path),
                    ("SCHEMA", "/experiment"),
                )

    def test_missing_assignments_fail_before_compilation(self):
        with self.assertRaises(BioIRValidationError) as caught:
            committed(parameters=())
        self.assertEqual(
            (caught.exception.category, caught.exception.path),
            ("SCHEMA", "/parameters"),
        )


if __name__ == "__main__":
    unittest.main()
