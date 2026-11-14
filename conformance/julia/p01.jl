# Independent Julia P01 reference validator; no Fenix or Python imports.
module P01Reference
using JSON, JSONSchema, SHA
export Rejection, strict_parse, validate_design, validate_experiment, evaluate

struct Rejection <: Exception
    category::String
    path::String
end
reject(category, path="") = throw(Rejection(category, path))
pointer(parent, key) = parent * "/" * replace(string(key), "~" => "~0", "/" => "~1")
mutable struct Cursor
    bytes::Vector{UInt8}
    i::Int
end
peek(c) = c.i <= length(c.bytes) ? c.bytes[c.i] : 0x00
function spaces!(c)
    while peek(c) in (0x20, 0x09, 0x0a, 0x0d)
        c.i += 1
    end
end
function take!(c, byte)
    peek(c) == byte || reject("JSON_SYNTAX")
    c.i += 1
end
function string!(c, path)
    start = c.i
    take!(c, 0x22)
    while true
        b = peek(c)
        b == 0x00 && reject("JSON_SYNTAX")
        if b == 0x22
            c.i += 1
            raw = String(c.bytes[start:c.i-1])
            # Validate escape pairs before JSON decoding can replace/accept them.
            units = collect(eachmatch(r"\\u([0-9a-fA-F]{4})|\\.", raw))
            i = 1
            while i <= length(units)
                m = units[i]
                if m.captures[1] !== nothing
                    u = parse(UInt16, m.captures[1]; base=16)
                    if 0xd800 <= u <= 0xdbff
                        i < length(units) || reject("INVALID_UNICODE", path)
                        next = units[i+1]
                        next.offset == m.offset + 6 && next.captures[1] !== nothing || reject("INVALID_UNICODE", path)
                        low = parse(UInt16, next.captures[1]; base=16)
                        0xdc00 <= low <= 0xdfff || reject("INVALID_UNICODE", path)
                        i += 1
                    elseif 0xdc00 <= u <= 0xdfff
                        reject("INVALID_UNICODE", path)
                    end
                end
                i += 1
            end
            return try
                JSON.parse(raw)
            catch
                reject("JSON_SYNTAX")
            end
        elseif b == 0x5c
            c.i += 1
            peek(c) != 0x00 || reject("JSON_SYNTAX")
        elseif b < 0x20
            reject("JSON_SYNTAX")
        end
        c.i += 1
    end
end
function number!(c)
    start = c.i
    while peek(c) in codeunits("0123456789.eE+-")
        c.i += 1
    end
    raw = String(c.bytes[start:c.i-1])
    occursin(r"^-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?$", raw) || reject("JSON_SYNTAX")
    if !occursin(r"[.eE]", raw)
        digits = startswith(raw, "-") ? raw[2:end] : raw
        (length(digits) > 16 || (length(digits) == 16 && digits > "9007199254740991")) && reject("INTEGER_RANGE")
        return parse(Int64, raw)
    end
    value = tryparse(Float64, raw)
    if value === nothing
        # Julia reports ERANGE for both overflow and rounding to zero. Classify
        # using the lexical decimal order, without first losing the input value.
        parts = split(lowercase(raw), 'e')
        mantissa = replace(parts[1], "-" => "")
        exponent = length(parts) == 2 ? parse(BigInt, parts[2]) : big(0)
        digits = replace(mantissa, "." => "")
        first_nonzero = findfirst(ch -> ch != '0', digits)
        if first_nonzero === nothing
            return startswith(raw, "-") ? -0.0 : 0.0
        end
        point = findfirst(==('.'), mantissa)
        before_point = point === nothing ? length(mantissa) : point - 1
        order = before_point - first_nonzero + exponent
        reject(order < 0 ? "NUMBER_UNDERFLOW" : "NUMBER_RANGE")
    end
    isfinite(value) || reject("NUMBER_RANGE")
    mantissa = split(lowercase(raw), 'e')[1]
    value == 0 && any(ch -> ch in '1':'9', mantissa) && reject("NUMBER_UNDERFLOW")
    return value
