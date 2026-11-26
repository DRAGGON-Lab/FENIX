"""PROPOSED P10 finite shapes and literal AST construction, never native FENIX."""

from __future__ import annotations

from functools import reduce

VERSION = "0.3.0"
CANON = "0.2.0"
SINGLE = "repressilator.single_cell.v1"
COMMUNITY = "repressilator.three_strain.v1"
SAFE = 2**53 - 1
ID = {
    "type": "string",
    "pattern": "^[A-Za-z][A-Za-z0-9_-]*$",
    "maxLength": 64,
    "not": {"pattern": "[^A-Za-z0-9_-]"},
}
DIGEST = {
    "type": "string",
    "pattern": "^[0-9a-f]{64}$",
    "minLength": 64,
    "maxLength": 64,
}


def obj(properties):
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def const(value):
    return {"const": value}


def array(items, count=None):
    result = {"type": "array", "items": items}
    if count is not None:
        result.update(minItems=count, maxItems=count)
    return result


def collection(items, roles, key="id"):
    result = array(items, len(roles))
    result["allOf"] = [
        {"contains": {"properties": {key: const(role)}, "required": [key]}}
        for role in roles
    ]
    return result


def number(positive=False, integer=False, maximum=None):
    result = {"type": "integer" if integer else "number"}
    result["exclusiveMinimum" if positive and not integer else "minimum"] = (
        0 if not integer or not positive else 1
    )
    if maximum is not None:
        result["maximum"] = maximum
    return result


def quantity(unit, positive=False):
    return obj({"value": number(positive), "unit": const(unit)})


def endpoint():
    return obj({key: ID for key in ("owner", "species", "port")})


def owners(community):
    return ["strain1", "strain2", "strain3", "medium"] if community else ["cell"]


def state_owners(community):
    result = {}
    for i in range(1, 4):
        owner = f"strain{i}" if community else "cell"
        result.update({f"m{i}": owner, f"p{i}": owner})
    if community:
        result.update(
            {f"a{j}{k}": f"strain{j}" for j in range(1, 4) for k in range(1, 4)}
        )
        result.update({f"e{k}": "medium" for k in range(1, 4)})
    return dict(sorted(result.items()))


def parameter_roles(community):
    result = {}
    for i in range(1, 4):
        for prefix, unit, basis in (
            ("b", "molecule/s", "per_representative_cell"),
            ("h", "molecule/s", "per_representative_cell"),
            ("gm", "1/s", "first_order"),
            ("gp", "1/s", "first_order"),
            ("beta", "1/s", "protein_per_transcript"),
            ("K", "molecule/L", "density"),
            ("n", "1", "dimensionless"),
        ):
            result[prefix + str(i)] = (unit, basis)
    if community:
        result.update(
            {f"sigma{i}": ("1/s", "signal_per_synthase") for i in range(1, 4)}
        )
        result.update({f"ge{i}": ("1/s", "first_order") for i in range(1, 4)})
        result.update(
            {
                f"{prefix}{j}{k}": ("1/s", "first_order")
                for prefix in ("ga", "out", "in")
                for j in range(1, 4)
                for k in range(1, 4)
            }
        )
    return dict(sorted(result.items()))


def leaf(op, role):
    return {"op": op, "id": role}


def binary(op, left, right):
    return {"op": op, "left": left, "right": right}


def add(left, right):
    return binary("add", left, right)


def sub(left, right):
    return binary("subtract", left, right)


def mul(left, right):
    return binary("multiply", left, right)


