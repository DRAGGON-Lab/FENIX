"""Run unchanged M0 mathematics across exact source revisions and verify readback.

Copy this file with production_decay.py; both use only installed FENIX runtime APIs.
"""

import argparse
import dataclasses
import hashlib
import json
from pathlib import Path

from fenix.bioir import (
    BioIRValidationError,
    ExperimentDocument,
    Metadata,
    Quantity,
)
from fenix.compiler import compile_experiment
from fenix.fir import FIRValidationError
from fenix.results import ResultValidationError, RunRecord
from production_decay import (
    CASES,
    METHODS,
    build_experiment,
    execution_settings,
    save_run,
)

SOURCE_MISMATCH_PATHS = (
    "/manifest/sources/design/revision",
    "/manifest/sources/design/digest",
    "/manifest/sources/experiment/revision",
    "/manifest/sources/experiment/digest",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def expect_rejection(action, error_type, category, path):
    try:
        action()
    except error_type as error:
        paths = (path,) if isinstance(path, str) else path
        require(
            error.category == category and error.path in paths, "unexpected diagnostic"
        )
        return {"category": category, "path": error.path}
    raise ValueError("invalid source/artifact was accepted")


def revised_experiment(original):
    """Advance explicit revisions; reverse declarations and change M0 cell volume."""
    design = original.source_design
    content = design.content
    next_design = design.replace_content(
        dataclasses.replace(
            content,
            revision=2,
            compartments=(
                dataclasses.replace(
                    content.compartments[0], volume=Quantity(value=2e-15, unit="L")
                ),
            ),
            parameters=content.parameters[::-1],
            functions=content.functions[::-1],
        )
    )
    return original.replace_content(
        dataclasses.replace(
            original.content,
            revision=2,
            design=next_design.reference,
            source_design=next_design.content,
            parameters=original.content.parameters[::-1],
        ),
        source_design=next_design,
    )


def run_workflow(case, method, output_dir):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=False)
    original = build_experiment(case)
    original_sources = (original.source_design.to_json(), original.to_json())
    decorated_design = original.source_design.with_metadata(
        Metadata(name="annotated Design")
    )
    annotated = ExperimentDocument(
        content=original.content,
        source_design=decorated_design,
        metadata=Metadata(description="author annotation only"),
    )
    revised = revised_experiment(original)
    base_fir, revised_fir = compile_experiment(original), compile_experiment(revised)
    require(
        annotated.digest == original.digest
        and decorated_design.digest == original.source_design.digest,
        "metadata changed source identity",
    )
    require(
        base_fir.model.identity_bytes() == revised_fir.model.identity_bytes(),
        "M0 volume/declaration/revision changes altered mathematics",
    )
    require(
        original.digest != revised.digest
        and original.source_design.digest != revised.source_design.digest,
        "scientific source revisions did not change identity",
    )
    require(
        original_sources == (original.source_design.to_json(), original.to_json()),
        "updating sources mutated originals",
    )
    spec = execution_settings(case, method)
    first = save_run(original, spec, output / "original")
    second = save_run(revised, spec, output / "revised")
    manifest = first.manifest.to_json()
    manifest_hash = hashlib.sha256(manifest.encode()).hexdigest()
    loaded = RunRecord.from_json(
        manifest,
        first.result_bytes,
        experiment=annotated,
        expected_manifest_sha256=manifest_hash,
    )
    require(
        loaded.result_bytes == first.result_bytes,
        "annotated source readback changed result bytes",
    )
    # Whitespace is valid JSON but remains part of a trusted transport checksum.
    untrusted = RunRecord.from_json(
        manifest + " ", first.result_bytes, experiment=original
    )
    require(
        untrusted.result_bytes == first.result_bytes,
        "manifest formatting changed result bytes",
    )
    checks = {
        "same_revision_change": expect_rejection(
            lambda: original.source_design.replace_content(
                dataclasses.replace(revised.source_design.content, revision=1)
            ),
            BioIRValidationError,
            "IMMUTABLE_REVISION",
            "/content/revision",
        ),
        "old_experiment_new_design": expect_rejection(
            lambda: ExperimentDocument.from_json(
                original.to_json(), designs=(revised.source_design,)
            ),
            BioIRValidationError,
            "DESIGN_REFERENCE",
            "/content/design/revision",
        ),
        "old_fir_new_sources": expect_rejection(
            lambda: base_fir.validate_sources(revised.source_design, revised),
            FIRValidationError,
            "SOURCE_DIGEST",
            "/provenance/design_digest",
        ),
        "old_record_new_sources": expect_rejection(
            lambda: RunRecord.from_json(
                manifest, first.result_bytes, experiment=revised
            ),
            ResultValidationError,
            "REFERENCE",
            SOURCE_MISMATCH_PATHS,
        ),
        "new_record_old_sources": expect_rejection(
            lambda: RunRecord.from_json(
                second.manifest.to_json(), second.result_bytes, experiment=original
            ),
            ResultValidationError,
            "REFERENCE",
            SOURCE_MISMATCH_PATHS,
        ),
        "result_transport_checksum": expect_rejection(
            lambda: RunRecord.from_json(
                manifest, first.result_bytes + b" ", experiment=original
            ),
            ResultValidationError,
            "CHECKSUM",
            "/manifest/output/sha256",
        ),
        "manifest_transport_checksum": expect_rejection(
            lambda: RunRecord.from_json(
                manifest + " ",
                first.result_bytes,
                experiment=original,
                expected_manifest_sha256=manifest_hash,
            ),
            ResultValidationError,
            "CHECKSUM",
            "/manifest",
        ),
    }
    require(
        original_sources == (original.source_design.to_json(), original.to_json()),
        "capture/readback mutated original sources",
    )
    summary = {
        "format": "m0-source-revisions-v1",
        "case": case,
        "method": method,
        "fir_digest": base_fir.digest,
        "original_design_digest": original.source_design.digest,
        "revised_design_digest": revised.source_design.digest,
        "original_experiment_digest": original.digest,
        "revised_experiment_digest": revised.digest,
        "rejections": checks,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASES, default="baseline-five")
    parser.add_argument("--method", choices=METHODS, default="DOP853")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    run_workflow(args.case, args.method, args.output_dir)


if __name__ == "__main__":
    main()
