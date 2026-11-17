"""P07 source-linked ODE capture and strict, non-executing verified readback.

Checksums establish byte consistency, not execution authenticity, numerical
correctness or biological validity. Loading never executes an ODE.
"""
module Results
using SHA, Dates
import JSON
import ..BioIR, ..FIR, ..Execution
import ..Fenix: compile_experiment
export RunRecord, RunManifest, ODEResult, ResultValidationError,
       run_experiment, from_json, to_dict, to_json

struct ResultValidationError <: Exception
    category::String
    path::String
    message::String
end
Base.showerror(io::IO,e::ResultValidationError) = print(io,e.category," at ",e.path,": ",e.message)
_fail(path,message,category="SCHEMA") = throw(ResultValidationError(category,path,message))
_need(ok,path,message,category="SCHEMA") = ok || _fail(path,message,category)
_pointer(path,key) = path*"/"*replace(string(key),"~"=>"~0","/"=>"~1")

# BigInt is mutable. Preserve exact integer values internally as immutable
# decimal text and allocate a fresh BigInt on every ordinary dictionary export.
struct _Integer
    decimal::String
end
struct _Object
    entries::Tuple
end
_freeze(x::AbstractDict) = _Object(Tuple(k=>_freeze(v) for (k,v) in x))
_freeze(x::Union{AbstractVector,Tuple}) = Tuple(_freeze(v) for v in x)
_freeze(x::Integer) = x isa Bool ? x : _Integer(string(x))
_freeze(x) = x
_thaw(x::_Object) = Dict{String,Any}(k=>_thaw(v) for (k,v) in x.entries)
_thaw(x::Tuple) = Any[_thaw(v) for v in x]
_thaw(x::_Integer) = parse(BigInt,x.decimal)
_thaw(x) = x

# The marker is private: public construction is only through capture/readback.
struct _Validated end
struct RunManifest
    _data::_Object
    _text::String
    RunManifest(::_Validated,data::_Object,text::String) = new(data,text)
end
struct ODEResult
    _data::_Object
    ODEResult(::_Validated,data::_Object) = new(data)
end
function Base.getproperty(value::ODEResult,name::Symbol)
    name === :_data && return getfield(value,:_data)
    for (key,item) in getfield(value,:_data).entries
        key == string(name) && return item
    end
    throw(ArgumentError("ODEResult has no property $name"))
end
Base.propertynames(value::ODEResult,private::Bool=false) =
    private ? (:_data,Tuple(Symbol(k) for (k,_) in getfield(value,:_data).entries)...) :
              Tuple(Symbol(k) for (k,_) in getfield(value,:_data).entries)
struct RunRecord
    manifest::RunManifest
    result::ODEResult
    _bytes::String
    RunRecord(::_Validated,manifest::RunManifest,result::ODEResult,bytes::String) = new(manifest,result,bytes)
end
Base.getproperty(record::RunRecord,name::Symbol) = name === :result_bytes ? Vector{UInt8}(codeunits(getfield(record,:_bytes))) : getfield(record,name)
Base.propertynames(::RunRecord,private::Bool=false) = private ? (:manifest,:result,:result_bytes,:_bytes) : (:manifest,:result,:result_bytes)
to_dict(value::Union{RunManifest,ODEResult}) = _thaw(getfield(value,:_data))
to_json(value::RunManifest) = getfield(value,:_text)

function _text(raw,path)
    _need(raw isa String || raw isa Vector{UInt8},path,"require JSON text or UTF-8 byte vector")
    text = raw isa String ? raw : String(copy(raw))
    _need(isvalid(text),path,"require strict UTF-8 Unicode scalars","INVALID_UNICODE")
    text
end
function _parse(text,path)
    try
        BioIR._parse_json_tokens(text)
    catch error
        error isa BioIR.BioIRValidationError || rethrow()
        _fail(path*error.path,error.message,error.category)
    end
end
function _object(raw,path,keys)
    _need(raw isa Dict{String,Any},path,"require an object")
    expected = split(keys)
    for key in Base.keys(raw)
        _need(key in expected,_pointer(path,key),"unknown member")
    end
    for key in expected
        _need(haskey(raw,key),_pointer(path,key),"missing member")
    end
    raw
end
function _equal(value,expected,path,category="SCHEMA")
    # Numeric equality must never turn booleans into numbers.
    _need(typeof(value) === typeof(expected) && isequal(value,expected),path,"differs from required value",category)
end
function _string(value,path)
    _need(value isa String && !isempty(value),path,"require a nonempty string")
    value
