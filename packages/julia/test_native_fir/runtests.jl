# Native APIs only; unchanged approved artifacts supply all expectations.
using Test, JSON, JSONSchema, SHA
pushfirst!(LOAD_PATH, normpath(joinpath(@__DIR__, "..")))
using Fenix
const B = Fenix.BioIR
const F = Fenix.FIR
const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const ROWS = Any[]
@test realpath(pathof(Fenix)) == realpath(joinpath(@__DIR__, "../src/Fenix.jl"))
sha(raw) = bytes2hex(sha256(raw))
include("report_paths.jl")
const REPORT_PATH = if isempty(ARGS)
    nothing
elseif length(ARGS) == 2 && ARGS[1] == "--report"
    report_destination(ARGS[2])
else
    error("Usage: runtests.jl [--report path]")
end
include("test_report_paths.jl")
function artifact(path, checksum=nothing)
    raw = read(joinpath(ROOT, path))
    checksum === nothing || @test sha(raw) == checksum
    raw
end
artifact(item::AbstractDict; prefix="") = artifact(prefix * item["path"], item["sha256"])
function observe(work)
    try
        work()
        Dict("outcome"=>"accept")
    catch error
        error isa Union{B.BioIRValidationError,F.FIRValidationError} || rethrow()
        Dict("outcome"=>"reject", "category"=>error.category, "path"=>error.path)
    end
end
function sources(case)
    d = B.from_json(B.DesignDocument, artifact(case["inputs"]["design"]))
    e = B.from_json(B.ExperimentDocument, artifact(case["inputs"]["experiment"]); designs=(d,))
    d,e
end
@testset "All 207 approved rejection catalog cases" begin
    catalog = JSON.parsefile(joinpath(ROOT,"conformance/rejections/catalog.json"))
    @test catalog["status"] == "APPROVED"
    @test length(catalog["cases"]) == 207
    @testset "$(case["id"])" for case in catalog["cases"]
        label = Ref("primary")
        observed = observe() do
            deps = Dict{String,Any}()
            for key in ("design","experiment","previous")
                if haskey(case["inputs"],key)
                    label[] = key
                    raw = artifact(case["inputs"][key])
                    deps[key] = key == "experiment" ? B.from_json(B.ExperimentDocument,raw;designs=(deps["design"],)) : B.from_json(B.DesignDocument,raw)
                end
            end
            label[] = "primary"
            raw = artifact(case["inputs"]["primary"])
            op = case["operation"]
            if op == "parse"
                B.parse_json(raw;numeric_policy=Symbol(lowercase(case["contract"])))
            elseif op == "experiment"
                B.from_json(B.ExperimentDocument,raw;designs=(deps["design"],))
            elseif op in ("design","revision")
                B.from_json(B.DesignDocument,raw;previous=get(deps,"previous",nothing))
            elseif op == "producer"
                F.from_json(F.FIRDocument,raw;design=deps["design"],experiment=deps["experiment"])
            else
                doc = F.from_json(F.FIRDocument,raw)
                if op == "capability"
                    label[] = "request"
                    request = B.parse_json(artifact(case["inputs"]["request"]);numeric_policy=:p03)
                    F.require_capability(doc.model,request["profile"])
                end
            end
        end
        observed["outcome"] == "reject" && (observed["document"] = label[])
        @test observed == Dict(k=>v for (k,v) in case["expected"] if k != "stage")
        push!(ROWS,Dict("catalog"=>"rejections","id"=>case["id"],"observed"=>observed))
    end
