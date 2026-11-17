using Fenix.FIR: FIRModel, FIRDocument, FIRValidationError, normalized,
                 canonical_model_bytes, identity_bytes, require_capability

# Self-contained synthetic contract examples; no repository reference dependency.
function fir_model()
    parameter(id) = Dict{String,Any}("op" => "parameter", "id" => id)
    decay() = Dict{String,Any}("op" => "multiply", "left" => parameter("beta"),
                             "right" => Dict{String,Any}("op" => "state", "id" => "x"))
    Dict{String,Any}(
        "schema_version" => "0.1.0", "time_unit" => "s",
        "states" => [Dict{String,Any}("id" => "x", "quantity" => "molecular_count",
                      "scope" => "representative_cell", "unit" => "molecule", "initial" => 0.5)],
        "parameters" => [Dict{String,Any}("id" => "alpha", "unit" => "molecule/s", "value" => 10.0),
                         Dict{String,Any}("id" => "beta", "unit" => "1/s", "value" => 0.1)],
        "reactions" => [Dict{String,Any}("id" => "production", "stoichiometry" => Dict("x" => 1.0), "flux" => parameter("alpha")),
                        Dict{String,Any}("id" => "decay", "stoichiometry" => Dict("x" => -1.0), "flux" => decay())],
        "equations" => [Dict{String,Any}("state" => "x", "unit" => "molecule/s", "rhs" => Dict("op" => "subtract", "left" => parameter("alpha"), "right" => decay()))],
        "observables" => [Dict("id" => "z", "state" => "x", "unit" => "molecule"), Dict("id" => "a", "state" => "x", "unit" => "molecule")],
        "assumptions" => ["single_representative_cell", "well_mixed", "fixed_volume", "constant_rates", "no_interventions"],
        "capabilities" => Dict("ode" => true, "ssa" => false))
end
function fir_error(f, category, path)
    caught = try
        f()
        nothing
    catch error
        error
    end
    @test caught isa FIRValidationError
    if caught isa FIRValidationError
        @test caught.category == category
        @test caught.path == path
    end
end
@testset "Immutable mathematical FIR and P03 identity" begin
    raw = fir_model()
    model = FIRModel(raw)
    original = FIR.to_dict(model)
    raw["parameters"][1]["value"] = 999.0
    @test FIR.to_dict(model) == original
    exported = FIR.to_dict(model)
    exported["equations"][1]["rhs"]["left"]["id"] = "beta"
    @test FIR.to_dict(model) == original
    @test isimmutable(model) && isimmutable(model._data) && isimmutable(model._data.entries)
    normalized_model = normalized(model)
    @test [o["id"] for o in FIR.to_dict(normalized_model)["observables"]] == ["a", "z"]
    @test FIR.to_dict(model)["observables"][1]["id"] == "z"
    @test FIR.to_dict(normalized(normalized_model)) == FIR.to_dict(normalized_model)
    @test canonical_model_bytes(model) == canonical_model_bytes(normalized_model)
    @test identity_bytes(model) != canonical_model_bytes(model)
    @test model.digest == bytes2hex(FIR.sha256(identity_bytes(model)))
    @test FIR.from_json(FIRModel, canonical_model_bytes(model)).digest == model.digest
    document = FIRDocument(model=model, provenance=Dict("compiler" => Dict("name" => "example", "version" => "0")))
    @test document.digest == model.digest
    fir_error(() -> FIRDocument(model=model, provenance=Dict("display_labels" => Dict("observables" => Dict("absent" => "label")))), "REFERENCE", "/provenance/display_labels/observables/absent")
    @test FIR.from_json(FIRDocument, FIR.to_json(document)).digest == model.digest
    p = document.provenance
    p["compiler"]["name"] = "changed"
    @test document.provenance["compiler"]["name"] == "example"
    bytes = identity_bytes(document)
    bytes[1] = 0x00
    @test identity_bytes(document)[1] == 0x7b
    @test require_capability(document, "ode") === document
    fir_error(() -> require_capability(document, "ssa"), "UNSUPPORTED_PROFILE", "/profile")
    fir_error(() -> require_capability(document, "hybrid"), "UNSUPPORTED_PROFILE", "/profile")
    renamed = FIR.to_dict(model)
    renamed["observables"][1]["id"] = "renamed"
    @test FIRModel(renamed).digest != model.digest
    empty_observables = FIR.to_dict(model)
    empty_observables["observables"] = []
    @test isempty(FIR.to_dict(FIRModel(empty_observables))["observables"])
end
@testset "FIR rejection before normalization" begin
    for invalid in (0, true, big"1.0", Float32(1), big(1))
        raw = fir_model(); raw["parameters"][1]["value"] = invalid
        fir_error(() -> FIRModel(raw), "SCHEMA", "/model/parameters/0/value")
    end
    for invalid in (Inf, NaN)
        raw = fir_model(); raw["states"][1]["initial"] = invalid
        fir_error(() -> FIRModel(raw), "NUMBER_RANGE", "/model/states/0/initial")
    end
    raw = fir_model(); raw["parameters"][2]["id"] = "alpha"
    fir_error(() -> FIRModel(raw), "DUPLICATE_ID", "/model/parameters/1/id")
    raw = fir_model(); raw["parameters"][1]["unit"] = "1/s"
    fir_error(() -> FIRModel(raw), "UNIT", "/model/parameters/0/unit")
    raw = fir_model(); raw["reactions"][1]["stoichiometry"]["x"] = -1.0
    fir_error(() -> FIRModel(raw), "STOICHIOMETRY", "/model/reactions/0/stoichiometry/x")
    raw = fir_model(); reverse!(raw["parameters"])
    @test FIRModel(raw).digest == FIRModel(fir_model()).digest
    raw = fir_model(); flux = raw["reactions"][2]["flux"]
    flux["left"], flux["right"] = flux["right"], flux["left"]
    fir_error(() -> FIRModel(raw), "TEMPLATE", "/model/reactions/1/flux")
    raw = fir_model(); raw["equations"][1]["rhs"]["right"]["right"]["id"] = "missing"
    fir_error(() -> FIRModel(raw), "REFERENCE", "/model/equations/0/rhs/right/right/id")
    raw = fir_model(); raw["solver"] = "example"
    fir_error(() -> FIRModel(raw), "SCHEMA", "/model/solver")
    raw = fir_model(); raw["schema_version"] = "future"
    fir_error(() -> FIRModel(raw), "SCHEMA", "/model/schema_version")
    raw = fir_model(); raw["capabilities"]["ssa"] = true
    fir_error(() -> FIRModel(raw), "SCHEMA", "/model/capabilities/ssa")
    raw = fir_model(); raw["states"][1]["initial"] = -0.0
    zero = fir_model(); zero["states"][1]["initial"] = 0.0
    @test FIRModel(raw).digest == FIRModel(zero).digest
    raw = fir_model(); raw["parameters"][1]["value"] = nextfloat(0.0)
    @test FIR.from_json(FIRModel, canonical_model_bytes(FIRModel(raw))).digest == FIRModel(raw).digest
    fir_error(() -> FIR.from_dict(FIRDocument, Dict("model" => fir_model()); design=:missing), "SOURCE_REQUIRED", "/provenance")
end
