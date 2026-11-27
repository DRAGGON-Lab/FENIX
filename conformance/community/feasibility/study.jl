# PROPOSED independent P08 method-stage investigation. No native FENIX imports.
# The active pinned conformance environment already contains these dependencies;
# load their explicit package identities without importing the Fenix package.
using JSON, SHA, UUIDs, Test
const SciML = Base.require(Base.PkgId(UUID("0bca4576-84f4-4d90-8ffe-ffa030f20462"), "SciMLBase"))
const Tsit = Base.require(Base.PkgId(UUID("b1df2697-797e-41e3-8120-5422d3b24e4a"), "OrdinaryDiffEqTsit5"))
const Rosen = Base.require(Base.PkgId(UUID("43230ef6-c299-4910-a778-202eb28ce4ce"), "OrdinaryDiffEqRosenbrock"))
include(joinpath(@__DIR__, "..", "reference.jl"))

struct ProbeFailure <: Exception
    category::String
    time::Float64
    environment::Float64
end

function kernel(case, budget)
    p = case["parameters"]
    ns, nr = case["populations"]
    vs, vr, ve = Float64.(case["volumes"])
    calls, jac_calls, minimum_e = Ref(0), Ref(0), Ref(Inf)
    function domain(u, t)
        all(isfinite, u) || throw(ProbeFailure("NONFINITE_STAGE", t, u[3]))
        minimum_e[] = min(minimum_e[], u[3])
        u[3] >= 0 || throw(ProbeFailure("STAGE_DOMAIN", t, u[3]))
    end
    function hill(e)
        e == 0 && return 0.0
        ratio = (e / ve) / p["threshold"]
        ratio <= 1 ? ratio^p["hill_n"] / (1 + ratio^p["hill_n"]) :
                     1 / (1 + (1 / ratio)^p["hill_n"])
    end
    function rhs!(du, u, _, t)
        calls[] < budget || throw(ProbeFailure("WORK_LIMIT", t, u[3]))
        calls[] += 1
        domain(u, t)
        s, r, e, y = u
        outward_s = p["sender_export"] * s
        outward_r = p["receiver_export"] * r
        inward_s = p["sender_import"] * vs * e / ve
        inward_r = p["receiver_import"] * vr * e / ve
        du[1] = p["sender_production"] - p["sender_decay"] * s + inward_s - outward_s
        du[2] = inward_r - outward_r - p["receiver_decay"] * r
        du[3] = ns * outward_s + nr * outward_r - ns * inward_s - nr * inward_r - p["env_decay"] * e
        du[4] = p["reporter_basal"] + p["reporter_induced"] * hill(e) - p["reporter_decay"] * y
        all(isfinite, du) || throw(ProbeFailure("NONFINITE_RHS", t, e))
        nothing
    end
    function jac!(matrix, u, _, t)
        jac_calls[] += 1
        domain(u, t)
        fill!(matrix, 0.0)
        matrix[1,1] = -p["sender_decay"] - p["sender_export"]
        matrix[2,2] = -p["receiver_decay"] - p["receiver_export"]
        matrix[1,3] = p["sender_import"] * vs / ve
        matrix[2,3] = p["receiver_import"] * vr / ve
        matrix[3,1] = ns * p["sender_export"]
        matrix[3,2] = nr * p["receiver_export"]
        matrix[3,3] = -ns * matrix[1,3] - nr * matrix[2,3] - p["env_decay"]
        e = u[3]
        h = hill(e)
        slope = e == 0 ? (p["hill_n"] == 1 ? 1 / (p["threshold"] * ve) : 0.0) :
                        p["hill_n"] * h * (1 - h) / e
        matrix[4,3] = p["reporter_induced"] * slope
        matrix[4,4] = -p["reporter_decay"]
        all(isfinite, matrix) || throw(ProbeFailure("NONFINITE_JACOBIAN", t, e))
        nothing
    end
    function time_gradient!(gradient, u, _, t)
        domain(u, t)
        fill!(gradient, 0.0)
        nothing
    end
    (; rhs!, jac!, time_gradient!, calls, jac_calls, minimum_e)
end