end
@testset "All 84 approved P03 canonicalization cases" begin
    prefix = "conformance/canonicalization/"
    catalog = JSON.parsefile(joinpath(ROOT,prefix,"catalog.json"))
    @test catalog["status"] == "APPROVED"
    @test length(catalog["cases"]) == 84
    @testset "$(case["id"])" for case in catalog["cases"]
        raw = artifact(case["input"];prefix)
        outcome = observe() do
            stage = case["stage"]
            if stage == "contract_only"
                startswith(case["id"],"fir-") ? F.from_json(F.FIRDocument,raw) : B.parse_json(raw;numeric_policy=:p03)
            elseif stage == "fir_identity"
                model = F.from_json(F.FIRDocument,raw).model
                normalized = F.normalized(model)
                @test F.to_dict(normalized) == B.parse_json(artifact(case["normalized"];prefix);numeric_policy=:p03)
                @test F.to_dict(F.normalized(normalized)) == F.to_dict(normalized)
                @test F.canonical_model_bytes(model) == artifact(case["model_canonical"];prefix)
                @test F.identity_bytes(model) == artifact(case["canonical"];prefix)
                @test model.digest == case["canonical"]["sha256"]
                @test F.from_json(F.FIRModel,F.canonical_model_bytes(model)).digest == model.digest
                @test F.from_json(F.FIRModel,F.to_json(model)).digest == model.digest
            else
                value = stage == "binary64_jcs" ? reinterpret(Float64,parse(UInt64,case["binary64_bits"];base=16)) : B.parse_json(raw;numeric_policy=:p03)
                output = B.canonical_bytes(value)
                @test output == artifact(case["canonical"];prefix)
                haskey(case,"canonical_sha256") && @test sha(output) == case["canonical_sha256"]
            end
        end
        @test outcome["outcome"] == case["expected_outcome"]
        push!(ROWS,Dict("catalog"=>"canonicalization","id"=>case["id"],"observed"=>outcome))
    end
end
@testset "Nine approved producer controls compiled natively" begin
    catalog = JSON.parsefile(joinpath(ROOT,"conformance/rejections/catalog.json"))
    controls = filter(c -> c["operation"] == "producer" && c["expected"]["outcome"] == "accept",catalog["cases"])
    @test length(controls) == 9
    schema = JSONSchema.Schema(JSON.parsefile(joinpath(ROOT,"spec/fir/proposals/fir-m0.schema.json")))
    @testset "$(case["id"])" for case in controls
        d,e = sources(case)
        expected = F.from_json(F.FIRDocument,artifact(case["inputs"]["primary"]);design=d,experiment=e)
        actual = Fenix.compile_experiment(e)
        @test JSONSchema.validate(schema,F.to_dict(actual)) === nothing
        @test F.to_dict(F.normalized(actual.model)) == F.to_dict(F.normalized(expected.model))
        @test F.identity_bytes(actual) == F.identity_bytes(expected)
        @test actual.digest == expected.digest
        F.validate_sources(actual;design=d,experiment=e)
        push!(ROWS,Dict("catalog"=>"producer","id"=>case["id"],"observed"=>Dict("outcome"=>"accept"),"digest"=>actual.digest))
    end
end
include("oracle.jl")
if REPORT_PATH !== nothing
    source_paths = [relpath(joinpath(dir,file),ROOT) for (dir,_,files) in walkdir(joinpath(ROOT,"packages/julia/src")) for file in files if endswith(file,".jl")]
    catalogs = ["conformance/$name/catalog.json" for name in ("rejections","canonicalization","production_decay")]
    report = Dict("implementation"=>"native-julia-fir","runtime"=>Dict("julia"=>string(VERSION),"mpfr"=>string(Base.MPFR.version())),
        "passed"=>true,"fixture_status"=>"APPROVED","source_fingerprints"=>Dict(p=>sha(artifact(p)) for p in source_paths),
        "catalog_fingerprints"=>Dict(p=>sha(artifact(p)) for p in catalogs),
        "evaluator_fingerprints"=>Dict(p=>sha(artifact(p)) for p in
            ("packages/julia/test_native_fir/runtests.jl","packages/julia/test_native_fir/oracle.jl","packages/julia/test_native_fir/report_paths.jl","packages/julia/test_native_fir/test_report_paths.jl","conformance/production_decay/review_oracle.jl")),
        "dependency_fingerprints"=>Dict(p=>sha(artifact(p)) for p in
            ("packages/julia/Project.toml","conformance/julia/Project.toml","conformance/julia/Manifest.toml")),
        "contract_fingerprints"=>Dict(p=>sha(artifact(p)) for p in
            ("spec/bioir/proposals/ADR-P01.md","spec/fir/proposals/ADR-P02.md","spec/canonicalization/proposals/ADR-P03.md")),
        "cases"=>ROWS)
    mkpath(dirname(REPORT_PATH))
    write(REPORT_PATH,JSON.json(report;pretty=true)*"\n")
end
