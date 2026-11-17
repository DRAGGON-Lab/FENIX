"""Immutable M0 mathematical FIR under ratified P02/P03. No execution API."""
module FIR
using SHA
using JSON
import ..BioIR
export FIRModel, FIRDocument, FIRValidationError, from_dict, from_json, to_dict,
       to_json, normalized, canonical_model_bytes, identity_bytes, validate_sources,
       require_capability

struct FIRValidationError <: Exception
    category::String
    path::String
    message::String
end
Base.showerror(io::IO, e::FIRValidationError) = print(io, e.category, " at ", isempty(e.path) ? "/" : e.path, ": ", e.message)
_need(ok, path, message, category="SCHEMA") = ok || throw(FIRValidationError(category, path, message))
_pointer(path, key) = path * "/" * replace(string(key), "~" => "~0", "/" => "~1")
function _portable(f)
    try
        f()
    catch error
        error isa BioIR.BioIRValidationError || rethrow()
        throw(FIRValidationError(error.category, error.path, error.message))
    end
end
function _object(value, required, path, optional=())
    _need(value isa AbstractDict, path, "expected object")
    for key in sort!(collect(required))
        _need(haskey(value, key), _pointer(path, key), "required member missing")
    end
    for key in keys(value)
        _need(key isa String, path, "expected string member name")
        _need(key in required || key in optional, _pointer(path, key), "unknown member")
    end
    value
end
function _array(value, path, size=nothing)
    _need(value isa AbstractVector || value isa Tuple, path, "expected array")
    size === nothing || _need(length(value) == size, path, "incorrect M0 collection size")
    value
end
function _text(value, path, choices=nothing)
    _need(value isa String, path, "expected string")
    _need(isvalid(value), path, "invalid Unicode", "INVALID_UNICODE")
    choices === nothing || _need(value in choices, path, "unsupported token")
    value
end
function _id(value, path)
    _text(value, path)
    _need(occursin(r"\A[A-Za-z][A-Za-z0-9_-]{0,63}\z", value), path, "expected ASCII identifier")
end
function _number(value, path; nonnegative=true)
    _need(value isa Float64, path, "expected native binary64")
    _need(isfinite(value), path, "expected finite binary64", "NUMBER_RANGE")
    nonnegative && _need(value >= 0, path, "expected nonnegative quantity")
    value
end
function _expression(value, path)
    _need(value isa AbstractDict, path, "expected expression object")
    _need(haskey(value, "op"), path * "/op", "required expression operator")
    op = _text(value["op"], path * "/op", ("parameter", "state", "multiply", "subtract"))
    if op in ("parameter", "state")
        _object(value, ("op", "id"), path)
        _id(value["id"], path * "/id")
    else
        _object(value, ("op", "left", "right"), path)
        _expression(value["left"], path * "/left")
        _expression(value["right"], path * "/right")
    end
