"""Independent-law and failure controls for the proposed feasibility probe."""

import copy
import hashlib
import json
import sys
import unittest
from decimal import Decimal, localcontext
from pathlib import Path
from types import SimpleNamespace

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import study


class FeasibilityTests(unittest.TestCase):
    def setUp(self):
        self.config = study.settings()
        self.case = study.reference.catalog()["cases"][0]

    def test_all_cases_methods_settings_against_independent_laws(self):
        report = study.run("test-base")
        self.assertEqual(report["bounded_reference_matrix"], "PASS")
        self.assertEqual(len(report["runs"]), 40)
        self.assertEqual(sum(len(row["comparisons"]) for row in report["runs"]), 120)
        self.assertEqual(report["tail_controls_match_prediction"], "PASS")
        self.assertEqual(len(report["tail_controls"]), 4)
        for row in report["tail_controls"]:
            self.assertEqual(row["outcome"], "STAGE_DOMAIN")
            self.assertLess(row["minimum_environment_stage"], 0)
            self.assertGreater(Decimal(row["analytical_environment_at_stop"]), 0)
            self.assertNotIn("states", row)
        self.assertEqual(report["native_implementation"], "NOT RUN")
        self.assertEqual(report["julia_stage_feasibility"], "NOT RUN")
        json.dumps(report, allow_nan=False)

    def test_rhs_and_jacobian_against_decimal_balance_equations(self):
        """High precision differences do not use the float Jacobian or RHS."""
        with localcontext() as ctx:
            ctx.prec = 100
            step = Decimal("1e-30")
            for n in range(1, 5):
                case = copy.deepcopy(self.case)
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
                for e in (0, 13, 26, 52):
                    values = list(map(Decimal, [4, 9, e, 2]))
                    kernel = study.Kernel(case, 1000)
                    actual = kernel.rhs(0, np.array(values, dtype=float))
                    expected = study.reference.rhs(case, values)
                    np.testing.assert_allclose(
                        actual, list(map(float, expected)), rtol=1e-14
                    )
                    jac = kernel.jacobian(0, np.array(values, dtype=float))
                    for column in range(4):
                        above, below = values.copy(), values.copy()
                        above[column] += step
                        below[column] -= step
                        # Differentiate the analytic formula at E=0; these are
                        # mathematical probes, never solver stages or counts.
                        plus = study.reference.rhs(case, above)
                        minus = study.reference.rhs(case, below)
                        difference = [
                            float((a - b) / (2 * step))
                            for a, b in zip(plus, minus, strict=True)
                        ]
                        np.testing.assert_allclose(
                            jac[:, column], difference, rtol=1e-13, atol=1e-25
                        )

    def test_changed_signal_weight_or_sign_is_detected(self):
        kernel = study.Kernel(self.case, 100)
        values = np.array([8.0, 2.0, 24.0, 0.0])
        derivative = kernel.rhs(0, values)
        weights = np.array([3, 5, 1, 0])
        self.assertAlmostEqual(weights @ derivative, 0)
        self.assertNotEqual(np.array([1, 1, 1, 0]) @ derivative, 0)
        derivative[2] *= -1
        self.assertNotEqual(weights @ derivative, 0)

    def test_stage_rejection_and_no_clipping(self):
        kernel = study.Kernel(self.case, 10)
        for evaluator in (kernel.rhs, kernel.jacobian):
            with self.assertRaises(study.ProbeFailure) as caught:
                evaluator(1, [0, 0, -1e-20, 0])
            self.assertEqual(caught.exception.category, "STAGE_DOMAIN")
        self.assertEqual(kernel.minimum_environment_stage, -1e-20)
        with self.assertRaises(study.ProbeFailure) as caught:
            kernel.rhs(1, [0, 0, float("nan"), 0])
        self.assertEqual(caught.exception.category, "NONFINITE_STAGE")

    def test_rhs_budget_and_backend_options(self):
        calls = []

        def backend(rhs, span, initial, **options):
            calls.append(options)
            rhs(0, initial)
            rhs(0, initial)
            self.fail("budget was not enforced")

        result = study.integrate(
            self.case, "Radau", self.config["settings"][0], 1, 1, backend=backend
        )
        self.assertEqual(result["outcome"], "WORK_LIMIT")
        self.assertEqual(result["rhs_calls"], 1)
        self.assertEqual(len(calls), 1)
        self.assertIn("jac", calls[0])
        self.assertEqual(calls[0]["method"], "Radau")
        self.assertEqual(calls[0]["rtol"], 1e-9)
        self.assertEqual(calls[0]["atol"], 1e-11)

    def test_incomplete_failed_negative_and_nonfinite_output(self):
        controls = self.config["settings"][0]
        for category, changes in (
            ("INTEGRATION_FAILURE", {"success": False}),
            ("INTEGRATION_FAILURE", {"success": False, "t": np.array([])}),
            ("INCOMPLETE_OUTPUT", {"t": np.array([0, 1])}),
            ("INCOMPLETE_OUTPUT", {"y": np.zeros((3, 3))}),
            ("NEGATIVE_OUTPUT", {"y": np.full((4, 3), -1e-30)}),
            ("NONFINITE_OUTPUT", {"y": np.full((4, 3), np.nan)}),
        ):
            with self.subTest(category=category):

                def backend(*args, changes=changes, **kwargs):
                    result = {
                        "success": True,
                        "t": np.array([0, 1, 4]),
                        "y": np.zeros((4, 3)),
                        "nfev": 0,
                        "njev": 0,
                        "nlu": 0,
                    }
                    result.update(changes)
                    return SimpleNamespace(**result)

                row = study.integrate(self.case, "DOP853", controls, 1, 100, backend)
                self.assertEqual(row["outcome"], category)
                self.assertNotIn("states", row)

    def test_comparator_detects_changed_sample(self):
        controls = self.config["settings"][0]
        row = study.integrate(self.case, "DOP853", controls, 1, 10000)
        row["states"][1][2] += 0.01
        comparisons = study.comparisons(self.case, row, self.config["state_bound"])
        self.assertFalse(comparisons[1]["within_state_bound"])
        self.assertFalse(comparisons[1]["within_balance_bound"])

    def test_balance_bound_accounts_for_initial_representation(self):
        with localcontext() as ctx:
            ctx.prec = 100
            weights = list(map(Decimal, [3, 5, 1, 0]))
            expected = [Decimal("0.1"), Decimal(0), Decimal(0), Decimal(0)]
            represented = [Decimal.from_float(0.1), Decimal(0), Decimal(0), Decimal(0)]
            error = study.weighted_initial_error(weights, represented, expected)
            self.assertGreater(error, 0)
            # Exact rational binary64 representation of 0.1 minus 1/10,
            # multiplied by the sender population 3.
            self.assertEqual(error, Decimal(3) / (Decimal(10) * Decimal(2) ** 54))
        case = copy.deepcopy(self.case)
        row = {
            "outcome": "SUCCESS",
            "states": [
                list(map(float, study.reference.state(case["id"], Decimal(t))))
                for t in case["times"]
            ],
        }
        records = study.comparisons(case, row, self.config["state_bound"])
        self.assertEqual(Decimal(records[0]["initial_representation_error"]), 0)
        # Also detect a mismatched represented initial condition when forming
        # the bound. Catalog validation rejects this as a native study input.
        case["initial"][0] = 4.000000000000001
        records = study.comparisons(case, row, self.config["state_bound"])
        self.assertGreater(Decimal(records[0]["initial_representation_error"]), 0)

    def test_retained_receipt_is_bound_to_candidate_files(self):
        receipt = json.loads((HERE / "scipy-receipt.json").read_bytes())
        self.assertEqual(receipt["settings"], self.config)
        for name, digest in receipt["files_sha256"].items():
            self.assertEqual(
                hashlib.sha256((HERE.parents[2] / name).read_bytes()).hexdigest(),
                digest,
            )


if __name__ == "__main__":
    unittest.main()
