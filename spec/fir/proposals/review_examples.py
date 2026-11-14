"""Proposal-only structural review; no FIR semantic validation or hashing."""

import copy
import json
from pathlib import Path

from jsonschema import Draft7Validator

HERE = Path(__file__).resolve().parent
EXAMPLES = HERE / "examples"


def load(path):
    return json.loads(path.read_text())


def main():
    schema = load(HERE / "fir-m0.schema.json")
    Draft7Validator.check_schema(schema)
    validator = Draft7Validator(schema)
    examples = {p.stem: load(p) for p in sorted(EXAMPLES.glob("*.json"))}
    for name, example in examples.items():
        assert validator.is_valid(example) == (name != "invalid-ssa"), name

    base = examples["production-decay"]
    # Fixed fixture comparisons only; these do not implement a source resolver.
    for suffix in ("initial-five", "no-observables"):
        expected = copy.deepcopy(base)
        source = load(EXAMPLES / f"sources/{suffix}-experiment.json")
        expected["provenance"]["experiment_digest"] = source["digest"]
        if suffix == "initial-five":
            assert source["content"]["initial_counts"][0]["quantity"] == {"value": 5, "unit": "molecule"}
            expected["model"]["states"][0]["initial"] = 5
        else:
            assert source["content"]["observables"] == []
            expected["model"]["observables"] = []
        assert examples[f"production-decay-{suffix}"] == expected
    expected = copy.deepcopy(examples["production-decay-initial-five"])
    expected["model"]["states"][0]["initial"] = 0
    assert examples["invalid-initial-count"] == expected
    expected = copy.deepcopy(examples["production-decay-no-observables"])
    expected["model"]["observables"] = copy.deepcopy(base["model"]["observables"])
    assert examples["invalid-observable-invented"] == expected
    expected = copy.deepcopy(base)
    expected["model"]["observables"] = []
    assert examples["invalid-observable-missing"] == expected
    for suffix, key, value in (("renamed", "id", "protein_amount"), ("target", "state", "other")):
        expected = copy.deepcopy(base)
        expected["model"]["observables"][0][key] = value
        assert examples[f"invalid-observable-{suffix}"] == expected
    for collection in ("states", "observables"):
        bad = copy.deepcopy(base)
        bad["model"][collection][0]["unit"] = "mol"
        assert not validator.is_valid(bad)
    gfp = examples["production-decay-gfp"]
    laci = examples["production-decay-laci"]
    assert base["model"] == gfp["model"] == laci["model"]
    assert gfp["provenance"] != laci["provenance"]
    for key in ("design_digest", "experiment_digest"):
        assert gfp["provenance"][key] != laci["provenance"][key]
    renamed = copy.deepcopy(base["model"])
    renamed["observables"][0]["id"] = "protein_amount"
    assert examples["observable-renamed"] == {"model": renamed}
    assert renamed != base["model"]

    # Whole-envelope comparisons detect accidental extra defects in negatives.
    expected = copy.deepcopy(base)
    expected["model"]["capabilities"]["ssa"] = True
    assert examples["invalid-ssa"] == expected
    expected = copy.deepcopy(base)
    expected["model"]["equations"][0]["rhs"]["right"]["right"]["id"] = "missing"
    assert examples["invalid-reference"] == expected
    expected = copy.deepcopy(base)
    expected["model"]["reactions"][0]["stoichiometry"]["x"] = -1
    assert examples["invalid-production-sign"] == expected
    expected = copy.deepcopy(base)
    expected["model"]["reactions"][0]["flux"]["id"] = "beta"
    expected["model"]["reactions"][1]["flux"]["left"]["id"] = "alpha"
    assert examples["invalid-rate-references"] == expected
    expected = copy.deepcopy(base)
    rhs = expected["model"]["equations"][0]["rhs"]
    rhs["left"], rhs["right"] = rhs["right"], rhs["left"]
    assert examples["invalid-equation"] == expected
    expected = copy.deepcopy(base)
    expected["model"]["reactions"][1]["stoichiometry"]["x"] = 1
    assert examples["invalid-decay-sign"] == expected
    expected = copy.deepcopy(base)
    expected["model"]["reactions"][0]["flux"] = copy.deepcopy(base["model"]["reactions"][1]["flux"])
    assert examples["invalid-production-role"] == expected
    expected = copy.deepcopy(base)
    expected["model"]["equations"][0]["rhs"] = {"op": "parameter", "id": "alpha"}
    assert examples["invalid-equation-missing-decay"] == expected
    for name, key, value in (("invalid-parameter-map-reference", "bioir_parameter_id", "missing"),
                             ("invalid-parameter-map-role", "bioir_function_id", "decay")):
        expected = copy.deepcopy(base)
        expected["provenance"]["symbol_map"]["parameters"][0][key] = value
        assert examples[name] == expected

    renamed_source = examples["production-decay-renamed-parameters"]
    assert renamed_source["model"] == base["model"]
    assert [item["bioir_parameter_id"] for item in renamed_source["provenance"]["symbol_map"]["parameters"]] == ["k_prod", "k_loss"]
    expected = copy.deepcopy(base)
    expected["provenance"]["design_digest"] = load(EXAMPLES / "sources/renamed-parameters-design.json")["digest"]
    expected["provenance"]["experiment_digest"] = load(EXAMPLES / "sources/renamed-parameters-experiment.json")["digest"]
    for entry, parameter, function in zip(expected["provenance"]["symbol_map"]["parameters"],
                                          ("k_prod", "k_loss"), ("synthesis", "degradation")):
        entry.update(bioir_parameter_id=parameter, bioir_function_id=function)
    assert renamed_source == expected
    for name, label in (("display-label-a", "Protein amount"), ("display-label-b", "Expected protein molecules per cell")):
        expected = copy.deepcopy(base)
        expected["provenance"]["display_labels"] = {"observables": {"amount_x": label}}
        assert examples[name] == expected

    # General schema permits standalone and partial provenance; the producer
    # contract, rather than an origin flag, requires complete compiler output.
    assert validator.is_valid({"model": base["model"]})
    assert validator.is_valid({"model": base["model"], "provenance": {}})
    partial = copy.deepcopy(base)
    del partial["provenance"]["symbol_map"]
    assert validator.is_valid(partial)
    partial = copy.deepcopy(base)
    del partial["provenance"]["experiment_digest"]
    assert validator.is_valid(partial)

    entry = base["provenance"]["symbol_map"]["states"][0]
    for states in ([], [entry, entry]):
        bad = copy.deepcopy(base)
        bad["provenance"]["symbol_map"]["states"] = states
        assert not validator.is_valid(bad)
    for key in entry:
        bad = copy.deepcopy(base)
        del bad["provenance"]["symbol_map"]["states"][0][key]
        assert not validator.is_valid(bad), key
    bad = copy.deepcopy(base)
    bad["provenance"]["symbol_map"]["states"][0]["fir_state_id"] = "y"
    assert not validator.is_valid(bad)
    bad = copy.deepcopy(base)
    del bad["provenance"]["symbol_map"]["states"]
    assert not validator.is_valid(bad)
    bad = copy.deepcopy(base)
    del bad["provenance"]["design_digest"]
    assert not validator.is_valid(bad)
    bad = copy.deepcopy(base)
    bad["provenance"]["symbol_map"]["reactions"] = []
    assert not validator.is_valid(bad)
    # Unresolved source IDs remain a separate post-ratification provenance check.
    for key in ("bioir_species_id", "bioir_port_id", "bioir_compartment_id"):
        unresolved = copy.deepcopy(base)
        unresolved["provenance"]["symbol_map"]["states"][0][key] = "missing"
        assert validator.is_valid(unresolved), key

    source_schema = Draft7Validator(load(HERE.parents[1] / "bioir/proposals/bioir-m0.schema.json"))
    sources = sorted((EXAMPLES / "sources").glob("*.json"))
    assert len(sources) == 8
    for path in sources:
        source_schema.validate(load(path))
    parameters = base["provenance"]["symbol_map"]["parameters"]
    for values in ([], parameters[:1], [parameters[0], parameters[0]], parameters + parameters[:1]):
        bad = copy.deepcopy(base)
        bad["provenance"]["symbol_map"]["parameters"] = values
        assert not validator.is_valid(bad)
    for key in parameters[0]:
        bad = copy.deepcopy(base)
        del bad["provenance"]["symbol_map"]["parameters"][0][key]
        assert not validator.is_valid(bad)
    bad = copy.deepcopy(base)
    del bad["provenance"]["symbol_map"]["parameters"]
    assert not validator.is_valid(bad)
    reversed_map = copy.deepcopy(base)
    reversed_map["provenance"]["symbol_map"]["parameters"].reverse()
    assert validator.is_valid(reversed_map)
    for labels in ({}, {"amount_x": ""}, {"amount_x": "Molecules λ"}, {"missing": "Unresolved label"}):
        candidate = copy.deepcopy(base)
        candidate["provenance"]["display_labels"] = {"observables": labels}
        assert validator.is_valid(candidate)
    for labels in ({"amount_x": 1}, {"invalid id": "label"}):
        bad = copy.deepcopy(base)
        bad["provenance"]["display_labels"] = {"observables": labels}
        assert not validator.is_valid(bad)
    bad = copy.deepcopy(base)
    bad["model"]["observables"][0]["label"] = "Misplaced label"
    assert not validator.is_valid(bad)
    print(f"PASS: {len(examples)} FIR examples, 8 source structures, identity/isolation, source-correspondence fixtures, labels and mapping assertions (not FIR semantics).")


if __name__ == "__main__":
    main()