end
const ASSUMPTIONS = ("single_representative_cell", "well_mixed", "fixed_volume", "constant_rates", "no_interventions")
function _model_structure(m)
    _object(m, ("schema_version", "time_unit", "states", "parameters", "reactions", "equations", "observables", "assumptions", "capabilities"), "/model")
    _text(m["schema_version"], "/model/schema_version", ("0.1.0",))
    _text(m["time_unit"], "/model/time_unit", ("s",))
    for (i, s) in enumerate(_array(m["states"], "/model/states", 1))
        p = "/model/states/$(i-1)"
        _object(s, ("id", "quantity", "scope", "unit", "initial"), p)
        for (key, token) in (("id", "x"), ("quantity", "molecular_count"), ("scope", "representative_cell"), ("unit", "molecule"))
            _text(s[key], p * "/" * key, (token,))
        end
        _number(s["initial"], p * "/initial")
    end
    for (i, parameter) in enumerate(_array(m["parameters"], "/model/parameters", 2))
        p = "/model/parameters/$(i-1)"
        _object(parameter, ("id", "value", "unit"), p)
        _text(parameter["id"], p * "/id", ("alpha", "beta"))
        _text(parameter["unit"], p * "/unit", ("molecule/s", "1/s"))
        _number(parameter["value"], p * "/value")
    end
    for (i, r) in enumerate(_array(m["reactions"], "/model/reactions", 2))
        p = "/model/reactions/$(i-1)"
        _object(r, ("id", "stoichiometry", "flux"), p)
        _text(r["id"], p * "/id", ("production", "decay"))
        _object(r["stoichiometry"], ("x",), p * "/stoichiometry")
        value = _number(r["stoichiometry"]["x"], p * "/stoichiometry/x"; nonnegative=false)
        _need(value in (-1.0, 1.0), p * "/stoichiometry/x", "expected unit stoichiometry")
        _expression(r["flux"], p * "/flux")
    end
    for (i, e) in enumerate(_array(m["equations"], "/model/equations", 1))
        p = "/model/equations/$(i-1)"
        _object(e, ("state", "unit", "rhs"), p)
        _id(e["state"], p * "/state")
        _text(e["unit"], p * "/unit", ("molecule/s",))
        _expression(e["rhs"], p * "/rhs")
    end
    for (i, o) in enumerate(_array(m["observables"], "/model/observables"))
        p = "/model/observables/$(i-1)"
        _object(o, ("id", "state", "unit"), p)
        _id(o["id"], p * "/id"); _id(o["state"], p * "/state")
        _text(o["unit"], p * "/unit", ("molecule",))
    end
    a = _array(m["assumptions"], "/model/assumptions", 5)
    for (i, token) in enumerate(a)
        _text(token, "/model/assumptions/$(i-1)", ASSUMPTIONS)
    end
    _need(length(Set(a)) == 5, "/model/assumptions", "assumptions must be distinct")
    c = _object(m["capabilities"], ("ode", "ssa"), "/model/capabilities")
    _need(c["ode"] === true, "/model/capabilities/ode", "ODE must be declared")
    _need(c["ssa"] === false, "/model/capabilities/ssa", "SSA is not supported")
    m
end
function _unique(values, key, path)
    result = Dict{String,Any}()
    for (i, item) in enumerate(values)
        id = item[key]
        _need(!haskey(result, id), "$path/$(i-1)/$key", "duplicate identifier", "DUPLICATE_ID")
        result[id] = item
    end
    result
end
_parameter(id) = Dict{String,Any}("op" => "parameter", "id" => id)
_state(id) = Dict{String,Any}("op" => "state", "id" => id)
_decay() = Dict{String,Any}("op" => "multiply", "left" => _parameter("beta"), "right" => _state("x"))
_rhs() = Dict{String,Any}("op" => "subtract", "left" => _parameter("alpha"), "right" => _decay())
function _references(expr, path, states, parameters)
    if expr["op"] in ("parameter", "state")
        namespace = expr["op"] == "parameter" ? parameters : states
        _need(haskey(namespace, expr["id"]), path * "/id", "unknown typed reference", "REFERENCE")
    else
        _references(expr["left"], path * "/left", states, parameters)
        _references(expr["right"], path * "/right", states, parameters)
    end
end
function _model_semantics(m)
    states = _unique(m["states"], "id", "/model/states")
    parameters = _unique(m["parameters"], "id", "/model/parameters")
    reactions = _unique(m["reactions"], "id", "/model/reactions")
    equations = _unique(m["equations"], "state", "/model/equations")
    _unique(m["observables"], "id", "/model/observables")
    _need(Set(keys(parameters)) == Set(("alpha", "beta")), "/model/parameters", "missing parameter role", "ROLE")
    _need(Set(keys(reactions)) == Set(("production", "decay")), "/model/reactions", "missing reaction role", "ROLE")
    _need(Set(keys(equations)) == Set(("x",)), "/model/equations/0/state", "unknown equation state", "REFERENCE")
    for (i, p) in enumerate(m["parameters"])
        _need(p["unit"] == (p["id"] == "alpha" ? "molecule/s" : "1/s"), "/model/parameters/$(i-1)/unit", "incorrect role unit", "UNIT")
    end
    for (collection, field) in (("reactions", "flux"), ("equations", "rhs"))
        for (i, item) in enumerate(m[collection])
            _references(item[field], "/model/$collection/$(i-1)/$field", states, parameters)
        end
    end
    for (i, o) in enumerate(m["observables"])
        _need(haskey(states, o["state"]), "/model/observables/$(i-1)/state", "unknown observable state", "REFERENCE")
    end
    for (i, r) in enumerate(m["reactions"])
        production = r["id"] == "production"
        p = "/model/reactions/$(i-1)"
        _need(r["stoichiometry"]["x"] == (production ? 1.0 : -1.0), p * "/stoichiometry/x", "incorrect reaction sign", "STOICHIOMETRY")
        _need(r["flux"] == (production ? _parameter("alpha") : _decay()), p * "/flux", "incorrect exact M0 flux template", "TEMPLATE")
    end
    _need(m["equations"][1]["rhs"] == _rhs(), "/model/equations/0/rhs", "incorrect exact M0 derivative template", "TEMPLATE")
    m
