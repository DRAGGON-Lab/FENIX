# Immutable P01 document envelopes and exact local Design resolution.
# Content self-consistency is separate from trust, origin and archival persistence.
using SHA
export Metadata, DesignDocument, ExperimentDocument, from_json, reference,
       canonical_content_bytes, replace_content, with_metadata

struct Metadata
    name::Union{Nothing,String}
    description::Union{Nothing,String}
    function Metadata(; name=nothing, description=nothing)
        for (key, value) in (("name", name), ("description", description))
            value === nothing && continue
            require(value isa String, "/" * key, "expected a string")
            require(isvalid(value), "/" * key, "invalid Unicode", "INVALID_UNICODE")
        end
        new(name, description)
    end
end
function to_dict(metadata::Metadata)
    Dict{String,Any}(string(key) => getfield(metadata, key)
                    for key in (:name, :description) if getfield(metadata, key) !== nothing)
end
_doc_pointer(path, key) = path * "/" * replace(string(key), "~" => "~0", "/" => "~1")
function _doc_prefix(f, path)
    try
        f()
    catch error
        error isa BioIRValidationError || rethrow()
        throw(BioIRValidationError(error.category, path * error.path, error.message))
    end
end
function _doc_metadata(value)
    require(value === nothing || typeof(value) === Metadata, "/metadata", "expected Metadata or nothing")
    value
end
function _doc_digest(value, path="/digest")
    require(value isa String && isvalid(value) && occursin(r"\A[0-9a-f]{64}\z", value), path,
            "expected lowercase hexadecimal SHA-256")
    value
end
abstract type BioIRDocument end
struct DesignDocument <: BioIRDocument
    content::DesignContent
    metadata::Union{Nothing,Metadata}
    digest::String
    _canonical::String
    function DesignDocument(; content, metadata=nothing)
        typed(content, DesignContent, "/content")
        _doc_metadata(metadata)
        bytes = canonical_bytes(to_dict(content))
        new(content, metadata, bytes2hex(sha256(bytes)), String(bytes))
    end
end
reference(document::DesignDocument) = DesignReference(id=document.content.id,
    revision=document.content.revision, digest=document.digest)
struct ExperimentDocument <: BioIRDocument
    content::ExperimentContent
    source_design::DesignDocument
    metadata::Union{Nothing,Metadata}
    digest::String
    _canonical::String
    function ExperimentDocument(; content, source_design, metadata=nothing)
        typed(content, ExperimentContent, "/content")
        typed(source_design, DesignDocument, "/source_design")
        _doc_metadata(metadata)
        expected = reference(source_design)
        for key in (:id, :revision, :digest)
            require(getfield(content.design, key) == getfield(expected, key),
                "/content/design/" * string(key), "reference differs from verified local Design", "DESIGN_REFERENCE")
        end
        # Revalidate against this exact Design, rather than an earlier uncommitted
        # context with the same ID/revision but different biological declarations.
        args = (; (key => getfield(content, key) for key in fieldnames(ExperimentContent))...)
        _doc_prefix("/content") do
            ExperimentContent(; args..., source_design=source_design.content)
        end
        bytes = canonical_bytes(to_dict(content))
        new(content, source_design, metadata, bytes2hex(sha256(bytes)), String(bytes))
    end
end
"""Fresh direct JCS scientific-content bytes; digest and metadata are excluded."""
canonical_content_bytes(document::BioIRDocument) = Vector{UInt8}(codeunits(document._canonical))
function to_dict(document::BioIRDocument)
    result = Dict{String,Any}("content" => to_dict(document.content), "digest" => document.digest)
    document.metadata === nothing || (result["metadata"] = to_dict(document.metadata))
    result
end
"""Transport JSON, separate from canonical bytes and their numeric spellings."""
to_json(document::BioIRDocument) = JSON.json(to_dict(document))
with_metadata(document::DesignDocument, metadata) = DesignDocument(content=document.content, metadata=metadata)
with_metadata(document::ExperimentDocument, metadata) = ExperimentDocument(content=document.content,
    source_design=document.source_design, metadata=metadata)
function _doc_previous(current::BioIRDocument, previous)
    previous === nothing && return current
    require(typeof(previous) === typeof(current), "/previous", "expected same document type")
    require(current.content.id == previous.content.id, "/content/id", "replacement changes logical ID", "REFERENCE")
    require(current.digest == previous.digest || current.content.revision > previous.content.revision,
        "/content/revision", "changed content must advance trusted predecessor revision", "IMMUTABLE_REVISION")
    current
end
replace_content(document::DesignDocument, content) = _doc_previous(
    DesignDocument(content=content, metadata=document.metadata), document)
function replace_content(document::ExperimentDocument, content; source_design=document.source_design)
    _doc_previous(ExperimentDocument(content=content, source_design=source_design,
        metadata=document.metadata), document)
end

# Wire decoding checks every required member, including fields with native
# constructor defaults. These checks load no schemas, fixtures or network data.
function _doc_members(value, required, allowed, path)
    require(value isa AbstractDict, path, "expected an object")
    for key in sort!(collect(required))
        require(haskey(value, key), _doc_pointer(path, key), "required member missing")
    end
    for key in keys(value)
        require(key isa String, path, "expected string member name")
        require(key in allowed, _doc_pointer(path, key), "unknown member")
    end
    value
