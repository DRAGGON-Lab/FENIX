# Independent BigFloat analytical evaluator. No native FENIX imports.
using JSON, SHA

function samples(bits)
    setprecision(BigFloat, bits) do
        output = Dict{String,Any}[]
        for n in 1:4, time in (0, 1, 4)
            y = 4 * (-expm1(-BigFloat(time) / 2))
            push!(output, Dict("case" => "threshold-n$n", "time" => time,
                              "state" => BigFloat[4, 12, 24, y]))
        end
        for time in (0, 1, 4)
            # Derive E first from E' = 72-(5/2)E, then recover s from mass.
            e = BigFloat(24) + BigFloat(24)/5 * (-expm1(-BigFloat(5)*time/2))
            s = (BigFloat(36)-e)/3
            push!(output, Dict("case" => "reversible-transient", "time" => time,
                              "state" => BigFloat[s, 2, e, 0]))
        end
        for n in 1:4, time in (0, 1, 4)
            beta = BigFloat(n)/2
            amplitude = BigFloat(2)^n
            decay = exp(-beta*time)
            # Integrating factor: beta*t+log1p(A*exp(-beta*t))-log1p(A).
            integral = beta*time + log1p(amplitude*decay) - log1p(amplitude)
            reporter = 2*decay - expm1(-beta*time)/beta + 4*amplitude*decay*integral/beta
            push!(output, Dict("case" => "driven-n$n", "time" => time,
                              "state" => BigFloat[0, 0, 48*exp(-BigFloat(time)/2), reporter]))
        end
        for time in (0, 1, 4)
            # Environment approaches the common equilibrium density 36/11.
            e = BigFloat(24) + BigFloat(168)/11 * (-expm1(-BigFloat(11)*time/4))
            density = (108-e)/21
            push!(output, Dict("case" => "two-strain-transient", "time" => time,
                              "state" => BigFloat[2*density, 3*density, e, 0]))
        end
        output
    end
end

function validate_catalog_metadata(data)
    expected = Dict(
        "state_ids" => ["sender.signal", "receiver.signal", "env.signal", "receiver.reporter"],
        "time_unit" => "s", "volumes_unit" => "L", "state_unit" => "molecule",
        "parameter_units" => Dict(
            "sender_production" => "molecule/s", "sender_decay" => "1/s",
            "receiver_decay" => "1/s", "env_decay" => "1/s", "reporter_decay" => "1/s",
            "reporter_basal" => "molecule/s", "reporter_induced" => "molecule/s",
            "sender_export" => "1/s", "sender_import" => "1/s",
            "receiver_export" => "1/s", "receiver_import" => "1/s",
            "threshold" => "molecule/L", "hill_n" => "1"))
    for (field, value) in expected
        @assert get(data, field, nothing) == value "catalog metadata differs from ADR-P08: $field"
    end
end

function compare_report(report; catalog_path=joinpath(@__DIR__, "cases.json"))
    validate_catalog_metadata(JSON.parsefile(catalog_path))
    low, high = samples(512), samples(1024)
    setprecision(BigFloat, 1024) do
        @assert length(low) == length(high) == 30
        for (a, b) in zip(low, high)
            @assert all(abs(x-y) <= big"1e-140"*max(1, abs(y))
                        for (x, y) in zip(a["state"], b["state"]))
        end
        @assert Set(keys(report)) == Set(["status", "samples", "max_refinement_error", "catalog_sha256"])
        @assert report["status"] == "PROPOSED"
        @assert report["catalog_sha256"] == bytes2hex(sha256(read(catalog_path)))
        refinement = parse(BigFloat, report["max_refinement_error"])
        @assert isfinite(refinement) && 0 <= refinement <= big"1e-70"
        @assert length(report["samples"]) == length(high)
        for (a, b) in zip(report["samples"], high)
            @assert Set(keys(a)) == Set(["case", "time", "state"])
            @assert a["case"] == b["case"]
            @assert typeof(a["time"]) === Int && a["time"] == b["time"]
            @assert length(a["state"]) == length(b["state"]) == 4
            actual = parse.(BigFloat, a["state"])
            @assert all(x -> isfinite(x) && x >= 0, actual)
            @assert all(abs(x-y) <= big"1e-150"*max(1, abs(y))
                        for (x,y) in zip(actual, b["state"]))
        end
    end
end

if abspath(PROGRAM_FILE) == @__FILE__
    compare_report(JSON.parsefile(ARGS[1]))
    println("PASS: 30 analytical samples, Julia 512/1024-bit refinement and Python agreement")
end
