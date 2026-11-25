"""Author, execute and verify the ratified M0 production–decay example.

Standalone: this file needs only an installed fenix package and its runtime dependencies.
"""

import argparse
import hashlib
import json
from pathlib import Path

import fenix
from fenix.bioir import (
    Compartment,
    DesignContent,
    DesignDocument,
    ExperimentContent,
    ExperimentDocument,
    Function,
    InitialCount,
    Observable,
    Parameter,
    ParameterAssignment,
    Port,
    PortReference,
    Quantity,
    Species,
)
from fenix.compiler import compile_experiment
from fenix.execution import ODEExecutionSpec
from fenix.results import RunRecord, run_experiment

# Exact binary64 inputs and grids from the APPROVED production–decay catalog.
CASES = {
    "baseline-five": (10.0, 0.1, 5.0, (0.0, 1.0, 10.0, 100.0)),
    "linear-production": (2.0, 0.0, 0.5, (0.0, 0.5, 1.0, 10.0)),
}
METHODS = ("DOP853", "Radau")


def build_experiment(case):
    """Commit independently authored native content with exact Design references."""
    alpha, beta, x0, _ = CASES[case]
    target = PortReference(species="GFP", port="amount")
    design = DesignDocument(
        content=DesignContent(
            id="production_decay_GFP",
            revision=1,
            compartments=(
                Compartment(id="cell", volume=Quantity(value=1e-15, unit="L")),
            ),
            species=(
                Species(id="GFP", compartment="cell", ports=(Port(id="amount"),)),
            ),
            parameters=(
                Parameter(id="alpha", unit="molecule/s"),
                Parameter(id="beta", unit="1/s"),
            ),
            functions=(
                Function(
                    id="production",
                    kind="constitutive_production",
                    target=target,
                    parameter="alpha",
                ),
                Function(
                    id="decay",
                    kind="first_order_decay",
                    target=target,
                    parameter="beta",
                ),
            ),
        )
    )
    return ExperimentDocument(
        content=ExperimentContent(
            id="ode_" + case,
            revision=1,
            design=design.reference,
            source_design=design.content,
            parameters=(
                ParameterAssignment(
                    parameter="alpha", quantity=Quantity(value=alpha, unit="molecule/s")
                ),
                ParameterAssignment(
                    parameter="beta", quantity=Quantity(value=beta, unit="1/s")
                ),
            ),
            initial_counts=(
                InitialCount(
                    species="GFP", quantity=Quantity(value=x0, unit="molecule")
                ),
            ),
            observables=(Observable(id="amount", target=target),),
            interventions=(),
        ),
        source_design=design,
    )


def execution_settings(case, method):
    return ODEExecutionSpec(
        time_grid=CASES[case][3],
        method=method,
        rtol=1e-10,
        atol=1e-12,
        max_step=1.0,
        max_nfev=100000,
    )


def save_run(experiment, spec, output_dir):
    """Capture, persist and independently reload the exact saved bytes."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    design = experiment.source_design
    fir = compile_experiment(experiment)
    record = run_experiment(experiment, spec)
    artifacts = {
        "design.json": design.to_json().encode(),
        "experiment.json": experiment.to_json().encode(),
        "design.canonical.json": design.canonical_content_bytes(),
        "experiment.canonical.json": experiment.canonical_content_bytes(),
        "fir.json": fir.to_json().encode(),
        "model.canonical.json": fir.model.canonical_model_bytes(),
        "identity.canonical.json": fir.model.identity_bytes(),
        "result.json": record.result_bytes,
        "manifest.json": record.manifest.to_json().encode(),
    }
    for name, raw in artifacts.items():
        (output / name).write_bytes(raw)
    loaded_design = DesignDocument.from_json((output / "design.json").read_bytes())
    loaded_experiment = ExperimentDocument.from_json(
        (output / "experiment.json").read_bytes(), designs=(loaded_design,)
    )
    loaded = RunRecord.from_json(
        (output / "manifest.json").read_bytes(),
        (output / "result.json").read_bytes(),
        experiment=loaded_experiment,
    )
    if loaded.result_bytes != record.result_bytes:
        raise ValueError("Saved result readback changed bytes")
    summary = {
        "format": "m0-example-v1",
        "language": "python",
        "case_id": experiment.content.id.removeprefix("ode_"),
        "method": spec.method,
        "design_digest": design.digest,
        "experiment_digest": experiment.digest,
        "fir_digest": fir.digest,
        "package_path": str(Path(fenix.__file__).resolve()),
        "checksums": {
            name: hashlib.sha256(raw).hexdigest() for name, raw in artifacts.items()
        },
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASES, default="baseline-five")
    parser.add_argument("--method", choices=METHODS, default="DOP853")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    save_run(
        build_experiment(args.case),
        execution_settings(args.case, args.method),
        args.output_dir,
    )


if __name__ == "__main__":
    main()
