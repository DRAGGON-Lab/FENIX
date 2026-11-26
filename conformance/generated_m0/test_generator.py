"""Controls for replay/reduction and detection of deliberately broken compilers."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import run
from fenix.fir import FIRDocument


class TestGeneratedConformance(unittest.TestCase):
    def test_seeded_generation_covers_boundaries_and_is_reproducible(self):
        a = list(run.scenarios(5901, 64))
        self.assertEqual(a, list(run.scenarios(5901, 64)))
        self.assertNotEqual(a, list(run.scenarios(5902, 64)))
        for field in ("alpha", "beta", "initial"):
            self.assertEqual(
                {getattr(s, field) for s in a}, set(range(len(run.TOKENS)))
            )
        self.assertEqual({s.volume for s in a}, set(range(len(run.VOLUMES))))
        self.assertEqual({s.observables for s in a}, {0, 1, 2, 3})
        for bit in range(8):
            self.assertEqual({bool(s.mask & (1 << bit)) for s in a}, {False, True})

    def test_reduction_preserves_the_same_failure_and_interaction(self):
        calls = []

        def broken(spec):
            calls.append(spec)
            if not spec.mask & 128:
                # A different failure must never replace the target failure.
                raise run.Failure("different", "irrelevant")
            if spec.alpha:
                raise run.Failure("role-resolution", "combined interaction")

        original = run.Scenario(
            alpha=6, beta=5, initial=4, volume=3, mask=255, observables=3, revision=2
        )
        minimal = run.reduce_failure(original, "role-resolution", broken)
        self.assertEqual(minimal, run.Scenario(alpha=6, mask=128))
        with self.assertRaisesRegex(run.Failure, "role-resolution"):
            broken(minimal)
        self.assertGreater(len(calls), 1)

    def test_combined_boundaries_pass_independent_checks(self):
        with run.Oracle() as oracle:
            bases = run.fixtures()
            for spec in run.scenarios(5901, len(run.TOKENS)):
                with self.subTest(spec=spec):
                    run.verify(spec, oracle, bases)

    def test_compiler_regression_is_captured_minimized_and_replayed(self):
        native = run.compile_experiment

        def wrong_value(experiment):
            envelope = native(experiment).to_dict()
            envelope["model"]["parameters"][0]["value"] = 7.0
            return FIRDocument.from_dict(envelope)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            failure_dir = root / "failure"
            replay_dir = root / "replay"
            fixed_dir = root / "fixed"
            with (
                patch.object(run, "compile_experiment", side_effect=wrong_value),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(
                    run.main(["--cases", "1", "--output-dir", str(failure_dir)]), 1
                )
                failure = json.loads((failure_dir / "failure.json").read_text())
                self.assertEqual(failure["property"], "alpha.compiler-bits")
                self.assertEqual(
                    failure["minimized_scenario"], run.asdict(run.Scenario())
                )
                self.assertEqual(
                    json.loads((failure_dir / "report.json").read_text())["status"],
                    "FAIL",
                )
                for filename in ("design.json", "experiment.json"):
                    self.assertIn(
                        "digest", json.loads((failure_dir / filename).read_text())
                    )
                self.assertEqual(
                    run.main(
                        [
                            "--replay",
                            str(failure_dir / "failure.json"),
                            "--output-dir",
                            str(replay_dir),
                        ]
                    ),
                    1,
                )
                replay = json.loads((replay_dir / "failure.json").read_text())
                self.assertEqual(replay["property"], failure["property"])
                self.assertEqual(
                    replay["minimized_scenario"], failure["minimized_scenario"]
                )
            # Removing the injected regression makes exactly that replay pass.
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    run.main(
                        [
                            "--replay",
                            str(failure_dir / "failure.json"),
                            "--output-dir",
                            str(fixed_dir),
                        ]
                    ),
                    0,
                )
            self.assertEqual(
                json.loads((fixed_dir / "report.json").read_text())["status"], "PASS"
            )

    def test_saved_use_case_reloads_with_exact_sources_and_expected_model(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "examples-run"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    run.main(
                        ["--cases", "1", "--save-examples", "--output-dir", str(output)]
                    ),
                    0,
                )
            report = json.loads((output / "report.json").read_text())
            row = report["cases"][0]
            case = output / row["example"]
            source = run.DesignDocument.from_json((case / "design.json").read_bytes())
            experiment = run.ExperimentDocument.from_json(
                (case / "experiment.json").read_bytes(), designs=(source,)
            )
            observed = FIRDocument.from_json(
                (case / "fir.json").read_bytes(), design=source, experiment=experiment
            )
            self.assertEqual(
                (source.digest, experiment.digest, observed.digest),
                (row["design_digest"], row["experiment_digest"], row["fir_digest"]),
            )
            with run.Oracle() as oracle:
                self.assertEqual(
                    observed.model.canonical_model_bytes(),
                    oracle.canonical((case / "expected-model.json").read_text()),
                )

    def test_missing_producer_map_is_detected(self):
        native = run.compile_experiment

        def wrong_map(experiment):
            envelope = native(experiment).to_dict()
            envelope["provenance"]["symbol_map"]["parameters"] = list(
                reversed(envelope["provenance"]["symbol_map"]["parameters"])
            )
            envelope["provenance"]["symbol_map"]["parameters"][0][
                "bioir_parameter_id"
            ] = "unmapped"
            return FIRDocument.from_dict(envelope)

        with (
            run.Oracle() as oracle,
            patch.object(run, "compile_experiment", side_effect=wrong_map),
        ):
            with self.assertRaisesRegex(
                run.Failure,
                "producer.transport-readback|unexpected-diagnostic.REFERENCE",
            ):
                run.verify(
                    run.Scenario(mask=255, observables=3), oracle, run.fixtures()
                )

    def test_malformed_byte_failure_keeps_a_json_serializable_exact_witness(self):
        with self.assertRaises(run.Failure) as caught:
            run.rejected(
                lambda: None, "INVALID_UNICODE", "", "raw.invalid-utf8", b"\xff"
            )
        self.assertEqual(caught.exception.witness, {"raw_hex": "ff"})
        self.assertEqual(
            json.loads(json.dumps(caught.exception.witness)), {"raw_hex": "ff"}
        )

    def test_replay_accepts_only_bounded_data(self):
        default = run.asdict(run.Scenario())
        self.assertEqual(run.Scenario.decode(default), run.Scenario())
        for mutation in (
            {"alpha": True},
            {"mask": 256},
            {"initial": -1},
            {"revision": 2**53},
            {"unknown": "executable"},
        ):
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                run.Scenario.decode({**default, **mutation})

    def test_output_never_overwrites_sources_or_existing_artifacts(self):
        with self.assertRaises(ValueError):
            run.output_directory(run.HERE)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileExistsError):
                run.output_directory(directory)
            # Resolve symlinks before applying the protected-checkout restriction.
            link = Path(directory) / "fixtures"
            link.symlink_to(run.ROOT / "conformance")
            with self.assertRaises(ValueError):
                run.output_directory(link / "generated-overwrite")


if __name__ == "__main__":
    unittest.main()
