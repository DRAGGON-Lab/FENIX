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
