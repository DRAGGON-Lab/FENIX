"""Native P04 execution against approved references and explicit failure controls."""

import dataclasses
import json
import math
import struct
import sys
import unittest
from decimal import Decimal, localcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from test_compiler import committed
from test_fir import model

from fenix.compiler import compile_experiment
from fenix.execution import (
    ExecutionValidationError,
    ODEExecutionError,
    ODEExecutionSpec,
    ODETrajectory,
    solve_ode,
)
from fenix.fir import FIRDocument, FIRModel, FIRValidationError

ROOT = Path(__file__).resolve().parents[3]


def settings(**changes):
    values = {
        "time_grid": (0.0, 1.0),
        "method": "DOP853",
        "rtol": 1e-10,
        "atol": 1e-12,
        "max_step": 1.0,
        "max_nfev": 100000,
    }
    values.update(changes)
    return ODEExecutionSpec(**values)


def resolved(alpha=10.0, beta=0.1, initial=0.5, *, empty=False):
    raw = model()
    raw["parameters"][0]["value"] = alpha
    raw["parameters"][1]["value"] = beta
    raw["states"][0]["initial"] = initial
    if empty:
        raw["observables"] = []
    return FIRModel.from_dict(raw)


def backend_result(**changes):
    values = {
        "success": True,
        "status": 0,
        "message": "complete",
        "t": np.array([0.0, 1.0]),
        "y": np.array([[0.5, 1.0]]),
        "nfev": 0,
        "njev": 0,
        "nlu": 0,
    }
    values.update(changes)
    return SimpleNamespace(**values)


def decode(bits):
    return struct.unpack(">d", bytes.fromhex(bits))[0]


