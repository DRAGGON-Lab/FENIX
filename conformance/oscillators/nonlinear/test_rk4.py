"""Independent laws, coordinate bases, convergence and corrupted-artifact controls."""

import copy
import json
import tempfile
import unittest
from itertools import pairwise
from pathlib import Path

import numpy as np
import rk4


class TestIndependentRK4(unittest.TestCase):
    def test_accepted_component_laws(self):
        result = rk4.component_checks()
        self.assertEqual(result["comparisons"], 414)
        self.assertLessEqual(result["max_error_to_candidate_bound"], 1)

    def test_complete_input_pin(self):
        rk4.catalog()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "cases.json"
            raw = (rk4.HERE.parent / "cases.json").read_bytes()
            path.write_bytes(raw + b"\n")
            with self.assertRaisesRegex(ValueError, "catalog bytes"):
                rk4.catalog(path)
            changed = json.loads(raw)
            changed["cases"][1]["populations"][0] += 1
            path.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError, "catalog bytes"):
                rk4.catalog(path)

    def test_fourth_order_against_analytical_translation(self):
        rk4.component_checks()  # Loads the fixed analytical module independently.
        import reference as analytical

        analytical.catalog()
        cases = json.loads((analytical.HERE / "cases.json").read_bytes())["cases"]
        case = next(c for c in cases if c["id"] == "single-translation-cascade")
        expected = np.array([float(x) for x in analytical.state(case["id"], 1)])
        errors = []
        for step in (1 / 16, 1 / 32, 1 / 64):
            _, values = rk4.integrate(case, step, 1, 1)
            errors.append(float(np.max(np.abs(values[-1] - expected))))
        for coarse, fine in pairwise(errors):
            self.assertGreater(coarse / fine, 14)
            self.assertLess(coarse / fine, 19)

    def test_invalid_domains_grids_and_budgets(self):
        case = rk4.catalog()["cases"][0]
        for step, end, sample in (
            (True, 1, 1),
            (0, 1, 1),
            (float("nan"), 1, 1),
            (0.3, 1, 1),
            (1, -1, 1),
            (1, 2_000_001, 1),
        ):
            with self.subTest(step=step, end=end), self.assertRaises(ValueError):
                rk4.integrate(case, step, end, sample)
        scale, rhs = rk4.density_field(case)
        density = np.array(case["initial_counts"]) / scale
        for fault in ("negative_sensor", "nan", "shape"):
            changed = density.copy()
            if fault == "negative_sensor":
                changed[5] = -1
            elif fault == "nan":
                changed[0] = np.nan
            else:
                changed = changed[:-1]
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                rhs(changed)
        density[0] = -1  # Linear intermediate stages may be signed under P09.
        self.assertTrue(np.all(np.isfinite(rhs(density))))
        invalid = copy.deepcopy(case)
        invalid["initial_counts"][0] = -1
        with self.assertRaisesRegex(ValueError, "initial counts"):
            rk4.integrate(invalid, 0.5, 1, 1)

    def test_density_population_weighting_and_read_only_sensing(self):
        case = copy.deepcopy(rk4.catalog()["cases"][1])
        case["populations"] = [3, 5, 7]
        case["cell_volumes_L"] = [2.0, 3.0, 5.0]
        case["medium_volume_L"] = 12.0
        scale, rhs = rk4.density_field(case)
        counts = np.arange(1.0, 19.0)
        derivative = rhs(counts / scale) * scale
        p = case["parameters"]
        for k in range(3):
            weighted = derivative[15 + k] + sum(
                case["populations"][j] * derivative[6 + 3 * j + k] for j in range(3)
            )
            expected = case["populations"][k] * p["signal_synthesis"][k] * counts[3 + k]
            expected -= sum(
                case["populations"][j]
                * p["intracellular_signal_decay"][j][k]
                * counts[6 + 3 * j + k]
                for j in range(3)
            )
            expected -= p["medium_signal_decay"][k] * counts[15 + k]
            self.assertAlmostEqual(weighted, expected, places=12)
        changed = copy.deepcopy(case)
        changed["parameters"]["induced"][0] *= 2
        delta = rk4.density_field(changed)[1](counts / scale) - rhs(counts / scale)
        self.assertGreater(delta[0], 0)
        np.testing.assert_array_equal(delta[1:], 0)
        replicated = copy.deepcopy(case)
        replicated["populations"] = [3 * n for n in case["populations"]]
        replicated["medium_volume_L"] *= 3
        replicated_scale, replicated_rhs = rk4.density_field(replicated)
        np.testing.assert_allclose(
            replicated_rhs(counts / scale), rhs(counts / scale), rtol=1e-14
        )
        self.assertEqual(replicated_scale[-1], 3 * scale[-1])

    def test_independent_crossings_and_no_cycle_control(self):
        time = np.arange(0, 100, 0.1)
        values = np.ones((len(time), 6))
        values[:, 3:] = 10 + np.sin(2 * np.pi * time[:, None] / 10)
        for row in rk4.cycle_summary(time, values, 20, 90)["proteins"]:
            self.assertAlmostEqual(row["mean_period_s"], 10, places=12)
        values[:, 3:] = 10
        for row in rk4.cycle_summary(time, values, 20, 90)["proteins"]:
            self.assertIsNone(row["mean_period_s"])
            self.assertEqual(row["midpoint_upcrossings_s"], [])

    def test_transport_corruptions_and_plausible_rehashed_wrong_values(self):
        definitions = rk4.catalog()
        definitions["protocol"].update(horizon_s=2, sample_step_s=1)
        for fault in (
            None,
            "checksum",
            "grid",
            "header",
            "metadata",
            "shape",
            "initial",
            "nan",
            "negative",
            "plausible",
            "duplicate",
            "source",
        ):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as folder:
                directory = Path(folder)
                report = {
                    "catalog_sha256": rk4.CATALOG_SHA256,
                    "evaluator_sha256": rk4.sha256(rk4.HERE.parent / "study.py"),
                    "cases": definitions["cases"],
                    "protocol": definitions["protocol"],
                    "feasibility_checks": "PASS",
                    "failures": [],
                    "runs": [],
                }
                target_key = None
                original = None
                for case in definitions["cases"]:
                    times, counts = rk4.integrate(case, 1 / 32, 4, 1)
                    for method in ("DOP853", "Radau"):
                        for refined in (False, True):
                            path = (
                                directory
                                / f"{case['id']}-{method}-{'refined' if refined else 'baseline'}.csv.gz"
                            )
                            data = np.column_stack((times, counts))
                            names = rk4.columns(case)
                            if not report["runs"]:
                                target_key = (case["id"], method, refined)
                                original = counts.copy()
                                if fault == "grid":
                                    data[1, 0] += 0.1
                                elif fault == "header":
                                    names = ["wrong", *names[1:]]
                                elif fault == "shape":
                                    data = data[:-1]
                                elif fault == "initial":
                                    data[0, 1] += 1
                                elif fault == "nan":
                                    data[1, 1] = np.nan
                                elif fault == "negative":
                                    data[1, 1] = -1
                                elif fault == "plausible":
                                    data[1, 1] += 1
                            np.savetxt(
                                path, data, delimiter=",", header=",".join(names)
                            )
                            report["runs"].append(
                                {
                                    "case": case["id"],
                                    "method": method,
                                    "refined": refined,
                                    "trajectory": {
                                        "path": path.name,
                                        "sha256": rk4.sha256(path),
                                        "samples": 5,
                                        "columns": rk4.columns(case),
                                    },
                                }
                            )
                control_ids = [
                    case["id"] + "-hill1-control" for case in definitions["cases"]
                ]
                control_ids.append(
                    definitions["cases"][1]["id"] + "-absent-signal3-control"
                )
                report["runs"] += [
                    {"case": name, "method": "Radau", "refined": True}
                    for name in control_ids
                ]
                if fault == "checksum":
                    report["runs"][0]["trajectory"]["sha256"] = "0" * 64
                elif fault == "metadata":
                    report["runs"][0]["trajectory"]["columns"][0] = "wrong"
                elif fault == "duplicate":
                    report["runs"][-1] = report["runs"][0]
                elif fault == "source":
                    report["evaluator_sha256"] = "0" * 64
                (directory / "report.json").write_text(json.dumps(report))
                if fault in (None, "plausible"):
                    _, traces = rk4.load_study(directory, definitions)
                    ratio = max(
                        rk4.scaled_errors(traces[target_key], original)[
                            "scaled_per_state"
                        ]
                    )
                    if fault is None:
                        self.assertEqual(ratio, 0)
                    else:
                        self.assertGreater(ratio, rk4.CANDIDATE_SCALED_LIMIT)
                else:
                    with self.assertRaises(ValueError):
                        rk4.load_study(directory, definitions)


if __name__ == "__main__":
    unittest.main()
