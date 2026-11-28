using Test, JSON, SHA, Fenix
const C = Fenix.Community
const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const PACKET = joinpath(ROOT, "spec/community/wire-candidates")
const CATALOG = JSON.parsefile(joinpath(PACKET, "catalog.json"))
@testset "Bundled accepted schemas" begin
    fingerprints = JSON.parsefile(joinpath(ROOT,"spec/community/review-manifest.json"))["sha256"]
    for name in ("bioir","fir","ode-result","run-manifest")
        filename = "$name-m1.schema.json"
        packaged = joinpath(dirname(pathof(Fenix)),"community/schemas",filename)
        @test bytes2hex(sha256(read(packaged))) == fingerprints["spec/community/$filename"]
    end
end
module Independent
include(joinpath(@__DIR__, "../../../conformance/community/feasibility/study.jl"))
end
using .Independent: samples, validate_catalog, precise_rhs, tail_comparisons

function packet(folder)
    directory = joinpath(PACKET, folder)
    design = C.from_json(C.Design, read(joinpath(directory, "design.json")))
    experiment = C.from_json(C.Experiment, read(joinpath(directory, "experiment.json")); design)
    directory, design, experiment, C.compile_experiment(experiment)
end

@testset "Accepted literal packet" begin
    for row in CATALOG["positive"]
        directory, design, experiment, fir = packet(row["folder"])
        @test C.model_bytes(fir) == read(joinpath(directory, "model.jcs"))
        @test C.identity_bytes(fir) == read(joinpath(directory, "identity.jcs"))
        @test C.digest(fir) == strip(read(joinpath(directory, "digest.txt"), String))
        @test C.digest(C.from_json(C.FIR, read(joinpath(directory, "fir.json")); experiment)) == C.digest(fir)
        for label in ("zero", "analytical"), language in ("python", "julia")
            raw = read(joinpath(directory, "$label.result.json"))
            manifest = read(joinpath(directory, "$label.$language.manifest.json"))
            record = C.from_json(C.RunRecord, raw, manifest; experiment)
            @test C.result_bytes(record) == raw
            @test C.manifest_bytes(record) == manifest
        end
    end
    for row in CATALOG["rejections"]
        directory, design, experiment, _ = packet(row["base"])
        raw = read(joinpath(PACKET, row["file"]))
        target = row["target"]
        failure = try
            if target == "design"
                C.from_json(C.Design, raw)
            elseif target == "experiment"
                C.from_json(C.Experiment, raw; design)
            elseif target == "fir"
                C.from_json(C.FIR, raw; experiment)
            elseif target == "result"
                C.from_json(C.RunRecord, raw, read(joinpath(PACKET, row["manifest"])); experiment)
            else
                C.from_json(C.RunRecord, read(joinpath(directory, "zero.result.json")), raw; experiment)
            end
            nothing
        catch error
            error
        end
        @test failure isa C.ValidationError
        if failure isa C.ValidationError
            @test (failure.category, failure.path) == (row["category"], row["path"])
        else
            @info "Unexpected rejection outcome" witness=row["id"] failure
        end
    end
end

