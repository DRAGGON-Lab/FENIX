"""Native P04 M0 execution. Bounded numerical agreement, not bitwise replay.

No clipping, method fallback, analytical substitution or serialized callbacks.
This in-memory trajectory is not a portable P07 result or authenticated manifest.
"""
module Execution
import ..FIR
import SciMLBase
import OrdinaryDiffEqTsit5
import OrdinaryDiffEqRosenbrock
using LinearAlgebra: SingularException
export ExecutionValidationError, ODEExecutionSpec, ODEExecutionError, ODETrajectory, solve_ode

struct ExecutionValidationError <: Exception
    category::String
    path::String
    message::String
end
Base.showerror(io::IO,e::ExecutionValidationError) = print(io,e.category," at ",e.path,": ",e.message)
_invalid(path,message) = throw(ExecutionValidationError("EXECUTION_SPEC",path,message))
"""Explicit local error controls, maximum step in seconds and RHS-call budget.

Times are snapshotted without sorting or coercion. Tolerances are not certified
global error bounds. The budget bounds RHS work, not wall-clock time or memory.
"""
struct ODEExecutionSpec
    time_grid::Tuple{Vararg{Float64}}
    method::String
    rtol::Float64
    atol::Float64
    max_step::Float64
    max_nfev::Int
    profile::String
    function ODEExecutionSpec(;time_grid,method,rtol,atol,max_step,max_nfev,profile="ode")
        (time_grid isa Tuple || time_grid isa AbstractVector) && !isempty(time_grid) ||
            _invalid("/time_grid","require a nonempty tuple or vector of binary64 times")
        previous = -1.0
        for (i,time) in enumerate(time_grid)
            path = "/time_grid/$(i-1)"
            time isa Float64 && isfinite(time) && time >= 0 || _invalid(path,"require finite nonnegative Float64")
            time > previous || _invalid(path,"times must be strictly increasing")
            previous = time
        end
        method isa String && method in ("Tsit5","Rodas5P") ||
            throw(ExecutionValidationError("UNSUPPORTED_METHOD","/method","require Tsit5 or Rodas5P"))
        for (name,value) in (("rtol",rtol),("atol",atol),("max_step",max_step))
            value isa Float64 && isfinite(value) && value > 0 || _invalid("/"*name,"require positive finite Float64")
        end
        max_nfev isa Int && max_nfev > 0 || _invalid("/max_nfev","require positive native Int budget")
        profile isa String || _invalid("/profile","require profile string")
        new(Tuple(time_grid),method,rtol,atol,max_step,max_nfev,profile)
    end
end
struct ODEExecutionError <: Exception
    category::String
    spec::ODEExecutionSpec
    nfev::Int
    message::String
    cause::Union{Nothing,Exception}
end
Base.showerror(io::IO,e::ODEExecutionError) = print(io,e.category," (",e.spec.method,", RHS calls=",e.nfev,"): ",e.message)

"""Immutable sample-major output aligned with declared IDs/units and settings.

Backend versions describe the computation; repeatability means bounded numerical
agreement. Source-linked portable result serialization remains separate work.
"""
struct ODETrajectory
    times::Tuple{Vararg{Float64}}
    state_ids::Tuple{String}
    state_values::Tuple{Vararg{Tuple{Float64}}}
    state_units::Tuple{String}
    observable_ids::Tuple{Vararg{String}}
    observable_values::Tuple{Vararg{Tuple{Vararg{Float64}}}}
    observable_units::Tuple{Vararg{String}}
    time_unit::String
    fir_digest::String
    spec::ODEExecutionSpec
    nfev::Int
    njev::Int
    nw::Int
    backend_versions::Tuple{Vararg{Pair{String,String}}}
end
function _backend_versions()
    ("julia"=>string(VERSION),"SciMLBase"=>string(pkgversion(SciMLBase)),
     "OrdinaryDiffEqTsit5"=>string(pkgversion(OrdinaryDiffEqTsit5)),
     "OrdinaryDiffEqRosenbrock"=>string(pkgversion(OrdinaryDiffEqRosenbrock)))
