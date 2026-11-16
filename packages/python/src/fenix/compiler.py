"""Native BioIR-to-FIR compilation for the ratified M0 production/decay subset."""

from __future__ import annotations

from . import __version__
from .bioir import BioIRValidationError, DesignDocument, ExperimentDocument
from .fir import FIRDocument, FIRValidationError


def compile_experiment(experiment: ExperimentDocument) -> FIRDocument:
    """Resolve one verified Experiment into immutable P02 mathematics.

    Only constitutive production and first-order decay of P01's one molecular
    species are supported. Function kinds define parameter roles; source names
    and declaration positions do not. No units are converted, cell-volume factor
    introduced, observable invented, or execution configuration selected.

    Source metadata does not enter the FIR model or compiler provenance. Verified
    document identity establishes self-consistency, not researcher authorization.
    """
    if type(experiment) is not ExperimentDocument:
        raise FIRValidationError(
            "SCHEMA", "/experiment", "expected a verified native ExperimentDocument"
        )

    # Recheck both exact document identities at the compiler boundary. This uses
    # P01 ingestion, never P03's more permissive large-integer token policy.
    source = experiment.source_design
    try:
        design = DesignDocument.from_json(
            source.to_json(), expected_digest=source.digest
        )
    except BioIRValidationError as error:
        raise FIRValidationError(
            error.category, "/design" + error.path, str(error)
        ) from error
    try:
        scenario = ExperimentDocument.from_json(
            experiment.to_json(), designs=(design,), expected_digest=experiment.digest
        )
    except BioIRValidationError as error:
        raise FIRValidationError(
            error.category, "/experiment" + error.path, str(error)
        ) from error

    d, e = design.content, scenario.content
    species = d.species[0]
    port = species.ports[0]
    functions = {function.kind: function for function in d.functions}
    production = functions["constitutive_production"]
    decay = functions["first_order_decay"]
    assignments = {item.parameter: item.quantity for item in e.parameters}
    initial = {item.species: item.quantity for item in e.initial_counts}[species.id]

    alpha = {"op": "parameter", "id": "alpha"}
    decay_flux = {
        "op": "multiply",
        "left": {"op": "parameter", "id": "beta"},
        "right": {"op": "state", "id": "x"},
    }
    model: dict[str, object] = {
        "schema_version": "0.1.0",
        "time_unit": "s",
        "states": [
            {
                "id": "x",
                "quantity": "molecular_count",
                "scope": "representative_cell",
                "unit": "molecule",
                "initial": float(initial.value),
            }
        ],
        "parameters": [
            {
                "id": "alpha",
                "value": float(assignments[production.parameter].value),
                "unit": "molecule/s",
            },
            {
                "id": "beta",
                "value": float(assignments[decay.parameter].value),
                "unit": "1/s",
            },
        ],
        "reactions": [
            {"id": "production", "stoichiometry": {"x": 1.0}, "flux": alpha},
            {"id": "decay", "stoichiometry": {"x": -1.0}, "flux": decay_flux},
        ],
        "equations": [
            {
                "state": "x",
                "unit": "molecule/s",
                "rhs": {"op": "subtract", "left": alpha, "right": decay_flux},
            }
        ],
        "observables": [
            {"id": item.id, "state": "x", "unit": "molecule"} for item in e.observables
        ],
        "assumptions": [
            "single_representative_cell",
            "well_mixed",
            "fixed_volume",
            "constant_rates",
            "no_interventions",
        ],
        "capabilities": {"ode": True, "ssa": False},
    }
    provenance = {
        "design_digest": design.digest,
        "experiment_digest": scenario.digest,
        "compiler": {"name": "fenix-bio", "version": __version__},
        "symbol_map": {
            "states": [
                {
                    "fir_state_id": "x",
                    "bioir_species_id": species.id,
                    "bioir_port_id": port.id,
                    "bioir_compartment_id": species.compartment,
                }
            ],
            "parameters": [
                {
                    "fir_parameter_id": symbol,
                    "bioir_parameter_id": function.parameter,
                    "bioir_function_id": function.id,
                    "bioir_function_kind": function.kind,
                }
                for symbol, function in (("alpha", production), ("beta", decay))
            ],
        },
    }
    # Complete producer/source checks are separate from mathematical validity.
    # They cannot supply missing model fields or repair the generated payload.
    return FIRDocument.from_dict(
        {"model": model, "provenance": provenance}, design=design, experiment=scenario
    )
