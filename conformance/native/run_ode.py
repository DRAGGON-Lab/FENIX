"""Native Python committed-source ODE producer; expectations are external artifacts."""

import argparse
import json
import platform
from importlib.metadata import version
from pathlib import Path

import fenix
from common import ROOT, blob, compare_bytes, read_report, report_destination
from fenix.bioir import (
    BioIRValidationError,
    DesignDocument,
    ExperimentContent,
    ExperimentDocument,
    InitialCount,
    Observable,
    ParameterAssignment,
    PortReference,
    Quantity,
)
from fenix.compiler import compile_experiment
from fenix.execution import ODEExecutionError, ODEExecutionSpec, solve_ode
from fenix.fir import FIRValidationError
from ode_common import (
    bits,
    decode,
    ode_fingerprints,
    validate_ode_report,
    validate_references,
)


def author(design, case, *, invalid_unit=False):
    functions = {f.kind: f for f in design.content.functions}
    species = design.content.species[0]
    assignments = tuple(
        ParameterAssignment(
            parameter=functions[kind].parameter,
            quantity=Quantity(value=decode(case["parameters"][parameter]), unit=unit),
        )
        for kind, parameter, unit in (
            (
                "constitutive_production",
                "alpha",
                "1/s" if invalid_unit else "molecule/s",
            ),
            ("first_order_decay", "beta", "1/s"),
        )
    )
    content = ExperimentContent(
        id="ode_" + case["id"],
        revision=1,
        design=design.reference,
        source_design=design.content,
        parameters=assignments,
        initial_counts=(
            InitialCount(
                species=species.id,
                quantity=Quantity(
                    value=decode(case["parameters"]["x0"]), unit="molecule"
                ),
            ),
        ),
        observables=(
            Observable(
                id="amount",
                target=PortReference(species=species.id, port=species.ports[0].id),
            ),
        ),
        interventions=(),
    )
    return ExperimentDocument(content=content, source_design=design)


def artifacts(design, experiment, compiled):
    for label, source in (("design", design), ("experiment", experiment)):
        if source.digest != blob(source.canonical_content_bytes())["sha256"]:
            raise ValueError(
                "Native " + label + " digest differs from canonical content hash"
            )
    identity = compiled.model.identity_bytes()
    if compiled.digest != blob(identity)["sha256"]:
        raise ValueError("Native FIR digest does not match native identity bytes")
    return {
        "design": blob(design.canonical_content_bytes()),
        "experiment": blob(experiment.canonical_content_bytes()),
        "model": blob(compiled.model.canonical_model_bytes()),
        "identity": blob(identity),
    }


def settings(study, grid, method, **changes):
    args = {
        "time_grid": tuple(grid),
        "method": method,
        "rtol": decode(study["rtol_bits"]),
        "atol": decode(study["atol_bits"]),
        "max_step": decode(study["max_step_bits"]),
        "max_nfev": study["max_nfev"],
    }
    args.update(changes)
    return ODEExecutionSpec(**args)


def controls(design, case, compiled, baseline):
    rows = []
    for method in ("DOP853", "Radau"):
        operations = (
            ("unit-rejection", lambda: author(design, case, invalid_unit=True)),
            (
                "unsupported-profile",
                lambda method=method: solve_ode(
                    compiled.model, settings(baseline, (0.0,), method, profile="ssa")
                ),
            ),
            (
                "work-limit",
                lambda method=method: solve_ode(
                    compiled.model, settings(baseline, (0.0, 1.0), method, max_nfev=1)
                ),
            ),
        )
        for name, operation in operations:
            try:
                operation()
                row = {
                    "id": name,
                    "method": method,
                    "outcome": "accept",
                    "category": "",
                    "path": "",
                    "nfev": 0,
                }
            except (
                BioIRValidationError,
                FIRValidationError,
                ODEExecutionError,
            ) as error:
                row = {
                    "id": name,
                    "method": method,
                    "outcome": "reject",
                    "category": error.category,
                    "path": getattr(error, "path", ""),
                    "nfev": getattr(error, "nfev", 0),
                }
            rows.append(row)
    return rows


