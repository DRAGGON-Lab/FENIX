module Fenix
include("BioIR.jl")
include("FIR.jl")
include("Compiler.jl")
include("Execution.jl")
include("Results.jl")
include("Community.jl")
export BioIR, FIR, Execution, Results, Community, compile_experiment
end # module Fenix