end
function value!(c, path="")
    spaces!(c)
    b = peek(c)
    if b == 0x22
        return string!(c, path)
    elseif b == 0x7b
        c.i += 1; spaces!(c)
        out = Dict{String,Any}()
        if peek(c) != 0x7d
            while true
                key = string!(c, path)
                child = pointer(path, key)
                haskey(out, key) && reject("DUPLICATE_KEY", child)
                spaces!(c); take!(c, 0x3a)
                out[key] = value!(c, child)
                spaces!(c)
                peek(c) != 0x2c && break
                c.i += 1; spaces!(c)
            end
        end
        take!(c, 0x7d)
        return out
    elseif b == 0x5b
        c.i += 1; spaces!(c)
        out = Any[]
        if peek(c) != 0x5d
            while true
                push!(out, value!(c, pointer(path, length(out))))
                spaces!(c)
                peek(c) != 0x2c && break
                c.i += 1
            end
        end
        take!(c, 0x5d)
        return out
    elseif b == 0x2d || b in 0x30:0x39
        return number!(c)
    else
        for (word, value) in (("true", true), ("false", false), ("null", nothing))
            bytes = codeunits(word)
            stop = c.i + length(bytes) - 1
            if stop <= length(c.bytes) && c.bytes[c.i:stop] == bytes
                c.i = stop + 1
                return value
            end
        end
        reject("JSON_SYNTAX")
    end
end
function strict_parse(raw::Vector{UInt8})
    isvalid(String(copy(raw))) || reject("INVALID_UNICODE")
    c = Cursor(raw, 1)
    value = value!(c)
    spaces!(c)
    c.i == length(raw) + 1 || reject("JSON_SYNTAX")
    return value
end

# JCS for P01 content identity, not FENIX FIR normalization (pending P03).
function json_string(value)
    io = IOBuffer(); write(io, '"')
    escapes = Dict('"' => "\\\"", '\\' => "\\\\", '\b' => "\\b", '\t' => "\\t", '\n' => "\\n", '\f' => "\\f", '\r' => "\\r")
    for ch in value
        if haskey(escapes, ch)
            write(io, escapes[ch])
        elseif UInt32(ch) < 0x20
            write(io, "\\u", string(UInt32(ch); base=16, pad=4))
        else
            write(io, ch)
        end
    end
    write(io, '"'); String(Base.take!(io))
end
function number_string(value::Float64)
    isfinite(value) || reject("NUMBER_RANGE")
    value == 0 && return "0"
    negative = value < 0
    raw = lowercase(string(abs(value)))
    parts = split(raw, 'e')
    exponent = length(parts) == 2 ? parse(Int, parts[2]) : 0
    mantissa = split(parts[1], '.')
    digits = join(mantissa)
    leading = length(digits) - length(lstrip(digits, '0'))
    position = length(mantissa[1]) + exponent - leading
    digits = rstrip(lstrip(digits, '0'), '0')
    n = length(digits)
    text = if 0 < position <= 21
        position >= n ? digits * repeat("0", position-n) : digits[1:position] * "." * digits[position+1:end]
    elseif -6 < position <= 0
        "0." * repeat("0", -position) * digits
    else
        digits[1:1] * (n > 1 ? "." * digits[2:end] : "") * "e" * (position-1 >= 0 ? "+" : "") * string(position-1)
    end
    (negative ? "-" : "") * text
end
function canonical(value)
    value === nothing && return "null"
    value isa Bool && return value ? "true" : "false"
    value isa AbstractString && return json_string(value)
    value isa Integer && return string(value)
    value isa Float64 && return number_string(value)
    value isa AbstractVector && return "[" * join(canonical.(value), ",") * "]"
    keys_sorted = sort(collect(keys(value)); by=k -> Tuple(transcode(UInt16, k)))
    "{" * join([json_string(k) * ":" * canonical(value[k]) for k in keys_sorted], ",") * "}"
end
digest(doc) = bytes2hex(sha256(canonical(doc["content"])))
const ROOT = normpath(joinpath(@__DIR__, "../.."))
const SCHEMA = JSONSchema.Schema(JSON.parsefile(joinpath(ROOT, "spec/bioir/proposals/bioir-m0.schema.json")))
function structure(doc)
    JSONSchema.validate(SCHEMA, doc) === nothing || reject("SCHEMA")
end
function unique_items(items, key, path)
    out = Dict{String,Any}()
    for (i, item) in enumerate(items)
        haskey(out, item[key]) && reject("DUPLICATE_ID", pointer(pointer(path, i-1), key))
        out[item[key]] = item
    end
    out
