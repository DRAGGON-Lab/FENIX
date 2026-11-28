struct ValidationError <: Exception
    category::String
    path::String
end
Base.showerror(io::IO, error::ValidationError) = print(io, error.category, " at ", error.path)
_need(ok, category, path) = ok || throw(ValidationError(category, path))
_pointer(path, key) = BioIR._json_pointer(path, key)
_sha(bytes) = bytes2hex(sha256(bytes))
_sha(text::String) = _sha(codeunits(text))
_emit(value) = Results._emit(value)
_isnumber(value) = value isa Real && !(value isa Bool)
_bits(a::Float64, b::Float64) = reinterpret(UInt64, a) == reinterpret(UInt64, b)

function _decode(raw::Union{String,Vector{UInt8}}, policy=:source)
    parsed = try
        BioIR._parse_json_with_policy(raw, :community_tokens)
    catch error
        error isa BioIR.BioIRValidationError || rethrow()
        category = Dict("JSON_SYNTAX" => "JSON", "INVALID_UNICODE" => (error.path == "" && error.message == "input is not strict UTF-8" ? "JSON" : "UNICODE"))
        category = get(category, error.category, error.category)
        # Match the bounded catalog's document-relative lexical diagnostics.
        throw(ValidationError(category, ""))
    end
    _numbers(parsed, policy, "")
end

function _numbers(value, policy, path)
    exact = policy === :manifest && (path in (
        "/execution/max_nfev", "/evaluations/nfev", "/backend/solver/options/maxiters",
        "/sources/design/revision", "/sources/experiment/revision",
    ) || startswith(path, "/backend/evaluations/"))
    if exact
        _need(value isa BioIR._JSONNumberToken && !occursin(r"[.eE]", value.raw), "INTEGER_TOKEN", path)
        return parse(BigInt, value.raw)
    elseif value isa BioIR._JSONNumberToken
        token = value.raw
        integral = !occursin(r"[.eE]", token)
        if policy === :source && integral
            number = tryparse(Int64, token)
            _need(number !== nothing && -BioIR.MAX_INTEGER <= number <= BioIR.MAX_INTEGER, "SOURCE_INTEGER", "")
            return token == "-0" ? -0.0 : number
        elseif policy === :transport && integral
            return token == "-0" ? -0.0 : parse(BigInt, token)
        end
        try
            return BioIR._json_binary64(token, path)
        catch error
            error isa BioIR.BioIRValidationError || rethrow()
            diagnostic = policy in (:result, :manifest) && error.category == "NUMBER_RANGE" ? path : ""
            throw(ValidationError(error.category, diagnostic))
        end
    elseif value isa AbstractDict
        return Dict{String,Any}(key => _numbers(item, policy, _pointer(path, key)) for (key,item) in value)
    elseif value isa AbstractVector
        return Any[_numbers(item, policy, _pointer(path, i-1)) for (i,item) in enumerate(value)]
    end
    value
end

function _equal(a, b)
    if a isa Bool || b isa Bool
        return a isa Bool && b isa Bool && a == b
    elseif a isa AbstractDict && b isa AbstractDict
        return keys(a) == keys(b) && all(_equal(a[k], b[k]) for k in keys(a))
    elseif a isa AbstractVector && b isa AbstractVector
        return length(a) == length(b) && all(_equal(x,y) for (x,y) in zip(a,b))
    end
    a == b
end

const CONTRACTS = Dict(name => JSON.parsefile(joinpath(@__DIR__, "schemas", "$name-m1.schema.json"))
                       for name in ("bioir", "fir", "ode-result", "run-manifest"))

# Interpreter for the finite vocabulary used by the four bundled contracts.
# Only local definition references are permitted.
function _validate(name, value)
    root = CONTRACTS[name]
    _validate(root, root, value, "")
end
function _matches(root, schema, value, path)
    try
        _validate(root, schema, value, path)
        true
    catch error
        error isa ValidationError || rethrow()
        false
    end
end
function _type_matches(kind, value)
    kind == "object" && return value isa AbstractDict
    kind == "array" && return value isa AbstractVector
    kind == "string" && return value isa String
    kind == "boolean" && return value isa Bool
    kind == "null" && return value === nothing
    kind == "number" && return _isnumber(value)
    kind == "integer" && return _isnumber(value) && isinteger(value)
    error("Unsupported bundled schema type: $kind")
end
function _validate(root, schema, value, path)
    check(ok) = _need(ok, "SCHEMA", path)
    if haskey(schema, "\$ref")
        prefix = "#/definitions/"
        ref = schema["\$ref"]
        startswith(ref, prefix) || error("External schema resolution is forbidden")
        return _validate(root, root["definitions"][ref[length(prefix)+1:end]], value, path)
    end
    if haskey(schema, "oneOf")
        check(count(choice -> _matches(root, choice, value, path), schema["oneOf"]) == 1)
    end
    for constraint in get(schema, "allOf", ())
        _validate(root, constraint, value, path)
    end
    if haskey(schema, "if")
        branch = _matches(root, schema["if"], value, path) ? "then" : "else"
        _validate(root, get(schema, branch, Dict()), value, path)
    end
    if haskey(schema, "not")
        check(!_matches(root, schema["not"], value, path))
    end
    haskey(schema, "const") && check(_equal(value, schema["const"]))
    haskey(schema, "enum") && check(any(choice -> _equal(value, choice), schema["enum"]))
    if haskey(schema, "type")
        kinds = schema["type"]
        check(kinds isa String ? _type_matches(kinds, value) : any(k -> _type_matches(k,value), kinds))
    end
    if value isa AbstractDict
        check(all(k -> haskey(value,k), get(schema,"required",())))
        fields = get(schema, "properties", Dict())
        for (key,item) in value
            if haskey(fields,key)
                _validate(root, fields[key], item, _pointer(path,key))
            else
                check(get(schema,"additionalProperties",true))
            end
        end
    elseif value isa AbstractVector
        check(get(schema,"minItems",0) <= length(value) <= get(schema,"maxItems",Inf))
        if get(schema,"uniqueItems",false)
            check(!any(_equal(value[i],value[j]) for i in eachindex(value) for j in 1:i-1))
        end
        item_schema = get(schema,"items",Dict())
        for (index,item) in enumerate(value)
            _validate(root, item_schema, item, _pointer(path,index-1))
        end
    elseif value isa String
        check(get(schema,"minLength",0) <= length(value) <= get(schema,"maxLength",Inf))
        haskey(schema,"pattern") && check(occursin(Regex(schema["pattern"]),value))
    elseif _isnumber(value)
        _need(isfinite(value), "NUMBER_RANGE", path)
        check(get(schema,"minimum",-Inf) <= value <= get(schema,"maximum",Inf))
        haskey(schema,"exclusiveMinimum") && check(value > schema["exclusiveMinimum"])
    end
    nothing
end
