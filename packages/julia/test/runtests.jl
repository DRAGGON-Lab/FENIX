using Test
using Fenix
using Fenix.BioIR
using JSON

function design(; changes...)
    args = (id="design", revision=1,
        compartments=(Compartment(id="cell", volume=Quantity(value=1e-15, unit="L")),),
        species=(Species(id="x", compartment="cell", ports=(Port(id="amount"),)),),
        parameters=(Parameter(id="alpha", unit="molecule/s"), Parameter(id="beta", unit="1/s")),
        functions=(BioIRFunction(id="production", kind="constitutive_production", target=PortReference(species="x", port="amount"), parameter="alpha"),
                   BioIRFunction(id="decay", kind="first_order_decay", target=PortReference(species="x", port="amount"), parameter="beta")))
    DesignContent(; merge(args, (; changes...))...)
end
function experiment(; changes...)
    args = (id="experiment", revision=1, source_design=design(),
        design=DesignReference(id="design", revision=1, digest=repeat("0",64)),
        parameters=(ParameterAssignment(parameter="alpha", quantity=Quantity(value=10, unit="molecule/s")), ParameterAssignment(parameter="beta", quantity=Quantity(value=0.1, unit="1/s"))),
        initial_counts=(InitialCount(species="x", quantity=Quantity(value=0.5, unit="molecule")),),
        observables=(Observable(id="amount_x", target=PortReference(species="x", port="amount")),), interventions=())
    ExperimentContent(; merge(args, (; changes...))...)
end
function checkerror(category, path, f)
    failure = try
        f()
        nothing
    catch err
        err
    end
    @test failure isa BioIRValidationError
    if failure isa BioIRValidationError
        @test failure.category == category
        @test failure.path == path
        @test !isempty(sprint(showerror, failure))
    end
end

@testset "Native immutable authoring and ordinary JSON" begin
    d, e = design(), experiment()
    @test d.compartments isa Tuple
    @test e.observables isa Tuple
    @test e.initial_counts[1].quantity.value === 0.5
    @test !hasproperty(e, :source_design)
    for content in (d, e, experiment(observables=()), design(functions=reverse(d.functions)))
        output = to_dict(content)
        @test JSON.parse(to_json(content)) == output
        @test !haskey(output, "source_design")
        @test !haskey(output, "content")
        @test !haskey(output, "digest")
    end
    @test to_dict(design(functions=reverse(d.functions)))["functions"][1]["id"] == "decay"
    for field in (:compartments, :species, :parameters, :functions)
        inputs = collect(getproperty(d, field))
        content = design(; NamedTuple{(field,)}((inputs,))...)
        empty!(inputs)
        @test length(getproperty(content, field)) == length(getproperty(d, field))
    end
    obs = collect(e.observables)
    content = experiment(observables=obs, interventions=Any[])
    empty!(obs)
    @test length(content.observables) == 1
    out = to_dict(d)
    out["species"][1]["ports"][1]["id"] = "changed"
    empty!(out["functions"])
    @test d.species[1].ports[1].id == "amount"
    @test length(to_dict(d)["functions"]) == 2
    @test_throws Exception setproperty!(d, :id, "changed")
    @test_throws Exception setproperty!(d.compartments[1].volume, :value, 2)
    @test experiment(design=DesignReference(id="design", revision=1, digest=repeat("f",64))).design.digest == repeat("f",64)
end