class TestExecution(unittest.TestCase):
    def assert_reference(self, actual, expected):
        with localcontext() as context:
            context.prec = 100
            reference = Decimal(expected)
            error = abs(Decimal.from_float(actual) - reference)
            self.assertLessEqual(
                error, Decimal("1e-9") + Decimal("1e-8") * abs(reference)
            )

    def test_both_methods_match_all_40_approved_samples_at_two_settings(self):
        catalog = json.loads(
            (ROOT / "conformance/production_decay/catalog.json").read_bytes()
        )
        self.assertEqual(catalog["status"], "APPROVED")
        for method in ("DOP853", "Radau"):
            for rtol, atol, max_step in ((1e-10, 1e-12, 1.0), (1e-11, 1e-13, 0.5)):
                count = 0
                for case in catalog["cases"]:
                    with self.subTest(method=method, rtol=rtol, case=case["id"]):
                        parameters = {
                            k: decode(v) for k, v in case["parameters"].items()
                        }
                        samples = sorted(
                            case["samples"], key=lambda s: decode(s["time_bits"])
                        )
                        grid = tuple(decode(s["time_bits"]) for s in samples)
                        result = solve_ode(
                            resolved(
                                parameters["alpha"],
                                parameters["beta"],
                                parameters["x0"],
                            ),
                            settings(
                                time_grid=grid,
                                method=method,
                                rtol=rtol,
                                atol=atol,
                                max_step=max_step,
                            ),
                        )
                        self.assertEqual(result.times, grid)
                        for row, sample in zip(
                            result.state_values, samples, strict=True
                        ):
                            self.assert_reference(row[0], sample["expected"])
                            count += 1
                self.assertEqual(count, 40)

    def test_zero_only_grid_avoids_backend_and_preserves_signed_zero(self):
        m = resolved(initial=5e-324)
        for method in ("DOP853", "Radau"):
            with patch("fenix.execution.solve_ivp") as backend:
                result = solve_ode(m, settings(time_grid=(-0.0,), method=method))
            backend.assert_not_called()
            self.assertEqual(result.state_values, ((5e-324,),))
            self.assertEqual(result.nfev, 0)
            self.assertEqual(math.copysign(1.0, result.times[0]), -1.0)

    def test_late_first_sample_integrates_from_zero(self):
        for method in ("DOP853", "Radau"):
            result = solve_ode(
                resolved(2.0, 0.0, 0.5), settings(time_grid=(1.0, 10.0), method=method)
            )
            self.assertEqual(result.times, (1.0, 10.0))
            for row, expected in zip(result.state_values, ("2.5", "20.5"), strict=True):
                self.assert_reference(row[0], expected)

    def test_malformed_grids_are_not_sorted_or_coerced(self):
        grids = [
            (),
            [],
            (1.0, 0.0),
            (0.0, 0.0),
            (-0.0, 0.0),
            (-1.0,),
            (float("nan"),),
            (float("inf"),),
            (True,),
            (1,),
            ("1",),
            (np.float64(1.0),),
        ]
        for grid in grids:
            with (
                self.subTest(grid=grid),
                self.assertRaises(ExecutionValidationError) as caught,
            ):
                settings(time_grid=grid)
            self.assertEqual(caught.exception.category, "EXECUTION_SPEC")
            self.assertTrue(caught.exception.path.startswith("/time_grid"))

    def test_invalid_numeric_settings_and_budget(self):
        for name in ("rtol", "atol", "max_step"):
            for value in (
                0.0,
                -1.0,
                1,
                True,
                "1",
                float("inf"),
                float("nan"),
                np.float64(1.0),
            ):
                with (
                    self.subTest(name=name, value=value),
                    self.assertRaises(ExecutionValidationError) as caught,
                ):
                    settings(**{name: value})
                self.assertEqual(
                    (caught.exception.category, caught.exception.path),
                    ("EXECUTION_SPEC", "/" + name),
                )
        with self.assertRaises(ExecutionValidationError):
            settings(rtol=100 * 2**-52 / 2)
        self.assertEqual(settings(rtol=100 * 2**-52).rtol, 100 * 2**-52)
        for budget in (0, -1, True, 1.0, "1", None):
            with (
                self.subTest(budget=budget),
                self.assertRaises(ExecutionValidationError) as caught,
            ):
                settings(max_nfev=budget)
            self.assertEqual(
                (caught.exception.category, caught.exception.path),
                ("EXECUTION_SPEC", "/max_nfev"),
            )

    def test_method_and_profile_rejection_even_for_zero_grid(self):
        for method in ("RK45", "radau", "", True, None):
            with (
                self.subTest(method=method),
                self.assertRaises(ExecutionValidationError) as caught,
            ):
                settings(method=method)
            self.assertEqual(
                (caught.exception.category, caught.exception.path),
                ("UNSUPPORTED_METHOD", "/method"),
            )
        for grid in ((0.0,), (0.0, 1.0)):
            for profile in ("ssa", "unknown"):
                with patch("fenix.execution.solve_ivp") as backend:
                    with self.assertRaises(FIRValidationError) as caught:
                        solve_ode(resolved(), settings(time_grid=grid, profile=profile))
                backend.assert_not_called()
                self.assertEqual(
                    (caught.exception.category, caught.exception.path),
                    ("UNSUPPORTED_PROFILE", "/profile"),
                )

    def test_only_validated_exact_native_input_types(self):
        m = resolved()
        for value in (
            None,
            m.to_dict(),
            m.to_json(),
            FIRDocument.from_dict({"model": m.to_dict()}),
        ):
            with self.subTest(value=type(value)), self.assertRaises(TypeError):
                solve_ode(value, settings())
        for value in (None, {}, "ode"):
            with self.assertRaises(TypeError):
                solve_ode(m, value)

    def test_real_work_budget_exhaustion_counts_at_most_limit(self):
        for method in ("DOP853", "Radau"):
            spec = settings(method=method, max_nfev=1)
            with self.assertRaises(ODEExecutionError) as caught:
                solve_ode(resolved(), spec)
            self.assertEqual(caught.exception.category, "WORK_LIMIT")
            self.assertEqual(caught.exception.nfev, 1)
            self.assertEqual(caught.exception.spec, spec)

    def test_real_overflow_is_numerical_failure_not_model_repair(self):
        m = resolved(0.0, sys.float_info.max, sys.float_info.max)
        before = (m.to_dict(), m.identity_bytes(), m.digest)
        for method in ("DOP853", "Radau"):
            with self.assertRaises(ODEExecutionError) as caught:
                solve_ode(m, settings(method=method))
            self.assertEqual(caught.exception.category, "NONFINITE")
            self.assertEqual((m.to_dict(), m.identity_bytes(), m.digest), before)

    def test_real_subnormal_underflow_does_not_introduce_a_floor(self):
        m = resolved(0.0, 0.5, 5e-324)
        for method in ("DOP853", "Radau"):
            result = solve_ode(m, settings(method=method))
            self.assertEqual(result.state_values[0], (5e-324,))
            self.assertTrue(
                all(
                    math.isfinite(row[0]) and 0.0 <= row[0] <= 5e-324
                    for row in result.state_values
                )
            )
            self.assertEqual(m.to_dict()["states"][0]["initial"], 5e-324)

    def test_negative_samples_fail_without_clipping(self):
        for value in (-5e-324, -1e-15, -1.0):
            with (
                self.subTest(value=value),
                patch(
                    "fenix.execution.solve_ivp",
                    return_value=backend_result(y=np.array([[0.5, value]])),
                ),
            ):
                with self.assertRaises(ODEExecutionError) as caught:
                    solve_ode(resolved(), settings())
            self.assertEqual(caught.exception.category, "NEGATIVE_STATE")

    def test_signed_zero_and_finite_subnormal_output_are_preserved(self):
        for value in (-0.0, 5e-324):
            with patch(
                "fenix.execution.solve_ivp",
                return_value=backend_result(y=np.array([[0.5, value]])),
            ):
                result = solve_ode(resolved(), settings())
            self.assertEqual(result.state_values[-1][0], value)
            self.assertEqual(
                math.copysign(1.0, result.state_values[-1][0]),
                math.copysign(1.0, value),
            )

    def test_sampled_outputs_require_float64_without_coercion(self):
        for method in ("DOP853", "Radau"):
            for dtype in (np.float32, np.float64):
                # Exactly representable in both types: only the dtype differs.
                values = np.array([[0.5, 1.0]], dtype=dtype)
                with (
                    self.subTest(method=method, dtype=dtype),
                    patch(
                        "fenix.execution.solve_ivp",
                        return_value=backend_result(y=values),
                    ),
                ):
                    if dtype is np.float32:
                        with self.assertRaises(ODEExecutionError) as caught:
                            solve_ode(resolved(), settings(method=method))
                        self.assertEqual(caught.exception.category, "INVALID_OUTPUT")
                    else:
                        result = solve_ode(resolved(), settings(method=method))
                        self.assertEqual(result.state_values, ((0.5,), (1.0,)))
                self.assertEqual(values.dtype, np.dtype(dtype))

    def test_nonfinite_sampled_outputs_fail(self):
        for value in (float("nan"), float("inf"), -float("inf")):
            with (
                self.subTest(value=value),
                patch(
                    "fenix.execution.solve_ivp",
                    return_value=backend_result(y=np.array([[0.5, value]])),
                ),
            ):
                with self.assertRaises(ODEExecutionError) as caught:
                    solve_ode(resolved(), settings())
            self.assertEqual(caught.exception.category, "NONFINITE")

    def test_failed_status_is_not_partial_success(self):
        for changed in (
            {"success": False, "status": -1},
            {"success": True, "status": 1},
        ):
            with patch(
                "fenix.execution.solve_ivp", return_value=backend_result(**changed)
            ):
                with self.assertRaises(ODEExecutionError) as caught:
                    solve_ode(resolved(), settings())
            self.assertEqual(caught.exception.category, "SOLVER_FAILURE")

    def test_incomplete_misaligned_and_malformed_outputs_fail(self):
        cases = [
            {"t": np.array([0.0])},
            {"t": np.array([0.0, 0.5])},
            {"t": np.array([0.0, float("nan")])},
            {"y": np.array([[0.5]])},
            {"y": np.array([0.5, 1.0])},
            {"y": np.array([[0.5, 1.0], [0.5, 1.0]])},
        ]
        for changed in cases:
            with (
                self.subTest(changed=changed),
                patch(
                    "fenix.execution.solve_ivp", return_value=backend_result(**changed)
                ),
            ):
                with self.assertRaises(ODEExecutionError) as caught:
                    solve_ode(resolved(), settings())
            self.assertIn(caught.exception.category, ("INVALID_OUTPUT", "NONFINITE"))

    def test_programming_errors_are_not_hidden_as_numerical_failure(self):
        with patch(
            "fenix.execution.solve_ivp", side_effect=RuntimeError("programming defect")
        ):
            with self.assertRaisesRegex(RuntimeError, "programming defect"):
                solve_ode(resolved(), settings())

    def test_compiled_sources_and_fir_identity_remain_unchanged(self):
        document = compile_experiment(committed())
        before = (
            document.to_dict(),
            document.model.canonical_model_bytes(),
            document.model.identity_bytes(),
            document.digest,
        )
        for method in ("DOP853", "Radau"):
            result = solve_ode(document.model, settings(method=method))
            self.assertEqual(result.fir_digest, document.digest)
            self.assertEqual(
                (
                    document.to_dict(),
                    document.model.canonical_model_bytes(),
                    document.model.identity_bytes(),
                    document.digest,
                ),
                before,
            )

    def test_declaration_order_is_resolved_by_ids(self):
        raw = model()
        reference = FIRModel.from_dict(raw)
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
        self.assertEqual(reference.digest, permuted.digest)
        a = solve_ode(reference, settings())
        b = solve_ode(permuted, settings())
        for left, right in zip(a.state_values, b.state_values, strict=True):
            self.assert_reference(left[0], Decimal.from_float(right[0]))
        a_observations = dict(
            zip(a.observable_ids, zip(*a.observable_values, strict=True), strict=True)
        )
        b_observations = dict(
            zip(b.observable_ids, zip(*b.observable_values, strict=True), strict=True)
        )
        self.assertEqual(a_observations.keys(), b_observations.keys())
        for name in a_observations:
            for left, right in zip(
                a_observations[name], b_observations[name], strict=True
            ):
                self.assert_reference(left, Decimal.from_float(right))

    def test_empty_and_named_observables_and_units(self):
        for empty in (False, True):
            result = solve_ode(resolved(empty=empty), settings())
            self.assertEqual(result.state_ids, ("x",))
            self.assertEqual(result.state_units, ("molecule",))
            self.assertEqual(result.time_unit, "s")
            self.assertEqual(set(result.observable_ids), set() if empty else {"z", "a"})
            self.assertEqual(
                result.observable_units, () if empty else ("molecule", "molecule")
            )
            for state, observations in zip(
                result.state_values, result.observable_values, strict=True
            ):
                self.assertEqual(observations, () if empty else (state[0], state[0]))

    def test_results_settings_are_immutable_and_record_backend_versions(self):
        spec = settings()
        result = solve_ode(resolved(), spec)
        self.assertIsInstance(result, ODETrajectory)
        self.assertEqual(result.spec, spec)
        self.assertEqual(set(dict(result.backend_versions)), {"numpy", "scipy"})
        self.assertTrue(
            all(
                isinstance(version, str) and version
                for _, version in result.backend_versions
            )
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            spec.rtol = 0.5
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.times = ()
        with self.assertRaises(TypeError):
            result.state_values[0][0] = 4.0

    def test_repeated_runs_are_checked_by_bounds_not_bytes(self):
        first = solve_ode(resolved(), settings())
        second = solve_ode(resolved(), settings())
        self.assertEqual(first.times, second.times)
        self.assertEqual(first.spec, second.spec)
        for a, b in zip(first.state_values, second.state_values, strict=True):
            self.assert_reference(a[0], Decimal.from_float(b[0]))

    def test_stiff_radau_and_deliberate_dop853_work_limit(self):
        m = resolved(2000000.0, 1000000.0, 5.0)
        grid = (0.0, 1e-6, 1e-4, 1.0)
        result = solve_ode(m, settings(method="Radau", time_grid=grid))
        with localcontext() as context:
            context.prec = 100
            for time, row in zip(grid, result.state_values, strict=True):
                reference = (
                    Decimal(2)
                    + Decimal(3) * (-Decimal(1000000) * Decimal.from_float(time)).exp()
                )
                self.assert_reference(row[0], reference)
        with self.assertRaises(ODEExecutionError) as caught:
            solve_ode(m, settings(time_grid=grid, max_nfev=2000))
        self.assertEqual(caught.exception.category, "WORK_LIMIT")
        self.assertEqual(caught.exception.nfev, 2000)


if __name__ == "__main__":
    unittest.main()
