# Native P01 wire parsing and direct RFC 8785/JCS serialization. This file is
# included inside BioIR; it does not load schemas, fixtures or reference tools.
export parse_json, canonical_bytes

_json_error(category, path, message) = throw(BioIRValidationError(category, path, message))
_json_pointer(path, key) = path * "/" * replace(string(key), "~" => "~0", "/" => "~1")
mutable struct _JSONCursor
    bytes::Vector{UInt8}
    index::Int
end
_json_peek(c) = c.index <= length(c.bytes) ? c.bytes[c.index] : 0x00
function _json_space!(c)
    while _json_peek(c) in (0x20, 0x09, 0x0a, 0x0d)
        c.index += 1
    end
end
_json_syntax() = _json_error("JSON_SYNTAX", "", "invalid JSON grammar")
function _json_take!(c, expected)
    _json_peek(c) == expected || _json_syntax()
    c.index += 1
end
function _json_hex4!(c)
    value = UInt32(0)
    for _ in 1:4
        b = _json_peek(c)
        digit = if 0x30 <= b <= 0x39
            b - 0x30
        elseif 0x41 <= b <= 0x46
            b - 0x41 + 10
        elseif 0x61 <= b <= 0x66
            b - 0x61 + 10
        else
            _json_syntax()
        end
        value = (value << 4) | UInt32(digit)
        c.index += 1
    end
    value
end
function _json_string!(c, path)
    _json_take!(c, 0x22)
    io = IOBuffer()
    while c.index <= length(c.bytes)
        b = _json_peek(c)
        c.index += 1
        if b == 0x22
            return String(take!(io))
        elseif b == 0x5c
            escape = _json_peek(c)
            c.index += 1
            if escape == 0x75
                unit = _json_hex4!(c)
                if 0xd800 <= unit <= 0xdbff
                    if _json_peek(c) != 0x5c || c.index + 1 > length(c.bytes) || c.bytes[c.index + 1] != 0x75
                        _json_error("INVALID_UNICODE", path, "unpaired high surrogate")
                    end
                    c.index += 2
                    low = _json_hex4!(c)
                    0xdc00 <= low <= 0xdfff || _json_error("INVALID_UNICODE", path, "invalid surrogate pair")
                    unit = 0x10000 + ((unit - 0xd800) << 10) + low - 0xdc00
                elseif 0xdc00 <= unit <= 0xdfff
                    _json_error("INVALID_UNICODE", path, "unpaired low surrogate")
                end
                write(io, Char(unit))
            elseif escape in (0x22, 0x5c, 0x2f)
                write(io, escape)
            elseif escape == 0x62
                write(io, 0x08)
            elseif escape == 0x66
                write(io, 0x0c)
            elseif escape == 0x6e
                write(io, 0x0a)
            elseif escape == 0x72
                write(io, 0x0d)
            elseif escape == 0x74
                write(io, 0x09)
            else
                _json_syntax()
            end
        elseif b < 0x20
            _json_syntax()
        else
            write(io, b)
        end
    end
    _json_syntax()
end
function _json_number!(c, path)
    start = c.index
    while _json_peek(c) in codeunits("0123456789.eE+-")
        c.index += 1
    end
    raw = String(c.bytes[start:c.index-1])
    occursin(r"\A-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?\z", raw) || _json_syntax()
    if !occursin(r"[.eE]", raw)
        digits = startswith(raw, "-") ? raw[2:end] : raw
        if length(digits) > 16 || (length(digits) == 16 && digits > "9007199254740991")
            _json_error("INTEGER_RANGE", path, "integer token exceeds P01 exact range")
        end
        return parse(Int64, raw)
    end
    value = tryparse(Float64, raw)
    mantissa, exponent = let pieces = split(lowercase(raw), 'e')
        (pieces[1], length(pieces) == 2 ? parse(BigInt, pieces[2]) : big(0))
    end
    nonzero = any(ch -> ch in '1':'9', mantissa)
    if value === nothing
        # Julia reports ERANGE for both overflow and underflow. Determine the
        # decimal order from the original token without lossy numeric conversion.
        if !nonzero
            return startswith(raw, "-") ? -0.0 : 0.0
        end
        unsigned = replace(mantissa, "-" => "")
        digits = replace(unsigned, "." => "")
        first = findfirst(!=('0'), digits)
        point = findfirst(==('.'), unsigned)
        whole = point === nothing ? length(unsigned) : point - 1
        order = whole - first + exponent
        category = order < 0 ? "NUMBER_UNDERFLOW" : "NUMBER_RANGE"
        _json_error(category, path, "floating token is outside finite nonzero binary64")
    end
    isfinite(value) || _json_error("NUMBER_RANGE", path, "floating token overflows binary64")
    value == 0 && nonzero && _json_error("NUMBER_UNDERFLOW", path, "nonzero floating token rounds to zero")
    value
