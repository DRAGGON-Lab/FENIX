struct ODEResult
    text::String
    ODEResult(::_Verified,text) = new(text)
end
struct RunManifest
    text::String
    RunManifest(::_Verified,text) = new(text)
end
struct RunRecord
    result::ODEResult
    manifest::RunManifest
    RunRecord(::_Verified,result,manifest) = new(result,manifest)
end
to_json(doc::Union{ODEResult,RunManifest}) = doc.text
to_dict(doc::ODEResult) = _decode(doc.text,:result)
to_dict(doc::RunManifest) = _decode(doc.text,:manifest)
result_bytes(record::RunRecord) = Vector{UInt8}(codeunits(to_json(record.result)))
manifest_bytes(record::RunRecord) = Vector{UInt8}(codeunits(to_json(record.manifest)))
_source_reference(doc) = merge(reference(doc), Dict("schema_version"=>"0.2.0"))
_fir_reference(fir_digest) = Dict("schema_version"=>"0.2.0","canonicalization_version"=>"0.2.0","digest"=>fir_digest)

function _observable_metadata(observations)
    columns = _observable_columns(observations)
    Dict("observable_ids"=>[o["id"] for o in observations],
         "observable_state_ids"=>[STATES[i] for i in columns],
         "observable_units"=>fill("molecule",length(columns)),
         "observable_owners"=>[OWNERS[i] for i in columns],
         "observable_scopes"=>[SCOPES[i] for i in columns])
end
function _validate_record(result, manifest, result_text, experiment, fir)
    _validate("ode-result",result)
    _validate("run-manifest",manifest)
    fir_digest = digest(fir)
    _need(result["fir_digest"] == fir_digest,"FIR_LINK","/fir_digest")
    _need(manifest["fir"]["digest"] == fir_digest,"FIR_LINK","/fir/digest")
    for (key,doc) in (("design",experiment.design),("experiment",experiment))
        _need(_equal(manifest["sources"][key],_source_reference(doc)),"SOURCE_LINK","/sources/$key")
    end
    _need(manifest["output"]["sha256"] == _sha(result_text),"RESULT_CHECKSUM","/output/sha256")
    times = result["times"]
    execution,backend = manifest["execution"],manifest["backend"]
    grid = execution["time_grid"]
    _need(all(times[i] > times[i-1] for i in 2:length(times)),"GRID","/times")
    _need(length(grid) == length(times) && all(_bits(a,b) for (a,b) in zip(grid,times)),"GRID","/execution/time_grid")
    _need(result["state_owners"] == collect(OWNERS),"SCOPE_ALIGNMENT","/state_owners")
    _need(result["state_scopes"] == collect(SCOPES),"SCOPE_ALIGNMENT","/state_scopes")
    model = normalized_model(fir)
    observations = model["observables"]
    columns = _observable_columns(observations)
    for (key,expected) in _observable_metadata(observations)
        _need(result[key] == expected,"OBSERVABLE_ALIGNMENT","/$key")
    end
    for key in ("state_values","observable_values")
        _need(length(result[key]) == length(times),"DIMENSIONS","/$key")
    end
    for i in eachindex(times)
        states,copies = result["state_values"][i],result["observable_values"][i]
        _need(length(copies) == length(columns),"DIMENSIONS","/observable_values/$(i-1)")
        for (j,column) in enumerate(columns)
            _need(_bits(copies[j],states[column]),"OBSERVABLE_COPY","/observable_values/$(i-1)/$(j-1)")
        end
        if times[i] == 0
            _need(all(states[j] == model["initial_counts"][id]["value"] for (j,id) in enumerate(STATES)),
                  "INITIAL_SAMPLE","/state_values/$(i-1)")
        end
    end
    nfev = manifest["evaluations"]["nfev"]
    _need(nfev <= execution["max_nfev"],"WORK_COUNT","/evaluations/nfev")
    zero = length(times) == 1 && only(times) == 0
    _need(manifest["integration"] == (zero ? "skipped_zero_grid" : "performed"),"INTEGRATION","/integration")
    if zero
        _need(nfev == 0 && all(iszero,values(backend["evaluations"])),"WORK_COUNT","/evaluations")
    else
        _need(nfev > 0,"WORK_COUNT","/evaluations/nfev")
    end
    if startswith(backend["profile"],"julia-")
        options = backend["solver"]["options"]
        _need(options["save_start"] == (first(times) == 0),"BACKEND_OPTIONS","/backend/solver/options/save_start")
        _need(options["maxiters"] == typemax(Int64),"BACKEND_OPTIONS","/backend/solver/options/maxiters")
    end
    for key in ("started_at_utc","finished_at_utc")
        stamp = manifest["timing"][key]
        # The schema has already checked the UTC six-digit text grammar.
        date = tryparse(DateTime, stamp[1:23], dateformat"yyyy-mm-ddTHH:MM:SS.sss")
        _need(date !== nothing && year(date) >= 1,"TIMESTAMP","/timing/$key")
    end
    nothing
