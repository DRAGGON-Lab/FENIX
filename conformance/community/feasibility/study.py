"""Proposed P08 numerical-stage investigation; imports no native FENIX code.

SciPy results are compared with the existing Decimal analytical laws, never used
to generate golden values. These local controls do not approve native methods.
"""

import argparse
import hashlib
import json
import math
import platform
import sys
from decimal import Decimal, localcontext
from pathlib import Path

import numpy as np
import scipy
from scipy.integrate import solve_ivp

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import reference


class ProbeFailure(ValueError):
    def __init__(self, category, time, values):
        super().__init__(category)
        self.category = category
        self.time = float(time)
        self.values = [float(value) for value in values]


def settings():
    return json.loads((HERE / "settings.json").read_bytes())


class Kernel:
    """Direct count-balance equations and Jacobian, independent of FIR ASTs."""

    def __init__(self, case, budget):
        self.p = case["parameters"]
        self.ns, self.nr = case["populations"]
        self.vs, self.vr, self.ve = case["volumes"]
        self.budget = budget
        self.calls = 0
        self.jac_calls = 0
        self.minimum_environment_stage = None

    def domain(self, time, values):
        if len(values) != 4 or not all(math.isfinite(float(v)) for v in values):
            raise ProbeFailure("NONFINITE_STAGE", time, values)
        e = float(values[2])
        self.minimum_environment_stage = (
            e
            if self.minimum_environment_stage is None
            else min(e, self.minimum_environment_stage)
        )
        if e < 0:
            raise ProbeFailure("STAGE_DOMAIN", time, values)

    def hill(self, e):
        if e == 0:
            return 0.0
        c, k, n = e / self.ve, self.p["threshold"], self.p["hill_n"]
        if c <= k:
            power = (c / k) ** n
            return power / (1 + power)
        return 1 / (1 + (k / c) ** n)

    def rhs(self, time, values):
        if self.calls >= self.budget:
            raise ProbeFailure("WORK_LIMIT", time, values)
        self.calls += 1
        self.domain(time, values)
        s, r, e, y = values
        p = self.p
        js = p["sender_export"] * s - p["sender_import"] * self.vs * e / self.ve
        jr = p["receiver_export"] * r - p["receiver_import"] * self.vr * e / self.ve
        result = np.array(
            [
                p["sender_production"] - p["sender_decay"] * s - js,
                -p["receiver_decay"] * r - jr,
                self.ns * js + self.nr * jr - p["env_decay"] * e,
                p["reporter_basal"]
                + p["reporter_induced"] * self.hill(e)
                - p["reporter_decay"] * y,
            ]
        )
        if not np.isfinite(result).all():
            raise ProbeFailure("NONFINITE_RHS", time, result)
        return result

    def jacobian(self, time, values):
        self.jac_calls += 1
        self.domain(time, values)
        p, e = self.p, values[2]
        ai = p["sender_import"] * self.vs / self.ve
        bi = p["receiver_import"] * self.vr / self.ve
        ao, bo = p["sender_export"], p["receiver_export"]
        if e == 0:
            derivative = 1 / (p["threshold"] * self.ve) if p["hill_n"] == 1 else 0
        else:
            h = self.hill(e)
            derivative = p["hill_n"] * h * (1 - h) / e
        matrix = np.array(
            [
                [-p["sender_decay"] - ao, 0, ai, 0],
                [0, -p["receiver_decay"] - bo, bi, 0],
                [
                    self.ns * ao,
                    self.nr * bo,
                    -self.ns * ai - self.nr * bi - p["env_decay"],
                    0,
                ],
                [0, 0, p["reporter_induced"] * derivative, -p["reporter_decay"]],
            ],
            dtype=float,
        )
        if not np.isfinite(matrix).all():
            raise ProbeFailure("NONFINITE_JACOBIAN", time, matrix.ravel())
        return matrix


def integrate(case, method, controls, max_step, budget, backend=solve_ivp):
    """One attempt only. Preserve the first failure; never clip or substitute."""
    kernel = Kernel(case, budget)
    row = {
        "case": case["id"],
        "method": method,
        "setting": controls["id"],
        "times": case["times"],
        "max_step": max_step,
    }
    try:
        options = {"jac": kernel.jacobian} if method == "Radau" else {}
        solution = backend(
            kernel.rhs,
            (0.0, float(case["times"][-1])),
            np.array(case["initial"], dtype=float),
            method=method,
            t_eval=case["times"],
            rtol=controls["rtol"],
            atol=controls["atol"],
            max_step=max_step,
            **options,
        )
        if not solution.success:
            raise ProbeFailure(
                "INTEGRATION_FAILURE", solution.t[-1] if len(solution.t) else 0, []
            )
        if not np.array_equal(solution.t, case["times"]) or solution.y.shape != (
            4,
            len(case["times"]),
        ):
            raise ProbeFailure("INCOMPLETE_OUTPUT", 0, [])
        if not np.isfinite(solution.y).all():
            raise ProbeFailure("NONFINITE_OUTPUT", 0, [])
        if np.any(solution.y < 0):
            raise ProbeFailure("NEGATIVE_OUTPUT", 0, [])
        row.update(
            outcome="SUCCESS",
            states=solution.y.T.tolist(),
            backend_nfev=int(solution.nfev),
            njev=int(solution.njev),
            nlu=int(solution.nlu),
        )
    except ProbeFailure as failure:
        row.update(
            outcome=failure.category,
            failure_time=failure.time,
            failure_values=[v if math.isfinite(v) else str(v) for v in failure.values],
        )
    row.update(
        rhs_calls=kernel.calls,
        jacobian_calls=kernel.jac_calls,
        minimum_environment_stage=kernel.minimum_environment_stage,
    )
    return row


