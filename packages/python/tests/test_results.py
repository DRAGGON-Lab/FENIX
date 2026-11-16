"""Native P07 capture and verified transport against ratified examples."""

import dataclasses
import hashlib
import json
import struct
import sys
import unittest
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from test_compiler import committed
from test_execution import settings

from fenix.bioir import DesignDocument, ExperimentDocument
from fenix.compiler import compile_experiment
from fenix.execution import ODEExecutionError
from fenix.fir import FIRValidationError
from fenix.results import (
    ODEResult,
    ResultValidationError,
    RunManifest,
    RunRecord,
    run_experiment,
)

ROOT = Path(__file__).resolve().parents[3]
EXAMPLES = ROOT / "spec/results/proposals/examples"


def bits(value):
    return struct.pack(">d", value).hex()


def example(name="late-first"):
    d = DesignDocument.from_json(
        (ROOT / "spec/bioir/proposals/examples/design.json").read_bytes()
    )
    path = {
        "empty-observables": ROOT
        / "spec/fir/proposals/examples/sources/no-observables-experiment.json",
        "multi-observables": EXAMPLES / "multi-observables.experiment.json",
    }.get(name, ROOT / "spec/bioir/proposals/examples/experiment.json")
    e = ExperimentDocument.from_json(path.read_bytes(), designs=(d,))
    return (
        e,
        (EXAMPLES / f"{name}.manifest.json").read_bytes(),
        (EXAMPLES / f"{name}.result.json").read_bytes(),
    )


def encode_pair(m, r):
    rb = json.dumps(r).encode()
    m["output"]["sha256"] = hashlib.sha256(rb).hexdigest()
    return json.dumps(m), rb


