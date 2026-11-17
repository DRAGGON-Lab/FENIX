# Native producer regressions use local authoring only, no repository fixtures.
function compiler_pair(; alpha=10.0, beta=0.1, initial=0.5, volume=1e-15,
                       misleading=false, reordered=false, observable_ids=("amount_x",))
    species_id, port_id = misleading ? ("protein", "count") : ("x", "amount")
    production_id, decay_id = misleading ? ("beta", "alpha") : ("alpha", "beta")
    target = PortReference(species=species_id, port=port_id)
    parameters = [Parameter(id=production_id, unit="molecule/s"), Parameter(id=decay_id, unit="1/s")]
    functions = [BioIRFunction(id="synthesis", kind="constitutive_production", target=target, parameter=production_id),
                 BioIRFunction(id="loss", kind="first_order_decay", target=target, parameter=decay_id)]
    assignments = [ParameterAssignment(parameter=production_id, quantity=Quantity(value=alpha, unit="molecule/s")),
                   ParameterAssignment(parameter=decay_id, quantity=Quantity(value=beta, unit="1/s"))]
    reordered && (reverse!(parameters); reverse!(functions); reverse!(assignments))
    content = DesignContent(id="compile_design", revision=1,
        compartments=[Compartment(id="cell",volume=Quantity(value=volume,unit="L"))],
        species=[Species(id=species_id,compartment="cell",ports=[Port(id=port_id)])],
        parameters=parameters, functions=functions)
    d = DesignDocument(content=content)
    scenario = ExperimentContent(id="compile_experiment",revision=1,source_design=d.content,design=reference(d),
        parameters=assignments,initial_counts=[InitialCount(species=species_id,quantity=Quantity(value=initial,unit="molecule"))],
        observables=[Observable(id=id,target=target) for id in observable_ids],interventions=())
    d, ExperimentDocument(content=scenario,source_design=d)
end

function compiler_error(category, path, f)
    failure = try
        f()
        nothing
    catch error
        error
    end
    @test failure isa Fenix.FIR.FIRValidationError
    if failure isa Fenix.FIR.FIRValidationError
        @test failure.category == category
        @test failure.path == path
    end
end

@testset "Native compiler binds roles independently of names and order" begin
    d, e = compiler_pair()
    output = Fenix.compile_experiment(e)
    raw = Fenix.FIR.to_dict(output)
    @test output isa Fenix.FIR.FIRDocument
    @test Fenix.FIR.validate_sources(output;design=d,experiment=e) === output
    @test raw["provenance"]["compiler"] == Dict("name"=>"Fenix","version"=>string(pkgversion(Fenix)))
    @test raw["provenance"]["design_digest"] == d.digest
    @test raw["provenance"]["experiment_digest"] == e.digest
    @test raw["model"]["states"][1]["initial"] === 0.5
    @test Dict(item["id"]=>item["value"] for item in raw["model"]["parameters"]) == Dict("alpha"=>10.0,"beta"=>0.1)
    for (misleading,reordered) in ((true,false),(false,true),(true,true))
        renamed_d, renamed_e = compiler_pair(;misleading,reordered)
        compiled = Fenix.compile_experiment(renamed_e)
        @test Fenix.FIR.canonical_model_bytes(compiled) == Fenix.FIR.canonical_model_bytes(output)
        @test renamed_d.digest != d.digest
        mapping = Fenix.FIR.to_dict(compiled)["provenance"]["symbol_map"]
        @test mapping["states"][1]["bioir_species_id"] == (misleading ? "protein" : "x")
        @test mapping["parameters"][1]["bioir_parameter_id"] == (misleading ? "beta" : "alpha")
    end
    larger_d, larger_e = compiler_pair(volume=2e-15)
    @test larger_d.digest != d.digest
    @test Fenix.FIR.canonical_model_bytes(Fenix.compile_experiment(larger_e)) == Fenix.FIR.canonical_model_bytes(output)
    annotated = with_metadata(e,Metadata(name="different envelope 🧬"))
    @test Fenix.FIR.to_dict(Fenix.compile_experiment(annotated)) == raw
    for (alpha,beta,initial) in ((0,0,0.25),(-0.0,-0.0,-0.0),
            (nextfloat(0.0),nextfloat(0.0),nextfloat(0.0)),
            (floatmax(Float64),Float64(2)^53,1e20))
        source, scenario = compiler_pair(;alpha,beta,initial,observable_ids=())
        compiled = Fenix.compile_experiment(scenario)
        values = Fenix.FIR.to_dict(compiled)["model"]
        @test isequal(values["parameters"][1]["value"], Float64(alpha))
        @test isequal(values["parameters"][2]["value"], Float64(beta))
        @test isequal(values["states"][1]["initial"], Float64(initial))
        @test isempty(values["observables"])
        @test values["capabilities"] == Dict("ode"=>true,"ssa"=>false)
    end
