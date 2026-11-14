using Test, JSON
include("../review.jl")
const Review = RejectionReview
const R = Review.R
@testset "Native catalog integrity" begin
    original = R.load_catalog()
    mktempdir() do root
        cp(joinpath(R.ROOT, "conformance"), joinpath(root, "conformance"))
        cp(joinpath(R.ROOT, "spec"), joinpath(root, "spec"))
        directory = joinpath(root, "conformance/rejections")
        function fails(change)
            catalog = deepcopy(original)
            change(catalog)
            write(joinpath(directory, "catalog.json"), JSON.json(catalog))
            @test_throws Exception R.load_catalog(; directory=directory, root=root)
        end
        fails(c -> push!(c["cases"], c["cases"][1]))
        fails(c -> push!(c["coverage"]["invalid-event"], "unknown"))
        fails(c -> push!(c["coverage"]["invalid-event"], c["coverage"]["invalid-event"][1]))
        fails(c -> c["cases"][1]["inputs"]["primary"]["sha256"] = repeat("0", 64))
        fails(c -> c["cases"][1]["inputs"]["primary"]["path"] = "../escape.input")
        fails(c -> c["cases"][1]["inputs"]["primary"]["path"] = "/tmp/escape.input")
        fails(c -> pop!(c["coverage"]["p03-contract-only"]))
        fails(c -> pop!(c["coverage"]["p02-examples"]))
        fails(c -> delete!(first(x for x in c["cases"] if x["operation"] == "producer")["inputs"], "design"))
        fails(c -> c["cases"][1]["inputs"]["request"] = c["cases"][1]["inputs"]["primary"])
        write(joinpath(directory, "catalog.json"), JSON.json(original))
        orphan = joinpath(directory, "inputs/orphan.input")
        write(orphan, "{}")
        @test_throws Exception R.load_catalog(; directory=directory, root=root)
        rm(orphan)
        rm(joinpath(directory, "inputs/request-ode.input"))
        @test_throws Exception R.load_catalog(; directory=directory, root=root)
    end
end
@testset "Protected output aliases" begin
    protected = joinpath(R.HERE, "reference.jl")
    @test_throws ErrorException Review.check_output(protected)
    for path in ("conformance/rejections/catalog.json", "conformance/rejections/inputs/request-ode.input",
                 "spec/fir/proposals/fir-m0.schema.json", "packages/python/pyproject.toml")
        @test_throws ErrorException Review.check_output(joinpath(R.ROOT, path))
    end
    mktempdir() do directory
        link = joinpath(directory, "symlink")
        symlink(protected, link)
        @test_throws ErrorException Review.check_output(link)
        hard = joinpath(directory, "hardlink")
        hardlink(protected, hard)
        @test_throws ErrorException Review.check_output(hard)
        doc_alias = joinpath(directory, "document-hardlink")
        hardlink(joinpath(R.ROOT, "docs/DEVELOPMENT_WORKFLOW.md"), doc_alias)
        @test_throws ErrorException Review.check_output(doc_alias)
        @test Review.check_output(joinpath(directory, "new.json")) == joinpath(realpath(directory), "new.json")
    end
end
@testset "Producer operations preserve supplied data" begin
    for case in R.load_catalog()["cases"]
        if case["expected"]["outcome"] == "accept" && case["operation"] == "producer"
            doc = R.parse_input(R.read_artifact(case["inputs"]["primary"]), "P03")
            design = R.parse_input(R.read_artifact(case["inputs"]["design"]), "P01")
            experiment = R.parse_input(R.read_artifact(case["inputs"]["experiment"]), "P01")
            before = deepcopy((doc, design, experiment))
            R.validate_producer(doc, design, experiment)
            @test (doc, design, experiment) == before
            @test JSON.json((doc, design, experiment)) == JSON.json(before)
        end
    end
end
