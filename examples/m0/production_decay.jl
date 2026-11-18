"""Standalone native authoring, capture and verified readback under P01–P04/P07."""
module M0Example
using Fenix
using Fenix.BioIR
using Fenix.Execution: ODEExecutionSpec
using SHA
using JSON

const CASES = Dict(
    "baseline-five" => (10.0, 0.1, 5.0, (0.0, 1.0, 10.0, 100.0)),
    "linear-production" => (2.0, 0.0, 0.5, (0.0, 0.5, 1.0, 10.0)),
)
const METHODS = ("Tsit5", "Rodas5P")

function build_experiment(case)
    alpha, beta, x0, _ = CASES[case]
    target = PortReference(species="GFP", port="amount")
    design = DesignDocument(content=DesignContent(
        id="production_decay_GFP", revision=1,
        compartments=(Compartment(id="cell", volume=Quantity(value=1e-15, unit="L")),),
        species=(Species(id="GFP", compartment="cell", ports=(Port(id="amount"),)),),
        parameters=(Parameter(id="alpha", unit="molecule/s"), Parameter(id="beta", unit="1/s")),
        functions=(
            BioIRFunction(id="production", kind="constitutive_production", target=target, parameter="alpha"),
            BioIRFunction(id="decay", kind="first_order_decay", target=target, parameter="beta"),
        ),
    ))
    ExperimentDocument(content=ExperimentContent(
        id="ode_" * case, revision=1, design=BioIR.reference(design), source_design=design.content,
        parameters=(
            ParameterAssignment(parameter="alpha", quantity=Quantity(value=alpha, unit="molecule/s")),
            ParameterAssignment(parameter="beta", quantity=Quantity(value=beta, unit="1/s")),
        ),
        initial_counts=(InitialCount(species="GFP", quantity=Quantity(value=x0, unit="molecule")),),
        observables=(Observable(id="amount", target=target),), interventions=(),
    ), source_design=design)
end

execution_settings(case, method) = ODEExecutionSpec(
    time_grid=CASES[case][4], method=method,
    rtol=1e-10, atol=1e-12, max_step=1.0, max_nfev=100000,
)

function save_run(experiment, spec, output_dir)
    mkpath(output_dir)
    design = experiment.source_design
    fir = Fenix.compile_experiment(experiment)
    record = Fenix.Results.run_experiment(experiment, spec)
    raw(text) = Vector{UInt8}(codeunits(text))
    artifacts = Dict(
        "design.json" => raw(BioIR.to_json(design)),
        "experiment.json" => raw(BioIR.to_json(experiment)),
        "design.canonical.json" => BioIR.canonical_content_bytes(design),
        "experiment.canonical.json" => BioIR.canonical_content_bytes(experiment),
        "fir.json" => raw(FIR.to_json(fir)),
        "model.canonical.json" => FIR.canonical_model_bytes(fir),
        "identity.canonical.json" => FIR.identity_bytes(fir),
        "result.json" => record.result_bytes,
        "manifest.json" => raw(Fenix.Results.to_json(record.manifest)),
    )
    for (name, bytes) in artifacts
        write(joinpath(output_dir, name), bytes)
    end
    loaded_design = BioIR.from_json(DesignDocument, read(joinpath(output_dir, "design.json"), String))
    loaded_experiment = BioIR.from_json(ExperimentDocument,
        read(joinpath(output_dir, "experiment.json"), String); designs=[loaded_design])
    loaded = Fenix.Results.from_json(Fenix.Results.RunRecord,
        read(joinpath(output_dir, "manifest.json"), String),
        read(joinpath(output_dir, "result.json")); experiment=loaded_experiment)
    loaded.result_bytes == record.result_bytes || error("Saved result readback changed bytes")
    summary = Dict(
        "format" => "m0-example-v1", "language" => "julia",
        "case_id" => replace(experiment.content.id, r"^ode_" => ""),
        "method" => spec.method, "design_digest" => design.digest,
        "experiment_digest" => experiment.digest, "fir_digest" => fir.digest,
        "package_path" => realpath(pathof(Fenix)),
        "checksums" => Dict(name => bytes2hex(sha256(bytes)) for (name, bytes) in artifacts),
    )
    write(joinpath(output_dir, "summary.json"), JSON.json(summary) * "\n")
    record
end

function main(args=ARGS)
    options = Dict("--case" => "baseline-five", "--method" => "Tsit5")
    iseven(length(args)) || error("Expected --case NAME --method METHOD --output-dir PATH")
    for i in 1:2:length(args)
        args[i] in ("--case", "--method", "--output-dir") || error("Unknown option: " * args[i])
        options[args[i]] = args[i+1]
    end
    haskey(options, "--output-dir") || error("--output-dir is required")
    haskey(CASES, options["--case"]) || error("Unknown case")
    options["--method"] in METHODS || error("Unknown method")
    save_run(build_experiment(options["--case"]),
             execution_settings(options["--case"], options["--method"]), options["--output-dir"])
end
end # module

if abspath(PROGRAM_FILE) == @__FILE__
    M0Example.main()
end