end
function _checksum(value,path)
    _string(value,path)
    _need(occursin(r"\A[0-9a-f]{64}\z",value),path,"require lowercase hexadecimal SHA-256","CHECKSUM")
    value
end
function _float(raw,path;positive=false)
    _need(raw isa BioIR._JSONNumberToken,path,"require JSON number","NUMBER")
    value = try
        BioIR._json_binary64(raw.raw,path)
    catch error
        error isa BioIR.BioIRValidationError || rethrow()
        _fail(error.path,error.message,error.category)
    end
    _need(value >= 0 && (!positive || value > 0),path,positive ? "require positive value" : "negative value","NUMBER")
    value
end
function _integer(raw,path;minimum=0,maximum=nothing)
    _need(raw isa BioIR._JSONNumberToken && occursin(r"\A-?(0|[1-9][0-9]*)\z",raw.raw),path,"require integer-form JSON number","INTEGER")
    value = parse(BigInt,raw.raw)
    _need(value >= minimum && (maximum === nothing || value <= maximum),path,"integer outside field range","INTEGER")
    value
end
function _array(raw,path)
    _need(raw isa Vector,path,"require array")
    raw
end
function _grid(raw,path)
    values = Float64[_float(item,_pointer(path,i-1)) for (i,item) in enumerate(_array(raw,path))]
    _need(!isempty(values),path,"require nonempty time grid","GRID")
    for i in 2:length(values)
        _need(values[i]>values[i-1],_pointer(path,i-1),"times must be strictly increasing","GRID")
    end
    values
end
_bits(value::Float64) = reinterpret(UInt64,value)
_reference(document) = Dict{String,Any}("schema_version"=>document.content.schema_version,
    "id"=>document.content.id,"revision"=>document.content.revision,"digest"=>document.digest)
function _timestamp(raw,path)
    text = _string(raw,path)
    _need(occursin(r"\A[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z\z",text),path,"require six-fractional-digit UTC timestamp")
    y,mo,d,h,mi,s = (parse(Int,text[a:b]) for (a,b) in ((1,4),(6,7),(9,10),(12,13),(15,16),(18,19)))
    _need(1 <= y <= 9999 && 0 <= h <= 23 && 0 <= mi <= 59 && 0 <= s <= 59,path,"invalid Gregorian UTC timestamp")
    try
        Date(y,mo,d)
    catch error
        error isa ArgumentError || rethrow()
        _fail(path,"invalid Gregorian UTC timestamp")
    end
    nothing
end
function _julia_options(grid)
    Dict{String,Any}("dt"=>nothing,"adaptive"=>true,"saveat"=>"requested_grid",
        "save_start"=>first(grid)==0.0,"save_end"=>true,"save_everystep"=>false,
        "dense"=>false,"callback"=>nothing,"force_dtmin"=>false,
        "dtmin"=>"backend_default","maxiters"=>typemax(Int),
        "jacobian"=>"exact_inplace","time_derivative"=>"autonomous_zero_inplace")
end
_python_options(method) = Dict{String,Any}("first_step"=>nothing,"vectorized"=>false,
    "dense_output"=>false,"events"=>nothing,"jacobian"=>method=="Radau" ? "constant_exact" : "not_supplied")