function integrate(case, method, controls, cap, budget)
    k = kernel(case, budget)
    row = Dict{String,Any}("case" => case["id"], "method" => method,
        "setting" => controls["id"], "times" => case["times"], "max_step" => cap)
    f = SciML.ODEFunction{true}(k.rhs!; jac=k.jac!, tgrad=k.time_gradient!)
    problem = SciML.ODEProblem(f, Float64.(case["initial"]), (0.0, Float64(last(case["times"]))))
    try
        solution = SciML.solve(problem, method == "Tsit5" ? Tsit.Tsit5() : Rosen.Rodas5P();
            reltol=controls["rtol"], abstol=controls["atol"], dtmax=Float64(cap),
            saveat=Float64.(case["times"]), save_start=first(case["times"]) == 0,
            save_end=true, save_everystep=false, dense=false, adaptive=true,
            dt=nothing, force_dtmin=false, maxiters=typemax(Int), callback=nothing)
        SciML.successful_retcode(solution.retcode) || throw(ProbeFailure("INTEGRATION_FAILURE", 0, 0))
        solution.t == case["times"] && length(solution.u) == length(case["times"]) ||
            throw(ProbeFailure("INCOMPLETE_OUTPUT", 0, 0))
        all(u -> length(u) == 4 && all(isfinite, u), solution.u) || throw(ProbeFailure("NONFINITE_OUTPUT", 0, 0))
        all(u -> all(>=(0), u), solution.u) || throw(ProbeFailure("NEGATIVE_OUTPUT", 0, 0))
        row["outcome"] = "SUCCESS"
        row["states"] = [collect(u) for u in solution.u]
        row["backend_nf"] = solution.stats.nf
        row["njev"] = solution.stats.njacs
        row["nw"] = solution.stats.nw
    catch error
        error isa ProbeFailure || rethrow()
        row["outcome"] = error.category
        row["failure_time"] = error.time
        row["failure_environment"] = isfinite(error.environment) ? error.environment : string(error.environment)
    end
    row["rhs_calls"] = k.calls[]
    row["jacobian_calls"] = k.jac_calls[]
    row["minimum_environment_stage"] = isfinite(k.minimum_e[]) ? k.minimum_e[] : nothing
    row
end

# Independent high-precision balance formula used only to check derivatives.
function precise_rhs(case, u)
    p = Dict(k => BigFloat(v) for (k,v) in case["parameters"])
    ns, nr = case["populations"]
    vs, vr, ve = BigFloat.(case["volumes"])
    s, r, e, y = u
    js = p["sender_export"]*s - p["sender_import"]*vs*e/ve
    jr = p["receiver_export"]*r - p["receiver_import"]*vr*e/ve
    c, n = e/ve, Int(p["hill_n"])
    h = c^n/(p["threshold"]^n+c^n)
    [p["sender_production"]-p["sender_decay"]*s-js, -p["receiver_decay"]*r-jr,
     ns*js+nr*jr-p["env_decay"]*e, p["reporter_basal"]+p["reporter_induced"]*h-p["reporter_decay"]*y]
end

function regression_tests(cases)
    @testset "Proposed M1 independent Julia kernel" begin
        setprecision(BigFloat, 512) do
            for n in 1:4, e in (0.0, 13.0, 26.0, 52.0)
                case = deepcopy(first(cases))
                case["populations"] = [7,11]
                case["volumes"] = [2,5,13]
                merge!(case["parameters"], Dict("hill_n"=>n, "sender_export"=>3, "receiver_export"=>2,
                    "sender_import"=>5, "receiver_import"=>7, "sender_decay"=>2,
                    "receiver_decay"=>3, "env_decay"=>1, "sender_production"=>4,
                    "reporter_basal"=>3, "reporter_induced"=>7, "reporter_decay"=>2))
                k = kernel(case, 1000)
                u, du, jac = [4.0,9.0,e,2.0], zeros(4), zeros(4,4)
                k.rhs!(du,u,nothing,0.0)
                k.jac!(jac,u,nothing,0.0)
                expected = precise_rhs(case, BigFloat.(u))
                @test all(abs.(BigFloat.(du).-expected) .<= big"1e-12".*max.(1,abs.(expected)))
                h = big"1e-30"
                for j in 1:4
                    above, below = BigFloat.(u), BigFloat.(u)
                    above[j] += h; below[j] -= h
                    difference = (precise_rhs(case,above).-precise_rhs(case,below))./(2h)
                    @test all(abs.(BigFloat.(jac[:,j]).-difference) .<= big"1e-12".*max.(1,abs.(difference)))
                end
            end
        end
        k = kernel(first(cases), 1)
        @test_throws ProbeFailure k.rhs!(zeros(4),[0.0,0.0,-1e-30,0.0],nothing,0.0)
        @test_throws ProbeFailure k.rhs!(zeros(4),Float64.(first(cases)["initial"]),nothing,0.0)
        k = kernel(first(cases), 10)
        @test_throws ProbeFailure k.jac!(zeros(4,4),[0.0,0.0,-1e-30,0.0],nothing,0.0)
        gradient = ones(4)
        k.time_gradient!(gradient, Float64.(first(cases)["initial"]),nothing,0.0)
        @test gradient == zeros(4)
    end
