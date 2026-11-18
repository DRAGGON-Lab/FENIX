# Native Julia committed-source -> compiler -> solver evidence for P04/#29.
# Expected bytes are supplied by the independent, external-serializer manifest.
using Fenix, JSON, SHA, Pkg
using Fenix.Execution
const B = Fenix.BioIR
const F = Fenix.FIR
const ROOT = normpath(joinpath(@__DIR__, "../.."))
sha(raw) = bytes2hex(sha256(raw))
blob(raw) = Dict("hex"=>bytes2hex(raw), "sha256"=>sha(raw))
bits(value::Float64) = string(reinterpret(UInt64,value);base=16,pad=16)
decode(word) = reinterpret(Float64,parse(UInt64,word;base=16))
include(joinpath(ROOT,"packages/julia/test_native_fir/report_paths.jl"))
function ode_fingerprints()
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
        "conformance/canonicalization/catalog.json","conformance/canonicalization/catalog.schema.json",
        "conformance/production_decay/catalog.json","conformance/production_decay/catalog.schema.json"))
    isfile(joinpath(ROOT,".github/workflows/native-ode.yml")) && push!(paths,".github/workflows/native-ode.yml")
    Dict(p=>sha(read(joinpath(ROOT,p))) for p in paths)
end
function source_experiment(design,scenario;wrong_unit=false)
    functions = Dict(f.kind=>f for f in design.content.functions)
    parameters = scenario["parameters"]
    content = B.ExperimentContent(id="ode_"*scenario["id"],revision=1,design=B.reference(design),source_design=design.content,
        parameters=[B.ParameterAssignment(parameter=functions[kind].parameter,quantity=B.Quantity(value=decode(parameters[key]),unit=unit)) for (kind,key,unit) in
            (("constitutive_production","alpha",wrong_unit ? "1/s" : "molecule/s"),("first_order_decay","beta","1/s"))],
        initial_counts=[B.InitialCount(species=only(design.content.species).id,quantity=B.Quantity(value=decode(parameters["x0"]),unit="molecule"))],
        observables=[B.Observable(id="amount",target=B.PortReference(species=only(design.content.species).id,port=only(only(design.content.species).ports).id))],interventions=())
    B.ExperimentDocument(content=content,source_design=design)
end
function actual_artifacts(design,experiment,compiled)
    identity = F.identity_bytes(compiled.model)
    sha(identity) == compiled.digest || error("Native FIR digest does not match actual identity bytes")
    Dict("design"=>blob(B.canonical_content_bytes(design)),"experiment"=>blob(B.canonical_content_bytes(experiment)),
         "model"=>blob(F.canonical_model_bytes(compiled.model)),"identity"=>blob(identity))
end
function check_bytes(label,expected,actual)
    for name in ("design","experiment","model","identity")
        want,got = expected[name],actual[name]
        raw = hex2bytes(want["hex"])
        sha(raw) == want["sha256"] || error("$label/$name: reference blob hash mismatch")
        if want != got
            observed = hex2bytes(got["hex"])
            offset = something(findfirst(i->raw[i]!=observed[i],1:min(length(raw),length(observed))),min(length(raw),length(observed))+1)-1
            lo,hi = max(1,offset-15),offset+17
            error("$label/$name: expected sha256=$(want["sha256"]), actual sha256=$(got["sha256"]); first differing byte=$offset; expected context=$(bytes2hex(raw[lo:min(hi,length(raw))])); actual context=$(bytes2hex(observed[lo:min(hi,length(observed))]))")
        end
    end
end
function settings(values,grid,method;changes...)
    ODEExecutionSpec(;merge((time_grid=grid,method=method,rtol=decode(values["rtol_bits"]),atol=decode(values["atol_bits"]),
        max_step=decode(values["max_step_bits"]),max_nfev=values["max_nfev"]),(;changes...))...)
end
function control(work,id,method)
    try
        work()
        Dict("id"=>id,"method"=>method,"outcome"=>"accept","category"=>"","path"=>"","nfev"=>0)
    catch err
        err isa Union{B.BioIRValidationError,F.FIRValidationError,ExecutionValidationError,ODEExecutionError} || rethrow()
        Dict("id"=>id,"method"=>method,"outcome"=>"reject","category"=>err.category,
            "path"=>hasproperty(err,:path) ? err.path : "","nfev"=>hasproperty(err,:nfev) ? err.nfev : 0)
    end
