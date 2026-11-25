"""Offline review of proposed examples. Run with the locked Python dev environment."""

import copy
import hashlib
import json
from fractions import Fraction
from pathlib import Path

import rfc8785
from jsonschema import Draft7Validator

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_bytes())


def check(condition, message):
    if not condition:
        raise ValueError(message)


def check_bindings(design):
    ports = {}
    for owner in design["owners"]:
        for species in owner["species"]:
            for port in species["ports"]:
                key = (owner["id"], species["id"], port["id"])
                check(key not in ports, "duplicate address")
                ports[key] = (owner["role"], species["role"], port["kind"])

    def resolve(address):
        key = tuple(address.get(k) for k in ("owner", "species", "port"))
        check(key in ports, "unresolved address")
        return ports[key]

    edges = [
        (resolve(e["source"]), resolve(e["target"])) for e in design["connections"]
    ]
    required = {
        ((a, "signal", "transport_out"), (b, "signal", "transport_in"))
        for strain in ("sender", "receiver")
        for a, b in ((strain, "env"), ("env", strain))
    }
    required.add(
        (("env", "signal", "density_out"), ("receiver", "reporter", "sensor_in"))
    )
    check(len(edges) == 5 and set(edges) == required, "invalid port bindings")


def main():
    design, experiment, fir, cases = (
        read("examples/" + name + ".json")
        for name in ("design", "experiment", "fir", "cases")
    )
    for schema_name, documents in (("bioir", [design, experiment]), ("fir", [fir])):
        schema = read(schema_name + "-m1.schema.json")
        Draft7Validator.check_schema(schema)
        for document in documents:
            Draft7Validator(schema).validate(document)
    for doc in (design, experiment):
        check(
            hashlib.sha256(rfc8785.dumps(doc["content"])).hexdigest() == doc["digest"],
            "digest",
        )
    check(
        experiment["content"]["design"]
        == {
            "id": design["content"]["id"],
            "revision": design["content"]["revision"],
            "digest": design["digest"],
        },
        "design link",
    )
    check_bindings(design["content"])
    for mutation in cases["invalid_bindings"]:
        candidate = copy.deepcopy(design["content"])
        candidate["connections"][mutation["edge"]].update(
            {k: v for k, v in mutation.items() if k != "edge"}
        )
        try:
            check_bindings(candidate)
        except ValueError:
            continue
        raise ValueError("negative binding accepted")

    model = fir["model"]
    for key in ("parameters", "initial_counts", "populations", "observables"):
        check(model[key] == experiment["content"][key], key)
    check(
        model["volumes"]
        == {o["role"]: o["volume"] for o in design["content"]["owners"]},
        "volumes",
    )
    for kind, doc in (("design", design), ("experiment", experiment)):
        check(fir["provenance"][kind + "_digest"] == doc["digest"], "source link")
    p = {k: Fraction(v["value"]) for k, v in model["parameters"].items()}
    a = {k: Fraction(v["value"]) for k, v in model["initial_counts"].items()}
    volume = {k: Fraction(v["value"]) for k, v in model["volumes"].items()}
    density = a["env.signal"] / volume["env"]
    strains = ("sender", "receiver")
    # Evaluate inward and outward transfers independently of the derivative table.
    flux = [
        p[k + "_export"] * a[k + ".signal"] - p[k + "_import"] * volume[k] * density
        for k in strains
    ]
    expected = cases["closed_transport"]
    check(flux == expected["net_out_per_cell"], "exchange rates")
    n = [model["populations"][k] for k in strains]
    activation = 1 / (1 + (p["threshold"] / density) ** int(p["hill_n"]))
    slopes = [
        -flux[0],
        -flux[1],
        sum(x * j for x, j in zip(n, flux)),
        p["reporter_induced"] * activation,
    ]
    check(slopes == expected["derivative"], "closed transport and sensing")
    check(
        sum(x * a[k + ".signal"] for x, k in zip(n, strains)) + a["env.signal"]
        == expected["weighted_signal"],
        "mass",
    )
    check(
        sum(x * j for x, j in zip(n, slopes)) + slopes[2]
        == expected["weighted_derivative"],
        "mass balance",
    )
    print(
        "PASS: three proposed documents, four invalid bindings and exact closed-transport example"
    )


if __name__ == "__main__":
    main()
