"""Corruption and isolation checks against independently expected mathematics."""

import copy
import json
import runpy
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import verify  # noqa: E402 - repository-only tools need the local paths above


class TestAlphaVerifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.revision = "ba943e6882e7301f2356139df7010ff141494b7f"
        cls.expected = next(
            s
            for s in verify.make_references(cls.revision)["scenarios"]
            if s["id"] == "baseline-five"
        )
        cls.example = runpy.run_path(
            str(verify.ROOT / "examples/m0/production_decay.py")
        )

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.example["save_run"](
            self.example["build_experiment"]("baseline-five"),
            self.example["execution_settings"]("baseline-five", "DOP853"),
            self.directory,
        )
        import fenix

        self.package_root = str(Path(fenix.__file__).resolve().parent)

    def validate(self):
        return verify.validate_example(
            self.directory,
            "python",
            "baseline-five",
            "DOP853",
            self.package_root,
            self.expected,
        )

    def test_independent_example_and_import_isolation(self):
        self.validate()
        with self.assertRaisesRegex(ValueError, "import fell back"):
            verify.validate_example(
                self.directory,
                "python",
                "baseline-five",
                "DOP853",
                "/unrelated/isolated/install",
                self.expected,
            )

    def test_inconsistent_fir_provenance_with_recomputed_checksums(self):
        fir = verify.read_report(self.directory / "fir.json")
        fir["provenance"]["design_digest"] = "0" * 64
        raw = json.dumps(fir).encode()
        (self.directory / "fir.json").write_bytes(raw)
        summary = verify.read_report(self.directory / "summary.json")
        summary["checksums"]["fir.json"] = verify.sha(raw)
        (self.directory / "summary.json").write_text(json.dumps(summary))
        with self.assertRaisesRegex(ValueError, "FIR provenance"):
            self.validate()

    def test_fir_producer_provenance(self):
        path = self.directory / "fir.json"
        original = verify.read_report(path)
        summary = verify.read_report(self.directory / "summary.json")

        def check(fir):
            raw = json.dumps(fir).encode()
            path.write_bytes(raw)
            summary["checksums"]["fir.json"] = verify.sha(raw)
            (self.directory / "summary.json").write_text(json.dumps(summary))
            self.validate()

        for label, change in (
            ("missing compiler", lambda p: p.pop("compiler")),
            ("wrong compiler", lambda p: p["compiler"].update(name="Fenix")),
            ("wrong version", lambda p: p["compiler"].update(version="9.9.9")),
            ("extra field", lambda p: p.update(unknown=True)),
            ("missing map", lambda p: p.pop("symbol_map")),
            ("partial map", lambda p: p["symbol_map"]["parameters"].pop()),
            (
                "wrong port",
                lambda p: p["symbol_map"]["states"][0].update(bioir_port_id="other"),
            ),
            (
                "wrong function",
                lambda p: p["symbol_map"]["parameters"][0].update(
                    bioir_function_id=p["symbol_map"]["parameters"][1][
                        "bioir_function_id"
                    ]
                ),
            ),
            (
                "unknown observable",
                lambda p: p.update(display_labels={"observables": {"other": "Label"}}),
            ),
            (
                "invalid label",
                lambda p: p.update(display_labels={"observables": {"amount": 5}}),
            ),
        ):
            with self.subTest(label=label):
                fir = copy.deepcopy(original)
                change(fir["provenance"])
                with self.assertRaisesRegex(ValueError, "FIR provenance"):
                    check(fir)

        original["provenance"]["symbol_map"]["parameters"].reverse()
        original["provenance"]["display_labels"] = {
            "observables": {"amount": "Molecules"}
        }
        check(original)

    def test_corrupted_result_bytes(self):
        with (self.directory / "result.json").open("ab") as stream:
            stream.write(b" ")
        with self.assertRaisesRegex(ValueError, "checksum"):
            self.validate()

    def test_wrong_numerics_with_consistent_checksums(self):
        result = verify.read_report(self.directory / "result.json")
        result["state_values"][-1][0] = 1000.0
        result["observable_values"][-1][0] = 1000.0
        raw = json.dumps(result).encode()
        (self.directory / "result.json").write_bytes(raw)
        manifest = verify.read_report(self.directory / "manifest.json")
        manifest["output"]["sha256"] = verify.sha(raw)
        (self.directory / "manifest.json").write_text(json.dumps(manifest))
        summary = verify.read_report(self.directory / "summary.json")
        for name in ("manifest.json", "result.json"):
            summary["checksums"][name] = verify.sha(
                (self.directory / name).read_bytes()
            )
        (self.directory / "summary.json").write_text(json.dumps(summary))
        with self.assertRaisesRegex(ValueError, "P04 oracle mismatch"):
            self.validate()

    def test_wrong_source_identity(self):
        expected = copy.deepcopy(self.expected)
        expected["artifacts"]["model"]["hex"] = "00"
        with self.assertRaisesRegex(ValueError, "independent canonical bytes"):
            verify.validate_example(
                self.directory,
                "python",
                "baseline-five",
                "DOP853",
                self.package_root,
                expected,
            )

    def test_missing_language_evidence(self):
        with self.assertRaises(FileNotFoundError):
            verify.verify(
                self.directory,
                self.revision,
                {"python": self.package_root, "julia": "/isolated/julia"},
            )

    def benchmark(self):
        dependencies = verify.locked_dependencies("python")
        dependencies.pop("jsonschema")
        return {
            "format": "m0-benchmark-v1",
            "language": "python",
            "case": "baseline-five",
            "method": "DOP853",
            "source_revision": self.revision,
            "validation": "PASS",
            "repeats": 20,
            "warmups": 3,
            "package_load_seconds": 0.1,
            "first_seconds": dict.fromkeys(("compile", "solve", "capture"), 0.1),
            "timings": {
                p: {"seconds": [0.1] * 20, "median": 0.1, "min": 0.1, "max": 0.1}
                for p in ("compile", "solve", "capture")
            },
            "settings": {
                "time_grid": [0.0, 1.0, 10.0, 100.0],
                "rtol": 1e-10,
                "atol": 1e-12,
                "max_step": 1.0,
                "max_nfev": 100000,
            },
            "runtime": {"language_version": "3.12.13", "dependencies": dependencies},
            "hardware": dict.fromkeys(
                ("os", "machine", "cpu", "threads", "logical_cpus", "runner_image"),
                "test",
            ),
            "fingerprints": verify.expected_fingerprints(),
            "identities": {
                "design": self.expected["artifacts"]["design"]["sha256"],
                "experiment": self.expected["artifacts"]["experiment"]["sha256"],
                "fir": self.expected["artifacts"]["identity"]["sha256"],
            },
        }

    def test_incomplete_nonfinite_and_stale_benchmark(self):
        baseline = self.benchmark()
        verify.validate_benchmark(
            baseline, "python", "baseline-five", "DOP853", self.revision, self.expected
        )
        for field, value in (
            ("seconds", [0.1]),
            ("seconds", [float("nan")] * 20),
            ("median", 0.2),
        ):
            report = copy.deepcopy(baseline)
            report["timings"]["solve"][field] = value
            with self.assertRaises(ValueError):
                verify.validate_benchmark(
                    report,
                    "python",
                    "baseline-five",
                    "DOP853",
                    self.revision,
                    self.expected,
                )
        baseline["fingerprints"] = {}
        with self.assertRaisesRegex(ValueError, "fingerprints"):
            verify.validate_benchmark(
                baseline,
                "python",
                "baseline-five",
                "DOP853",
                self.revision,
                self.expected,
            )


class TestSourceRevisionWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(verify.ROOT / "examples/m0"))
        import source_revisions

        cls.example = source_revisions
        cls.expected = next(
            s
            for s in verify.make_references("0670cf35d7791e610b4e7c3931a720e9109532ad")[
                "scenarios"
            ]
            if s["id"] == "baseline-five"
        )

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name) / "workflow"
        self.example.run_workflow("baseline-five", "DOP853", self.directory)
        import fenix

        self.package_root = str(Path(fenix.__file__).resolve().parent)

    def validate(self):
        return verify.validate_revision_workflow(
            self.directory,
            "python",
            "baseline-five",
            "DOP853",
            self.package_root,
            self.expected,
        )

    def test_independent_source_revisions_and_same_mathematics(self):
        self.assertEqual(
            self.validate(), self.expected["artifacts"]["identity"]["sha256"]
        )
        next_expected = verify.revision_expectation(self.expected)
        self.assertNotEqual(
            next_expected["artifacts"]["design"], self.expected["artifacts"]["design"]
        )
        self.assertNotEqual(
            next_expected["artifacts"]["experiment"],
            self.expected["artifacts"]["experiment"],
        )
        self.assertEqual(
            next_expected["artifacts"]["model"], self.expected["artifacts"]["model"]
        )

    def test_old_artifacts_cannot_replace_revised_sources(self):
        import shutil

        shutil.copytree(
            self.directory / "original", self.directory / "revised", dirs_exist_ok=True
        )
        with self.assertRaisesRegex(ValueError, "independent canonical bytes"):
            self.validate()

    def test_swapped_records_reject_despite_matching_fir(self):
        import shutil

        old, new = self.directory / "original", self.directory / "revised"
        summary = verify.read_report(new / "summary.json")
        for name in ("manifest.json", "result.json"):
            shutil.copyfile(old / name, new / name)
            summary["checksums"][name] = verify.sha((new / name).read_bytes())
        (new / "summary.json").write_text(json.dumps(summary))
        with self.assertRaisesRegex(ValueError, "source digest|source reference"):
            self.validate()

    def test_plausible_samples_still_require_independent_numerical_check(self):
        directory = self.directory / "revised"
        result = verify.read_report(directory / "result.json")
        result["state_values"][1][0] += 1.0
        result["observable_values"][1][0] = result["state_values"][1][0]
        raw = json.dumps(result).encode()
        (directory / "result.json").write_bytes(raw)
        manifest = verify.read_report(directory / "manifest.json")
        manifest["output"]["sha256"] = verify.sha(raw)
        (directory / "manifest.json").write_text(json.dumps(manifest))
        summary = verify.read_report(directory / "summary.json")
        for name in ("manifest.json", "result.json"):
            summary["checksums"][name] = verify.sha((directory / name).read_bytes())
        (directory / "summary.json").write_text(json.dumps(summary))
        with self.assertRaisesRegex(ValueError, "P04 oracle mismatch"):
            self.validate()

    def test_compound_mismatch_diagnostic_stays_on_exact_source_fields(self):
        path = self.directory / "summary.json"
        summary = verify.read_report(path)
        summary["rejections"]["old_record_new_sources"]["path"] = "/manifest/fir/digest"
        path.write_text(json.dumps(summary))
        with self.assertRaisesRegex(ValueError, "source reference diagnostic"):
            self.validate()

    def test_missing_rejection_control_fails_summary_validation(self):
        path = self.directory / "summary.json"
        summary = verify.read_report(path)
        summary["rejections"].pop("old_fir_new_sources")
        path.write_text(json.dumps(summary))
        with self.assertRaisesRegex(ValueError, "workflow summary"):
            self.validate()


if __name__ == "__main__":
    unittest.main()