end
const _DOC_CHILDREN = Dict(
    Compartment => Dict(:volume => (Quantity, nothing, false)),
    Species => Dict(:ports => (Port, 1, true)),
    BioIRFunction => Dict(:target => (PortReference, nothing, false)),
    ParameterAssignment => Dict(:quantity => (Quantity, nothing, false)),
    InitialCount => Dict(:quantity => (Quantity, nothing, false)),
    Observable => Dict(:target => (PortReference, nothing, false)),
    DesignContent => Dict(:compartments => (Compartment, 1, true),
        :species => (Species, 1, true), :parameters => (Parameter, 2, true),
        :functions => (BioIRFunction, 2, true)),
    ExperimentContent => Dict(:design => (DesignReference, nothing, false),
        :parameters => (ParameterAssignment, 2, true),
        :initial_counts => (InitialCount, 1, true), :observables => (Observable, nothing, true)),
)
function _doc_arguments(T, raw, path)
    names = Set(string.(fieldnames(T)))
    data = _doc_members(raw, names, names, path)
    args = Dict{Symbol,Any}(Symbol(key) => value for (key, value) in data)
    # Iterate declaration order so diagnostics are deterministic, without
    # prescribing a universal precedence for documents with multiple faults.
    children = get(_DOC_CHILDREN, T, nothing)
    for name in fieldnames(T)
        children === nothing && break
        haskey(children, name) || continue
        child_type, size, repeated = children[name]
        child_path = _doc_pointer(path, name)
        value = args[name]
        if repeated
            require(value isa AbstractVector, child_path, "expected an array")
            size === nothing || require(length(value) == size, child_path, "incorrect M0 collection size")
            args[name] = Tuple(_doc_build(child_type, item, _doc_pointer(child_path, i-1))
                for (i, item) in enumerate(value))
        else
            args[name] = _doc_build(child_type, value, child_path)
        end
    end
    if haskey(args, :revision)
        value = args[:revision]
        if value isa Float64 && isfinite(value) && isinteger(value) && 1 <= value <= MAX_INTEGER
            args[:revision] = Int64(value)
        end
    end
    if T === ExperimentContent
        require(data["interventions"] isa AbstractVector && isempty(data["interventions"]),
            path * "/interventions", "expected empty interventions array")
        args[:interventions] = ()
    end
    args
end
function _doc_build(T, raw, path; context...)
    args = _doc_arguments(T, raw, path)
    _doc_prefix(path) do
        T(; args..., context...)
    end
end
function _doc_structure(raw, T)
    args = _doc_arguments(T, raw, "/content")
    kind = T === DesignContent ? "Design" : "Experiment"
    _doc_prefix("/content") do
        header(args[:kind], kind, args[:schema_version], args[:id], args[:revision])
    end
    raw
end
function _doc_envelope(raw, T)
    data = _doc_members(raw, Set(["content", "digest"]), Set(["content", "digest", "metadata"]), "")
    claimed = _doc_digest(data["digest"])
    metadata = nothing
    if haskey(data, "metadata")
        fields = _doc_members(data["metadata"], Set{String}(), Set(["name", "description"]), "/metadata")
        for (key, value) in fields
            require(value isa String, _doc_pointer("/metadata", key), "expected a string")
        end
        metadata = _doc_prefix("/metadata") do
            Metadata(; (Symbol(key) => value for (key, value) in fields)...)
        end
    end
    content = _doc_structure(data["content"], T)
    content, claimed, metadata
end
function _doc_verify(raw, claimed, expected)
    actual = bytes2hex(sha256(canonical_bytes(raw)))
    require(actual == claimed, "/digest", "digest differs from canonical scientific content", "DIGEST")
    if expected !== nothing
        _doc_digest(expected)
        require(actual == expected, "/digest", "digest differs from caller's trusted expectation", "DIGEST")
    end
    nothing
end
function from_json(::Type{DesignDocument}, raw; expected_digest=nothing, previous=nothing)
    content, claimed, metadata = _doc_envelope(parse_json(raw), DesignContent)
    _doc_verify(content, claimed, expected_digest)
    result = DesignDocument(content=_doc_build(DesignContent, content, "/content"), metadata=metadata)
    _doc_previous(result, previous)
end
function _doc_resolve(content, designs)
    require(designs isa Tuple || designs isa AbstractVector, "/designs", "expected local verified Design collection")
    candidates = Tuple(designs)
    for item in candidates
        typed(item, DesignDocument, "/designs")
    end
    for name in ("id", "revision", "digest")
        candidates = Tuple(item for item in candidates if
            (name == "digest" ? item.digest : getfield(item.content, Symbol(name))) == content["design"][name])
        require(!isempty(candidates), "/content/design/" * name, "no local Design matches exact reference", "DESIGN_REFERENCE")
    end
    first(candidates)
end
function from_json(::Type{ExperimentDocument}, raw; designs, expected_digest=nothing, previous=nothing)
    content, claimed, metadata = _doc_envelope(parse_json(raw), ExperimentContent)
    # Verify Experiment self-consistency before attempting reference resolution.
    _doc_verify(content, claimed, expected_digest)
    source = _doc_resolve(content, designs)
    native = _doc_build(ExperimentContent, content, "/content"; source_design=source.content)
    _doc_previous(ExperimentDocument(content=native, source_design=source, metadata=metadata), previous)
end
