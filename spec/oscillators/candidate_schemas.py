"""Build PROPOSED P10 structural schemas; never updates accepted specifications."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from wire_shapes import (
    CANON,
    COMMUNITY,
    DIGEST,
    ID,
    SAFE,
    SINGLE,
    VERSION,
    array,
    collection,
    const,
    endpoint,
    number,
    obj,
    owners,
    parameter_roles,
    quantity,
    state_owners,
    templates,
)

HERE = Path(__file__).resolve().parent
REVISION = {"type": "integer", "minimum": 1, "maximum": SAFE}
UNITS = {"enum": ["molecule/s", "1/s", "molecule/L", "1"]}


def schema(name, body):
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": f"urn:fenix:proposed:p10:{name}",
        "title": "PROPOSED P10 " + name,
        "$comment": "Structural candidate only. Raw tokens, exact source correspondence and independent scientific approval remain separate.",
        **body,
    }


def source_schema():
    designs = []
    for community in (False, True):
        states, parameters = state_owners(community), parameter_roles(community)
        owner_shapes = []
        for owner in owners(community):
            species_shapes = []
            roles = [role for role, at in states.items() if at == owner]
            for role in roles:
                kinds = ["molecular_count"]
                if role.startswith("a"):
                    kinds += ["density_out", "transport_out", "transport_in"]
                elif role.startswith("e"):
                    kinds += ["transport_out", "transport_in"]
                elif role.startswith("p") and not community:
                    kinds += ["density_out"]
                species_shapes.append(
                    obj(
                        {
                            "id": ID,
                            "role": const(role),
                            "ports": collection(
                                obj({"id": ID, "kind": {"enum": kinds}}), kinds, "kind"
                            ),
                        }
                    )
                )
            owner_shapes.append(
                obj(
                    {
                        "id": ID,
                        "role": const(owner),
                        "volume": quantity("L", True),
                        "species": collection({"oneOf": species_shapes}, roles, "role"),
                    }
                )
            )
        parameter_shapes = [
            obj(
                {
                    "id": ID,
                    "role": const(role),
                    "unit": const(unit),
                    "basis": const(basis),
                }
            )
            for role, (unit, basis) in parameters.items()
        ]
        common = {
            "kind": const("Design"),
            "schema_version": const(VERSION),
            "id": ID,
            "revision": REVISION,
            "template": const(COMMUNITY if community else SINGLE),
            "owners": collection({"oneOf": owner_shapes}, owners(community), "role"),
            "parameters": collection(
                {"oneOf": parameter_shapes}, list(parameters), "role"
            ),
            "gates": collection(
                obj(
                    {
                        "id": ID,
                        "role": {"enum": ["g1", "g2", "g3"]},
                        "transcript": endpoint(),
                        "protein": endpoint(),
                        "sensor": endpoint(),
                        "parameters": obj(
                            {
                                key: ID
                                for key in (
                                    "basal",
                                    "induced",
                                    "mrna_decay",
                                    "translation",
                                    "protein_decay",
                                    "threshold",
                                    "hill_n",
                                )
                            }
                        ),
                    }
                ),
                ["g1", "g2", "g3"],
                "role",
            ),
            "signal_synthesis": array(
                obj(
                    {"id": ID, "catalyst": endpoint(), "target": endpoint(), "rate": ID}
                ),
                3 if community else 0,
            ),
            "signal_losses": array(
                obj({"id": ID, "target": endpoint(), "rate": ID}),
                12 if community else 0,
            ),
            "transport": array(
                obj({"id": ID, "source": endpoint(), "target": endpoint(), "rate": ID}),
                18 if community else 0,
            ),
        }
        designs.append(obj(common))
    experiment = obj(
        {
            "kind": const("Experiment"),
            "schema_version": const(VERSION),
            "id": ID,
            "revision": REVISION,
            "design": obj({"id": ID, "revision": REVISION, "digest": DIGEST}),
            "populations": {
                "oneOf": [
                    array({}, 0),
                    array(obj({"owner": ID, "value": number(True, True, SAFE)}), 3),
                ]
            },
            "parameters": {
                "oneOf": [
                    array(obj({"parameter": ID, "value": number(), "unit": UNITS}), n)
                    for n in (21, 54)
                ]
            },
            "initial_counts": {
                "oneOf": [
                    array(
                        obj(
                            {
                                "target": endpoint(),
                                "value": number(),
                                "unit": const("molecule"),
                            }
                        ),
                        n,
                    )
                    for n in (6, 18)
                ]
            },
            "observables": array(obj({"id": ID, "target": endpoint()})),
            "interventions": array({}, 0),
        }
    )
    envelope = obj(
        {
            "content": {"oneOf": [*designs, experiment]},
            "digest": DIGEST,
            "metadata": {"type": "object"},
        }
    )
    envelope["required"].remove("metadata")
    return schema("bioir-oscillator", envelope)


def provenance_schema(community, reactions):
    source = obj(
        {
            "schema_version": const(VERSION),
            "id": ID,
            "revision": REVISION,
            "digest": DIGEST,
        }
    )
    mapping = obj(
        {
            "owners": collection(
                obj({"fir_owner": {"enum": owners(community)}, "source_owner": ID}),
                owners(community),
                "fir_owner",
            ),
            "states": collection(
                obj(
                    {
                        "fir_state": {"enum": list(state_owners(community))},
                        "source_endpoint": endpoint(),
                    }
                ),
                list(state_owners(community)),
                "fir_state",
            ),
            "parameters": collection(
                obj(
                    {
                        "fir_parameter": {"enum": list(parameter_roles(community))},
                        "source_parameter": ID,
                    }
                ),
                list(parameter_roles(community)),
                "fir_parameter",
            ),
            "reactions": collection(
                obj(
                    {
                        "fir_reaction": {"enum": [r["id"] for r in reactions]},
                        "source_collection": {
                            "enum": [
                                "gates",
                                "signal_synthesis",
                                "signal_losses",
                                "transport",
                            ]
                        },
                        "source_function": ID,
                        "source_role": {
                            "enum": [
                                "basal",
                                "induced",
                                "mrna_decay",
                                "translation",
                                "protein_decay",
                                "synthesis",
                                "loss",
                                "export",
                                "import",
                            ]
                        },
                    }
                ),
                [r["id"] for r in reactions],
                "fir_reaction",
            ),
        }
    )
    return {
        "oneOf": [
            {"type": "null"},
            obj({"design": source, "experiment": source, "symbol_map": mapping}),
        ]
    }


def fir_schema():
    branches = []
    for community in (False, True):
        states, parameters = state_owners(community), parameter_roles(community)
        reactions, equations = templates(community)
        state_shapes = []
        observable_shapes = []
        for role, owner in states.items():
            fields = {
                "id": const(role),
                "owner": const(owner),
                "quantity": const("molecular_count"),
                "scope": const(
                    "environment_total" if owner == "medium" else "representative_cell"
                ),
                "unit": const("molecule"),
                "initial": number(),
            }
            state_shapes.append(obj(fields))
            observable_shapes.append(
                obj(
                    {
                        "id": ID,
                        "state": const(role),
                        "owner": fields["owner"],
                        "scope": fields["scope"],
                        "unit": fields["unit"],
                    }
                )
            )
        parameter_shapes = []
        for role, (unit, basis) in parameters.items():
            value = number(positive=role.startswith("K"))
            if role.startswith("n"):
                value = {"type": "integer", "minimum": 1, "maximum": 4}
            parameter_shapes.append(
                obj(
                    {
                        "id": const(role),
                        "value": value,
                        "unit": const(unit),
                        "basis": const(basis),
                    }
                )
            )
        assumptions = [
            "constant_rates",
            "fixed_volume",
            "no_interventions",
            "read_only_sensing",
            "well_mixed",
        ]
        assumptions += (
            ["fixed_populations", "three_strain_ring"]
            if community
            else ["single_representative_cell"]
        )
        model = obj(
            {
                "schema_version": const(VERSION),
                "template": const(COMMUNITY if community else SINGLE),
                "time_unit": const("s"),
                "geometry": obj(
                    {owner: quantity("L", True) for owner in owners(community)}
                ),
                "populations": obj(
                    {
                        owner: number(True, True, SAFE)
                        for owner in owners(community)
                        if owner != "medium"
                    }
                    if community
                    else {}
                ),
                "states": collection({"oneOf": state_shapes}, list(states)),
                "parameters": collection({"oneOf": parameter_shapes}, list(parameters)),
                "reactions": {
                    **array({"enum": reactions}, len(reactions)),
                    "uniqueItems": True,
                },
                "equations": {
                    **array({"enum": equations}, len(equations)),
                    "uniqueItems": True,
                },
                "observables": array({"oneOf": observable_shapes}),
                "assumptions": {
                    **array({"enum": assumptions}, len(assumptions)),
                    "uniqueItems": True,
                },
                "capabilities": const({"ode": True, "ssa": False}),
            }
        )
        branches.append(
            obj(
                {
                    "canonicalization_version": const(CANON),
                    "model": model,
                    "provenance": provenance_schema(community, reactions),
                }
            )
        )
    return schema("fir-oscillator", {"oneOf": branches})


def result_schema():
    result = json.loads(
        (HERE.parent / "results/proposals/ode-result-m0.schema.json").read_bytes()
    )
    result = schema(
        "ode-result-oscillator",
        {k: v for k, v in result.items() if not k.startswith("$") and k != "title"},
    )
    properties = result["properties"]
    properties["schema_version"] = const("0.2.0")
    states = list(state_owners(True))
    properties["state_ids"] = {
        "oneOf": [const(list(state_owners(c))) for c in (False, True)]
    }
    properties["state_units"] = {
        "oneOf": [array(const("molecule"), n) for n in (6, 18)]
    }
    properties["state_values"]["items"] = {
        "oneOf": [array(number(), n) for n in (6, 18)]
    }
    properties["observable_state_ids"]["items"] = {"enum": states}
    for prefix in ("state", "observable"):
        properties[prefix + "_owners"] = array({"enum": ["cell", *owners(True)]})
        properties[prefix + "_scopes"] = array(
            {"enum": ["representative_cell", "environment_total"]}
        )
        result["required"] += [prefix + "_owners", prefix + "_scopes"]
    result["allOf"] = []
    for community in (False, True):
        roles = state_owners(community)
        result["allOf"].append(
            {
                "if": {"properties": {"state_ids": const(list(roles))}},
                "then": {
                    "properties": {
                        "state_owners": const(list(roles.values())),
                        "state_scopes": const(
                            [
                                "environment_total"
                                if o == "medium"
                                else "representative_cell"
                                for o in roles.values()
                            ]
                        ),
                        "state_units": const(["molecule"] * len(roles)),
                        "state_values": array(array(number(), len(roles))),
                    }
                },
            }
        )
    return result


def manifest_schema():
    original = json.loads(
        (HERE.parent / "results/proposals/run-manifest-m0.schema.json").read_bytes()
    )
    result = schema(
        "run-manifest-oscillator",
        {
            k: copy.deepcopy(v)
            for k, v in original.items()
            if not k.startswith("$") and k != "title"
        },
    )
    properties, definitions = result["properties"], result["definitions"]
    properties["schema_version"] = const("0.2.0")
    definitions["source"]["properties"]["schema_version"] = const(VERSION)
    properties["fir"]["properties"]["schema_version"] = const(VERSION)
    properties["fir"]["properties"]["canonicalization_version"] = const(CANON)
    properties["output"]["properties"]["schema_version"] = const("0.2.0")
    python = definitions["pythonScipyODE"]
    python["properties"]["profile"] = const("python-scipy-oscillator-ode/0.1.0")
    solver = python["properties"]["solver"]
    solver["properties"]["options"]["properties"]["jacobian"] = {
        "enum": ["state_dependent_exact", "not_supplied"]
    }
    solver["allOf"] = [
        {
            "if": {"properties": {"method": const("Radau")}},
            "then": {
                "properties": {
                    "options": {
                        "properties": {"jacobian": const("state_dependent_exact")}
                    }
                }
            },
            "else": {
                "properties": {
                    "options": {"properties": {"jacobian": const("not_supplied")}}
                }
            },
        }
    ]
    result["allOf"][0]["if"]["properties"]["backend"]["properties"]["profile"] = python[
        "properties"
    ]["profile"]
    julia_original = json.loads(
        (
            HERE.parent / "results/proposals/run-manifest-julia-sciml-m0.schema.json"
        ).read_bytes()
    )
    julia = julia_original["properties"]["backend"]
    julia["properties"]["profile"] = const("julia-sciml-oscillator-ode/0.1.0")
    julia["properties"]["solver"]["properties"]["options"]["properties"]["jacobian"] = (
        const("state_dependent_exact_inplace")
    )
    definitions["juliaScimlODE"] = julia
    properties["backend"]["oneOf"].append({"$ref": "#/definitions/juliaScimlODE"})
    return result


def artifacts():
    return {
        "bioir-oscillator.schema.json": source_schema(),
        "fir-oscillator.schema.json": fir_schema(),
        "ode-result-oscillator.schema.json": result_schema(),
        "run-manifest-oscillator.schema.json": manifest_schema(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        for name, value in artifacts().items():
            if json.loads((HERE / "schemas" / name).read_bytes()) != value:
                raise ValueError("schema differs from proposed construction: " + name)
        print("PASS: proposed schema reproduction only; not independent science")
        return
    if args.output_dir is None:
        parser.error("--output-dir must be a new directory (or use --check)")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    for name, value in artifacts().items():
        (args.output_dir / name).write_text(
            json.dumps(value, indent=2, allow_nan=False) + "\n"
        )


if __name__ == "__main__":
    main()