end
function _sciml_solve(problem,spec)
    algorithm = spec.method == "Tsit5" ? OrdinaryDiffEqTsit5.Tsit5() : OrdinaryDiffEqRosenbrock.Rodas5P()
    SciMLBase.solve(problem,algorithm;
        reltol=spec.rtol,abstol=spec.atol,dtmax=spec.max_step,
        saveat=collect(spec.time_grid),save_start=first(spec.time_grid)==0.0,
        save_end=true,save_everystep=false,dense=false,
        adaptive=true,dt=nothing,force_dtmin=false,
        # RHS counting enforces the requested work bound; no smaller hidden
        # iteration limit should preempt it. No callbacks or automatic switches.
        maxiters=typemax(Int),callback=nothing)
end
function _solve_ode(model::FIR.FIRModel,spec::ODEExecutionSpec,backend)
    FIR.require_capability(model,spec.profile)
    data = FIR.to_dict(model)
    parameters = Dict(p["id"]=>p["value"] for p in data["parameters"])
    state = only(s for s in data["states"] if s["id"]=="x")
    alpha,beta,x0 = parameters["alpha"],parameters["beta"],state["initial"]
    calls = Ref(0)
    fail(category,message;cause=nothing) = throw(ODEExecutionError(category,spec,calls[],message,cause))
    function rhs!(du,u,p,t)
        calls[] < spec.max_nfev || fail("WORK_LIMIT","RHS evaluation budget exhausted")
        calls[] += 1
        value = alpha-beta*u[1]
        isfinite(value) || fail("NONFINITE","nonfinite RHS arithmetic")
        du[1] = value
        nothing
    end
    # Exact autonomous Jacobian/time derivative avoid numerical differentiation.
    jac!(J,u,p,t) = (J[1,1] = -beta; nothing)
    tgrad!(out,u,p,t) = (out[1] = 0.0; nothing)
    samples = (x0,)
    njev,nw = 0,0
    if last(spec.time_grid) != 0.0
        function_value = SciMLBase.ODEFunction{true}(rhs!;jac=jac!,tgrad=tgrad!)
        problem = SciMLBase.ODEProblem(function_value,[x0],(0.0,last(spec.time_grid)))
        result = try
            backend(problem,spec)
        catch error
            error isa ODEExecutionError && rethrow()
            if error isa SingularException || error isa OverflowError
                fail("SOLVER_FAILURE",sprint(showerror,error);cause=error)
            end
            rethrow() # programming errors must remain visible
        end
        SciMLBase.successful_retcode(result.retcode) || fail("SOLVER_FAILURE","backend returned $(result.retcode)")
        result.t isa AbstractVector && result.u isa AbstractVector ||
            fail("INVALID_OUTPUT","expected sampled time and state collections")
        length(result.t)==length(spec.time_grid) && length(result.u)==length(spec.time_grid) ||
            fail("INVALID_OUTPUT","incomplete sampled grid")
        for (i,time) in enumerate(result.t)
            time isa Float64 && time==spec.time_grid[i] || fail("INVALID_OUTPUT","misaligned sampled times")
            row = result.u[i]
            row isa AbstractVector && length(row)==1 && row[1] isa Float64 || fail("INVALID_OUTPUT","expected one binary64 state per requested time")
            isfinite(row[1]) || fail("NONFINITE","nonfinite sampled output")
            row[1] >= 0 || fail("NEGATIVE_STATE","negative sampled count; no clipping is permitted")
        end
        samples = Tuple(row[1] for row in result.u)
        njev,nw = result.stats.njacs,result.stats.nw
    end
    observables = data["observables"]
    ODETrajectory(spec.time_grid,("x",),Tuple((x,) for x in samples),(state["unit"],),
        Tuple(o["id"] for o in observables),Tuple(Tuple(x for _ in observables) for x in samples),
        Tuple(o["unit"] for o in observables),data["time_unit"],model.digest,spec,calls[],njev,nw,_backend_versions())
end
"""Execute validated M0 FIR from t=0 at exact requested times through SciML.

A mathematically admissible finite model can fail numerically. Every negative
sample fails, however small; ordinary floating-point underflow is permitted.
"""
solve_ode(model::FIR.FIRModel,spec::ODEExecutionSpec) = _solve_ode(model,spec,_sciml_solve)
end # module Execution
