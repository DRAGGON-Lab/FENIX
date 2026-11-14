using Test, JSON
include(joinpath(@__DIR__, "../review_oracle.jl"))
using .ProductionDecayOracle

@testset "Candidate mathematical oracle" begin
    catalog = load_catalog()
    report = make_report()
    expected_keys = Set((c["id"], s["time_bits"], p) for c in catalog["cases"]
                        for s in c["samples"] for p in (512, 1024))
    @test length(report["rows"]) == length(expected_keys)
    @test Set((r["case_id"], r["time_bits"], r["precision"]) for r in report["rows"]) == expected_keys
    @test report["implementation"] == "julia-bigfloat"
    for p in (512, 1024), case in catalog["cases"]
        a, b, x = [decode(case["parameters"][k]) for k in ("alpha", "beta", "x0")]
        @test evaluate(a, b, x, 0.0, p) == x
        values = [evaluate(a, b, x, decode(s["time_bits"]), p) for s in case["samples"]]
        @test all(v -> v >= 0, values)
        setprecision(BigFloat, p) do
            q = b == 0 ? nothing : BigFloat(a) / BigFloat(b)
            @test issorted(values; rev=(b > 0 && BigFloat(x) > q))
            if b > 0
                @test all(v -> min(BigFloat(x), q) <= v <= max(BigFloat(x), q), values)
            end
            for (s, value) in zip(case["samples"], values)
                @test decimal_string(value, 50) == s["expected"]
                if a == 0 && x == 0
                    @test iszero(value)
                end
                if b > 0 && a == b * x
                    @test value == x
                end
                if b == 0
                    @test value == x + a * decode(s["time_bits"])
                end
            end
        end
    end
    setprecision(BigFloat, 1024) do
        for t in (0.5, 1.0, 10.0)
            linear = BigFloat(0.5) + 2 * BigFloat(t)
            gaps = [linear - evaluate(2.0, b, 0.5, t, 1024) for b in (2.0^-20, 2.0^-40)]
            @test 0 < gaps[2] < gaps[1]
            for (gap, b) in zip(gaps, (2.0^-20, 2.0^-40))
                @test gap <= BigFloat(b) * (BigFloat(0.5) * t + BigFloat(t)^2)
            end
        end
        wrong = BigFloat(100) * -expm1(-parse(BigFloat, "0.1"))
        @test decimal_string(wrong, 50) != catalog["cases"][1]["samples"][2]["expected"]
    end
end

@testset "Decimal half-even publication" begin
    @test decimal_string(BigFloat(1.25), 2) == "1.2E+0"
    @test decimal_string(BigFloat(1.75), 2) == "1.8E+0"
    @test decimal_string(BigFloat(9.5), 1) == "1E+1"
    @test decimal_string(BigFloat(0), 50) == "0"
end

@testset "Reject corrupt candidate inputs" begin
    catalog = load_catalog()
    mutations = Any[]
    for bad in ("x", "000000000000000", "3FB999999999999A", "bff0000000000000",
                "7ff0000000000000", "7ff8000000000000"), field in ("alpha", "beta", "x0", "time")
        data = deepcopy(catalog)
        if field == "time"
            data["cases"][1]["samples"][1]["time_bits"] = bad
        else
            data["cases"][1]["parameters"][field] = bad
        end
        push!(mutations, data)
    end
    for bad in ("NaN", "-1", "1", "0.0", "1E+0", "1.234", "1e999999", 1)
        data = deepcopy(catalog); data["cases"][1]["samples"][1]["expected"] = bad
        push!(mutations, data)
    end
    data = deepcopy(catalog); data["units"]["alpha"] = "molecule/min"; push!(mutations, data)
    data = deepcopy(catalog); data["status"] = "APPROVED"; push!(mutations, data)
    data = deepcopy(catalog); push!(data["cases"], deepcopy(data["cases"][1])); push!(mutations, data)
    data = deepcopy(catalog); push!(data["cases"][1]["samples"], deepcopy(data["cases"][1]["samples"][1])); push!(mutations, data)
    data = deepcopy(catalog)
    duplicate_zero = deepcopy(data["cases"][1]["samples"][1])
    duplicate_zero["time_bits"] = "8000000000000000"
    push!(data["cases"][1]["samples"], duplicate_zero); push!(mutations, data)
    mktempdir() do tmp
        path = joinpath(tmp, "catalog.json")
        for data in mutations
            write(path, JSON.json(data))
            @test_throws ArgumentError load_catalog(path)
        end
        data = deepcopy(catalog)
        data["cases"][1]["samples"][1]["expected"] = "1." * "0"^49 * "E+0"
        write(path, JSON.json(data)); before = read(path)
        @test_throws ArgumentError make_report(path)
        @test read(path) == before
    end
end
