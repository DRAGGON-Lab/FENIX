# Produce native Julia artifacts or verify Python artifacts through Julia readback.
using Fenix, JSON, SHA
const C = Fenix.Community

function main(args)
    mode,root,exchange,revision = args
    mode in ("produce","read") || error("Expected produce or read")
    inputs = joinpath(root,"spec/community/wire-candidates")
    catalog = JSON.parsefile(joinpath(root,"conformance/community/cases.json"))
    settings = JSON.parsefile(joinpath(root,"conformance/community/feasibility/settings.json"))
    methods = mode == "produce" ? ("Tsit5","Rodas5P") : ("DOP853","Radau")
    rows = []
    for case in catalog["cases"]
        folder = joinpath(inputs,case["id"])
        design = C.from_json(C.Design,read(joinpath(folder,"design.json")))
        experiment = C.from_json(C.Experiment,read(joinpath(folder,"experiment.json"));design)
        fir = C.compile_experiment(experiment)
        for method in methods, setting in settings["settings"]
            key = joinpath(case["id"],method,setting["id"])
            output = joinpath(exchange,key)
            if mode == "produce"
                mkpath(dirname(output))
                mkdir(output)
                spec = C.ODEExecutionSpec(;time_grid=Tuple(Float64.(case["times"])),method,
                    rtol=setting["rtol"],atol=setting["atol"],max_step=settings["reference_max_step"],
                    max_nfev=settings["max_rhs_calls"])
                record = C.run_experiment(experiment,spec)
                for (name,data) in (("model.jcs",C.model_bytes(fir)),("identity.jcs",C.identity_bytes(fir)),
                                    ("result.json",C.result_bytes(record)),("manifest.json",C.manifest_bytes(record)))
                    write(joinpath(output,name),data)
                end
            else
                raw,manifest = read(joinpath(output,"result.json")),read(joinpath(output,"manifest.json"))
                record = C.from_json(C.RunRecord,raw,manifest;experiment)
                @assert C.result_bytes(record)==raw && C.manifest_bytes(record)==manifest
                @assert C.model_bytes(fir)==read(joinpath(output,"model.jcs"))
                @assert C.identity_bytes(fir)==read(joinpath(output,"identity.jcs"))
            end
            push!(rows,Dict("key"=>key,"result_sha256"=>bytes2hex(sha256(C.result_bytes(record))),
                            "manifest_sha256"=>bytes2hex(sha256(C.manifest_bytes(record))),"fir_digest"=>C.digest(fir)))
        end
    end
    report = Dict("runtime"=>"julia","mode"=>mode,"source_revision"=>revision,"rows"=>rows)
    open(io -> JSON.print(io,report,2),joinpath(exchange,"julia-$mode.json"),"w")
    println("PASS native Julia $mode: ",length(rows)," records")
end
main(ARGS)
