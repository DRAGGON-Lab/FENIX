# Native source-linked capture/readback; fixed independent mathematical samples.
using Test, JSON, JSONSchema, SHA
using Fenix
const B = Fenix.BioIR
const F = Fenix.FIR
const E = Fenix.Execution
const R = Fenix.Results
const ROOT = normpath(joinpath(@__DIR__,"../../.."))
@test realpath(pathof(Fenix)) == realpath(joinpath(@__DIR__,"../src/Fenix.jl"))
sha(raw) = bytes2hex(sha256(raw))
bits(x) = string(reinterpret(UInt64,x);base=16,pad=16)
include("../test_native_fir/report_paths.jl")
const REPORT_PATH = isempty(ARGS) ? nothing : length(ARGS)==2 && ARGS[1]=="--report" ? report_destination(ARGS[2]) : error("Usage: runtests.jl [--report path]")
include("fixtures.jl")
include(joinpath(ROOT,"conformance/production_decay/review_oracle.jl"))
const O = ProductionDecayOracle
const ROWS = Any[]
const CONTROLS = Any[]

# Resolve approved schema IDs from explicitly supplied local documents only.
function local_schema(node,document,docs)
    if node isa AbstractDict
        if haskey(node,"\$ref")
            name,fragment = split(node["\$ref"],'#';limit=2)
            doc = isempty(name) ? document : docs[name]
            target = doc
            for part in split(fragment,'/')[2:end]
                target = target[part]
            end
            return local_schema(target,doc,docs)
        end
        return Dict(k=>local_schema(v,document,docs) for (k,v) in node if !(k in ("\$id","\$schema")))
    elseif node isa AbstractVector
        return [local_schema(v,document,docs) for v in node]
    end
    node
end
const SCHEMAS = let
    files = ("run-manifest-m0.schema.json","run-manifest-julia-sciml-m0.schema.json","ode-result-m0.schema.json")
    docs = Dict(name=>JSON.parsefile(joinpath(ROOT,"spec/results/proposals",name)) for name in files)
    by_id = Dict(d["\$id"]=>d for d in values(docs))
    Dict(name=>JSONSchema.Schema(local_schema(d,d,by_id)) for (name,d) in docs)
end
function invalid_record(manifest,result,experiment)
    caught = try R.from_json(R.RunRecord,manifest,result;experiment);nothing catch e;e end
    @test caught isa R.ResultValidationError
    if caught isa R.ResultValidationError
        @test startswith(caught.path,"/")
        @test !isempty(caught.category)
    end
end
function changed_record(m,r,experiment;manifest_change=identity,result_change=identity)
    manifest_change(m);result_change(r)
    bytes = Vector{UInt8}(codeunits(JSON.json(r)))
    m["output"]["sha256"] = sha(bytes)
    invalid_record(JSON.json(m),bytes,experiment)
end

@testset "All accepted Python/Julia examples retain original transport" begin
    for directory in (EXAMPLES,JULIA_EXAMPLES), name in EXAMPLE_NAMES
        experiment = example_experiment(name)
        mbytes = read(joinpath(directory,name*".manifest.json"))
        rbytes = read(joinpath(EXAMPLES,name*".result.json"))
        mcopy,rcopy = copy(mbytes),copy(rbytes)
        record = R.from_json(R.RunRecord,mbytes,rbytes;experiment,expected_manifest_sha256=sha(mbytes))
        @test R.to_json(record.manifest) == String(mcopy)
        @test record.result_bytes == rcopy
        @test sha(record.result_bytes) == R.to_dict(record.manifest)["output"]["sha256"]
        expected = JSON.parse(String(copy(rcopy)))
        @test isequal(R.to_dict(record.result),expected)
        empty!(mbytes);fill!(rbytes,0xff)
        @test record.result_bytes == rcopy
        output = record.result_bytes;empty!(output)
        @test record.result_bytes == rcopy
        exported = R.to_dict(record.manifest)
        exported["backend"]["environment"] = Dict("changed"=>"reader")
        @test R.to_dict(record.manifest)["backend"]["environment"] != exported["backend"]["environment"]
        # Hash whitespace as supplied; successful readback retains that spelling.
        text = R.to_json(record.manifest)*" \n"
        result_transport = vcat(rcopy,UInt8[0x20,0x0a])
        m = R.to_dict(record.manifest);m["output"]["sha256"] = sha(result_transport)
        formatted = " \n"*JSON.json(m;pretty=true)*"\n"
        reloaded = R.from_json(R.RunRecord,formatted,result_transport;experiment,expected_manifest_sha256=sha(codeunits(formatted)))
        @test R.to_json(reloaded.manifest) == formatted
        @test reloaded.result_bytes == result_transport
        @test_throws R.ResultValidationError R.from_json(R.RunRecord,text,rcopy;experiment,expected_manifest_sha256=sha(codeunits(R.to_json(record.manifest))))
        @test_throws R.ResultValidationError R.from_json(R.RunRecord,R.to_json(record.manifest),vcat(rcopy,UInt8[0x20]);experiment)
        push!(CONTROLS,Dict("profile"=>R.to_dict(record.manifest)["backend"]["profile"],"case"=>name,"status"=>"PASS","manifest_sha256"=>sha(mcopy),"result_sha256"=>sha(rcopy)))
    end
