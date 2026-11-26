"""Artifact and failure-path checks, using stub integrations rather than new oracles."""

import contextlib
import gzip
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import study

CATALOG = json.loads((study.HERE / "cases.json").read_bytes())


class TestStudyEvidence(unittest.TestCase):
    def test_incomplete_and_invalid_solver_outputs_are_rejected(self):
        case = CATALOG["cases"][0]
        protocol = dict(CATALOG["protocol"], horizon_s=2, sample_step_s=1)
        for fault in ("failure", "short", "grid", "nan", "negative"):
            result = SimpleNamespace(
                success=True,
                t=np.arange(3.0),
                y=np.ones((6, 3)),
                nfev=0,
                njev=0,
                nlu=0,
            )
            if fault == "failure":
                result.success = False
            elif fault == "short":
                result.y = result.y[:, :-1]
            elif fault == "grid":
                result.t[1] = 0.5
            elif fault == "nan":
                result.y[0, 1] = np.nan
            else:
                result.y[0, 1] = -1e-20
            with (
                self.subTest(fault=fault),
                patch("study.solve_ivp", return_value=result),
                self.assertRaises(ValueError),
            ):
                study.simulate(case, protocol, "Radau", True, False)

    def test_all_runs_retain_traces_and_controls_fail_closed(self):
        # Test orchestration independently of integration/classifier correctness,
        # which the existing mathematical and classifier suites exercise.
        for fault in (None, "oscillatory", "integration"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as folder:
                output = Path(folder) / "evidence"
                control_ids = {c["id"] for c in study.controls(CATALOG["cases"])}

                def simulate(case, *args, fault=fault, control_ids=control_ids):
                    if fault == "integration" and case["id"] in control_ids:
                        raise ValueError("incomplete integration")
                    return np.arange(3.0), np.ones((3, len(case["initial_counts"]))), {}

                def metrics(case, *args, fault=fault, control_ids=control_ids):
                    window = {
                        "proteins": [
                            {
                                "oscillatory_window": True,
                                "period_s": 1.0,
                                "prominence_molecules_per_cell": 1.0,
                            }
                        ]
                        * 3,
                        "phase_cycles": [0.0, 1 / 3, 2 / 3],
                    }
                    return {
                        "extended_window": window,
                        "sustained_candidate": fault == "oscillatory"
                        or case["id"] not in control_ids,
                    }

                with (
                    patch("sys.argv", ["study", "--output-dir", str(output)]),
                    patch("study.simulate", side_effect=simulate),
                    patch("study.oscillation_metrics", side_effect=metrics),
                    patch("study.plot_candidates"),
                    patch("study.plot_controls") as plots,
                    contextlib.redirect_stdout(io.StringIO()),
                ):
                    self.assertEqual(study.main(), fault is not None)
                report = json.loads((output / "report.json").read_bytes())
                self.assertEqual(
                    report["feasibility_checks"], "FAIL" if fault else "PASS"
                )
                self.assertEqual(len(report["failures"]), 3 if fault else 0)
                expected_runs = 8 if fault == "integration" else 11
                self.assertEqual(len(report["runs"]), expected_runs)
                self.assertEqual(len(list(output.glob("*.csv.gz"))), expected_runs)
                self.assertEqual(plots.call_count, 0 if fault == "integration" else 1)
                for run in report["runs"]:
                    artifact = run["trajectory"]
                    path = output / artifact["path"]
                    self.assertEqual(
                        hashlib.sha256(path.read_bytes()).hexdigest(),
                        artifact["sha256"],
                    )
                    with gzip.open(path, "rt") as stream:
                        self.assertEqual(
                            stream.readline().strip(),
                            "# " + ",".join(artifact["columns"]),
                        )
                    values = np.loadtxt(path, delimiter=",")
                    self.assertEqual(values.shape, (3, len(artifact["columns"])))
                    np.testing.assert_array_equal(values[:, 0], np.arange(3.0))
                    np.testing.assert_array_equal(values[:, 1:], 1.0)
                    self.assertEqual(artifact["samples"], 3)
                if fault == "oscillatory":
                    self.assertTrue(
                        all("unexpectedly oscillatory" in x for x in report["failures"])
                    )
                elif fault == "integration":
                    self.assertTrue(
                        all("incomplete integration" in x for x in report["failures"])
                    )


if __name__ == "__main__":
    unittest.main()
