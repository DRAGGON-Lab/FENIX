"""P01 uncommitted M0 authoring. No raw parsing or committed identity verification."""
module BioIR
using JSON
export BioIRValidationError, Quantity, Port, Compartment, Species, Parameter,
       PortReference, BioIRFunction, ParameterAssignment, InitialCount, Observable,
       DesignReference, DesignContent, ExperimentContent, to_dict, to_json

abstract type BioIRValue end
struct BioIRValidationError <: Exception
    category::String
    path::String
    message::String
end
Base.showerror(io::IO, e::BioIRValidationError) = print(io, e.category, " at ", isempty(e.path) ? "/" : e.path, ": ", e.message)
require(ok, path, message, category="SCHEMA") = ok || throw(BioIRValidationError(category, path, message))
const MAX_INTEGER = Int64(2)^53 - 1
const FIXED_INTEGERS = Union{Int8,Int16,Int32,Int64,Int128,UInt8,UInt16,UInt32,UInt64,UInt128}
function identifier(value, path)
    require(value isa String && isvalid(value) && occursin(r"\A[A-Za-z][A-Za-z0-9_-]{0,63}\z", value), path, "expected ASCII identifier of 1–64 characters")
end
function revision_number(value)
    require(value isa FIXED_INTEGERS && 1 <= value <= MAX_INTEGER, "/revision", "expected positive safe integer revision")
    Int64(value)
end
token(value, allowed, path) = require(value isa String && value in allowed, path, "unsupported token; expected $(allowed)")
typed(value, T, path) = require(typeof(value) === T, path, "expected $(T)")
function collection(values, T, path, size=nothing)
    require(values isa Tuple || values isa AbstractVector, path, "expected tuple or vector")
    result = Tuple(values)
    size === nothing || require(length(result) == size, path, "incorrect M0 collection size")
    for (i, value) in enumerate(result)
        typed(value, T, "$path/$(i-1)")
    end
    result
end
function unique_ids(values, key, path)
    seen = Set{String}()
    for (i, value) in enumerate(values)
        id = getfield(value, key)
        require(!(id in seen), "$path/$(i-1)/$key", "duplicate identifier", "DUPLICATE_ID")
        push!(seen, id)
    end
end
function numeric(value)
    require(value isa FIXED_INTEGERS || value isa Float64, "/value", "expected fixed-width integer or Float64")
    if value isa FIXED_INTEGERS
        require(-MAX_INTEGER <= value <= MAX_INTEGER, "/value", "integer exceeds P01 safe range", "INTEGER_RANGE")
        value = Int64(value)
    else
        require(isfinite(value), "/value", "expected finite binary64", "NUMBER_RANGE")
    end
    require(value >= 0, "/value", "expected nonnegative quantity")
    value
end
struct Quantity <: BioIRValue
    value::Union{Int64,Float64}
    unit::String
    function Quantity(; value, unit)
        value = numeric(value)
        token(unit, ("L", "molecule", "molecule/s", "1/s"), "/unit")
        new(value, unit)
    end
end
function quantity(value, units, path; positive=false)
    typed(value, Quantity, path)
    token(value.unit, units, path * "/unit")
    positive && require(value.value > 0, path * "/value", "volume must be positive")
end
struct Port <: BioIRValue
    id::String
    kind::String
    function Port(; id, kind="molecular_count")
        identifier(id, "/id"); token(kind, ("molecular_count",), "/kind")
        new(id, kind)
    end
end
struct Compartment <: BioIRValue
    id::String
    volume::Quantity
    kind::String
    function Compartment(; id, volume, kind="representative_cell")
        identifier(id, "/id"); token(kind, ("representative_cell",), "/kind")
        quantity(volume, ("L",), "/volume"; positive=true)
        new(id, volume, kind)
    end
