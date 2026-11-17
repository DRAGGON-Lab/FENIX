# Native builder projections only. Run in the independent Julia reference-tool
# environment to make JSONSchema a test tool rather than a library dependency.
using Test, JSON, JSONSchema, SHA
pushfirst!(LOAD_PATH, normpath(joinpath(@__DIR__, "..")))
using Fenix
@test realpath(pathof(Fenix)) == realpath(joinpath(@__DIR__, "../src/Fenix.jl"))
include("adapter.jl")
using .ContentProjection

const B = Fenix.BioIR
const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const BIOIR = joinpath(ROOT, "conformance/bioir")

@testset "Native Julia uncommitted BioIR content projections" begin
    catalog = JSON.parsefile(joinpath(BIOIR, "catalog.json"))
    coverage = JSON.parsefile(joinpath(@__DIR__, "coverage.json"))["cases"]
    rejections = JSON.parsefile(joinpath(ROOT, "conformance/rejections/catalog.json"))
    diagnostics = Dict(case["id"] => case for case in rejections["cases"])
    schema = JSON.parsefile(joinpath(ROOT, "spec/bioir/proposals/bioir-m0.schema.json"))

    @testset "Coverage partition" begin
        @test catalog["status"] == "APPROVED"
        @test rejections["status"] == "APPROVED"
        @test [case["id"] for case in coverage] == [case["id"] for case in catalog["cases"]]
        @test length(Set(case["id"] for case in coverage)) == 92
        @test count(case -> case["status"] == "PROJECTED", coverage) == 29
        @test count(case -> case["status"] == "DEFERRED", coverage) == 63
        @test all(case -> !isempty(case["reason"]), coverage)
        @test all(case -> case["status"] in ("PROJECTED", "DEFERRED"), coverage)
    end

    projected = Set(case["id"] for case in coverage if case["status"] == "PROJECTED")
    selected = [case for case in catalog["cases"] if case["id"] in projected]
    @test count(case -> case["expected"]["outcome"] == "accept", selected) == 6
    @test count(case -> case["expected"]["outcome"] == "reject", selected) == 23

    for case in selected
        @testset "$(case["id"])" begin
            raw = read(joinpath(BIOIR, case["input"]))
            @test bytes2hex(sha256(raw)) == case["input_sha256"]
            # Ordinary JSON parsing projects only preselected approved inputs;
            # this is not a native raw parser or document-validation test.
            document = JSON.parse(String(raw))
            context = Dict{Symbol,Any}()
            if case["operation"] == "experiment"
                design_raw = read(joinpath(BIOIR, case["design"]))
                dependency = diagnostics["p01-" * case["id"]]["inputs"]["design"]
                @test bytes2hex(sha256(design_raw)) == dependency["sha256"]
                context[:source_design] = construct(B.DesignContent, JSON.parse(String(design_raw))["content"])
            end
            type = case["operation"] == "design" ? B.DesignContent : B.ExperimentContent
            outcome = try
                construct(type, document["content"]; context...)
            catch error
                error isa ProjectionError || rethrow()
                error
            end
            if outcome isa ProjectionError
                @test case["expected"]["outcome"] == "reject"
                @test outcome.error.category == case["expected"]["category"]
                detailed = diagnostics["p01-" * case["id"]]["expected"]
                @test detailed["document"] == "primary"
                @test outcome.error.category == detailed["category"]
                # Public constructors report paths relative to their own root.
                # The adapter adds only the nesting location, not semantics.
                @test outcome.prefix * outcome.error.path == detailed["path"]
            else
                @test case["expected"]["outcome"] == "accept"
                output = B.to_dict(outcome)
                @test output == document["content"]
                @test JSON.parse(B.to_json(outcome)) == output
                definition = type === B.DesignContent ? "design" : "experiment"
                validator = JSONSchema.Schema(Dict(
                    "\$ref" => "#/definitions/" * definition,
                    "definitions" => schema["definitions"],
                ))
                @test JSONSchema.validate(validator, output) === nothing
            end
        end
    end
end
