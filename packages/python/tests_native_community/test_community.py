"""Native M1 API against independently accepted literal/math references."""

import copy
import hashlib
import importlib.util
import json
import struct
import unittest
from decimal import Decimal, localcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from fenix.community import (
    FIR,
    CommunityValidationError,
    Design,
    Experiment,
    RunRecord,
    compile_experiment,
    run_experiment,
    solve_ode,
)
from fenix.community._execution import Kernel
from fenix.community._wire import decode, encode
from fenix.execution import ODEExecutionError, ODEExecutionSpec

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "spec/community/wire-candidates"
CATALOG = json.loads((FIXTURES / "catalog.json").read_bytes())
spec = importlib.util.spec_from_file_location(
    "m1_reference", ROOT / "conformance/community/reference.py"
)
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)


def load(folder):
    path = FIXTURES / folder
    design = Design.from_json((path / "design.json").read_bytes())
    experiment = Experiment.from_json(
        (path / "experiment.json").read_bytes(), design=design
    )
    return design, experiment, compile_experiment(experiment)


def controls(times=(0.0, 1.0, 4.0), method="Radau", **changes):
    return ODEExecutionSpec(
        **dict(
            time_grid=times,
            method=method,
            rtol=1e-9,
            atol=1e-11,
            max_step=1.0,
            max_nfev=200000,
            **changes,
        )
    )


def closed_limit(weights, bounds, represented_initial, reference_initial):
    initial_error = abs(
        sum(
            w * (a - b)
            for w, a, b in zip(
                weights, represented_initial, reference_initial, strict=True
            )
        )
    )
    return sum(w * b for w, b in zip(weights, bounds, strict=True)) + initial_error