end
function _provenance(p)
    _object(p, (), "/provenance", ("design_digest", "experiment_digest", "compiler", "symbol_map", "display_labels"))
    for key in ("design_digest", "experiment_digest")
        haskey(p, key) || continue
        v = _text(p[key], "/provenance/" * key)
        _need(occursin(r"\A[0-9a-f]{64}\z", v), "/provenance/" * key, "expected lowercase SHA-256 digest")
    end
    if haskey(p, "compiler")
        c = _object(p["compiler"], ("name", "version"), "/provenance/compiler")
        for key in ("name", "version")
            _text(c[key], "/provenance/compiler/" * key)
        end
    end
    if haskey(p, "symbol_map")
        _need(haskey(p, "design_digest"), "/provenance", "symbol map requires Design digest")
        mapping = _object(p["symbol_map"], ("states", "parameters"), "/provenance/symbol_map")
        for (i, s) in enumerate(_array(mapping["states"], "/provenance/symbol_map/states", 1))
            path = "/provenance/symbol_map/states/$(i-1)"
            _object(s, ("fir_state_id", "bioir_species_id", "bioir_port_id", "bioir_compartment_id"), path)
            _text(s["fir_state_id"], path * "/fir_state_id", ("x",))
            for key in ("bioir_species_id", "bioir_port_id", "bioir_compartment_id")
                _id(s[key], path * "/" * key)
            end
        end
        entries = _array(mapping["parameters"], "/provenance/symbol_map/parameters", 2)
        for (i, entry) in enumerate(entries)
            path = "/provenance/symbol_map/parameters/$(i-1)"
            _object(entry, ("fir_parameter_id", "bioir_parameter_id", "bioir_function_id", "bioir_function_kind"), path)
            _text(entry["fir_parameter_id"], path * "/fir_parameter_id", ("alpha", "beta"))
            _id(entry["bioir_parameter_id"], path * "/bioir_parameter_id")
            _id(entry["bioir_function_id"], path * "/bioir_function_id")
            _text(entry["bioir_function_kind"], path * "/bioir_function_kind", ("constitutive_production", "first_order_decay"))
        end
        _need(Set(e["fir_parameter_id"] for e in entries) == Set(("alpha", "beta")), "/provenance/symbol_map/parameters", "map must cover both parameter roles")
    end
    if haskey(p, "display_labels")
        labels = _object(p["display_labels"], (), "/provenance/display_labels", ("observables",))
        if haskey(labels, "observables")
            items = labels["observables"]
            _need(items isa AbstractDict, "/provenance/display_labels/observables", "expected object")
            for (key, value) in items
                path = _pointer("/provenance/display_labels/observables", key)
                _id(key, path); _text(value, path)
            end
        end
    end
    p
end

# Recursively immutable snapshots. The wrapper distinguishes empty objects from arrays.
struct _Object
    entries::Tuple
end
_freeze(value::AbstractDict) = _Object(Tuple(key => _freeze(item) for (key, item) in value))
_freeze(value::Union{AbstractVector,Tuple}) = Tuple(_freeze(item) for item in value)
_freeze(value::Union{String,Float64,Bool,Nothing}) = value
_thaw(value::_Object) = Dict{String,Any}(key => _thaw(item) for (key, item) in value.entries)
_thaw(value::Tuple) = Any[_thaw(item) for item in value]
_thaw(value) = value

