# Native identity regressions. No shared fixtures or reference tools required.
using SHA

function committed_pair(; source=DesignDocument(content=design()))
    content = experiment(source_design=source.content, design=reference(source))
    source, ExperimentDocument(content=content, source_design=source)
end

# Recompute an envelope to isolate a semantic defect from stale digest handling.
function rehash_envelope(raw)
    result = deepcopy(raw)
    result["digest"] = bytes2hex(sha256(canonical_bytes(result["content"])))
    JSON.json(result)
end

@testset "Committed content identity and immutable snapshots" begin
    d, e = committed_pair()
    for document in (d, e)
        @test length(document.digest) == 64
        @test document.digest == bytes2hex(sha256(canonical_content_bytes(document)))
        @test JSON.parse(String(canonical_content_bytes(document))) == to_dict(document.content)
        bytes = canonical_content_bytes(document)
        bytes[1] = 0x00
        @test canonical_content_bytes(document)[1] == UInt8('{')
        exported = to_dict(document)
        exported["content"]["id"] = "changed"
        exported["digest"] = repeat("0",64)
        @test to_dict(document)["content"]["id"] == document.content.id
        @test to_dict(document)["digest"] == document.digest
        @test_throws Exception setproperty!(document, :digest, repeat("f",64))
    end
    @test reference(d).id == d.content.id
    @test reference(d).revision == d.content.revision
    @test reference(d).digest == d.digest
    @test e.source_design === d
    checkerror("SCHEMA", "/content", () -> DesignDocument(content=to_dict(d.content)))
    checkerror("SCHEMA", "/source_design", () -> ExperimentDocument(content=e.content, source_design=d.content))
    @test_throws MethodError DesignDocument(d.content, d.digest)
    @test_throws MethodError ExperimentDocument(e.content, d, e.digest)
end

@testset "Document transport and trusted integrity" begin
    d, e = committed_pair()
    reread_d = from_json(DesignDocument, to_json(d); expected_digest=d.digest)
    reread_e = from_json(ExperimentDocument, Vector{UInt8}(codeunits(to_json(e))); designs=[reread_d], expected_digest=e.digest)
    @test reread_d.digest == d.digest
    @test reread_e.digest == e.digest
    @test to_dict(reread_e) == to_dict(e)
    checkerror("DIGEST", "/digest", () -> from_json(DesignDocument, to_json(d); expected_digest=repeat("0",64)))
    checkerror("SCHEMA", "/digest", () -> from_json(DesignDocument, to_json(d); expected_digest="bad"))
    checkerror("DIGEST", "/digest", () -> from_json(ExperimentDocument, to_json(e); designs=[d], expected_digest=repeat("0",64)))
    for document in (d, e)
        tampered = to_dict(document)
        tampered["content"]["revision"] = 2
        if document isa DesignDocument
            checkerror("DIGEST", "/digest", () -> from_json(DesignDocument, JSON.json(tampered)))
        else
            # Own integrity must fail before looking for a missing local Design.
            checkerror("DIGEST", "/digest", () -> from_json(ExperimentDocument, JSON.json(tampered); designs=()))
        end
    end
    replacement = DesignDocument(content=design(revision=2))
    @test from_json(DesignDocument, to_json(replacement)).digest == replacement.digest
    checkerror("DIGEST", "/digest", () -> from_json(DesignDocument, to_json(replacement); expected_digest=d.digest))
    for value in (-0.0, nextfloat(0.0), Float64(2)^53, 1.0e20, floatmax(Float64))
        source = DesignDocument(content=design(compartments=[Compartment(id="cell", volume=Quantity(value=1e-15,unit="L"))]))
        content = experiment(source_design=source.content, design=reference(source),
            parameters=[ParameterAssignment(parameter="alpha",quantity=Quantity(value=value,unit="molecule/s")),
                        ParameterAssignment(parameter="beta",quantity=Quantity(value=0,unit="1/s"))])
        document = ExperimentDocument(content=content, source_design=source)
        decoded = from_json(ExperimentDocument, to_json(document); designs=(source,))
        @test decoded.digest == document.digest
        @test isequal(decoded.content.parameters[1].quantity.value, value)
    end
end

