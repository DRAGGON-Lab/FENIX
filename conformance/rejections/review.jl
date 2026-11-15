# Native evidence writer; no subprocesses or cross-language dependencies.
module RejectionReview
include("reference.jl")
using .RejectionReference, JSON, SHA, TOML
const R = RejectionReference
const ROOT = R.ROOT
const IMPLEMENTATION = "independent-julia-rejection-reference"
const EVALUATORS = ["conformance/rejections/reference.jl", "conformance/rejections/review.jl", "conformance/julia/p01.jl"]
const CONTRACTS = ["spec/bioir/proposals/ADR-P01.md", "spec/fir/proposals/ADR-P02.md", "spec/canonicalization/proposals/ADR-P03.md"]
const SCHEMAS = ["spec/bioir/proposals/bioir-m0.schema.json", "spec/fir/proposals/fir-m0.schema.json"]
const DEPENDENCIES = ["packages/python/pyproject.toml", "packages/python/uv.lock", "conformance/julia/Project.toml", "conformance/julia/Manifest.toml"]
const HISTORICAL = ["conformance/bioir/catalog.json", "conformance/canonicalization/catalog.json"]
fingerprints(paths) = Dict(path => R.sha(read(joinpath(ROOT, path))) for path in paths)
function provenance()
    Dict("report_version" => 1, "implementation" => IMPLEMENTATION,
         "catalog_sha256" => R.sha(read(joinpath(@__DIR__, "catalog.json"))),
         "catalog_schema_sha256" => R.sha(read(joinpath(@__DIR__, "catalog.schema.json"))),
         "fixture_status" => JSON.parsefile(joinpath(@__DIR__, "catalog.json"))["status"], "catalog_version" => "1.0.0",
         "evaluator_fingerprints" => fingerprints(EVALUATORS),
         "schema_fingerprints" => fingerprints(SCHEMAS), "contract_fingerprints" => fingerprints(CONTRACTS),
         "dependency_fingerprints" => fingerprints(DEPENDENCIES), "historical_catalog_fingerprints" => fingerprints(HISTORICAL))
end
function run_catalog()
    catalog = R.load_catalog()
    rows = Any[]
    for case in catalog["cases"]
        observed = R.observe(case)
        push!(rows, Dict("id" => case["id"], "observed" => observed, "passed" => observed == case["expected"]))
    end
    report = provenance()
    report["runtime"] = Dict("name" => "julia", "version" => string(VERSION),
                             "dependencies" => Dict("JSON" => string(pkgversion(JSON)), "JSONSchema" => string(pkgversion(R.JSONSchema))))
    report["passed"] = all(row["passed"] for row in rows)
    report["cases"] = rows
    report
end
function resolve_output(path)
    absolute = abspath(path)
    ispath(absolute) && return realpath(absolute)
    islink(absolute) && error("Dangling report symlink")
    parent = dirname(absolute)
    parent == absolute && error("Invalid output path")
    joinpath(resolve_output(parent), basename(absolute))
end
function check_output(path)
    target = resolve_output(path)
    if (target == ROOT || startswith(target, ROOT * "/")) && !startswith(target, joinpath(ROOT, "artifacts") * "/")
        error("Report would overwrite repository source")
    end
    if ispath(target)
        identity = (stat(target).device, stat(target).inode)
        protected = Set{String}()
        ignored = Set([".git", ".venv", "venv", "__pycache__", "artifacts", "dist", "build", ".julia", "node_modules"])
        for (dir, dirs, files) in walkdir(ROOT)
            filter!(d -> !(d in ignored), dirs)
            for file in files
                push!(protected, relpath(joinpath(dir, file), ROOT))
            end
        end
        for relative in protected
            st = stat(joinpath(ROOT, relative))
            identity == (st.device, st.inode) && error("Report aliases protected source, schema or fixture")
        end
    end
    target
end
function main(args)
    (isempty(args) || (length(args) == 2 && args[1] == "--report")) || error("Usage: review.jl [--report PATH]")
    target = isempty(args) ? nothing : check_output(args[2])
    report = run_catalog()
    output = JSON.json(report; pretty=true) * "\n"
    if target === nothing
        print(output)
    else
        mkpath(dirname(target)); write(target, output)
    end
    println(stderr, "$(length(report["cases"])) rejection-suite cases; passed=$(report["passed"])")
    report["passed"] ? 0 : 1
end
end
if abspath(PROGRAM_FILE) == @__FILE__
    exit(RejectionReview.main(ARGS))
end
