using Test, JSON
include("../reference.jl")
const R = RejectionReference
@testset "Fixed rejection catalog and immutable input" begin
    catalog = R.load_catalog()
    for case in catalog["cases"]
        @testset "$(case["id"])" begin
            @test R.observe(case) == case["expected"]
            if case["expected"]["outcome"] == "accept" && case["operation"] in ("model", "producer", "capability")
                doc = R.parse_input(R.read_artifact(case["inputs"]["primary"]), "P03")
                before = deepcopy(doc)
                R.validate_model(doc)
                @test doc == before
                @test JSON.json(doc) == JSON.json(before)
            end
        end
    end
end
@testset "Raw numeric policy and exact templates" begin
    @test R.parse_input(Vector{UInt8}("9007199254740993"), "P03") === 9007199254740992.0
    for (token, category, policy) in (("9007199254740993", "INTEGER_RANGE", "P01"), ("1e400", "NUMBER_RANGE", "P03"), ("1e-400", "NUMBER_UNDERFLOW", "P03"))
        err = try R.parse_input(Vector{UInt8}("{\"a/b~\":[0,$token]}"), policy) catch e; e end
        @test err isa R.Rejection
        @test (err.category, err.path) == (category, "/a~1b~0/1")
    end
    @test R.parse_input(Vector{UInt8}("0e-999999"), "P03") == 0
    @test R.parse_input(Vector{UInt8}("5e-324"), "P03") == 5e-324
    doc = JSON.parsefile(joinpath(R.ROOT, "spec/fir/proposals/examples/production-decay.json"))
    expr = doc["model"]["reactions"][2]["flux"]
    expr["left"], expr["right"] = expr["right"], expr["left"]
    before = deepcopy(doc)
    @test_throws R.Rejection R.validate_model(doc)
    @test doc == before
end
