using Test, JSON, SHA
include("reference.jl")
using .P09References

report = JSON.parsefile(only(ARGS))
@testset "P09 independent analytical candidates" begin
    @test P09References.compare_report(report) === nothing
    for action in ("missing", "duplicate", "reordered", "short", "wrong", "nan", "negative", "boolean_time", "extra", "digest", "precision", "residual")
        changed = deepcopy(report)
        if action == "missing"
            pop!(changed["samples"])
        elseif action == "duplicate"
            push!(changed["samples"], deepcopy(changed["samples"][end]))
        elseif action == "reordered"
            reverse!(changed["samples"])
        elseif action == "short"
            pop!(changed["samples"][1]["state"])
        elseif action == "wrong"
            changed["samples"][2]["state"][1] = "2"
        elseif action == "nan"
            changed["samples"][1]["state"][1] = "NaN"
        elseif action == "negative"
            changed["samples"][1]["state"][1] = "-1"
        elseif action == "boolean_time"
            changed["samples"][1]["time"] = false
        elseif action == "extra"
            changed["unrecognized"] = 1
        elseif action == "digest"
            changed["catalog_sha256"] = repeat("0", 64)
        elseif action == "precision"
            changed["max_precision_error"] = "1e-10"
        else
            changed["max_ode_residual"] = "1e-10"
        end
        @test_throws AssertionError P09References.compare_report(changed)
    end
    # All catalog bytes are bound before trusting even a freshly recomputed hash.
    original = JSON.parsefile(joinpath(@__DIR__, "cases.json"))
    for action in ("population", "rate", "volume", "missing", "extra", "boolean", "reordered")
        changed = deepcopy(original)
        if action == "population"
            changed["cases"][10]["populations"][1] += 1 # zero net flux: samples unchanged
        elseif action == "rate"
            changed["cases"][10]["parameters"]["export"][1][1] *= 2
            changed["cases"][10]["parameters"]["import"][1][1] *= 2
        elseif action == "volume"
            changed["cases"][5]["medium_volume_L"] += 1 # disconnected medium
        elseif action == "missing"
            pop!(changed["cases"])
        elseif action == "extra"
            changed["unrecognized"] = 1
        elseif action == "boolean"
            changed["cases"][1]["parameters"]["basal"][1] = true
        else
            reverse!(changed["cases"])
        end
        mktemp() do path, io
            write(io, JSON.json(changed)); close(io)
            fresh = deepcopy(report)
            fresh["catalog_sha256"] = bytes2hex(sha256(read(path)))
            @test_throws AssertionError P09References.compare_report(fresh; catalog_path=path)
        end
    end
end
