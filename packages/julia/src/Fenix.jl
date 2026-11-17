module Fenix
include("BioIR.jl")
include("FIR.jl")
include("Compiler.jl")
include("Execution.jl")
include("Results.jl")
export BioIR, FIR, Execution, Results, compile_experiment
end # module Fenix