def produce(references, revision):
    if (
        Path(fenix.__file__).resolve()
        != (ROOT / "packages/python/src/fenix/__init__.py").resolve()
    ):
        raise ValueError(
            "Installed fenix does not resolve to fingerprinted checkout sources"
        )
    validate_references(references, revision)
    design = DesignDocument.from_json(
        (ROOT / "spec/fir/proposals/examples/sources/gfp-design.json").read_bytes()
    )
    report = {
        "format": "native-ode-report-v1",
        "implementation": "python",
        "source_revision": revision,
        "fingerprints": ode_fingerprints(),
        "runtime": {
            "name": "CPython",
            "version": platform.python_version(),
            "os": platform.system(),
            "arch": platform.machine(),
            "dependencies": {
                p: version(p)
                for p in ("fenix-bio", "rfc8785", "numpy", "scipy", "jsonschema")
            },
        },
        "scenarios": [],
        "runs": [],
        "controls": [],
        "failures": [],
    }
    for case in references["scenarios"]:
        experiment = author(design, case)
        compiled = compile_experiment(experiment)
        compiled.validate_sources(design, experiment)
        before = artifacts(design, experiment, compiled)
        for name, expected in case["artifacts"].items():
            compare_bytes(
                case["id"] + "/" + name,
                bytes.fromhex(expected["hex"]),
                bytes.fromhex(before[name]["hex"]),
            )
        parameters = {p["id"]: p for p in compiled.model.to_dict()["parameters"]}
        for name in ("alpha", "beta"):
            if bits(parameters[name]["value"]) != case["parameters"][name]:
                raise ValueError(case["id"] + ": represented parameter bits changed")
        if (
            bits(compiled.model.to_dict()["states"][0]["initial"])
            != case["parameters"]["x0"]
        ):
            raise ValueError(case["id"] + ": represented initial bits changed")
        for method in ("DOP853", "Radau"):
            for study, local in references["studies"].items():
                grid = tuple(decode(sample["time_bits"]) for sample in case["samples"])
                try:
                    trajectory = solve_ode(
                        compiled.model, settings(local, grid, method)
                    )
                except ODEExecutionError as error:
                    report["failures"].append(
                        {
                            "case_id": case["id"],
                            "method": method,
                            "study": study,
                            "category": error.category,
                            "message": str(error),
                            "nfev": error.nfev,
                        }
                    )
                    report["scenarios"].append(
                        {
                            "id": case["id"],
                            "artifacts": before,
                            "after_artifacts": artifacts(design, experiment, compiled),
                        }
                    )
                    return report
                if dict(trajectory.backend_versions) != {
                    p: version(p) for p in ("numpy", "scipy")
                }:
                    raise ValueError("Native backend version identity mismatch")
                if (
                    trajectory.state_ids != ("x",)
                    or trajectory.state_units != ("molecule",)
                    or trajectory.observable_ids != ("amount",)
                    or trajectory.observable_units != ("molecule",)
                    or trajectory.time_unit != "s"
                ):
                    raise ValueError("Incorrect native state/observable IDs or units")
                if (
                    trajectory.fir_digest != compiled.digest
                    or trajectory.spec != settings(local, grid, method)
                ):
                    raise ValueError(
                        "Incorrect native FIR identity or execution settings"
                    )
                report["runs"].append(
                    {
                        "case_id": case["id"],
                        "state_ids": list(trajectory.state_ids),
                        "state_units": list(trajectory.state_units),
                        "observable_ids": list(trajectory.observable_ids),
                        "observable_units": list(trajectory.observable_units),
                        "time_unit": trajectory.time_unit,
                        "method": method,
                        "study": study,
                        "settings": dict(local),
                        "fir_digest": trajectory.fir_digest,
                        "diagnostics": {
                            "nfev": trajectory.nfev,
                            "njev": trajectory.njev,
                            "nlu": trajectory.nlu,
                        },
                        "samples": [
                            {
                                "time_bits": bits(time),
                                "state_bits": bits(state[0]),
                                "observable_bits": bits(observation[0]),
                            }
                            for time, state, observation in zip(
                                trajectory.times,
                                trajectory.state_values,
                                trajectory.observable_values,
                                strict=True,
                            )
                        ],
                    }
                )
                if artifacts(design, experiment, compiled) != before:
                    raise ValueError("Execution mutated source or FIR identity")
        report["scenarios"].append(
            {
                "id": case["id"],
                "artifacts": before,
                "after_artifacts": artifacts(design, experiment, compiled),
            }
        )
        if case["id"] == "baseline-zero":
            report["controls"] = controls(
                design, case, compiled, references["studies"]["baseline"]
            )
            if artifacts(design, experiment, compiled) != before:
                raise ValueError("Failure controls mutated source or FIR identity")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--references", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    destination = report_destination(args.report)
    references = read_report(args.references)
    report = produce(references, args.source_revision)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n")
    validate_ode_report(report, args.source_revision, references)
    print("PASS: Python native ODE report; 60 runs, 240 samples")


if __name__ == "__main__":
    main()
