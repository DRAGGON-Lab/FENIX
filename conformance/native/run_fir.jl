# Installed native package, via conformance/julia_ode's pinned Pkg environment.
# No LOAD_PATH override, Python invocation, or native expectation generation.
using Fenix, JSON, SHA, Pkg
const B = Fenix.BioIR
const F = Fenix.FIR
const ROOT = normpath(joinpath(@__DIR__, "../.."))
sha(raw) = bytes2hex(sha256(raw))
blob(raw) = Dict("hex"=>bytes2hex(raw), "sha256"=>sha(raw))
load(path) = JSON.parsefile(joinpath(ROOT,path))
function artifact(item; prefix="")
    raw = read(joinpath(ROOT,prefix * item["path"]))
    sha(raw) == item["sha256"] || error("Artifact checksum mismatch: " * item["path"])
    raw
end
function sources(case,catalog)
    catalog in ("rejections","producer") && return case["inputs"]
    Dict(k=>Dict("path"=>"conformance/canonicalization/" * case[k]["path"],"sha256"=>case[k]["sha256"])
        for k in ("input","normalized","canonical","model_canonical") if haskey(case,k))
end
function model_artifacts(model)
    identity = F.identity_bytes(model)
    sha(identity) == model.digest || error("Native digest differs from native identity bytes")
    Dict("model"=>blob(F.canonical_model_bytes(model)),"identity"=>blob(identity))
end
function fingerprints()
    paths = Set{String}()
    for (folder,extensions) in (("packages/python/src",(".py",)),("packages/julia/src",(".jl",)),
        ("conformance/native",(".py",".jl",".json")),("spec",(".json",)))
        for (dir,_,files) in walkdir(joinpath(ROOT,folder)), file in files
            (any(endswith(file,ext) for ext in extensions) || (folder == "spec" && startswith(file,"ADR-") && endswith(file,".md"))) && push!(paths,relpath(joinpath(dir,file),ROOT))
        end
    end
    union!(paths,("packages/python/pyproject.toml","packages/python/uv.lock","packages/julia/Project.toml",
        "packages/julia/test_native_fir/report_paths.jl",".github/workflows/native-fir.yml",
        "conformance/julia_ode/Project.toml","conformance/julia_ode/Manifest.toml",
        "conformance/rejections/catalog.json","conformance/rejections/catalog.schema.json",
        "conformance/canonicalization/catalog.json","conformance/canonicalization/catalog.schema.json"))
    Dict(p=>sha(read(joinpath(ROOT,p))) for p in paths)
end
function produce(revision)
    realpath(pathof(Fenix)) == realpath(joinpath(ROOT,"packages/julia/src/Fenix.jl")) || error("Installed Fenix does not resolve to fingerprinted checkout sources")
    rows = Any[]
    for case in load("conformance/rejections/catalog.json")["cases"]
        label = "primary"
        deps = Dict{String,Any}()
        observed = try
            for key in ("design","experiment","previous")
                if haskey(case["inputs"],key)
                    label = key
                    raw = artifact(case["inputs"][key])
                    deps[key] = key == "experiment" ? B.from_json(B.ExperimentDocument,raw;designs=(deps["design"],)) : B.from_json(B.DesignDocument,raw)
                end
            end
            label = "primary"
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
                    label = "request"
                    request = B.parse_json(artifact(case["inputs"]["request"]);numeric_policy=:p03)
                    F.require_capability(doc.model,request["profile"])
                end
            end
            Dict("outcome"=>"accept")
        catch err
            err isa Union{B.BioIRValidationError,F.FIRValidationError} || rethrow()
            Dict("outcome"=>"reject","category"=>err.category,"path"=>err.path,"document"=>label)
        end
        push!(rows,Dict("catalog"=>"rejections","id"=>case["id"],"sources"=>sources(case,"rejections"),"observed"=>observed,"artifacts"=>Dict()))
        if case["operation"] == "producer" && case["expected"]["outcome"] == "accept"
            compiled = Fenix.compile_experiment(deps["experiment"])
            F.validate_sources(compiled;design=deps["design"],experiment=deps["experiment"])
            push!(rows,Dict("catalog"=>"producer","id"=>case["id"],"sources"=>sources(case,"producer"),"observed"=>Dict("outcome"=>"accept"),"artifacts"=>model_artifacts(compiled.model)))
        end
    end
    for case in load("conformance/canonicalization/catalog.json")["cases"]
        artifacts = Dict{String,Any}()
        observed = try
            raw = artifact(case["input"];prefix="conformance/canonicalization/")
            stage = case["stage"]
            if stage == "contract_only"
                startswith(case["id"],"fir-") ? F.from_json(F.FIRDocument,raw) : B.parse_json(raw;numeric_policy=:p03)
            elseif stage == "fir_identity"
                artifacts = model_artifacts(F.from_json(F.FIRDocument,raw).model)
            else
                value = stage == "binary64_jcs" ? reinterpret(Float64,parse(UInt64,case["binary64_bits"];base=16)) : B.parse_json(raw;numeric_policy=:p03)
                artifacts["canonical"] = blob(B.canonical_bytes(value))
            end
            Dict("outcome"=>"accept")
        catch err
            err isa Union{B.BioIRValidationError,F.FIRValidationError,ArgumentError} || rethrow()
            Dict("outcome"=>"reject")
        end
        push!(rows,Dict("catalog"=>"canonicalization","id"=>case["id"],"sources"=>sources(case,"canonicalization"),"observed"=>observed,"artifacts"=>artifacts))
    end
    dependencies = Dict(info.name=>string(info.version) for info in values(Pkg.dependencies()) if info.version !== nothing)
    Dict("report_version"=>1,"implementation"=>"julia","source_revision"=>revision,
         "runtime"=>Dict("name"=>"Julia","version"=>string(VERSION),"os"=>string(Sys.KERNEL),"arch"=>string(Sys.ARCH),"dependencies"=>dependencies),
         "fingerprints"=>fingerprints(),"cases"=>rows)
end
include(joinpath(ROOT,"packages/julia/test_native_fir/report_paths.jl"))
function main()
    length(ARGS) == 4 || error("Usage: run_fir.jl --report path --source-revision sha")
    options = Dict(ARGS[i]=>ARGS[i+1] for i in 1:2:4)
    Set(keys(options)) == Set(("--report","--source-revision")) || error("Unknown arguments")
    occursin(r"^[0-9a-f]{40}$",options["--source-revision"]) || error("Expected full source revision")
    destination = report_destination(options["--report"])
    report = produce(options["--source-revision"])
    mkpath(dirname(destination))
    write(destination,JSON.json(report;pretty=true)*"\n")
    println("Produced native Julia report (300 cases); independent validation required by compare_fir.py")
end
main()
