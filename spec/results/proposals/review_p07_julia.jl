"""Independent bounded Julia audit of the proposed P07 SciML profile.

Uses only reference-tool packages and the independent P01 reference encoder.
Not a production JSON reader, source compiler or solver; no Fenix imports.
Local schema expansion is allowlisted and never resolves remote resources.
"""
module P07JuliaAudit
using JSON, JSONSchema, SHA
const HERE = @__DIR__
const ROOT = normpath(joinpath(HERE,"../../.."))
const CANDIDATES = joinpath(HERE,"julia-examples")
const ORIGINALS = joinpath(HERE,"examples")
include(joinpath(ROOT,"conformance/julia/p01.jl"))
const NAMES = ("late-first","zero-only","empty-observables","multi-observables")
const INPUTS = Set{String}()
readinput(path) = (push!(INPUTS,normpath(path)); read(path))
load(path) = JSON.parse(String(readinput(path)))
sha(path) = bytes2hex(sha256(readinput(path)))
word(x) = reinterpret(UInt64,Float64(x))
bits(x) = string(word(x);base=16,pad=16)
require(ok,message) = ok || throw(ArgumentError(message))

# Replace references from only these local files, preserving each reference's
# document scope. In particular #/definitions/source belongs to the old schema.
function expand(node,document,documents)
    if node isa AbstractDict
        if haskey(node,"\$ref")
            ref = node["\$ref"]
            parts = split(ref,'#';limit=2)
            filename = isempty(parts[1]) ? document :
                parts[1] == "urn:fenix:proposed:run-manifest:m0:0.1.0" ? "run-manifest-m0.schema.json" : parts[1]
            haskey(documents,filename) || error("nonlocal or unknown schema ref: $ref")
            target = documents[filename]
            if length(parts)==2 && !isempty(parts[2])
                startswith(parts[2],"/") || error("unsupported ref fragment")
                for key in split(parts[2][2:end],'/')
                    target = target[replace(key,"~1"=>"/","~0"=>"~")]
                end
            end
            return expand(target,filename,documents)
        end
        return Dict(k=>expand(v,document,documents) for (k,v) in node if !(k in ("\$id","\$schema")))
    elseif node isa AbstractVector
        return [expand(v,document,documents) for v in node]
    end
    node
end
function schemas()
    names = ("run-manifest-m0.schema.json","run-manifest-julia-sciml-m0.schema.json","ode-result-m0.schema.json")
    docs = Dict(name=>load(joinpath(HERE,name)) for name in names)
    old,new,result = names
    # Core properties are reused, not copied/redefined; no SciPy root floor is inherited.
    for key in keys(docs[old]["properties"])
        key=="backend" && continue
        require(docs[new]["properties"][key]==Dict("\$ref"=>"urn:fenix:proposed:run-manifest:m0:0.1.0#/properties/"*key),"core reference drift")
    end
    Dict(name=>JSONSchema.Schema(expand(docs[name],name,docs)) for name in names)
end
valid(schema,value) = JSONSchema.validate(schema,value) === nothing

# Bounded field converters: full JSON syntax is still an implementation gate.
const NUMBER = r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\z"
const INTEGER = r"^-?(?:0|[1-9][0-9]*)\z"
function exactdecimal(token)
    require(occursin(NUMBER,token),"invalid number token")
    halves = split(lowercase(token),'e';limit=2)
    exponent = length(halves)==2 ? parse(Int,halves[2]) : 0
    mantissa = split(halves[1],'.';limit=2)
    fractional = length(mantissa)==2 ? length(mantissa[2]) : 0
    numerator = parse(BigInt,join(mantissa))
    power = exponent-fractional
    power >= 0 ? (numerator*big(10)^power)//big(1) : numerator//big(10)^(-power)
end
function binary64(token)
    exact = exactdecimal(token)
    value = parse(Float64,token)
    require(isfinite(value) && !(iszero(value) && !iszero(exact)),"binary64 range")
    value
end
function integer(token;positive=false)
    require(occursin(INTEGER,token),"integer-form required")
    value=parse(BigInt,token)
    require(positive ? value>0 : value>=0,"integer range")
    value
end
function rationalword(w::UInt64)
    require(w < 0x7ff0000000000000,"positive finite word required")
    exponent=Int(w>>52)
    fraction=BigInt(w&0x000fffffffffffff)
    exponent!=0 && (fraction+=big(1)<<52)
    power=exponent==0 ? -1074 : exponent-1023-52
    power>=0 ? (fraction<<power)//big(1) : fraction//(big(1)<<(-power))
