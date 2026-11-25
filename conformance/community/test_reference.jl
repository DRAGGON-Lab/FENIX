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