end

@testset "Closed records and cross-artifact rejections" begin
    for directory in (EXAMPLES,JULIA_EXAMPLES)
        experiment = example_experiment("late-first")
        record = R.from_json(R.RunRecord,read(joinpath(directory,"late-first.manifest.json")),read(joinpath(EXAMPLES,"late-first.result.json"));experiment)
        m,r = R.to_dict(record.manifest),R.to_dict(record.result)
        # Every nested object member is required; unknown fields never ignored.
        function closure_tests(node,path=String[])
            node isa AbstractDict || return
            for key in (collect(keys(node))...,"unexpected")
                changed = deepcopy(m);target=changed
                for part in path;target=target[part];end
                key=="unexpected" ? (target[key]=nothing) : delete!(target,key)
                invalid_record(JSON.json(changed),record.result_bytes,experiment)
            end
            for (key,child) in node;closure_tests(child,[path...,key]);end
        end
        closure_tests(m)
        for field in (collect(keys(r))...,"unexpected")
            changed = deepcopy(r)
            field=="unexpected" ? (changed[field]=nothing) : delete!(changed,field)
            changed_record(deepcopy(m),changed,experiment)
        end
        for (field,value) in (("state_ids",["wrong"]),("time_unit","min"),("state_units",["mol"]),
            ("observable_state_ids",["missing"]),("observable_units",["mol"]),("observable_ids",String[]),
            ("times",[1.0,10.0]),("state_values",[[1.0]]),("observable_values",[[1.0]]),
            ("fir_digest",repeat("0",64)),("state_values",[[-1.0],[1.0],[2.0]]))
            changed_record(deepcopy(m),deepcopy(r),experiment;result_change=x->(x[field]=value))
        end
        for path in (("sources","design","id"),("sources","design","revision"),("sources","design","schema_version"),("sources","design","digest"),
                     ("sources","experiment","id"),("sources","experiment","revision"),("sources","experiment","schema_version"),("sources","experiment","digest"))
            changed = deepcopy(m)
            changed[path[1]][path[2]][path[3]] = path[3]=="revision" ? 2 : path[3]=="digest" ? repeat("0",64) : "different"
            invalid_record(JSON.json(changed),record.result_bytes,experiment)
        end
        changed_record(deepcopy(m),deepcopy(r),experiment;manifest_change=x->(x["evaluations"]["nfev"]=x["execution"]["max_nfev"]+1))
        changed_record(deepcopy(m),deepcopy(r),experiment;manifest_change=x->(x["integration"]="skipped_zero_grid"))
        changed_record(deepcopy(m),deepcopy(r),experiment;manifest_change=x->(x["backend"]["profile"]="unsupported/0.1.0"))
        # Source changes that retain the exact mathematical FIR still reject.
        args = (; (key=>getfield(experiment.content,key) for key in fieldnames(B.ExperimentContent))...)
        content = B.ExperimentContent(; merge(args,(id="same_fir_other_context",source_design=experiment.source_design.content))...)
        same_fir = B.ExperimentDocument(content=content,source_design=experiment.source_design)
        @test Fenix.compile_experiment(same_fir).digest == Fenix.compile_experiment(experiment).digest
        invalid_record(R.to_json(record.manifest),record.result_bytes,same_fir)
        # Observations remain the writer's, including a valid non-null build ID.
        altered = deepcopy(m)
        altered["producer"] = Dict("name"=>"archived-producer","version"=>"past","build_id"=>"opaque:archived")
        for key in keys(altered["backend"]["environment"]);altered["backend"]["environment"][key]="past";end
        restored = R.from_json(R.RunRecord,JSON.json(altered),record.result_bytes;experiment)
        @test R.to_dict(restored.manifest)["producer"] == altered["producer"]
        @test R.to_dict(restored.manifest)["backend"]["environment"] == altered["backend"]["environment"]
    end