class CommunityTests(unittest.TestCase):
    def test_accepted_positive_bytes_and_scoped_records(self):
        for row in CATALOG["positive"]:
            with self.subTest(packet=row["id"]):
                folder = FIXTURES / row["folder"]
                design, experiment, fir = load(row["folder"])
                self.assertEqual(fir.model_bytes(), (folder / "model.jcs").read_bytes())
                self.assertEqual(
                    fir.identity_bytes(), (folder / "identity.jcs").read_bytes()
                )
                self.assertEqual(
                    fir.digest, (folder / "digest.txt").read_text().strip()
                )
                self.assertEqual(
                    FIR.from_json(
                        (folder / "fir.json").read_bytes(), experiment=experiment
                    ).digest,
                    fir.digest,
                )
                for label in ("zero", "analytical"):
                    for language in ("python", "julia"):
                        raw = (folder / f"{label}.result.json").read_bytes()
                        manifest = (
                            folder / f"{label}.{language}.manifest.json"
                        ).read_bytes()
                        record = RunRecord.from_json(
                            raw, manifest, experiment=experiment
                        )
                        self.assertEqual(record.result_bytes, raw)
                        self.assertEqual(record.manifest_bytes, manifest)
                        self.assertEqual(
                            record.result.to_dict()["fir_digest"], fir.digest
                        )
                self.assertEqual(design.digest, design.to_dict()["digest"])

    def test_all_accepted_rejections(self):
        for row in CATALOG["rejections"]:
            with self.subTest(witness=row["id"]):
                base = FIXTURES / row["base"]
                design, experiment, _ = load(row["base"])
                raw = (FIXTURES / row["file"]).read_bytes()
                with self.assertRaises(CommunityValidationError) as caught:
                    if row["target"] == "design":
                        Design.from_json(raw)
                    elif row["target"] == "experiment":
                        Experiment.from_json(raw, design=design)
                    elif row["target"] == "fir":
                        FIR.from_json(raw, experiment=experiment)
                    else:
                        result = (
                            raw
                            if row["target"] == "result"
                            else (base / "zero.result.json").read_bytes()
                        )
                        manifest = (
                            (FIXTURES / row["manifest"]).read_bytes()
                            if row["target"] == "result"
                            else raw
                        )
                        RunRecord.from_json(result, manifest, experiment=experiment)
                self.assertEqual(
                    (caught.exception.category, caught.exception.path),
                    (row["category"], row["path"]),
                )

    def test_lexical_and_binary64_transport_projections(self):
        for row in CATALOG["raw_numbers"]:
            with self.subTest(lexical=row["id"]):
                raw = (FIXTURES / row["file"]).read_bytes()
                if row["category"]:
                    with self.assertRaises(CommunityValidationError) as caught:
                        decode(raw, row["policy"])
                    self.assertEqual(caught.exception.category, row["category"])
                else:
                    actual = decode(raw, row["policy"])
                    self.assertEqual(actual, row["value"])
                    if isinstance(row["value"]["value"], float):
                        self.assertEqual(
                            struct.pack(">d", actual["value"]),
                            struct.pack(">d", row["value"]["value"]),
                        )
        for row in json.loads((FIXTURES / "transport-vectors.json").read_bytes()):
            with self.subTest(transport=row["id"]):
                if "category" in row:
                    with self.assertRaises(CommunityValidationError) as caught:
                        decode(row["raw"], row["kind"])
                    self.assertEqual(
                        (caught.exception.category, caught.exception.path),
                        (row["category"], row["error_path"]),
                    )
                else:
                    value = decode(row["raw"], row["kind"])
                    for key in row["path"]:
                        value = value[key]
                    if "bits" in row:
                        self.assertEqual(struct.pack(">d", value).hex(), row["bits"])
                    else:
                        self.assertEqual(str(value), row["decimal"])
        # Integer-form work counters remain exact beyond binary64 and Python's
        # default decimal integer-string conversion limit.
        huge = 10**5000 + 1
        self.assertEqual(
            decode(encode({"execution": {"max_nfev": huge}}), "manifest")["execution"][
                "max_nfev"
            ],
            huge,
        )

    def test_grid_witnesses_after_binary64_conversion(self):
        _, experiment, _ = load("threshold-n1")
        folder = FIXTURES / "threshold-n1"
        for row in json.loads((FIXTURES / "grid-vectors.json").read_bytes()):
            result = json.loads((folder / "zero.result.json").read_bytes())
            manifest = json.loads((folder / "zero.python.manifest.json").read_bytes())
            result["times"] = row["times"]
            for key in ("state_values", "observable_values"):
                result[key] = result[key] * len(row["times"])
            raw = encode(result).encode()
            manifest["execution"]["time_grid"] = row["manifest"]
            zero = len(row["times"]) == 1 and row["times"][0] == 0
            manifest["integration"] = "skipped_zero_grid" if zero else "performed"
            manifest["evaluations"]["nfev"] = 0 if zero else 1
            manifest["output"]["sha256"] = hashlib.sha256(raw).hexdigest()
            if row["accepted"]:
                RunRecord.from_json(raw, encode(manifest), experiment=experiment)
            else:
                with self.assertRaises(CommunityValidationError):
                    RunRecord.from_json(raw, encode(manifest), experiment=experiment)

    def test_jacobian_and_rhs_against_independent_decimal_equations(self):
        design, experiment, _ = load("threshold-n1")
        order = ["env.signal", "receiver.reporter", "receiver.signal", "sender.signal"]
        ref_order = reference.catalog()["state_ids"]
        permutation = [ref_order.index(state) for state in order]
        with localcontext() as context:
            context.prec = 100
            step = Decimal("1e-30")
            for n in range(1, 5):
                case = copy.deepcopy(reference.catalog()["cases"][0])
                case["populations"] = [7, 11]
                case["volumes"] = [2, 5, 13]
                case["parameters"].update(
                    hill_n=n,
                    sender_export=3,
                    receiver_export=2,
                    sender_import=5,
                    receiver_import=7,
                    sender_decay=2,
                    receiver_decay=3,
                    env_decay=1,
                    sender_production=4,
                    reporter_basal=3,
                    reporter_induced=7,
                    reporter_decay=2,
                )
                d = design.to_dict()["content"]
                for owner in d["owners"]:
                    owner["volume"]["value"] = dict(
                        zip(("sender", "receiver", "env"), case["volumes"], strict=True)
                    )[owner["role"]]
                new_design = Design.from_content(d)
                e = experiment.to_dict()["content"]
                e["design"] = new_design.reference
                e["populations"] = dict(
                    zip(("sender", "receiver"), case["populations"], strict=True)
                )
                for key, value in case["parameters"].items():
                    e["parameters"][key]["value"] = value
                fir = compile_experiment(Experiment.from_content(e, design=new_design))
                kernel = Kernel(fir, controls())
                for env in (0, 13, 26, 52):
                    values = list(map(Decimal, [4, 9, env, 2]))
                    canonical = np.array([float(values[i]) for i in permutation])
                    expected = reference.rhs(case, values)
                    np.testing.assert_allclose(
                        kernel.rhs(0.0, canonical),
                        [float(expected[i]) for i in permutation],
                        rtol=1e-14,
                    )
                    jac = kernel.jacobian(0.0, canonical)
                    for column, ref_column in enumerate(permutation):
                        above, below = values.copy(), values.copy()
                        above[ref_column] += step
                        below[ref_column] -= step
                        plus, minus = (
                            reference.rhs(case, above),
                            reference.rhs(case, below),
                        )
                        diff = [
                            float((plus[i] - minus[i]) / (2 * step))
                            for i in permutation
                        ]
                        np.testing.assert_allclose(
                            jac[:, column], diff, rtol=1e-13, atol=1e-25
                        )

    def test_nonfinite_jacobian_intermediate_rejects(self):
        design, experiment, _ = load("threshold-n1")
        d = design.to_dict()["content"]
        for owner in d["owners"]:
            if owner["role"] == "env":
                owner["volume"]["value"] = 1e308
        design = Design.from_content(d)
        e = experiment.to_dict()["content"]
        e["design"] = design.reference
        for entry in e["initial_counts"].values():
            entry["value"] = 0
        for key, entry in e["parameters"].items():
            entry["value"] = (
                1e308
                if key == "threshold"
                else 1
                if key in ("hill_n", "reporter_basal")
                else 0
            )
        fir = compile_experiment(Experiment.from_content(e, design=design))
        with self.assertRaises(ODEExecutionError) as caught:
            solve_ode(fir, controls(times=(0.0, 1.0)))
        self.assertEqual(caught.exception.category, "NONFINITE")
        # Validation followed by a zero-only skip does not evaluate derivatives.
        self.assertEqual(solve_ode(fir, controls(times=(0.0,))).nfev, 0)

    def test_failed_and_corrupted_backend_returns(self):
        _, _, fir = load("threshold-n1")
        settings = controls()
        for defect, category in (
            ("failed", "INTEGRATION_FAILURE"),
            ("incomplete", "INCOMPLETE_OUTPUT"),
            ("negative", "NEGATIVE_OUTPUT"),
            ("nonfinite", "NONFINITE"),
        ):
            output = SimpleNamespace(
                success=True,
                t=np.array(settings.time_grid),
                y=np.ones((4, 3)),
                nfev=1,
                njev=0,
                nlu=0,
            )
            if defect == "failed":
                output.success = False
            if defect == "incomplete":
                output.t = output.t[:-1]
            if defect == "negative":
                output.y[0, 1] = -1
            if defect == "nonfinite":
                output.y[0, 1] = np.nan
            with (
                patch("fenix.community._execution.solve_ivp", return_value=output),
                self.assertRaises(ODEExecutionError) as caught,
            ):
                solve_ode(fir, settings)
            self.assertEqual(caught.exception.category, category)

    def test_immutable_sources_and_revision_rules(self):
        design, experiment, fir = load("threshold-n1")
        data = design.to_dict()
        data["content"]["owners"][0]["volume"]["value"] = -1
        self.assertNotEqual(data, design.to_dict())
        with self.assertRaises(AttributeError):
            design._text = "corrupted"
        content = design.to_dict()["content"]
        content["owners"][0]["volume"]["value"] = 4
        with self.assertRaises(CommunityValidationError):
            design.replace_content(content)
        content["revision"] = 2
        successor = design.replace_content(content)
        with self.assertRaises(CommunityValidationError):
            Experiment.from_json(experiment.to_json(), design=successor)
        self.assertEqual(
            FIR.from_json(fir.to_json(), experiment=experiment).digest, fir.digest
        )

    def test_coupled_methods_against_independent_laws(self):
        reference.validate_catalog(reference.catalog())
        with localcontext() as context:
            context.prec = 160
            for case in reference.catalog()["cases"]:
                _, experiment, fir = load(case["id"])
                for method in ("DOP853", "Radau"):
                    for rtol, atol in ((1e-9, 1e-11), (1e-11, 1e-13)):
                        with self.subTest(case=case["id"], method=method, rtol=rtol):
                            execution = ODEExecutionSpec(
                                time_grid=(0.0, 1.0, 4.0),
                                method=method,
                                rtol=rtol,
                                atol=atol,
                                max_step=1.0,
                                max_nfev=200000,
                            )
                            trajectory = solve_ode(fir, execution)
                            for time, row in zip(
                                trajectory.times, trajectory.state_values, strict=True
                            ):
                                expected = reference.state(case["id"], Decimal(time))
                                values = [
                                    Decimal.from_float(
                                        row[trajectory.state_ids.index(state)]
                                    )
                                    for state in reference.catalog()["state_ids"]
                                ]
                                bounds = [
                                    Decimal("1e-9") + Decimal("1e-8") * abs(x)
                                    for x in expected
                                ]
                                self.assertTrue(
                                    all(
                                        abs(a - b) <= bound
                                        for a, b, bound in zip(
                                            values, expected, bounds, strict=True
                                        )
                                    )
                                )
                                if all(
                                    case["parameters"][name] == 0
                                    for name in (
                                        "sender_production",
                                        "sender_decay",
                                        "receiver_decay",
                                        "env_decay",
                                    )
                                ):
                                    weights = [
                                        *map(Decimal, case["populations"]),
                                        Decimal(1),
                                        Decimal(0),
                                    ]
                                    initial = [
                                        Decimal.from_float(float(value))
                                        for value in case["initial"]
                                    ]
                                    reference_initial = reference.state(
                                        case["id"], Decimal(0)
                                    )
                                    drift = abs(
                                        sum(
                                            w * (v - i)
                                            for w, v, i in zip(
                                                weights, values, initial, strict=True
                                            )
                                        )
                                    )
                                    self.assertLessEqual(
                                        drift,
                                        closed_limit(
                                            weights, bounds, initial, reference_initial
                                        ),
                                    )
                            self.assertEqual(
                                fir.digest, compile_experiment(experiment).digest
                            )

    def test_nonzero_initial_representation_term(self):
        with localcontext() as context:
            context.prec = 100
            # Exact binary64 0.1 discrepancy, independently expanded in base 10.
            limit = closed_limit(
                [Decimal(3)], [Decimal(0)], [Decimal.from_float(0.1)], [Decimal("0.1")]
            )
            self.assertEqual(
                limit, Decimal("1.66533453693773481063544750213623046875e-17")
            )
            self.assertGreater(limit, 0)

    def test_malformed_unicode_readback_is_a_validation_error(self):
        _, experiment, _ = load("threshold-n1")
        for raw_result, raw_manifest in (("\ud800", b"{}"), (b"{}", "\ud800")):
            with self.assertRaises(CommunityValidationError) as caught:
                RunRecord.from_json(raw_result, raw_manifest, experiment=experiment)
            self.assertEqual(caught.exception.category, "UNICODE")

    def test_invalid_capture_metadata_rejects_before_solving(self):
        _, experiment, _ = load("threshold-n1")
        for invalid in ("", False, [], "\ud800"):
            with (
                patch(
                    "fenix.community._results.solve_ode",
                    side_effect=AssertionError("invalid capture solved"),
                ),
                self.assertRaises(CommunityValidationError),
            ):
                run_experiment(experiment, controls(), build_id=invalid)

    def test_late_first_and_empty_observables_capture(self):
        for folder in ("late-first", "empty-observables"):
            _, experiment, _ = load(folder)
            record = run_experiment(experiment, controls(times=(1.0, 4.0)))
            result = record.result.to_dict()
            catalog_row = next(
                row for row in CATALOG["positive"] if row["folder"] == folder
            )
            with localcontext() as context:
                context.prec = 160
                for time, values in zip(
                    result["times"], result["state_values"], strict=True
                ):
                    expected = reference.state(
                        catalog_row["reference_case"], Decimal(time)
                    )
                    for state, value in zip(result["state_ids"], values, strict=True):
                        target = expected[reference.catalog()["state_ids"].index(state)]
                        self.assertLessEqual(
                            abs(Decimal.from_float(value) - target),
                            Decimal("1e-9") + Decimal("1e-8") * abs(target),
                        )
            if folder == "empty-observables":
                self.assertEqual(result["observable_values"], [[], []])

    def test_capture_once_and_readback_without_solver(self):
        _, experiment, _ = load("two-strain-transient")
        with (
            patch("fenix.community._results.solve_ode", wraps=solve_ode) as solver,
            patch(
                "fenix.community._results.compile_experiment", wraps=compile_experiment
            ) as compiler,
        ):
            record = run_experiment(experiment, controls(), build_id="observed-build")
            self.assertEqual(solver.call_count, 1)
            self.assertEqual(compiler.call_count, 1)
        with patch(
            "fenix.community._results.solve_ode",
            side_effect=AssertionError("readback solved"),
        ):
            reread = RunRecord.from_json(
                record.result_bytes,
                record.manifest_bytes,
                experiment=experiment,
                expected_manifest_sha256=hashlib.sha256(
                    record.manifest_bytes
                ).hexdigest(),
            )
        self.assertEqual(reread.result_bytes, record.result_bytes)
        with self.assertRaises(CommunityValidationError):
            RunRecord.from_json(
                record.result_bytes,
                record.manifest_bytes,
                experiment=experiment,
                expected_manifest_sha256="0" * 64,
            )

    def test_zero_grid_large_budget_signed_zero_and_empty_observables(self):
        for folder in ("threshold-n1", "empty-observables"):
            _, experiment, _ = load(folder)
            settings = ODEExecutionSpec(
                time_grid=(-0.0,),
                method="Radau",
                rtol=1e-9,
                atol=1e-11,
                max_step=1.0,
                max_nfev=9007199254740993,
            )
            with patch(
                "fenix.community._execution.solve_ivp",
                side_effect=AssertionError("zero grid integrated"),
            ):
                record = run_experiment(experiment, settings)
            self.assertEqual(
                record.manifest.to_dict()["execution"]["max_nfev"], 9007199254740993
            )
            self.assertEqual(
                struct.pack(">d", record.result.to_dict()["times"][0]),
                struct.pack(">d", -0.0),
            )
            self.assertEqual(record.manifest.to_dict()["evaluations"]["nfev"], 0)

    def test_budget_and_strict_tail_failure(self):
        _, _, fir = load("driven-n1")
        with self.assertRaises(ODEExecutionError) as caught:
            solve_ode(
                fir,
                ODEExecutionSpec(
                    time_grid=(0.0, 4.0),
                    method="Radau",
                    rtol=1e-9,
                    atol=1e-11,
                    max_step=1.0,
                    max_nfev=1,
                ),
            )
        self.assertEqual(caught.exception.category, "WORK_LIMIT")
        for method in ("DOP853", "Radau"):
            with self.assertRaises(ODEExecutionError) as caught:
                solve_ode(
                    fir,
                    ODEExecutionSpec(
                        time_grid=(0.0, 1000.0),
                        method=method,
                        rtol=1e-9,
                        atol=1e-11,
                        max_step=10.0,
                        max_nfev=200000,
                    ),
                )
            self.assertEqual(caught.exception.category, "STAGE_DOMAIN")


if __name__ == "__main__":
    unittest.main()
