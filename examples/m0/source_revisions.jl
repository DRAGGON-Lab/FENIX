"""Unchanged M0 mathematics across exact source revisions and result readback."""
module M0SourceRevisions
using Fenix
using Fenix.BioIR
using SHA, JSON
include("production_decay.jl")

require(condition, message) = condition || error(message)
properties(value) = (; (key => getfield(value, key) for key in fieldnames(typeof(value)))...)

function expect_rejection(action, error_type, category, path)
    try
        action()
    catch failure
        failure isa error_type || rethrow()
        paths = path isa String ? (path,) : path
        require(failure.category == category && failure.path in paths, "unexpected diagnostic")
        return Dict("category" => category, "path" => failure.path)
    end
    error("invalid source/artifact was accepted")
end

function revised_experiment(original)
    design = original.source_design
    content = design.content
    compartment = Compartment(; properties(content.compartments[1])...,
                              volume=Quantity(value=2e-15, unit="L"))
    next_design = BioIR.replace_content(design, DesignContent(; properties(content)...,
        revision=2, compartments=(compartment,), parameters=reverse(content.parameters),
        functions=reverse(content.functions)))
    next_content = ExperimentContent(; properties(original.content)...,
        revision=2, design=BioIR.reference(next_design), source_design=next_design.content,
        parameters=reverse(original.content.parameters))
    BioIR.replace_content(original, next_content; source_design=next_design)
end

function run_workflow(case, method, output_dir)
    ispath(output_dir) && error("output directory must be new")
    mkpath(output_dir)
    original = M0Example.build_experiment(case)
    original_sources = (BioIR.to_json(original.source_design), BioIR.to_json(original))
    decorated_design = BioIR.with_metadata(original.source_design, Metadata(name="annotated Design"))
    annotated = ExperimentDocument(content=original.content, source_design=decorated_design,
                                   metadata=Metadata(description="author annotation only"))
    revised = revised_experiment(original)
    base_fir, revised_fir = Fenix.compile_experiment(original), Fenix.compile_experiment(revised)
    require(annotated.digest == original.digest && decorated_design.digest == original.source_design.digest,
            "metadata changed source identity")
    require(FIR.identity_bytes(base_fir) == FIR.identity_bytes(revised_fir),
            "M0 volume/declaration/revision changes altered mathematics")
    require(original.digest != revised.digest && original.source_design.digest != revised.source_design.digest,
            "scientific source revisions did not change identity")
    require(original_sources == (BioIR.to_json(original.source_design), BioIR.to_json(original)),
            "updating sources mutated originals")
    spec = M0Example.execution_settings(case, method)
    first = M0Example.save_run(original, spec, joinpath(output_dir, "original"))
    second = M0Example.save_run(revised, spec, joinpath(output_dir, "revised"))
    manifest = Results.to_json(first.manifest)
    manifest_hash = bytes2hex(sha256(codeunits(manifest)))
    loaded = Results.from_json(Results.RunRecord, manifest, first.result_bytes;
                               experiment=annotated, expected_manifest_sha256=manifest_hash)
    require(loaded.result_bytes == first.result_bytes, "annotated source readback changed result bytes")
    untrusted = Results.from_json(Results.RunRecord, manifest * " ", first.result_bytes; experiment=original)
    require(untrusted.result_bytes == first.result_bytes, "manifest formatting changed result bytes")
    old_revision = DesignContent(; properties(revised.source_design.content)..., revision=1)
    checks = Dict(
        "same_revision_change" => expect_rejection(
            () -> BioIR.replace_content(original.source_design, old_revision),
            BioIRValidationError, "IMMUTABLE_REVISION", "/content/revision"),
        "old_experiment_new_design" => expect_rejection(
            () -> BioIR.from_json(ExperimentDocument, BioIR.to_json(original); designs=[revised.source_design]),
            BioIRValidationError, "DESIGN_REFERENCE", "/content/design/revision"),
        "old_fir_new_sources" => expect_rejection(
            () -> FIR.validate_sources(base_fir; design=revised.source_design, experiment=revised),
            FIR.FIRValidationError, "SOURCE_DIGEST", "/provenance/design_digest"),
        "old_record_new_sources" => expect_rejection(
            () -> Results.from_json(Results.RunRecord, manifest, first.result_bytes; experiment=revised),
            Results.ResultValidationError, "REFERENCE",
            ("/manifest/sources/design/revision", "/manifest/sources/design/digest")),
        "new_record_old_sources" => expect_rejection(
            () -> Results.from_json(Results.RunRecord, Results.to_json(second.manifest), second.result_bytes;
                                   experiment=original),
            Results.ResultValidationError, "REFERENCE",
            ("/manifest/sources/design/revision", "/manifest/sources/design/digest")),
        "result_transport_checksum" => expect_rejection(
            () -> Results.from_json(Results.RunRecord, manifest, vcat(first.result_bytes, UInt8[0x20]);
                                   experiment=original),
            Results.ResultValidationError, "CHECKSUM", "/manifest/output/sha256"),
        "manifest_transport_checksum" => expect_rejection(
            () -> Results.from_json(Results.RunRecord, manifest * " ", first.result_bytes;
                                   experiment=original, expected_manifest_sha256=manifest_hash),
            Results.ResultValidationError, "CHECKSUM", "/manifest"),
    )
    require(original_sources == (BioIR.to_json(original.source_design), BioIR.to_json(original)),
            "capture/readback mutated original sources")
    summary = Dict("format" => "m0-source-revisions-v1", "case" => case, "method" => method,
        "fir_digest" => base_fir.digest, "original_design_digest" => original.source_design.digest,
        "revised_design_digest" => revised.source_design.digest, "original_experiment_digest" => original.digest,
        "revised_experiment_digest" => revised.digest, "rejections" => checks)
    write(joinpath(output_dir, "summary.json"), JSON.json(summary) * "\n")
    summary
end

function main(args=ARGS)
    options = Dict("--case" => "baseline-five", "--method" => "Tsit5")
    iseven(length(args)) || error("Expected --case NAME --method METHOD --output-dir PATH")
    for i in 1:2:length(args)
        args[i] in ("--case", "--method", "--output-dir") || error("Unknown option")
        options[args[i]] = args[i+1]
    end
    haskey(options, "--output-dir") || error("--output-dir is required")
    haskey(M0Example.CASES, options["--case"]) || error("Unknown case")
    options["--method"] in M0Example.METHODS || error("Unknown method")
    run_workflow(options["--case"], options["--method"], options["--output-dir"])
end
end

if abspath(PROGRAM_FILE) == @__FILE__
    M0SourceRevisions.main()
end
