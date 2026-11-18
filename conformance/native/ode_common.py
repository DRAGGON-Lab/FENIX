"""Independent, test-only P04 reference preparation and numerical comparison."""

import copy
import math
import re
import struct
from decimal import Decimal, localcontext

import rfc8785
from common import (
    ROOT,
    blob,
    compare_bytes,
    fingerprints,
    load,
    locked_dependencies,
    sha,
)
from jsonschema import Draft7Validator

METHODS = {"python": ("DOP853", "Radau"), "julia": ("Tsit5", "Rodas5P")}


def bits(value):
    return struct.pack(">d", value).hex()


def decode(word):
    if not isinstance(word, str) or not re.fullmatch("[0-9a-f]{16}", word):
        raise ValueError("Expected binary64 hexadecimal word")
    value = struct.unpack(">d", bytes.fromhex(word))[0]
    if not math.isfinite(value) or value < 0:
        raise ValueError("Nonfinite or negative binary64 sample")
    return value


STUDIES = {
    name: {
        "rtol_bits": bits(r),
        "atol_bits": bits(a),
        "max_step_bits": bits(s),
        "max_nfev": 100000,
    }
    for name, r, a, s in [
        ("baseline", 1e-10, 1e-12, 1.0),
        ("refined", 1e-11, 1e-13, 0.5),
        ("coarse", 1e-9, 1e-11, 2.0),
    ]
}


def ode_fingerprints():
    result = fingerprints()
    for path in (
        "conformance/production_decay/catalog.json",
        "conformance/production_decay/catalog.schema.json",
        ".github/workflows/native-ode.yml",
    ):
        result[path] = sha((ROOT / path).read_bytes())
    return result


def make_references(revision):
    from common import reference_model

    if not re.fullmatch("[0-9a-f]{40}", revision):
        raise ValueError("Expected full source revision")
    catalog = load("conformance/production_decay/catalog.json")
    Draft7Validator(load("conformance/production_decay/catalog.schema.json")).validate(
        catalog
    )
    if (
        catalog["status"] != "APPROVED"
        or len(catalog["cases"]) != 10
        or sum(len(c["samples"]) for c in catalog["cases"]) != 40
    ):
        raise ValueError("Approved ten-case/40-sample catalog required")
    design = load("spec/fir/proposals/examples/sources/gfp-design.json")
    if sha(rfc8785.dumps(design["content"])) != design["digest"]:
        raise ValueError("Design identity mismatch")
    scenarios = []
    for case in catalog["cases"]:
        parameters = {k: decode(v) for k, v in case["parameters"].items()}
        content = copy.deepcopy(
            load("spec/fir/proposals/examples/sources/gfp-experiment.json")["content"]
        )
        content["id"] = "ode_" + case["id"]
        content["revision"] = 1
        for assignment in content["parameters"]:
            assignment["quantity"]["value"] = parameters[assignment["parameter"]]
        content["initial_counts"][0]["quantity"]["value"] = parameters["x0"]
        content["observables"][0]["id"] = "amount"
        experiment_bytes = rfc8785.dumps(content)
        experiment = {"content": content, "digest": sha(experiment_bytes)}
        model = copy.deepcopy(
            load("spec/fir/proposals/examples/production-decay-gfp.json")["model"]
        )
        for parameter in model["parameters"]:
            parameter["value"] = parameters[parameter["id"]]
        model["states"][0]["initial"] = parameters["x0"]
        model["observables"][0]["id"] = "amount"
        samples = sorted(case["samples"], key=lambda s: decode(s["time_bits"]))
        times = [decode(s["time_bits"]) for s in samples]
        if len(set(times)) != len(times):
            raise ValueError("Duplicate reference sample times")
        scenarios.append(
            {
                "id": case["id"],
                "parameters": case["parameters"],
                "samples": samples,
                "experiment": experiment,
                "artifacts": dict(
                    reference_model(model),
                    design=blob(rfc8785.dumps(design["content"])),
                    experiment=blob(experiment_bytes),
                ),
            }
        )
    return {
        "format": "native-ode-references-v1",
        "source_revision": revision,
        "fingerprints": ode_fingerprints(),
        "studies": copy.deepcopy(STUDIES),
        "scenarios": scenarios,
    }


def validate_references(manifest, revision):
    Draft7Validator(load("conformance/native/ode-references.schema.json")).validate(
        manifest
    )
    if manifest != make_references(revision):
        raise ValueError("Stale or corrupted independent reference manifest")


def controls(language):
    return [
        {
            "id": cid,
            "method": method,
            "outcome": "reject",
            "category": category,
            "path": path,
            "nfev": count,
        }
        for method in METHODS[language]
        for cid, category, path, count in (
            ("unit-rejection", "UNIT", "/parameters/0/quantity/unit", 0),
            ("unsupported-profile", "UNSUPPORTED_PROFILE", "/profile", 0),
            ("work-limit", "WORK_LIMIT", "", 1),
        )
    ]


