"""PROPOSED independent P10 AST-versus-P09 algebra audit; no native execution."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import platform
from decimal import Decimal as D
from decimal import localcontext
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REFERENCE = ROOT / "conformance/oscillators/references/reference.py"
REFERENCE_SHA256 = "497127a82add2992da5cc9c101dc5cec0c9e9447774a4864d67d5b57abb380aa"
PRIMARY_SHA256 = "70932f56c47cddb7fd502b165580c65f8a34431721972fbf11a2588ab5c15d25"
COMPONENT_SHA256 = "071615af6915854cb9ebb53990d44eafad967b88221bccfca285dcdc610d2355"
PROBES_SHA256 = "a4f96bc6a16c04fc17401560bd08c412852ebdd2a14ebf239ac4f7d577520867"
PRECISIONS = (80, 160)
ALGEBRA_LIMIT = D(
    "1e-65"
)  # Proposed algebra audit criterion, never a native ODE bound.


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pinned(path, expected):
    raw = Path(path).read_bytes()
    require(
        hashlib.sha256(raw).hexdigest() == expected,
        "pinned input bytes differ: " + Path(path).name,
    )
    return json.loads(raw)


def oracle():
    # Fixed, byte-pinned local reference code, never a serialized module/callback.
    require(
        sha256(REFERENCE) == REFERENCE_SHA256, "pinned P09 reference source differs"
    )
    spec = importlib.util.spec_from_file_location(
        "p09_component_equation_reference", REFERENCE
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.catalog()  # Its independently reviewed complete input pin also holds.
    return module


def binary64(value):
    require(type(value) in (int, float), "binary64 quantity required")
    result = float(value)
    require(math.isfinite(result), "nonfinite binary64 input")
    return result


def decimal(value):
    # Preserve the represented binary64 value, not its decimal display spelling.
    return D.from_float(binary64(value))


def lifted(value):
    if type(value) in (int, float):
        return decimal(value)
    if isinstance(value, list):
        return [lifted(child) for child in value]
    if isinstance(value, dict):
        return {key: lifted(child) for key, child in value.items()}
    return value


def community(case):
    require(
        case["model"]
        in ("single_cell_mrna_protein", "three_strain_mrna_protein_exchange"),
        "unknown P09 model",
    )
    return case["model"] == "three_strain_mrna_protein_exchange"


def reference_order(case):
    roles = [f"{prefix}{i}" for prefix in ("m", "p") for i in range(1, 4)]
    names = [f"{prefix}{i}" for prefix in ("mRNA", "protein") for i in range(1, 4)]
    if community(case):
        roles += [f"a{j}{k}" for j in range(1, 4) for k in range(1, 4)] + [
            f"e{k}" for k in range(1, 4)
        ]
        names += [f"strain{j}.signal{k}" for j in range(1, 4) for k in range(1, 4)] + [
            f"medium.signal{k}" for k in range(1, 4)
        ]
    if "state_ids" in case:
        require(case["state_ids"] == names, "reference state-ID/order mismatch")
    return roles


def quantities(case):
    """Independently map P09 quantity roles to the proposed P10 names.

    This does not import wire_shapes or either candidate builder. Every role's
    numeric value comes from a pinned P09 definition or the proposed probe file.
    """
    parameters = {}
    for source, target in (
        ("basal", "b"),
        ("induced", "h"),
        ("mrna_decay", "gm"),
        ("protein_decay", "gp"),
        ("translation", "beta"),
        ("threshold_density", "K"),
        ("hill_n", "n"),
    ):
        parameters.update(
            {
                target + str(i): value
                for i, value in enumerate(case["parameters"][source], 1)
            }
        )
    geometry = {"cell": case.get("cell_volume_L")}
    populations = {}
    if community(case):
        geometry = {
            f"strain{i}": value for i, value in enumerate(case["cell_volumes_L"], 1)
        }
        geometry["medium"] = case["medium_volume_L"]
        populations = {
            f"strain{i}": value for i, value in enumerate(case["populations"], 1)
        }
        for source, target in (
            ("signal_synthesis", "sigma"),
            ("medium_signal_decay", "ge"),
        ):
            parameters.update(
                {
                    target + str(i): value
                    for i, value in enumerate(case["parameters"][source], 1)
                }
            )
        for source, target in (
            ("export", "out"),
            ("import", "in"),
            ("intracellular_signal_decay", "ga"),
        ):
            parameters.update(
                {
                    f"{target}{j}{k}": value
                    for j, row in enumerate(case["parameters"][source], 1)
                    for k, value in enumerate(row, 1)
                }
            )
    initial = dict(zip(reference_order(case), case["initial_counts"], strict=True))
    return parameters, geometry, populations, initial


def indexed(rows, key):
    result = {row[key]: row for row in rows}
    require(len(result) == len(rows), "duplicate mathematical role: " + key)
    return result


def check_projection(model, case):
    parameters, geometry, populations, initial = quantities(case)
    rates, states = indexed(model["parameters"], "id"), indexed(model["states"], "id")
    require(
        set(rates) == set(parameters) and set(states) == set(initial),
        "incomplete mathematical role projection",
    )
    require(
        model["template"]
        == (
            "repressilator.three_strain.v1"
            if community(case)
            else "repressilator.single_cell.v1"
        ),
        "wrong scientific template",
    )
    require(model["time_unit"] == "s", "wrong time unit")
    require(
        set(model["geometry"]) == set(geometry)
        and set(model["populations"]) == set(populations),
        "geometry/population roles differ",
    )
    for role, expected in parameters.items():
        if role.startswith("K"):
            unit, basis = "molecule/L", "density"
        elif role.startswith("n"):
            unit, basis = "1", "dimensionless"
        elif role.startswith("beta"):
            unit, basis = "1/s", "protein_per_transcript"
        elif role.startswith("sigma"):
            unit, basis = "1/s", "signal_per_synthase"
        elif role.startswith(("b", "h")):
            unit, basis = "molecule/s", "per_representative_cell"
        else:
            unit, basis = "1/s", "first_order"
        require(
            (rates[role]["unit"], rates[role]["basis"]) == (unit, basis),
            "parameter unit/basis differs: " + role,
        )
        require(
            binary64(rates[role]["value"]) == binary64(expected),
            "parameter projection differs: " + role,
        )
    for role, expected in geometry.items():
        require(
            model["geometry"][role]["unit"] == "L"
            and binary64(model["geometry"][role]["value"]) == binary64(expected),
            "volume projection differs: " + role,
        )
    for role, expected in populations.items():
        require(
            binary64(model["populations"][role]) == binary64(expected),
            "population projection differs: " + role,
        )
    for role, expected in initial.items():
        owner = (
            "medium"
            if role[0] == "e"
            else ("strain" + (role[1] if role[0] == "a" else role[-1]))
            if community(case)
            else "cell"
        )
        require(
            states[role]["owner"] == owner
            and states[role]["scope"]
            == ("environment_total" if owner == "medium" else "representative_cell")
            and states[role]["unit"] == "molecule"
            and states[role]["quantity"] == "molecular_count",
            "count scope differs: " + role,
        )
        require(
            binary64(states[role]["initial"]) == binary64(expected),
            "initial projection differs: " + role,
        )


def rebound(model, case):
    """In-memory numeric rebindings only; never emit/approve new FIR artifacts."""
    result = copy.deepcopy(model)
    parameters, geometry, populations, initial = quantities(case)
    require(
        set(indexed(model["parameters"], "id")) == set(parameters),
        "incompatible rebinding",
    )
    for row in result["parameters"]:
        row["value"] = binary64(parameters[row["id"]])
    for row in result["states"]:
        row["initial"] = binary64(initial[row["id"]])
    for owner in result["geometry"]:
        result["geometry"][owner]["value"] = binary64(geometry[owner])
    result["populations"] = {
        owner: binary64(value) for owner, value in populations.items()
    }
    return result


def expression(node, model, states, fluxes=None, depth=0):
    require(isinstance(node, dict) and depth <= 32, "invalid/budgeted expression shape")
    operation = node.get("op")
    if operation in ("state", "parameter", "volume", "population", "flux"):
        require(set(node) == {"op", "id"}, "unknown expression field")
        role = node["id"]
        if operation == "state":
            namespace = states
        elif operation == "parameter":
            namespace = {
                row["id"]: decimal(row["value"]) for row in model["parameters"]
            }
        elif operation == "volume":
            namespace = {
                key: decimal(row["value"]) for key, row in model["geometry"].items()
            }
        elif operation == "population":
            namespace = {
                key: decimal(value) for key, value in model["populations"].items()
            }
        else:
            require(fluxes is not None, "flux reference inside reaction")
            namespace = fluxes
        require(role in namespace, "unresolved expression role: " + str(role))
        return namespace[role]
    if operation in ("add", "subtract", "multiply", "divide"):
        require(set(node) == {"op", "left", "right"}, "unknown expression field")
        left, right = [
            expression(node[key], model, states, fluxes, depth + 1)
            for key in ("left", "right")
        ]
        if operation == "add":
            result = left + right
        elif operation == "subtract":
            result = left - right
        elif operation == "multiply":
            result = left * right
        else:
            result = left / right
    elif operation == "hill_repression":
        require(
            set(node) == {"op", "sensor", "threshold", "exponent"}, "unknown Hill field"
        )
        sensor, threshold, exponent = [
            expression(node[key], model, states, fluxes, depth + 1)
            for key in ("sensor", "threshold", "exponent")
        ]
        require(
            sensor.is_finite()
            and sensor >= 0
            and threshold > 0
            and exponent in (1, 2, 3, 4),
            "undefined Hill sensor/domain",
        )
        if sensor <= threshold:
            result = 1 / (1 + (sensor / threshold) ** int(exponent))
        else:
            power = (threshold / sensor) ** int(exponent)
            result = power / (1 + power)
    else:
        raise ValueError("unsupported expression operation")
    require(result.is_finite(), "nonfinite expression result")
    return result


def coefficient(value, model):
    if type(value) in (int, float):
        require(value in (-1, 1), "unsupported literal coefficient")
        return Fraction(value)
    require(
        isinstance(value, dict)
        and set(value) == {"op", "id"}
        and value["op"] in ("population", "negative_population"),
        "unknown population coefficient",
    )
    require(value["id"] in model["populations"], "unresolved population coefficient")
    population = Fraction(binary64(model["populations"][value["id"]]))
    return population if value["op"] == "population" else -population


def evaluated(model, states):
    require(
        set(states) == set(indexed(model["states"], "id"))
        and all(
            isinstance(value, D) and value.is_finite() for value in states.values()
        ),
        "nonfinite/misaligned count probe",
    )
    reactions = indexed(model["reactions"], "id")
    equations = indexed(model["equations"], "state")
    require(set(equations) == set(states), "equation state coverage differs")
    fluxes = {
        role: expression(reaction["flux"], model, states)
        for role, reaction in reactions.items()
    }
    aggregate = dict.fromkeys(states, D(0))
    for role, reaction in reactions.items():
        require(
            set(reaction) == {"id", "flux", "stoichiometry"}, "unknown reaction field"
        )
        for state, encoded in reaction["stoichiometry"].items():
            require(state in states, "unresolved update state")
            amount = coefficient(encoded, model)
            aggregate[state] += (
                D(amount.numerator) / D(amount.denominator) * fluxes[role]
            )
    for row in equations.values():
        require(
            set(row) == {"state", "unit", "rhs"} and row["unit"] == "molecule/s",
            "unknown equation field/unit",
        )
    rhs = {
        role: expression(row["rhs"], model, states, fluxes)
        for role, row in equations.items()
    }
    return aggregate, rhs


def transport_balance(model):
    checked = 0
    for reaction in model["reactions"]:
        if not reaction["id"].startswith(("export", "import")):
            continue
        updates = {
            state: coefficient(value, model)
            for state, value in reaction["stoichiometry"].items()
        }
        for signal in range(1, 4):
            balance = updates.get(f"e{signal}", Fraction(0))
            balance += sum(
                Fraction(binary64(model["populations"][f"strain{strain}"]))
                * updates.get(f"a{strain}{signal}", Fraction(0))
                for strain in range(1, 4)
            )
            require(
                balance == 0,
                "exact weighted transport balance differs: " + reaction["id"],
            )
            checked += 1
    require(
        checked == (54 if model["populations"] else 0),
        "transport role coverage differs",
    )
    return checked


def difference(actual, expected, label):
    require(set(actual) == set(expected), "comparison role coverage differs")
    error = max(
        abs(actual[key] - expected[key]) / max(D(1), abs(expected[key]))
        for key in expected
    )
    require(error <= ALGEBRA_LIMIT, label + " disagreement")
    return error


def weighted_balance(model, states, derivative):
    if not model["populations"]:
        return D(0)
    rates = {row["id"]: decimal(row["value"]) for row in model["parameters"]}
    populations = {
        owner: decimal(value) for owner, value in model["populations"].items()
    }
    actual, expected = {}, {}
    for k in range(1, 4):
        actual[str(k)] = derivative[f"e{k}"] + sum(
            populations[f"strain{j}"] * derivative[f"a{j}{k}"] for j in range(1, 4)
        )
        expected[str(k)] = (
            populations[f"strain{k}"] * rates[f"sigma{k}"] * states[f"p{k}"]
            - sum(
                populations[f"strain{j}"] * rates[f"ga{j}{k}"] * states[f"a{j}{k}"]
                for j in range(1, 4)
            )
            - rates[f"ge{k}"] * states[f"e{k}"]
        )
    return difference(actual, expected, "weighted source/loss balance")


def points(case, reference):
    roles = reference_order(case)
    initial = dict(
        zip(roles, [decimal(value) for value in case["initial_counts"]], strict=True)
    )
    yield "initial", initial
    yield "zero", dict.fromkeys(roles, D(0))
    ramp = {role: D(i + 1) / 2 for i, role in enumerate(roles)}
    yield "positive_ramp", ramp
    yield (
        "perturbed_initial",
        {role: initial[role] + D(i + 1) / 4 for i, role in enumerate(roles)},
    )
    if "times" in case:
        for time in case["times"]:
            yield (
                "analytical_t=" + str(time),
                dict(zip(roles, reference.state(case["id"], time), strict=True)),
            )


def audit_case(model, case, reference=None):
    reference = oracle() if reference is None else reference
    check_projection(model, case)
    exact_checks = transport_balance(model)
    rows, low = [], {}
    for precision in PRECISIONS:
        with localcontext() as context:
            context.prec = precision
            for name, states in points(case, reference):
                aggregate, rhs = evaluated(model, states)
                expected = dict(
                    zip(
                        reference_order(case),
                        reference.rhs(
                            lifted(case),
                            [states[role] for role in reference_order(case)],
                        ),
                        strict=True,
                    )
                )
                errors = {
                    "reaction_vs_reference": difference(
                        aggregate, expected, "reaction/P09"
                    ),
                    "equation_vs_reference": difference(rhs, expected, "equation/P09"),
                    "reaction_vs_equation": difference(
                        aggregate, rhs, "reaction/equation"
                    ),
                    "weighted_reaction_balance": weighted_balance(
                        model, states, aggregate
                    ),
                    "weighted_equation_balance": weighted_balance(model, states, rhs),
                }
                if precision == PRECISIONS[0]:
                    low[name] = rhs
                else:
                    errors["precision_refinement"] = difference(
                        low[name], rhs, "precision refinement"
                    )
                rows.append(
                    {
                        "precision": precision,
                        "probe": name,
                        "counts_by_id": {
                            key: str(value) for key, value in states.items()
                        },
                        "reaction_sum": {
                            key: str(value) for key, value in aggregate.items()
                        },
                        "equation_rhs": {key: str(value) for key, value in rhs.items()},
                        "p09_rhs": {key: str(value) for key, value in expected.items()},
                        "max_scaled_differences": {
                            key: str(value) for key, value in errors.items()
                        },
                    }
                )
    input_values = dict(
        zip(
            ("parameters", "geometry", "populations", "initial_counts"),
            quantities(case),
            strict=True,
        )
    )
    return {
        "case": case["id"],
        "definition": case,
        "reference_state_ids": reference_order(case),
        "binary64_inputs_hex": {
            kind: {role: binary64(value).hex() for role, value in values.items()}
            for kind, values in input_values.items()
        },
        "exact_transport_coefficient_checks": exact_checks,
        "evaluations": rows,
    }


def cases():
    primary = pinned(ROOT / "conformance/oscillators/cases.json", PRIMARY_SHA256)[
        "cases"
    ]
    components = pinned(REFERENCE.with_name("cases.json"), COMPONENT_SHA256)["cases"]
    probes = pinned(HERE / "equation-probes.json", PROBES_SHA256)["cases"]
    return primary, components, probes


def report():
    reference = oracle()
    primary, components, probes = cases()
    models = {
        case["model"]: json.loads(
            (HERE / "examples" / case["id"] / "fir.json").read_bytes()
        )["model"]
        for case in primary
    }
    inputs = [
        REFERENCE,
        REFERENCE.with_name("cases.json"),
        ROOT / "conformance/oscillators/cases.json",
        HERE / "equation-probes.json",
        *[HERE / "examples" / case["id"] / "fir.json" for case in primary],
        Path(__file__),
        HERE / "test_equations.py",
    ]
    result = {
        "status": "PASS_PROPOSED_P10_EQUATION_AUDIT",
        "native_fenix": "NOT_RUN_UNSUPPORTED_PROFILE",
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "precision_digits": PRECISIONS,
        "proposed_algebra_scaled_limit": str(ALGEBRA_LIMIT),
        "numeric_interpretation": "exact Decimal lift of represented binary64 inputs",
        "input_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in inputs},
        "cases": [],
    }
    for group, definitions in (
        ("primary", primary),
        ("analytical_component", components),
        ("proposed_asymmetric", probes),
    ):
        for case in definitions:
            model = models[case["model"]]
            if group != "primary":
                model = rebound(model, case)
            row = audit_case(model, case, reference)
            row["group"] = group
            result["cases"].append(row)
    result["counts"] = {
        "definitions": len(result["cases"]),
        "precision_probe_vectors": sum(
            len(row["evaluations"]) for row in result["cases"]
        ),
        "state_values_per_comparison_path": sum(
            len(point["counts_by_id"])
            for row in result["cases"]
            for point in row["evaluations"]
        ),
        "exact_transport_coefficient_checks": sum(
            row["exact_transport_coefficient_checks"] for row in result["cases"]
        ),
    }
    result["max_scaled_difference"] = str(
        max(
            D(value)
            for row in result["cases"]
            for point in row["evaluations"]
            for value in point["max_scaled_differences"].values()
        )
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = report()
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(
        f"PASS: {len(result['cases'])} proposed equation-audit definitions; no native execution"
    )


if __name__ == "__main__":
    main()
