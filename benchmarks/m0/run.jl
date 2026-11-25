# One native case/method per process. Measurements are observations, not targets.
const ROOT = normpath(joinpath(@__DIR__, "../.."))
const LOAD_STARTED = time_ns()
include(joinpath(ROOT, "examples/m0/production_decay.jl"))
using Fenix
const PACKAGE_LOAD_SECONDS = (time_ns()-LOAD_STARTED)/1e9
using JSON, SHA, Statistics
using Pkg

# Bounded references copied from the unchanged APPROVED production-decay catalog.
const EXPECTED = Dict(
    "baseline-five" => ["5.0000000000000000000000000000000000000000000000000E+0",
        "1.4040445286583840498309275603109457596127989442110E+1",
        "6.5051453088712977879485320987896138779345130140148E+1",
        "9.9995687006672558390635208165519821728469934817363E+1"],
    "linear-production" => ["0.5", "1.5", "2.5", "20.5"])

function validate_values(case, values)
    length(values)==length(EXPECTED[case]) || error("incomplete sampled output")
    setprecision(BigFloat, 384) do
        for (actual, expected) in zip(values,EXPECTED[case])
            isfinite(actual) && actual >= 0 || error("nonfinite or negative output")
            reference = parse(BigFloat,expected)
            bound = parse(BigFloat,"1e-9") + parse(BigFloat,"1e-8")*abs(reference)
            abs(BigFloat(actual)-reference) <= bound || error("sample exceeds approved P04 bound")
        end
    end
end
function summary(samples)
    !isempty(samples) && all(x->isfinite(x)&&x>=0,samples) || error("invalid timing observations")
    Dict("seconds"=>samples,"median"=>median(samples),"min"=>minimum(samples),"max"=>maximum(samples))
end
function fingerprints()
    paths = ["packages/python/uv.lock", "conformance/julia_ode/Project.toml",
        "conformance/julia_ode/Manifest.toml","conformance/production_decay/catalog.json"]
    for directory in ("packages/python/src","packages/julia/src","examples/m0","benchmarks/m0")
        for (root, _, files) in walkdir(joinpath(ROOT,directory)), file in files
            splitext(file)[2] in (".py",".jl") && push!(paths,relpath(joinpath(root,file),ROOT))
        end
    end
    Dict(path=>bytes2hex(sha256(read(joinpath(ROOT,path)))) for path in sort(paths))
end
function timed(operation)
    start=time_ns()
    value=operation()
    value,(time_ns()-start)/1e9
end
function main(args)
    iseven(length(args)) || error("arguments require --name value pairs")
    options=Dict(args[i]=>args[i+1] for i in 1:2:length(args))
    all(k->k in ("--case","--method","--output","--source-revision","--warmups","--repeats"),keys(options)) || error("unknown argument")
    case=options["--case"]; method=options["--method"]; revision=options["--source-revision"]
    occursin(r"^[0-9a-f]{40}$",revision) || error("require full lowercase revision SHA")
    haskey(EXPECTED,case) || error("unsupported case")
    method in ("Tsit5","Rodas5P") || error("unsupported method")
    warmups=parse(Int,get(options,"--warmups","3")); repeats=parse(Int,get(options,"--repeats","20"))
    warmups>=0 && repeats>0 || error("invalid repetition counts")
    experiment=M0Example.build_experiment(case)
    spec=M0Example.execution_settings(case,method)
    compiled,first_compile=timed(()->Fenix.compile_experiment(experiment))
    check_compiled(value) = Fenix.FIR.identity_bytes(value.model)==Fenix.FIR.identity_bytes(compiled.model) || error("FIR changed")
    function check_trajectory(value)
        value.times==spec.time_grid || error("incorrect sampling times")
        validate_values(case,[row[1] for row in value.state_values])
    end
    function check_record(value)
        loaded=Fenix.Results.from_json(Fenix.Results.RunRecord,Fenix.Results.to_json(value.manifest),value.result_bytes;experiment)
        loaded.result_bytes==value.result_bytes || error("readback changed result bytes")
        check_trajectory(value.result)
    end
    operations=("compile"=>(() -> Fenix.compile_experiment(experiment),check_compiled),
        "solve"=>(() -> Fenix.Execution.solve_ode(compiled.model,spec),check_trajectory),
        "capture"=>(() -> Fenix.Results.run_experiment(experiment,spec),check_record))
    first=Dict("compile"=>first_compile); timings=Dict{String,Any}()
    for (name,(operation,check)) in operations
        if name!="compile"
            value,duration=timed(operation);first[name]=duration;check(value)
        end
        for _ in 1:warmups
            check(operation())
        end
        samples=Float64[]
        for _ in 1:repeats
            value,duration=timed(operation);push!(samples,duration);check(value)
        end
        timings[name]=summary(samples)
    end
    dependencies=Dict(info.name=>string(info.version) for info in values(Pkg.dependencies()) if info.version!==nothing)
    report=Dict("format"=>"m0-benchmark-v1","language"=>"julia","case"=>case,"method"=>method,
        "source_revision"=>revision,"settings"=>Dict(string(k)=>getproperty(spec,k) for k in (:time_grid,:rtol,:atol,:max_step,:max_nfev)),
        "warmups"=>warmups,"repeats"=>repeats,"package_load_seconds"=>PACKAGE_LOAD_SECONDS,
        "first_seconds"=>first,"timings"=>timings,"runtime"=>Dict("language_version"=>string(VERSION),"dependencies"=>dependencies),
        "hardware"=>Dict("os"=>string(Sys.KERNEL," ",Sys.MACHINE),"machine"=>string(Sys.ARCH),
            "cpu"=>string(Sys.cpu_info()),"logical_cpus"=>Sys.CPU_THREADS,
            "threads"=>Dict(k=>get(ENV,k,"unset") for k in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","JULIA_NUM_THREADS")),
            "julia_threads"=>Threads.nthreads(),"runner_image"=>Dict(k=>get(ENV,k,"local") for k in ("ImageOS","ImageVersion"))),
        "fingerprints"=>fingerprints(),"identities"=>Dict("design"=>experiment.source_design.digest,"experiment"=>experiment.digest,"fir"=>compiled.digest),
        "package_path"=>pathof(Fenix),"validation"=>"PASS")
    output=options["--output"];mkpath(dirname(abspath(output)))
    open(output,"w") do io
        JSON.print(io,report,2);println(io)
    end
    println("PASS: $case/$method, $repeats validated repetitions per phase")
end
if abspath(PROGRAM_FILE) == @__FILE__
    main(ARGS)
end
