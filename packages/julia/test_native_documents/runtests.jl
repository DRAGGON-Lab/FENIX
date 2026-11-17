# Native document conformance against unchanged independent reference expectations.
using Test, JSON, JSONSchema, SHA
pushfirst!(LOAD_PATH, normpath(joinpath(@__DIR__, "..")))
using Fenix.BioIR
using Fenix
const ROOT = normpath(joinpath(@__DIR__, "../../.."))
@test realpath(pathof(Fenix)) == realpath(joinpath(@__DIR__, "../src/Fenix.jl"))
const ROWS = Any[]
function input(path, digest=nothing)
    raw = read(joinpath(ROOT, path))
    digest === nothing || @test bytes2hex(sha256(raw)) == digest
    raw
end
function failure_row(id, expected, work; label=Ref("primary"), legacy=false)
    observed = try
        work()
        Dict("outcome" => "accept")
    catch error
        error isa BioIRValidationError || rethrow()
        Dict("outcome" => "reject", "category" => error.category,
             "path" => error.path, "document" => label[])
    end
    @test observed["outcome"] == expected["outcome"]
    if expected["outcome"] == "reject" && observed["outcome"] == "reject"
        @test observed["category"] == expected["category"]
        if haskey(expected, "path")
            path = legacy && expected["category"] == "SCHEMA" && expected["path"] == "" ? "" : observed["path"]
            @test path == expected["path"]
        end
        haskey(expected, "document") && @test observed["document"] == expected["document"]
    end
    push!(ROWS, Dict("id" => id, "observed" => observed))
end

@testset "Native Julia P01 documents" begin
    catalog = JSON.parsefile(joinpath(ROOT,"conformance/bioir/catalog.json"))
    rejection = JSON.parsefile(joinpath(ROOT,"conformance/rejections/catalog.json"))
    @test catalog["status"] == rejection["status"] == "APPROVED"
    @test length(catalog["cases"]) == 92
    diagnostics = Dict(c["id"] => c for c in rejection["cases"])
    @testset "Original 92 — $(case["id"])" for case in catalog["cases"]
        expected = case["expected"]
        failure_row(case["id"], expected, () -> begin
            raw = input("conformance/bioir/" * case["input"], case["input_sha256"])
            op = case["operation"]
            if op in ("parse", "canonical")
                value = parse_json(raw)
                if haskey(expected,"value")
                    @test value == expected["value"]
                    expected["value"] isa Bool && @test value isa Bool
                end
                if haskey(expected,"binary64_bits")
                    @test string(reinterpret(UInt64,Float64(value));base=16,pad=16) == expected["binary64_bits"]
                end
                op == "canonical" && @test String(canonical_bytes(value)) == expected["canonical_utf8"]
            elseif op == "experiment"
                dep = diagnostics["p01-" * case["id"]]["inputs"]["design"]
                design = from_json(DesignDocument,input("conformance/bioir/" * case["design"],dep["sha256"]))
                from_json(ExperimentDocument,raw;designs=(design,))
            else
                previous = nothing
                if op == "revision"
                    dep = diagnostics["p01-" * case["id"]]["inputs"]["previous"]
                    previous = from_json(DesignDocument,input("conformance/bioir/" * case["previous"],dep["sha256"]))
                end
                from_json(DesignDocument,raw;previous)
            end
        end;legacy=true)
    end
    cases = filter(c -> c["contract"] == "P01", rejection["cases"])
    @test length(cases) == 97
    @test length(rejection["cases"]) - length(cases) == 110
    @testset "Rejection P01 subset — $(case["id"])" for case in cases
        label = Ref("primary")
        failure_row(case["id"],case["expected"], () -> begin
            deps = Dict{String,Any}()
            for key in ("design","previous")
                if haskey(case["inputs"],key)
                    label[] = key
                    item = case["inputs"][key]
                    deps[key] = from_json(DesignDocument,input(item["path"],item["sha256"]))
                end
            end
            label[] = "primary"
            item = case["inputs"]["primary"]
            raw = input(item["path"],item["sha256"])
            if case["operation"] == "parse"
                parse_json(raw)
            elseif case["operation"] == "experiment"
                from_json(ExperimentDocument,raw;designs=(deps["design"],))
            else
                from_json(DesignDocument,raw;previous=get(deps,"previous",nothing))
            end
        end;label)
    end
    @testset "Schema and transport" begin
        validator = JSONSchema.Schema(JSON.parsefile(joinpath(ROOT,"spec/bioir/proposals/bioir-m0.schema.json")))
        d = from_json(DesignDocument,input("conformance/bioir/inputs/design-valid.input"))
        e = from_json(ExperimentDocument,input("conformance/bioir/inputs/experiment-valid.input");designs=(d,))
        for doc in (d,e)
            @test JSONSchema.validate(validator,to_dict(doc)) === nothing
            @test JSON.parse(to_json(doc)) == to_dict(doc)
        end
    end
end
@testset "Approved binary64 JCS serialization only" begin
    catalog = JSON.parsefile(joinpath(ROOT,"conformance/canonicalization/catalog.json"))
    @test catalog["status"] == "APPROVED"
    cases = filter(c -> c["stage"] == "binary64_jcs", catalog["cases"])
    @test length(cases) == 27
    @testset "$(case["id"])" for case in cases
        value = reinterpret(Float64,parse(UInt64,case["binary64_bits"];base=16))
        if case["expected_outcome"] == "accept"
            expected = case["canonical"]
            bytes = input("conformance/canonicalization/" * expected["path"],expected["sha256"])
            @test canonical_bytes(value) == bytes
        else
            @test_throws BioIRValidationError canonical_bytes(value)
        end
    end
end
if length(ARGS) == 2 && ARGS[1] == "--report"
    path = ARGS[2]
    mkpath(dirname(path))
    write(path,JSON.json(Dict("implementation"=>"native-julia-documents","runtime"=>string(VERSION),"passed"=>true,
        "catalogs"=>Dict(p=>bytes2hex(sha256(input(p))) for p in ("conformance/bioir/catalog.json","conformance/rejections/catalog.json","conformance/canonicalization/catalog.json")),
        "scope"=>"92 original P01 + 97 rejection P01 rows; overlapping cases", "cases"=>ROWS);pretty=true))
elseif !isempty(ARGS)
    error("Usage: runtests.jl [--report path]")
end
