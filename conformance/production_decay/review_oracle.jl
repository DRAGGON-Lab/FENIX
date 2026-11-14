"""Independent read-only BigFloat analytical reference; no FENIX/Python dependency."""
module ProductionDecayOracle
using JSON, JSONSchema, SHA
export load_catalog, decode, evaluate, decimal_string, make_report

const ROOT = @__DIR__
const CATALOG = joinpath(ROOT, "catalog.json")
const SCHEMA = JSONSchema.Schema(JSON.parsefile(joinpath(ROOT, "catalog.schema.json")))

function decode(bits)
    bits isa AbstractString && occursin(r"^[0-9a-f]{16}\z", bits) ||
        throw(ArgumentError("invalid binary64 encoding: $bits"))
    value = reinterpret(Float64, parse(UInt64, bits; base=16))
    isfinite(value) && value >= 0 || throw(ArgumentError("expected finite nonnegative binary64: $bits"))
    value
end

function load_catalog(path=CATALOG)
    catalog = JSON.parsefile(path)
    JSONSchema.validate(SCHEMA, catalog) === nothing || throw(ArgumentError("invalid candidate catalog schema/units/status"))
    ids = Set{String}()
    for case in catalog["cases"]
        case["id"] in ids && throw(ArgumentError("duplicate case ID"))
        push!(ids, case["id"])
        foreach(decode, values(case["parameters"]))
        times = Set{Float64}()
        for sample in case["samples"]
            t = decode(sample["time_bits"])
            # Set uses isequal, which distinguishes signed zeros; sample times do not.
            iszero(t) && (t = 0.0)
            t in times && throw(ArgumentError("duplicate sample time"))
            push!(times, t)
            occursin(r"^(0|[1-9]\.[0-9]{49}E[+-][0-9]{1,4})\z", sample["expected"]) ||
                throw(ArgumentError("expected 50-digit scientific decimal or explicit zero"))
        end
    end
    catalog
end

function evaluate(alpha::Float64, beta::Float64, x0::Float64, time::Float64, bits::Int)
    all(v -> isfinite(v) && v >= 0, (alpha, beta, x0, time)) ||
        throw(ArgumentError("evaluation requires finite nonnegative inputs"))
    setprecision(BigFloat, bits) do
        setrounding(BigFloat, RoundNearest) do
            a, b, x, t = BigFloat.((alpha, beta, x0, time))
            iszero(b) && return x + a * t
            z = -b * t
            x * exp(z) + a * (-expm1(z)) / b
        end
    end
end

"""Half-even decimal rounding using the exact rational represented by a BigFloat."""
function decimal_string(value::BigFloat, digits::Int)
    isfinite(value) && value >= 0 || throw(ArgumentError("invalid reference result"))
    iszero(value) && return "0"
    rational = Rational{BigInt}(value)
    n, d = numerator(rational), denominator(rational)
    k = ndigits(n) - ndigits(d)
    # Correct the base-ten exponent estimate without floating-point logarithms.
    if k >= 0 ? n < d * big(10)^k : n * big(10)^(-k) < d
        k -= 1
    end
    scale = digits - 1 - k
    if scale >= 0
        n *= big(10)^scale
    else
        d *= big(10)^(-scale)
    end
    q, r = divrem(n, d)
    if 2r > d || (2r == d && isodd(q))
        q += 1
    end
    if q == big(10)^digits
        q = div(q, 10)
        k += 1
    end
    coefficient = string(q)
    mantissa = digits == 1 ? coefficient : coefficient[1:1] * "." * coefficient[2:end]
    mantissa * "E" * (k >= 0 ? "+" : "") * string(k)
end

function make_report(catalog_path=CATALOG)
    catalog = load_catalog(catalog_path)
    rows = Any[]
    stability = Dict{Tuple{String,String},String}()
    for precision in (512, 1024), case in catalog["cases"]
        a, b, x = [decode(case["parameters"][k]) for k in ("alpha", "beta", "x0")]
        for sample in case["samples"]
            value = evaluate(a, b, x, decode(sample["time_bits"]), precision)
            decimal_string(value, 50) == sample["expected"] ||
                throw(ArgumentError("$(case["id"])/$(sample["time_bits"]): fixed expectation mismatch at $precision bits"))
            key = (case["id"], sample["time_bits"])
            rounded = decimal_string(value, 70)
            get(stability, key, rounded) == rounded || throw(ArgumentError("precision runs disagree at 70 digits"))
            stability[key] = rounded
            push!(rows, Dict("case_id" => case["id"], "time_bits" => sample["time_bits"],
                             "precision" => precision, "value" => iszero(value) ? "0" : string(value)))
        end
    end
    Dict("format" => "production-decay-report-v1", "implementation" => "julia-bigfloat",
         "runtime" => Dict("julia" => string(VERSION), "mpfr" => string(Base.MPFR.version())),
         "catalog_sha256" => bytes2hex(sha256(read(catalog_path))),
         "evaluator_sha256" => bytes2hex(sha256(read(@__FILE__))),
         "precision_unit" => "bits", "rows" => rows)
end

function main(args)
    length(args) == 2 && args[1] == "--report" || throw(ArgumentError("Usage: review_oracle.jl --report PATH"))
    destination = abspath(args[2])
    # Resolve existing symlinks as well; only report files may be written.
    ispath(args[2]) && (destination = realpath(args[2]))
    destination in (CATALOG, joinpath(ROOT, "catalog.schema.json"), @__FILE__, joinpath(ROOT, "review_oracle.py")) &&
        throw(ArgumentError("report destination must not overwrite reference inputs or evaluators"))
    report = make_report()
    mkpath(dirname(args[2]))
    write(args[2], JSON.json(report; pretty=true) * "\n")
    println("PASS: $(length(report["rows"])) computations; candidate expectations remain REVIEW_REQUIRED")
end
end

if abspath(PROGRAM_FILE) == @__FILE__
    try
        ProductionDecayOracle.main(ARGS)
    catch error
        println(stderr, "FAIL: ", sprint(showerror, error))
        exit(1)
    end
end
