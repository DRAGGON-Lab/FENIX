"""Independent installed-artifact checks for the bounded M0 alpha candidate.

Never imports FENIX. Expectations are derived by the accepted #29 reference
builder from approved templates/catalogs, not from either native compiler.
"""

import argparse
import copy
import hashlib
import json
import math
import statistics
import sys
import tomllib
from decimal import Decimal, localcontext
from pathlib import Path

import rfc8785
from jsonschema import Draft7Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "conformance/native"))
sys.path.insert(0, str(ROOT / "conformance/rejections"))
import reference as fir_reference  # noqa: E402 - repository-only tools need the local paths above
from common import blob, locked_dependencies, read_report, reference_model  # noqa: E402 - repository-only tools need the local paths above
from ode_common import METHODS, bits, make_references  # noqa: E402 - repository-only tools need the local paths above

CASES = ("baseline-five", "linear-production")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def finite_duration(value):
    require(
        type(value) in (float, int) and math.isfinite(value) and value >= 0,
        "nonfinite/negative timing",
    )


def expected_fingerprints():
    paths = [
        ROOT / p
        for p in (
            "packages/python/uv.lock",
            "conformance/julia_ode/Project.toml",
            "conformance/julia_ode/Manifest.toml",
            "conformance/production_decay/catalog.json",
        )
    ]
    for directory in (
        "packages/python/src",
        "packages/julia/src",
        "examples/m0",
        "benchmarks/m0",
    ):
        paths.extend(
            p for p in (ROOT / directory).rglob("*") if p.suffix in (".py", ".jl")
        )
    return {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in paths}


def validate_benchmark(report, language, case, method, revision, expected):
    require(report["format"] == "m0-benchmark-v1", "benchmark format")
    require(
        (
            report["language"],
            report["case"],
            report["method"],
            report["source_revision"],
        )
        == (language, case, method, revision),
        "benchmark identity",
    )
    require(report["validation"] == "PASS", "benchmark native validation failed")
    require(
        type(report["repeats"]) is int
        and report["repeats"] == 20
        and type(report["warmups"]) is int
        and report["warmups"] == 3,
        "benchmark requires 3 warmups and 20 repetitions",
    )
    finite_duration(report["package_load_seconds"])
    require(set(report["timings"]) == {"compile", "solve", "capture"}, "timing phases")
    require(set(report["first_seconds"]) == set(report["timings"]), "first-call phases")
    for phase, timing in report["timings"].items():
        finite_duration(report["first_seconds"][phase])
        samples = timing["seconds"]
        require(len(samples) == 20, "missing benchmark samples")
        for value in samples:
            finite_duration(value)
        require(
            (timing["median"], timing["min"], timing["max"])
            == (statistics.median(samples), min(samples), max(samples)),
            "incorrect timing summary",
        )
    settings = report["settings"]
    require(
        [bits(t) for t in settings["time_grid"]]
        == [s["time_bits"] for s in expected["samples"]],
        "benchmark grid",
    )
    require(
        (settings["rtol"], settings["atol"], settings["max_step"], settings["max_nfev"])
        == (1e-10, 1e-12, 1.0, 100000),
        "benchmark settings",
    )
    require(
        report["runtime"]["language_version"]
        == {"python": "3.12.13", "julia": "1.10.13"}[language],
        "runtime pin",
    )
    locked = locked_dependencies(language)
    dependencies = report["runtime"]["dependencies"]
    if language == "python":
        locked.pop("jsonschema")
    require(dependencies == locked, "unlocked dependency version")
    require(
        set(report["hardware"])
        >= {"os", "machine", "cpu", "threads", "logical_cpus", "runner_image"},
        "missing hardware configuration",
    )
    require(
        report["fingerprints"] == expected_fingerprints(),
        "incomplete/stale source fingerprints",
    )
    want = expected["artifacts"]
    require(
        report["identities"]
        == {
            "design": want["design"]["sha256"],
            "experiment": want["experiment"]["sha256"],
            "fir": want["identity"]["sha256"],
        },
        "benchmark source/FIR identities",
    )


