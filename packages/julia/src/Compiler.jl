# Native M0 producer: biological names remain provenance; function roles select
# mathematical parameters. No solver or stochastic profile is implemented here.
export compile_experiment

function _verified_sources(design::BioIR.DesignDocument, experiment::BioIR.ExperimentDocument)
    verified_design = BioIR.from_json(BioIR.DesignDocument, BioIR.to_json(design);
        expected_digest=design.digest)
    verified_experiment = BioIR.from_json(BioIR.ExperimentDocument, BioIR.to_json(experiment);
        designs=(verified_design,), expected_digest=experiment.digest)
    verified_design, verified_experiment
end
_source_require(ok, category, path, message) = ok || throw(FIR.FIRValidationError(category, path, message))

"""Check P02 producer correspondence against both exact, verified P01 sources.

Standalone FIR may omit provenance. Source-aware validation requires complete
producer provenance, and never supplies missing mathematical values.
"""
function FIR.validate_sources(document::FIR.FIRDocument; design, experiment)
    _source_require(design isa BioIR.DesignDocument, "SOURCE_REQUIRED", "/design", "expected native committed Design")
    _source_require(experiment isa BioIR.ExperimentDocument, "SOURCE_REQUIRED", "/experiment", "expected native committed Experiment")
    verified_design, verified_experiment = _verified_sources(design, experiment)
    raw = FIR.to_dict(document)
    _source_require(haskey(raw, "provenance"), "SOURCE_REQUIRED", "/provenance", "producer provenance is required")
    provenance = raw["provenance"]
    for field in ("design_digest", "experiment_digest", "symbol_map")
        _source_require(haskey(provenance, field), "SOURCE_REQUIRED", "/provenance/" * field, "required producer field")
    end
    for (field, source) in (("design_digest", verified_design), ("experiment_digest", verified_experiment))
        _source_require(provenance[field] == source.digest, "SOURCE_DIGEST", "/provenance/" * field, "source digest differs from verified document")
    end
    d, e, model = verified_design.content, verified_experiment.content, raw["model"]
    state_map = only(provenance["symbol_map"]["states"])
    path = "/provenance/symbol_map/states/0"
    species = Dict(item.id => item for item in d.species)
    _source_require(haskey(species, state_map["bioir_species_id"]), "REFERENCE", path * "/bioir_species_id", "unknown source species")
    source_species = species[state_map["bioir_species_id"]]
    ports = Dict(item.id => item for item in source_species.ports)
    _source_require(haskey(ports, state_map["bioir_port_id"]), "REFERENCE", path * "/bioir_port_id", "unknown species-scoped source port")
    _source_require(source_species.compartment == state_map["bioir_compartment_id"] &&
        any(item.id == state_map["bioir_compartment_id"] for item in d.compartments),
        "REFERENCE", path * "/bioir_compartment_id", "source compartment differs from species")
    source_parameters = Dict(item.id => item for item in d.parameters)
    functions = Dict(item.id => item for item in d.functions)
    assignments = Dict(item.parameter => item.quantity for item in e.parameters)
    fir_parameters = Dict(item["id"] => (i, item) for (i, item) in enumerate(model["parameters"]))
    for (i, entry) in enumerate(provenance["symbol_map"]["parameters"])
        path = "/provenance/symbol_map/parameters/$(i-1)"
        parameter_id, function_id = entry["bioir_parameter_id"], entry["bioir_function_id"]
        _source_require(haskey(source_parameters, parameter_id), "REFERENCE", path * "/bioir_parameter_id", "unknown source parameter")
        _source_require(haskey(functions, function_id), "REFERENCE", path * "/bioir_function_id", "unknown source function")
        function_value = functions[function_id]
        kind = entry["fir_parameter_id"] == "alpha" ? "constitutive_production" : "first_order_decay"
        _source_require(function_value.kind == kind && function_value.parameter == parameter_id &&
            function_value.target.species == source_species.id && function_value.target.port == state_map["bioir_port_id"],
            "SOURCE_ROLE", path * "/bioir_function_id", "source function has wrong parameter, role or target")
        _source_require(entry["bioir_function_kind"] == function_value.kind, "SOURCE_ROLE", path * "/bioir_function_kind", "source function kind differs")
        j, target = fir_parameters[entry["fir_parameter_id"]]
        assignment = assignments[parameter_id]
        _source_require(target["unit"] == assignment.unit == source_parameters[parameter_id].unit,
            "UNIT", "/model/parameters/$(j-1)/unit", "parameter unit differs from source")
        _source_require(target["value"] == assignment.value, "SOURCE_VALUE", "/model/parameters/$(j-1)/value", "parameter value differs from source")
    end
    initial = only(item.quantity for item in e.initial_counts if item.species == source_species.id)
    state = only(model["states"])
    _source_require(state["initial"] == initial.value, "SOURCE_VALUE", "/model/states/0/initial", "initial count differs from source")
    _source_require(state["unit"] == initial.unit, "UNIT", "/model/states/0/unit", "initial-count unit differs from source")
    source_observables = Dict(item.id => item for item in e.observables)
    for (i, observable) in enumerate(model["observables"])
        path = "/model/observables/$(i-1)"
        _source_require(haskey(source_observables, observable["id"]), "SOURCE_OBSERVABLE", path * "/id", "observable is absent from source")
        source = source_observables[observable["id"]]
        _source_require(source.target.species == source_species.id && source.target.port == state_map["bioir_port_id"] &&
            observable["state"] == state_map["fir_state_id"], "SOURCE_OBSERVABLE", path * "/state", "observable source target differs")
        _source_require(observable["unit"] == state["unit"] == "molecule" && ports[source.target.port].kind == "molecular_count",
            "UNIT", path * "/unit", "observable unit differs from mapped count port")
    end
    _source_require(Set(item["id"] for item in model["observables"]) == Set(keys(source_observables)),
        "SOURCE_OBSERVABLE", "/model/observables", "observables must exhaustively match source")
    document
