# Proposal-only structural review; no FIR semantic validation or hashing.
using JSON, JSONSchema, Test

const examples_dir = joinpath(@__DIR__, "examples")
const schema = JSONSchema.Schema(JSON.parsefile(joinpath(@__DIR__, "fir-m0.schema.json")))
valid(value) = JSONSchema.validate(schema, value) === nothing
const examples = Dict(splitext(name)[1] => JSON.parsefile(joinpath(examples_dir, name))
                      for name in readdir(examples_dir) if endswith(name, ".json"))

@testset "P02 proposal structure (not FIR semantics)" begin
    for (name, example) in examples
        @test valid(example) == (name != "invalid-ssa")
    end
    base = examples["production-decay"]
    gfp = examples["production-decay-gfp"]
    laci = examples["production-decay-laci"]
    @test base["model"] == gfp["model"] == laci["model"]
    @test gfp["provenance"] != laci["provenance"]
    for key in ("design_digest", "experiment_digest")
        @test gfp["provenance"][key] != laci["provenance"][key]
    end
    renamed = deepcopy(base["model"])
    renamed["observables"][1]["id"] = "protein_amount"
    @test examples["observable-renamed"] == Dict("model" => renamed)
    @test renamed != base["model"]

    # Whole-envelope equality detects unrelated defects in each negative.
    expected = deepcopy(base)
    expected["model"]["capabilities"]["ssa"] = true
    @test examples["invalid-ssa"] == expected
    expected = deepcopy(base)
    expected["model"]["equations"][1]["rhs"]["right"]["right"]["id"] = "missing"
    @test examples["invalid-reference"] == expected
    expected = deepcopy(base)
    expected["model"]["reactions"][1]["stoichiometry"]["x"] = -1
    @test examples["invalid-production-sign"] == expected
    expected = deepcopy(base)
    expected["model"]["reactions"][1]["flux"]["id"] = "beta"
    expected["model"]["reactions"][2]["flux"]["left"]["id"] = "alpha"
    @test examples["invalid-rate-references"] == expected
    expected = deepcopy(base)
    rhs = expected["model"]["equations"][1]["rhs"]
    rhs["left"], rhs["right"] = rhs["right"], rhs["left"]
    @test examples["invalid-equation"] == expected

    @test valid(Dict("model" => base["model"]))
    @test valid(Dict("model" => base["model"], "provenance" => Dict()))
    partial = deepcopy(base)
    delete!(partial["provenance"], "symbol_map")
    @test valid(partial)
    partial = deepcopy(base)
    delete!(partial["provenance"], "experiment_digest")
    @test valid(partial)

    entry = base["provenance"]["symbol_map"]["states"][1]
    for states in (Any[], [entry, entry])
        bad = deepcopy(base)
        bad["provenance"]["symbol_map"]["states"] = states
        @test !valid(bad)
    end
    for key in keys(entry)
        bad = deepcopy(base)
        delete!(bad["provenance"]["symbol_map"]["states"][1], key)
        @test !valid(bad)
    end
    bad = deepcopy(base)
    bad["provenance"]["symbol_map"]["states"][1]["fir_state_id"] = "y"
    @test !valid(bad)
    bad = deepcopy(base)
    delete!(bad["provenance"]["symbol_map"], "states")
    @test !valid(bad)
    bad = deepcopy(base)
    delete!(bad["provenance"], "design_digest")
    @test !valid(bad)
    bad = deepcopy(base)
    bad["provenance"]["symbol_map"]["parameters"] = []
    @test !valid(bad)
    # Structure cannot resolve source IDs against a supplied Design.
    for key in ("bioir_species_id", "bioir_port_id", "bioir_compartment_id")
        unresolved = deepcopy(base)
        unresolved["provenance"]["symbol_map"]["states"][1][key] = "missing"
        @test valid(unresolved)
    end

    source_schema = JSONSchema.Schema(JSON.parsefile(joinpath(@__DIR__, "../../bioir/proposals/bioir-m0.schema.json")))
    sources = filter(name -> endswith(name, ".json"), readdir(joinpath(examples_dir, "sources")))
    @test length(sources) == 4
    for name in sources
        @test JSONSchema.validate(source_schema, JSON.parsefile(joinpath(examples_dir, "sources", name))) === nothing
    end
end
