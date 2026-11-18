"""Corrupt evidence must fail even when both languages agree on the corruption."""

import copy
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from common import (
    blob,
    compare,
    expected_rows,
    fingerprints,
    locked_dependencies,
    read_report,
    report_destination,
)
from jsonschema import ValidationError

REVISION = "1" * 40


def report(language):
    return {
        "report_version": 1,
        "implementation": language,
        "source_revision": REVISION,
        "runtime": {
            "name": "CPython" if language == "python" else "Julia",
            "version": "3.12.13" if language == "python" else "1.10.13",
            "os": "test",
            "arch": "test",
            "dependencies": locked_dependencies(language),
        },
        "fingerprints": fingerprints(),
        "cases": expected_rows(),
    }


class TestReports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reports = [report("python"), report("julia")]

    def test_approved_reports(self):
        compare(self.reports, REVISION)

    def corrupt(self, mutate):
        reports = copy.deepcopy(self.reports)
        for item in reports:
            mutate(item)
        with self.assertRaises((ValueError, ValidationError)):
            compare(reports, REVISION)

    def test_missing_duplicate_extra_cases(self):
        self.corrupt(lambda r: r["cases"].pop())
        self.corrupt(lambda r: r["cases"].append(r["cases"][0]))
        self.corrupt(lambda r: r["cases"][0].update(id="unknown-case"))
        self.corrupt(lambda r: r["cases"].__setitem__(0, copy.deepcopy(r["cases"][1])))

    def test_stale_fingerprints_and_revision(self):
        self.corrupt(lambda r: r["fingerprints"].pop(next(iter(r["fingerprints"]))))
        self.corrupt(lambda r: r["fingerprints"].update({"extra": "0" * 64}))
        self.corrupt(lambda r: r.update(source_revision="0" * 40))

    def test_closed_report_row_runtime_and_artifact(self):
        self.corrupt(lambda r: r.update(passed=True))
        self.corrupt(lambda r: r["cases"][0].update(passed=True))
        self.corrupt(lambda r: r["runtime"].update(extra=True))
        self.corrupt(lambda r: r.update(report_version=True))

    def test_wrong_dependencies_and_runtime(self):
        self.corrupt(
            lambda r: r["runtime"].update(
                name="CPython" if r["implementation"] == "julia" else "Julia"
            )
        )
        self.corrupt(lambda r: r["runtime"]["dependencies"].update(extra="1.0.0"))
        self.corrupt(lambda r: r["runtime"].update(version="9.99.99"))

    def test_wrong_outcomes_and_diagnostics(self):
        self.corrupt(lambda r: r["cases"][0]["observed"].update(outcome="reject"))

        def change(r):
            row = next(c for c in r["cases"] if "category" in c["observed"])
            row["observed"]["path"] = "/wrong"

        self.corrupt(change)

    def test_wrong_sources(self):
        self.corrupt(
            lambda r: r["cases"][0]["sources"]["primary"].update(sha256="0" * 64)
        )

    def test_malformed_bytes_and_digests(self):
        def change(r, field, value):
            row = next(c for c in r["cases"] if c["artifacts"])
            next(iter(row["artifacts"].values()))[field] = value

        for field, value in (
            ("hex", "zz"),
            ("hex", "0"),
            ("sha256", "g" * 64),
            ("sha256", "0" * 64),
        ):
            with self.subTest(field=field, value=value):
                self.corrupt(
                    lambda r, field=field, value=value: change(r, field, value)
                )

    def test_both_agree_on_wrong_bytes_with_correct_hash(self):
        reports = copy.deepcopy(self.reports)
        for r in reports:
            row = next(c for c in r["cases"] if c["artifacts"])
            row["artifacts"]["identity"] = blob(b"wrong but mutually identical")
        with self.assertRaisesRegex(ValueError, "first differing byte=.*expected\\["):
            compare(reports, REVISION)

    def test_reference_normalization_retains_expression_order(self):
        # Fixed approved fixture, serialized without importing native Fenix.
        self.assertNotIn("fenix", sys.modules)
        row = next(c for c in expected_rows() if c["catalog"] == "producer")
        self.assertNotIn(
            "provenance", bytes.fromhex(row["artifacts"]["model"]["hex"]).decode()
        )

    def test_protected_destinations(self):
        with self.assertRaises(ValueError):
            report_destination(HERE / "run_fir.py")


class TestReportJSON(unittest.TestCase):
    def test_duplicate_keys_and_nonfinite_numbers(self):
        for raw in (
            '{"cases": [], "cases": []}',
            '{"nested": {"x": 1, "x": 2}}',
            '{"number": NaN}',
            '{"number": Infinity}',
        ):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "report.json"
                path.write_text(raw)
                with self.assertRaises(ValueError):
                    read_report(path)


class TestReportPaths(unittest.TestCase):
    def test_symlink_and_hardlink_aliases(self):
        with tempfile.TemporaryDirectory() as directory:
            alias = Path(directory) / "alias.json"
            alias.symlink_to(HERE / "fir-report.schema.json")
            with self.assertRaises(ValueError):
                report_destination(alias)
            alias.unlink()
            original = Path(directory) / "original.json"
            original.write_text("{}")
            alias.hardlink_to(original)
            with self.assertRaises(ValueError):
                report_destination(alias)
