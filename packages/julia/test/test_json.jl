using Test
using Fenix.BioIR

@testset "Native strict P01 JSON" begin
    @test parse_json("null") === nothing
    @test parse_json("false") === false
    @test parse_json("[12, true, null]") == Any[12, true, nothing]
    @test parse_json("\"\\ud83d\\ude00\"") == "😀"
    @test parse_json("\"\\u0061\\/\\b\\f\\n\\r\\t\\\\\\\"\"") == "a/\b\f\n\r\t\\\""
    @test parse_json("9007199254740991") === Int64(9007199254740991)
    @test parse_json("9007199254740992e0") === Float64(9007199254740992)
    @test reinterpret(UInt64, parse_json("5e-324")) == 0x0000000000000001
    @test reinterpret(UInt64, parse_json("-0.0")) == 0x8000000000000000
    @test parse_json("0e-99999999999999999999") == 0.0
    @test parse_json("1.7976931348623157e308") == floatmax(Float64)
    for (raw, category, path) in (
        ("{\"x\":1,\"\\u0078\":2}", "DUPLICATE_KEY", "/x"),
        ("{\"a/b~\":[0,9007199254740992]}", "INTEGER_RANGE", "/a~1b~0/1"),
        ("{\"a\":[\"\\ud800\"]}", "INVALID_UNICODE", "/a/0"),
        ("\"\\udc00\"", "INVALID_UNICODE", ""),
        ("1e400", "NUMBER_RANGE", ""),
        ("1e-400", "NUMBER_UNDERFLOW", ""),
        ("2e-324", "NUMBER_UNDERFLOW", ""),
        ("-9007199254740992", "INTEGER_RANGE", ""),
        ("[NaN]", "JSON_SYNTAX", ""),
        ("[1,]", "JSON_SYNTAX", ""),
        ("{\"a\":0,}", "JSON_SYNTAX", ""),
        ("01", "JSON_SYNTAX", ""),
        ("1.", "JSON_SYNTAX", ""),
        ("\"\\x\"", "JSON_SYNTAX", ""),
        ("\"abc", "JSON_SYNTAX", ""),
        ("true false", "JSON_SYNTAX", ""))
        caught = try parse_json(raw); nothing catch error; error end
        @test caught isa BioIRValidationError
        @test caught.category == category
        @test caught.path == path
    end
    @test_throws BioIRValidationError parse_json(UInt8[0xff])
    @test_throws BioIRValidationError parse_json(UInt8[0xed, 0xa0, 0x80])
    bytes = collect(codeunits("{\"x\":1}"))
    @test parse_json(bytes) == Dict("x" => 1)
    @test String(bytes) == "{\"x\":1}"
end

@testset "Explicit P03 numeric input policy" begin
    @test parse_json("12"; numeric_policy=:p03) === 12.0
    @test parse_json("-0"; numeric_policy=:p03) === -0.0
    tree = parse_json("{\"n\":[1,true,null]}"; numeric_policy=:p03)
    @test tree["n"][1] === 1.0
    @test tree["n"][2] === true
    @test tree["n"][3] === nothing
    @test parse_json("9007199254740993"; numeric_policy=:p03) === 9007199254740992.0
    @test parse_json("1000000000000000128"; numeric_policy=:p03) === 1000000000000000128.0
    @test String(canonical_bytes(parse_json("1000000000000000128"; numeric_policy=:p03))) == "1000000000000000100"
    @test reinterpret(UInt64, parse_json("5e-324"; numeric_policy=:p03)) == 0x0000000000000001
    @test parse_json("0e999999999999999999999999"; numeric_policy=:p03) === 0.0
    @test parse_json("-0e-999999999999999999999999"; numeric_policy=:p03) === -0.0
    @test parse_json("1.7976931348623157e308"; numeric_policy=:p03) === floatmax(Float64)
    for (raw, category, path) in (
        ("{\"n\":[1e400]}", "NUMBER_RANGE", "/n/0"),
        ("1e-400", "NUMBER_UNDERFLOW", ""),
        ("2e-324", "NUMBER_UNDERFLOW", ""),
        (repeat("9", 400), "NUMBER_RANGE", ""),
        ("{\"x\":1,\"\\u0078\":2}", "DUPLICATE_KEY", "/x"),
        ("NaN", "JSON_SYNTAX", ""))
        caught = try parse_json(raw; numeric_policy=:p03); nothing catch error; error end
        @test caught isa BioIRValidationError
        @test caught.category == category
        @test caught.path == path
    end
    @test_throws ArgumentError parse_json("1"; numeric_policy=:unknown)
    @test parse_json("1") === Int64(1)
    @test_throws BioIRValidationError parse_json("9007199254740993")
end

