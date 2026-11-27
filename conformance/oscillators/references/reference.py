"""Independent Decimal closed-form P09 candidates; no FENIX, NumPy or SciPy."""

from __future__ import annotations

import argparse
import hashlib
import json
from decimal import Decimal as D
from decimal import localcontext
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATALOG_SHA256 = "071615af6915854cb9ebb53990d44eafad967b88221bccfca285dcdc610d2355"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def catalog(path=HERE / "cases.json"):
    raw = Path(path).read_bytes()
    # Validate the complete frozen document before trusting a report fingerprint.
    # This intentionally pins bytes, including formatting, for candidate review.
    require(hashlib.sha256(raw).hexdigest() == CATALOG_SHA256, "catalog bytes differ")
    return json.loads(raw, parse_float=D)


def state(case_id, time):
    """Closed forms derived from P09, independently of the feasibility evaluator."""
    time = D(time)
    if "-driven-n" in case_id:
        n = int(case_id.rsplit("n", 1)[1])
        rate = D(n) / 2
        z = (-rate * time).exp()
        amplitude = D(2) ** n
        log_ratio = (((rate * time).exp() + amplitude) / (1 + amplitude)).ln()
        transcript = (
            2 * z + (1 - z) / rate + 4 / rate * (1 - z - amplitude * z * log_ratio)
        )
        output = [D(0)] * (18 if case_id.startswith("community") else 6)
        output[0] = transcript
        output[8 if case_id.startswith("community") else 5] = 8 * (-time / 2).exp()
        if case_id.startswith("community"):
            output[17] = D(999)
        return output
    if case_id == "single-translation-cascade":
        transcripts = [D(i + 2) * (-D(i + 1) * time).exp() for i in range(3)]
        proteins = [
            D(i + 5) * (-D(i + 2) * time).exp()
            + D((i + 3) * (i + 2))
            * ((-D(i + 1) * time).exp() - (-D(i + 2) * time).exp())
            for i in range(3)
        ]
        return transcripts + proteins
    if case_id == "community-threshold-equilibrium":
        return [D(1)] * 6 + [D(v) for v in (2, 3, 5) for _ in range(3)] + [D(12)] * 3
    if case_id == "community-closed-transport":
        z = (-D(17) * time / 3).exp()
        densities, external = [], []
        for k in range(3):
            equilibrium = D(56 * (k + 2) + 12 * (k + 6)) / 68
            densities.append(equilibrium + (k + 2 - equilibrium) * z)
            external.append(12 * (equilibrium + (k + 6 - equilibrium) * z))
        return [D(0)] * 6 + [v * q for v in (2, 3, 5) for q in densities] + external
    raise ValueError("unknown closed-form case")


def rhs(case, values):
    """Literal component equations used solely to check the analytical laws."""
    p = case["parameters"]
    community = case["model"] == "three_strain_mrna_protein_exchange"
    volumes = case.get("cell_volumes_L", [case.get("cell_volume_L")] * 3)
    output = [D(0)] * len(values)
    for gate in range(3):
        previous = (gate + 2) % 3
        sensor = values[6 + 3 * gate + previous] if community else values[3 + previous]
        density = sensor / D(volumes[gate])
        gain = 1 / (
            1 + (density / D(p["threshold_density"][gate])) ** p["hill_n"][gate]
        )
        output[gate] = (
            D(p["basal"][gate])
            + D(p["induced"][gate]) * gain
            - D(p["mrna_decay"][gate]) * values[gate]
        )
        output[3 + gate] = (
            D(p["translation"][gate]) * values[gate]
            - D(p["protein_decay"][gate]) * values[3 + gate]
        )
    if community:
        for signal in range(3):
            medium = values[15 + signal]
            output[15 + signal] = -D(p["medium_signal_decay"][signal]) * medium
            for strain in range(3):
                index = 6 + 3 * strain + signal
                outward = D(p["export"][strain][signal]) * values[index]
                inward = (
                    D(p["import"][strain][signal])
                    * D(volumes[strain])
                    * medium
                    / D(case["medium_volume_L"])
                )
                production = (
                    D(p["signal_synthesis"][signal]) * values[3 + signal]
                    if strain == signal
                    else D(0)
                )
                output[index] = (
                    production
                    - D(p["intracellular_signal_decay"][strain][signal]) * values[index]
                    - outward
                    + inward
                )
                output[15 + signal] += D(case["populations"][strain]) * (
                    outward - inward
                )
    return output


def residual(case, time, precision=160):
    """High-precision central derivative of closed form versus independent RHS."""
    with localcontext() as ctx:
        ctx.prec = precision
        h = D("1e-35")
        plus, minus = state(case["id"], D(time) + h), state(case["id"], D(time) - h)
        actual = rhs(case, state(case["id"], time))
        return max(
            abs((a - b) / (2 * h) - r) / max(D(1), abs(r))
            for a, b, r in zip(plus, minus, actual, strict=True)
        )


def report(path=HERE / "cases.json"):
    data = catalog(path)
    samples, max_precision, max_residual = [], D(0), D(0)
    for case in data["cases"]:
        for time in case["times"]:
            with localcontext() as ctx:
                ctx.prec = 80
                low = state(case["id"], time)
            with localcontext() as ctx:
                ctx.prec = 160
                high = state(case["id"], time)
                require(
                    all(y.is_finite() and y >= 0 for y in high),
                    "invalid closed-form state",
                )
                if time == 0:
                    require(
                        high == case["initial_counts"], "initial definition mismatch"
                    )
                error = max(
                    abs(x - y) / max(D(1), abs(y))
                    for x, y in zip(low, high, strict=True)
                )
                ode_error = residual(case, time)
                require(error <= D("1e-70"), "precision refinement failed")
                require(
                    ode_error <= D("1e-65"), "closed form does not satisfy equations"
                )
                max_precision = max(max_precision, error)
                max_residual = max(max_residual, ode_error)
                samples.append(
                    {"case": case["id"], "time": time, "state": list(map(str, high))}
                )
    return {
        "status": "PROPOSED_ANALYTICAL",
        "catalog_sha256": CATALOG_SHA256,
        "samples": samples,
        "max_precision_error": str(max_precision),
        "max_ode_residual": str(max_residual),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=HERE / "cases.json")
    args = parser.parse_args()
    print(json.dumps(report(args.catalog), indent=2))


if __name__ == "__main__":
    main()
