"""PROPOSED independent density-coordinate RK4 evidence; no SciPy or FENIX."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import platform
import sys
from itertools import pairwise
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CATALOG_SHA256 = "70932f56c47cddb7fd502b165580c65f8a34431721972fbf11a2588ab5c15d25"
STEPS_S = (2.5, 1.25, 0.625, 0.3125)
CANDIDATE_SCALED_LIMIT = 1e-5
COMPONENT_STEP_S = 1 / 256


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def catalog(path=HERE.parent / "cases.json"):
    require(sha256(path) == CATALOG_SHA256, "complete study catalog bytes differ")
    return json.loads(Path(path).read_bytes())


def density_field(case):
    """Derive density equations directly from P09, including expression states.

    Each intracellular count is divided by its owner's volume; medium totals
    are divided by medium volume. Thus extracellular transport is weighted by
    N_j*v_j/V, while all intracellular transport acts directly on densities.
    """
    community = case["model"] == "three_strain_mrna_protein_exchange"
    require(community or case["model"] == "single_cell_mrna_protein", "unknown model")
    p = {
        key: np.asarray(value, dtype=float) for key, value in case["parameters"].items()
    }
    volumes = np.array(
        case["cell_volumes_L"] if community else [case["cell_volume_L"]] * 3
    )
    scale = np.r_[volumes, volumes]
    if community:
        scale = np.r_[scale, np.repeat(volumes, 3), [case["medium_volume_L"]] * 3]
        capacities = np.array(case["populations"]) * volumes / case["medium_volume_L"]

    def rhs(density):
        require(density.shape == scale.shape, "state dimensions")
        require(np.all(np.isfinite(density)), "nonfinite RK4 stage")
        # Ring i senses its predecessor in the same representative cell.
        sensor = density[[8, 9, 13]] if community else density[[5, 3, 4]]
        require(np.all(sensor >= 0), "negative nonlinear sensor stage")
        low = sensor <= p["threshold_density"]
        gain = np.empty(3)
        gain[low] = 1 / (
            1 + (sensor[low] / p["threshold_density"][low]) ** p["hill_n"][low]
        )
        reciprocal = (p["threshold_density"][~low] / sensor[~low]) ** p["hill_n"][~low]
        gain[~low] = reciprocal / (1 + reciprocal)
        output = np.empty_like(density)
        output[:3] = (p["basal"] + p["induced"] * gain) / volumes - p[
            "mrna_decay"
        ] * density[:3]
        output[3:6] = p["translation"] * density[:3] - p["protein_decay"] * density[3:6]
        if community:
            intracellular = density[6:15].reshape(3, 3)
            # Flux densities have no cell-volume conversion on this side.
            outward = p["export"] * intracellular
            inward = p["import"] * density[15:18]
            change = inward - outward - p["intracellular_signal_decay"] * intracellular
            for i in range(3):
                change[i, i] += p["signal_synthesis"][i] * density[3 + i]
            output[6:15] = change.ravel()
            output[15:18] = (
                capacities @ (outward - inward)
                - p["medium_signal_decay"] * density[15:18]
            )
        require(np.all(np.isfinite(output)), "nonfinite RK4 derivative")
        return output

    return scale, rhs


def integrate(case, step_s, end_s, sample_step_s):
    for value in (step_s, end_s, sample_step_s):
        require(
            type(value) in (int, float) and math.isfinite(value) and value > 0,
            "positive finite integration settings required",
        )
    steps_per_sample = sample_step_s / step_s
    sample_intervals = end_s / sample_step_s
    require(
        steps_per_sample.is_integer() and sample_intervals.is_integer(),
        "unaligned RK4/sample grid",
    )
    stride, intervals = int(steps_per_sample), int(sample_intervals)
    require(1 <= stride * intervals <= 2_000_000, "RK4 work budget")
    scale, rhs = density_field(case)
    initial = np.array(case["initial_counts"], dtype=float)
    require(
        initial.shape == scale.shape
        and np.all(np.isfinite(initial))
        and np.all(initial >= 0),
        "invalid initial counts",
    )
    density = initial / scale
    values = np.empty((intervals + 1, len(scale)))
    values[0] = case["initial_counts"]
    with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
        for index in range(1, stride * intervals + 1):
            k1 = rhs(density)
            k2 = rhs(density + step_s * k1 / 2)
            k3 = rhs(density + step_s * k2 / 2)
            k4 = rhs(density + step_s * k3)
            density = density + (step_s / 6) * (k1 + 2 * k2 + 2 * k3 + k4)
            if index % stride == 0:
                counts = density * scale
                require(
                    np.all(np.isfinite(counts)) and np.all(counts >= 0),
                    "invalid RK4 returned counts; no clipping",
                )
                values[index // stride] = counts
    return np.arange(intervals + 1) * sample_step_s, values


def component_checks():
    # Fixed local analytical reference module; never import the SciPy evaluator.
    sys.path.insert(0, str(HERE.parent / "references"))
    import reference as analytical

    analytical.catalog()  # Complete component catalog pin precedes binary64 parsing.
    cases = json.loads((analytical.HERE / "cases.json").read_bytes())["cases"]
    worst, count = 0.0, 0
    for case in cases:
        _, values = integrate(case, COMPONENT_STEP_S, 4, 1)
        for time in case["times"]:
            expected = np.array([float(x) for x in analytical.state(case["id"], time)])
            bound = 1e-9 + 1e-8 * np.abs(expected)
            ratio = np.abs(values[time] - expected) / bound
            require(np.all(ratio <= 1), "RK4 component-law disagreement: " + case["id"])
            worst = max(worst, float(np.max(ratio)))
            count += len(expected)
    return {
        "comparisons": count,
        "step_s": COMPONENT_STEP_S,
        "candidate_comparison_bound": "1e-9 + 1e-8 * abs(analytical)",
        "max_error_to_candidate_bound": worst,
        "catalog_sha256": analytical.CATALOG_SHA256,
        "evaluator_sha256": sha256(analytical.__file__),
    }


def scaled_errors(actual, reference):
    require(actual.shape == reference.shape and actual.ndim == 2, "trace dimensions")
    require(
        np.all(np.isfinite(actual)) and np.all(np.isfinite(reference)), "invalid trace"
    )
    absolute = np.max(np.abs(actual - reference), axis=0)
    scale = np.maximum(1, np.max(np.abs(reference), axis=0))
    return {
        "absolute_per_state": absolute.tolist(),
        "scaled_per_state": (absolute / scale).tolist(),
    }


def columns(case):
    names = [f"mRNA_{i}" for i in range(1, 4)] + [f"protein_{i}" for i in range(1, 4)]
    if case["model"] == "three_strain_mrna_protein_exchange":
        names += [f"strain{j}.signal{k}" for j in range(1, 4) for k in range(1, 4)]
        names += [f"medium.signal{k}" for k in range(1, 4)]
    return ["time_s", *names]


def cycle_summary(times, values, start, end):
    """Independent midpoint upcrossings; observations, not a new classifier."""
    selected = (times >= start) & (times <= end)
    t = times[selected]
    rows = []
    for index in range(3, 6):
        y = values[selected, index]
        lower, upper = float(np.min(y)), float(np.max(y))
        level = (lower + upper) / 2
        indices = np.flatnonzero((y[:-1] <= level) & (y[1:] > level))
        crossings = t[indices] + (level - y[indices]) * (
            t[indices + 1] - t[indices]
        ) / (y[indices + 1] - y[indices])
        rows.append(
            {
                "minimum_count_per_cell": lower,
                "maximum_count_per_cell": upper,
                "midpoint_upcrossings_s": crossings.tolist(),
                "mean_period_s": float(np.mean(np.diff(crossings)))
                if len(crossings) >= 2
                else None,
            }
        )
    return {"start_s": start, "end_s": end, "proteins": rows}


def load_study(directory, definitions):
    """Check source context and trace integrity before numerical comparisons.

    Checksums bind files to a report, without authenticating either artifact.
    The independent density solution supplies the numerical comparison.
    """
    report = json.loads((directory / "report.json").read_bytes())
    require(report["catalog_sha256"] == CATALOG_SHA256, "study catalog mismatch")
    require(
        report["evaluator_sha256"] == sha256(HERE.parent / "study.py"),
        "study source mismatch",
    )
    require(
        report["protocol"] == definitions["protocol"]
        and report["cases"] == definitions["cases"],
        "study definitions mismatch",
    )
    require(
        report["feasibility_checks"] == "PASS" and report["failures"] == [],
        "study failed",
    )
    runs = {(r["case"], r["method"], r["refined"]): r for r in report["runs"]}
    expected_runs = (
        {
            (case["id"], method, refined)
            for case in definitions["cases"]
            for method in ("DOP853", "Radau")
            for refined in (False, True)
        }
        | {
            (case["id"] + "-hill1-control", "Radau", True)
            for case in definitions["cases"]
        }
        | {(definitions["cases"][1]["id"] + "-absent-signal3-control", "Radau", True)}
    )
    require(
        set(runs) == expected_runs and len(report["runs"]) == 11,
        "incomplete/duplicate study runs",
    )
    traces = {}
    end = 2 * definitions["protocol"]["horizon_s"]
    sample = definitions["protocol"]["sample_step_s"]
    grid = np.arange(round(end / sample) + 1) * sample
    for case in definitions["cases"]:
        for method in ("DOP853", "Radau"):
            for refined in (False, True):
                key = (case["id"], method, refined)
                require(key in runs, "missing primary run")
                filename = f"{case['id']}-{method}-{'refined' if refined else 'baseline'}.csv.gz"
                artifact = runs[key]["trajectory"]
                require(artifact["path"] == filename, "wrong trace path")
                require(
                    artifact["samples"] == len(grid)
                    and artifact["columns"] == columns(case),
                    "study trace column/sample metadata",
                )
                path = directory / filename
                require(
                    artifact["sha256"] == sha256(path), "study trace checksum mismatch"
                )
                with gzip.open(path, "rt") as stream:
                    require(
                        stream.readline().strip() == "# " + ",".join(columns(case)),
                        "study trace header",
                    )
                values = np.loadtxt(path, delimiter=",")
                require(
                    values.shape == (len(grid), len(case["initial_counts"]) + 1),
                    "study trace shape",
                )
                require(np.array_equal(values[:, 0], grid), "study trace grid")
                require(
                    np.all(np.isfinite(values)) and np.all(values[:, 1:] >= 0),
                    "invalid study counts",
                )
                require(
                    np.array_equal(values[0, 1:], case["initial_counts"]),
                    "study initial state",
                )
                traces[key] = values[:, 1:]
    return report, traces


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    destination = args.output_dir.resolve()
    require(
        not destination.is_relative_to(ROOT)
        or destination.is_relative_to(ROOT / "artifacts"),
        "checkout output must be under artifacts/",
    )
    destination.mkdir(parents=True, exist_ok=False)
    definitions = catalog()
    _, study_traces = load_study(args.study_dir, definitions)
    report = {
        "status": "PROPOSED_INDEPENDENT_NUMERICAL_STUDY",
        "native_fenix": "NOT_RUN_UNSUPPORTED_PROFILE",
        "catalog_sha256": CATALOG_SHA256,
        "evaluator_sha256": sha256(__file__),
        "study_report_sha256": sha256(args.study_dir / "report.json"),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "lock_sha256": sha256(HERE.parent / "uv.lock"),
        "definitions": definitions,
        "steps_s": STEPS_S,
        "candidate_scaled_limit": CANDIDATE_SCALED_LIMIT,
        "components": component_checks(),
        "cases": [],
    }
    for case in definitions["cases"]:
        results = []
        row = {
            "case": case["id"],
            "trajectories": [],
            "refinement": [],
            "adaptive_comparisons": [],
        }
        for step in STEPS_S:
            print(f"Independent density RK4: {case['id']} step={step} s", flush=True)
            times, values = integrate(
                case,
                step,
                2 * definitions["protocol"]["horizon_s"],
                definitions["protocol"]["sample_step_s"],
            )
            path = destination / f"{case['id']}-RK4-{step}.csv.gz"
            np.savetxt(
                path,
                np.column_stack((times, values)),
                delimiter=",",
                header=",".join(columns(case)),
            )
            row["trajectories"].append(
                {
                    "step_s": step,
                    "path": path.name,
                    "sha256": sha256(path),
                    "samples": len(times),
                    "columns": columns(case),
                    "rhs_calls": 4 * round(times[-1] / step),
                }
            )
            results.append(values)
        horizon, transient = (
            definitions["protocol"]["horizon_s"],
            definitions["protocol"]["transient_s"],
        )
        row["cycle_observations"] = [
            cycle_summary(times, results[-1], transient, horizon),
            cycle_summary(times, results[-1], horizon + transient, 2 * horizon),
        ]
        gaps = []
        for i in range(1, len(results)):
            errors = scaled_errors(results[i - 1], results[i])
            gaps.append(max(errors["scaled_per_state"]))
            row["refinement"].append(
                {"coarse_step_s": STEPS_S[i - 1], "fine_step_s": STEPS_S[i], **errors}
            )
        row["observed_orders"] = [
            math.log2(a / b) if a > 0 and b > 0 else None for a, b in pairwise(gaps)
        ]
        row["refinement_passed"] = bool(
            all(a > b for a, b in pairwise(gaps)) and gaps[-1] <= CANDIDATE_SCALED_LIMIT
        )
        for (case_id, method, refined), values in study_traces.items():
            if case_id != case["id"]:
                continue
            errors = scaled_errors(values, results[-1])
            row["adaptive_comparisons"].append(
                {
                    "method": method,
                    "refined": refined,
                    **errors,
                    "passed": max(errors["scaled_per_state"]) <= CANDIDATE_SCALED_LIMIT,
                }
            )
        report["cases"].append(row)
    passed = all(
        r["refinement_passed"] and all(c["passed"] for c in r["adaptive_comparisons"])
        for r in report["cases"]
    )
    report["candidate_checks"] = "PASS" if passed else "FAIL"
    (destination / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    print(report["candidate_checks"], flush=True)
    return not passed


if __name__ == "__main__":
    raise SystemExit(main())
