"""Author PROPOSED P10 examples from reviewed P09 inputs, not golden references."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

import rfc8785
from wire_shapes import (
    CANON,
    COMMUNITY,
    SINGLE,
    VERSION,
    owners,
    parameter_roles,
    state_owners,
    templates,
)

HERE = Path(__file__).resolve().parent


def digest(content):
    return hashlib.sha256(rfc8785.dumps(content)).hexdigest()


def envelope(content):
    return {
        "content": content,
        "digest": digest(content),
        "metadata": {
            "status": "PROPOSED illustrative P10 candidate, not native execution"
        },
    }


def examples(case):
    community = case["id"] == "three-strain"
    state_map, rate_roles = state_owners(community), parameter_roles(community)
    owner_ids = dict(
        zip(
            owners(community),
            ["strainA", "strainB", "strainC", "bath"] if community else ["cellA"],
            strict=True,
        )
    )
    species_ids = {
        role: (
            "transcript"
            if role[0] == "m"
            else "synthase"
            if role[0] == "p"
            else "signal" + role[-1]
        )
        if community
        else ("mrna" + role[-1] if role[0] == "m" else "protein" + role[-1])
        for role in state_map
    }

    def endpoint(role, port="amount"):
        return {
            "owner": owner_ids[state_map[role]],
            "species": species_ids[role],
            "port": port,
        }

    study_order = [f"{prefix}{i}" for prefix in ("m", "p") for i in range(1, 4)]
    if community:
        study_order += [f"a{j}{k}" for j in range(1, 4) for k in range(1, 4)] + [
            f"e{i}" for i in range(1, 4)
        ]
    initial = dict(zip(study_order, case["initial_counts"], strict=True))
    values = {}
    for prefix, key in (
        ("b", "basal"),
        ("h", "induced"),
        ("gm", "mrna_decay"),
        ("beta", "translation"),
        ("gp", "protein_decay"),
        ("K", "threshold_density"),
        ("n", "hill_n"),
    ):
        values.update(
            {
                prefix + str(i): float(v)
                for i, v in enumerate(case["parameters"][key], 1)
            }
        )
    if community:
        for prefix, key in (
            ("sigma", "signal_synthesis"),
            ("ge", "medium_signal_decay"),
        ):
            values.update(
                {
                    prefix + str(i): float(v)
                    for i, v in enumerate(case["parameters"][key], 1)
                }
            )
        for prefix, key in (
            ("ga", "intracellular_signal_decay"),
            ("out", "export"),
            ("in", "import"),
        ):
            values.update(
                {
                    f"{prefix}{j}{k}": float(v)
                    for j, row in enumerate(case["parameters"][key], 1)
                    for k, v in enumerate(row, 1)
                }
            )
    volumes = dict(
        zip(
            owners(community),
            [*case["cell_volumes_L"], case["medium_volume_L"]]
            if community
            else [case["cell_volume_L"]],
            strict=True,
        )
    )
    design = {
        "kind": "Design",
        "schema_version": VERSION,
        "id": case["id"],
        "revision": 1,
        "template": COMMUNITY if community else SINGLE,
        "owners": [],
        "parameters": [
            {"id": "par_" + role, "role": role, "unit": unit, "basis": basis}
            for role, (unit, basis) in rate_roles.items()
        ],
        "gates": [],
        "signal_synthesis": [],
        "signal_losses": [],
        "transport": [],
    }
    for owner in owners(community):
        species = []
        for role, at in state_map.items():
            if at != owner:
                continue
            ports = [{"id": "amount", "kind": "molecular_count"}]
            if role[0] == "a" or role[0] == "p" and not community:
                ports.append({"id": "density", "kind": "density_out"})
            if role[0] in ("a", "e"):
                ports += [
                    {"id": "out", "kind": "transport_out"},
                    {"id": "in", "kind": "transport_in"},
                ]
            species.append({"id": species_ids[role], "role": role, "ports": ports})
        design["owners"].append(
            {
                "id": owner_ids[owner],
                "role": owner,
                "volume": {"value": volumes[owner], "unit": "L"},
                "species": species,
            }
        )
    for i in range(1, 4):
        prev = (i + 1) % 3 + 1
        design["gates"].append(
            {
                "id": f"not{i}",
                "role": f"g{i}",
                "transcript": endpoint(f"m{i}"),
                "protein": endpoint(f"p{i}"),
                "sensor": endpoint(
                    f"a{i}{prev}" if community else f"p{prev}", "density"
                ),
                "parameters": {
                    key: f"par_{prefix}{i}"
                    for key, prefix in (
                        ("basal", "b"),
                        ("induced", "h"),
                        ("mrna_decay", "gm"),
                        ("translation", "beta"),
                        ("protein_decay", "gp"),
                        ("threshold", "K"),
                        ("hill_n", "n"),
                    )
                },
            }
        )
    if community:
        for k in range(1, 4):
            design["signal_synthesis"].append(
                {
                    "id": f"synthesize{k}",
                    "catalyst": endpoint(f"p{k}"),
                    "target": endpoint(f"a{k}{k}"),
                    "rate": f"par_sigma{k}",
                }
            )
            for role in [f"a{j}{k}" for j in range(1, 4)] + [f"e{k}"]:
                design["signal_losses"].append(
                    {
                        "id": "loss_" + role,
                        "target": endpoint(role),
                        "rate": "par_g" + role,
                    }
                )
            for j in range(1, 4):
                for direction, source, target in (
                    ("out", f"a{j}{k}", f"e{k}"),
                    ("in", f"e{k}", f"a{j}{k}"),
                ):
                    design["transport"].append(
                        {
                            "id": f"{direction}_{j}{k}",
                            "source": endpoint(source, "out"),
                            "target": endpoint(target, "in"),
                            "rate": f"par_{direction}{j}{k}",
                        }
                    )
    design = envelope(design)
    observed = [f"p{i}" for i in range(1, 4)] + (
        ["a13", "e1", "e2", "e3"] if community else []
    )
    experiment = envelope(
        {
            "kind": "Experiment",
            "schema_version": VERSION,
            "id": "scenario",
            "revision": 1,
            "design": {
                "id": design["content"]["id"],
                "revision": 1,
                "digest": design["digest"],
            },
            "populations": [
                {"owner": owner_ids[f"strain{i}"], "value": n}
                for i, n in enumerate(case["populations"], 1)
            ]
            if community
            else [],
            "parameters": [
                {"parameter": "par_" + role, "value": values[role], "unit": unit}
                for role, (unit, _) in rate_roles.items()
            ],
            "initial_counts": [
                {"target": endpoint(role), "value": initial[role], "unit": "molecule"}
                for role in state_map
            ],
            "observables": [
                {"id": "observe_" + role, "target": endpoint(role)} for role in observed
            ],
            "interventions": [],
        }
    )
    reactions, equations = templates(community)
    model = {
        "schema_version": VERSION,
        "template": design["content"]["template"],
        "time_unit": "s",
        "geometry": {
            role: {"value": value, "unit": "L"} for role, value in volumes.items()
        },
        "populations": {
            f"strain{i}": float(n) for i, n in enumerate(case["populations"], 1)
        }
        if community
        else {},
        "states": [
            {
                "id": role,
                "owner": owner,
                "quantity": "molecular_count",
                "scope": "environment_total"
                if owner == "medium"
                else "representative_cell",
                "unit": "molecule",
                "initial": float(initial[role]),
            }
            for role, owner in state_map.items()
        ],
        "parameters": [
            {"id": role, "value": values[role], "unit": unit, "basis": basis}
            for role, (unit, basis) in rate_roles.items()
        ],
        "reactions": reactions,
        "equations": equations,
        "observables": [
            {
                "id": "observe_" + role,
                "state": role,
                "owner": state_map[role],
                "scope": "environment_total"
                if state_map[role] == "medium"
                else "representative_cell",
                "unit": "molecule",
            }
            for role in sorted(observed)
        ],
        "assumptions": sorted(
            [
                "constant_rates",
                "fixed_volume",
                "no_interventions",
                "read_only_sensing",
                "well_mixed",
            ]
            + (
                ["fixed_populations", "three_strain_ring"]
                if community
                else ["single_representative_cell"]
            )
        ),
        "capabilities": {"ode": True, "ssa": False},
    }
    sources = {
        name: {
            "schema_version": VERSION,
            "id": doc["content"]["id"],
            "revision": 1,
            "digest": doc["digest"],
        }
        for name, doc in (("design", design), ("experiment", experiment))
    }
    reaction_map = []
    for reaction in reactions:
        role = reaction["id"]
        for prefix, source_role in (
            ("basal", "basal"),
            ("repressed", "induced"),
            ("mrna_decay", "mrna_decay"),
            ("protein_decay", "protein_decay"),
            ("translation", "translation"),
        ):
            if role.startswith(prefix):
                collection, function = "gates", "not" + role[len(prefix) :]
                break
        else:
            if role.startswith("synthesis"):
                collection, function, source_role = (
                    "signal_synthesis",
                    "synthesize" + role[9:],
                    "synthesis",
                )
            elif role.startswith("signal_decay"):
                collection, function, source_role = (
                    "signal_losses",
                    "loss_a" + role[12:],
                    "loss",
                )
            elif role.startswith("medium_decay"):
                collection, function, source_role = (
                    "signal_losses",
                    "loss_e" + role[12:],
                    "loss",
                )
            elif role.startswith("export"):
                collection, function, source_role = (
                    "transport",
                    "out_" + role[6:],
                    "export",
                )
            else:
                collection, function, source_role = (
                    "transport",
                    "in_" + role[6:],
                    "import",
                )
        reaction_map.append(
            {
                "fir_reaction": role,
                "source_collection": collection,
                "source_function": function,
                "source_role": source_role,
            }
        )
    fir = {
        "canonicalization_version": CANON,
        "model": model,
        "provenance": {
            **sources,
            "symbol_map": {
                "owners": [
                    {"fir_owner": role, "source_owner": owner_ids[role]}
                    for role in owners(community)
                ],
                "states": [
                    {"fir_state": role, "source_endpoint": endpoint(role)}
                    for role in state_map
                ],
                "parameters": [
                    {"fir_parameter": role, "source_parameter": "par_" + role}
                    for role in rate_roles
                ],
                "reactions": reaction_map,
            },
        },
    }
    fir_digest = digest(
        {"domain": "fenix.fir", "canonicalization_version": CANON, "model": model}
    )
    result = {
        "kind": "ODEResult",
        "schema_version": "0.2.0",
        "fir_digest": fir_digest,
        "time_unit": "s",
        "times": [0.0],
        "state_ids": list(state_map),
        "state_units": ["molecule"] * len(state_map),
        "state_owners": list(state_map.values()),
        "state_scopes": [state["scope"] for state in model["states"]],
        "state_values": [[initial[role] for role in state_map]],
        "observable_ids": [o["id"] for o in model["observables"]],
        "observable_state_ids": [o["state"] for o in model["observables"]],
        "observable_units": ["molecule"] * len(observed),
        "observable_owners": [o["owner"] for o in model["observables"]],
        "observable_scopes": [o["scope"] for o in model["observables"]],
        "observable_values": [[initial[o["state"]] for o in model["observables"]]],
    }
    files = {
        "design.json": design,
        "experiment.json": experiment,
        "fir.json": fir,
        "zero-grid.result.json": result,
    }
    return files, sources, fir_digest


def encoded(value):
    return (json.dumps(value, indent=2, allow_nan=False) + "\n").encode()


def manifests(sources, fir_digest, result_bytes):
    # Explicitly illustrative zero-grid records; no native solver is called.
    source = json.loads(
        (
            HERE.parent / "results/proposals/examples/zero-only.manifest.json"
        ).read_bytes()
    )
    source["schema_version"] = "0.2.0"
    source["sources"] = sources
    source["fir"] = {
        "schema_version": VERSION,
        "canonicalization_version": CANON,
        "digest": fir_digest,
    }
    source["output"]["schema_version"] = "0.2.0"
    source["output"]["sha256"] = hashlib.sha256(result_bytes).hexdigest()
    source["producer"] = {
        "name": "P10-illustrative-not-executed",
        "version": "not-executed",
        "build_id": None,
    }
    python = source["backend"]
    python["profile"] = "python-scipy-oscillator-ode/0.1.0"
    python["solver"]["method"] = "Radau"
    python["solver"]["options"]["jacobian"] = "state_dependent_exact"
    python["environment"] = dict.fromkeys(
        python["environment"], "illustrative_not_observed"
    )
    julia = copy.deepcopy(source)
    julia_schema = json.loads(
        (
            HERE.parent / "results/proposals/run-manifest-julia-sciml-m0.schema.json"
        ).read_bytes()
    )["properties"]["backend"]
    properties = julia_schema["properties"]
    options = {
        key: v.get("const")
        for key, v in properties["solver"]["properties"]["options"][
            "properties"
        ].items()
    }
    options.update(
        save_start=True, maxiters=1000000, jacobian="state_dependent_exact_inplace"
    )
    julia["backend"] = {
        "profile": "julia-sciml-oscillator-ode/0.1.0",
        "solver": {"name": "SciMLBase.solve", "method": "Rodas5P", "options": options},
        "environment": dict.fromkeys(
            properties["environment"]["properties"], "illustrative_not_observed"
        ),
        "evaluations": {"njev": 0, "nw": 0},
    }
    return {
        "zero-grid.python.manifest.json": source,
        "zero-grid.julia.manifest.json": julia,
    }


def artifacts():
    raw = (HERE.parents[1] / "conformance/oscillators/cases.json").read_bytes()
    if (
        hashlib.sha256(raw).hexdigest()
        != "70932f56c47cddb7fd502b165580c65f8a34431721972fbf11a2588ab5c15d25"
    ):
        raise ValueError("reviewed P09 catalog bytes differ")
    result = {}
    for case in json.loads(raw)["cases"]:
        files, sources, fir_digest = examples(case)
        files.update(
            manifests(sources, fir_digest, encoded(files["zero-grid.result.json"]))
        )
        result.update(
            {case["id"] + "/" + name: encoded(value) for name, value in files.items()}
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        for name, raw in artifacts().items():
            if (HERE / "examples" / name).read_bytes() != raw:
                raise ValueError("example differs from proposed construction: " + name)
        print("PASS: proposed example reproduction only; not independent science")
        return
    if args.output_dir is None:
        parser.error("--output-dir must be a new directory (or use --check)")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    for name, raw in artifacts().items():
        path = args.output_dir / name
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(raw)


if __name__ == "__main__":
    main()