end
function validate_design(doc)
    structure(doc)
    c = doc["content"]
    c["kind"] == "Design" || reject("SCHEMA")
    compartments = unique_items(c["compartments"], "id", "/content/compartments")
    species = unique_items(c["species"], "id", "/content/species")
    parameters = unique_items(c["parameters"], "id", "/content/parameters")
    unique_items(c["functions"], "id", "/content/functions")
    for (i, item) in enumerate(c["species"])
        haskey(compartments, item["compartment"]) || reject("REFERENCE", "/content/species/$(i-1)/compartment")
        unique_items(item["ports"], "id", "/content/species/$(i-1)/ports")
    end
    kinds, used = Set{String}(), Set{String}()
    for (i, fn) in enumerate(c["functions"])
        path = "/content/functions/$(i-1)"; target = fn["target"]
        haskey(species, target["species"]) || reject("REFERENCE", path * "/target/species")
        target["port"] in [p["id"] for p in species[target["species"]]["ports"]] || reject("REFERENCE", path * "/target/port")
        haskey(parameters, fn["parameter"]) || reject("REFERENCE", path * "/parameter")
        expected = fn["kind"] == "constitutive_production" ? "molecule/s" : "1/s"
        parameters[fn["parameter"]]["unit"] == expected || reject("UNIT", path * "/parameter")
        (fn["kind"] in kinds || fn["parameter"] in used) && reject("FUNCTION_ROLE", path)
        push!(kinds, fn["kind"]); push!(used, fn["parameter"])
    end
    used == Set(keys(parameters)) || reject("REFERENCE", "/content/parameters")
    digest(doc) == doc["digest"] || reject("DIGEST", "/digest")
    doc
end
function validate_experiment(doc, design)
    structure(doc); validate_design(design)
    c, d = doc["content"], design["content"]
    c["kind"] == "Experiment" || reject("SCHEMA")
    for key in ("id", "revision", "digest")
        expected = key == "digest" ? design["digest"] : d[key]
        c["design"][key] == expected || reject("DESIGN_REFERENCE", "/content/design/" * key)
    end
    assignments = unique_items(c["parameters"], "parameter", "/content/parameters")
    initial = unique_items(c["initial_counts"], "species", "/content/initial_counts")
    unique_items(c["observables"], "id", "/content/observables")
    parameters = Dict(p["id"] => p for p in d["parameters"])
    for (i, item) in enumerate(c["parameters"])
        path = "/content/parameters/$(i-1)"
        haskey(parameters, item["parameter"]) || reject("REFERENCE", path * "/parameter")
        item["quantity"]["unit"] == parameters[item["parameter"]]["unit"] || reject("UNIT", path * "/quantity/unit")
    end
    Set(keys(assignments)) == Set(keys(parameters)) || reject("REFERENCE", "/content/parameters")
    species = Dict(s["id"] => s for s in d["species"])
    Set(keys(initial)) == Set(keys(species)) || reject("REFERENCE", "/content/initial_counts")
    for (i, item) in enumerate(c["observables"])
        target = item["target"]; path = "/content/observables/$(i-1)/target"
        haskey(species, target["species"]) || reject("REFERENCE", path * "/species")
        target["port"] in [p["id"] for p in species[target["species"]]["ports"]] || reject("REFERENCE", path * "/port")
    end
    digest(doc) == doc["digest"] || reject("DIGEST", "/digest")
    doc
end
function validate_revision(doc, previous)
    validate_design(doc); validate_design(previous)
    current, old = doc["content"], previous["content"]
    current["id"] == old["id"] || reject("REFERENCE", "/content/id")
    if doc["digest"] != previous["digest"] && current["revision"] <= old["revision"]
        reject("IMMUTABLE_REVISION", "/content/revision")
    end
    doc
end
function evaluate(case, directory)
    doc = strict_parse(read(joinpath(directory, case["input"])))
    op = case["operation"]
    if op == "design"
        validate_design(doc)
    elseif op == "experiment"
        validate_experiment(doc, strict_parse(read(joinpath(directory, case["design"]))))
    elseif op == "revision"
        validate_revision(doc, strict_parse(read(joinpath(directory, case["previous"]))))
    elseif !(op in ("parse", "canonical"))
        error("Unknown catalog operation: $op")
    end
    doc
end
end
