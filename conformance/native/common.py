"""Test report contract and independent P03 reference serialization.

This module never imports either native package. Expected compiler output comes
only from approved FIR artifacts, with P03's six collection sorts and RFC 8785.
"""

import hashlib
import json
import re
import tomllib
from pathlib import Path

import rfc8785
from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "conformance/native"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_report(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key: " + key)
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError("Nonfinite JSON number: " + value)

    return json.loads(
        Path(path).read_bytes(),
        object_pairs_hook=unique,
        parse_constant=reject_constant,
    )


def load(path):
    return json.loads((ROOT / path).read_bytes())


def artifact(item, prefix=""):
    path = prefix + item["path"]
    raw = (ROOT / path).read_bytes()
    if sha(raw) != item["sha256"]:
        raise ValueError("Artifact checksum mismatch: " + path)
    return raw


def blob(raw):
    return {"hex": raw.hex(), "sha256": sha(raw)}


def reference_model(model):
    # ADR-P03: declarations sort on UTF-16, expressions retain their AST order.
    def utf16(value):
        return value.encode("utf-16-be")

    for name in ("states", "parameters", "reactions", "observables"):
        model[name].sort(key=lambda x: utf16(x["id"]))
    model["equations"].sort(key=lambda x: utf16(x["state"]))
    model["assumptions"].sort(key=utf16)
    model_bytes = rfc8785.dumps(model)
    identity = rfc8785.dumps(
        {"domain": "fenix.fir", "canonicalization_version": "0.1.0", "model": model}
    )
    return {"model": blob(model_bytes), "identity": blob(identity)}


def sources(case, catalog):
    if catalog in ("rejections", "producer"):
        return {k: dict(v) for k, v in case["inputs"].items()}
    return {
        k: {
            "path": "conformance/canonicalization/" + case[k]["path"],
            "sha256": case[k]["sha256"],
        }
        for k in ("input", "normalized", "canonical", "model_canonical")
        if k in case
    }


def expected_rows():
    rows = []
    rejection = load("conformance/rejections/catalog.json")
    canonical = load("conformance/canonicalization/catalog.json")
    if rejection["status"] != "APPROVED" or canonical["status"] != "APPROVED":
        raise ValueError("Approved catalogs required")
    if len(rejection["cases"]) != 207 or len(canonical["cases"]) != 84:
        raise ValueError("Unexpected catalog coverage")
    for case in rejection["cases"]:
        for item in case["inputs"].values():
            artifact(item)
        observed = {k: v for k, v in case["expected"].items() if k != "stage"}
        rows.append(
            {
                "catalog": "rejections",
                "id": case["id"],
                "sources": sources(case, "rejections"),
                "observed": observed,
                "artifacts": {},
            }
        )
        if case["operation"] == "producer" and observed["outcome"] == "accept":
            approved = json.loads(
                artifact(case["inputs"]["primary"]), parse_int=float, parse_float=float
            )
            rows.append(
                {
                    "catalog": "producer",
                    "id": case["id"],
                    "sources": sources(case, "producer"),
                    "observed": {"outcome": "accept"},
                    "artifacts": reference_model(approved["model"]),
                }
            )
    for case in canonical["cases"]:
        refs = sources(case, "canonicalization")
        for item in refs.values():
            artifact(item)
        artifacts = {}
        if "canonical" in case:
            key = "identity" if case["stage"] == "fir_identity" else "canonical"
            artifacts[key] = blob(artifact(refs["canonical"]))
        if "model_canonical" in case:
            artifacts["model"] = blob(artifact(refs["model_canonical"]))
        rows.append(
            {
                "catalog": "canonicalization",
                "id": case["id"],
                "sources": refs,
                "observed": {"outcome": case["expected_outcome"]},
                "artifacts": artifacts,
            }
        )
    if sum(r["catalog"] == "producer" for r in rows) != 9:
        raise ValueError("Nine producer controls required")
    return rows


def fingerprints():
    paths = set()
    for folder, pattern in (
        ("packages/python/src", "*.py"),
        ("packages/julia/src", "*.jl"),
        ("conformance/native", "*.py"),
        ("conformance/native", "*.jl"),
        ("conformance/native", "*.json"),
        ("spec", "*.json"),
        ("spec", "ADR-*.md"),
    ):
        paths.update(p for p in (ROOT / folder).rglob(pattern) if p.is_file())
    paths.update(
        ROOT / p
        for p in (
            "packages/python/pyproject.toml",
            "packages/python/uv.lock",
            "packages/julia/Project.toml",
            "packages/julia/test_native_fir/report_paths.jl",
            ".github/workflows/native-fir.yml",
            "conformance/julia_ode/Project.toml",
            "conformance/julia_ode/Manifest.toml",
            "conformance/rejections/catalog.json",
            "conformance/rejections/catalog.schema.json",
            "conformance/canonicalization/catalog.json",
            "conformance/canonicalization/catalog.schema.json",
        )
    )
    return {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(paths)}


def locked_dependencies(language):
    if language == "python":
        lock = tomllib.loads((ROOT / "packages/python/uv.lock").read_text())
        names = {"fenix-bio", "rfc8785", "numpy", "scipy", "jsonschema"}
        return {p["name"]: p["version"] for p in lock["package"] if p["name"] in names}
    lock = tomllib.loads((ROOT / "conformance/julia_ode/Manifest.toml").read_text())
    return {
        name: entry["version"]
        for name, entries in lock["deps"].items()
        for entry in entries
        if "version" in entry
    }


def validate_report(report, revision):
    schema = load("conformance/native/fir-report.schema.json")
    Draft7Validator(schema).validate(report)
    if type(report["report_version"]) is not int:
        raise ValueError("Invalid report version type")
    runtime = report["runtime"]
    language = report["implementation"]
    if runtime["version"] != {"python": "3.12.13", "julia": "1.10.13"}[language]:
        raise ValueError("Runtime does not match default test pin")
    if runtime["name"] != {"python": "CPython", "julia": "Julia"}[language] or runtime[
        "dependencies"
    ] != locked_dependencies(language):
        raise ValueError(
            "Runtime/dependencies do not match implementation and locked environment"
        )
    if report["source_revision"] != revision or not re.fullmatch(
        "[0-9a-f]{40}", revision
    ):
        raise ValueError("Source revision mismatch")
    if report["fingerprints"] != fingerprints():
        raise ValueError("Stale or incomplete source/catalog/schema/lock fingerprints")
    expected = {(r["catalog"], r["id"]): r for r in expected_rows()}
    actual = {(r["catalog"], r["id"]): r for r in report["cases"]}
    if len(actual) != len(report["cases"]) or actual.keys() != expected.keys():
        raise ValueError("Missing, duplicate or extra report cases")
    for key, want in expected.items():
        got = actual[key]
        label = "/".join(key)
        if got["sources"] != want["sources"] or got["observed"] != want["observed"]:
            raise ValueError(label + ": source/outcome/diagnostic mismatch")
        if got["artifacts"].keys() != want["artifacts"].keys():
            raise ValueError(label + ": missing or extra byte artifacts")
        for name, expected_blob in want["artifacts"].items():
            value = got["artifacts"][name]
            raw = bytes.fromhex(value["hex"])
            if sha(raw) != value["sha256"]:
                raise ValueError(
                    label + "/" + name + ": actual digest does not match actual bytes"
                )
            compare_bytes(label + "/" + name, bytes.fromhex(expected_blob["hex"]), raw)
    return actual


def compare_bytes(label, expected, actual):
    if expected == actual:
        return
    offset = next(
        (i for i, (a, b) in enumerate(zip(expected, actual)) if a != b),
        min(len(expected), len(actual)),
    )
    start, end = max(0, offset - 16), offset + 17
    raise ValueError(
        f"{label}: expected sha256={sha(expected)}, actual sha256={sha(actual)}; "
        f"first differing byte={offset}; expected[{start}:{end}]={expected[start:end].hex()}; "
        f"actual[{start}:{end}]={actual[start:end].hex()}"
    )


def compare(reports, revision):
    if len(reports) != 2 or {r.get("implementation") for r in reports} != {
        "python",
        "julia",
    }:
        raise ValueError("Exactly one Python and one Julia report required")
    indexes = [validate_report(r, revision) for r in reports]
    for key in indexes[0]:
        for name, value in indexes[0][key]["artifacts"].items():
            compare_bytes(
                "/".join((*key, name)),
                bytes.fromhex(value["hex"]),
                bytes.fromhex(indexes[1][key]["artifacts"][name]["hex"]),
            )


def report_destination(path):
    target = Path(path).resolve()
    if target.is_relative_to(ROOT) and not target.is_relative_to(ROOT / "artifacts"):
        raise ValueError("Reports inside repository must be under artifacts/")
    if target.exists() and (not target.is_file() or target.stat().st_nlink != 1):
        raise ValueError("Report must be a regular file without hardlink aliases")
    return target
