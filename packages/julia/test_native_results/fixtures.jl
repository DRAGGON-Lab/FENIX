# Fixed source selection only; no numerical expectations generated here.
const EXAMPLES = joinpath(ROOT,"spec/results/proposals/examples")
const JULIA_EXAMPLES = joinpath(ROOT,"spec/results/proposals/julia-examples")
const EXAMPLE_NAMES = ("late-first","zero-only","empty-observables","multi-observables")
function example_experiment(name)
    d = B.from_json(B.DesignDocument,read(joinpath(ROOT,"spec/bioir/proposals/examples/design.json")))
    path = name == "empty-observables" ? joinpath(ROOT,"spec/fir/proposals/examples/sources/no-observables-experiment.json") :
        name == "multi-observables" ? joinpath(EXAMPLES,"multi-observables.experiment.json") :
        joinpath(ROOT,"spec/bioir/proposals/examples/experiment.json")
    B.from_json(B.ExperimentDocument,read(path);designs=(d,))
end