end
function nearest(token,expected)
    value=binary64(token)
    require(bits(value)==expected,"decoder bit mismatch: $token")
    exact=exactdecimal(token)
    w=parse(UInt64,expected;base=16)
    if iszero(exact)
        require(w==(startswith(token,"-") ? 0x8000000000000000 : 0x0000000000000000),"zero sign")
    else
        require(exact>0 && w>0,"positive rounding probe required")
        center=rationalword(w)
        lower=(rationalword(w-UInt64(1))+center)/2
        following=w==0x7fefffffffffffff ? (big(1)<<1024)//big(1) : rationalword(w+UInt64(1))
        upper=(center+following)/2
        require(lower<=exact<=upper,"outside nearest interval")
        require(!(exact==lower || exact==upper) || iseven(w),"ties must round even")
    end
end
function rejection(f)
    try
        f()
    catch e
        e isa ArgumentError || rethrow()
        return true
    end
    error("expected rejection")
end

function modeldigest(model)
    normalized=deepcopy(model)
    for key in ("states","parameters","reactions","observables")
        sort!(normalized[key];by=x->x["id"])
    end
    sort!(normalized["equations"];by=x->x["state"])
    sort!(normalized["assumptions"])
    bytes2hex(sha256(P01Reference.canonical(Dict("domain"=>"fenix.fir","canonicalization_version"=>"0.1.0","model"=>normalized))))
end
function relations(manifest,result,model)
    grid=manifest["execution"]["time_grid"]
    require(!isempty(grid) && all(t->isfinite(t)&&t>=0,grid),"grid range")
    require(all(diff(grid).>0),"strictly increasing grid")
    require(bits.(grid)==bits.(result["times"]),"grid bits")
    opts=manifest["backend"]["solver"]["options"]
    require(opts["save_start"]==iszero(first(grid)),"save_start relation")
    zero=length(grid)==1 && iszero(only(grid))
    require(manifest["integration"]==(zero ? "skipped_zero_grid" : "performed"),"integration relation")
    nfev=manifest["evaluations"]["nfev"]
    backend=manifest["backend"]["evaluations"]
    require(nfev<=manifest["execution"]["max_nfev"],"work bound")
    require(zero ? nfev==0 && all(iszero,values(backend)) : nfev>0,"integration counters")
    require(result["fir_digest"]==manifest["fir"]["digest"]==modeldigest(model),"FIR correspondence")
    states=sort(model["states"];by=x->x["id"])
    observables=sort(model["observables"];by=x->x["id"])
    require(result["time_unit"]==model["time_unit"],"time units")
    require(result["state_ids"]==[s["id"] for s in states],"state order")
    require(result["state_units"]==[s["unit"] for s in states],"state units")
    for (field,key) in (("observable_ids","id"),("observable_state_ids","state"),("observable_units","unit"))
        require(result[field]==[o[key] for o in observables],"observable interface")
    end
    require(length(result["state_values"])==length(grid)==length(result["observable_values"]),"sample rows")
    for (i,t) in enumerate(grid)
        row,obs=result["state_values"][i],result["observable_values"][i]
        require(length(row)==length(states) && length(obs)==length(observables),"column dimensions")
        require(all(v->isfinite(v)&&v>=0,row) && all(v->isfinite(v)&&v>=0,obs),"sample range")
        for (j,o) in enumerate(observables)
            state=findfirst(s->s["id"]==o["state"],states)
            require(bits(obs[j])==bits(row[state]),"direct observable bits")
        end
        if iszero(t)
            require(row==[s["initial"] for s in states],"initial state")
        end
    end
    true
end
function sourcechecks(manifest,name)
    design=load(joinpath(ROOT,"spec/bioir/proposals/examples/design.json"))
    expath=name=="empty-observables" ? joinpath(ROOT,"spec/fir/proposals/examples/sources/no-observables-experiment.json") :
        name=="multi-observables" ? joinpath(ORIGINALS,"multi-observables.experiment.json") : joinpath(ROOT,"spec/bioir/proposals/examples/experiment.json")
    experiment=load(expath)
    for (key,doc) in (("design",design),("experiment",experiment))
        require(bytes2hex(sha256(P01Reference.canonical(doc["content"])))==doc["digest"],"source content digest")
        c=doc["content"]
        require(manifest["sources"][key]==Dict("schema_version"=>c["schema_version"],"id"=>c["id"],"revision"=>c["revision"],"digest"=>doc["digest"]),"complete source reference")
    end
    expected_design=Dict("id"=>design["content"]["id"],"revision"=>design["content"]["revision"],"digest"=>design["digest"])
    require(experiment["content"]["design"]==expected_design,"source pair")
