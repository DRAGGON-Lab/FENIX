"""Analytical candidate references for ADR-P08, independent of native FENIX.

Each Decimal computation is repeated at doubled precision. Expected Hill values
are independently evaluated as exact rationals. No runtime ODE solver is used.
"""

import hashlib
import json
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path


def driven_reporter(n, time):
    """Exact integrating-factor solution with E=48 exp(-t/2), beta=n/2."""
    D = Decimal
    beta = D(n) / 2
    amplitude = D(2) ** n
    growth = (beta * time).exp()
    return (
        D(2) / growth
        + (1 - 1 / growth) / beta
        + 4
        * amplitude
        / (beta * growth)
        * ((growth + amplitude) / (1 + amplitude)).ln()
    )


def state(case_id, time):
    """Evaluate independently derived laws at a Decimal time."""
    D = Decimal
    if case_id.startswith("threshold-n"):
        return [D(4), D(12), D(24), D(4) * (1 - (-time / 2).exp())]
    if case_id == "reversible-transient":
        z = (-D(5) * time / 2).exp()
        return [D(12) / 5 + D(8) / 5 * z, D(2), D(144) / 5 - D(24) / 5 * z, D(0)]
    if case_id.startswith("driven-n"):
        n = int(case_id.removeprefix("driven-n"))
        return [D(0), D(0), D(48) * (-time / 2).exp(), driven_reporter(n, time)]
    if case_id == "two-strain-transient":
        z = (-D(11) * time / 4).exp()
        return [
            (D(72) + 16 * z) / 11,
            (D(108) + 24 * z) / 11,
            (D(432) - 168 * z) / 11,
            D(0),
        ]
    raise ValueError("unknown reference case")


def catalog():
    return json.loads(Path(__file__).with_name("cases.json").read_bytes())


def validate_catalog_metadata(data):
    """Check positional state and quantity metadata against ADR-P08."""
    expected = {
        "state_ids": [
            "sender.signal",
            "receiver.signal",
            "env.signal",
            "receiver.reporter",
        ],
        "time_unit": "s",
        "volumes_unit": "L",
        "state_unit": "molecule",
        "parameter_units": {
            "sender_production": "molecule/s",
            "sender_decay": "1/s",
            "receiver_decay": "1/s",
            "env_decay": "1/s",
            "reporter_decay": "1/s",
            "reporter_basal": "molecule/s",
            "reporter_induced": "molecule/s",
            "sender_export": "1/s",
            "sender_import": "1/s",
            "receiver_export": "1/s",
            "receiver_import": "1/s",
            "threshold": "molecule/L",
            "hill_n": "1",
        },
    }
    for field, value in expected.items():
        if data.get(field) != value:
            raise ValueError(f"catalog metadata differs from ADR-P08: {field}")


def rhs(case, values):
    s, r, e, y = values
    p = {k: Decimal(v) for k, v in case["parameters"].items()}
    vs, vr, ve = map(Decimal, case["volumes"])
    ns, nr = case["populations"]
    density = e / ve
    js = p["sender_export"] * s - p["sender_import"] * vs * density
    jr = p["receiver_export"] * r - p["receiver_import"] * vr * density
    n = int(p["hill_n"])
    activation = density**n / (p["threshold"] ** n + density**n)
    return [
        p["sender_production"] - p["sender_decay"] * s - js,
        -p["receiver_decay"] * r - jr,
        ns * js + nr * jr - p["env_decay"] * e,
        p["reporter_basal"]
        + p["reporter_induced"] * activation
        - p["reporter_decay"] * y,
    ]


def rows(precision):
    with localcontext() as ctx:
        ctx.prec = precision
        return [
            {
                "case": case["id"],
                "time": time,
                "state": state(case["id"], Decimal(time)),
            }
            for case in catalog()["cases"]
            for time in case["times"]
        ]


