"""Analytical candidate references for ADR-P08, independent of native FENIX.

Each Decimal computation is repeated at doubled precision. Expected Hill values
are independently evaluated as exact rationals. No runtime ODE solver is used.
"""

import json
from decimal import Decimal, localcontext
from fractions import Fraction


def rows(precision):
    with localcontext() as ctx:
        ctx.prec = precision
        D = Decimal
        output = []
        # At density K, H=1/2 for every admitted exponent. Choose exchange
        # rates so both strains have zero net flux at unequal cell volumes.
        # Counts s=4, r=12, E=24; volumes 2,3,12. Export/import rate pairs
        # (1,1) and (1,2) give intracellular equilibrium densities 2 and 4.
        for n in range(1, 5):
            for time in (0, 1, 4):
                y = D(4) * (1 - (-D(time) / 2).exp())
                output.append(
                    {
                        "case": f"threshold-n{n}",
                        "time": time,
                        "state": [D(4), D(12), D(24), y],
                    }
                )
        # Isolate sender/environment reversible exchange. N_s=3, v_s=2,
        # V_e=12, k_out=2, k_in=1. N_r=5 and r=2 remain fixed.
        # s+E/3=12; the exchange eigenvalue is -(2+3*2/12)=-5/2.
        for time in (0, 1, 4):
            decay = (-D(5) * time / 2).exp()
            s = D(12) / 5 + D(8) / 5 * decay
            e = D(144) / 5 - D(24) / 5 * decay
            output.append(
                {
                    "case": "reversible-transient",
                    "time": time,
                    "state": [s, D(2), e, D(0)],
                }
            )
        return output


def verify():
    low, high = rows(80), rows(160)
    max_error = Decimal(0)
    for a, b in zip(low, high, strict=True):
        for x, y in zip(a["state"], b["state"], strict=True):
            error = abs(x - y)
            if error > Decimal("1e-70") * max(Decimal(1), abs(y)):
                raise ValueError("precision refinement")
            max_error = max(max_error, error)
        if b["case"] == "reversible-transient":
            with localcontext() as ctx:
                ctx.prec = 160
                mass = 3 * b["state"][0] + 5 * b["state"][1] + b["state"][2]
                if abs(mass - 46) > Decimal("1e-150"):
                    raise ValueError("weighted balance")
    # Exact Hill limits and concentration scaling, including unequal volumes.
    for n in range(1, 5):
        for count, volume, k in ((0, 12, 2), (24, 12, 2), (48, 12, 2), (24, 24, 2)):
            c = Fraction(count, volume)
            expected = c**n / (Fraction(k) ** n + c**n)
            if count == 0 and expected != 0:
                raise ValueError("zero sensing")
            if count == 24 and volume == 12 and expected != Fraction(1, 2):
                raise ValueError("threshold sensing")
            if count == 48 and expected <= Fraction(1, 2):
                raise ValueError("above threshold sensing")
            if volume == 24 and expected >= Fraction(1, 2):
                raise ValueError("volume scaling")
    return high, max_error


if __name__ == "__main__":
    samples, error = verify()
    report = {"status": "PROPOSED", "samples": samples, "max_refinement_error": error}
    print(json.dumps(report, default=str, indent=2))
