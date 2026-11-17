# Evaluate parameters extracted from native compiled FIR with the unchanged,
# independent high precision oracle. This introduces no native solver API.
include(joinpath(ROOT,"conformance/production_decay/review_oracle.jl"))
const O = ProductionDecayOracle
function oracle_experiment(d, a, b, x)
    functions = Dict(f.kind=>f for f in d.content.functions)
    content = B.ExperimentContent(id="oracle",revision=1,design=B.reference(d),source_design=d.content,
        parameters=[B.ParameterAssignment(parameter=functions[kind].parameter,
            quantity=B.Quantity(value=value,unit=unit)) for (kind,value,unit) in
            (("constitutive_production",a,"molecule/s"),("first_order_decay",b,"1/s"))],
        initial_counts=[B.InitialCount(species=only(d.content.species).id,quantity=B.Quantity(value=x,unit="molecule"))],
        observables=(),interventions=())
    B.ExperimentDocument(content=content,source_design=d)
end
@testset "Compiler bridge: ten binary64 triples, 40 fixed oracle samples" begin
    catalog = O.load_catalog()
    @test catalog["status"] == "APPROVED"
    @test length(catalog["cases"]) == 10
    @test sum(length(c["samples"]) for c in catalog["cases"]) == 40
    d = B.from_json(B.DesignDocument,artifact("spec/fir/proposals/examples/sources/gfp-design.json"))
    @testset "$(case["id"])" for case in catalog["cases"]
        a,b,x = [O.decode(case["parameters"][key]) for key in ("alpha","beta","x0")]
        compiled = Fenix.compile_experiment(oracle_experiment(d,a,b,x))
        model = F.to_dict(compiled.model)
        parameters = Dict(p["id"]=>p for p in model["parameters"])
        extracted = (parameters["alpha"]["value"],parameters["beta"]["value"],only(model["states"])["initial"])
        for (value,key) in zip(extracted,("alpha","beta","x0"))
            @test string(reinterpret(UInt64,value);base=16,pad=16) == case["parameters"][key]
        end
        @test parameters["alpha"]["unit"] == "molecule/s"
        @test parameters["beta"]["unit"] == "1/s"
        @test only(model["states"])["unit"] == "molecule"
        @test model["time_unit"] == "s"
        alpha = Dict("op"=>"parameter","id"=>"alpha")
        decay = Dict("op"=>"multiply","left"=>Dict("op"=>"parameter","id"=>"beta"),"right"=>Dict("op"=>"state","id"=>"x"))
        reactions = Dict(r["id"]=>r for r in model["reactions"])
        @test reactions["production"]["stoichiometry"] == Dict("x"=>1.0)
        @test reactions["decay"]["stoichiometry"] == Dict("x"=>-1.0)
        @test reactions["production"]["flux"] == alpha
        @test reactions["decay"]["flux"] == decay
        @test only(model["equations"])["rhs"] == Dict("op"=>"subtract","left"=>alpha,"right"=>decay)
        for sample in case["samples"]
            rounded = String[]
            for precision in (512,1024)
                value = O.evaluate(extracted...,O.decode(sample["time_bits"]),precision)
                @test O.decimal_string(value,50) == sample["expected"]
                push!(rounded,O.decimal_string(value,70))
            end
            @test rounded[1] == rounded[2]
        end
        push!(ROWS,Dict("catalog"=>"compiler-oracle","id"=>case["id"],"observed"=>Dict("outcome"=>"accept"),
            "samples"=>length(case["samples"]),"precisions_bits"=>[512,1024],"digest"=>compiled.digest))
    end
end