function _manifest(raw,experiment,fir)
    p = "/manifest"
    m = _object(raw,p,"kind schema_version status repeatability sources fir execution randomness evaluations timing integration output producer backend")
    for (key,value) in (("kind","RunManifest"),("schema_version","0.1.0"),("status","success"),("repeatability","bounded_numerical_agreement"))
        _equal(m[key],value,p*"/"*key,key=="schema_version" ? "UNSUPPORTED_VERSION" : "SCHEMA")
    end
    sources = _object(m["sources"],p*"/sources","design experiment")
    for (name,document) in (("design",experiment.source_design),("experiment",experiment))
        at = p*"/sources/"*name
        ref = _object(sources[name],at,"schema_version id revision digest")
        ref["revision"] = _integer(ref["revision"],at*"/revision";minimum=1,maximum=9007199254740991)
        for (key,value) in _reference(document)
            if key == "revision"
                _need(ref[key] == value,at*"/"*key,"source revision differs","REFERENCE")
            else
                _equal(ref[key],value,at*"/"*key,"REFERENCE")
            end
        end
    end
    f = _object(m["fir"],p*"/fir","schema_version canonicalization_version digest")
    for (key,value) in (("schema_version","0.1.0"),("canonicalization_version","0.1.0"),("digest",fir.digest))
        _equal(f[key],value,p*"/fir/"*key,"IDENTITY")
    end
    e = _object(m["execution"],p*"/execution","profile time_grid rtol atol max_step max_nfev")
    _equal(e["profile"],"ode",p*"/execution/profile","UNSUPPORTED_PROFILE")
    e["time_grid"] = _grid(e["time_grid"],p*"/execution/time_grid")
    for key in ("rtol","atol","max_step")
        e[key] = _float(e[key],p*"/execution/"*key;positive=true)
    end
    e["max_nfev"] = _integer(e["max_nfev"],p*"/execution/max_nfev";minimum=1)
    rng = _object(m["randomness"],p*"/randomness","rng seed")
    _equal(rng["rng"],"none",p*"/randomness/rng")
    _equal(rng["seed"],nothing,p*"/randomness/seed")
    ev = _object(m["evaluations"],p*"/evaluations","nfev")
    ev["nfev"] = _integer(ev["nfev"],p*"/evaluations/nfev")
    _need(ev["nfev"] <= e["max_nfev"],p*"/evaluations/nfev","exceeds work budget","COUNTERS")
    timing = _object(m["timing"],p*"/timing","started_at_utc finished_at_utc elapsed_seconds")
    for key in ("started_at_utc","finished_at_utc")
        _timestamp(timing[key],p*"/timing/"*key)
    end
    timing["elapsed_seconds"] = _float(timing["elapsed_seconds"],p*"/timing/elapsed_seconds")
    output = _object(m["output"],p*"/output","schema_version media_type encoding sha256")
    for (key,value) in (("schema_version","0.1.0"),("media_type","application/json"),("encoding","utf-8"))
        _equal(output[key],value,p*"/output/"*key)
    end
    _checksum(output["sha256"],p*"/output/sha256")
    producer = _object(m["producer"],p*"/producer","name version build_id")
    for key in ("name","version","build_id")
        key=="build_id" && producer[key]===nothing && continue
        _string(producer[key],p*"/producer/"*key)
    end
    backend = _object(m["backend"],p*"/backend","profile solver environment evaluations")
    profile = backend["profile"]
    _need(profile isa String && profile in ("python-scipy-ode/0.1.0","julia-sciml-ode/0.1.0"),p*"/backend/profile","unsupported backend profile","UNSUPPORTED_PROFILE")
    julia = profile=="julia-sciml-ode/0.1.0"
    solver = _object(backend["solver"],p*"/backend/solver","name method options")
    _equal(solver["name"],julia ? "SciMLBase.solve" : "scipy.integrate.solve_ivp",p*"/backend/solver/name")
    methods = julia ? ("Tsit5","Rodas5P") : ("DOP853","Radau")
    _need(solver["method"] isa String && solver["method"] in methods,p*"/backend/solver/method","unsupported method","UNSUPPORTED_METHOD")
    required = julia ? _julia_options(e["time_grid"]) : _python_options(solver["method"])
    options = _object(solver["options"],p*"/backend/solver/options",join(keys(required),' '))
    for (key,value) in required
        at = p*"/backend/solver/options/"*key
        if julia && key=="maxiters"
            options[key] = _integer(options[key],at;minimum=1)
        else
            _equal(options[key],value,at)
        end
    end
    if !julia
        _need(e["rtol"] >= 100*2.0^-52,p*"/execution/rtol","below SciPy tolerance floor","EXECUTION_SPEC")
    end
    environment_keys = julia ? "julia_version scimlbase_version ordinarydiffeqtsit5_version ordinarydiffeqrosenbrock_version json_version" : "python_implementation python_version rfc8785_version numpy_version scipy_version"
    env = _object(backend["environment"],p*"/backend/environment",environment_keys)
    for (key,value) in env
        _string(value,p*"/backend/environment/"*key)
    end
    bev = _object(backend["evaluations"],p*"/backend/evaluations",julia ? "njev nw" : "njev nlu")
    for key in keys(bev)
        bev[key] = _integer(bev[key],p*"/backend/evaluations/"*key)
    end
    skipped = length(e["time_grid"])==1 && first(e["time_grid"])==0.0
    _equal(m["integration"],skipped ? "skipped_zero_grid" : "performed",p*"/integration")
    _need(skipped ? ev["nfev"]==0 : ev["nfev"]>0,p*"/evaluations/nfev","inconsistent integration counter","COUNTERS")
    if skipped
        for (key,value) in bev
            _need(value==0,p*"/backend/evaluations/"*key,"skipped integration requires zero counters","COUNTERS")
        end
    end
    m