def weighted_initial_error(weights, represented, expected):
    return abs(
        sum(w * (a - b) for w, a, b in zip(weights, represented, expected, strict=True))
    )


def comparisons(case, numerical, bounds):
    """Evaluate signed errors with Decimal, including exact float conversion.

    For closed transport, |M_num(t)-M_num(0)| is bounded by the sum
    w_i*b_i(t) plus |M_num(0)-M_ref(0)|. The latter includes initial
    representation error. The reporter has zero signal-mass weight.
    """
    if numerical["outcome"] != "SUCCESS":
        return []
    records = []
    with localcontext() as ctx:
        ctx.prec = 160
        weights = [
            Decimal(case["populations"][0]),
            Decimal(case["populations"][1]),
            Decimal(1),
            Decimal(0),
        ]
        initial = reference.state(case["id"], Decimal(0))
        represented_initial = [Decimal.from_float(float(v)) for v in case["initial"]]
        initial_error = weighted_initial_error(weights, represented_initial, initial)
        p = case["parameters"]
        closed = all(
            p[k] == 0
            for k in (
                "sender_production",
                "sender_decay",
                "receiver_decay",
                "env_decay",
            )
        )
        for time, values in zip(case["times"], numerical["states"], strict=True):
            expected = reference.state(case["id"], Decimal(time))
            represented = list(map(Decimal.from_float, values))
            limits = [
                Decimal(bounds["absolute"]) + Decimal(bounds["relative"]) * abs(v)
                for v in expected
            ]
            ratios = [
                abs(a - b) / limit
                for a, b, limit in zip(represented, expected, limits, strict=True)
            ]
            record = {
                "time": time,
                "reference": list(map(str, expected)),
                "state_error_ratios": list(map(str, ratios)),
                "within_state_bound": all(r <= 1 for r in ratios),
            }
            if closed:
                drift = abs(
                    sum(
                        w * (a - b)
                        for w, a, b in zip(
                            weights, represented, represented_initial, strict=True
                        )
                    )
                )
                limit = (
                    sum(w * b for w, b in zip(weights, limits, strict=True))
                    + initial_error
                )
                record.update(
                    closed_signal_drift=str(drift),
                    balance_bound=str(limit),
                    initial_representation_error=str(initial_error),
                    within_balance_bound=drift <= limit,
                )
            records.append(record)
    return records


def run(base_revision):
    config = settings()
    data = reference.catalog()
    reference.validate_catalog(data)
    reference.verify_laws()
    runs = []
    for case in data["cases"]:
        for method in config["methods"]:
            for controls in config["settings"]:
                row = integrate(
                    case,
                    method,
                    controls,
                    config["reference_max_step"],
                    config["max_rhs_calls"],
                )
                row["comparisons"] = comparisons(case, row, config["state_bound"])
                runs.append(row)
    tail = next(
        c.copy() for c in data["cases"] if c["id"] == config["tail_control"]["case"]
    )
    tail["times"] = config["tail_control"]["times"]
    tails = [
        integrate(
            tail,
            method,
            controls,
            config["tail_control"]["max_step"],
            config["max_rhs_calls"],
        )
        for method in config["methods"]
        for controls in config["settings"]
    ]
    for row in tails:
        with localcontext() as ctx:
            ctx.prec = 160
            # This exact positive law holds at every finite real time.
            time = Decimal.from_float(row.get("failure_time", 1000.0))
            row["analytical_environment_at_stop"] = str(Decimal(48) * (-time / 2).exp())
    passed = all(
        row["outcome"] == "SUCCESS"
        and all(
            sample["within_state_bound"] and sample.get("within_balance_bound", True)
            for sample in row["comparisons"]
        )
        for row in runs
    )
    files = [
        HERE / "settings.json",
        HERE / "study.py",
        HERE.parent / "cases.json",
        HERE.parent / "reference.py",
        HERE.parent / "reference.jl",
        HERE.parents[2] / "packages/python/uv.lock",
    ]
    root = HERE.parents[2]
    return {
        "status": "PROPOSED",
        "base_revision": base_revision,
        "study_version": config["study_version"],
        "settings": config,
        "files_sha256": {
            str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in files
        },
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "platform": platform.platform(),
        },
        "reference_state_ids": data["state_ids"],
        "runs": runs,
        "tail_controls": tails,
        "bounded_reference_matrix": "PASS" if passed else "FAIL",
        "tail_controls_match_prediction": "PASS"
        if all(
            row["outcome"] == config["tail_control"]["expected_outcome"]
            for row in tails
        )
        else "FAIL",
        "julia_stage_feasibility": "NOT RUN",
        "native_implementation": "NOT RUN",
        "pi_executable_profile_acceptance": "PENDING",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-revision",
        required=True,
        help="Reviewed main base; exact candidate files are fingerprinted separately",
    )
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.base_revision)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print("Bounded analytical matrix:", report["bounded_reference_matrix"])
    print(
        "Tail domain controls:",
        ", ".join(row["outcome"] for row in report["tail_controls"]),
    )
    print("PI executable-profile acceptance: PENDING; Julia/native execution: NOT RUN")
    if (
        report["bounded_reference_matrix"] != "PASS"
        or report["tail_controls_match_prediction"] != "PASS"
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
