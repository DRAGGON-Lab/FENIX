"""Independent expectations reject corrupted or mutually incorrect native evidence."""

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import locked_dependencies
from jsonschema import ValidationError
from ode_common import (
    METHODS,
    bits,
    compare_ode,
    controls,
    make_references,
    validate_ode_report,
    validate_references,
)

REV = "1" * 40


def transport(language):
    refs = make_references(REV)
    return {
        "format": "native-ode-report-v1",
        "implementation": language,
        "source_revision": REV,
        "fingerprints": refs["fingerprints"],
        "runtime": {
            "name": "CPython" if language == "python" else "Julia",
            "version": "3.12.13" if language == "python" else "1.10.13",
            "os": "synthetic-transport",
            "arch": "test",
            "dependencies": locked_dependencies(language),
        },
        "scenarios": [
            {
                "id": c["id"],
                "artifacts": c["artifacts"],
                "after_artifacts": c["artifacts"],
            }
            for c in refs["scenarios"]
        ],
        "runs": [
            {
                "case_id": c["id"],
                "method": method,
                "study": study,
                "settings": settings,
                "samples": [
                    {
                        "time_bits": s["time_bits"],
                        "state_bits": bits(float(s["expected"])),
                        "observable_bits": bits(float(s["expected"])),
                    }
                    for s in c["samples"]
                ],
                "diagnostics": {
                    "nfev": 1,
                    "njev": 0,
                    "nlu" if language == "python" else "nw": 0,
                },
                "fir_digest": c["artifacts"]["identity"]["sha256"],
                "state_ids": ["x"],
                "state_units": ["molecule"],
                "observable_ids": ["amount"],
                "observable_units": ["molecule"],
                "time_unit": "s",
            }
            for c in refs["scenarios"]
            for method in METHODS[language]
            for study, settings in refs["studies"].items()
        ],
        "controls": controls(language),
        "failures": [],
    }


class TestODEReports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reports = [transport("python"), transport("julia")]

    def test_full_coverage_and_derived_bounds(self):
        result = compare_ode(self.reports, REV)
        self.assertTrue(result["passed"])
        self.assertEqual(len(result["reference_comparisons"]), 480)
        self.assertEqual(len(result["pairwise_comparisons"]), 480)
        self.assertEqual(
            sum(r["study"] != "coarse" for r in result["reference_comparisons"]), 320
        )

    def corrupt(self, work):
        reports = copy.deepcopy(self.reports)
        for report in reports:
            work(report)
        with self.assertRaises((ValueError, ValidationError)):
            compare_ode(reports, REV)

    def test_missing_duplicate_extra_runs_and_samples(self):
        self.corrupt(lambda r: r["runs"].pop())
        self.corrupt(lambda r: r["runs"].__setitem__(0, copy.deepcopy(r["runs"][1])))
        self.corrupt(lambda r: r["runs"][0].update(case_id="extra"))
        self.corrupt(lambda r: r["runs"][0]["samples"].pop())
        self.corrupt(
            lambda r: r["runs"][0]["samples"].__setitem__(
                0, copy.deepcopy(r["runs"][0]["samples"][1])
            )
        )

    def test_stale_identities_and_settings(self):
        self.corrupt(lambda r: r.update(source_revision="0" * 40))
        self.corrupt(lambda r: r["fingerprints"].pop(next(iter(r["fingerprints"]))))
        self.corrupt(lambda r: r["runs"][0].update(fir_digest="0" * 64))
        self.corrupt(lambda r: r["runs"][0]["settings"].update(rtol_bits=bits(1e-5)))
        self.corrupt(
            lambda r: r["scenarios"][0]["after_artifacts"]["model"].update(
                sha256="0" * 64
            )
        )
        self.corrupt(lambda r: r["runtime"]["dependencies"].update(extra="1.0.0"))

    def test_malformed_negative_nonfinite_and_observable_bits(self):
        for value in (
            "zz",
            "0" * 15,
            "7ff0000000000000",
            "7ff8000000000000",
            "8000000000000001",
        ):
            self.corrupt(
                lambda r, value=value: r["runs"][0]["samples"][0].update(
                    state_bits=value
                )
            )
        self.corrupt(
            lambda r: r["runs"][0]["samples"][0].update(observable_bits=bits(123.0))
        )

    def test_controls_and_counters_are_not_pass_flags(self):
        self.corrupt(lambda r: r["controls"][0].update(category="WRONG"))
        self.corrupt(lambda r: r["controls"].pop())
        self.corrupt(lambda r: r["runs"][0]["diagnostics"].update(nfev=100001))
        self.corrupt(lambda r: r["runs"][0]["diagnostics"].update(nfev=True))
        self.corrupt(lambda r: r.update(passed=True))

    def test_two_reports_agree_on_wrong_numbers(self):
        reports = copy.deepcopy(self.reports)
        for report in reports:
            for run in report["runs"]:
                for sample in run["samples"]:
                    sample.update(state_bits=bits(123.0), observable_bits=bits(123.0))
        result = compare_ode(reports, REV)
        self.assertFalse(result["passed"])
        self.assertTrue(result["failures"])
        self.assertTrue(all(r["within_bound"] for r in result["pairwise_comparisons"]))

    def test_coarse_is_reported_without_changing_required_bound(self):
        reports = copy.deepcopy(self.reports)
        for report in reports:
            for run in report["runs"]:
                if run["study"] == "coarse":
                    for sample in run["samples"]:
                        sample.update(
                            state_bits=bits(123.0), observable_bits=bits(123.0)
                        )
        result = compare_ode(reports, REV)
        self.assertTrue(result["passed"])
        self.assertTrue(
            any(not r["within_bound"] for r in result["reference_comparisons"])
        )

    def test_corrupt_reference_manifest(self):
        refs = make_references(REV)
        refs["scenarios"][0]["experiment"]["content"]["revision"] = 2
        with self.assertRaises(ValueError):
            validate_references(refs, REV)

    def test_explicit_failure_cannot_be_success(self):
        self.corrupt(
            lambda r: r["failures"].append(
                {
                    "case_id": "baseline-zero",
                    "method": METHODS[r["implementation"]][0],
                    "study": "baseline",
                    "category": "WORK_LIMIT",
                    "message": "exhausted",
                    "nfev": 100000,
                }
            )
        )

    def test_signed_zero_is_numerically_admissible(self):
        reports = copy.deepcopy(self.reports)
        for report in reports:
            for run in report["runs"]:
                if run["case_id"] == "zero-solution":
                    for sample in run["samples"]:
                        sample.update(
                            state_bits="8000000000000000",
                            observable_bits="8000000000000000",
                        )
        self.assertTrue(compare_ode(reports, REV)["passed"])

    def test_wrong_units_are_rejected(self):
        self.corrupt(lambda r: r["runs"][0].update(state_units=["mol/L"]))

    def test_partial_failure_preserves_explicit_diagnostic(self):
        report = copy.deepcopy(self.reports[0])
        report.update(
            scenarios=[],
            runs=[],
            controls=[],
            failures=[
                {
                    "case_id": "baseline-zero",
                    "method": "DOP853",
                    "study": "baseline",
                    "category": "WORK_LIMIT",
                    "message": "exhausted",
                    "nfev": 100000,
                }
            ],
        )
        with self.assertRaisesRegex(ValueError, "Native solver failure.*WORK_LIMIT"):
            validate_ode_report(report, REV)