@testset "Native coupled methods against independent BigFloat laws" begin
    data = JSON.parsefile(joinpath(ROOT, "conformance/community/cases.json"))
    validate_catalog(data)
    setprecision(BigFloat, 1024) do
        expectations = Dict((row["case"], row["time"]) => row["state"] for row in samples(1024))
        order = data["state_ids"]
        for case in data["cases"], method in ("Tsit5", "Rodas5P"), (rtol, atol) in ((1e-9,1e-11),(1e-11,1e-13))
            _, _, experiment, fir = packet(case["id"])
            spec = C.ODEExecutionSpec(; time_grid=(0.0,1.0,4.0), method, rtol, atol, max_step=1.0,max_nfev=200000)
            trajectory = C.solve_ode(fir, spec)
            indices = [findfirst(==(id), trajectory.state_ids) for id in order]
            weights = BigFloat[case["populations"]...,1,0]
            initial = BigFloat.(Float64.(case["initial"]))
            initial_error = abs(sum(weights .* (initial - expectations[(case["id"],0)])))
            for (time, row) in zip(trajectory.times, trajectory.state_values)
                expected = expectations[(case["id"],Int(time))]
                observed = BigFloat[row[i] for i in indices]
                bounds = big"1e-9" .+ big"1e-8" .* abs.(expected)
                @test all(abs.(observed - expected) .<= bounds)
                if all(iszero(case["parameters"][key]) for key in ("sender_production","sender_decay","receiver_decay","env_decay"))
                    @test abs(sum(weights .* (observed - initial))) <= sum(weights .* bounds) + initial_error
                end
            end
        end
    end
end

settings(;times=(0.0,1.0,4.0),method="Rodas5P",cap=1.0,budget=200000,rtol=1e-9,atol=1e-11) =
    C.ODEExecutionSpec(;time_grid=times,method,rtol,atol,max_step=cap,max_nfev=budget)

@testset "Numeric transport and grids" begin
    for row in CATALOG["raw_numbers"]
        raw = read(joinpath(PACKET,row["file"]))
        if row["category"] === nothing
            decoded = C._decode(raw, Symbol(row["policy"]))
            @test decoded == row["value"]
            if row["value"]["value"] isa Float64
                @test C._bits(decoded["value"],row["value"]["value"])
            end
        else
            @test_throws C.ValidationError(row["category"],row["path"]) C._decode(raw,Symbol(row["policy"]))
        end
    end
    for row in JSON.parsefile(joinpath(PACKET,"transport-vectors.json"))
        if haskey(row,"category")
            @test_throws C.ValidationError(row["category"],row["error_path"]) C._decode(row["raw"],Symbol(row["kind"]))
        else
            value = C._decode(row["raw"],Symbol(row["kind"]))
            for key in row["path"]
                value = value[key isa Integer ? key+1 : key]
            end
            if haskey(row,"bits")
                @test string(reinterpret(UInt64,value);base=16,pad=16) == row["bits"]
            else
                @test string(value) == row["decimal"]
            end
        end
    end
    directory,_,experiment,_ = packet("threshold-n1")
    for row in JSON.parsefile(joinpath(PACKET,"grid-vectors.json"))
        result = JSON.parsefile(joinpath(directory,"zero.result.json"))
        manifest = JSON.parsefile(joinpath(directory,"zero.python.manifest.json"))
        times = row["times"]
        result["times"] = times
        for key in ("state_values","observable_values")
            result[key] = fill(only(result[key]),length(times))
        end
        raw = C._emit(result)
        zero = length(times) == 1 && only(times) == 0
        manifest["execution"]["time_grid"] = row["manifest"]
        manifest["integration"] = zero ? "skipped_zero_grid" : "performed"
        manifest["evaluations"]["nfev"] = zero ? 0 : 1
        manifest["output"]["sha256"] = bytes2hex(sha256(raw))
        if row["accepted"]
            @test C.to_json(C.from_json(C.RunRecord,raw,C._emit(manifest);experiment).result) == raw
        else
            @test_throws C.ValidationError C.from_json(C.RunRecord,raw,C._emit(manifest);experiment)
        end
    end
end