end

function source_experiment(d,a,b,x)
    functions = Dict(f.kind=>f for f in d.content.functions)
    content = B.ExperimentContent(id="results",revision=1,design=B.reference(d),source_design=d.content,
        parameters=[B.ParameterAssignment(parameter=functions[kind].parameter,quantity=B.Quantity(value=value,unit=unit)) for (kind,value,unit) in
            (("constitutive_production",a,"molecule/s"),("first_order_decay",b,"1/s"))],
        initial_counts=[B.InitialCount(species=only(d.content.species).id,quantity=B.Quantity(value=x,unit="molecule"))],
        observables=[B.Observable(id="amount",target=B.PortReference(species=only(d.content.species).id,port=only(only(d.content.species).ports).id))],interventions=())
    B.ExperimentDocument(content=content,source_design=d)
end
@testset "Capture matrix against all 40 independent analytical samples" begin
    catalog = O.load_catalog()
    @test catalog["status"] == "APPROVED"
    @test sum(length(c["samples"]) for c in catalog["cases"]) == 40
    d = B.from_json(B.DesignDocument,read(joinpath(ROOT,"spec/fir/proposals/examples/sources/gfp-design.json")))
    for method in ("Tsit5","Rodas5P"), (study,rtol,atol,max_step) in (("baseline",1e-10,1e-12,1.0),("refined",1e-11,1e-13,0.5))
        @testset "$method/$study/$(case["id"])" for case in catalog["cases"]
            a,b,x = [O.decode(case["parameters"][key]) for key in ("alpha","beta","x0")]
            experiment = source_experiment(d,a,b,x)
            fir = Fenix.compile_experiment(experiment)
            before = B.to_dict(experiment),F.to_dict(fir)
            samples = sort(case["samples"];by=s->O.decode(s["time_bits"]))
            grid = Tuple(O.decode(s["time_bits"]) for s in samples)
            spec = E.ODEExecutionSpec(time_grid=grid,method=method,rtol=rtol,atol=atol,max_step=max_step,max_nfev=100000)
            record = R.run_experiment(experiment,spec)
            manifest,result = R.to_dict(record.manifest),R.to_dict(record.result)
            @test JSONSchema.validate(SCHEMAS["run-manifest-julia-sciml-m0.schema.json"],manifest) === nothing
            @test JSONSchema.validate(SCHEMAS["ode-result-m0.schema.json"],result) === nothing
            @test (B.to_dict(experiment),F.to_dict(fir)) == before
            @test manifest["fir"]["digest"] == result["fir_digest"] == fir.digest
            loaded = R.from_json(R.RunRecord,R.to_json(record.manifest),record.result_bytes;experiment)
            @test isequal(R.to_dict(loaded.result),result)
            @test loaded.result_bytes == record.result_bytes
            @test result["times"] == collect(grid)
            @test manifest["producer"]["name"] == "Fenix"
            @test manifest["producer"]["version"] == string(pkgversion(Fenix))
            @test manifest["producer"]["build_id"] === nothing
            @test manifest["backend"]["solver"]["method"] == method
            @test manifest["backend"]["solver"]["options"]["maxiters"] == typemax(Int)
            for (i,sample) in enumerate(samples)
                actual = result["state_values"][i][1]
                error,bound = setprecision(BigFloat,512) do
                    expected = parse(BigFloat,sample["expected"])
                    abs(BigFloat(actual)-expected),parse(BigFloat,"1e-9")+parse(BigFloat,"1e-8")*abs(expected)
                end
                @test error <= bound
                @test bits(actual) == bits(R.to_dict(loaded.result)["state_values"][i][1])
                @test bits(actual) == bits(result["observable_values"][i][1])
                push!(ROWS,Dict("case"=>case["id"],"method"=>method,"study"=>study,"time_bits"=>sample["time_bits"],
                    "actual_bits"=>bits(actual),"absolute_error_molecule"=>string(error),"fraction_of_acceptance_bound"=>string(error/bound),
                    "fir_digest"=>fir.digest,"nfev"=>manifest["evaluations"]["nfev"],"njev"=>manifest["backend"]["evaluations"]["njev"],
                    "nw"=>manifest["backend"]["evaluations"]["nw"],"manifest_sha256"=>sha(codeunits(R.to_json(record.manifest))),
                    "result_sha256"=>sha(record.result_bytes),"status"=>"PASS"))
            end
        end
    end
