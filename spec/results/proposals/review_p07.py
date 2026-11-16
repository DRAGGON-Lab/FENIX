"""Read-only bounded P07 proposal audit; no native FENIX imports or execution.

Not a general manifest parser, source resolver or implementation conformance
suite. Fixed examples and mutations exercise distinct structural/byte/numeric
claims. JSON Schema does not enforce the ADR's complete semantic contract.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import platform
import struct
from decimal import Decimal
from fractions import Fraction
from importlib.metadata import version
from pathlib import Path
from typing import Any

import rfc8785
from jsonschema import Draft7Validator  # type: ignore[import-untyped]

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXAMPLES = HERE / "examples"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bits(value: float) -> str:
    return struct.pack(">d", value).hex()


def fixture_identity(model: dict[str, Any]) -> str:
    """External JCS of these fixed ASCII-ID fixtures under unchanged P03 rules."""
    expected = copy.deepcopy(model)
    for collection in ("states", "parameters", "reactions", "observables"):
        expected[collection].sort(key=lambda item: item["id"])
    expected["equations"].sort(key=lambda item: item["state"])
    expected["assumptions"].sort()
    return hashlib.sha256(
        rfc8785.dumps(
            {
                "domain": "fenix.fir",
                "canonicalization_version": "0.1.0",
                "model": expected,
            }
        )
    ).hexdigest()


def binary_fraction(word: int) -> Fraction:
    """Exact positive finite IEEE binary64 value from exponent/significand bits."""
    exponent = (word >> 52) & 0x7FF
    significand = word & ((1 << 52) - 1)
    assert word >> 63 == 0 and exponent != 0x7FF
    if exponent:
        significand += 1 << 52
    power = exponent - 1023 - 52 if exponent else -1074
    return Fraction(significand) * Fraction(2) ** power


def check_nearest(token: str, expected: str) -> None:
    """Check a decimal's independently specified nearest/ties-even bit pattern.

    Rational midpoint intervals derive from IEEE fields, without float arithmetic.
    max finite uses the next mathematical binade value for its upper boundary.
    """
    decimal = Decimal(token)
    exact = Fraction(decimal)
    word = int(expected, 16)
    if exact == 0:
        assert word == (1 << 63 if decimal.is_signed() else 0)
    else:
        assert exact > 0 and word > 0 and word >> 63 == 0
        value = binary_fraction(word)
        previous = binary_fraction(word - 1)
        following = (
            binary_fraction(word + 1)
            if word < 0x7FEFFFFFFFFFFFFF
            else Fraction(2) ** 1024
        )
        lower, upper = (value + previous) / 2, (value + following) / 2
        assert lower <= exact <= upper
        if exact in (lower, upper):
            assert word % 2 == 0
    # Compare the independent bit expectation to the JSON number decoder with
    # field-specific float conversion, including integer-form negative zero.
    decoded = json.loads(token, parse_int=float, parse_float=float)
    assert type(decoded) is float and bits(decoded) == expected


def main() -> None:
    catalog = load(EXAMPLES / "checksums.json")
    assert catalog["status"] == "PROPOSED"
    assert set(catalog["artifacts"]) == {
        p.name for p in EXAMPLES.glob("*.json") if p.name != "checksums.json"
    }
    for name, expected in catalog["artifacts"].items():
        assert sha(EXAMPLES / name) == expected, name

    validators = {}
    for name in ("run-manifest", "ode-result"):
        schema = load(HERE / f"{name}-m0.schema.json")
        Draft7Validator.check_schema(schema)
        validators[name] = Draft7Validator(schema)

    baseline_design = ROOT / "spec/bioir/proposals/examples/design.json"
    baseline_experiment = ROOT / "spec/bioir/proposals/examples/experiment.json"
    empty_experiment = (
        ROOT / "spec/fir/proposals/examples/sources/no-observables-experiment.json"
    )
    multi_experiment = EXAMPLES / "multi-observables.experiment.json"
    multi_fir = EXAMPLES / "multi-observables.fir.json"
    # External JCS only; these inputs already exist independently of production
    # parsers/compilers. This is a bounded fixture relation, not a source resolver.
    for path in (
        baseline_design,
        baseline_experiment,
        empty_experiment,
        multi_experiment,
    ):
        document = load(path)
        assert (
            hashlib.sha256(rfc8785.dumps(document["content"])).hexdigest()
            == document["digest"]
        )
    fir_base = ROOT / "conformance/canonicalization/expected/fir-base.canonical"
    named_digest = sha(fir_base)
    assert named_digest == (
        "cf4011a6c97891192c0b84951dd53ae38bd1fc629e05c885a8dff30bd5e53a50"
    )
    empty_model = load(
        ROOT / "spec/fir/proposals/examples/production-decay-no-observables.json"
    )["model"]
    empty_digest = fixture_identity(empty_model)
    multi_model = load(multi_fir)["model"]
    baseline_model = load(ROOT / "spec/fir/proposals/examples/production-decay.json")[
        "model"
    ]
    # Hand-prepared model differs only in the explicitly declared observables.
    expected_multi = copy.deepcopy(baseline_model)
    expected_multi["observables"] = [
        {"id": name, "state": "x", "unit": "molecule"}
        for name in ("z_amount", "a_amount", "m_amount")
    ]
    assert multi_model == expected_multi
    multi_source = load(multi_experiment)["content"]
    expected_source = copy.deepcopy(load(baseline_experiment)["content"])
    expected_source["id"] = "multiple_observables"
    expected_source["observables"] = [
        {"id": name, "target": {"species": "x", "port": "amount"}}
        for name in ("z_amount", "a_amount", "m_amount")
    ]
    assert multi_source == expected_source
    Draft7Validator(load(ROOT / "spec/bioir/proposals/bioir-m0.schema.json")).validate(
        load(multi_experiment)
    )
    Draft7Validator(load(ROOT / "spec/fir/proposals/fir-m0.schema.json")).validate(
        load(multi_fir)
    )

    pairs = {}
    for name in ("late-first", "zero-only", "empty-observables", "multi-observables"):
        manifest = load(EXAMPLES / f"{name}.manifest.json")
        result_path = EXAMPLES / f"{name}.result.json"
        result = load(result_path)
        validators["run-manifest"].validate(manifest)
        validators["ode-result"].validate(result)
        assert manifest["output"]["sha256"] == sha(result_path)
        assert result["fir_digest"] == manifest["fir"]["digest"]
        expected_digest = {
            "empty-observables": empty_digest,
            "multi-observables": fixture_identity(multi_model),
        }.get(name, named_digest)
        assert result["fir_digest"] == expected_digest
        experiment_path = (
            empty_experiment
            if name == "empty-observables"
            else multi_experiment
            if name == "multi-observables"
            else baseline_experiment
        )
        for field, path in (
            ("design", baseline_design),
            ("experiment", experiment_path),
        ):
            document = load(path)
            content = document["content"]
            assert manifest["sources"][field] == {
                "schema_version": content["schema_version"],
                "id": content["id"],
                "revision": content["revision"],
                "digest": document["digest"],
            }
        assert list(map(bits, result["times"])) == list(
            map(bits, manifest["execution"]["time_grid"])
        )
        assert len(result["state_values"]) == len(result["times"])
        assert len(result["observable_values"]) == len(result["times"])
        if name == "empty-observables":
            for field in ("observable_ids", "observable_state_ids", "observable_units"):
                assert result[field] == []
            assert result["observable_values"] == [[]]
        else:
            ordered = sorted(
                multi_model["observables"]
                if name == "multi-observables"
                else baseline_model["observables"],
                key=lambda item: item["id"],
            )
            assert result["observable_ids"] == [o["id"] for o in ordered]
            assert result["observable_state_ids"] == [o["state"] for o in ordered]
            assert result["observable_units"] == [o["unit"] for o in ordered]
            for state_row, observable_row in zip(
                result["state_values"], result["observable_values"], strict=True
            ):
                assert len(observable_row) == len(ordered)
                for column, observable in enumerate(ordered):
                    state_index = result["state_ids"].index(observable["state"])
                    assert bits(observable_row[column]) == bits(state_row[state_index])
        assert manifest["randomness"] == {"rng": "none", "seed": None}
        assert manifest["backend"]["profile"] == "python-scipy-ode/0.1.0"
        method = manifest["backend"]["solver"]["method"]
        assert manifest["backend"]["solver"]["options"]["jacobian"] == (
            "constant_exact" if method == "Radau" else "not_supplied"
        )
        if name in ("zero-only", "empty-observables"):
            assert manifest["integration"] == "skipped_zero_grid"
            assert manifest["evaluations"] == {"nfev": 0}
            assert manifest["backend"]["evaluations"] == {"njev": 0, "nlu": 0}
            assert result["state_values"] == [[0.0]]
        # Transport evidence only: no native RunRecord loader is invoked.
        for artifact in (EXAMPLES / f"{name}.manifest.json", result_path):
            raw = artifact.read_bytes()
            assert raw.decode("utf-8", errors="strict").encode("utf-8") == raw
            assert json.loads(raw) == json.loads(raw + b" ")
            assert hashlib.sha256(raw).digest() != hashlib.sha256(raw + b" ").digest()
        pairs[name] = manifest, result

    multi_result = pairs["multi-observables"][1]
    assert [o["id"] for o in multi_source["observables"]] == [
        "z_amount",
        "a_amount",
        "m_amount",
    ]
    assert multi_result["observable_ids"] == ["a_amount", "m_amount", "z_amount"]
    assert multi_result["observable_ids"] != [
        o["id"] for o in multi_source["observables"]
    ]
    assert pairs["multi-observables"][0]["producer"]["build_id"] == (
        "candidate:p07-multi-observable-v1"
    )
    assert pairs["late-first"][0]["producer"]["build_id"] is None

    # Fixed wrong-source/same-FIR counterexamples, not native rejection tests.
    for suffix in ("gfp", "laci"):
        alternate = load(
            ROOT / f"spec/fir/proposals/examples/production-decay-{suffix}.json"
        )
        assert fixture_identity(alternate["model"]) == named_digest
        for kind in ("design", "experiment"):
            alternate_source = load(
                ROOT / f"spec/fir/proposals/examples/sources/{suffix}-{kind}.json"
            )
            assert (
                alternate_source["digest"]
                != pairs["late-first"][0]["sources"][kind]["digest"]
            )

    # Reference values come from the already accepted analytical catalog, not a
    # solver. Audit nearest binary64 to each published decimal with rational math.
    oracle_path = ROOT / "conformance/production_decay/catalog.json"
    oracle = load(oracle_path)
    case = next(c for c in oracle["cases"] if c["id"] == "baseline-zero")
    late_result = pairs["late-first"][1]
    for index, sample in enumerate(case["samples"][1:]):
        assert bits(late_result["times"][index]) == sample["time_bits"]
        check_nearest(sample["expected"], bits(late_result["state_values"][index][0]))
    assert multi_result["times"] == late_result["times"][:2]
    assert multi_result["state_values"] == late_result["state_values"][:2]

    probes = load(EXAMPLES / "numeric-tokens.json")
    for probe in probes["binary64"]:
        check_nearest(probe["token"], probe["bits"])
    assert probes["integers"] == [9007199254740993, 1000000000000000000000000000001]
    assert pairs["zero-only"][0]["execution"]["max_nfev"] == 9007199254740993
    assert bits(pairs["zero-only"][1]["times"][0]) == "8000000000000000"
    for token in probes["reject_binary64"]:
        decoded = json.loads(token, parse_int=float, parse_float=float)
        assert (
            type(decoded) is not float
            or not math.isfinite(decoded)
            or (decoded == 0 and Decimal(token) != 0)
        )
    for token in probes["reject_integer"]:
        assert type(json.loads(token)) is not int

    structural_rejections = 0
    value: object
    for key, validator in validators.items():
        original = pairs["late-first"][0 if key == "run-manifest" else 1]
        # Every present object level is closed and every member required.
        mutations = []
        pending: list[tuple[tuple[str, ...], Any]] = [((), original)]
        while pending:
            node_path, node = pending.pop()
            if not isinstance(node, dict):
                continue
            for field, child in node.items():
                pending.append(((*node_path, field), child))
            for field in (*node, "unrecognized"):
                changed = copy.deepcopy(original)
                target = changed
                for segment in node_path:
                    target = target[segment]
                if field == "unrecognized":
                    target[field] = True
                else:
                    del target[field]
                mutations.append(changed)
        unsupported = copy.deepcopy(original)
        unsupported["schema_version"] = "999.0.0"
        mutations.append(unsupported)
        if key == "run-manifest":
            for field, value in (
                ("seed", 123),
                ("rng", "PCG64"),
                ("unknown", None),
            ):
                bad = copy.deepcopy(original)
                bad["randomness"][field] = value
                mutations.append(bad)
            for field, value in (("nfev", -1), ("nfev", True), ("nfev", 1.5)):
                bad = copy.deepcopy(original)
                bad["evaluations"][field] = value
                mutations.append(bad)
            bad_id: object
            for bad_id in ("", 123, True, []):
                bad = copy.deepcopy(original)
                bad["producer"]["build_id"] = bad_id
                mutations.append(bad)
            for bad_profile in ("unknown", "julia-sciml-ode/0.1.0"):
                bad = copy.deepcopy(original)
                bad["backend"]["profile"] = bad_profile
                mutations.append(bad)
            bad = copy.deepcopy(original)
            bad["execution"]["rtol"] = 1e-15
            mutations.append(bad)
        else:
            for field, value in (
                ("time_unit", "min"),
                ("state_units", ["mol"]),
                ("state_ids", ["wrong"]),
                ("state_values", [[-1.0]]),
                ("observable_ids", ["amount_x", "amount_x"]),
            ):
                bad = copy.deepcopy(original)
                bad[field] = value
                mutations.append(bad)
        for mutation in mutations:
            assert not validator.is_valid(mutation)
            structural_rejections += 1

    original_bytes = (EXAMPLES / "late-first.result.json").read_bytes()
    assert (
        hashlib.sha256(original_bytes).digest()
        != hashlib.sha256(original_bytes + b" ").digest()
    )
    assert json.loads(original_bytes) == json.loads(original_bytes + b" ")

    inputs = [
        HERE / "ADR-P07.md",
        HERE / "run-manifest-m0.schema.json",
        HERE / "ode-result-m0.schema.json",
        HERE / "review_p07_refinements.js",
        Path(__file__),
        EXAMPLES / "checksums.json",
        baseline_design,
        baseline_experiment,
        empty_experiment,
        multi_experiment,
        multi_fir,
        ROOT / "spec/bioir/proposals/bioir-m0.schema.json",
        ROOT / "spec/fir/proposals/fir-m0.schema.json",
        ROOT / "spec/fir/proposals/examples/production-decay.json",
        ROOT / "spec/fir/proposals/examples/production-decay-no-observables.json",
        fir_base,
        oracle_path,
    ]
    for suffix in ("gfp", "laci"):
        inputs.append(
            ROOT / f"spec/fir/proposals/examples/production-decay-{suffix}.json"
        )
        inputs.extend(
            ROOT / f"spec/fir/proposals/examples/sources/{suffix}-{kind}.json"
            for kind in ("design", "experiment")
        )
    print(
        json.dumps(
            {
                "status": "PROPOSED",
                "outcome": "PASS",
                "python": platform.python_version(),
                "jsonschema": version("jsonschema"),
                "rfc8785": version("rfc8785"),
                "example_pairs": len(pairs),
                "multi_observable_columns": 3,
                "wrong_source_same_fir_counterexamples": 2,
                "analytical_reference_samples": 3,
                "binary64_transport_probes": len(probes["binary64"]),
                "structural_rejection_mutations": structural_rejections,
                "native_readback_execution_tests": "NOT RUN",
                "human_pi_ratification": "PENDING",
                "input_sha256": {str(p.relative_to(ROOT)): sha(p) for p in inputs},
                "candidate_sha256": catalog["artifacts"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