def validate_ode_report(report, revision, manifest=None):
    Draft7Validator(load("conformance/native/ode-report.schema.json")).validate(report)
    if report["failures"]:
        raise ValueError("Native solver failure: " + str(report["failures"]))
    refs = make_references(revision)
    if manifest is not None:
        validate_references(manifest, revision)
    if (
        report["source_revision"] != revision
        or report["fingerprints"] != refs["fingerprints"]
    ):
        raise ValueError("Source revision/fingerprint mismatch")
    language = report["implementation"]
    runtime = report["runtime"]
    if (
        runtime["name"] != {"python": "CPython", "julia": "Julia"}[language]
        or runtime["version"] != {"python": "3.12.13", "julia": "1.10.13"}[language]
        or runtime["dependencies"] != locked_dependencies(language)
    ):
        raise ValueError("Incorrect runtime or locked dependency identity")
    expected = {c["id"]: c for c in refs["scenarios"]}
    scenarios = {c["id"]: c for c in report["scenarios"]}
    if (
        len(scenarios) != len(report["scenarios"])
        or scenarios.keys() != expected.keys()
    ):
        raise ValueError("Missing/duplicate/extra scenarios")
    for cid, want in expected.items():
        for phase in ("artifacts", "after_artifacts"):
            got = scenarios[cid][phase]
            if got.keys() != want["artifacts"].keys():
                raise ValueError(cid + ": missing byte artifacts")
            for key, value in got.items():
                raw = bytes.fromhex(value["hex"])
                if sha(raw) != value["sha256"]:
                    raise ValueError(cid + "/" + key + ": digest/bytes mismatch")
                compare_bytes(
                    cid + "/" + phase + "/" + key,
                    bytes.fromhex(want["artifacts"][key]["hex"]),
                    raw,
                )
    index = {(r["case_id"], r["method"], r["study"]): r for r in report["runs"]}
    keys = {
        (cid, method, study)
        for cid in expected
        for method in METHODS[language]
        for study in STUDIES
    }
    if len(index) != len(report["runs"]) or index.keys() != keys:
        raise ValueError("Missing/duplicate/extra runs")
    for (cid, method, study), run in index.items():
        label = f"{cid}/{method}/{study}"
        want = expected[cid]
        if (
            run["settings"] != STUDIES[study]
            or run["fir_digest"] != want["artifacts"]["identity"]["sha256"]
        ):
            raise ValueError(label + ": incorrect settings or FIR identity")
        diagnostics = run["diagnostics"]
        if (
            set(diagnostics)
            != {"nfev", "njev", "nlu" if language == "python" else "nw"}
            or not 0 < diagnostics["nfev"] <= 100000
        ):
            raise ValueError(label + ": invalid counters")
        samples = run["samples"]
        if [s["time_bits"] for s in samples] != [
            s["time_bits"] for s in want["samples"]
        ]:
            raise ValueError(label + ": incomplete or misaligned samples")
        for sample in samples:
            decode(sample["time_bits"])
            decode(sample["state_bits"])
            decode(sample["observable_bits"])
            if sample["state_bits"] != sample["observable_bits"]:
                raise ValueError(label + ": direct observable differs from state")
    actual_controls = {(c["id"], c["method"]): c for c in report["controls"]}
    required = {(c["id"], c["method"]): c for c in controls(language)}
    if len(actual_controls) != len(report["controls"]) or actual_controls != required:
        raise ValueError("Incorrect or incomplete control diagnostics")
    return index


def compare_ode(reports, revision, manifest=None):
    if len(reports) != 2 or {r["implementation"] for r in reports} != set(METHODS):
        raise ValueError("Exactly one Python and one Julia report required")
    indexes = {
        r["implementation"]: validate_ode_report(r, revision, manifest) for r in reports
    }
    rows, pairs = [], []
    with localcontext() as context:
        context.prec = 100
        for case in make_references(revision)["scenarios"]:
            for study in STUDIES:
                for i, sample in enumerate(case["samples"]):
                    reference = Decimal(sample["expected"])
                    bound = Decimal("1e-9") + Decimal("1e-8") * abs(reference)
                    values = {}
                    words = {}
                    for language, methods in METHODS.items():
                        for method in methods:
                            word = indexes[language][case["id"], method, study][
                                "samples"
                            ][i]["state_bits"]
                            actual = Decimal.from_float(decode(word))
                            values[method] = actual
                            words[method] = word
                            error = abs(actual - reference)
                            rows.append(
                                {
                                    "case_id": case["id"],
                                    "method": method,
                                    "study": study,
                                    "time_bits": sample["time_bits"],
                                    "actual_bits": word,
                                    "reference": str(reference),
                                    "error": str(error),
                                    "bound": str(bound),
                                    "within_bound": error <= bound,
                                }
                            )
                    for python in METHODS["python"]:
                        for julia in METHODS["julia"]:
                            difference = abs(values[python] - values[julia])
                            pairs.append(
                                {
                                    "case_id": case["id"],
                                    "study": study,
                                    "time_bits": sample["time_bits"],
                                    "python_method": python,
                                    "julia_method": julia,
                                    "python_bits": words[python],
                                    "julia_bits": words[julia],
                                    "reference": str(reference),
                                    "difference": str(difference),
                                    "bound": str(2 * bound),
                                    "within_bound": difference <= 2 * bound,
                                }
                            )
    failed = [
        r for r in rows + pairs if r["study"] != "coarse" and not r["within_bound"]
    ]
    worst_cases = []
    with localcontext() as context:
        context.prec = 100
        for study in STUDIES:
            for kind, candidates, key in (
                ("reference", rows, "error"),
                ("pairwise", pairs, "difference"),
            ):
                selected = max(
                    (r for r in candidates if r["study"] == study),
                    key=lambda r: Decimal(r[key]) / Decimal(r["bound"]),
                )
                worst_cases.append(
                    {
                        "study": study,
                        "kind": kind,
                        "max_fraction_of_bound": str(
                            Decimal(selected[key]) / Decimal(selected["bound"])
                        ),
                        "comparison": selected,
                    }
                )
    result = {
        "worst_cases": worst_cases,
        "format": "native-ode-comparison-v1",
        "source_revision": revision,
        "fingerprints": ode_fingerprints(),
        "passed": not failed,
        "reference_comparisons": rows,
        "pairwise_comparisons": pairs,
        "failures": failed,
    }

    Draft7Validator(load("conformance/native/ode-comparison.schema.json")).validate(
        result
    )
    return result
