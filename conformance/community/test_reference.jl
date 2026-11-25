using Test
include("reference.jl")

report = JSON.parsefile(ARGS[1])
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
