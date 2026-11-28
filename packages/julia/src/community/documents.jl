const STATES = ("env.signal", "receiver.reporter", "receiver.signal", "sender.signal")
const OWNERS = ("env", "receiver", "receiver", "sender")
const SCOPES = ("environment_total", "representative_cell", "representative_cell", "representative_cell")

struct _Verified end
struct Design
    text::String
    Design(::_Verified,text) = new(text)
end
struct Experiment
    text::String
    design::Design
    Experiment(::_Verified,text,design) = new(text,design)
end
struct FIR
    text::String
    FIR(::_Verified,text) = new(text)
end

to_json(doc::Union{Design,Experiment,FIR}) = doc.text
to_dict(doc::Union{Design,Experiment}) = _decode(doc.text)
to_dict(doc::FIR) = _decode(doc.text,:fir)
digest(doc::Union{Design,Experiment}) = to_dict(doc)["digest"]
_content(doc::Union{Design,Experiment}) = to_dict(doc)["content"]
_text(raw::String) = raw
_text(raw::Vector{UInt8}) = String(copy(raw))

function reference(doc::Union{Design,Experiment})
    data = to_dict(doc)
    content = data["content"]
    Dict("id" => content["id"], "revision" => Int(content["revision"]), "digest" => data["digest"])
end
_content_digest(content) = _sha(BioIR.canonical_bytes(content))
function _unique(items, field, path)
    _need(allunique(item[field] for item in items), "DUPLICATE_ID", path)
end

function _bindings(content)
    owners = content["owners"]
    _unique(owners, "id", "/content/owners")
    _unique(owners, "role", "/content/owners")
    _need(Set(o["role"] for o in owners) == Set(("sender","receiver","env")), "ROLE_COVERAGE", "/content/owners")
    addresses = Dict{NTuple{3,String},NTuple{3,String}}()
    owner_map, species_map = Dict{String,String}(), Dict{String,String}()
    for (index, owner) in enumerate(owners)
        role = owner["role"]
        owner_map[role] = owner["id"]
        species = owner["species"]
        path = "/content/owners/$(index-1)/species"
        _unique(species,"id",path)
        _unique(species,"role",path)
        expected = role == "receiver" ? Set(("signal","reporter")) : Set(("signal",))
        _need(Set(s["role"] for s in species) == expected,"ROLE_COVERAGE",path)
        for (j, definition) in enumerate(species)
            species_map[role * "." * definition["role"]] = definition["id"]
            ports = definition["ports"]
            port_path = path * "/$(j-1)/ports"
            _unique(ports,"id",port_path)
            kinds = definition["role"] == "reporter" ? Set(("sensor_in",)) : Set(("transport_out","transport_in"))
            role == "env" && push!(kinds,"density_out")
            _need(length(ports) == length(kinds) && Set(p["kind"] for p in ports) == kinds, "PORT_KINDS",port_path)
            for port in ports
                addresses[(owner["id"],definition["id"],port["id"])] = (role,definition["role"],port["kind"])
            end
        end
    end
    required = Set(((a,"signal","transport_out"),(b,"signal","transport_in"))
                   for strain in ("sender","receiver") for (a,b) in ((strain,"env"),("env",strain)))
    push!(required,(("env","signal","density_out"),("receiver","reporter","sensor_in")))
    connections = content["connections"]
    resolved = map(enumerate(connections)) do (index, edge)
        map(("source","target")) do side
            endpoint = edge[side]
            address = (endpoint["owner"],endpoint["species"],endpoint["port"])
            _need(haskey(addresses,address),"ENDPOINT","/content/connections/$(index-1)/$side")
            addresses[address]
        end
    end
    _need(length(resolved) == 5 && Set(resolved) == required,"BINDINGS","/content/connections")
    owner_map, species_map
end

function _source(text, kind, expected_digest)
    value = _decode(text)
    _validate("bioir",value)
    content = value["content"]
    _need(content["kind"] == kind,"SOURCE_KIND","/content/kind")
    _need(_content_digest(content) == value["digest"],"SOURCE_DIGEST","/digest")
    expected_digest === nothing || _need(value["digest"] == expected_digest,"SOURCE_DIGEST","/digest")
    content