end
function _json_value!(c, path)
    _json_space!(c)
    b = _json_peek(c)
    if b == 0x22
        return _json_string!(c, path)
    elseif b == 0x7b
        c.index += 1
        _json_space!(c)
        value = Dict{String,Any}()
        if _json_peek(c) != 0x7d
            while true
                key = _json_string!(c, path)
                child = _json_pointer(path, key)
                haskey(value, key) && _json_error("DUPLICATE_KEY", child, "duplicate decoded object key")
                _json_space!(c)
                _json_take!(c, 0x3a)
                value[key] = _json_value!(c, child)
                _json_space!(c)
                _json_peek(c) != 0x2c && break
                c.index += 1
                _json_space!(c)
            end
        end
        _json_take!(c, 0x7d)
        return value
    elseif b == 0x5b
        c.index += 1
        _json_space!(c)
        value = Any[]
        if _json_peek(c) != 0x5d
            while true
                push!(value, _json_value!(c, _json_pointer(path, length(value))))
                _json_space!(c)
                _json_peek(c) != 0x2c && break
                c.index += 1
            end
        end
        _json_take!(c, 0x5d)
        return value
    elseif b == 0x2d || b in 0x30:0x39
        return _json_number!(c, path)
    end
    for (literal, value) in (("true", true), ("false", false), ("null", nothing))
        stop = c.index + ncodeunits(literal) - 1
        if stop <= length(c.bytes) && c.bytes[c.index:stop] == codeunits(literal)
            c.index = stop + 1
            return value
        end
    end
    _json_syntax()
end
"""Parse original strict UTF-8 JSON under P01 token and Unicode rules.

Object keys and number tokens are checked before dictionary insertion or numeric
rounding. Returned objects are ordinary fresh Julia JSON trees, not documents.
"""
function parse_json(raw::Union{String,Vector{UInt8}})
    bytes = raw isa String ? Vector{UInt8}(codeunits(raw)) : copy(raw)
    isvalid(String(copy(bytes))) || _json_error("INVALID_UNICODE", "", "input is not strict UTF-8")
    cursor = _JSONCursor(bytes, 1)
    value = _json_value!(cursor, "")
    _json_space!(cursor)
    cursor.index == length(bytes) + 1 || _json_syntax()
    value
end

function _jcs_string(io, value::String, path)
    isvalid(value) || _json_error("INVALID_UNICODE", path, "string is not valid Unicode")
    write(io, '"')
    for ch in value
        if ch == '"'
            write(io, "\\\"")
        elseif ch == '\\'
            write(io, "\\\\")
        elseif ch == '\b'
            write(io, "\\b")
        elseif ch == '\t'
            write(io, "\\t")
        elseif ch == '\n'
            write(io, "\\n")
        elseif ch == '\f'
            write(io, "\\f")
        elseif ch == '\r'
            write(io, "\\r")
        elseif UInt32(ch) < 0x20
            write(io, "\\u", string(UInt32(ch); base=16, pad=4))
        else
            write(io, ch)
        end
    end
    write(io, '"')
end
function _jcs_number(value::Float64, path)
    isfinite(value) || _json_error("NUMBER_RANGE", path, "JCS requires finite binary64")
    value == 0 && return "0"
    # Julia's shortest-roundtrip Ryu significand is rendered using the decimal
    # placement and exponent thresholds required by ECMAScript/RFC 8785.
    pieces = split(lowercase(string(abs(value))), 'e')
    exponent = length(pieces) == 2 ? parse(Int, pieces[2]) : 0
    whole_fraction = split(pieces[1], '.')
    digits = join(whole_fraction)
    skipped = length(digits) - length(lstrip(digits, '0'))
    decimal_position = length(whole_fraction[1]) + exponent - skipped
    digits = rstrip(lstrip(digits, '0'), '0')
    count = length(digits)
    text = if 0 < decimal_position <= 21
        decimal_position >= count ? digits * repeat("0", decimal_position-count) : digits[1:decimal_position] * "." * digits[decimal_position+1:end]
    elseif -6 < decimal_position <= 0
        "0." * repeat("0", -decimal_position) * digits
    else
        digits[1:1] * (count > 1 ? "." * digits[2:end] : "") * "e" * (decimal_position > 0 ? "+" : "") * string(decimal_position-1)
    end
    (signbit(value) ? "-" : "") * text
end
function _jcs_write(io, value, path)
    if value === nothing
        write(io, "null")
    elseif value isa Bool
        write(io, value ? "true" : "false")
    elseif value isa String
        _jcs_string(io, value, path)
    elseif value isa FIXED_INTEGERS
        -MAX_INTEGER <= value <= MAX_INTEGER || _json_error("INTEGER_RANGE", path, "native integer exceeds P01 exact range")
        write(io, string(value))
    elseif value isa Float64
        write(io, _jcs_number(value, path))
    elseif value isa AbstractVector || value isa Tuple
        write(io, '[')
        for (i, item) in enumerate(value)
            i == 1 || write(io, ',')
            _jcs_write(io, item, _json_pointer(path, i-1))
        end
        write(io, ']')
    elseif value isa AbstractDict
        keys = collect(Base.keys(value))
        all(key -> key isa String, keys) || _json_error("SCHEMA", path, "JCS object keys must be strings")
        for key in keys
            isvalid(key) || _json_error("INVALID_UNICODE", path, "object key is not valid Unicode")
        end
        sort!(keys; by=key -> Tuple(transcode(UInt16, key)))
        write(io, '{')
        for (i, key) in enumerate(keys)
            i == 1 || write(io, ',')
            child = _json_pointer(path, key)
            _jcs_string(io, key, child)
            write(io, ':')
            _jcs_write(io, value[key], child)
        end
        write(io, '}')
    else
        _json_error("SCHEMA", path, "unsupported native JSON value")
    end
end
"""Return fresh direct RFC 8785 content bytes, with no FIR normalization.

Canonical bytes can spell a binary64 value as an integer outside P01's raw-token
range. They are identity bytes, not a transport format for strict P01 readback.
"""
function canonical_bytes(value)
    io = IOBuffer()
    _jcs_write(io, value, "")
    take!(io)
end
