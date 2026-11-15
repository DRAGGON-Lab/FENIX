include("p01.jl")
using .P01Reference, JSON, JSONSchema, SHA

function run_catalog()
    directory = normpath(joinpath(@__DIR__, "../bioir"))
    raw = read(joinpath(directory, "catalog.json"))
    catalog = JSON.parse(String(copy(raw)))
    catalog_schema = JSONSchema.Schema(JSON.parsefile(joinpath(directory, "catalog.schema.json")))
    JSONSchema.validate(catalog_schema, catalog) === nothing || error("Invalid catalog structure")
    length(Set(c["id"] for c in catalog["cases"])) == length(catalog["cases"]) || error("Duplicate catalog IDs")
    results = Any[]
    for case in catalog["cases"]
        bytes2hex(sha256(read(joinpath(directory, case["input"])))) == case["input_sha256"] || error("Fixture input checksum mismatch")
        expected = case["expected"]
        checks = true
        observed = try
            value = evaluate(case, directory)
            if haskey(expected, "value")
                checks = value == expected["value"]
                if expected["value"] isa Bool
                    checks = checks && value isa Bool
                end
            end
            if haskey(expected, "binary64_bits")
                checks = string(reinterpret(UInt64, Float64(value)); base=16, pad=16) == expected["binary64_bits"]
            end
            result = Dict("outcome" => "accept")
            if haskey(expected, "canonical_utf8")
                result["canonical_utf8"] = P01Reference.canonical(value)
                checks = checks && result["canonical_utf8"] == expected["canonical_utf8"]
            end
            result
        catch error
            error isa Rejection || rethrow()
            Dict("outcome" => "reject", "category" => error.category, "path" => error.path)
        end
        passed = checks && all(get(observed, key, nothing) == value for (key, value) in expected if key in ("outcome", "category", "path"))
        push!(results, Dict("id" => case["id"], "passed" => passed, "observed" => observed))
    end
    Dict("catalog_sha256" => bytes2hex(sha256(raw)), "runtime" => string(VERSION), "catalog_version" => catalog["catalog_version"], "fixture_status" => catalog["status"],
         "implementation" => "independent-julia-reference", "passed" => all(r["passed"] for r in results), "cases" => results)
end

report = run_catalog()
if isempty(ARGS)
    println(JSON.json(report; pretty=true))
elseif length(ARGS) == 2 && ARGS[1] == "--report"
    mkpath(dirname(ARGS[2]))
    write(ARGS[2], JSON.json(report; pretty=true) * "\n")
else
    error("Usage: run_p01.jl [--report path]")
end
println(stderr, "$(length(report["cases"])) P01 reference cases; fixture_status=$(report["fixture_status"]); passed=$(report["passed"])")
exit(report["passed"] ? 0 : 1)
