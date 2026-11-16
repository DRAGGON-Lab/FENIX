"""Read-only exploratory SciPy evidence for PROPOSED P04; no FENIX imports.

Run with the isolated dependencies documented in the verification record.
Writes JSON to stdout only; never generates approved expectations.
"""

from __future__ import annotations

import hashlib
import json
import platform
import struct
import sys
from decimal import Decimal, localcontext
from pathlib import Path

import numpy as np
import scipy
from scipy.integrate import solve_ivp

ROOT = Path(__file__).resolve().parents[3]
A, R = Decimal("1e-9"), Decimal("1e-8")


class WorkLimit(RuntimeError):
    pass


def decode(bits):
    return struct.unpack(">d", bytes.fromhex(bits))[0]


def integrate(method, parameters, times, settings, budget=100000):
    calls = 0
    alpha, beta, x0 = (parameters[k] for k in ("alpha", "beta", "x0"))

    def rhs(t, y):
        nonlocal calls
        if calls >= budget:
            raise WorkLimit(f"RHS budget {budget} exhausted")
        calls += 1
        return np.array([alpha - beta * y[0]], dtype=np.float64)

    with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
        result = solve_ivp(
            rhs,
            (0.0, times[-1]),
            [x0],
            method=method,
            t_eval=times,
            vectorized=False,
            dense_output=False,
            first_step=None,
            rtol=settings[0],
            atol=settings[1],
            max_step=settings[2],
            **({"jac": np.array([[-beta]])} if method == "Radau" else {}),
        )
    assert result.success, result.message
    assert np.array_equal(result.t, times)
    assert result.y.shape == (1, len(times))
    assert np.isfinite(result.y).all() and (result.y >= 0).all()
    assert result.nfev == calls
    return result.y[0], calls


def compare(actual, expected):
    error = abs(Decimal.from_float(float(actual)) - expected)
    return error, error / (A + R * abs(expected))


def main():
    path = ROOT / "conformance/production_decay/catalog.json"
    raw = path.read_bytes()
    catalog = json.loads(raw)
    assert catalog["status"] == "APPROVED"
    configurations = {
        "coarse": (1e-9, 1e-11, 2.0),
        "nominal": (1e-10, 1e-12, 1.0),
        "fine": (1e-11, 1e-13, 0.5),
    }
    rows = []
    summaries = []
    with localcontext() as context:
        context.prec = 100
        for method in ("DOP853", "Radau"):
            for configuration, settings in configurations.items():
                group = []
                total_calls = 0
                for case in catalog["cases"]:
                    parameters = {k: decode(v) for k, v in case["parameters"].items()}
                    samples = sorted(
                        case["samples"], key=lambda s: decode(s["time_bits"])
                    )
                    times = tuple(decode(s["time_bits"]) for s in samples)
                    values, calls = integrate(method, parameters, times, settings)
                    total_calls += calls
                    for sample, value in zip(samples, values, strict=True):
                        error, fraction = compare(value, Decimal(sample["expected"]))
                        row = {
                            "method": method,
                            "configuration": configuration,
                            "case": case["id"],
                            "time_bits": sample["time_bits"],
                            "actual_bits": struct.pack(">d", float(value)).hex(),
                            "absolute_error": str(error),
                            "bound_fraction": str(fraction),
                            "passed": fraction <= 1,
                        }
                        group.append(row)
                        rows.append(row)
                assert len(group) == 40
                # Coarse results are observations; nominal/fine are acceptance checks.
                if configuration != "coarse":
                    assert all(row["passed"] for row in group), (method, configuration)
                summaries.append(
                    {
                        "method": method,
                        "configuration": configuration,
                        "samples": len(group),
                        "nfev": total_calls,
                        "max_absolute_error": str(
                            max(Decimal(r["absolute_error"]) for r in group)
                        ),
                        "max_bound_fraction": str(
                            max(Decimal(r["bound_fraction"]) for r in group)
                        ),
                        "passed": all(row["passed"] for row in group),
                    }
                )
        parameters = {"alpha": 2000000.0, "beta": 1000000.0, "x0": 5.0}
        times = (0.0, 1e-6, 1e-4, 1.0)
        values, calls = integrate("Radau", parameters, times, configurations["nominal"])
        stiff = []
        for time, value in zip(times, values, strict=True):
            reference = (
                Decimal(2)
                + Decimal(3) * (-Decimal(1000000) * Decimal.from_float(time)).exp()
            )
            error, fraction = compare(value, reference)
            assert fraction <= 1
            stiff.append(
                {
                    "time_bits": struct.pack(">d", time).hex(),
                    "absolute_error": str(error),
                    "bound_fraction": str(fraction),
                }
            )
        try:
            integrate(
                "DOP853", parameters, times, configurations["nominal"], budget=2000
            )
        except WorkLimit as error:
            limit_result = str(error)
        else:
            raise AssertionError("expected stiff DOP853 trial to exhaust budget")
    report = {
        "status": "PROPOSED_NOT_RATIFIED",
        "scope": "isolated SciPy trials; no FENIX executor",
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "catalog_sha256": hashlib.sha256(raw).hexdigest(),
        "thresholds": {"absolute": str(A), "relative": str(R)},
        "configurations": configurations,
        "summaries": summaries,
        "samples": rows,
        "stiff_radau": {"nfev": calls, "samples": stiff},
        "stiff_dop853": limit_result,
        "not_run": [
            "Native FENIX execution and error diagnostics",
            "Julia ODE execution",
            "Cross-language ODE gate #29",
            "Human PI ratification",
            "Clean-wheel executor tests",
        ],
    }
    json.dump(report, sys.stdout, indent=2, allow_nan=False)
    print()


if __name__ == "__main__":
    main()