def templates(community):
    """Direct expansion of ADR-P10's proposed reaction/equation tables.

    Shared by the candidate writer only. Reproduction and schema agreement are
    not independent mathematical verification of these proposed expectations.
    """
    reactions, equations = [], []

    def reaction(role, flux, updates):
        reactions.append({"id": role, "flux": flux, "stoichiometry": updates})

    for i in range(1, 4):
        prev = (i + 1) % 3 + 1
        sensor = f"a{i}{prev}" if community else f"p{prev}"
        gain = {
            "op": "hill_repression",
            "sensor": binary(
                "divide",
                leaf("state", sensor),
                leaf("volume", f"strain{i}" if community else "cell"),
            ),
            "threshold": leaf("parameter", f"K{i}"),
            "exponent": leaf("parameter", f"n{i}"),
        }
        reaction(f"basal{i}", leaf("parameter", f"b{i}"), {f"m{i}": 1})
        reaction(f"repressed{i}", mul(leaf("parameter", f"h{i}"), gain), {f"m{i}": 1})
        for name, parameter, target in (
            ("mrna_decay", "gm", "m"),
            ("protein_decay", "gp", "p"),
        ):
            reaction(
                name + str(i),
                mul(
                    leaf("parameter", parameter + str(i)),
                    leaf("state", target + str(i)),
                ),
                {target + str(i): -1},
            )
        reaction(
            f"translation{i}",
            mul(leaf("parameter", f"beta{i}"), leaf("state", f"m{i}")),
            {f"p{i}": 1},
        )
        equations += [
            {
                "state": f"m{i}",
                "unit": "molecule/s",
                "rhs": sub(
                    add(leaf("flux", f"basal{i}"), leaf("flux", f"repressed{i}")),
                    leaf("flux", f"mrna_decay{i}"),
                ),
            },
            {
                "state": f"p{i}",
                "unit": "molecule/s",
                "rhs": sub(
                    leaf("flux", f"translation{i}"), leaf("flux", f"protein_decay{i}")
                ),
            },
        ]
    if community:
        for k in range(1, 4):
            reaction(
                f"synthesis{k}",
                mul(leaf("parameter", f"sigma{k}"), leaf("state", f"p{k}")),
                {f"a{k}{k}": 1},
            )
            reaction(
                f"medium_decay{k}",
                mul(leaf("parameter", f"ge{k}"), leaf("state", f"e{k}")),
                {f"e{k}": -1},
            )
            for j in range(1, 4):
                state, owner = f"a{j}{k}", f"strain{j}"
                reaction(
                    f"signal_decay{j}{k}",
                    mul(leaf("parameter", f"ga{j}{k}"), leaf("state", state)),
                    {state: -1},
                )
                reaction(
                    f"export{j}{k}",
                    mul(leaf("parameter", f"out{j}{k}"), leaf("state", state)),
                    {state: -1, f"e{k}": leaf("population", owner)},
                )
                inward = mul(
                    leaf("parameter", f"in{j}{k}"),
                    mul(
                        leaf("volume", owner),
                        binary(
                            "divide", leaf("state", f"e{k}"), leaf("volume", "medium")
                        ),
                    ),
                )
                reaction(
                    f"import{j}{k}",
                    inward,
                    {state: 1, f"e{k}": leaf("negative_population", owner)},
                )
                incoming = leaf("flux", f"import{j}{k}")
                if j == k:
                    incoming = add(leaf("flux", f"synthesis{k}"), incoming)
                equations.append(
                    {
                        "state": state,
                        "unit": "molecule/s",
                        "rhs": sub(
                            incoming,
                            add(
                                leaf("flux", f"export{j}{k}"),
                                leaf("flux", f"signal_decay{j}{k}"),
                            ),
                        ),
                    }
                )
            exports, imports = [
                reduce(
                    add,
                    [
                        mul(
                            leaf("population", f"strain{j}"),
                            leaf("flux", f"{name}{j}{k}"),
                        )
                        for j in range(1, 4)
                    ],
                )
                for name in ("export", "import")
            ]
            equations.append(
                {
                    "state": f"e{k}",
                    "unit": "molecule/s",
                    "rhs": sub(exports, add(imports, leaf("flux", f"medium_decay{k}"))),
                }
            )
    return sorted(reactions, key=lambda r: r["id"]), sorted(
        equations, key=lambda e: e["state"]
    )