@testset "Immutable sources, capture, and readback" begin
    _,design,experiment,fir = packet("threshold-n1")
    content = C.to_dict(design)["content"]
    content["owners"][1]["volume"]["value"] = 100.0
    @test C.to_dict(design)["content"] != content
    @test_throws C.ValidationError("REVISION","/content/revision") C.replace_content(design,content)
    content["revision"] = 2
    successor = C.replace_content(design,content)
    @test_throws C.ValidationError("DESIGN_LINK","/content/design") C.from_json(C.Experiment,C.to_json(experiment);design=successor)
    compilation, solving = Ref(0),Ref(0)
    compile(x) = (compilation[] += 1; C.compile_experiment(x))
    solve(x,spec) = (solving[] += 1; C.solve_ode(x,spec))
    record = C._capture(experiment,settings();compile,solve,build_id="observed")
    @test compilation[] == solving[] == 1
    @test C.to_dict(record.result)["fir_digest"] == C.digest(fir)
    raw,manifest = C.result_bytes(record),C.manifest_bytes(record)
    trusted = bytes2hex(sha256(manifest))
    @test C.result_bytes(C.from_json(C.RunRecord,raw,manifest;experiment,expected_manifest_sha256=trusted)) == raw
    @test_throws C.ValidationError("MANIFEST_CHECKSUM","") C.from_json(C.RunRecord,raw,manifest;experiment,expected_manifest_sha256="bad")
    bad = C.result_bytes(record)
    bad[1] = 0x00
    @test C.result_bytes(record) == raw
    @test_throws C.ValidationError C._capture(experiment,settings();build_id="",compile,solve)
    @test compilation[] == solving[] == 1
    for folder in ("threshold-n1","empty-observables")
        _,_,exp_model,model_fir = packet(folder)
        zero = settings(;times=(-0.0,),budget=9007199254740993)
        skipped = C._solve_ode(model_fir,zero,(_,_) -> error("zero-only grid invoked solver"))
        @test skipped.nfev == 0
        record = C.run_experiment(exp_model,zero)
        @test signbit(only(C.to_dict(record.result)["times"]))
        @test C.to_dict(record.manifest)["execution"]["max_nfev"] == 9007199254740993
        later = C.run_experiment(exp_model,settings(;times=(1.0,4.0)))
        @test !C.to_dict(later.manifest)["backend"]["solver"]["options"]["save_start"]
        @test C.to_dict(later.result)["times"] == [1.0,4.0]
        if folder == "empty-observables"
            @test C.to_dict(later.result)["observable_values"] == [[],[]]
        end
    end
end

@testset "Numerical failure and kernel controls" begin
    _,_,_,fir = packet("driven-n1")
    error_category(f) = try f(); nothing catch error; error.category end
    @test error_category(() -> C.solve_ode(fir,settings(;budget=1))) == "WORK_LIMIT"
    kernel = C._kernel(C.normalized_model(fir),settings())
    @test error_category(() -> kernel.rhs!(zeros(4),[-1.0,0.0,0.0,0.0],nothing,0.0)) == "STAGE_DOMAIN"
    @test error_category(() -> kernel.jac!(zeros(4,4),[NaN,0.0,0.0,0.0],nothing,0.0)) == "NONFINITE"
    gradient = ones(4)
    kernel.tgrad!(gradient,[0.0,1.0,-1.0,0.0],nothing,0.0)
    @test gradient == zeros(4)
    config = JSON.parsefile(joinpath(ROOT,"conformance/community/feasibility/settings.json"))
    function tail_pass(times, rows)
        report = Dict("outcome"=>"SUCCESS","times"=>times,"states"=>rows)
        comparisons = tail_comparisons(report,config)
        length(comparisons) == length(times) && all(c["within_state_bound"] for c in comparisons)
    end
    valid = [[0.,0.,48.,2.],[0.,0.,3.419797155236988e-216,2.]]
    @test tail_pass((0.0,1000.0),valid)
    for column in 1:4
        broken = deepcopy(valid)
        broken[2][column] += 1
        @test !tail_pass((0.0,1000.0),broken)
    end
    for method in ("Tsit5","Rodas5P"), (rtol,atol) in ((1e-9,1e-11),(1e-11,1e-13))
        outcome = try
            C.solve_ode(fir,settings(;times=(0.0,1000.0),method,cap=10.0,rtol,atol))
        catch error
            error isa Fenix.Execution.ODEExecutionError || rethrow()
            error
        end
        if outcome isa Fenix.Execution.ODEExecutionError
            @test outcome.category in ("STAGE_DOMAIN","NEGATIVE_OUTPUT","NONFINITE","INCOMPLETE_OUTPUT","INTEGRATION_FAILURE")
            @info "Native Julia tail outcome" method rtol category=outcome.category
        else
            @test tail_pass(outcome.times,[[row[i] for i in (4,3,1,2)] for row in outcome.state_values])
        end
    end
    mock(times,rows) = (_,_) -> (retcode=C.SciMLBase.ReturnCode.Success,t=times,u=rows,stats=(njacs=0,nw=0))
    @test error_category(() -> C._solve_ode(fir,settings(),mock([0.0],[zeros(4)]))) == "INCOMPLETE_OUTPUT"
    @test error_category(() -> C._solve_ode(fir,settings(),mock([0.0,1.0,4.0],fill([-1.,0.,0.,0.],3)))) == "NEGATIVE_OUTPUT"
    @test error_category(() -> C._solve_ode(fir,settings(),mock([0.0,1.0,4.0],fill([Inf,0.,0.,0.],3)))) == "NONFINITE"