end

function main(report_path)
    config = JSON.parsefile(joinpath(@__DIR__, "settings.json"))
    catalog_path = joinpath(@__DIR__, "..", "cases.json")
    data = JSON.parsefile(catalog_path)
    validate_catalog(data)
    regression_tests(data["cases"])
    references = samples(1024)
    runs, tails = Any[], Any[]
    setprecision(BigFloat,1024) do
        for case in data["cases"], method in ("Tsit5","Rodas5P"), controls in config["settings"]
            row = integrate(case,method,controls,config["reference_max_step"],config["max_rhs_calls"])
            comparisons = Any[]
            if row["outcome"] == "SUCCESS"
                ns,nr = case["populations"]
                weights = BigFloat[ns,nr,1,0]
                initial = BigFloat.(case["initial"])
                reference_initial = only(filter(r -> r["case"]==case["id"] && r["time"]==0,references))["state"]
                initial_error = abs(sum(weights.*(initial.-reference_initial)))
                p = case["parameters"]
                closed = all(p[k]==0 for k in ("sender_production","sender_decay","receiver_decay","env_decay"))
                for (time,values) in zip(case["times"],row["states"])
                    expected = only(filter(r -> r["case"]==case["id"] && r["time"]==time,references))["state"]
                    bounds = BigFloat(config["state_bound"]["absolute"]) .+
                             BigFloat(config["state_bound"]["relative"]).*abs.(expected)
                    ratios = abs.(BigFloat.(values).-expected)./bounds
                    comparison = Dict{String,Any}("time"=>time,"reference"=>string.(expected),
                        "state_error_ratios"=>string.(ratios),"within_state_bound"=>all(<=(1),ratios))
                    if closed
                        drift = abs(sum(weights.*(BigFloat.(values).-initial)))
                        bound = sum(weights.*bounds)+initial_error
                        merge!(comparison,Dict("closed_signal_drift"=>string(drift),"balance_bound"=>string(bound),
                            "initial_representation_error"=>string(initial_error),"within_balance_bound"=>drift<=bound))
                    end
                    push!(comparisons,comparison)
                end
            end
            row["comparisons"] = comparisons
            push!(runs,row)
        end
        tail = deepcopy(only(filter(c -> c["id"]==config["tail_control"]["case"],data["cases"])))
        tail["times"] = config["tail_control"]["times"]
        for method in ("Tsit5","Rodas5P"), controls in config["settings"]
            row = integrate(tail,method,controls,config["tail_control"]["max_step"],config["max_rhs_calls"])
            stop = get(row,"failure_time",1000.0)
            row["analytical_environment_at_stop"] = string(48*exp(-BigFloat(stop)/2))
            push!(tails,row)
        end
    end
    passed = length(runs)==40 && all(row["outcome"]=="SUCCESS" && length(row["comparisons"])==3 &&
        all(c["within_state_bound"] && get(c,"within_balance_bound",true) for c in row["comparisons"]) for row in runs)
    files = ["settings.json","study.jl","../cases.json","../reference.jl",
             "../../julia_ode/Project.toml","../../julia_ode/Manifest.toml"]
    report = Dict("status"=>"PROPOSED","runtime"=>Dict("julia"=>string(VERSION),
        "SciMLBase"=>string(pkgversion(SciML)),"OrdinaryDiffEqTsit5"=>string(pkgversion(Tsit)),
        "OrdinaryDiffEqRosenbrock"=>string(pkgversion(Rosen))),
        "files_sha256"=>Dict(file=>bytes2hex(sha256(read(joinpath(@__DIR__,file)))) for file in files),
        "settings"=>config,"source_revision"=>get(ENV,"GITHUB_SHA","unrecorded"),
        "reference_state_ids"=>data["state_ids"],"runs"=>runs,"tail_controls"=>tails,
        "bounded_reference_matrix"=>passed ? "PASS" : "FAIL",
        "tail_policy"=>"observed; explicit domain/output failure allowed; no SciPy outcome inferred",
        "native_implementation"=>"NOT RUN","pi_executable_profile_acceptance"=>"PENDING")
    mkpath(dirname(report_path))
    open(report_path,"w") do io
        JSON.print(io,report,2)
    end
    @assert passed "bounded Julia reference matrix failed; inspect retained report"
    println("PASS proposed Julia bounded matrix: 40 integrations / 120 samples")
    println("Tail observations: ",join([row["outcome"] for row in tails],", "))
end

if abspath(PROGRAM_FILE) == @__FILE__
    main(only(ARGS))
end