end
function _result(raw,m,fir)
    p = "/result"
    r = _object(raw,p,"kind schema_version fir_digest time_unit times state_ids state_units state_values observable_ids observable_state_ids observable_units observable_values")
    for (key,value) in (("kind","ODEResult"),("schema_version","0.1.0"),("fir_digest",fir.digest),("time_unit","s"))
        _equal(r[key],value,p*"/"*key,key=="schema_version" ? "UNSUPPORTED_VERSION" : "IDENTITY")
    end
    model = FIR.to_dict(FIR.normalized(fir.model))
    states,obs = model["states"],model["observables"]
    for (key,expected) in (("state_ids",[s["id"] for s in states]),("state_units",[s["unit"] for s in states]),
        ("observable_ids",[o["id"] for o in obs]),("observable_state_ids",[o["state"] for o in obs]),("observable_units",[o["unit"] for o in obs]))
        values = _array(r[key],p*"/"*key)
        _need(length(values)==length(expected) && all(v isa String && v==e for (v,e) in zip(values,expected)),p*"/"*key,"columns differ from normalized FIR","COLUMNS")
    end
    r["times"] = _grid(r["times"],p*"/times")
    grid = m["execution"]["time_grid"]
    _need(length(r["times"])==length(grid),p*"/times","grid length mismatch","GRID")
    for (i,(a,b)) in enumerate(zip(r["times"],grid))
        _need(_bits(a)==_bits(b),p*"/times/$(i-1)","grid bits differ","GRID")
    end
    for (key,columns) in (("state_values",length(states)),("observable_values",length(obs)))
        rows = _array(r[key],p*"/"*key)
        _need(length(rows)==length(grid),p*"/"*key,"sample count mismatch","DIMENSIONS")
        for (i,row) in enumerate(rows)
            at = p*"/"*key*"/$(i-1)"
            _array(row,at)
            _need(length(row)==columns,at,"column count mismatch","DIMENSIONS")
            rows[i] = Float64[_float(value,at*"/$(j-1)") for (j,value) in enumerate(row)]
        end
    end
    indices = Dict(s["id"]=>i for (i,s) in enumerate(states))
    for (i,time) in enumerate(grid)
        for (j,state) in enumerate(states)
            _need(time!=0.0 || r["state_values"][i][j]==state["initial"],p*"/state_values/$(i-1)/$(j-1)","zero-time sample differs from initial state","INITIAL_STATE")
        end
        for (j,observable) in enumerate(obs)
            value = r["state_values"][i][indices[observable["state"]]]
            _need(_bits(r["observable_values"][i][j])==_bits(value),p*"/observable_values/$(i-1)/$(j-1)","observable bits differ from mapped state","OBSERVABLE")
        end
    end
    r
end
function _record(text,bytes,experiment,fir)
    m = _manifest(_parse(text,"/manifest"),experiment,fir)
    _need(bytes2hex(sha256(bytes))==m["output"]["sha256"],"/manifest/output/sha256","result byte checksum mismatch","CHECKSUM")
    r = _result(_parse(_text(bytes,"/result"),"/result"),m,fir)
    RunRecord(_Validated(),RunManifest(_Validated(),_freeze(m),text),ODEResult(_Validated(),_freeze(r)),String(copy(bytes)))
end
"""Verify exact transport and supplied local sources, without executing an ODE.

Portable limits are exact integers without a native Int cap. Loading preserves
recorded producer/environment observations rather than querying reader versions.
"""
function from_json(::Type{RunRecord},manifest_json,result_bytes;
                   experiment,expected_manifest_sha256=nothing)
    text = _text(manifest_json,"/manifest")
    _need(result_bytes isa Vector{UInt8},"/result","require result UTF-8 byte vector")
    bytes = copy(result_bytes)
    if expected_manifest_sha256 !== nothing
        expected = _checksum(expected_manifest_sha256,"/manifest")
        _need(bytes2hex(sha256(codeunits(text)))==expected,"/manifest","differs from trusted manifest checksum","CHECKSUM")
    end
    _need(experiment isa BioIR.ExperimentDocument,"/manifest/sources","require native committed Experiment","SOURCE_REQUIRED")
    fir = try
        compile_experiment(experiment)
    catch error
        if error isa FIR.FIRValidationError || error isa BioIR.BioIRValidationError
            _fail("/manifest/sources"*error.path,error.message,error.category)
        end
        rethrow()
    end
    _record(text,bytes,experiment,fir)
end