@testset "Native numbers and identifiers" begin
    for value in (true, false, "1", nothing, big(1), Float32(1), 1//2, 1+0im)
        checkerror("SCHEMA", "/value", () -> Quantity(value=value, unit="molecule"))
    end
    for value in (NaN, Inf, -Inf)
        checkerror("NUMBER_RANGE", "/value", () -> Quantity(value=value, unit="molecule"))
    end
    for value in (Int64(2)^53, -(Int64(2)^53), typemax(UInt128))
        checkerror("INTEGER_RANGE", "/value", () -> Quantity(value=value, unit="molecule"))
    end
    for value in (Int8(0), UInt16(3), Int64(2)^53-1, -0.0, nextfloat(0.0), Float64(2)^53, floatmax(Float64))
        quantity = Quantity(value=value, unit="molecule/s")
        @test quantity.value isa Union{Int64,Float64}
        @test isequal(quantity.value, value)
        content = experiment(parameters=(ParameterAssignment(parameter="alpha", quantity=quantity), experiment().parameters[2]))
        @test isequal(JSON.parse(to_json(content))["parameters"][1]["quantity"]["value"], value)
    end
    checkerror("SCHEMA", "/value", () -> Quantity(value=-nextfloat(0.0), unit="molecule"))
    checkerror("SCHEMA", "/volume/value", () -> Compartment(id="c", volume=Quantity(value=0, unit="L")))
    @test Compartment(id="c", volume=Quantity(value=nextfloat(0.0), unit="L")).volume.value == nextfloat(0.0)
    for value in ("", "1x", "é", "a\n", "a/b", repeat("a",65), nothing, 1)
        checkerror("SCHEMA", "/id", () -> Port(id=value))
    end
    @test Port(id=repeat("a",64)).id == repeat("a",64)
    for value in (0, -1, true, 1.0, Int64(2)^53, "1")
        checkerror("SCHEMA", "/revision", () -> design(revision=value))
    end
    @test design(revision=Int64(2)^53-1).revision == Int64(2)^53-1
    for digest in (repeat("A",64), repeat("0",63), repeat("0",64)*"\n", 0)
        checkerror("SCHEMA", "/digest", () -> DesignReference(id="d", revision=1, digest=digest))
    end
end

@testset "Units, typed values and M0 structure" begin
    checkerror("SCHEMA", "/unit", () -> Quantity(value=1, unit="mol/L"))
    checkerror("SCHEMA", "/unit", () -> Parameter(id="p", unit="molecule"))
    checkerror("SCHEMA", "/volume/unit", () -> Compartment(id="c", volume=Quantity(value=1, unit="molecule")))
    checkerror("SCHEMA", "/quantity/unit", () -> InitialCount(species="x", quantity=Quantity(value=1, unit="L")))
    checkerror("SCHEMA", "/quantity/unit", () -> ParameterAssignment(parameter="a", quantity=Quantity(value=1, unit="molecule")))
    checkerror("SCHEMA", "/kind", () -> Port(id="p",kind="concentration"))
    checkerror("SCHEMA", "/kind", () -> design(kind="Experiment"))
    checkerror("SCHEMA", "/schema_version", () -> experiment(schema_version="2"))
    checkerror("SCHEMA", "/target", () -> Observable(id="o", target=Dict()))
    checkerror("SCHEMA", "/volume", () -> Compartment(id="c", volume=Dict()))
    d = design()
    for field in (:compartments, :species, :parameters, :functions)
        values = getproperty(d, field)
        for invalid in ((), (values..., values...), Dict())
            checkerror("SCHEMA", "/"*string(field), () -> design(; NamedTuple{(field,)}((invalid,))...))
        end
        invalid = (Dict(), values[2:end]...)
        checkerror("SCHEMA", "/"*string(field)*"/0", () -> design(; NamedTuple{(field,)}((invalid,))...))
    end
    checkerror("SCHEMA", "/ports", () -> Species(id="x",compartment="c",ports=()))
    checkerror("SCHEMA", "/ports/0", () -> Species(id="x",compartment="c",ports=(Dict(),)))
    checkerror("SCHEMA", "/interventions", () -> experiment(interventions=(Dict(),)))
    checkerror("SCHEMA", "/source_design", () -> experiment(source_design=Dict()))
    checkerror("SCHEMA", "/design", () -> experiment(design=Dict()))
end

@testset "References, roles and uniqueness" begin
    d,e = design(),experiment()
    checkerror("REFERENCE", "/species/0/compartment", () -> design(species=(Species(id="x",compartment="Cell",ports=d.species[1].ports),)))
    for (target,path) in ((PortReference(species="missing",port="amount"),"species"),(PortReference(species="x",port="missing"),"port"))
        fn = BioIRFunction(id="production",kind="constitutive_production",target=target,parameter="alpha")
        checkerror("REFERENCE", "/functions/0/target/"*path, () -> design(functions=(fn,d.functions[2])))
        checkerror("REFERENCE", "/observables/0/target/"*path, () -> experiment(observables=(Observable(id="o",target=target),)))
    end
    fn = BioIRFunction(id="production",kind="constitutive_production",target=d.functions[1].target,parameter="missing")
    checkerror("REFERENCE", "/functions/0/parameter", () -> design(functions=(fn,d.functions[2])))
    for field in (:parameters,:functions)
        values = getproperty(d,field)
        checkerror("DUPLICATE_ID", "/"*string(field)*"/1/id", () -> design(; NamedTuple{(field,)}(((values[1],values[1]),))...))
    end
    fn = BioIRFunction(id="other",kind="constitutive_production",target=d.functions[1].target,parameter="alpha")
    checkerror("FUNCTION_ROLE", "/functions/1", () -> design(functions=(d.functions[1],fn)))
    checkerror("UNIT", "/functions/0/parameter", () -> design(parameters=(Parameter(id="alpha",unit="1/s"),d.parameters[2])))
    checkerror("UNIT", "/parameters/0/quantity/unit", () -> experiment(parameters=(ParameterAssignment(parameter="alpha",quantity=Quantity(value=1,unit="1/s")),e.parameters[2])))
    for ref in (DesignReference(id="missing",revision=1,digest=repeat("0",64)),DesignReference(id="design",revision=2,digest=repeat("0",64)))
        path = ref.id == "missing" ? "/design/id" : "/design/revision"
        checkerror("DESIGN_REFERENCE", path, () -> experiment(design=ref))
    end
    checkerror("DUPLICATE_ID", "/parameters/1/parameter", () -> experiment(parameters=(e.parameters[1],e.parameters[1])))
    checkerror("REFERENCE", "/parameters/0/parameter", () -> experiment(parameters=(ParameterAssignment(parameter="missing",quantity=e.parameters[1].quantity),e.parameters[2])))
    checkerror("REFERENCE", "/initial_counts", () -> experiment(initial_counts=(InitialCount(species="missing",quantity=e.initial_counts[1].quantity),)))
    checkerror("DUPLICATE_ID", "/observables/1/id", () -> experiment(observables=(e.observables[1],e.observables[1])))
end

@testset "No unchecked constructor path or executable content" begin
    @test_throws Exception Port("p")
    @test_throws Exception Quantity(1,"molecule")
    @test_throws Exception Quantity(unit="molecule")
    for field in (:profile,:callback,:time_grid,:solver,:events,:metadata,:digest)
        @test_throws Exception experiment(; NamedTuple{(field,)}(("unsupported",))...)
    end
    @test_throws Exception Quantity{Float64}(NaN,"molecule")
end

@testset "Invalid native string encoding" begin
    checkerror("SCHEMA", "/id", () -> Port(id=String(UInt8[0xff])))
    checkerror("SCHEMA", "/digest", () -> DesignReference(id="design", revision=1, digest=String(UInt8[0xff])))
end

include("test_json.jl")
include("test_documents.jl")
include("test_fir.jl")
include("test_compiler.jl")