end


@testset "Asymmetric independent RHS and Jacobian probes" begin
    _,design,experiment,fir = packet("threshold-n1")
    data = JSON.parsefile(joinpath(ROOT,"conformance/community/cases.json"))
    permutation = Int[findfirst(==(id),data["state_ids"]) for id in C.STATES]
    setprecision(BigFloat,512) do
        for exponent in 1:4
            case = deepcopy(first(data["cases"]))
            case["populations"] = [7,11]
            case["volumes"] = [2,5,13]
            merge!(case["parameters"],Dict("hill_n"=>exponent,"sender_export"=>3,"receiver_export"=>2,
                "sender_import"=>5,"receiver_import"=>7,"sender_decay"=>2,"receiver_decay"=>3,
                "env_decay"=>1,"sender_production"=>4,"reporter_basal"=>3,"reporter_induced"=>7,"reporter_decay"=>2))
            model = C.normalized_model(fir)
            for (id,entry) in model["parameters"]
                entry["value"] = case["parameters"][id]
            end
            for (i,role) in enumerate(("sender","receiver","env"))
                model["volumes"][role]["value"] = case["volumes"][i]
            end
            for (i,role) in enumerate(("sender","receiver"))
                model["populations"][role] = case["populations"][i]
            end
            kernel = C._kernel(model,settings())
            for env in (0.0,13.0,26.0,52.0)
                ref_state = BigFloat[4,9,env,2]
                native_state = Float64.(ref_state[permutation])
                rhs,jac = zeros(4),zeros(4,4)
                kernel.rhs!(rhs,native_state,nothing,0.0)
                kernel.jac!(jac,native_state,nothing,0.0)
                expected = precise_rhs(case,ref_state)[permutation]
                @test all(abs.(rhs - expected) .<= big"1e-12" .* max.(1,abs.(expected)))
                step = big"1e-30"
                for (column,reference_column) in enumerate(permutation)
                    above,below = copy(ref_state),copy(ref_state)
                    above[reference_column] += step
                    below[reference_column] -= step
                    expected = ((precise_rhs(case,above)-precise_rhs(case,below))/(2step))[permutation]
                    @test all(abs.(jac[:,column] - expected) .<= big"1e-12" .* max.(1,abs.(expected)))
                end
            end
        end
    end
    model = C.normalized_model(fir)
    model["parameters"]["threshold"]["value"] = 1e308
    model["volumes"]["env"]["value"] = 1e308
    kernel = C._kernel(model,settings())
    failure = try
        kernel.jac!(zeros(4,4),zeros(4),nothing,0.0)
        nothing
    catch error
        error
    end
    @test failure isa Fenix.Execution.ODEExecutionError
    @test failure.category == "NONFINITE"
end
