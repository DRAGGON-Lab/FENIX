function _kernel(model, spec)
    rates = Dict(key => entry["value"] for (key,entry) in model["parameters"])
    volumes = Dict(key => entry["value"] for (key,entry) in model["volumes"])
    ns, nr = model["populations"]["sender"], model["populations"]["receiver"]
    vs, vr, ve = volumes["sender"], volumes["receiver"], volumes["env"]
    ks, kr = rates["sender_export"], rates["receiver_export"]
    ki_s, ki_r = rates["sender_import"], rates["receiver_import"]
    threshold, exponent = rates["threshold"], Int(rates["hill_n"])
    calls = Ref(0)
    fail(category,message;cause=nothing) =
        throw(Execution.ODEExecutionError(category,spec,calls[],message,cause))
    function domain(u,t)
        isfinite(t) && all(isfinite,u) || fail("NONFINITE","nonfinite internal stage")
        u[1] >= 0 || fail("STAGE_DOMAIN","negative extracellular sensing stage at $t")
        nothing
    end
    function hill(density)
        if density <= threshold
            z = (density/threshold)^exponent
            return z/(1+z)
        end
        1/(1+(threshold/density)^exponent)
    end
    function rhs!(du,u,_,t)
        calls[] < spec.max_nfev || fail("WORK_LIMIT","RHS evaluation budget exhausted")
        calls[] += 1
        domain(u,t)
        e,y,r,s = u
        density = e/ve
        isfinite(density) || fail("NONFINITE","nonfinite sensing density")
        js = ks*s - ki_s*(vs*density)
        jr = kr*r - ki_r*(vr*density)
        du[1] = ns*js + nr*jr - rates["env_decay"]*e
        du[2] = rates["reporter_basal"] + rates["reporter_induced"]*hill(density) - rates["reporter_decay"]*y
        du[3] = -rates["receiver_decay"]*r - jr
        du[4] = rates["sender_production"] - rates["sender_decay"]*s - js
        all(isfinite,du) || fail("NONFINITE","nonfinite RHS arithmetic")
        nothing
    end
    function jac!(matrix,u,_,t)
        domain(u,t)
        e = u[1]
        density = e/ve
        isfinite(density) || fail("NONFINITE","nonfinite sensing density")
        slope = if e != 0
            h = hill(density)
            exponent*h*(1-h)/e
        elseif exponent == 1
            denominator = threshold*ve
            isfinite(denominator) && denominator > 0 || fail("NONFINITE","invalid zero-signal Jacobian denominator")
            1/denominator
        else
            0.0
        end
        isfinite(slope) || fail("NONFINITE","nonfinite sensing derivative")
        si, ri = ki_s*vs/ve, ki_r*vr/ve
        fill!(matrix,0.0)
        matrix[1,1] = -ns*si - nr*ri - rates["env_decay"]
        matrix[1,3] = nr*kr
        matrix[1,4] = ns*ks
        matrix[2,1] = rates["reporter_induced"]*slope
        matrix[2,2] = -rates["reporter_decay"]
        matrix[3,1] = ri
        matrix[3,3] = -rates["receiver_decay"] - kr
        matrix[4,1] = si
        matrix[4,4] = -rates["sender_decay"] - ks
        all(isfinite,matrix) || fail("NONFINITE","nonfinite Jacobian arithmetic")
        nothing
    end
    function tgrad!(gradient,u,_,t)
        domain(u,t)
        fill!(gradient,0.0)
        nothing
    end
    (;rhs!,jac!,tgrad!,calls,fail)
end

solve_ode(fir::FIR,spec::ODEExecutionSpec) = _solve_ode(fir,spec,Execution._sciml_solve)
function _solve_ode(fir::FIR,spec::ODEExecutionSpec,backend)
    model = normalized_model(fir)
    kernel = _kernel(model,spec)
    spec.profile == "ode" || kernel.fail("UNSUPPORTED_PROFILE","M1 supports deterministic ode only")
    initial = Float64[model["initial_counts"][id]["value"] for id in STATES]
    njev,nw = 0,0
    if last(spec.time_grid) == 0
        states = (Tuple(initial),)
    else
        function_value = SciMLBase.ODEFunction{true}(kernel.rhs!; jac=kernel.jac!,tgrad=kernel.tgrad!)
        problem = SciMLBase.ODEProblem(function_value,initial,(0.0,last(spec.time_grid)))
        result = try
            backend(problem,spec)
        catch error
            if error isa SingularException || error isa OverflowError
                kernel.fail("INTEGRATION_FAILURE",sprint(showerror,error);cause=error)
            end
            rethrow()
        end
        SciMLBase.successful_retcode(result.retcode) || kernel.fail("INTEGRATION_FAILURE","backend returned $(result.retcode)")
        length(result.t) == length(spec.time_grid) == length(result.u) ||
            kernel.fail("INCOMPLETE_OUTPUT","backend returned an incomplete grid")
        Tuple(result.t) == spec.time_grid || kernel.fail("INCOMPLETE_OUTPUT","backend returned misaligned times")
        for row in result.u
            length(row) == length(STATES) && all(x -> x isa Float64,row) ||
                kernel.fail("INCOMPLETE_OUTPUT","backend returned invalid state columns")
            all(isfinite,row) || kernel.fail("NONFINITE","nonfinite returned counts")
            all(>=(0),row) || kernel.fail("NEGATIVE_OUTPUT","negative returned counts")
        end
        states = Tuple(Tuple(row) for row in result.u)
        njev,nw = result.stats.njacs,result.stats.nw
    end
    observations = model["observables"]
    columns = _observable_columns(observations)
    observed = Tuple(Tuple(row[i] for i in columns) for row in states)
    (; times=spec.time_grid,state_ids=STATES,state_values=states,
       observable_ids=Tuple(o["id"] for o in observations),observable_values=observed,
       fir_digest=digest(fir),spec,nfev=kernel.calls[],njev,nw)
end
_observable_columns(observations) = [findfirst(==(o["state"]),STATES)::Int for o in observations]