def validate_example(directory, language, case, method, package_root, expected):
    summary = read_report(directory / "summary.json")
    require(
        (summary["format"], summary["language"], summary["case_id"], summary["method"])
        == ("m0-example-v1", language, case, method),
        "example identity",
    )
    loaded = Path(summary["package_path"])
    require(
        loaded.is_absolute()
        and loaded.resolve().is_relative_to(Path(package_root).resolve()),
        "package import fell back outside isolated installation",
    )
    required = {
        "design.json",
        "experiment.json",
        "fir.json",
        "model.canonical.json",
        "identity.canonical.json",
        "design.canonical.json",
        "experiment.canonical.json",
        "manifest.json",
        "result.json",
    }
    require(set(summary["checksums"]) == required, "missing/extra example artifact")
    for name, digest in summary["checksums"].items():
        require(
            sha((directory / name).read_bytes()) == digest, "artifact checksum: " + name
        )
    for artifact in ("model", "identity", "design", "experiment"):
        raw = (directory / (artifact + ".canonical.json")).read_bytes()
        require(
            raw == bytes.fromhex(expected["artifacts"][artifact]["hex"]),
            "independent canonical bytes: " + artifact,
        )
    manifest = read_report(directory / "manifest.json")
    result = read_report(directory / "result.json")
    schemas = [
        read_report(ROOT / "spec/results/proposals" / name)
        for name in (
            "run-manifest-m0.schema.json",
            "run-manifest-julia-sciml-m0.schema.json",
            "ode-result-m0.schema.json",
        )
    ]
    registry = Registry().with_resources(
        (s["$id"], Resource.from_contents(s)) for s in schemas
    )
    Draft7Validator(
        schemas[0 if language == "python" else 1], registry=registry
    ).validate(manifest)
    Draft7Validator(schemas[2], registry=registry).validate(result)
    require(
        manifest["execution"]
        == {
            "profile": "ode",
            "time_grid": result["times"],
            "rtol": 1e-10,
            "atol": 1e-12,
            "max_step": 1.0,
            "max_nfev": 100000,
        },
        "manifest execution settings",
    )
    want_fir = expected["artifacts"]["identity"]["sha256"]
    require(
        summary["fir_digest"]
        == manifest["fir"]["digest"]
        == result["fir_digest"]
        == want_fir,
        "FIR digest",
    )
    sources = {}
    for kind in ("design", "experiment"):
        source = read_report(directory / (kind + ".json"))
        sources[kind] = source
        want_digest = expected["artifacts"][kind]["sha256"]
        require(
            rfc8785.dumps(source["content"])
            == bytes.fromhex(expected["artifacts"][kind]["hex"]),
            "source transport content",
        )
        require(
            source["digest"]
            == summary[kind + "_digest"]
            == manifest["sources"][kind]["digest"]
            == want_digest,
            "source digest",
        )
        for key in ("schema_version", "id", "revision"):
            require(
                source["content"][key] == manifest["sources"][kind][key],
                "source reference",
            )
    require(
        manifest["output"]["sha256"] == sha((directory / "result.json").read_bytes()),
        "result checksum",
    )
    fir = read_report(directory / "fir.json")
    try:
        fir_reference.validate_model(fir)
        fir_reference.validate_producer(fir, sources["design"], sources["experiment"])
    except fir_reference.Rejection as error:
        raise ValueError(f"FIR provenance or model: {error}") from error
    if language == "python":
        package = tomllib.loads((ROOT / "packages/python/pyproject.toml").read_text())[
            "project"
        ]
    else:
        package = tomllib.loads((ROOT / "packages/julia/Project.toml").read_text())
    compiler = {key: package[key] for key in ("name", "version")}
    require(
        fir["provenance"].get("compiler") == compiler
        and all(manifest["producer"][key] == value for key, value in compiler.items()),
        "FIR provenance compiler differs from installed example producer",
    )
    require(
        reference_model(fir["model"])["model"] == expected["artifacts"]["model"],
        "FIR transport model",
    )
    require(manifest["backend"]["solver"]["method"] == method, "solver method")
    require(
        manifest["backend"]["profile"]
        == {
            "python": "python-scipy-ode/0.1.0",
            "julia": "julia-sciml-ode/0.1.0",
        }[language],
        "backend profile",
    )
    require(
        result["state_ids"] == ["x"]
        and result["state_units"] == ["molecule"]
        and result["time_unit"] == "s"
        and result["observable_ids"] == ["amount"]
        and result["observable_state_ids"] == ["x"]
        and result["observable_units"] == ["molecule"],
        "result identities/units",
    )
    require(
        [bits(t) for t in result["times"]]
        == [s["time_bits"] for s in expected["samples"]],
        "result grid",
    )
    require(
        len(result["state_values"]) == len(expected["samples"])
        and result["observable_values"] == result["state_values"],
        "sample coverage",
    )
    with localcontext() as context:
        context.prec = 100
        for row, sample in zip(
            result["state_values"], expected["samples"], strict=True
        ):
            require(len(row) == 1, "sample shape")
            value = row[0]
            require(
                type(value) in (int, float) and math.isfinite(value) and value >= 0,
                "nonfinite/negative count",
            )
            reference = Decimal(sample["expected"])
            bound = Decimal("1e-9") + Decimal("1e-8") * abs(reference)
            require(
                abs(Decimal.from_float(float(value)) - reference) <= bound,
                "P04 oracle mismatch",
            )
    return want_fir