end

"""Compile one verified native M0 Experiment into immutable mathematical FIR.

Function roles determine alpha/beta; source names, declaration order and fixed
cell volume introduce no change to represented molecular-count mathematics.
"""
function compile_experiment(experiment::BioIR.ExperimentDocument)::FIR.FIRDocument
    design, verified = _verified_sources(experiment.source_design, experiment)
    source, scenario = design.content, verified.content
    species = only(source.species)
    functions = Dict(item.kind => item for item in source.functions)
    assignments = Dict(item.parameter => item.quantity for item in scenario.parameters)
    initial = only(item.quantity for item in scenario.initial_counts if item.species == species.id)
    parameter_map = Any[]
    parameters = Any[]
    for (id, kind) in (("alpha", "constitutive_production"), ("beta", "first_order_decay"))
        function_value = functions[kind]
        quantity = assignments[function_value.parameter]
        push!(parameters, Dict("id" => id, "value" => Float64(quantity.value), "unit" => quantity.unit))
        push!(parameter_map, Dict("fir_parameter_id" => id,
            "bioir_parameter_id" => function_value.parameter, "bioir_function_id" => function_value.id,
            "bioir_function_kind" => function_value.kind))
    end
    alpha = Dict("op" => "parameter", "id" => "alpha")
    decay = Dict("op" => "multiply", "left" => Dict("op" => "parameter", "id" => "beta"),
        "right" => Dict("op" => "state", "id" => "x"))
    model = Dict("schema_version" => "0.1.0", "time_unit" => "s",
        "states" => [Dict("id" => "x", "quantity" => "molecular_count", "scope" => "representative_cell", "unit" => initial.unit, "initial" => Float64(initial.value))],
        "parameters" => parameters,
        "reactions" => [Dict("id" => "production", "stoichiometry" => Dict("x" => 1.0), "flux" => alpha),
                        Dict("id" => "decay", "stoichiometry" => Dict("x" => -1.0), "flux" => decay)],
        "equations" => [Dict("state" => "x", "unit" => "molecule/s", "rhs" => Dict("op" => "subtract", "left" => alpha, "right" => decay))],
        "observables" => [Dict("id" => item.id, "state" => "x", "unit" => "molecule") for item in scenario.observables],
        "assumptions" => ["single_representative_cell", "well_mixed", "fixed_volume", "constant_rates", "no_interventions"],
        "capabilities" => Dict("ode" => true, "ssa" => false))
    provenance = Dict("design_digest" => design.digest, "experiment_digest" => verified.digest,
        "compiler" => Dict("name" => "Fenix", "version" => string(pkgversion(@__MODULE__))),
        "symbol_map" => Dict("states" => [Dict("fir_state_id" => "x", "bioir_species_id" => species.id,
            "bioir_port_id" => only(species.ports).id, "bioir_compartment_id" => species.compartment)], "parameters" => parameter_map))
    document = FIR.FIRDocument(model=FIR.FIRModel(model), provenance=provenance)
    FIR.validate_sources(document; design=design, experiment=verified)
end
