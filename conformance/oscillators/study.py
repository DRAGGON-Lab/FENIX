"""PROPOSED mathematical feasibility studies; never imports or executes FENIX."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import platform
from pathlib import Path

import numpy as np
import scipy
from scipy.integrate import solve_ivp
from scipy.signal import find_peaks

HERE = Path(__file__).resolve().parent
PREVIOUS = np.array([2, 0, 1])
BASE_PARAMETERS = {
    "basal",
    "induced",
    "mrna_decay",
    "translation",
    "protein_decay",
    "threshold_density",
    "hill_n",
}
SIGNAL_PARAMETERS = {
    "signal_synthesis",
    "intracellular_signal_decay",
    "medium_signal_decay",
    "export",
    "import",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def numeric_array(value, shape, name):
    if not shape:
        require(
            type(value) in (int, float) and math.isfinite(value) and value >= 0,
            "numeric type/range: " + name,
        )
        return
    require(type(value) is list and len(value) == shape[0], "array shape: " + name)
    for child in value:
        numeric_array(child, shape[1:], name)


def validate_catalog(catalog):
    require(
        set(catalog) == {"format", "status", "units", "bases", "protocol", "cases"},
        "unknown/missing catalog fields",
    )
    require(
        catalog["status"] == "PROPOSED"
        and catalog["format"] == "fenix.repressilator-candidate/1",
        "unknown catalog status/format",
    )
    require(
        catalog["units"]
        == {
            "time": "s",
            "volume": "L",
            "state": "molecule",
            "threshold_density": "molecule/L",
            "basal": "molecule/s",
            "induced": "molecule/s",
            "first_order_rates": "1/s",
            "hill_n": "1",
        },
        "catalog quantity units",
    )
    require(
        catalog["bases"]
        == {
            "intracellular": "expected count per representative cell",
            "medium": "total count",
            "translation": "protein molecules per transcript molecule per second",
            "signal_synthesis": "signal molecules per synthase molecule per second",
        },
        "catalog quantity bases",
    )
    protocol = catalog["protocol"]
    require(
        set(protocol)
        == {
            "horizon_s",
            "sample_step_s",
            "transient_s",
            "methods",
            "rtol",
            "atol",
            "refined_rtol",
            "refined_atol",
            "max_step_s",
            "max_nfev",
            "min_peaks",
            "min_prominence_threshold_fraction",
            "max_period_cv",
            "max_amplitude_cv",
            "max_extension_period_drift",
            "max_extension_amplitude_drift",
            "min_peak_distance_s",
            "max_phase_spacing_error",
            "max_method_period_drift",
            "max_method_amplitude_drift",
            "max_extension_level_drift",
            "max_method_phase_drift_cycles",
        },
        "protocol fields",
    )
    require(
        protocol["methods"] == ["DOP853", "Radau"], "both declared methods required"
    )
    for key, value in protocol.items():
        if key == "methods":
            continue
        require(
            type(value) in (int, float) and math.isfinite(value) and value >= 0,
            "protocol numeric type/range: " + key,
        )
        if key != "transient_s":
            require(value > 0, "positive protocol value: " + key)
    require(
        type(protocol["max_nfev"]) is int
        and type(protocol["min_peaks"]) is int
        and protocol["min_peaks"] >= 3,
        "integer budgets/peak counts required",
    )
    require(
        protocol["transient_s"] < protocol["horizon_s"],
        "transient must precede horizon",
    )
    points = protocol["horizon_s"] / protocol["sample_step_s"]
    require(
        math.isfinite(points) and points.is_integer() and 1 <= points <= 500000,
        "finite aligned sampling grid required",
    )
    require(
        [c["id"] for c in catalog["cases"]] == ["single-cell", "three-strain"],
        "complete two-case study required",
    )
    for case in catalog["cases"]:
        validate(case)


def validate(case):
    common = {"id", "model", "parameters", "initial_counts"}
    community = case.get("model") == "three_strain_mrna_protein_exchange"
    require(
        community or case.get("model") == "single_cell_mrna_protein", "unknown model"
    )
    require(
        set(case)
        == common
        | (
            {"cell_volumes_L", "populations", "medium_volume_L"}
            if community
            else {"cell_volume_L"}
        ),
        "unknown/missing case fields",
    )
    p = case["parameters"]
    require(
        set(p) == BASE_PARAMETERS | (SIGNAL_PARAMETERS if community else set()),
        "unknown/missing parameters",
    )
    for key, value in p.items():
        expected_shape = (
            (3, 3)
            if key in ("intracellular_signal_decay", "export", "import")
            else (3,)
        )
        numeric_array(value, expected_shape, key)
        array = np.asarray(value)
        require(
            array.shape == expected_shape and array.dtype.kind in "fi",
            "parameter shape/type: " + key,
        )
        require(
            np.all(np.isfinite(array)) and np.all(array >= 0), "parameter range: " + key
        )
    require(
        all(type(n) is int and 1 <= n <= 4 for n in p["hill_n"]),
        "Hill exponents must be integers in 1..4",
    )
    require(all(k > 0 for k in p["threshold_density"]), "positive thresholds required")
    numeric_array(case["initial_counts"], (18 if community else 6,), "initial counts")
    initial = np.asarray(case["initial_counts"])
    require(
        initial.shape == (18 if community else 6,) and initial.dtype.kind in "fi",
        "initial shape/type",
    )
    require(np.all(np.isfinite(initial)) and np.all(initial >= 0), "initial counts")
    volumes = (
        case["cell_volumes_L"] + [case["medium_volume_L"]]
        if community
        else [case["cell_volume_L"]]
    )
    require(len(volumes) == (4 if community else 1), "volume shape")
    require(
        all(type(v) in (int, float) and math.isfinite(v) and v > 0 for v in volumes),
        "positive finite volumes",
    )
    if community:
        require(
            len(case["populations"]) == 3
            and all(type(n) is int and 1 <= n < 2**53 for n in case["populations"]),
            "fixed positive portable populations",
        )
    return community


def repression(density, threshold, exponent):
    density = np.asarray(density)
    require(
        np.all(np.isfinite(density)) and np.all(density >= 0), "undefined sensor stage"
    )
    low = density <= threshold
    ratio = np.empty_like(density, dtype=float)
    ratio[low] = density[low] / threshold[low]
    ratio[~low] = threshold[~low] / density[~low]
    power = ratio**exponent
    return np.where(density <= threshold, 1 / (1 + power), power / (1 + power))


def field(case):
    community = validate(case)
    p = {
        key: np.asarray(value, dtype=float) for key, value in case["parameters"].items()
    }
    v = np.asarray(case["cell_volumes_L"] if community else [case["cell_volume_L"]] * 3)
    populations = np.asarray(case["populations"], dtype=float) if community else None
    medium = case.get("medium_volume_L")

    def rhs(time, state):
        require(np.all(np.isfinite(state)), "nonfinite stage")
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            m, protein = state[:3], state[3:6]
            amounts = state[6:15].reshape(3, 3) if community else None
            sensor = amounts[np.arange(3), PREVIOUS] if community else protein[PREVIOUS]
            activation = repression(sensor / v, p["threshold_density"], p["hill_n"])
            dm = p["basal"] + p["induced"] * activation - p["mrna_decay"] * m
            dp = p["translation"] * m - p["protein_decay"] * protein
            if not community:
                output = np.concatenate((dm, dp))
            else:
                external = state[15:18]
                flux = (
                    p["export"] * amounts
                    - p["import"] * v[:, None] * external[None, :] / medium
                )
                da = (
                    np.diag(p["signal_synthesis"] * protein)
                    - p["intracellular_signal_decay"] * amounts
                    - flux
                )
                de = (populations[:, None] * flux).sum(axis=0) - p[
                    "medium_signal_decay"
                ] * external
                output = np.concatenate((dm, dp, da.ravel(), de))
            require(np.all(np.isfinite(output)), "nonfinite RHS")
            return output

    def jacobian(time, state):
        amounts = state[6:15].reshape(3, 3) if community else None
        sensor = amounts[np.arange(3), PREVIOUS] if community else state[3:6][PREVIOUS]
        density = sensor / v
        g = repression(density, p["threshold_density"], p["hill_n"])
        derivative = np.empty(3)
        for i in range(3):
            derivative[i] = (
                -p["hill_n"][i] * g[i] * (1 - g[i]) / sensor[i]
                if sensor[i] > 0
                else (
                    -1 / (v[i] * p["threshold_density"][i])
                    if p["hill_n"][i] == 1
                    else 0
                )
            )
        matrix = np.zeros((18 if community else 6,) * 2)
        for i in range(3):
            matrix[i, i] = -p["mrna_decay"][i]
            matrix[i, 6 + i * 3 + PREVIOUS[i] if community else 3 + PREVIOUS[i]] = (
                p["induced"][i] * derivative[i]
            )
            matrix[3 + i, i] = p["translation"][i]
            matrix[3 + i, 3 + i] = -p["protein_decay"][i]
        if community:
            for j in range(3):
                for k in range(3):
                    at = 6 + 3 * j + k
                    matrix[at, at] = (
                        -p["intracellular_signal_decay"][j, k] - p["export"][j, k]
                    )
                    matrix[at, 15 + k] = p["import"][j, k] * v[j] / medium
                    matrix[15 + k, at] = populations[j] * p["export"][j, k]
                    if j == k:
                        matrix[at, 3 + k] = p["signal_synthesis"][k]
            for k in range(3):
                matrix[15 + k, 15 + k] = (
                    -p["medium_signal_decay"][k]
                    - (populations * p["import"][:, k] * v / medium).sum()
                )
        require(np.all(np.isfinite(matrix)), "nonfinite Jacobian")
        return matrix

    return rhs, jacobian


def labels(case):
    names = [f"mRNA_{i + 1}" for i in range(3)] + [f"protein_{i + 1}" for i in range(3)]
    if "populations" in case:
        names += [f"strain{j + 1}.signal{k + 1}" for j in range(3) for k in range(3)]
        names += [f"medium.signal{k + 1}" for k in range(3)]
    return names


def simulate(case, protocol, method, refined=False, extend=True):
    rhs, jac = field(case)
    budget = protocol["max_nfev"]
    calls = 0

    def counted(time, state):
        nonlocal calls
        calls += 1
        require(calls <= budget, "RHS budget exhausted")
        return rhs(time, state)

    end = protocol["horizon_s"] * (2 if extend else 1)
    grid = np.arange(0, end + protocol["sample_step_s"] / 2, protocol["sample_step_s"])
    solution = solve_ivp(
        counted,
        (0.0, end),
        case["initial_counts"],
        method=method,
        t_eval=grid,
        rtol=protocol["refined_rtol" if refined else "rtol"],
        atol=protocol["refined_atol" if refined else "atol"],
        max_step=protocol["max_step_s"],
        **({"jac": jac} if method == "Radau" else {}),
    )
    require(
        solution.success
        and solution.y.shape == (len(case["initial_counts"]), len(grid)),
        "incomplete integration",
    )
    require(
        np.array_equal(solution.t, grid)
        and np.all(np.isfinite(solution.y))
        and np.all(solution.y >= 0),
        "invalid returned samples; no clipping is allowed",
    )
    return (
        grid,
        solution.y.T,
        {
            "rhs_calls": calls,
            "nfev": solution.nfev,
            "njev": solution.njev,
            "nlu": solution.nlu,
        },
    )


def window_metrics(case, protocol, times, values, start, end):
    chosen = (times >= start) & (times <= end)
    t, protein = times[chosen], values[chosen, 3:6]
    volumes = np.asarray(case.get("cell_volumes_L", [case.get("cell_volume_L")] * 3))
    threshold_counts = volumes * np.asarray(case["parameters"]["threshold_density"])
    rows, peak_times = [], []
    for i in range(3):
        peaks, _ = find_peaks(
            protein[:, i],
            prominence=protocol["min_prominence_threshold_fraction"]
            * threshold_counts[i],
            distance=max(
                1, round(protocol["min_peak_distance_s"] / protocol["sample_step_s"])
            ),
        )
        # Only peaks bracketed by earlier/later peaks define complete cycles;
        # partial cycles at analysis-window edges cannot depress amplitude.
        interior = peaks[1:-1]
        count = len(interior)
        periods = np.diff(t[interior[-protocol["min_peaks"] :]])
        troughs = np.array(
            [
                max(
                    np.min(protein[peaks[j - 1] : peaks[j] + 1, i]),
                    np.min(protein[peaks[j] : peaks[j + 1] + 1, i]),
                )
                for j in range(1, len(peaks) - 1)
            ]
        )[-protocol["min_peaks"] :]
        heights = protein[interior[-protocol["min_peaks"] :], i]
        amplitudes = heights - troughs
        mean_level = float(np.mean((heights + troughs) / 2)) if len(heights) else None
        mean_period = float(np.mean(periods)) if len(periods) else None
        mean_amplitude = float(np.mean(amplitudes)) if len(amplitudes) else None
        period_cv = float(np.std(periods) / mean_period) if mean_period else None
        amplitude_cv = (
            float(np.std(amplitudes) / mean_amplitude) if mean_amplitude else None
        )
        rows.append(
            {
                "peak_count": count,
                "cycle_midline_molecules_per_cell": mean_level,
                "period_s": mean_period,
                "prominence_molecules_per_cell": mean_amplitude,
                "period_cv": period_cv,
                "amplitude_cv": amplitude_cv,
                "oscillatory_window": count >= protocol["min_peaks"]
                and period_cv is not None
                and period_cv <= protocol["max_period_cv"]
                and amplitude_cv <= protocol["max_amplitude_cv"],
            }
        )
        peak_times.append(t[interior])
    phases = None
    if all(row["oscillatory_window"] for row in rows):
        period = rows[0]["period_s"]
        reference = peak_times[0][-protocol["min_peaks"]]
        phases = [
            float(
                np.angle(
                    np.mean(
                        np.exp(
                            2j
                            * np.pi
                            * (peaks[-protocol["min_peaks"] :] - reference)
                            / period
                        )
                    )
                )
                / (2 * np.pi)
                % 1
            )
            for peaks in peak_times
        ]
        spacing = np.diff(np.r_[np.sort(phases), np.sort(phases)[0] + 1])
        separated = bool(
            np.max(np.abs(spacing - 1 / 3)) <= protocol["max_phase_spacing_error"]
        )
    else:
        separated = False
    return {
        "start_s": start,
        "end_s": end,
        "proteins": rows,
        "phase_cycles": phases,
        "phase_separated": separated,
    }


def oscillation_metrics(case, protocol, times, values):
    horizon, transient = protocol["horizon_s"], protocol["transient_s"]
    first = window_metrics(case, protocol, times, values, transient, horizon)
    late = window_metrics(
        case, protocol, times, values, horizon + transient, 2 * horizon
    )
    sustained = first["phase_separated"] and late["phase_separated"]
    drift = []
    for a, b in zip(first["proteins"], late["proteins"], strict=True):
        if a["oscillatory_window"] and b["oscillatory_window"]:
            pd = abs(b["period_s"] / a["period_s"] - 1)
            ad = abs(
                b["prominence_molecules_per_cell"] / a["prominence_molecules_per_cell"]
                - 1
            )
            scale = max(1.0, abs(a["cycle_midline_molecules_per_cell"]))
            level_drift = (
                abs(
                    b["cycle_midline_molecules_per_cell"]
                    - a["cycle_midline_molecules_per_cell"]
                )
                / scale
            )
            drift.append(
                {
                    "period_fraction": pd,
                    "amplitude_fraction": ad,
                    "level_fraction": level_drift,
                }
            )
            sustained = (
                sustained and level_drift <= protocol["max_extension_level_drift"]
            )
            sustained = (
                sustained
                and pd <= protocol["max_extension_period_drift"]
                and ad <= protocol["max_extension_amplitude_drift"]
            )
        else:
            sustained = False
            drift.append(None)
    return {
        "first_window": first,
        "extended_window": late,
        "extension_drift": drift,
        "sustained_candidate": bool(sustained),
    }


def controls(cases):
    output = []
    for case in cases:
        low = copy.deepcopy(case)
        low["id"] += "-hill1-control"
        low["parameters"]["hill_n"] = [1, 1, 1]
        output.append(low)
    broken = copy.deepcopy(cases[1])
    broken["id"] += "-absent-signal3-control"
    broken["parameters"]["signal_synthesis"][2] = 0.0
    for index in (8, 11, 14, 17):
        broken["initial_counts"][index] = 0.0
    output.append(broken)
    return output


def plot_candidates(destination, studies, cases, protocol):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(
        3, 1, figsize=(10, 9), sharex=True, constrained_layout=True
    )
    colors = ("#2166ac", "#d6604d", "#4d9221")
    for axis, case in zip(axes[:2], cases, strict=True):
        time, values = studies[(case["id"], "Radau", True)]
        for i, color in enumerate(colors):
            axis.plot(
                time,
                values[:, 3 + i],
                color=color,
                label=f"gate {i + 1}",
                linewidth=1.0,
            )
        axis.set_ylabel("protein count / cell")
        axis.set_title(
            "One cell: three repressors"
            if case is cases[0]
            else "Three strains: one NOT gate per strain"
        )
        axis.axvline(
            protocol["transient_s"], color="gray", linestyle="--", linewidth=0.8
        )
        axis.legend(ncol=3, loc="upper right")
    time, values = studies[(cases[1]["id"], "Radau", True)]
    for k, color in enumerate(colors):
        axes[2].plot(
            time,
            values[:, 15 + k] / cases[1]["medium_volume_L"],
            color=color,
            label=f"medium signal {k + 1}",
            linewidth=1.0,
        )
    axes[2].set_ylabel("medium density (molecule/L)")
    axes[2].set_xlabel("time (s)")
    axes[2].legend(ncol=3, loc="upper right")
    figure.suptitle(
        "PROPOSED independent feasibility study — native FENIX execution NOT RUN",
        fontsize=11,
    )
    figure.savefig(destination / "repressilators.png", dpi=180)
    figure.savefig(destination / "repressilators.svg")
    plt.close(figure)
    # A separate detail view makes the phase relationships readable.
    figure, axes = plt.subplots(
        3, 1, figsize=(10, 8), sharex=True, constrained_layout=True
    )
    end = 2 * protocol["horizon_s"]
    for row, case in enumerate(cases):
        time, values = studies[(case["id"], "Radau", True)]
        keep = time >= end - 6000
        for i, color in enumerate(colors):
            axes[row].plot(
                time[keep], values[keep, 3 + i], color=color, label=f"gate {i + 1}"
            )
        axes[row].set_ylabel("protein count / cell")
        axes[row].set_title(
            "Single cell" if row == 0 else "Three strains: one NOT gate each"
        )
        axes[row].legend(ncol=3)
    time, values = studies[(cases[1]["id"], "Radau", True)]
    keep = time >= end - 6000
    for k, color in enumerate(colors):
        axes[2].plot(
            time[keep],
            values[keep, 15 + k] / cases[1]["medium_volume_L"],
            color=color,
            label=f"signal {k + 1}",
        )
    axes[2].set_ylabel("medium density (molecule/L)")
    axes[2].set_xlabel("time (s)")
    axes[2].legend(ncol=3)
    figure.suptitle(
        "PROPOSED study: phase detail — native FENIX execution NOT RUN", fontsize=11
    )
    figure.savefig(destination / "repressilators-detail.png", dpi=180)
    figure.savefig(destination / "repressilators-detail.svg")
    plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    destination = args.output_dir.resolve()
    root = HERE.parents[1]
    require(
        not destination.is_relative_to(root)
        or destination.is_relative_to(root / "artifacts"),
        "outputs inside the checkout must be under artifacts/",
    )
    destination.mkdir(parents=True, exist_ok=False)
    args.output_dir = destination
    raw = (HERE / "cases.json").read_bytes()
    catalog = json.loads(raw)
    validate_catalog(catalog)
    protocol, cases = catalog["protocol"], catalog["cases"]
    report = {
        "status": "PROPOSED_FEASIBILITY",
        "native_fenix": "NOT_RUN_UNSUPPORTED_PROFILE",
        "catalog_sha256": hashlib.sha256(raw).hexdigest(),
        "evaluator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "protocol": protocol,
        "cases": cases,
        "controls": controls(cases),
        "lock_sha256": hashlib.sha256((HERE / "uv.lock").read_bytes()).hexdigest(),
        "method_comparisons": [],
        "runs": [],
        "failures": [],
    }
    studies = {}
    for case in cases:
        for method in protocol["methods"]:
            for refined in (False, True):
                print(
                    f"Running {case['id']} {method} {'refined' if refined else 'baseline'}",
                    flush=True,
                )
                try:
                    times, values, work = simulate(case, protocol, method, refined)
                    metrics = oscillation_metrics(case, protocol, times, values)
                    studies[(case["id"], method, refined)] = (times, values)
                    report["runs"].append(
                        {
                            "case": case["id"],
                            "method": method,
                            "refined": refined,
                            "work": work,
                            "metrics": metrics,
                        }
                    )
                    np.savetxt(
                        args.output_dir
                        / f"{case['id']}-{method}-{'refined' if refined else 'baseline'}.csv.gz",
                        np.column_stack((times, values)),
                        delimiter=",",
                        header=",".join(["time_s", *labels(case)]),
                    )
                    if not metrics["sustained_candidate"]:
                        report["failures"].append(
                            f"no sustained-candidate evidence: {case['id']} {method} refined={refined}"
                        )
                except (ValueError, FloatingPointError) as error:
                    report["failures"].append(
                        f"{case['id']} {method} refined={refined}: {error}"
                    )
    metrics_by_run = {
        (r["case"], r["method"], r["refined"]): r["metrics"] for r in report["runs"]
    }
    for case in cases:
        reference_key = (case["id"], "Radau", True)
        if reference_key not in studies:
            continue
        reference_values = studies[reference_key][1]
        reference_metrics = metrics_by_run[reference_key]["extended_window"]
        for key, (_, values) in studies.items():
            if key[0] != case["id"]:
                continue
            absolute = np.max(np.abs(values - reference_values), axis=0)
            scaled = absolute / np.maximum(
                1.0, np.max(np.abs(reference_values), axis=0)
            )
            comparison = {
                "case": case["id"],
                "method": key[1],
                "refined": key[2],
                "reference": "Radau refined (same backend, not a golden oracle)",
                "max_absolute_sample_error_per_state": absolute.tolist(),
                "max_amplitude_scaled_sample_error_per_state": scaled.tolist(),
                "passed": True,
                "protein_metric_drifts": [],
            }
            actual_metrics = metrics_by_run[key]["extended_window"]
            for i in range(3):
                a, b = actual_metrics["proteins"][i], reference_metrics["proteins"][i]
                if not (
                    a["oscillatory_window"]
                    and b["oscillatory_window"]
                    and actual_metrics["phase_cycles"] is not None
                    and reference_metrics["phase_cycles"] is not None
                ):
                    comparison["passed"] = False
                    continue
                pd = abs(a["period_s"] / b["period_s"] - 1)
                ad = abs(
                    a["prominence_molecules_per_cell"]
                    / b["prominence_molecules_per_cell"]
                    - 1
                )
                phase = abs(
                    (
                        actual_metrics["phase_cycles"][i]
                        - reference_metrics["phase_cycles"][i]
                        + 0.5
                    )
                    % 1
                    - 0.5
                )
                comparison["protein_metric_drifts"].append(
                    {
                        "period_fraction": pd,
                        "amplitude_fraction": ad,
                        "phase_cycles": phase,
                    }
                )
                comparison["passed"] = (
                    comparison["passed"]
                    and pd <= protocol["max_method_period_drift"]
                    and ad <= protocol["max_method_amplitude_drift"]
                    and phase <= protocol["max_method_phase_drift_cycles"]
                )
            comparison["passed"] = bool(comparison["passed"])
            report["method_comparisons"].append(comparison)
            if not comparison["passed"]:
                report["failures"].append(f"method/refinement metrics differ: {key}")
    for control in controls(cases):
        print(f"Running {control['id']} Radau refined", flush=True)
        try:
            times, values, work = simulate(control, protocol, "Radau", True)
            metrics = oscillation_metrics(control, protocol, times, values)
            report["runs"].append(
                {
                    "case": control["id"],
                    "method": "Radau",
                    "refined": True,
                    "work": work,
                    "metrics": metrics,
                }
            )
            if metrics["sustained_candidate"]:
                report["failures"].append(
                    "control unexpectedly oscillatory: " + control["id"]
                )
        except (ValueError, FloatingPointError) as error:
            report["failures"].append(control["id"] + ": " + str(error))
    if all((case["id"], "Radau", True) in studies for case in cases):
        plot_candidates(args.output_dir, studies, cases, protocol)
    report["feasibility_checks"] = "FAIL" if report["failures"] else "PASS"
    (args.output_dir / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    print(
        json.dumps(
            {
                "feasibility_checks": report["feasibility_checks"],
                "failures": report["failures"],
            }
        ),
        flush=True,
    )
    return bool(report["failures"])


if __name__ == "__main__":
    raise SystemExit(main())
