# This runs in a fresh Julia process: replacing solver methods cannot contaminate
# capture tests or leave a trap disabled by test ordering/world-age effects.
using Test, Fenix
const B = Fenix.BioIR
const R = Fenix.Results
const ROOT = normpath(joinpath(@__DIR__,"../../.."))
include("fixtures.jl")
function Fenix.Execution.solve_ode(model::Fenix.FIR.FIRModel,spec::Fenix.Execution.ODEExecutionSpec)
    error("readback entered solve_ode")
end
Fenix.Execution._sciml_solve(problem,spec) = error("readback entered SciML adapter")
@testset "Readback with every native solver entry trapped" begin
    for directory in (EXAMPLES,JULIA_EXAMPLES), name in EXAMPLE_NAMES
        record = R.from_json(R.RunRecord,read(joinpath(directory,name*".manifest.json")),
            read(joinpath(EXAMPLES,name*".result.json"));experiment=example_experiment(name))
        @test record isa R.RunRecord
    end
end