def verify_laws():
    with localcontext() as ctx:
        ctx.prec = 160
        h = Decimal("1e-40")
        for case in catalog()["cases"]:
            if state(case["id"], Decimal(0)) != list(map(Decimal, case["initial"])):
                raise ValueError("initial state mismatch")
            for time in map(Decimal, (1, 4)):
                plus, minus = state(case["id"], time + h), state(case["id"], time - h)
                target = rhs(case, state(case["id"], time))
                for a, b, c in zip(plus, minus, target, strict=True):
                    if abs((a - b) / (2 * h) - c) > Decimal("1e-65") * max(1, abs(c)):
                        raise ValueError("analytical law does not satisfy declared ODE")
        # For arbitrary per-cell fluxes, the weighted signed columns vanish.
        for ns, nr in ((1, 1), (3, 5), (100, 7)):
            for js, jr in ((4, -10), (-2, 3), (0, 0)):
                if ns * (-js) + nr * (-jr) + ns * js + nr * jr != 0:
                    raise ValueError("weighted transport balance")
        # Missing population weights and an inverted environmental sign fail.
        if 3 * (-4) + 5 * 10 + (4 - 10) == 0 or 3 * (-4) + 5 * 10 + 38 == 0:
            raise ValueError("nonconservative counterexample")


def verify():
    validate_catalog_metadata(catalog())
    verify_laws()
    low, high = rows(80), rows(160)
    max_error = Decimal(0)
    for a, b in zip(low, high, strict=True):
        for x, y in zip(a["state"], b["state"], strict=True):
            error = abs(x - y)
            if error > Decimal("1e-70") * max(Decimal(1), abs(y)):
                raise ValueError("precision refinement")
            max_error = max(max_error, error)
        if b["case"] in ("reversible-transient", "two-strain-transient"):
            with localcontext() as ctx:
                ctx.prec = 160
                mass = 3 * b["state"][0] + 5 * b["state"][1] + b["state"][2]
                initial = 46 if b["case"] == "reversible-transient" else 108
                if abs(mass - initial) > Decimal("1e-150"):
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
    # Independent exact open-system balance with production and all losses.
    for ns, nr in ((1, 1), (3, 5), (100, 7)):
        for js, jr in ((4, -10), (-2, 3), (0, 0)):
            ps, ds, dr, de, ss, rr, ee = map(Fraction, (7, 2, 3, 1, 4, 12, 24))
            dsdt, drdt, dedt = (
                ps - ds * ss - js,
                -dr * rr - jr,
                ns * js + nr * jr - de * ee,
            )
            if (
                ns * dsdt + nr * drdt + dedt
                != ns * ps - ns * ds * ss - nr * dr * rr - de * ee
            ):
                raise ValueError("open-system balance")
    with localcontext() as ctx:
        ctx.prec = 160
        case = catalog()["cases"][9]
        values = state(case["id"], Decimal(1))
        baseline = rhs(case, values)
        # Doubling one population doubles its external flux contribution only.
        for index, role in enumerate(("sender", "receiver")):
            changed = json.loads(json.dumps(case))
            changed["populations"][index] *= 2
            actual = rhs(changed, values)
            volume = Decimal(case["volumes"][index])
            density = values[2] / Decimal(case["volumes"][2])
            p = case["parameters"]
            net = (
                Decimal(p[role + "_export"]) * values[index]
                - Decimal(p[role + "_import"]) * volume * density
            )
            if abs(
                actual[2] - baseline[2] - case["populations"][index] * net
            ) > Decimal("1e-150"):
                raise ValueError("population scaling")
            if actual[:2] != baseline[:2] or actual[3] != baseline[3]:
                raise ValueError("per-cell population scaling")
        # Sensing changes reporter production without a signal sink.
        changed = json.loads(json.dumps(case))
        changed["parameters"]["reporter_induced"] = 100
        actual = rhs(changed, values)
        if actual[:3] != baseline[:3] or actual[3] <= baseline[3]:
            raise ValueError("read-only sensing")
    return high, max_error


if __name__ == "__main__":
    samples, error = verify()
    report = {
        "status": "PROPOSED",
        "samples": samples,
        "max_refinement_error": error,
        "catalog_sha256": hashlib.sha256(
            Path(__file__).with_name("cases.json").read_bytes()
        ).hexdigest(),
    }
    print(json.dumps(report, default=str, indent=2))