end

function _record(result_text,manifest_text,experiment,fir)
    result,manifest = _decode(result_text,:result),_decode(manifest_text,:manifest)
    _validate_record(result,manifest,result_text,experiment,fir)
    RunRecord(_Verified(),ODEResult(_Verified(),result_text),RunManifest(_Verified(),manifest_text))
end

function from_json(::Type{RunRecord},raw_result,raw_manifest; experiment::Experiment,expected_manifest_sha256=nothing)
    result,manifest = _text(raw_result),_text(raw_manifest)
    expected_manifest_sha256 === nothing ||
        _need(_sha(manifest) == expected_manifest_sha256,"MANIFEST_CHECKSUM","")
    _record(result,manifest,experiment,compile_experiment(experiment))
end

function _capture(experiment,spec;build_id=nothing,compile=compile_experiment,solve=solve_ode)
    _need(build_id === nothing || build_id isa String && !isempty(build_id) && isvalid(build_id),
          "SCHEMA","/producer/build_id")
    start_wall,start_ns = Results._utc_now(),time_ns()
    fir = compile(experiment)
    trajectory = solve(fir,spec)
    finish_ns,finish_wall = time_ns(),Results._utc_now()
    observations = normalized_model(fir)["observables"]
    fir_digest = trajectory.fir_digest
    result = Dict{String,Any}("kind"=>"ODEResult","schema_version"=>"0.2.0","fir_digest"=>fir_digest,
        "time_unit"=>"s","times"=>trajectory.times,"state_ids"=>STATES,"state_units"=>fill("molecule",length(STATES)),
        "state_owners"=>OWNERS,"state_scopes"=>SCOPES,"state_values"=>trajectory.state_values,
        "observable_values"=>trajectory.observable_values)
    merge!(result,_observable_metadata(observations))
    result_text = _emit(result)
    versions = Dict(Execution._backend_versions())
    options = Results._julia_options(spec.time_grid)
    options["jacobian"] = "state_dependent_exact_inplace"
    manifest = Dict{String,Any}("kind"=>"RunManifest","schema_version"=>"0.2.0","status"=>"success",
        "repeatability"=>"bounded_numerical_agreement",
        "sources"=>Dict("design"=>_source_reference(experiment.design),"experiment"=>_source_reference(experiment)),
        "fir"=>_fir_reference(fir_digest),"execution"=>Dict("profile"=>"ode","time_grid"=>spec.time_grid,
            "rtol"=>spec.rtol,"atol"=>spec.atol,"max_step"=>spec.max_step,"max_nfev"=>spec.max_nfev),
        "randomness"=>Dict("rng"=>"none","seed"=>nothing),"evaluations"=>Dict("nfev"=>trajectory.nfev),
        "timing"=>Dict("started_at_utc"=>Results._wall_text(start_wall),"finished_at_utc"=>Results._wall_text(finish_wall),
            "elapsed_seconds"=>Float64(finish_ns-start_ns)/1e9),
        "integration"=>(last(spec.time_grid)==0 ? "skipped_zero_grid" : "performed"),
        "output"=>Dict("schema_version"=>"0.2.0","media_type"=>"application/json","encoding"=>"utf-8","sha256"=>_sha(result_text)),
        "producer"=>Dict("name"=>"Fenix","version"=>string(pkgversion(parentmodule(@__MODULE__))),"build_id"=>build_id),
        "backend"=>Dict("profile"=>"julia-sciml-community-ode/0.1.0",
            "solver"=>Dict("name"=>"SciMLBase.solve","method"=>spec.method,"options"=>options),
            "environment"=>Dict("julia_version"=>versions["julia"],"scimlbase_version"=>versions["SciMLBase"],
                "ordinarydiffeqtsit5_version"=>versions["OrdinaryDiffEqTsit5"],
                "ordinarydiffeqrosenbrock_version"=>versions["OrdinaryDiffEqRosenbrock"],"json_version"=>string(pkgversion(JSON))),
            "evaluations"=>Dict("njev"=>trajectory.njev,"nw"=>trajectory.nw)))
    _record(result_text,_emit(manifest),experiment,fir)
end

run_experiment(experiment::Experiment,spec::ODEExecutionSpec;build_id=nothing) =
    _capture(experiment,spec;build_id)