end

@testset "Producer correspondence rejects source mismatches" begin
    d,e = compiler_pair(observable_ids=("amount_x","other_amount"))
    output = Fenix.compile_experiment(e)
    raw = Fenix.FIR.to_dict(output)
    function changed(f)
        data = deepcopy(raw)
        f(data)
        Fenix.FIR.from_dict(Fenix.FIR.FIRDocument,data;design=d,experiment=e)
    end
    compiler_error("SOURCE_REQUIRED","/provenance", () -> changed(data -> delete!(data,"provenance")))
    for field in ("design_digest","experiment_digest","symbol_map")
        # A symbol map structurally requires its Design qualifier.
        if field != "design_digest"
            compiler_error("SOURCE_REQUIRED","/provenance/"*field, () -> changed(data -> delete!(data["provenance"],field)))
        end
    end
    for field in ("design_digest","experiment_digest")
        compiler_error("SOURCE_DIGEST","/provenance/"*field,
            () -> changed(data -> data["provenance"][field]=repeat("f",64)))
    end
    for field in ("bioir_species_id","bioir_port_id","bioir_compartment_id")
        compiler_error("REFERENCE","/provenance/symbol_map/states/0/"*field,
            () -> changed(data -> data["provenance"]["symbol_map"]["states"][1][field]="unknown"))
    end
    for field in ("bioir_parameter_id","bioir_function_id")
        compiler_error("REFERENCE","/provenance/symbol_map/parameters/0/"*field,
            () -> changed(data -> data["provenance"]["symbol_map"]["parameters"][1][field]="unknown"))
    end
    compiler_error("SOURCE_ROLE","/provenance/symbol_map/parameters/0/bioir_function_id",
        () -> changed(data -> data["provenance"]["symbol_map"]["parameters"][1]["bioir_function_id"]="loss"))
    compiler_error("SOURCE_ROLE","/provenance/symbol_map/parameters/0/bioir_function_kind",
        () -> changed(data -> data["provenance"]["symbol_map"]["parameters"][1]["bioir_function_kind"]="first_order_decay"))
    compiler_error("SOURCE_VALUE","/model/parameters/0/value",
        () -> changed(data -> data["model"]["parameters"][1]["value"]=12.0))
    compiler_error("SOURCE_VALUE","/model/states/0/initial",
        () -> changed(data -> data["model"]["states"][1]["initial"]=0.0))
    compiler_error("SOURCE_OBSERVABLE","/model/observables/0/id",
        () -> changed(data -> data["model"]["observables"][1]["id"]="invented"))
    compiler_error("SOURCE_OBSERVABLE","/model/observables",
        () -> changed(data -> pop!(data["model"]["observables"])))
    standalone = Fenix.FIR.from_dict(Fenix.FIR.FIRDocument,Dict("model"=>raw["model"]))
    @test Fenix.FIR.canonical_model_bytes(standalone) == Fenix.FIR.canonical_model_bytes(output)
    compiler_error("SOURCE_REQUIRED","/provenance", () -> Fenix.FIR.validate_sources(standalone;design=d,experiment=e))
    @test_throws BioIRValidationError Fenix.FIR.validate_sources(output;design=compiler_pair(volume=2e-15)[1],experiment=e)
end