@testset "Direct RFC 8785 bytes" begin
    @test String(canonical_bytes(parse_json("{\"z\":-0.0,\"a\":1.0}"))) == "{\"a\":1,\"z\":0}"
    @test String(canonical_bytes(Dict("\ue000" => 1, "😀" => 2))) == "{\"😀\":2,\"\ue000\":1}"
    @test String(canonical_bytes("\x00\b\t\n\f\r\"\\/")) == "\"\\u0000\\b\\t\\n\\f\\r\\\"\\\\/\""
    @test String(canonical_bytes([1e-7, 1e-6, 1e20, 1e21, 9007199254740992.0])) == "[1e-7,0.000001,100000000000000000000,1e+21,9007199254740992]"
    @test String(canonical_bytes(nextfloat(0.0))) == "5e-324"
    @test String(canonical_bytes(floatmax(Float64))) == "1.7976931348623157e+308"
    for value in (NaN, Inf, -Inf, BigInt(1), Float32(1), UInt64(9007199254740992), String(UInt8[0xff]))
        @test_throws BioIRValidationError canonical_bytes(value)
    end
    bytes = canonical_bytes(Dict("a"=>1)); bytes[1] = 0x00
    @test String(canonical_bytes(Dict("a"=>1))) == "{\"a\":1}"
end

@testset "Private token-preserving JSON leaves public policies unchanged" begin
    decode = Fenix.BioIR._parse_json_tokens
    token_type = Fenix.BioIR._JSONNumberToken
    lexemes = ("-0", "-0.0", "5e-324", "1e400", "1e-400",
               "9007199254740993", "1000000000000000000000000000001",
               "1.0", "1e0", "-0e99999999999999999999999")
    tree = decode("[" * join(lexemes, ",") * ",true,false,null,\"1\"]")
    @test all(item isa token_type for item in tree[1:length(lexemes)])
    @test Tuple(item.raw for item in tree[1:length(lexemes)]) == lexemes
    @test tree[end-3:end] == Any[true, false, nothing, "1"]
    @test isimmutable(tree[1])
    bytes = collect(codeunits("{\"n\":9007199254740993}"))
    parsed = decode(bytes)
    bytes[6] = UInt8('0')
    @test parsed["n"].raw == "9007199254740993"
    @test decode("\"\\ud83d\\ude00\"") == "😀"
    for policy in (:tokens, :unknown)
        @test_throws ArgumentError parse_json("1"; numeric_policy=policy)
    end
    @test parse_json("12") === Int64(12)
    @test parse_json("12"; numeric_policy=:p03) === 12.0
    @test_throws BioIRValidationError parse_json("9007199254740993")
    @test_throws BioIRValidationError parse_json("1e400"; numeric_policy=:p03)
    for (raw, category, path) in (
        ("{\"a/b~\":1,\"a\\/b~\":2}", "DUPLICATE_KEY", "/a~1b~0"),
        ("{\"n\":\"\\ud800\"}", "INVALID_UNICODE", "/n"),
        ("{\"n\":\"\\udc00\"}", "INVALID_UNICODE", "/n"),
        ("[1,]", "JSON_SYNTAX", ""),
        ("{\"x\":1,}", "JSON_SYNTAX", ""),
        ("01", "JSON_SYNTAX", ""),
        ("1e", "JSON_SYNTAX", ""),
        ("--1", "JSON_SYNTAX", ""),
        ("+1", "JSON_SYNTAX", ""),
        ("1.", "JSON_SYNTAX", ""),
        ("NaN", "JSON_SYNTAX", ""),
        ("Infinity", "JSON_SYNTAX", ""),
        ("/*x*/1", "JSON_SYNTAX", ""),
        ("1 true", "JSON_SYNTAX", ""))
        caught = try decode(raw); nothing catch error; error end
        @test caught isa BioIRValidationError
        @test caught.category == category
        @test caught.path == path
    end
    for raw in (UInt8[0xff], UInt8[0xed,0xa0,0x80], UInt8[0xef,0xbb,0xbf,0x31])
        @test_throws BioIRValidationError decode(raw)
    end
end

@testset "Private direct binary64 decoding preserves represented bits" begin
    decode = Fenix.BioIR._json_binary64
    for (token, word) in (
        ("-0", 0x8000000000000000),
        ("-0.0", 0x8000000000000000),
        ("0e99999999999999999999999", 0x0000000000000000),
        ("-0e-99999999999999999999999", 0x8000000000000000),
        ("5e-324", 0x0000000000000001),
        ("2.225073858507201e-308", 0x000fffffffffffff),
        ("2.2250738585072014e-308", 0x0010000000000000),
        ("1.7976931348623157e308", 0x7fefffffffffffff),
        ("9007199254740993", 0x4340000000000000),
        ("1.00000000000000011102230246251565404236316680908203125", 0x3ff0000000000000),
        ("1.00000000000000011102230246251565404236316680908203126", 0x3ff0000000000001))
        @test reinterpret(UInt64, decode(token, "/sample")) == word
    end
    for (token, category) in (("1e400", "NUMBER_RANGE"),
                               ("1e-400", "NUMBER_UNDERFLOW"),
                               ("2e-324", "NUMBER_UNDERFLOW"))
        caught = try decode(token, "/sample"); nothing catch error; error end
        @test caught isa BioIRValidationError
        @test caught.category == category
        @test caught.path == "/sample"
    end
end
