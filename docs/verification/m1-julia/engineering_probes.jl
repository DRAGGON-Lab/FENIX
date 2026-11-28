# Read-only focused native Julia M1 engineering probes.
using Fenix, JSON
C = Fenix.Community
p = "spec/community/wire-candidates/threshold-n1"
source = read(joinpath(p,"design.json"))
design = C.from_json(C.Design,source)
source[1] = 0x00
@assert startswith(C.to_json(design),"{")
experiment = C.from_json(C.Experiment,read(joinpath(p,"experiment.json"));design)
raw = read(joinpath(p,"zero.result.json"))
manifest = JSON.parsefile(joinpath(p,"zero.python.manifest.json"))
for stamp in ("2026-02-30T12:00:00.000000Z","2026-11-27T12:00:60.000000Z")
    manifest["timing"]["started_at_utc"] = stamp
    failure = try C.from_json(C.RunRecord,raw,C._emit(manifest);experiment); nothing catch error; error end
    @assert failure isa C.ValidationError && failure.category == "TIMESTAMP"
end
manifest["timing"]["started_at_utc"] = "2026-11-27T12:00:00.000000Z"
C.from_json(C.RunRecord,raw,C._emit(manifest);experiment)
for token in ("1.0","1e0","true")
    text = replace(C._emit(manifest),r"\"max_nfev\":9007199254740993"=>"\"max_nfev\":"*token)
    failure = try C.from_json(C.RunRecord,raw,text;experiment); nothing catch error; error end
    @assert failure isa C.ValidationError && failure.category == "INTEGER_TOKEN"
end
huge = big(10)^5000 + 1
manifest["execution"]["max_nfev"] = huge
text = C._emit(manifest)
record = C.from_json(C.RunRecord,raw,text;experiment)
@assert C.to_dict(record.manifest)["execution"]["max_nfev"] == huge
@assert String(C.manifest_bytes(record)) == text
copied = C.result_bytes(record); copied[1] = 0x00
@assert C.result_bytes(record) == raw
fresh = C.to_dict(design); fresh["content"]["owners"][1]["volume"]["value"] = -1
@assert C.to_dict(design)["content"]["owners"][1]["volume"]["value"] >= 0
println("PASS timestamp/counter rejection, exact large budget and immutable buffers; Julia ",VERSION)
