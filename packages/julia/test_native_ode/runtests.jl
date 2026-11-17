# Fixed approved references, independent BigFloat comparisons, native APIs only.
using Test, JSON, SHA
pushfirst!(LOAD_PATH,normpath(joinpath(@__DIR__,"..")))
using Fenix
using Fenix.Execution
const B = Fenix.BioIR
const F = Fenix.FIR
const ROOT = normpath(joinpath(@__DIR__,"../../.."))
sha(raw) = bytes2hex(sha256(raw))
include("../test_native_fir/report_paths.jl")
const REPORT_PATH = isempty(ARGS) ? nothing : length(ARGS)==2 && ARGS[1]=="--report" ? report_destination(ARGS[2]) : error("Usage: runtests.jl [--report path]")
include(joinpath(ROOT,"conformance/production_decay/review_oracle.jl"))
const O = ProductionDecayOracle
const ROWS = Any[]
function source_experiment(d,a,b,x)
    functions = Dict(f.kind=>f for f in d.content.functions)
    content = B.ExperimentContent(id="ode",revision=1,design=B.reference(d),source_design=d.content,
        parameters=[B.ParameterAssignment(parameter=functions[kind].parameter,quantity=B.Quantity(value=value,unit=unit)) for (kind,value,unit) in
            (("constitutive_production",a,"molecule/s"),("first_order_decay",b,"1/s"))],
        initial_counts=[B.InitialCount(species=only(d.content.species).id,quantity=B.Quantity(value=x,unit="molecule"))],
        observables=[B.Observable(id="amount",target=B.PortReference(species=only(d.content.species).id,port=only(only(d.content.species).ports).id))],interventions=())
    B.ExperimentDocument(content=content,source_design=d)
end
function error_row(actual,expected)
    setprecision(BigFloat,512) do
        reference = parse(BigFloat,expected)
        error = abs(BigFloat(actual)-reference)
        bound = parse(BigFloat,"1e-9")+parse(BigFloat,"1e-8")*abs(reference)
        @test error <= bound
        (absolute_error=string(error),scaled_error=string(error/bound))
    end
end
@testset "Native SciML P04 approved reference and refinement matrix" begin
    catalog = O.load_catalog()
    @test catalog["status"]=="APPROVED"
    @test length(catalog["cases"])==10
    @test sum(length(c["samples"]) for c in catalog["cases"])==40
    d = B.from_json(B.DesignDocument,read(joinpath(ROOT,"spec/fir/proposals/examples/sources/gfp-design.json")))
    for method in ("Tsit5","Rodas5P"), (name,rtol,atol,max_step) in (("coarse",1e-9,1e-11,2.0),("baseline",1e-10,1e-12,1.0),("refined",1e-11,1e-13,0.5))
        @testset "$method/$name/$(case["id"])" for case in catalog["cases"]
            a,b,x = [O.decode(case["parameters"][k]) for k in ("alpha","beta","x0")]
            compiled = Fenix.compile_experiment(source_experiment(d,a,b,x))
            before = F.to_dict(compiled)
            samples = sort(case["samples"];by=s->O.decode(s["time_bits"]))
            grid = Tuple(O.decode(s["time_bits"]) for s in samples)
            spec = ODEExecutionSpec(time_grid=grid,method=method,rtol=rtol,atol=atol,max_step=max_step,max_nfev=100000)
            trajectory = solve_ode(compiled.model,spec)
            @test trajectory.times==grid
            @test F.to_dict(compiled)==before
            for (i,sample) in enumerate(samples)
                errors = error_row(trajectory.state_values[i][1],sample["expected"])
                @test trajectory.observable_values[i][1] == trajectory.state_values[i][1]
                push!(ROWS,Dict("case"=>case["id"],"method"=>method,"study"=>name,"time_bits"=>sample["time_bits"],
                    "actual_bits"=>string(reinterpret(UInt64,trajectory.state_values[i][1]);base=16,pad=16),
                    "absolute_error_molecule"=>errors.absolute_error,"fraction_of_acceptance_bound"=>errors.scaled_error,
                    "nfev"=>trajectory.nfev,"njev"=>trajectory.njev,"nw"=>trajectory.nw,
                    "fir_digest"=>trajectory.fir_digest,"rtol"=>rtol,"atol"=>atol,"max_step_s"=>max_step,"max_nfev"=>100000,"status"=>"PASS"))
            end
        end
    end
end
@testset "Stiff exploratory control, independent law not a golden fixture" begin
    d=B.from_json(B.DesignDocument,read(joinpath(ROOT,"spec/fir/proposals/examples/sources/gfp-design.json")))
    model=Fenix.compile_experiment(source_experiment(d,2e6,1e6,5.0)).model
    grid=(0.0,1e-6,1e-4,1.0)
    spec=ODEExecutionSpec(time_grid=grid,method="Rodas5P",rtol=1e-10,atol=1e-12,max_step=1.0,max_nfev=100000)
    trajectory=solve_ode(model,spec)
    for (row,time) in zip(trajectory.state_values,grid)
        expected=O.evaluate(2e6,1e6,5.0,time,512)
        error_row(row[1],string(expected))
    end
    explicit=ODEExecutionSpec(time_grid=grid,method="Tsit5",rtol=1e-10,atol=1e-12,max_step=1.0,max_nfev=2000)
    caught=try solve_ode(model,explicit);nothing catch error;error end
    @test caught isa ODEExecutionError
    @test caught.category=="WORK_LIMIT"
    @test caught.nfev==2000
end
if REPORT_PATH !== nothing
    fingerprints(paths)=Dict(p=>sha(read(joinpath(ROOT,p))) for p in paths)
    report=Dict("implementation"=>"native-julia-sciml-ode","passed"=>true,"runtime"=>Dict(Fenix.Execution._backend_versions()),
        "platform"=>Dict("kernel"=>string(Sys.KERNEL),"architecture"=>string(Sys.ARCH),"julia_threads"=>Threads.nthreads()),
        "dependency_fingerprints"=>fingerprints(["conformance/julia_ode/Project.toml","conformance/julia_ode/Manifest.toml"]),
        "rows"=>ROWS,"acceptance"=>Dict("absolute_molecule"=>"1e-9","relative"=>"1e-8"),
        "catalog_fingerprints"=>fingerprints(["conformance/production_decay/catalog.json"]),
        "source_fingerprints"=>fingerprints(["packages/julia/src/Execution.jl","packages/julia/src/FIR.jl","packages/julia/src/Compiler.jl","packages/julia/src/Fenix.jl","packages/julia/Project.toml"]),
        "evaluator_fingerprints"=>fingerprints(["packages/julia/test_native_ode/runtests.jl","packages/julia/test_native_fir/report_paths.jl","conformance/production_decay/review_oracle.jl"]),
        "contract_fingerprints"=>fingerprints(["spec/execution/proposals/ADR-P04.md","spec/fir/proposals/ADR-P02.md"]))
    mkpath(dirname(REPORT_PATH));write(REPORT_PATH,JSON.json(report;pretty=true)*"\n")
end