end
function produce(manifest,revision)
    realpath(pathof(Fenix)) == realpath(joinpath(ROOT,"packages/julia/src/Fenix.jl")) || error("Installed Fenix differs from fingerprinted checkout")
    manifest["format"] == "native-ode-references-v1" || error("Unknown reference format")
    manifest["source_revision"] == revision || error("Stale reference source revision")
    fingerprints = ode_fingerprints()
    manifest["fingerprints"] == fingerprints || error("Stale reference fingerprints")
    length(manifest["scenarios"]) == 10 || error("Expected ten approved scenarios")
    catalog = JSON.parsefile(joinpath(ROOT,"conformance/production_decay/catalog.json"))
    catalog["status"] == "APPROVED" || error("Approved catalog required")
    approved = Dict(c["id"]=>c for c in catalog["cases"])
    ids = [s["id"] for s in manifest["scenarios"]]
    length(Set(ids)) == length(ids) && Set(ids) == Set(keys(approved)) || error("Reference scenario coverage mismatch")
    for scenario in manifest["scenarios"]
        case = approved[scenario["id"]]
        scenario["parameters"] == case["parameters"] || error("Reference parameters differ from approved catalog")
        scenario["samples"] == sort(case["samples"];by=s->decode(s["time_bits"])) || error("Reference samples differ from approved catalog")
    end
    expected_studies = Dict(name=>Dict("rtol_bits"=>bits(r),"atol_bits"=>bits(a),"max_step_bits"=>bits(step),"max_nfev"=>100000)
        for (name,r,a,step) in (("baseline",1e-10,1e-12,1.0),("refined",1e-11,1e-13,0.5),("coarse",1e-9,1e-11,2.0)))
    manifest["studies"] == expected_studies || error("Reference settings differ from P04 matrix")
    design = B.from_json(B.DesignDocument,read(joinpath(ROOT,"spec/fir/proposals/examples/sources/gfp-design.json")))
    scenarios,runs,controls,failures = Any[],Any[],Any[],Any[]
    for scenario in manifest["scenarios"]
        experiment = source_experiment(design,scenario)
        design.digest == scenario["artifacts"]["design"]["sha256"] || error("Native Design digest mismatch")
        experiment.digest == scenario["artifacts"]["experiment"]["sha256"] || error("Native Experiment digest mismatch")
        compiled = Fenix.compile_experiment(experiment)
        F.validate_sources(compiled;design=design,experiment=experiment)
        artifacts = actual_artifacts(design,experiment,compiled)
        check_bytes(scenario["id"],scenario["artifacts"],artifacts)
        model = F.to_dict(compiled.model)
        parameters = Dict(p["id"]=>p for p in model["parameters"])
        for key in ("alpha","beta")
            bits(parameters[key]["value"]) == scenario["parameters"][key] || error("Parameter bit mismatch")
        end
        bits(only(model["states"])["initial"]) == scenario["parameters"]["x0"] || error("Initial bit mismatch")
        grid = Tuple(decode(s["time_bits"]) for s in scenario["samples"])
        for method in ("Tsit5","Rodas5P"), study in ("coarse","baseline","refined")
            values = manifest["studies"][study]
            spec = settings(values,grid,method)
            trajectory = try
                solve_ode(compiled.model,spec)
            catch err
                err isa ODEExecutionError || rethrow()
                push!(failures,Dict("case_id"=>scenario["id"],"method"=>method,"study"=>study,"category"=>err.category,"message"=>sprint(showerror,err),"nfev"=>err.nfev))
                continue
            end
            trajectory.spec === spec || error("Trajectory execution settings mismatch")
            expected_versions = Dict("julia"=>string(VERSION),"SciMLBase"=>string(pkgversion(Fenix.Execution.SciMLBase)),
                "OrdinaryDiffEqTsit5"=>string(pkgversion(Fenix.Execution.OrdinaryDiffEqTsit5)),
                "OrdinaryDiffEqRosenbrock"=>string(pkgversion(Fenix.Execution.OrdinaryDiffEqRosenbrock)))
            Dict(trajectory.backend_versions) == expected_versions || error("Trajectory backend version mismatch")
            trajectory.fir_digest == compiled.digest || error("Trajectory FIR identity mismatch")
            trajectory.state_ids == ("x",) && trajectory.state_units == ("molecule",) && trajectory.time_unit == "s" || error("Invalid trajectory state metadata")
            trajectory.observable_ids == ("amount",) && trajectory.observable_units == ("molecule",) || error("Invalid trajectory observable metadata")
            samples = [Dict("time_bits"=>bits(trajectory.times[i]),"state_bits"=>bits(trajectory.state_values[i][1]),
                "observable_bits"=>bits(trajectory.observable_values[i][1])) for i in eachindex(trajectory.times)]
            check_bytes(scenario["id"],artifacts,actual_artifacts(design,experiment,compiled))
            push!(runs,Dict("case_id"=>scenario["id"],"method"=>method,"study"=>study,"settings"=>values,"samples"=>samples,
                "diagnostics"=>Dict("nfev"=>trajectory.nfev,"njev"=>trajectory.njev,"nw"=>trajectory.nw),"fir_digest"=>trajectory.fir_digest,
                "state_ids"=>collect(trajectory.state_ids),"state_units"=>collect(trajectory.state_units),
                "observable_ids"=>collect(trajectory.observable_ids),"observable_units"=>collect(trajectory.observable_units),"time_unit"=>trajectory.time_unit))
        end
        push!(scenarios,Dict("id"=>scenario["id"],"artifacts"=>artifacts,"after_artifacts"=>actual_artifacts(design,experiment,compiled)))
    end
    scenario = first(manifest["scenarios"])
    experiment = source_experiment(design,scenario)
    compiled = Fenix.compile_experiment(experiment)
    values = manifest["studies"]["baseline"]
    for method in ("Tsit5","Rodas5P")
        push!(controls,control(()->source_experiment(design,scenario;wrong_unit=true),"unit-rejection",method))
        push!(controls,control(()->solve_ode(compiled.model,settings(values,(0.0,),method;profile="ssa")),"unsupported-profile",method))
        push!(controls,control(()->solve_ode(compiled.model,settings(values,(0.0,1.0),method;max_nfev=1)),"work-limit",method))
    end
    dependencies = Dict(info.name=>string(info.version) for info in Base.values(Pkg.dependencies()) if info.version !== nothing)
    Dict("format"=>"native-ode-report-v1","implementation"=>"julia","source_revision"=>revision,"fingerprints"=>fingerprints,
        "runtime"=>Dict("name"=>"Julia","version"=>string(VERSION),"os"=>string(Sys.KERNEL),"arch"=>string(Sys.ARCH),"dependencies"=>dependencies),
        "scenarios"=>scenarios,"runs"=>runs,"controls"=>controls,"failures"=>failures)
end
function main()
    length(ARGS) == 6 || error("Usage: run_ode.jl --references path --report path --source-revision sha")
    options = Dict(ARGS[i]=>ARGS[i+1] for i in 1:2:6)
    Set(keys(options)) == Set(("--references","--report","--source-revision")) || error("Unknown arguments")
    occursin(r"^[0-9a-f]{40}$",options["--source-revision"]) || error("Expected full source revision")
    destination = report_destination(options["--report"])
    # Native parser rejects duplicate keys and malformed/nonfinite JSON inputs.
    raw = read(options["--references"])
    B.parse_json(raw;numeric_policy=:p03) # lexical checks, including duplicate keys
    manifest = JSON.parse(String(raw)) # retain integer execution-budget tokens
    report = produce(manifest,options["--source-revision"])
    mkpath(dirname(destination));write(destination,JSON.json(report;pretty=true)*"\n")
    println("Produced Julia ODE report: $(length(report["runs"])) runs; independent comparator required")
    isempty(report["failures"]) || exit(1)
end
if abspath(PROGRAM_FILE) == abspath(@__FILE__)
    main()
end