@testset "Exact local Design correspondence" begin
    d, e = committed_pair()
    checkerror("DESIGN_REFERENCE", "/content/design/id", () -> from_json(ExperimentDocument,to_json(e);designs=()))
    for (field, value) in (("id","other"), ("revision",2), ("digest",repeat("f",64)))
        raw = to_dict(e)
        raw["content"]["design"][field] = value
        checkerror("DESIGN_REFERENCE", "/content/design/"*field,
            () -> from_json(ExperimentDocument,rehash_envelope(raw);designs=(d,)))
    end
    incorrect = experiment(source_design=d.content,
        design=DesignReference(id=d.content.id,revision=d.content.revision,digest=repeat("f",64)))
    checkerror("DESIGN_REFERENCE", "/content/design/digest",
        () -> ExperimentDocument(content=incorrect,source_design=d))
    alternate = DesignDocument(content=design(compartments=[Compartment(id="cell",volume=Quantity(value=2e-15,unit="L"))]))
    checkerror("DESIGN_REFERENCE", "/content/design/digest",
        () -> from_json(ExperimentDocument,to_json(e);designs=(alternate,)))
    @test from_json(ExperimentDocument,to_json(e);designs=[alternate,d]).digest == e.digest
    @test from_json(ExperimentDocument,to_json(e);designs=(with_metadata(d,Metadata(name="alternate envelope")),)).digest == e.digest
    # A self-consistent claimed pair is not an authenticated source.
    alternate_content = experiment(source_design=alternate.content,design=reference(alternate))
    alternate_experiment = ExperimentDocument(content=alternate_content,source_design=alternate)
    @test from_json(ExperimentDocument,to_json(alternate_experiment);designs=(alternate,)).digest == alternate_experiment.digest
end

@testset "Verified context revalidation" begin
    verified = DesignDocument(content=design())
    p = PortReference(species="x",port="otheramount")
    alternate = design(species=[Species(id="x",compartment="cell",ports=[Port(id="otheramount")])],
        functions=[BioIRFunction(id="production",kind="constitutive_production",target=p,parameter="alpha"),
                   BioIRFunction(id="decay",kind="first_order_decay",target=p,parameter="beta")])
    unchecked = experiment(source_design=alternate, design=reference(verified),
        observables=[Observable(id="amount_x",target=p)])
    checkerror("REFERENCE", "/content/observables/0/target/port",
        () -> ExperimentDocument(content=unchecked,source_design=verified))
end

@testset "Metadata amendments and revision replacement" begin
    d, e = committed_pair()
    metadata = Metadata(name="α 🧬",description="new\nannotation")
    for document in (d,e)
        amended = with_metadata(document,metadata)
        @test amended !== document
        @test amended.digest == document.digest
        @test canonical_content_bytes(amended) == canonical_content_bytes(document)
        @test !haskey(to_dict(document),"metadata")
        @test to_dict(amended)["metadata"]["name"] == "α 🧬"
        @test !haskey(to_dict(with_metadata(amended,nothing)),"metadata")
    end
    @test to_dict(with_metadata(d,Metadata()))["metadata"] == Dict()
    checkerror("INVALID_UNICODE", "/name", () -> Metadata(name=String(UInt8[0xff])))
    checkerror("SCHEMA", "/name", () -> Metadata(name=1))
    checkerror("SCHEMA", "/metadata", () -> DesignDocument(content=d.content,metadata=Dict("name"=>"bad")))
    @test from_json(DesignDocument,to_json(with_metadata(d,metadata));previous=d).digest == d.digest
    advanced = replace_content(d,design(revision=2))
    @test advanced.content.revision == 2
    @test d.content.revision == 1
    @test advanced.digest != d.digest
    checkerror("IMMUTABLE_REVISION", "/content/revision", () -> replace_content(d,design(functions=reverse(d.content.functions))))
    checkerror("IMMUTABLE_REVISION", "/content/revision", () -> from_json(DesignDocument,to_json(d);previous=advanced))
    checkerror("REFERENCE", "/content/id", () -> replace_content(d,design(id="different",revision=2)))
    advanced_experiment = experiment(revision=2,source_design=d.content,design=reference(d))
    next_e = replace_content(e,advanced_experiment)
    @test next_e.digest != e.digest
    @test next_e.source_design === d
    checkerror("IMMUTABLE_REVISION", "/content/revision", () -> from_json(ExperimentDocument,to_json(e);designs=(d,),previous=next_e))
end

@testset "Strict committed envelope structure" begin
    d, e = committed_pair()
    for (mutate, path) in ((raw -> raw["extra"]=1,"/extra"),
                           (raw -> raw["content"]["extra"]=1,"/content/extra"),
                           (raw -> delete!(raw["content"],"id"),"/content/id"),
                           (raw -> raw["metadata"]=nothing,"/metadata"),
                           (raw -> raw["metadata"]=Dict("name"=>nothing),"/metadata/name"),
                           (raw -> raw["metadata"]=Dict("extra"=>"unknown"),"/metadata/extra"))
        raw = to_dict(d); mutate(raw)
        checkerror("SCHEMA",path,() -> from_json(DesignDocument,JSON.json(raw)))
    end
    for key in ("kind","schema_version")
        raw=to_dict(d);delete!(raw["content"],key)
        checkerror("SCHEMA","/content/"*key,() -> from_json(DesignDocument,JSON.json(raw)))
    end
    raw=to_dict(e);raw["content"]["profile"]="ode"
    checkerror("SCHEMA","/content/profile",() -> from_json(ExperimentDocument,JSON.json(raw);designs=(d,)))
    # Schema integer values may have decimal/exponent spellings without changing identity.
    raw=to_dict(d);raw["content"]["revision"]=1.0
    @test from_json(DesignDocument,JSON.json(raw)).digest == d.digest
end
