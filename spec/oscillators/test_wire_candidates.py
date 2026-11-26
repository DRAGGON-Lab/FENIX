"""Positive/negative structural and bounded cross-artifact candidate controls."""

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import review_candidates as review
from jsonschema import ValidationError


class TestWireCandidates(unittest.TestCase):
    def document(self, template, name):
        return review.read(review.HERE / "examples" / template / name)

    def test_both_literal_pairs(self):
        for template, dimensions in (
            ("single-cell", (6, 21, 15)),
            ("three-strain", (18, 54, 48)),
        ):
            with self.subTest(template=template):
                outcome = review.audit_pair(review.HERE / "examples" / template)
                self.assertEqual(
                    tuple(outcome[k] for k in ("states", "parameters", "reactions")),
                    dimensions,
                )

    def test_structural_source_negatives(self):
        for template in ("single-cell", "three-strain"):
            original = self.document(template, "design.json")
            for fault in (
                "field",
                "version",
                "scope",
                "missing_parameter_role",
                "missing_gate",
                "unit",
                "port",
                "id_newline",
            ):
                changed = copy.deepcopy(original)
                content = changed["content"]
                if fault == "field":
                    content["solver"] = "Radau"
                elif fault == "version":
                    content["schema_version"] = "0.1.0"
                elif fault == "scope":
                    content["owners"][0]["species"][0]["scope"] = "total"
                elif fault == "missing_parameter_role":
                    content["parameters"][0] = copy.deepcopy(content["parameters"][1])
                elif fault == "missing_gate":
                    content["gates"].pop()
                elif fault == "unit":
                    content["owners"][0]["volume"]["unit"] = "mL"
                elif fault == "port":
                    content["owners"][0]["species"][0]["ports"][0]["kind"] = "callback"
                else:
                    content["id"] += "\n"
                with (
                    self.subTest(template=template, fault=fault),
                    self.assertRaises(ValidationError),
                ):
                    review.validate("bioir", changed)

    def test_structural_fir_negatives(self):
        original = self.document("three-strain", "fir.json")
        for fault in (
            "population_sign",
            "weighted_flux",
            "catalyst_sink",
            "sensor",
            "operand_order",
            "missing_zero_reaction",
            "scope",
            "capability",
            "wrong_basis",
            "duplicate_state",
            "extra_ast",
        ):
            changed = copy.deepcopy(original)
            model = changed["model"]
            reactions = {r["id"]: r for r in model["reactions"]}
            if fault == "population_sign":
                reactions["import11"]["stoichiometry"]["e1"]["op"] = "population"
            elif fault == "weighted_flux":
                reactions["export11"]["stoichiometry"]["e1"] = 1
            elif fault == "catalyst_sink":
                reactions["translation1"]["stoichiometry"]["m1"] = -1
            elif fault == "sensor":
                reactions["repressed1"]["flux"]["right"]["sensor"]["left"]["id"] = "e3"
            elif fault == "operand_order":
                flux = reactions["translation1"]["flux"]
                flux["left"], flux["right"] = flux["right"], flux["left"]
            elif fault == "missing_zero_reaction":
                model["reactions"].pop()
            elif fault == "scope":
                model["states"][0]["scope"] = "environment_total"
            elif fault == "capability":
                model["capabilities"]["ssa"] = True
            elif fault == "wrong_basis":
                next(p for p in model["parameters"] if p["id"] == "beta1")["basis"] = (
                    "first_order"
                )
            elif fault == "duplicate_state":
                model["states"][0] = copy.deepcopy(model["states"][1])
            else:
                reactions["translation1"]["flux"]["callback"] = "untrusted"
            with self.subTest(fault=fault), self.assertRaises(ValidationError):
                review.validate("fir", changed)

    def test_result_scope_order_and_backend_negatives(self):
        original = self.document("three-strain", "zero-grid.result.json")
        for fault in ("order", "scope", "owner", "shape"):
            changed = copy.deepcopy(original)
            if fault == "order":
                changed["state_ids"][0], changed["state_ids"][9] = (
                    changed["state_ids"][9],
                    changed["state_ids"][0],
                )
            elif fault == "scope":
                changed["state_scopes"][0] = "environment_total"
            elif fault == "owner":
                changed["state_owners"][0] = "medium"
            else:
                changed["state_values"][0].pop()
            with self.subTest(fault=fault), self.assertRaises(ValidationError):
                review.validate("ode-result", changed)
        for backend, fault in (
            ("python", "old_profile"),
            ("python", "constant_jacobian"),
            ("julia", "old_profile"),
            ("julia", "counter_name"),
        ):
            changed = self.document("single-cell", f"zero-grid.{backend}.manifest.json")
            if fault == "old_profile":
                changed["backend"]["profile"] = (
                    "python-scipy-ode/0.1.0"
                    if backend == "python"
                    else "julia-sciml-ode/0.1.0"
                )
            elif fault == "constant_jacobian":
                changed["backend"]["solver"]["options"]["jacobian"] = "constant_exact"
            else:
                changed["backend"]["evaluations"]["nlu"] = changed["backend"][
                    "evaluations"
                ].pop("nw")
            with (
                self.subTest(backend=backend, fault=fault),
                self.assertRaises(ValidationError),
            ):
                review.validate("run-manifest", changed)

    def test_same_shape_wrong_bindings_after_rehash(self):
        for fault in (
            "sensor",
            "transport",
            "rate_role",
            "source_value",
            "initial",
            "reaction_map",
            "result",
            "observable_scope",
        ):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as folder:
                directory = Path(folder) / "case"
                shutil.copytree(review.HERE / "examples" / "three-strain", directory)
                files = {p.name: review.read(p) for p in directory.glob("*.json")}
                design = files["design.json"]["content"]
                fir = files["fir.json"]
                if fault == "sensor":
                    design["gates"][0]["sensor"]["species"] = "signal1"
                elif fault == "transport":
                    design["transport"][0]["target"]["species"] = "signal2"
                elif fault == "rate_role":
                    design["gates"][0]["parameters"]["translation"] = design["gates"][
                        0
                    ]["parameters"]["protein_decay"]
                elif fault == "source_value":
                    next(p for p in fir["model"]["parameters"] if p["id"] == "b1")[
                        "value"
                    ] += 0.01
                elif fault == "initial":
                    fir["model"]["states"][0]["initial"] += 1
                elif fault == "reaction_map":
                    next(
                        m
                        for m in fir["provenance"]["symbol_map"]["reactions"]
                        if m["fir_reaction"] == "basal1"
                    )["source_function"] = "not2"
                elif fault == "result":
                    files["zero-grid.result.json"]["state_values"][0][0] += 1
                else:
                    files["zero-grid.result.json"]["observable_scopes"][0] = (
                        "environment_total"
                    )
                # Defeat mere self-consistency checks: rehash changed sources,
                # exact Design references and all transport checksums.
                for kind in ("design", "experiment"):
                    doc = files[kind + ".json"]
                    if kind == "experiment":
                        doc["content"]["design"]["digest"] = files["design.json"][
                            "digest"
                        ]
                    doc["digest"] = review.hashed(doc["content"])
                    fir["provenance"][kind]["digest"] = doc["digest"]
                    for backend in ("python", "julia"):
                        files[f"zero-grid.{backend}.manifest.json"]["sources"][kind][
                            "digest"
                        ] = doc["digest"]
                for name, value in files.items():
                    (directory / name).write_text(json.dumps(value, allow_nan=False))
                result_hash = hashlib.sha256(
                    (directory / "zero-grid.result.json").read_bytes()
                ).hexdigest()
                for backend in ("python", "julia"):
                    name = f"zero-grid.{backend}.manifest.json"
                    files[name]["output"]["sha256"] = result_hash
                    (directory / name).write_text(json.dumps(files[name]))
                for name, document in files.items():
                    kind = (
                        "bioir"
                        if name in ("design.json", "experiment.json")
                        else "fir"
                        if name == "fir.json"
                        else "ode-result"
                        if name.endswith("result.json")
                        else "run-manifest"
                    )
                    review.validate(kind, document)
                with self.assertRaisesRegex(
                    ValueError,
                    {
                        "sensor": "sensor binding",
                        "transport": "transport signal",
                        "rate_role": "parameter role",
                        "source_value": "parameter value",
                        "initial": "initial value",
                        "reaction_map": "reaction source role",
                        "result": "state samples",
                        "observable_scope": "observable metadata",
                    }[fault],
                ):
                    review.audit_pair(directory)

    def test_schema_success_does_not_check_raw_integer_tokens(self):
        # This accepted structural probe is NOT P10 raw-input acceptance.
        experiment = self.document("three-strain", "experiment.json")
        experiment["content"]["populations"][0]["value"] = 100.0
        review.validate("bioir", experiment)
        manifest = self.document("single-cell", "zero-grid.python.manifest.json")
        manifest["evaluations"]["nfev"] = 0.0
        review.validate("run-manifest", manifest)

    def test_schemas_need_no_external_resolution(self):
        def inspect(value):
            if isinstance(value, dict):
                if "$ref" in value:
                    self.assertTrue(value["$ref"].startswith("#"))
                for child in value.values():
                    inspect(child)
            elif isinstance(value, list):
                for child in value:
                    inspect(child)

        for path in (review.HERE / "schemas").glob("*.json"):
            inspect(review.read(path))

    def test_empty_observables_structurally_supported(self):
        for template in ("single-cell", "three-strain"):
            experiment = self.document(template, "experiment.json")
            experiment["content"]["observables"] = []
            review.validate("bioir", experiment)
            fir = self.document(template, "fir.json")
            fir["model"]["observables"] = []
            review.validate("fir", fir)
            result = self.document(template, "zero-grid.result.json")
            for key in list(result):
                if key.startswith("observable_"):
                    result[key] = [[]] if key == "observable_values" else []
            review.validate("ode-result", result)

    def test_writers_refuse_existing_directories(self):
        for script in ("candidate_schemas.py", "candidate_examples.py"):
            with self.subTest(script=script), tempfile.TemporaryDirectory() as folder:
                sentinel = Path(folder) / "do-not-replace"
                sentinel.write_text("retained")
                run = subprocess.run(
                    [sys.executable, str(review.HERE / script), "--output-dir", folder],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertNotEqual(run.returncode, 0)
                self.assertEqual(sentinel.read_text(), "retained")
                self.assertEqual(list(Path(folder).iterdir()), [sentinel])


if __name__ == "__main__":
    unittest.main()