end
struct Species <: BioIRValue
    id::String
    compartment::String
    ports::Tuple{Port}
    function Species(; id, compartment, ports)
        identifier(id, "/id"); identifier(compartment, "/compartment")
        ports = collection(ports, Port, "/ports", 1)
        unique_ids(ports, :id, "/ports")
        new(id, compartment, ports)
    end
end
struct Parameter <: BioIRValue
    id::String
    unit::String
    function Parameter(; id, unit)
        identifier(id, "/id"); token(unit, ("molecule/s", "1/s"), "/unit")
        new(id, unit)
    end
end
struct PortReference <: BioIRValue
    species::String
    port::String
    function PortReference(; species, port)
        identifier(species, "/species"); identifier(port, "/port")
        new(species, port)
    end
end
struct BioIRFunction <: BioIRValue
    id::String
    kind::String
    target::PortReference
    parameter::String
    function BioIRFunction(; id, kind, target, parameter)
        identifier(id, "/id")
        token(kind, ("constitutive_production", "first_order_decay"), "/kind")
        typed(target, PortReference, "/target"); identifier(parameter, "/parameter")
        new(id, kind, target, parameter)
    end
end
struct ParameterAssignment <: BioIRValue
    parameter::String
    quantity::Quantity
    function ParameterAssignment(; parameter, quantity)
        identifier(parameter, "/parameter")
        BioIR.quantity(quantity, ("molecule/s", "1/s"), "/quantity")
        new(parameter, quantity)
    end
end
struct InitialCount <: BioIRValue
    species::String
    quantity::Quantity
    function InitialCount(; species, quantity)
        identifier(species, "/species")
        BioIR.quantity(quantity, ("molecule",), "/quantity")
        new(species, quantity)
    end
end
struct Observable <: BioIRValue
    id::String
    target::PortReference
    function Observable(; id, target)
        identifier(id, "/id"); typed(target, PortReference, "/target")
        new(id, target)
    end
end
"""Claimed Design identity; digest correspondence remains unverified."""
struct DesignReference <: BioIRValue
    id::String
    revision::Int64
    digest::String
    function DesignReference(; id, revision, digest)
        identifier(id, "/id"); revision = revision_number(revision)
        require(digest isa String && isvalid(digest) && occursin(r"\A[0-9a-f]{64}\z", digest), "/digest", "expected lowercase SHA-256 syntax")
        new(id, revision, digest)
    end
end
function header(kind, expected, version, id, revision)
    token(kind, (expected,), "/kind"); token(version, ("0.1.0",), "/schema_version")
    identifier(id, "/id")
    revision_number(revision)
end
function target_reference(target, species, path)
    lookup = Dict(s.id => s for s in species)
    require(haskey(lookup, target.species), path * "/species", "unknown species", "REFERENCE")
    require(any(p.id == target.port for p in lookup[target.species].ports), path * "/port", "unknown port", "REFERENCE")
end
"""Validated uncommitted Design content; no digest is assigned."""
struct DesignContent <: BioIRValue
    kind::String
    schema_version::String
    id::String
    revision::Int64
    compartments::Tuple{Compartment}
    species::Tuple{Species}
    parameters::NTuple{2,Parameter}
    functions::NTuple{2,BioIRFunction}
    function DesignContent(; id, revision, compartments, species, parameters, functions, kind="Design", schema_version="0.1.0")
        revision = header(kind, "Design", schema_version, id, revision)
        compartments = collection(compartments, Compartment, "/compartments", 1)
        species = collection(species, Species, "/species", 1)
        parameters = collection(parameters, Parameter, "/parameters", 2)
        functions = collection(functions, BioIRFunction, "/functions", 2)
        for (values, path) in ((compartments,"/compartments"), (species,"/species"), (parameters,"/parameters"), (functions,"/functions"))
            unique_ids(values, :id, path)
        end
        for (i, s) in enumerate(species)
            require(any(c.id == s.compartment for c in compartments), "/species/$(i-1)/compartment", "unknown compartment", "REFERENCE")
        end
        lookup = Dict(p.id => p for p in parameters)
        kinds = Set{String}(); used = Set{String}()
        for (i, f) in enumerate(functions)
            path = "/functions/$(i-1)"
            target_reference(f.target, species, path * "/target")
            require(haskey(lookup, f.parameter), path * "/parameter", "unknown parameter", "REFERENCE")
            unit = f.kind == "constitutive_production" ? "molecule/s" : "1/s"
            require(lookup[f.parameter].unit == unit, path * "/parameter", "incorrect function parameter unit", "UNIT")
            require(!(f.kind in kinds) && !(f.parameter in used), path, "roles and parameters must be distinct", "FUNCTION_ROLE")
            push!(kinds, f.kind); push!(used, f.parameter)
        end
        require(used == Set(keys(lookup)), "/parameters", "unused parameters", "REFERENCE")
        new(kind, schema_version, id, revision, compartments, species, parameters, functions)
    end