end
function _predecessor(current, previous)
    if previous !== nothing
        _need(typeof(current) === typeof(previous), "REVISION","/content/id")
        a,b = reference(current),reference(previous)
        _need(a["id"] == b["id"],"REVISION","/content/id")
        _need(a["digest"] == b["digest"] || a["revision"] > b["revision"],"REVISION","/content/revision")
    end
    current
end
function from_json(::Type{Design},raw; expected_digest=nothing,previous=nothing)
    text = _text(raw)
    _bindings(_source(text,"Design",expected_digest))
    _predecessor(Design(_Verified(),text),previous)
end
function from_json(::Type{Experiment},raw; design::Design,expected_digest=nothing,previous=nothing)
    text = _text(raw)
    content = _source(text,"Experiment",expected_digest)
    _need(_equal(content["design"], reference(design)),"DESIGN_LINK","/content/design")
    _unique(content["observables"],"id","/content/observables")
    _predecessor(Experiment(_Verified(),text,design),previous)
end
function _envelope(raw)
    content = _decode(_emit(raw))
    _emit(Dict("content" => content, "digest" => _content_digest(content)))
end
from_content(::Type{Design},content) = from_json(Design,_envelope(content))
from_content(::Type{Experiment},content; design::Design) = from_json(Experiment,_envelope(content);design)
replace_content(previous::Design,content) = from_json(Design,_envelope(content);previous)
replace_content(previous::Experiment,content; design=previous.design) =
    from_json(Experiment,_envelope(content);design,previous)

const SORTED_FIELDS = (("reactions","id"),("equations","state"),("observables","id"))
_utf16(value) = Tuple(transcode(UInt16,value))
_sorted_observables(data) = sort(data;by=item -> _utf16(item["id"]))
_volumes(content) = Dict(owner["role"] => owner["volume"] for owner in content["owners"])

function from_json(::Type{FIR},raw; experiment::Experiment)
    text = _text(raw)
    value = _decode(text,:fir)
    _validate("fir",value)
    model, provenance = value["model"],value["provenance"]
    design = experiment.design
    experiment_content, design_content = _content(experiment),_content(design)
    for key in ("parameters","populations","initial_counts")
        _need(_equal(model[key],experiment_content[key]),"SOURCE_CORRESPONDENCE","/model/$key")
    end
    for (key,field) in SORTED_FIELDS
        _unique(model[key],field,"/model/$key")
    end
    _need(_equal(_sorted_observables(model["observables"]),_sorted_observables(experiment_content["observables"])),
          "SOURCE_CORRESPONDENCE","/model/observables")
    _need(_equal(model["volumes"],_volumes(design_content)), "SOURCE_CORRESPONDENCE","/model/volumes")
    for (key,source) in (("design_digest",design),("experiment_digest",experiment))
        _need(provenance[key] == digest(source),"SOURCE_CORRESPONDENCE","/provenance/$key")
    end
    for (key,source_map) in zip(("owners","species"),_bindings(design_content))
        _need(_equal(provenance[key],source_map),"SOURCE_CORRESPONDENCE","/provenance/$key")
    end
    FIR(_Verified(),text)
end

function normalized_model(fir::FIR)
    model = to_dict(fir)["model"]
    for (key,field) in SORTED_FIELDS
        sort!(model[key];by=item -> _utf16(item[field]))
    end
    model
end
model_bytes(fir::FIR) = BioIR.canonical_bytes(normalized_model(fir))
identity_bytes(fir::FIR) = BioIR.canonical_bytes(Dict("domain"=>"fenix.fir",
    "canonicalization_version"=>"0.2.0","model"=>normalized_model(fir)))
digest(fir::FIR) = _sha(identity_bytes(fir))

function compile_experiment(experiment::Experiment)
    source, design = _content(experiment), _content(experiment.design)
    grammar = CONTRACTS["fir"]["properties"]["model"]["properties"]
    model = Dict{String,Any}(key => grammar[key]["const"] for key in
                            ("schema_version","template","time_unit","capabilities"))
    for key in ("parameters","populations","initial_counts","observables")
        model[key] = source[key]
    end
    model["volumes"] = _volumes(design)
    for key in ("reactions","equations")
        model[key] = grammar[key]["items"]["enum"]
    end
    owners,species = _bindings(design)
    provenance = Dict("design_digest"=>digest(experiment.design),"experiment_digest"=>digest(experiment),
                      "owners"=>owners,"species"=>species)
    from_json(FIR,_emit(Dict("model"=>model,"provenance"=>provenance));experiment)
end