end
function model(name)
    path=name=="empty-observables" ? joinpath(ROOT,"spec/fir/proposals/examples/production-decay-no-observables.json") :
        name=="multi-observables" ? joinpath(ORIGINALS,"multi-observables.fir.json") : joinpath(ROOT,"spec/fir/proposals/examples/production-decay.json")
    load(path)["model"]
end

function main()
    validators=schemas()
    jl=validators["run-manifest-julia-sciml-m0.schema.json"]
    py=validators["run-manifest-m0.schema.json"]
    rs=validators["ode-result-m0.schema.json"]
    catalog=load(joinpath(CANDIDATES,"checksums.json"))
    require(catalog["status"]=="PROPOSED_SYNTHETIC_NOT_EXECUTION_RECEIPTS","candidate status")
    expected=Set(vcat([name*".manifest.json" for name in NAMES],["../examples/"*name*".result.json" for name in NAMES]))
    require(Set(keys(catalog["artifacts"]))==expected,"complete catalog")
    for (path,digest) in catalog["artifacts"]
        require(sha(joinpath(CANDIDATES,path))==digest,"candidate checksum: $path")
    end
    pairs=Dict{String,Any}()
    for name in NAMES
        mp=joinpath(CANDIDATES,name*".manifest.json")
        rp=joinpath(ORIGINALS,name*".result.json")
        m,r=load(mp),load(rp)
        require(valid(jl,m)&&valid(rs,r),"schema: $name")
        require(!valid(py,m),"old schema must reject Julia")
        require(valid(py,load(joinpath(ORIGINALS,name*".manifest.json"))),"approved Python schema compatibility")
        require(m["output"]["sha256"]==sha(rp),"exact result checksum")
        require(m["producer"]==Dict("name"=>"Fenix","version"=>"0.0.0","build_id"=>nothing),"synthetic producer")
        sourcechecks(m,name)
        relations(m,r,model(name))
        # Inspect lexical form of every fixed integer field in the controlled
        # examples, rather than trusting JSON.parse's default numeric types.
        for match in eachmatch(r"\"(revision|max_nfev|nfev|njev|nw|maxiters)\"\s*:\s*([^\s,}\]]+)",String(readinput(mp)))
            integer(match.captures[2];positive=match.captures[1] in ("revision","max_nfev","maxiters"))
        end
        raw=readinput(rp)
        require(sha256(raw)!=sha256(vcat(raw,UInt8[0x20])),"whitespace affects checksum")
        require(JSON.parse(String(copy(raw)))==JSON.parse(String(vcat(raw,UInt8[0x20]))),"whitespace preserves values")
        pairs[name]=(m,r)
    end
    require([o["id"] for o in model("multi-observables")["observables"]]==["z_amount","a_amount","m_amount"],"reordered source fixture")
    z=pairs["zero-only"][1]
    require(z["execution"]["max_nfev"]>typemax(Int)&&z["backend"]["solver"]["options"]["maxiters"]>typemax(Int),"portable integer beyond Int")
    require(bits(z["execution"]["time_grid"][1])=="8000000000000000","negative-zero grid")
    probes=load(joinpath(ORIGINALS,"numeric-tokens.json"))
    for probe in probes["binary64"]
        nearest(probe["token"],probe["bits"])
    end
    midpointprobes=[("1.00000000000000011102230246251565404236316680908203125","3ff0000000000000"),
                    ("1.00000000000000033306690738754696212708950042724609375","3ff0000000000002")]
    foreach(p->nearest(p...),midpointprobes)
    for n in probes["integers"]
        require(integer(string(n))==n,"exact large integer")
    end
    numeric_rejections=0
    for token in vcat(probes["reject_binary64"],["-1e-400","01","1.",".1"])
        rejection(()->binary64(token)); numeric_rejections+=1
    end
    for token in vcat(probes["reject_integer"],["-1","01","+1"])
        rejection(()->integer(token)); numeric_rejections+=1
    end
    rejection(()->integer("0";positive=true)); numeric_rejections+=1
    base,result=pairs["late-first"]
    structural_rejections=0
    # Required/closed shape at every manifest object, plus fixed options/profile controls.
    function shape_mutations!(root,path=String[])
        node=root
        for k in path; node=node[k]; end
        node isa AbstractDict || return Any[]
        mutations=Any[]
        for key in keys(node)
            changed=deepcopy(root); cursor=changed
            for k in path; cursor=cursor[k]; end
            delete!(cursor,key); push!(mutations,changed)
            append!(mutations,shape_mutations!(root,vcat(path,[key])))
        end
        changed=deepcopy(root); cursor=changed
        for k in path; cursor=cursor[k]; end
        cursor["unknown"]=true; push!(mutations,changed)
        mutations
    end
    for bad in shape_mutations!(base)
        require(!valid(jl,bad),"required/closed shape mutation accepted"); structural_rejections+=1
    end
    controls=[(["backend","profile"],"python-scipy-ode/0.1.0"),(["backend","profile"],"julia-sciml-ode/99.0.0"),
              (["schema_version"],"99.0.0"),(["backend","solver","method"],"Radau"),
              (["backend","solver","options","jacobian"],"not_supplied"),
              (["backend","solver","options","time_derivative"],"not_supplied"),
              (["backend","solver","options","maxiters"],0),(["backend","evaluations","nw"],-1)]
    for (path,value) in controls
        bad=deepcopy(base); cursor=bad
        for k in path[1:end-1];cursor=cursor[k];end
        cursor[last(path)]=value
        require(!valid(jl,bad),"profile/option mutation accepted"); structural_rejections+=1
    end
    # This is intentionally a semantic audit beyond schema structure.
    semantic_rejections=0
    for mutate! in (m->(m["backend"]["solver"]["options"]["save_start"]=true),
                    m->(m["integration"]="skipped_zero_grid"),
                    m->(m["evaluations"]["nfev"]=m["execution"]["max_nfev"]+1),
                    m->(m["evaluations"]["nfev"]=0))
        bad=deepcopy(base); mutate!(bad)
        rejection(()->relations(bad,result,model("late-first"))); semantic_rejections+=1
    end
    bad=deepcopy(z); bad["backend"]["evaluations"]["nw"]=1
    rejection(()->relations(bad,pairs["zero-only"][2],model("zero-only")));semantic_rejections+=1
    tiny=deepcopy(base);tiny["execution"]["rtol"]=1e-15
    require(valid(jl,tiny),"SciPy floor leaked into Julia")
    tiny_py=load(joinpath(ORIGINALS,"late-first.manifest.json"));tiny_py["execution"]["rtol"]=1e-15
    require(!valid(py,tiny_py),"SciPy floor absent from Python")
    oracle=load(joinpath(ROOT,"conformance/production_decay/catalog.json"))
    baseline=only(c for c in oracle["cases"] if c["id"]=="baseline-zero")
    for (i,t) in enumerate(result["times"])
        sample=only(s for s in baseline["samples"] if s["time_bits"]==bits(t))
        nearest(sample["expected"],bits(result["state_values"][i][1]))
    end
    for file in ("ADR-P07-Julia.md","review_p07_julia.jl")
        readinput(joinpath(HERE,file))
    end
    for file in ("conformance/julia/Project.toml","conformance/julia/Manifest.toml","conformance/julia/p01.jl")
        readinput(joinpath(ROOT,file))
    end
    println(JSON.json(Dict("outcome"=>"PASS","status"=>"PROPOSED","implementation"=>"independent-julia-reference",
        "runtime"=>Dict("julia"=>string(VERSION),"JSON"=>string(pkgversion(JSON)),"JSONSchema"=>string(pkgversion(JSONSchema))),
        "example_pairs"=>length(NAMES),"binary64_transport_probes"=>length(probes["binary64"])+length(midpointprobes),
        "analytical_reference_samples"=>length(result["times"]),"structural_rejections"=>structural_rejections,
        "numeric_rejections"=>numeric_rejections,"semantic_rejections"=>semantic_rejections,
        "native_results_implementation"=>"NOT RUN","human_pi_ratification"=>"PENDING",
        "limits"=>"Bounded fixtures and scoped numeric converters; not a general raw JSON reader, compiler or solver audit.",
        "input_sha256"=>Dict(relpath(p,ROOT)=>bytes2hex(sha256(read(p))) for p in sort!(collect(INPUTS))))))
end
end
P07JuliaAudit.main()