end
"""Uncommitted Experiment checked against a local, unverified Design context.

The required source_design context is neither stored nor serialized. This does
not verify digest integrity or establish trusted committed identity.
"""
struct ExperimentContent <: BioIRValue
    kind::String
    schema_version::String
    id::String
    revision::Int64
    design::DesignReference
    parameters::NTuple{2,ParameterAssignment}
    initial_counts::Tuple{InitialCount}
    observables::Tuple{Vararg{Observable}}
    interventions::Tuple{}
    function ExperimentContent(; id, revision, design, parameters, initial_counts, observables, interventions, source_design, kind="Experiment", schema_version="0.1.0")
        revision = header(kind, "Experiment", schema_version, id, revision)
        typed(design, DesignReference, "/design"); typed(source_design, DesignContent, "/source_design")
        parameters = collection(parameters, ParameterAssignment, "/parameters", 2)
        initial_counts = collection(initial_counts, InitialCount, "/initial_counts", 1)
        observables = collection(observables, Observable, "/observables")
        require((interventions isa Tuple || interventions isa AbstractVector) && isempty(interventions), "/interventions", "M0 requires empty interventions")
        for key in (:id, :revision)
            require(getfield(design, key) == getfield(source_design, key), "/design/$key", "reference differs from local Design context", "DESIGN_REFERENCE")
        end
        unique_ids(parameters, :parameter, "/parameters")
        unique_ids(initial_counts, :species, "/initial_counts")
        unique_ids(observables, :id, "/observables")
        lookup = Dict(p.id => p for p in source_design.parameters)
        for (i, assignment) in enumerate(parameters)
            path = "/parameters/$(i-1)"
            require(haskey(lookup, assignment.parameter), path * "/parameter", "unknown parameter", "REFERENCE")
            require(assignment.quantity.unit == lookup[assignment.parameter].unit, path * "/quantity/unit", "assignment unit differs from Design", "UNIT")
        end
        require(Set(p.parameter for p in parameters) == Set(keys(lookup)), "/parameters", "assignments must be exhaustive", "REFERENCE")
        require(Set(c.species for c in initial_counts) == Set(s.id for s in source_design.species), "/initial_counts", "initial counts must cover Design species", "REFERENCE")
        for (i, observable) in enumerate(observables)
            target_reference(observable.target, source_design.species, "/observables/$(i-1)/target")
        end
        new(kind, schema_version, id, revision, design, parameters, initial_counts, observables, ())
    end
end
encode(value::BioIRValue) = Dict{String,Any}(string(key) => encode(getfield(value, key)) for key in fieldnames(typeof(value)))
encode(value::Tuple) = Any[encode(item) for item in value]
encode(value::Union{String,Int64,Float64}) = value
"""Export fresh JSON-compatible content, preserving array declaration order."""
to_dict(value::Union{DesignContent,ExperimentContent}) = encode(value)
"""Ordinary JSON content, without canonicalization, envelopes or digests."""
to_json(value::Union{DesignContent,ExperimentContent}) = JSON.json(to_dict(value))
end
