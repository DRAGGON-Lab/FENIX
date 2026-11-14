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
    bad["provenance"]["symbol_map"]["parameters"] = []
    assert not validator.is_valid(bad)
    # Unresolved source IDs remain a separate post-ratification provenance check.
    for key in ("bioir_species_id", "bioir_port_id", "bioir_compartment_id"):
        unresolved = copy.deepcopy(base)
        unresolved["provenance"]["symbol_map"]["states"][0][key] = "missing"
        assert validator.is_valid(unresolved), key

    source_schema = Draft7Validator(load(HERE.parents[1] / "bioir/proposals/bioir-m0.schema.json"))
    sources = sorted((EXAMPLES / "sources").glob("*.json"))
    assert len(sources) == 4
    for path in sources:
        source_schema.validate(load(path))
    print(f"PASS: {len(examples)} FIR examples, 4 source structures, identity/isolation and mapping assertions (not FIR semantics).")


if __name__ == "__main__":
    main()
