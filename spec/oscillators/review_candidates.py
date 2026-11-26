"""Read-only bounded P10 example audit, not a native parser or scientific gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from importlib.metadata import version
from pathlib import Path

import rfc8785
from jsonschema import Draft7Validator

HERE = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_bytes())


def validate(kind, document):
    schema = read(HERE / "schemas" / (kind + "-oscillator.schema.json"))
    Draft7Validator.check_schema(schema)
    Draft7Validator(schema).validate(document)


def hashed(content):
    return hashlib.sha256(rfc8785.dumps(content)).hexdigest()


def by_id(rows, key="id"):
    result = {row[key]: row for row in rows}
    require(len(result) == len(rows), "duplicate " + key)
    return result


def source_bindings(design):
    """Check literal endpoints independently of the example/schema builders."""
    owners = by_id(design["owners"])
    parameters = by_id(design["parameters"])
    endpoints, species = {}, {}
    for owner in owners.values():
        for item in by_id(owner["species"]).values():
            role = item["role"]
            require(role not in species, "duplicate species role")
            species[role] = (owner["id"], item["id"])
            for port in by_id(item["ports"]).values():
                endpoints[(owner["id"], item["id"], port["id"])] = (
                    owner["role"],
                    role,
                    port["kind"],
                )

    def resolve(endpoint):
        key = tuple(endpoint[k] for k in ("owner", "species", "port"))
        require(key in endpoints, "unresolved endpoint")
        return endpoints[key]

    used = []

    def rate(identifier, role):
        require(
            identifier in parameters and parameters[identifier]["role"] == role,
            "wrong parameter role",
        )
        used.append(identifier)

    community = design["template"] == "repressilator.three_strain.v1"
    for gate in by_id(design["gates"]).values():
        i = int(gate["role"][-1])
        owner = f"strain{i}" if community else "cell"
        prev = {1: 3, 2: 1, 3: 2}[i]
        sensor = f"a{i}{prev}" if community else f"p{prev}"
        require(
            resolve(gate["transcript"]) == (owner, f"m{i}", "molecular_count"),
            "wrong transcript binding",
        )
        require(
            resolve(gate["protein"]) == (owner, f"p{i}", "molecular_count"),
            "wrong protein binding",
        )
        require(
            resolve(gate["sensor"]) == (owner, sensor, "density_out"),
            "wrong sensor binding",
        )
        for name, prefix in (
            ("basal", "b"),
            ("induced", "h"),
            ("mrna_decay", "gm"),
            ("translation", "beta"),
            ("protein_decay", "gp"),
            ("threshold", "K"),
            ("hill_n", "n"),
        ):
            rate(gate["parameters"][name], prefix + str(i))
    for operation in by_id(design["signal_synthesis"]).values():
        owner, protein, kind = resolve(operation["catalyst"])
        require(
            kind == "molecular_count" and protein.startswith("p"),
            "wrong synthesis catalyst",
        )
        k = protein[-1]
        require(
            owner == "strain" + k
            and resolve(operation["target"]) == (owner, f"a{k}{k}", "molecular_count"),
            "wrong synthesis target",
        )
        rate(operation["rate"], "sigma" + k)
    losses = []
    for operation in by_id(design["signal_losses"]).values():
        _, role, kind = resolve(operation["target"])
        require(
            kind == "molecular_count" and role.startswith(("a", "e")),
            "wrong loss target",
        )
        rate(operation["rate"], "g" + role)
        losses.append(role)
    require(len(set(losses)) == len(losses), "duplicate signal loss")
    edges = set()
    for edge in by_id(design["transport"]).values():
        source, target = resolve(edge["source"]), resolve(edge["target"])
        require(
            source[2] == "transport_out" and target[2] == "transport_in",
            "wrong transport direction",
        )
        outgoing = source[1].startswith("a")
        inside, outside = (source, target) if outgoing else (target, source)
        require(
            inside[1].startswith("a") and outside[1].startswith("e"),
            "transport must cross medium",
        )
        j, k = inside[1][1:]
        require(
            inside[0] == "strain" + j and outside[:2] == ("medium", "e" + k),
            "wrong transport signal/owner",
        )
        direction = "out" if outgoing else "in"
        rate(edge["rate"], direction + j + k)
        edges.add((j, k, direction))
    require(len(edges) == len(design["transport"]), "duplicate transport edge")
    require(
        len(used) == len(set(used)) and set(used) == set(parameters),
        "incomplete/duplicate parameter usage",
    )
    return owners, parameters, resolve


def audit_pair(directory):
    files = {path.name: read(path) for path in Path(directory).glob("*.json")}
    for name, document in files.items():
        kind = (
            "bioir"
            if name in ("design.json", "experiment.json")
            else "fir"
            if name == "fir.json"
            else "ode-result"
            if name.endswith("result.json")
            else "run-manifest"
        )
        validate(kind, document)
    design_doc, experiment_doc, fir, result = (
        files[name]
        for name in (
            "design.json",
            "experiment.json",
            "fir.json",
            "zero-grid.result.json",
        )
    )
    for document in (design_doc, experiment_doc):
        require(
            hashed(document["content"]) == document["digest"], "source digest mismatch"
        )
    design, experiment, model = (
        design_doc["content"],
        experiment_doc["content"],
        fir["model"],
    )
    owners, parameters, resolve = source_bindings(design)
    sources = {
        kind: {
            "schema_version": doc["content"]["schema_version"],
            "id": doc["content"]["id"],
            "revision": doc["content"]["revision"],
            "digest": doc["digest"],
        }
        for kind, doc in (("design", design_doc), ("experiment", experiment_doc))
    }
    require(
        experiment["design"]
        == {k: v for k, v in sources["design"].items() if k != "schema_version"},
        "exact Design reference mismatch",
    )
    require(model["template"] == design["template"], "source template mismatch")
    for kind, reference in sources.items():
        require(fir["provenance"][kind] == reference, "FIR source reference mismatch")
    mapping = fir["provenance"]["symbol_map"]
    require(
        {m["fir_owner"]: m["source_owner"] for m in mapping["owners"]}
        == {o["role"]: o["id"] for o in owners.values()},
        "owner map mismatch",
    )
    require(
        model["geometry"] == {o["role"]: o["volume"] for o in owners.values()},
        "geometry mismatch",
    )
    population_rows = by_id(experiment["populations"], "owner")
    require(
        model["populations"]
        == {
            owners[owner]["role"]: row["value"]
            for owner, row in population_rows.items()
        },
        "population mismatch",
    )
    assignments = by_id(experiment["parameters"], "parameter")
    require(set(assignments) == set(parameters), "source parameter coverage")
    rate_map = {
        m["fir_parameter"]: m["source_parameter"] for m in mapping["parameters"]
    }
    require(
        rate_map == {p["role"]: p["id"] for p in parameters.values()},
        "parameter map mismatch",
    )
    for parameter in model["parameters"]:
        source_id = rate_map[parameter["id"]]
        assignment, declaration = assignments[source_id], parameters[source_id]
        require(
            parameter["value"] == assignment["value"]
            and parameter["unit"] == assignment["unit"] == declaration["unit"]
            and parameter["basis"] == declaration["basis"],
            "source parameter value/unit/basis mismatch",
        )
    initial = {
        tuple(row["target"][k] for k in ("owner", "species", "port")): row
        for row in experiment["initial_counts"]
    }
    require(
        len(initial) == len(experiment["initial_counts"]) == len(model["states"]),
        "initial count coverage",
    )
    state_map = {m["fir_state"]: m["source_endpoint"] for m in mapping["states"]}
    for state in model["states"]:
        address = state_map[state["id"]]
        require(
            resolve(address) == (state["owner"], state["id"], "molecular_count"),
            "state map mismatch",
        )
        row = initial[tuple(address[k] for k in ("owner", "species", "port"))]
        require(
            state["initial"] == row["value"] and row["unit"] == "molecule",
            "initial value mismatch",
        )
    for entry in mapping["reactions"]:
        functions = by_id(design[entry["source_collection"]])
        require(
            entry["source_function"] in functions,
            "unresolved reaction source function",
        )
        function = functions[entry["source_function"]]
        if entry["source_collection"] == "gates":
            suffix = function["role"][-1]
            allowed = {
                name + suffix: role
                for name, role in (
                    ("basal", "basal"),
                    ("repressed", "induced"),
                    ("mrna_decay", "mrna_decay"),
                    ("translation", "translation"),
                    ("protein_decay", "protein_decay"),
                )
            }
        elif entry["source_collection"] == "signal_synthesis":
            allowed = {"synthesis" + resolve(function["catalyst"])[1][-1]: "synthesis"}
        elif entry["source_collection"] == "signal_losses":
            target = resolve(function["target"])[1]
            allowed = {
                ("medium_decay" if target[0] == "e" else "signal_decay")
                + target[1:]: "loss"
            }
        else:
            source, target = (
                resolve(function["source"])[1],
                resolve(function["target"])[1],
            )
            inside, direction = (
                (source, "export") if source[0] == "a" else (target, "import")
            )
            allowed = {direction + inside[1:]: direction}
        require(
            allowed.get(entry["fir_reaction"]) == entry["source_role"],
            "reaction source role mismatch",
        )
    source_observables = by_id(experiment["observables"])
    require(
        set(source_observables) == {o["id"] for o in model["observables"]},
        "observable coverage",
    )
    for observable in model["observables"]:
        require(
            resolve(source_observables[observable["id"]]["target"])
            == (observable["owner"], observable["state"], "molecular_count"),
            "observable target mismatch",
        )
    # The literal examples are already normalized; this verifies that fact, not
    # an implementation of the future normalizer or an independent JCS oracle.
    for key, field in (
        ("states", "id"),
        ("parameters", "id"),
        ("reactions", "id"),
        ("equations", "state"),
        ("observables", "id"),
    ):
        require(
            model[key]
            == sorted(model[key], key=lambda row: row[field].encode("utf-16-be")),
            "example is not normalized",
        )
    require(model["assumptions"] == sorted(model["assumptions"]), "assumption order")
    fir_digest = hashed(
        {
            "domain": "fenix.fir",
            "canonicalization_version": fir["canonicalization_version"],
            "model": model,
        }
    )
    require(result["fir_digest"] == fir_digest, "result FIR identity mismatch")
    require(
        result["state_ids"] == [s["id"] for s in model["states"]]
        and result["state_values"] == [[s["initial"] for s in model["states"]]],
        "zero-grid state samples mismatch",
    )
    for suffix, field in (
        ("ids", "id"),
        ("state_ids", "state"),
        ("units", "unit"),
        ("owners", "owner"),
        ("scopes", "scope"),
    ):
        require(
            result["observable_" + suffix] == [o[field] for o in model["observables"]],
            "result observable metadata mismatch",
        )
    values = dict(zip(result["state_ids"], result["state_values"][0], strict=True))
    require(
        result["observable_values"]
        == [[values[state] for state in result["observable_state_ids"]]],
        "direct observable copies mismatch",
    )
    checksum = hashlib.sha256(
        (Path(directory) / "zero-grid.result.json").read_bytes()
    ).hexdigest()
    for backend in ("python", "julia"):
        manifest = files[f"zero-grid.{backend}.manifest.json"]
        require(
            manifest["sources"] == sources and manifest["fir"]["digest"] == fir_digest,
            "manifest source/FIR mismatch",
        )
        require(
            manifest["output"]["sha256"] == checksum
            and manifest["execution"]["time_grid"] == result["times"] == [0.0],
            "result checksum/grid mismatch",
        )
        require(
            manifest["integration"] == "skipped_zero_grid"
            and manifest["evaluations"]["nfev"] == 0,
            "zero-grid integration mismatch",
        )
    return {
        "status": "PASS_PROPOSED_BOUNDED_EXAMPLE_AUDIT",
        "states": len(model["states"]),
        "parameters": len(model["parameters"]),
        "reactions": len(model["reactions"]),
        "fir_digest_candidate": fir_digest,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    cases = {
        name: audit_pair(HERE / "examples" / name)
        for name in ("single-cell", "three-strain")
    }
    paths = [
        *sorted((HERE / "schemas").glob("*.json")),
        *sorted((HERE / "examples").glob("*/*.json")),
        *sorted(HERE.glob("*.py")),
    ]
    inputs = [
        HERE.parent / "results/proposals" / name
        for name in (
            "ode-result-m0.schema.json",
            "run-manifest-m0.schema.json",
            "run-manifest-julia-sciml-m0.schema.json",
        )
    ]
    inputs += [
        HERE.parents[1] / "conformance/oscillators/cases.json",
        HERE.parents[1] / "packages/python/uv.lock",
    ]
    results = {
        "status": "PASS_PROPOSED_BOUNDED_EXAMPLE_AUDIT",
        "native_fenix": "NOT_RUN_UNSUPPORTED_PROFILE",
        "cases": cases,
        "python": platform.python_version(),
        "jsonschema": version("jsonschema"),
        "rfc8785": version("rfc8785"),
        "artifact_sha256": {
            str(path.relative_to(HERE)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths
        },
        "input_sha256": {
            str(path.relative_to(HERE.parents[1])): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in inputs
        },
    }
    if args.output:
        with args.output.open("x") as stream:
            json.dump(results, stream, indent=2, allow_nan=False)
            stream.write("\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