# Source changes below follow existing P01/P02 identity rules; the mathematical
# model and all approved sample expectations remain exactly the original ones.
def revision_expectation(expected):
    revised = copy.deepcopy(expected)
    design = json.loads(bytes.fromhex(expected["artifacts"]["design"]["hex"]))
    design["revision"] = 2
    design["compartments"][0]["volume"]["value"] = 2e-15
    design["parameters"].reverse()
    design["functions"].reverse()
    design_bytes = rfc8785.dumps(design)
    experiment = json.loads(bytes.fromhex(expected["artifacts"]["experiment"]["hex"]))
    experiment["revision"] = 2
    experiment["design"]["revision"] = 2
    experiment["design"]["digest"] = sha(design_bytes)
    experiment["parameters"].reverse()
    experiment_bytes = rfc8785.dumps(experiment)
    revised["artifacts"]["design"] = blob(design_bytes)
    revised["artifacts"]["experiment"] = blob(experiment_bytes)
    revised["experiment"] = {"content": experiment, "digest": sha(experiment_bytes)}
    return revised


def validate_revision_workflow(
    directory, language, case, method, package_root, expected
):
    revised = revision_expectation(expected)
    identity = validate_example(
        directory / "original", language, case, method, package_root, expected
    )
    require(
        validate_example(
            directory / "revised", language, case, method, package_root, revised
        )
        == identity,
        "source revision changed mathematical identity",
    )
    diagnostics = {
        "same_revision_change": ("IMMUTABLE_REVISION", "/content/revision"),
        "old_experiment_new_design": ("DESIGN_REFERENCE", "/content/design/revision"),
        "old_fir_new_sources": ("SOURCE_DIGEST", "/provenance/design_digest"),
        "old_record_new_sources": ("REFERENCE", "/manifest/sources/design/revision"),
        "new_record_old_sources": ("REFERENCE", "/manifest/sources/design/revision"),
        "result_transport_checksum": ("CHECKSUM", "/manifest/output/sha256"),
        "manifest_transport_checksum": ("CHECKSUM", "/manifest"),
    }
    summary = read_report(directory / "summary.json")
    # Both revision and digest differ in these compound failures. P07 requires
    # rejection, but does not prescribe the order of source-member checks.
    for name in ("old_record_new_sources", "new_record_old_sources"):
        diagnostic = summary.get("rejections", {}).get(name, {})
        require(
            diagnostic.get("category") == "REFERENCE"
            and diagnostic.get("path")
            in (
                "/manifest/sources/design/revision",
                "/manifest/sources/design/digest",
            ),
            "source reference diagnostic",
        )
        diagnostics[name] = (diagnostic["category"], diagnostic["path"])
    require(
        summary
        == {
            "format": "m0-source-revisions-v1",
            "case": case,
            "method": method,
            "fir_digest": identity,
            "original_design_digest": expected["artifacts"]["design"]["sha256"],
            "original_experiment_digest": expected["artifacts"]["experiment"]["sha256"],
            "revised_design_digest": revised["artifacts"]["design"]["sha256"],
            "revised_experiment_digest": revised["artifacts"]["experiment"]["sha256"],
            "rejections": {
                name: {"category": category, "path": path}
                for name, (category, path) in diagnostics.items()
            },
        },
        "source revision workflow summary",
    )
    return identity


def verify(root, revision, package_roots):
    references = {s["id"]: s for s in make_references(revision)["scenarios"]}
    rows = []
    revision_rows = []
    for language in ("python", "julia"):
        for case in CASES:
            for method in METHODS[language]:
                directory = root / language / case / method
                identity = validate_example(
                    directory,
                    language,
                    case,
                    method,
                    package_roots[language],
                    references[case],
                )
                validate_benchmark(
                    read_report(directory / "benchmark.json"),
                    language,
                    case,
                    method,
                    revision,
                    references[case],
                )
                benchmark = read_report(directory / "benchmark.json")
                require(
                    Path(benchmark["package_path"]).is_absolute()
                    and Path(benchmark["package_path"])
                    .resolve()
                    .is_relative_to(Path(package_roots[language]).resolve()),
                    "benchmark import fallback",
                )
                revised_identity = validate_revision_workflow(
                    root / "source-revisions" / language / case / method,
                    language,
                    case,
                    method,
                    package_roots[language],
                    references[case],
                )
                require(revised_identity == identity, "workflow FIR identity")
                revision_rows.append(
                    {
                        "language": language,
                        "case": case,
                        "method": method,
                        "fir_digest": revised_identity,
                        "status": "PASS",
                    }
                )
                rows.append(
                    {
                        "language": language,
                        "case": case,
                        "method": method,
                        "fir_digest": identity,
                        "status": "PASS",
                    }
                )
    return {
        "format": "m0-alpha-comparison-v1",
        "source_revision": revision,
        "status": "PASS",
        "rows": rows,
        "source_revision_rows": revision_rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--python-package-root", required=True)
    parser.add_argument("--julia-package-root", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = verify(
        args.artifacts,
        args.source_revision,
        {"python": args.python_package_root, "julia": args.julia_package_root},
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(
        "PASS: eight installed example/benchmark combinations and eight source-revision workflows against independent references"
    )


if __name__ == "__main__":
    main()
