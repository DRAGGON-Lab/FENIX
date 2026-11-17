module Fenix
include("BioIR.jl")
include("FIR.jl")
include("Compiler.jl")
include("Execution.jl")
export BioIR, FIR, Execution, compile_experiment
end # module Fenix