class TestResults(unittest.TestCase):
    def load(self, m, r, e=None, **kwargs):
        return RunRecord.from_json(
            m, r, experiment=example()[0] if e is None else e, **kwargs
        )

    def reject(self, m, r, path, category=None, e=None):
        with self.assertRaises(ResultValidationError) as caught:
            self.load(m, r, e)
        self.assertEqual(caught.exception.path, path)
        if category:
            self.assertEqual(caught.exception.category, category)

    def test_all_accepted_artifacts_original_bytes_and_fixed_checksums(self):
        checksums = json.loads((EXAMPLES / "checksums.json").read_bytes())["artifacts"]
        for name in (
            "zero-only",
            "late-first",
            "empty-observables",
            "multi-observables",
        ):
            e, m, r = example(name)
            with (
                self.subTest(name=name),
                patch(
                    "fenix.execution.solve_ivp", side_effect=AssertionError("solver")
                ),
                patch("fenix.results.solve_ode", side_effect=AssertionError("solver")),
                patch(
                    "fenix.results.version", side_effect=AssertionError("environment")
                ),
            ):
                record = self.load(
                    m, r, e, expected_manifest_sha256=checksums[f"{name}.manifest.json"]
                )
            self.assertEqual(
                hashlib.sha256(r).hexdigest(), checksums[f"{name}.result.json"]
            )
            self.assertEqual(record.manifest.to_json().encode(), m)
            self.assertEqual(record.result_bytes, r)
            self.assertEqual(record.result.to_dict(), json.loads(r))
            self.assertEqual(record.manifest.to_dict(), json.loads(m))

    def test_capture_both_methods_grids_and_observables(self):
        for method in ("DOP853", "Radau"):
            for name, grid in (
                ("zero-only", (-0.0,)),
                ("late-first", (1.0, 10.0)),
                ("empty-observables", (0.0,)),
                ("multi-observables", (0.0, 1.0)),
            ):
                e = example(name)[0]
                fir = compile_experiment(e)
                before = (
                    e.to_json(),
                    e.source_design.to_json(),
                    fir.model.identity_bytes(),
                )
                with self.subTest(method=method, name=name):
                    record = run_experiment(e, settings(method=method, time_grid=grid))
                    loaded = self.load(
                        record.manifest.to_json(), record.result_bytes, e
                    )
                    self.assertEqual(loaded.result, record.result)
                    self.assertEqual(
                        tuple(bits(t) for t in record.result.times),
                        tuple(bits(t) for t in grid),
                    )
                    self.assertEqual(
                        record.result.observable_ids,
                        tuple(
                            o["id"]
                            for o in fir.model.normalized().to_dict()["observables"]
                        ),
                    )
                    self.assertEqual(
                        record.result.observable_state_ids,
                        ("x",) * len(record.result.observable_ids),
                    )
                    for state, obs in zip(
                        record.result.state_values,
                        record.result.observable_values,
                        strict=True,
                    ):
                        self.assertEqual(obs, state * len(record.result.observable_ids))
                    manifest = record.manifest.to_dict()
                    self.assertIsNone(manifest["producer"]["build_id"])
                    self.assertEqual(manifest["producer"]["name"], "fenix-bio")
                    self.assertEqual(
                        manifest["backend"]["solver"]["options"]["jacobian"],
                        "constant_exact" if method == "Radau" else "not_supplied",
                    )
                    self.assertEqual(
                        manifest["integration"],
                        "skipped_zero_grid" if grid[-1] == 0 else "performed",
                    )
                    self.assertEqual(
                        (
                            e.to_json(),
                            e.source_design.to_json(),
                            compile_experiment(e).model.identity_bytes(),
                        ),
                        before,
                    )

    def test_zero_capture_avoids_solver_and_clock_adjustments(self):
        start = datetime(2026, 11, 16, 12, 0, 0, 123456, tzinfo=UTC)
        finish = datetime(2026, 11, 15, 12, 0, 0, 654321, tzinfo=UTC)
        with (
            patch("fenix.results._utc_now", side_effect=(start, finish)),
            patch("fenix.results.monotonic_ns", side_effect=(1000000000, 1250000000)),
            patch("fenix.execution.solve_ivp", side_effect=AssertionError("solver")),
        ):
            record = run_experiment(committed(), settings(time_grid=(-0.0,)))
        m = record.manifest.to_dict()
        self.assertEqual(
            m["timing"],
            {
                "started_at_utc": "2026-11-16T12:00:00.123456Z",
                "finished_at_utc": "2026-11-15T12:00:00.654321Z",
                "elapsed_seconds": 0.25,
            },
        )
        self.assertEqual(m["evaluations"], {"nfev": 0})
        self.assertEqual(m["backend"]["evaluations"], {"njev": 0, "nlu": 0})

    def test_solver_failure_propagates(self):
        for method in ("DOP853", "Radau"):
            with self.assertRaises(ODEExecutionError) as caught:
                run_experiment(committed(), settings(method=method, max_nfev=1))
            self.assertEqual(caught.exception.category, "WORK_LIMIT")

    def test_immutable_no_unchecked_construction_fresh_dicts(self):
        record = run_experiment(committed(), settings(time_grid=(0.0,)))
        for cls in (RunRecord, RunManifest, ODEResult):
            with self.assertRaises(TypeError):
                cls()
        for obj, name, value in (
            (record, "result_bytes", b"x"),
            (record.result, "times", ()),
            (record.manifest, "_text", "x"),
        ):
            with self.assertRaises((dataclasses.FrozenInstanceError, AttributeError)):
                setattr(obj, name, value)
        with self.assertRaises(TypeError):
            record.result.state_values[0][0] = 3.0
        m = record.manifest.to_dict()
        m["execution"]["time_grid"][0] = 999
        r = record.result.to_dict()
        r["state_values"][0][0] = 999
        self.assertEqual(record.result.state_values, ((0.5,),))
        self.assertEqual(record.manifest.to_dict()["execution"]["time_grid"], [0.0])

    def test_preserve_environment_build_id_formatting_and_trust(self):
        e, mb, rb = example("multi-observables")
        m = json.loads(mb)
        m["producer"] = {"name": "other", "version": "future", "build_id": "snapshot:α"}
        m["backend"]["environment"] = {
            k: "recorded:α" for k in m["backend"]["environment"]
        }
        text = " \n" + json.dumps(m, ensure_ascii=False, indent=3) + "\n"
        expected = hashlib.sha256(text.encode()).hexdigest()
        record = self.load(text, rb, e, expected_manifest_sha256=expected)
        self.assertEqual(record.manifest.to_json(), text)
        self.assertEqual(record.manifest.to_dict(), m)
        with self.assertRaises(ResultValidationError) as caught:
            self.load(text + " ", rb, e, expected_manifest_sha256=expected)
        self.assertEqual(caught.exception.path, "/manifest")
        for checksum in ("", "A" * 64, "0" * 63, True, 1):
            with self.assertRaises(ResultValidationError):
                self.load(text, rb, e, expected_manifest_sha256=checksum)

    def test_plausible_altered_positive_samples_pass_only_internal_checks(self):
        e, mb, rb = example()
        trusted = hashlib.sha256(mb).hexdigest()
        m, r = json.loads(mb), json.loads(rb)
        r["state_values"][0][0] = r["observable_values"][0][0] = 123.0
        text, result = encode_pair(m, r)
        self.assertEqual(self.load(text, result, e).result.state_values[0], (123.0,))
        with self.assertRaises(ResultValidationError):
            self.load(text, result, e, expected_manifest_sha256=trusted)
        self.reject(mb, result, "/manifest/output/sha256", "CHECKSUM")

    def test_binary64_transport_vectors_and_negative_zero_observables(self):
        probes = json.loads((EXAMPLES / "numeric-tokens.json").read_bytes())
        e, mb, rb = example()
        for probe in probes["binary64"]:
            m, r = json.loads(mb), json.loads(rb)
            r["state_values"][0][0] = r["observable_values"][0][0] = "TOKEN"
            raw = json.dumps(r).replace('"TOKEN"', probe["token"]).encode()
            m["output"]["sha256"] = hashlib.sha256(raw).hexdigest()
            with self.subTest(token=probe["token"]):
                result = self.load(json.dumps(m), raw, e).result
                self.assertEqual(bits(result.state_values[0][0]), probe["bits"])
                self.assertEqual(bits(result.observable_values[0][0]), probe["bits"])
        for token in probes["reject_binary64"]:
            m, r = json.loads(mb), json.loads(rb)
            r["state_values"][0][0] = "TOKEN"
            raw = json.dumps(r).replace('"TOKEN"', token).encode()
            m["output"]["sha256"] = hashlib.sha256(raw).hexdigest()
            with self.subTest(token=token), self.assertRaises(ResultValidationError):
                self.load(json.dumps(m), raw, e)

    def test_large_exponents_exact_zero_underflow_and_rounding_ties(self):
        e, mb, rb = example()
        probes = (
            ("0e999999999999999999999999999999", "0000000000000000"),
            ("-0e-999999999999999999999999999999", "8000000000000000"),
            (
                "1.00000000000000011102230246251565404236316680908203125",
                "3ff0000000000000",
            ),
            (
                "1.00000000000000033306690738754696212708950042724609375",
                "3ff0000000000002",
            ),
        )
        for token, expected in probes:
            m, r = json.loads(mb), json.loads(rb)
            r["state_values"][0][0] = r["observable_values"][0][0] = "TOKEN"
            raw = json.dumps(r).replace('"TOKEN"', token).encode()
            m["output"]["sha256"] = hashlib.sha256(raw).hexdigest()
            with self.subTest(token=token):
                self.assertEqual(
                    bits(self.load(json.dumps(m), raw, e).result.state_values[0][0]),
                    expected,
                )
        for token in (
            "1e-999999999999999999999999999999",
            "-1e-999999999999999999999999999999",
            "1e999999999999999999999999999999",
        ):
            m, r = json.loads(mb), json.loads(rb)
            r["state_values"][0][0] = "TOKEN"
            raw = json.dumps(r).replace('"TOKEN"', token).encode()
            m["output"]["sha256"] = hashlib.sha256(raw).hexdigest()
            self.reject(json.dumps(m), raw, "/result/state_values/0/0", "NUMBER", e=e)

    def test_all_binary64_manifest_fields_use_field_numeric_policy(self):
        _, mb, rb = example()
        for field in ("rtol", "atol", "max_step", "elapsed_seconds", "time_grid"):
            for token in ("1e309", "1e-400", "true", '"1.0"'):
                m = json.loads(mb)
                target = m["timing"] if field == "elapsed_seconds" else m["execution"]
                target[field] = (
                    ["TOKEN", 10.0, 100.0] if field == "time_grid" else "TOKEN"
                )
                path = (
                    "/manifest/"
                    + ("timing/" if field == "elapsed_seconds" else "execution/")
                    + field
                    + ("/0" if field == "time_grid" else "")
                )
                self.reject(json.dumps(m).replace('"TOKEN"', token), rb, path, "NUMBER")
        for grid in ([], [-1.0], [-0.0, 0.0], [2.0, 1.0]):
            m = json.loads(mb)
            m["execution"]["time_grid"] = grid
            with (
                self.subTest(grid=grid),
                self.assertRaises(ResultValidationError) as caught,
            ):
                self.load(json.dumps(m), rb)
            self.assertTrue(
                caught.exception.path.startswith("/manifest/execution/time_grid")
            )

    def test_capture_revalidates_sources_preserves_errors_and_clock_boundaries(self):
        e = committed()
        events = []

        def compile_source(source):
            events.append("compile")
            return compile_experiment(source)

        from fenix import results

        emit = results._emit

        def serialize(value):
            if isinstance(value, dict) and value.get("kind") == "ODEResult":
                events.append("serialize_result")
            return emit(value)

        def wall():
            events.append("wall")
            return datetime(2026, 11, 16, tzinfo=UTC)

        def monotonic():
            events.append("monotonic")
            return 0

        with (
            patch("fenix.results.compile_experiment", side_effect=compile_source),
            patch("fenix.results._utc_now", side_effect=wall),
            patch("fenix.results.monotonic_ns", side_effect=monotonic),
            patch("fenix.results._emit", side_effect=serialize),
        ):
            run_experiment(e, settings(time_grid=(0.0,)))
        self.assertEqual(
            events,
            ["wall", "monotonic", "compile", "serialize_result", "wall", "monotonic"],
        )
        # Deliberate corruption bypassing the immutable public interface must
        # still be rejected at the existing compiler boundary.
        for corrupt_design in (False, True):
            source = committed()
            object.__setattr__(
                source.source_design if corrupt_design else source, "digest", "0" * 64
            )
            with patch(
                "fenix.execution.solve_ivp", side_effect=AssertionError("solver")
            ):
                with self.assertRaises(FIRValidationError):
                    run_experiment(source, settings())
                with self.assertRaises(ResultValidationError) as caught:
                    self.load(*example()[1:], e=source)
                self.assertTrue(caught.exception.path.startswith("/manifest/sources/"))
        failure = FIRValidationError("REFERENCE", "/experiment", "compiler failure")
        with patch("fenix.results.compile_experiment", side_effect=failure):
            with self.assertRaises(FIRValidationError) as caught:
                run_experiment(e, settings())
        self.assertIs(caught.exception, failure)

    def test_missing_members_and_invalid_native_inputs(self):
        e, mb, rb = example()
        for field in json.loads(mb):
            m = json.loads(mb)
            del m[field]
            self.reject(json.dumps(m), rb, "/manifest/" + field)
        for field in json.loads(rb):
            m, r = json.loads(mb), json.loads(rb)
            del r[field]
            text, raw = encode_pair(m, r)
            self.reject(text, raw, "/result/" + field)
        for value in (None, {}, bytearray(mb), "\ud800"):
            with self.assertRaises(ResultValidationError):
                self.load(value, rb, e)
        for value in (None, rb.decode(), bytearray(rb)):
            self.reject(mb, value, "/result")
        with self.assertRaises(ResultValidationError):
            self.load(mb, rb, e={})
        for cls in (RunManifest, ODEResult, RunRecord):
            with self.assertRaises(TypeError):
                cls(result_bytes=rb)

    def test_zero_counters_and_initial_zero_sign(self):
        e, mb, rb = example("zero-only")
        for container, key, path in (
            ("evaluations", "nfev", "/manifest/evaluations/nfev"),
            ("backend", "njev", "/manifest/backend/evaluations/njev"),
            ("backend", "nlu", "/manifest/backend/evaluations/nlu"),
        ):
            m = json.loads(mb)
            target = (
                m[container]["evaluations"] if container == "backend" else m[container]
            )
            target[key] = 1
            self.reject(json.dumps(m), rb, path, e=e)
        m, r = json.loads(mb), json.loads(rb)
        r["state_values"] = r["observable_values"] = [[-0.0]]
        text, raw = encode_pair(m, r)
        loaded = self.load(text, raw, e)
        self.assertEqual(bits(loaded.result.state_values[0][0]), "8000000000000000")

    def test_exact_large_integers_including_6000_digits_and_capture_emission(self):
        e, mb, rb = example()
        for token in ("9007199254740993", "1" + "0" * 5999):
            m = json.loads(mb)
            for container, key in (
                (m["execution"], "max_nfev"),
                (m["evaluations"], "nfev"),
                (m["backend"]["evaluations"], "njev"),
                (m["backend"]["evaluations"], "nlu"),
            ):
                container[key] = "TOKEN"
            text = json.dumps(m).replace('"TOKEN"', token)
            limit = sys.get_int_max_str_digits()
            record = self.load(text, rb, e)
            self.assertEqual(
                record.manifest.to_dict()["evaluations"]["nfev"], int(Decimal(token))
            )
            self.assertEqual(sys.get_int_max_str_digits(), limit)
            captured = run_experiment(
                e, settings(time_grid=(0.0,), max_nfev=int(Decimal(token)))
            )
            loaded = self.load(captured.manifest.to_json(), captured.result_bytes, e)
            self.assertEqual(
                loaded.manifest.to_dict()["execution"]["max_nfev"], int(Decimal(token))
            )

    def test_integer_field_token_rejection(self):
        e, mb, rb = example()
        for location, key, path in (
            ("execution", "max_nfev", "/manifest/execution/max_nfev"),
            ("evaluations", "nfev", "/manifest/evaluations/nfev"),
            ("sources", "revision", "/manifest/sources/design/revision"),
            ("backend", "njev", "/manifest/backend/evaluations/njev"),
        ):
            for token in ("1.0", "1e0", "true", '"1"', "-1"):
                m = json.loads(mb)
                target = m[location]
                if location == "sources":
                    target = target["design"]
                if location == "backend":
                    target = target["evaluations"]
                target[key] = "TOKEN"
                self.reject(json.dumps(m).replace('"TOKEN"', token), rb, path)

    def test_strict_raw_json_both_artifacts(self):
        _, mb, rb = example()
        for artifact, valid in (("manifest", mb), ("result", rb)):
            for invalid in (
                b"",
                b"{",
                valid[:-2],
                valid + b"x",
                b"\xef\xbb\xbf" + valid,
                b"\xff",
                b'{"x":NaN}',
                b'{"x":Infinity}',
                b'{"x":"\\ud800"}',
                b'{"x":"\\udfff"}',
                b'{"x":1,"\\u0078":2}',
                b'{"x":1,}',
                b"{/*comment*/}",
            ):
                with (
                    self.subTest(artifact=artifact, raw=invalid[:30]),
                    self.assertRaises(ResultValidationError) as caught,
                ):
                    m = json.loads(mb)
                    m["output"]["sha256"] = hashlib.sha256(invalid).hexdigest()
                    self.load(
                        invalid if artifact == "manifest" else json.dumps(m),
                        invalid if artifact == "result" else rb,
                    )
                self.assertTrue(caught.exception.path.startswith("/" + artifact))
        self.reject('{"x":1,"\\u0078":2}', rb, "/manifest/x", "DUPLICATE_KEY")

    def test_manifest_closed_structure_and_observation_failures(self):
        _, mb, rb = example()
        mutations = [
            (("schema_version",), "9", "UNSUPPORTED_VERSION"),
            (("backend", "profile"), "julia", "UNSUPPORTED_PROFILE"),
            (("execution", "profile"), "ssa", "UNSUPPORTED_PROFILE"),
            (("randomness", "seed"), 1, None),
            (("randomness", "rng"), "pcg", None),
            (("backend", "solver", "method"), "RK45", None),
            (("backend", "solver", "options", "jacobian"), "constant_exact", None),
            (("backend", "solver", "options", "first_step"), 1.0, None),
            (("backend", "solver", "options", "vectorized"), 0, None),
            (("backend", "solver", "options", "dense_output"), True, None),
            (("backend", "solver", "options", "events"), "callback", None),
            (("execution", "rtol"), 1e-16, None),
            (("execution", "atol"), 0, None),
            (("execution", "max_step"), -1, None),
            (("execution", "max_nfev"), 0, None),
            (("evaluations", "nfev"), 100001, None),
            (("evaluations", "nfev"), 0, None),
            (("backend", "evaluations", "nlu"), -1, None),
            (("integration",), "skipped_zero_grid", None),
            (("timing", "started_at_utc"), "2026-02-30T12:00:00.000000Z", None),
            (("timing", "finished_at_utc"), "2026-11-16T12:00:60.000000Z", None),
            (("timing", "elapsed_seconds"), -1, None),
            (("producer", "build_id"), "", None),
            (("producer", "version"), "", None),
            (("backend", "environment", "scipy_version"), 1, None),
        ]
        for keys, value, category in mutations:
            m = json.loads(mb)
            target = m
            for k in keys[:-1]:
                target = target[k]
            target[keys[-1]] = value
            with self.subTest(keys=keys):
                self.reject(json.dumps(m), rb, "/manifest/" + "/".join(keys), category)
        for keys in (
            (),
            ("sources",),
            ("sources", "design"),
            ("fir",),
            ("execution",),
            ("randomness",),
            ("timing",),
            ("output",),
            ("producer",),
            ("backend",),
            ("backend", "solver"),
            ("backend", "solver", "options"),
            ("backend", "environment"),
            ("backend", "evaluations"),
        ):
            m = json.loads(mb)
            target = m
            for k in keys:
                target = target[k]
            target["unknown/a~"] = 1
            self.reject(
                json.dumps(m), rb, "/manifest/" + "/".join((*keys, "unknown~1a~0"))
            )

    def test_source_and_fir_references_all_fields_and_same_fir_context(self):
        e, mb, rb = example()
        for scope in ("design", "experiment"):
            for field, value in (
                ("schema_version", "9"),
                ("id", "another"),
                ("revision", 2),
                ("digest", "0" * 64),
            ):
                m = json.loads(mb)
                m["sources"][scope][field] = value
                self.reject(json.dumps(m), rb, f"/manifest/sources/{scope}/{field}")
        for field, value in (
            ("schema_version", "9"),
            ("canonicalization_version", "9"),
            ("digest", "0" * 64),
        ):
            m = json.loads(mb)
            m["fir"][field] = value
            self.reject(json.dumps(m), rb, f"/manifest/fir/{field}")
        other = ExperimentDocument(
            content=dataclasses.replace(
                e.content, id="other", source_design=e.source_design.content
            ),
            source_design=e.source_design,
        )
        self.assertEqual(compile_experiment(other).digest, compile_experiment(e).digest)
        self.reject(mb, rb, "/manifest/sources/experiment/id", e=other)
        different_design = DesignDocument(
            content=dataclasses.replace(e.source_design.content, id="other_design")
        )
        other = ExperimentDocument(
            content=dataclasses.replace(
                e.content,
                design=different_design.reference,
                source_design=different_design.content,
            ),
            source_design=different_design,
        )
        self.assertEqual(compile_experiment(other).digest, compile_experiment(e).digest)
        self.reject(mb, rb, "/manifest/sources/design/id", e=other)

    def test_result_mismatches_dimensions_order_units_grid_mapping_samples(self):
        e, mb, rb = example("multi-observables")
        mutations = [
            ("schema_version", "9"),
            ("fir_digest", "0" * 64),
            ("time_unit", "min"),
            ("times", [1.0]),
            ("times", [1.0, 1.0]),
            ("times", [1.0, 11.0]),
            ("state_ids", ["y"]),
            ("state_units", ["mol"]),
            ("state_values", [[1.0]]),
            ("state_values", [[1.0, 2.0], [1.0, 2.0]]),
            ("state_values", [[-5e-324], [1.0]]),
            ("observable_ids", ["z_amount", "m_amount", "a_amount"]),
            ("observable_state_ids", ["y", "x", "x"]),
            ("observable_units", ["molecule", "mol", "molecule"]),
            ("observable_values", [[], []]),
            ("observable_values", [[1.0] * 3, [1.0] * 3]),
            ("unknown", 1),
        ]
        for key, value in mutations:
            m, r = json.loads(mb), json.loads(rb)
            r[key] = value
            text, raw = encode_pair(m, r)
            with (
                self.subTest(key=key, value=value),
                self.assertRaises(ResultValidationError) as caught,
            ):
                self.load(text, raw, e)
            self.assertTrue(caught.exception.path.startswith("/result/" + key))
        e, mb, rb = example("zero-only")
        m, r = json.loads(mb), json.loads(rb)
        r["times"] = [0.0]
        text, raw = encode_pair(m, r)
        self.reject(text, raw, "/result/times/0", e=e)
        r["times"] = [-0.0]
        r["state_values"] = [[1.0]]
        text, raw = encode_pair(m, r)
        self.reject(text, raw, "/result/state_values/0/0", e=e)
        r["state_values"] = [[-0.0]]
        r["observable_values"] = [[0.0]]
        text, raw = encode_pair(m, r)
        self.reject(text, raw, "/result/observable_values/0/0", e=e)
