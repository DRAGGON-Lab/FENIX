"""Independent algebra, domain and oscillation-classifier controls for P09 candidates."""

import copy
import json
import unittest
from fractions import Fraction
from pathlib import Path

import numpy as np
import study

CASES = json.loads((Path(__file__).with_name("cases.json")).read_text())["cases"]


class TestCandidateModels(unittest.TestCase):
    def test_one_gate_per_strain_and_explicit_signal_pools(self):
        case = copy.deepcopy(CASES[1])
        rhs, jac = study.field(case)
        y = np.asarray(case["initial_counts"])
        matrix = jac(0.0, y)
        self.assertEqual(matrix.shape, (18, 18))
        self.assertEqual(len(study.labels(case)), 18)
        for i in range(3):
            self.assertTrue(np.all(matrix[i, 3:6] == 0))
            expected = 6 + 3 * i + (i + 2) % 3
            dependencies = np.flatnonzero(matrix[i, 6:15]) + 6
            self.assertEqual(dependencies.tolist(), [expected])
            self.assertLess(matrix[i, expected], 0)
        changed = copy.deepcopy(case)
        changed["parameters"]["induced"][0] *= 2
        delta = study.field(changed)[0](0.0, y) - rhs(0.0, y)
        self.assertGreater(delta[0], 0)
        self.assertTrue(np.all(delta[1:] == 0), "sensing is not a signal sink")

    def test_exact_weighted_signal_balance_and_counterexample(self):
        case = copy.deepcopy(CASES[1])
        case["populations"] = [3, 5, 7]
        case["cell_volumes_L"] = [2.0, 3.0, 5.0]
        case["medium_volume_L"] = 12.0
        y = np.arange(1.0, 19.0)
        derivative = study.field(case)[0](0.0, y)
        p = case["parameters"]

        def q(value):
            return Fraction(str(value))

        for k in range(3):
            expected = (
                case["populations"][k] * q(p["signal_synthesis"][k]) * q(y[3 + k])
                - sum(
                    case["populations"][j]
                    * q(p["intracellular_signal_decay"][j][k])
                    * q(y[6 + 3 * j + k])
                    for j in range(3)
                )
                - q(p["medium_signal_decay"][k]) * q(y[15 + k])
            )
            parts = [
                case["populations"][j] * derivative[6 + 3 * j + k] for j in range(3)
            ] + [derivative[15 + k]]
            bound = (
                64
                * np.finfo(float).eps
                * max(1.0, sum(abs(x) for x in parts), abs(float(expected)))
            )
            self.assertLessEqual(abs(sum(parts) - float(expected)), bound)
            # Unweighted intracellular changes do not obey the weighted law.
            unweighted = (
                sum(derivative[6 + 3 * j + k] for j in range(3)) + derivative[15 + k]
            )
            self.assertGreater(abs(unweighted - float(expected)), 1e-3)

    def test_closed_transport_has_zero_weighted_derivative(self):
        case = copy.deepcopy(CASES[1])
        p = case["parameters"]
        p["signal_synthesis"] = [0.0, 0.0, 0.0]
        p["intracellular_signal_decay"] = [[0.0] * 3 for _ in range(3)]
        p["medium_signal_decay"] = [0.0] * 3
        case["populations"] = [3, 5, 7]
        y = np.arange(1.0, 19.0)
        dy = study.field(case)[0](0.0, y)
        for k in range(3):
            parts = [case["populations"][j] * dy[6 + 3 * j + k] for j in range(3)] + [
                dy[15 + k]
            ]
            self.assertLessEqual(
                abs(sum(parts)), 64 * np.finfo(float).eps * sum(abs(x) for x in parts)
            )

    def test_population_medium_and_count_volume_scaling(self):
        case = copy.deepcopy(CASES[1])
        y = np.arange(1.0, 19.0)
        baseline = study.field(case)[0](0.0, y)
        # Replicate the entire community: density and per-cell dynamics stay fixed.
        replicated = copy.deepcopy(case)
        replicated["populations"] = [3 * n for n in case["populations"]]
        replicated["medium_volume_L"] *= 3
        expanded = y.copy()
        expanded[15:] *= 3
        expected = baseline.copy()
        expected[15:] *= 3
        np.testing.assert_allclose(
            study.field(replicated)[0](0.0, expanded), expected, rtol=1e-14, atol=1e-14
        )
        # Enlarge all volumes and molecular amounts, preserving sensor densities.
        enlarged = copy.deepcopy(case)
        enlarged["cell_volumes_L"] = [2 * v for v in case["cell_volumes_L"]]
        enlarged["medium_volume_L"] *= 2
        for key in ("basal", "induced"):
            enlarged["parameters"][key] = [2 * x for x in case["parameters"][key]]
        np.testing.assert_allclose(
            study.field(enlarged)[0](0.0, 2 * y), 2 * baseline, rtol=1e-14, atol=1e-14
        )

    def test_analytic_jacobian_matches_independent_central_differences(self):
        for case in CASES:
            with self.subTest(case=case["id"]):
                rhs, jac = study.field(case)
                y = np.asarray(case["initial_counts"], dtype=float)
                numeric = np.zeros((len(y), len(y)))
                for column in range(len(y)):
                    h = np.cbrt(np.finfo(float).eps) * max(1.0, abs(y[column]))
                    plus, minus = y.copy(), y.copy()
                    plus[column] += h
                    minus[column] -= h
                    numeric[:, column] = (rhs(0.0, plus) - rhs(0.0, minus)) / (2 * h)
                np.testing.assert_allclose(jac(0.0, y), numeric, rtol=2e-6, atol=2e-8)

    def test_repression_limits_and_stable_extreme_ratios(self):
        for n in range(1, 5):
            actual = study.repression(
                np.array([0.0, 2.0, 4.0]), np.array([2.0, 2.0, 2.0]), np.array([n] * 3)
            )
            np.testing.assert_allclose(
                actual, [1.0, 0.5, float(Fraction(1, 1 + 2**n))], rtol=0, atol=1e-16
            )
        with np.errstate(over="raise", divide="raise", invalid="raise", under="ignore"):
            actual = study.repression(
                np.array([1e308, 1e-308, 0.0]),
                np.array([1e-308, 1e308, 1.0]),
                np.array([4, 4, 1]),
            )
        np.testing.assert_array_equal(actual, [0.0, 1.0, 1.0])
        with self.assertRaisesRegex(ValueError, "sensor"):
            study.repression(np.array([-1.0, 1.0, 1.0]), np.ones(3), np.ones(3))

    def test_absent_channel_is_an_exact_invariant(self):
        case = study.controls(CASES)[-1]
        y = np.asarray(case["initial_counts"], dtype=float)
        absent = [8, 11, 14, 17]
        np.testing.assert_array_equal(y[absent], np.zeros(4))
        np.testing.assert_array_equal(study.field(case)[0](0.0, y)[absent], np.zeros(4))
        protocol = json.loads((Path(__file__).with_name("cases.json")).read_text())[
            "protocol"
        ]
        protocol.update(horizon_s=20.0, sample_step_s=1.0)
        _, values, _ = study.simulate(case, protocol, "Radau", True, False)
        np.testing.assert_array_equal(values[:, absent], np.zeros((21, 4)))

    def test_bad_parameter_types_and_ranges_are_rejected(self):
        for key, value in (
            ("hill_n", [True, 2, 2]),
            ("basal", [True, 0.01, 0.01]),
            ("translation", [float("nan")] * 3),
            ("protein_decay", [-1.0] * 3),
        ):
            case = copy.deepcopy(CASES[0])
            case["parameters"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                study.field(case)
        case = copy.deepcopy(CASES[1])
        case["populations"] = [True, 100, 100]
        with self.assertRaises(ValueError):
            study.field(case)

    def test_classifier_distinguishes_sustained_from_damped_oscillations(self):
        protocol = json.loads((Path(__file__).with_name("cases.json")).read_text())[
            "protocol"
        ]
        times = np.arange(0.0, 2 * protocol["horizon_s"] + 5, 5.0)
        waves = np.sin(2 * np.pi * times[:, None] / 1000 - 2 * np.pi * np.arange(3) / 3)
        y = np.ones((len(times), 6))
        y[:, 3:6] = 200 + 100 * waves
        self.assertTrue(
            study.oscillation_metrics(CASES[0], protocol, times, y)[
                "sustained_candidate"
            ]
        )
        y[:, 3:6] = 200 + 100 * np.exp(-times[:, None] / 4000) * waves
        self.assertFalse(
            study.oscillation_metrics(CASES[0], protocol, times, y)[
                "sustained_candidate"
            ]
        )

    def test_catalog_rejects_changed_units_and_invalid_protocol(self):
        original = json.loads((Path(__file__).with_name("cases.json")).read_text())
        study.validate_catalog(original)
        for section, key, value in (
            ("units", "volume", "mL"),
            ("bases", "medium", "per cell"),
            ("protocol", "methods", ["Radau"]),
            ("protocol", "min_peaks", True),
            ("protocol", "sample_step_s", 3.0),
            ("protocol", "unknown", 1),
        ):
            changed = copy.deepcopy(original)
            changed[section][key] = value
            with self.subTest(section=section, key=key), self.assertRaises(ValueError):
                study.validate_catalog(changed)
        changed = copy.deepcopy(original)
        changed["cases"].pop()
        with self.assertRaises(ValueError):
            study.validate_catalog(changed)

    def test_classifier_rejects_drifting_baseline(self):
        protocol = json.loads((Path(__file__).with_name("cases.json")).read_text())[
            "protocol"
        ]
        times = np.arange(0.0, 2 * protocol["horizon_s"] + 5, 5.0)
        waves = np.sin(2 * np.pi * times[:, None] / 1000 - 2 * np.pi * np.arange(3) / 3)
        y = np.ones((len(times), 6))
        y[:, 3:6] = 200 + 0.01 * times[:, None] + 100 * waves
        metrics = study.oscillation_metrics(CASES[0], protocol, times, y)
        self.assertTrue(metrics["first_window"]["phase_separated"])
        self.assertTrue(metrics["extended_window"]["phase_separated"])
        self.assertFalse(metrics["sustained_candidate"])

    def test_rhs_budget_failure_is_explicit(self):
        protocol = json.loads((Path(__file__).with_name("cases.json")).read_text())[
            "protocol"
        ]
        protocol.update(max_nfev=1, horizon_s=20.0, sample_step_s=1.0)
        with self.assertRaisesRegex(ValueError, "budget exhausted"):
            study.simulate(CASES[0], protocol, "Radau", True, False)


if __name__ == "__main__":
    unittest.main()