end
@testset "Capture interfaces including late, zero-only and empty observables" begin
    for method in ("Tsit5","Rodas5P"), name in EXAMPLE_NAMES
        experiment = example_experiment(name)
        grid = name in ("zero-only","empty-observables") ? (-0.0,) : (1.0,10.0)
        spec = E.ODEExecutionSpec(time_grid=grid,method=method,rtol=1e-10,atol=1e-12,max_step=1.0,max_nfev=100000)
        record = R.run_experiment(experiment,spec)
        m,r=R.to_dict(record.manifest),R.to_dict(record.result)
        @test isequal(r["times"],collect(grid))
        @test r["observable_ids"] == (name=="multi-observables" ? ["a_amount","m_amount","z_amount"] : name=="empty-observables" ? String[] : ["amount_x"])
        @test m["integration"] == (last(grid)==0 ? "skipped_zero_grid" : "performed")
        @test all(length(row)==length(r["observable_ids"]) for row in r["observable_values"])
        @test isequal(R.to_dict(R.from_json(R.RunRecord,R.to_json(record.manifest),record.result_bytes;experiment).result),r)
    end
end
@testset "Readback cannot execute either backend" begin
    run(`$(Base.julia_cmd()) --project=$(dirname(Base.active_project())) $(joinpath(@__DIR__,"readback_trap.jl"))`)
    @test true
end
if REPORT_PATH !== nothing
    fingerprints(paths) = Dict(p=>sha(read(joinpath(ROOT,p))) for p in paths)
    report = Dict("implementation"=>"native-julia-source-linked-results","passed"=>true,
        "runtime"=>merge(Dict(E._backend_versions()),Dict("JSON"=>string(pkgversion(JSON)),"Fenix"=>string(pkgversion(Fenix)))),
        "platform"=>Dict("kernel"=>string(Sys.KERNEL),"architecture"=>string(Sys.ARCH),"julia_threads"=>Threads.nthreads()),
        "rows"=>ROWS,"examples"=>CONTROLS,"analytical_sample_method_setting_comparisons"=>length(ROWS),
        "acceptance"=>Dict("absolute_molecule"=>"1e-9","relative"=>"1e-8"),
        "dependency_fingerprints"=>fingerprints(["conformance/julia_ode/Project.toml","conformance/julia_ode/Manifest.toml","conformance/julia/Manifest.toml"]),
        "source_fingerprints"=>fingerprints(["packages/julia/src/Results.jl","packages/julia/src/PortableJSON.jl","packages/julia/src/Execution.jl","packages/julia/src/Fenix.jl","packages/julia/Project.toml"]),
        "evaluator_fingerprints"=>fingerprints(["packages/julia/test_native_results/runtests.jl","packages/julia/test_native_results/fixtures.jl","packages/julia/test_native_results/readback_trap.jl","packages/julia/test_native_fir/report_paths.jl","conformance/production_decay/review_oracle.jl"]),
        "catalog_fingerprints"=>fingerprints(["conformance/production_decay/catalog.json","spec/results/proposals/examples/checksums.json","spec/results/proposals/julia-examples/checksums.json"]),
        "contract_fingerprints"=>fingerprints(["spec/results/proposals/ADR-P07.md","spec/results/proposals/ADR-P07-Julia.md","spec/results/proposals/run-manifest-m0.schema.json","spec/results/proposals/run-manifest-julia-sciml-m0.schema.json","spec/results/proposals/ode-result-m0.schema.json"]),
        "limits"=>"Bounded source/schema/transport/analytical verification; not authenticated execution, biological validation, #29 acceptance or human implementation acceptance.")
    mkpath(dirname(REPORT_PATH));write(REPORT_PATH,JSON.json(report;pretty=true)*"\n")
end
