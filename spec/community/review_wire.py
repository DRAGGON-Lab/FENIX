"""Audit the literal PROPOSED M1 wire packet without native FENIX imports."""

import argparse
import hashlib
import json
from decimal import Decimal, localcontext
from pathlib import Path

from wire_contract import (
    HERE,
    Rejection,
    decode,
    producer,
    result_record,
    same_float,
    source_pair,
)

FIXTURES = HERE / "wire-candidates"


def read(path, policy="source"):
    return decode(path.read_bytes(), policy)


def load(folder):
    return (
        read(folder / "design.json"),
        read(folder / "experiment.json"),
        read(folder / "fir.json", "fir"),
    )


def positive(row):
    folder = FIXTURES / row["folder"]
    design, experiment, fir = load(folder)
    normalized, model_bytes, identity_bytes, digest = producer(design, experiment, fir)
    assert normalized == read(folder / "normalized.json", "fir"), "normalized model"
    assert model_bytes == (folder / "model.jcs").read_bytes(), "model bytes"
    assert identity_bytes == (folder / "identity.jcs").read_bytes(), "identity bytes"
    assert digest == (folder / "digest.txt").read_text().strip(), "digest"
    for label in ("zero", "analytical"):
        raw = (folder / f"{label}.result.json").read_bytes()
        result = decode(raw, "transport")
        for language in ("python", "julia"):
            manifest = read(folder / f"{label}.{language}.manifest.json", "transport")
            assert (
                result_record(design, experiment, fir, result, manifest, raw) == digest
            )
    return digest


def negative(row):
    folder = FIXTURES / row["base"]
    design, experiment, fir = load(folder)
    raw = (folder / "zero.result.json").read_bytes()
    result, manifest = (
        decode(raw, "transport"),
        read(folder / "zero.python.manifest.json", "transport"),
    )
    candidate = read(
        FIXTURES / row["file"],
        "transport"
        if row["target"] in ("result", "manifest")
        else "fir"
        if row["target"] == "fir"
        else "source",
    )
    if row["target"] == "design":
        design = candidate
    elif row["target"] == "experiment":
        experiment = candidate
    elif row["target"] == "fir":
        fir = candidate
    elif row["target"] == "result":
        result = candidate
        raw = (FIXTURES / row["file"]).read_bytes()
        manifest = read(FIXTURES / row["manifest"], "transport")
    else:
        manifest = candidate
    try:
        if row["target"] in ("design", "experiment"):
            source_pair(design, experiment)
        elif row["target"] == "fir":
            producer(design, experiment, fir)
        else:
            result_record(design, experiment, fir, result, manifest, raw)
    except Rejection as error:
        assert (error.category, error.path) == (row["category"], row["path"]), (
            row["id"],
            (error.category, error.path),
            (row["category"], row["path"]),
        )
        return {"id": row["id"], "category": error.category, "path": error.path}
    raise AssertionError("negative accepted: " + row["id"])


def raw_case(row):
    try:
        actual = read(FIXTURES / row["file"], row["policy"])
    except Rejection as error:
        assert (error.category, error.path) == (row["category"], row["path"]), row["id"]
    else:
        assert row["category"] is None and actual == row["value"], row["id"]
        if isinstance(row["value"]["value"], float):
            assert same_float(actual["value"], row["value"]["value"]), row["id"]


def audit():
    catalog = read(FIXTURES / "catalog.json", "transport")
    assert catalog["status"] == "PROPOSED", (
        "approval status must be explicitly revised, never inferred"
    )
    ids = [
        r["id"]
        for group in ("positive", "rejections", "raw_numbers")
        for r in catalog[group]
    ]
    assert len(ids) == len(set(ids)), "duplicate catalog IDs"
    identities = {row["id"]: positive(row) for row in catalog["positive"]}
    for row in catalog["positive"]:
        if row.get("same_fir_as"):
            assert identities[row["id"]] == identities[row["same_fir_as"]], row["id"]
    rejections = [negative(row) for row in catalog["rejections"]]
    for row in catalog["raw_numbers"]:
        raw_case(row)
    # Map analytical columns by explicit ID, independently of fixture writer order.
    import sys

    sys.path.insert(0, str(HERE.parents[1] / "conformance/community"))
    import reference

    reference.validate_catalog(reference.catalog())
    with localcontext() as ctx:
        ctx.prec = 160
        for row in catalog["positive"]:
            result = read(
                FIXTURES / row["folder"] / "analytical.result.json", "transport"
            )
            for time, samples in zip(
                result["times"], result["state_values"], strict=True
            ):
                expected = reference.state(row["reference_case"], Decimal(time))
                for state, actual in zip(result["state_ids"], samples, strict=True):
                    assert same_float(
                        actual,
                        float(expected[reference.catalog()["state_ids"].index(state)]),
                    )
    files = sorted(p for p in FIXTURES.rglob("*") if p.is_file())
    return {
        "status": "PROPOSED",
        "identities": identities,
        "rejections": rejections,
        "counts": {
            key: len(catalog[key]) for key in ("positive", "rejections", "raw_numbers")
        },
        "files_sha256": {
            str(p.relative_to(HERE)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in files
        },
        "native_implementation": "NOT RUN",
        "scientific_acceptance": "PENDING",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = audit()
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print("PASS proposed M1 wire packet:", report["counts"])
