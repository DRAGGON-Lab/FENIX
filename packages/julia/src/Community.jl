"""Native P08 deterministic fixed-population exchange and sensing."""
module Community
using SHA, Dates
import JSON
import ..BioIR, ..Execution, ..Results
import ..Execution: ODEExecutionSpec
import SciMLBase
using LinearAlgebra: SingularException

export Design, Experiment, FIR, ODEResult, RunManifest, RunRecord, ValidationError,
       ODEExecutionSpec, from_content, replace_content, from_json, to_dict, to_json,
       digest, reference, model_bytes, identity_bytes, compile_experiment,
       solve_ode, run_experiment, result_bytes, manifest_bytes

include("community/wire.jl")
include("community/documents.jl")
include("community/execution.jl")
include("community/results.jl")
end