# Ordinary value-preserving transport, deliberately separate from JCS identity.
function _emit(io,value)
    if value === nothing
        write(io,"null")
    elseif value isa Bool
        write(io,value ? "true" : "false")
    elseif value isa Integer
        write(io,string(value))
    elseif value isa Float64
        isfinite(value) || _fail("","cannot serialize nonfinite binary64","NUMBER")
        write(io,string(value))
    elseif value isa String
        write(io,JSON.json(value))
    elseif value isa AbstractDict
        write(io,'{')
        for (i,(key,item)) in enumerate(value)
            i==1 || write(io,',')
            write(io,JSON.json(key),':')
            _emit(io,item)
        end
        write(io,'}')
    elseif value isa Union{Tuple,AbstractVector}
        write(io,'[')
        for (i,item) in enumerate(value)
            i==1 || write(io,',')
            _emit(io,item)
        end
        write(io,']')
    else
        _fail("","unsupported transport value")
    end
end
_emit(value) = (io=IOBuffer(); _emit(io,value); String(take!(io)))
_utc_now() = Dates.now(Dates.UTC)
_monotonic_ns() = time_ns()
_wall_text(value::DateTime) = Dates.format(value,dateformat"yyyy-mm-ddTHH:MM:SS.sss")*"000Z"
function _capture(experiment::BioIR.ExperimentDocument,spec::Execution.ODEExecutionSpec;
                  wall=_utc_now,monotonic=_monotonic_ns,solve=Execution.solve_ode)
    started,start_ns = wall(),monotonic()
    fir = compile_experiment(experiment)
    model = FIR.normalized(fir.model)
    trajectory = solve(model,spec)
    normalized = FIR.to_dict(model)
    result = Dict{String,Any}("kind"=>"ODEResult","schema_version"=>"0.1.0","fir_digest"=>fir.digest,
        "time_unit"=>trajectory.time_unit,"times"=>trajectory.times,"state_ids"=>trajectory.state_ids,
        "state_units"=>trajectory.state_units,"state_values"=>trajectory.state_values,
        "observable_ids"=>trajectory.observable_ids,"observable_state_ids"=>[o["state"] for o in normalized["observables"]],
        "observable_units"=>trajectory.observable_units,"observable_values"=>trajectory.observable_values)
    bytes = Vector{UInt8}(codeunits(_emit(result)))
    checksum = bytes2hex(sha256(bytes))
    finished,finish_ns = wall(),monotonic()
    versions = Dict(trajectory.backend_versions)
    manifest = Dict{String,Any}("kind"=>"RunManifest","schema_version"=>"0.1.0","status"=>"success",
        "repeatability"=>"bounded_numerical_agreement","sources"=>Dict("design"=>_reference(experiment.source_design),"experiment"=>_reference(experiment)),
        "fir"=>Dict("schema_version"=>"0.1.0","canonicalization_version"=>"0.1.0","digest"=>fir.digest),
        "execution"=>Dict("profile"=>spec.profile,"time_grid"=>spec.time_grid,"rtol"=>spec.rtol,"atol"=>spec.atol,"max_step"=>spec.max_step,"max_nfev"=>spec.max_nfev),
        "randomness"=>Dict("rng"=>"none","seed"=>nothing),"evaluations"=>Dict("nfev"=>trajectory.nfev),
        "timing"=>Dict("started_at_utc"=>_wall_text(started),"finished_at_utc"=>_wall_text(finished),"elapsed_seconds"=>Float64(finish_ns-start_ns)/1e9),
        "integration"=>last(spec.time_grid)==0.0 ? "skipped_zero_grid" : "performed",
        "output"=>Dict("schema_version"=>"0.1.0","media_type"=>"application/json","encoding"=>"utf-8","sha256"=>checksum),
        "producer"=>Dict("name"=>"Fenix","version"=>string(pkgversion(parentmodule(@__MODULE__))),"build_id"=>nothing),
        "backend"=>Dict("profile"=>"julia-sciml-ode/0.1.0",
            "solver"=>Dict("name"=>"SciMLBase.solve","method"=>spec.method,"options"=>_julia_options(spec.time_grid)),
            "environment"=>Dict("julia_version"=>versions["julia"],"scimlbase_version"=>versions["SciMLBase"],
                "ordinarydiffeqtsit5_version"=>versions["OrdinaryDiffEqTsit5"],"ordinarydiffeqrosenbrock_version"=>versions["OrdinaryDiffEqRosenbrock"],"json_version"=>string(pkgversion(JSON))),
            "evaluations"=>Dict("njev"=>trajectory.njev,"nw"=>trajectory.nw)))
    _record(_emit(manifest),bytes,experiment,fir)
end
"""Reverify sources, compile, execute once and capture a successful P07 record.

Compiler/solver failures propagate unchanged and produce no successful record.
UTC wall observations have millisecond precision padded to six fractional digits;
elapsed seconds come solely from monotonic observations.
"""
run_experiment(experiment::BioIR.ExperimentDocument,spec::Execution.ODEExecutionSpec)::RunRecord = _capture(experiment,spec)
end # module Results
