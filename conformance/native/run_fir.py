"""Installed Python package producer; no reference compiler or expectation generation."""

import argparse
import json
import platform
import struct
from importlib.metadata import version
from pathlib import Path

import fenix
from common import (
    ROOT,
    artifact,
    blob,
    fingerprints,
    load,
    report_destination,
    sources,
    validate_report,
)
from fenix.bioir import BioIRValidationError, DesignDocument, ExperimentDocument
from fenix.bioir._json import canonical_bytes, parse_json
from fenix.compiler import compile_experiment
from fenix.fir import FIRDocument, FIRValidationError


def model_artifacts(model):
    identity = model.identity_bytes()
    if model.digest != blob(identity)["sha256"]:
        raise ValueError("Native digest differs from native identity bytes")
    return {"model": blob(model.canonical_model_bytes()), "identity": blob(identity)}


def produce(revision):
    if (
        Path(fenix.__file__).resolve()
        != (ROOT / "packages/python/src/fenix/__init__.py").resolve()
    ):
        raise ValueError(
            "Installed fenix does not resolve to fingerprinted checkout sources"
        )
    rows = []
    catalog = load("conformance/rejections/catalog.json")
    for case in catalog["cases"]:
        document = "primary"
        op = case["operation"]
        try:
            deps = {}
            for key in ("design", "experiment", "previous"):
                if key in case["inputs"]:
                    document = key
                    raw = artifact(case["inputs"][key])
                    deps[key] = (
                        ExperimentDocument.from_json(raw, designs=(deps["design"],))
                        if key == "experiment"
                        else DesignDocument.from_json(raw)
                    )
            document = "primary"
            raw = artifact(case["inputs"]["primary"])
            op = case["operation"]
            if op == "parse":
                parse_json(raw, numeric_policy=case["contract"].lower())
            elif op == "experiment":
                ExperimentDocument.from_json(raw, designs=(deps["design"],))
            elif op in ("design", "revision"):
                DesignDocument.from_json(raw, previous=deps.get("previous"))
            elif op == "producer":
                FIRDocument.from_json(
                    raw, design=deps["design"], experiment=deps["experiment"]
                )
            else:
                result = FIRDocument.from_json(raw)
                if op == "capability":
                    document = "request"
                    request = parse_json(
                        artifact(case["inputs"]["request"]), numeric_policy="p03"
                    )
                    result.model.require_capability(request["profile"])
            observed = {"outcome": "accept"}
        except (BioIRValidationError, FIRValidationError) as error:
            observed = {
                "outcome": "reject",
                "category": error.category,
                "path": error.path,
                "document": document,
            }
        rows.append(
            {
                "catalog": "rejections",
                "id": case["id"],
                "observed": observed,
                "sources": sources(case, "rejections"),
                "artifacts": {},
            }
        )
        if op == "producer" and case["expected"]["outcome"] == "accept":
            compiled = compile_experiment(deps["experiment"])
            compiled.validate_sources(deps["design"], deps["experiment"])
            rows.append(
                {
                    "catalog": "producer",
                    "id": case["id"],
                    "observed": {"outcome": "accept"},
                    "sources": sources(case, "producer"),
                    "artifacts": model_artifacts(compiled.model),
                }
            )
    for case in load("conformance/canonicalization/catalog.json")["cases"]:
        artifacts = {}
        try:
            raw = artifact(case["input"], "conformance/canonicalization/")
            stage = case["stage"]
            if stage == "contract_only":
                if case["id"].startswith("fir-"):
                    FIRDocument.from_json(raw)
                else:
                    parse_json(raw, numeric_policy="p03")
            elif stage == "fir_identity":
                artifacts = model_artifacts(FIRDocument.from_json(raw).model)
            else:
                value = (
                    struct.unpack(">d", bytes.fromhex(case["binary64_bits"]))[0]
                    if stage == "binary64_jcs"
                    else parse_json(raw, numeric_policy="p03")
                )
                artifacts["canonical"] = blob(canonical_bytes(value))
            observed = {"outcome": "accept"}
        except (BioIRValidationError, FIRValidationError, ValueError):
            observed = {"outcome": "reject"}
        rows.append(
            {
                "catalog": "canonicalization",
                "id": case["id"],
                "observed": observed,
                "sources": sources(case, "canonicalization"),
                "artifacts": artifacts,
            }
        )
    return {
        "report_version": 1,
        "implementation": "python",
        "source_revision": revision,
        "runtime": {
            "name": "CPython",
            "version": platform.python_version(),
            "os": platform.system(),
            "arch": platform.machine(),
            "dependencies": {
                p: version(p)
                for p in ("fenix-bio", "rfc8785", "numpy", "scipy", "jsonschema")
            },
        },
        "fingerprints": fingerprints(),
        "cases": rows,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    destination = report_destination(args.report)
    report = produce(args.source_revision)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n")
    validate_report(report, args.source_revision)
    print("PASS: native Python report independently validated (300 cases)")
