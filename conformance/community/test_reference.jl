using Test
include("reference.jl")

report = JSON.parsefile(ARGS[1])
@testset "Catalog metadata remains normative with a recomputed hash" begin
    original = JSON.parsefile(joinpath(@__DIR__, "cases.json"))
    mutations = Function[
        c -> reverse!(c["state_ids"]),
        c -> pop!(c["state_ids"]),
        c -> (c["time_unit"] = "min"),
        c -> (c["volumes_unit"] = "mL"),
        c -> (c["state_unit"] = "mol"),
        c -> pop!(c["parameter_units"], "hill_n"),
        c -> (c["parameter_units"]["unknown"] = "1"),
    ]
    for parameter in keys(original["parameter_units"])
        push!(mutations, c -> (c["parameter_units"][parameter] = "incorrect"))
    end
    for field in ("state_ids", "time_unit", "volumes_unit", "state_unit", "parameter_units")
        push!(mutations, c -> pop!(c, field))
    end
    mktemp() do path, io
        # Reserialization changes the hash while preserving the contract metadata.
        write(path, JSON.json(original))
        current = deepcopy(report)
        current["catalog_sha256"] = bytes2hex(sha256(read(path)))
        @test compare_report(current; catalog_path=path) === nothing
        for mutation in mutations
            candidate = deepcopy(original)
            mutation(candidate)
            write(path, JSON.json(candidate))
            current = deepcopy(report)
            current["catalog_sha256"] = bytes2hex(sha256(read(path)))
            @test_throws AssertionError compare_report(current; catalog_path=path)
        end
    end
end

# Traverse the supplied fixture, not the validator's expected definitions.
function catalog_mutations(value, path=Any[])
    mutations = Function[]
    at(c, p) = foldl((node, key) -> node[key], p; init=c)
    if value isa AbstractDict
        for (key, child) in value
            push!(mutations, c -> delete!(at(c, path), key))
            append!(mutations, catalog_mutations(child, [path; key]))
        end
        push!(mutations, c -> (at(c, path)["unknown"] = 0))
    elseif value isa AbstractVector
        push!(mutations, c -> pop!(at(c, path)))
        push!(mutations, c -> push!(at(c, path), deepcopy(at(c, path)[1])))
        push!(mutations, c -> reverse!(at(c, path)))
        for (i, child) in enumerate(value)
            append!(mutations, catalog_mutations(child, [path; i]))
        end
    else
        replacements = value isa Real ? Any[value + 1, true] : Any["wrong"]
        if value isa Real && (path[end] == "hill_n" || path[end-1] in ("populations", "times"))
            push!(replacements, Float64(value))
        end
        for replacement in replacements
            push!(mutations, c -> (at(c, path[1:end-1])[path[end]] = replacement))
        end
    end
    mutations
end

@testset "Complete catalog remains fixed with freshly recomputed hashes" begin
    original = JSON.parsefile(joinpath(@__DIR__, "cases.json"))
    mutations = catalog_mutations(original)
    append!(mutations, Function[
        c -> (c["cases"][1]["populations"] = [4, 5]),
        c -> begin
            c["cases"][1]["parameters"]["sender_export"] *= 2
            c["cases"][1]["parameters"]["sender_import"] *= 2
        end,
        c -> (c["cases"][6]["volumes"][1] *= 2),
    ])
    mktemp() do path, io
        for mutation in mutations
            candidate = deepcopy(original)
            mutation(candidate)
            # Some leaf replacements or reversals preserve a value.
            JSON.json(candidate) == JSON.json(original) && continue
            write(path, JSON.json(candidate))
            current = deepcopy(report)
            current["catalog_sha256"] = bytes2hex(sha256(read(path)))
            @test_throws AssertionError compare_report(current; catalog_path=path)
        end
        # Object member order and equivalent real-number spellings are immaterial.
        function reordered_json(value)
            if value isa AbstractDict
                members = [JSON.json(key) * ":" * reordered_json(value[key])
                           for key in reverse(collect(keys(value)))]
                return "{" * join(members, ",") * "}"
            elseif value isa AbstractVector
                return "[" * join(reordered_json.(value), ",") * "]"
            end
            JSON.json(value)
        end
        reordered = deepcopy(original)
        reordered["cases"][1]["initial"][1] = 4.0
        raw = reordered_json(reordered)
        write(path, raw)
        current = deepcopy(report)
        current["catalog_sha256"] = bytes2hex(sha256(read(path)))
        @test compare_report(current; catalog_path=path) === nothing
    end
end

@testset "Independent report completeness and corruption" begin
    @test compare_report(report) === nothing
    for mutation in (
        r -> pop!(r["samples"]),
        r -> pop!(r["samples"][1]["state"]),
        r -> (r["samples"][1]["state"] = String[]),
        r -> (r["samples"][1]["state"][1] = "NaN"),
        r -> (r["samples"][1]["state"][1] = "-1"),
        r -> (r["samples"][1]["state"][1] = "5"),
        r -> (r["samples"][2]["time"] = true),
        r -> (r["catalog_sha256"] = "stale"),
        r -> (r["max_refinement_error"] = "NaN"),
    )
        candidate = deepcopy(report)
        mutation(candidate)
        @test_throws AssertionError compare_report(candidate)
    end
end