struct FIRModel
    _data::_Object
    function FIRModel(raw)
        _model_structure(raw)
        _model_semantics(raw)
        new(_freeze(raw))
    end
end
function validate_sources end
struct FIRDocument
    model::FIRModel
    _provenance::Union{Nothing,_Object}
    function FIRDocument(; model, provenance=nothing)
        native = model isa FIRModel ? model : FIRModel(model)
        if provenance !== nothing
            _provenance(provenance)
            observables = Set(o["id"] for o in to_dict(native)["observables"])
            labels = get(get(provenance, "display_labels", Dict()), "observables", Dict())
            for key in keys(labels)
                _need(key in observables, _pointer("/provenance/display_labels/observables", key),
                      "display label refers to undeclared observable", "REFERENCE")
            end
        end
        new(native, provenance === nothing ? nothing : _freeze(provenance))
    end
end
to_dict(model::FIRModel) = _thaw(model._data)
function to_dict(document::FIRDocument)
    value = Dict{String,Any}("model" => to_dict(document.model))
    document._provenance === nothing || (value["provenance"] = _thaw(document._provenance))
    value
end
to_json(value::Union{FIRModel,FIRDocument}) = JSON.json(to_dict(value))
from_dict(::Type{FIRModel}, raw) = FIRModel(raw)
function from_dict(::Type{FIRDocument}, raw; design=nothing, experiment=nothing)
    _object(raw, ("model",), "", ("provenance",))
    # All structure precedes semantics, including the separate provenance shape.
    _model_structure(raw["model"])
    haskey(raw, "provenance") && _provenance(raw["provenance"])
    document = FIRDocument(model=raw["model"], provenance=get(raw, "provenance", nothing))
    if design !== nothing || experiment !== nothing
        _need(design !== nothing && experiment !== nothing, "/provenance", "source-aware validation requires both source documents", "SOURCE_REQUIRED")
        validate_sources(document; design=design, experiment=experiment)
    end
    document
end
function from_json(T::Type{<:Union{FIRModel,FIRDocument}}, raw; kwargs...)
    value = _portable() do
        BioIR.parse_json(raw; numeric_policy=:p03)
    end
    from_dict(T, value; kwargs...)
end
"""Copy and sort only the six declaration collections ratified in P03."""
function normalized(model::FIRModel)
    value = to_dict(model)
    utf16(s) = Tuple(transcode(UInt16, s))
    for key in ("states", "parameters", "reactions", "observables")
        sort!(value[key]; by=item -> utf16(item["id"]))
    end
    sort!(value["equations"]; by=item -> utf16(item["state"]))
    sort!(value["assumptions"]; by=utf16)
    FIRModel(value)
end
normalized(document::FIRDocument) = FIRDocument(model=normalized(document.model), provenance=document._provenance === nothing ? nothing : _thaw(document._provenance))
canonical_model_bytes(model::FIRModel) = _portable(() -> BioIR.canonical_bytes(to_dict(normalized(model))))
canonical_model_bytes(document::FIRDocument) = canonical_model_bytes(document.model)
function identity_bytes(model::FIRModel)
    _portable(() -> BioIR.canonical_bytes(Dict("domain" => "fenix.fir", "canonicalization_version" => "0.1.0", "model" => to_dict(normalized(model)))))
end
identity_bytes(document::FIRDocument) = identity_bytes(document.model)
function Base.getproperty(value::FIRModel, name::Symbol)
    name === :digest && return bytes2hex(sha256(identity_bytes(value)))
    getfield(value, name)
end
function Base.getproperty(value::FIRDocument, name::Symbol)
    name === :digest && return getfield(value, :model).digest
    name === :provenance && return getfield(value, :_provenance) === nothing ? nothing : _thaw(getfield(value, :_provenance))
    getfield(value, name)
end
function require_capability(value::Union{FIRModel,FIRDocument}, profile)
    _need(profile isa String && profile == "ode", "/profile", "unsupported execution profile", "UNSUPPORTED_PROFILE")
    value
end
end # module FIR
