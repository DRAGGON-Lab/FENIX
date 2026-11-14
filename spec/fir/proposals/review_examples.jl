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
    # Known fixture comparisons, not a general source correspondence validator.
    for suffix in ("initial-five", "no-observables")
        expected = deepcopy(base)
        source = JSON.parsefile(joinpath(examples_dir, "sources/$(suffix)-experiment.json"))
        expected["provenance"]["experiment_digest"] = source["digest"]
        if suffix == "initial-five"
            @test source["content"]["initial_counts"][1]["quantity"] == Dict("value" => 5, "unit" => "molecule")
            expected["model"]["states"][1]["initial"] = 5
        else
            @test isempty(source["content"]["observables"])
            expected["model"]["observables"] = []
        end
        @test examples["production-decay-$(suffix)"] == expected
    end
    expected = deepcopy(examples["production-decay-initial-five"])
    expected["model"]["states"][1]["initial"] = 0
    @test examples["invalid-initial-count"] == expected
    expected = deepcopy(examples["production-decay-no-observables"])
    expected["model"]["observables"] = deepcopy(base["model"]["observables"])
    @test examples["invalid-observable-invented"] == expected
    expected = deepcopy(base)
    expected["model"]["observables"] = []
    @test examples["invalid-observable-missing"] == expected
    for (suffix, key, value) in (("renamed", "id", "protein_amount"), ("target", "state", "other"))
        expected = deepcopy(base)
        expected["model"]["observables"][1][key] = value
        @test examples["invalid-observable-$(suffix)"] == expected
    end
    for collection in ("states", "observables")
        bad = deepcopy(base)
        bad["model"][collection][1]["unit"] = "mol"
        @test !valid(bad)
    end
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
    expected = deepcopy(base)
    expected["model"]["reactions"][2]["stoichiometry"]["x"] = 1
    @test examples["invalid-decay-sign"] == expected
    expected = deepcopy(base)
    expected["model"]["reactions"][1]["flux"] = deepcopy(base["model"]["reactions"][2]["flux"])
    @test examples["invalid-production-role"] == expected
    expected = deepcopy(base)
    expected["model"]["equations"][1]["rhs"] = Dict("op" => "parameter", "id" => "alpha")
    @test examples["invalid-equation-missing-decay"] == expected
    for (name, key, value) in (("invalid-parameter-map-reference", "bioir_parameter_id", "missing"),
                               ("invalid-parameter-map-role", "bioir_function_id", "decay"))
        expected = deepcopy(base)
        expected["provenance"]["symbol_map"]["parameters"][1][key] = value
        @test examples[name] == expected
    end
    renamed_source = examples["production-decay-renamed-parameters"]
    @test renamed_source["model"] == base["model"]
    @test [item["bioir_parameter_id"] for item in renamed_source["provenance"]["symbol_map"]["parameters"]] == ["k_prod", "k_loss"]
    expected = deepcopy(base)
    expected["provenance"]["design_digest"] = JSON.parsefile(joinpath(examples_dir, "sources/renamed-parameters-design.json"))["digest"]
    expected["provenance"]["experiment_digest"] = JSON.parsefile(joinpath(examples_dir, "sources/renamed-parameters-experiment.json"))["digest"]
    for (entry, parameter, function_id) in zip(expected["provenance"]["symbol_map"]["parameters"],
                                              ("k_prod", "k_loss"), ("synthesis", "degradation"))
        entry["bioir_parameter_id"] = parameter
        entry["bioir_function_id"] = function_id
    end
    @test renamed_source == expected
    for (name, label) in (("display-label-a", "Protein amount"), ("display-label-b", "Expected protein molecules per cell"))
        expected = deepcopy(base)
        expected["provenance"]["display_labels"] = Dict("observables" => Dict("amount_x" => label))
        @test examples[name] == expected
    end

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
    bad["provenance"]["symbol_map"]["reactions"] = []
    @test !valid(bad)
    # Structure cannot resolve source IDs against a supplied Design.
    for key in ("bioir_species_id", "bioir_port_id", "bioir_compartment_id")
        unresolved = deepcopy(base)
        unresolved["provenance"]["symbol_map"]["states"][1][key] = "missing"
        @test valid(unresolved)
    end

    source_schema = JSONSchema.Schema(JSON.parsefile(joinpath(@__DIR__, "../../bioir/proposals/bioir-m0.schema.json")))
    sources = filter(name -> endswith(name, ".json"), readdir(joinpath(examples_dir, "sources")))
    @test length(sources) == 8
    for name in sources
        @test JSONSchema.validate(source_schema, JSON.parsefile(joinpath(examples_dir, "sources", name))) === nothing
    end
    parameters = base["provenance"]["symbol_map"]["parameters"]
    for values in ([], parameters[1:1], [parameters[1], parameters[1]], vcat(parameters, parameters[1:1]))
        bad = deepcopy(base)
        bad["provenance"]["symbol_map"]["parameters"] = values
        @test !valid(bad)
    end
    for key in keys(parameters[1])
        bad = deepcopy(base)
        delete!(bad["provenance"]["symbol_map"]["parameters"][1], key)
        @test !valid(bad)
    end
    bad = deepcopy(base)
    delete!(bad["provenance"]["symbol_map"], "parameters")
    @test !valid(bad)
    reversed_map = deepcopy(base)
    reverse!(reversed_map["provenance"]["symbol_map"]["parameters"])
    @test valid(reversed_map)
    for labels in (Dict(), Dict("amount_x" => ""), Dict("amount_x" => "Molecules λ"), Dict("missing" => "Unresolved label"))
        candidate = deepcopy(base)
        candidate["provenance"]["display_labels"] = Dict("observables" => labels)
        @test valid(candidate)
    end
    for labels in (Dict("amount_x" => 1), Dict("invalid id" => "label"))
        bad = deepcopy(base)
        bad["provenance"]["display_labels"] = Dict("observables" => labels)
        @test !valid(bad)
    end
    bad = deepcopy(base)
    bad["model"]["observables"][1]["label"] = "Misplaced label"
    @test !valid(bad)
end
