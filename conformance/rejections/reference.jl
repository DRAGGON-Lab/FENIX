# Independent Julia M0 references. Never import Python or native Fenix packages.
module RejectionReference
include("../julia/p01.jl")
using .P01Reference, JSON, JSONSchema, SHA
const P = P01Reference
const ROOT = normpath(joinpath(@__DIR__, "../.."))
const HERE = @__DIR__
const Rejection = P.Rejection
const pointer = P.pointer
reject(category, path="") = P.reject(category, path)
const BIOIR = JSON.parsefile(joinpath(ROOT, "spec/bioir/proposals/bioir-m0.schema.json"))
const FIR = JSON.parsefile(joinpath(ROOT, "spec/fir/proposals/fir-m0.schema.json"))
const OPERATIONS = Dict(
    "parse" => Set(["primary"]), "design" => Set(["primary"]),
    "experiment" => Set(["primary", "design"]), "revision" => Set(["primary", "previous"]),
    "model" => Set(["primary"]), "producer" => Set(["primary", "design", "experiment"]),
    "capability" => Set(["primary", "request"]))
sha(raw) = bytes2hex(sha256(raw))
function parse_input(raw, contract)
    contract in ("P01", "P03") || error("Unknown parser contract")
    P.strict_parse(raw; numeric_policy=Symbol(lowercase(contract)), detailed=true)
end
function read_artifact(artifact; root=ROOT)
    relative = artifact["path"]
    parts = split(relative, '/')
    (!isabspath(relative) && !(".." in parts) && !occursin('\\', relative) &&
     first(parts) in ("conformance", "spec") && joinpath(parts...) == relative) || error("Invalid artifact path")
    path = realpath(joinpath(root, relative))
    startswith(path, realpath(root) * "/") || error("Artifact escapes repository")
    raw = read(path)
    sha(raw) == artifact["sha256"] || error("Artifact checksum mismatch: $relative")
    raw
end
function load_catalog(; directory=HERE, root=ROOT)
    catalog = P.strict_parse(read(joinpath(directory, "catalog.json")))
    schema = JSONSchema.Schema(JSON.parsefile(joinpath(directory, "catalog.schema.json")))
    JSONSchema.validate(schema, catalog) === nothing || error("Invalid catalog structure")
    index = Dict(c["id"] => c for c in catalog["cases"])
    length(index) == length(catalog["cases"]) || error("Duplicate catalog IDs")
    for (group, ids) in catalog["coverage"]
        length(Set(ids)) == length(ids) && issubset(Set(ids), Set(keys(index))) || error("Duplicate or unknown coverage reference: $group")
    end
    referenced = Set{String}()
    for case in catalog["cases"]
        Set(keys(case["inputs"])) == OPERATIONS[case["operation"]] || error("Missing or extra dependencies")
        op = case["operation"]
        ((op in ("design", "experiment", "revision") && case["contract"] != "P01") ||
         (op in ("model", "producer", "capability") && case["contract"] != "P03")) && error("Wrong raw-input contract")
        expected = case["expected"]
        expected["outcome"] == "reject" && !haskey(case["inputs"], expected["document"]) && error("Diagnostic identifies absent document")
        for artifact in values(case["inputs"])
            read_artifact(artifact; root=root)
            push!(referenced, artifact["path"])
        end
    end
    physical = Set{String}()
    for (folder, _, files) in walkdir(joinpath(directory, "inputs")), file in files
        push!(physical, relpath(joinpath(folder, file), root))
    end
    local_prefix = relpath(directory, root) * "/inputs/"
    Set(p for p in referenced if startswith(p, local_prefix)) == physical || error("Orphaned or missing new artifacts")
    historical = JSON.parsefile(joinpath(root, "conformance/canonicalization/catalog.json"))
    required = Set(("conformance/canonicalization/" * c["input"]["path"], c["input"]["sha256"], c["expected_outcome"])
                   for c in historical["cases"] if c["stage"] == "contract_only")
    ids = catalog["coverage"]["p03-contract-only"]
    actual = Set((index[id]["inputs"]["primary"]["path"], index[id]["inputs"]["primary"]["sha256"], index[id]["expected"]["outcome"]) for id in ids)
    length(ids) == length(required) && actual == required || error("Incomplete P03 contract-only coverage")
    examples = Set("spec/fir/proposals/examples/" * name for name in readdir(joinpath(root, "spec/fir/proposals/examples")) if endswith(name, ".json"))
    ids = catalog["coverage"]["p02-examples"]
    actual = Set(index[id]["inputs"]["primary"]["path"] for id in ids)
    length(ids) == length(examples) && actual == examples || error("Incomplete P02 example coverage")
    catalog
end
function diagnostic_schema(schema, value, root)
    if haskey(schema, "\$ref")
        target = root
        for key in split(schema["\$ref"], '/')[2:end]
            target = target[key]
        end
        return diagnostic_schema(target, value, root)
    end
    result = copy(schema)
    if haskey(schema, "oneOf") && value isa AbstractDict
        for branch in schema["oneOf"]
            resolved = haskey(branch, "\$ref") ? root["definitions"][last(split(branch["\$ref"], '/'))] : branch
            if any(haskey(value, k) && haskey(prop, "const") && value[k] == prop["const"]
                   for (k, prop) in get(resolved, "properties", Dict()) if k in ("kind", "op"))
                return diagnostic_schema(resolved, value, root)
            end
        end
    end
    if value isa AbstractDict && haskey(schema, "properties")
        result["properties"] = Dict(k => (haskey(value, k) ? diagnostic_schema(s, value[k], root) : s) for (k, s) in schema["properties"])
    elseif value isa AbstractVector && get(schema, "items", nothing) isa AbstractDict
        result["items"] = [diagnostic_schema(schema["items"], v, root) for v in value]
    end
    result
end
function validate_structure(doc, schema)
    JSONSchema.validate(JSONSchema.Schema(deepcopy(schema)), doc) === nothing && return
    diagnostic = diagnostic_schema(schema, doc, schema)
    issue = JSONSchema.validate(JSONSchema.Schema(JSON.parse(JSON.json(diagnostic))), doc)
    issue === nothing && error("Diagnostic schema masked a structural error")
    # Public library pointer retains actual object keys and zero-based array indices.
    path = JSONSchema.URIs.unescapeuri(JSONSchema.json_pointer(issue)[2:end])
    if issue.reason == "required"
        missing = sort(collect(setdiff(Set(issue.val), Set(keys(issue.x)))))
        path = pointer(path, first(missing))
    elseif issue.reason == "additionalProperties" && issue.val === false
        subschema = diagnostic
        instance = doc
        if !isempty(path)
            for token in split(path, '/')[2:end]
                key = replace(token, "~1" => "/", "~0" => "~")
                if instance isa AbstractVector
                    i = Base.parse(Int, key) + 1
                    subschema = subschema["items"][i]; instance = instance[i]
                else
                    subschema = subschema["properties"][key]; instance = instance[key]
                end
            end
        end
        extras = sort(collect(setdiff(Set(keys(issue.x)), Set(keys(get(subschema, "properties", Dict()))))))
        path = pointer(path, first(extras))
    end
    reject("SCHEMA", path)
end
function validate_model(doc)
    validate_structure(doc, FIR)
    m = doc["model"]
    states = P.unique_items(m["states"], "id", "/model/states")
    parameters = P.unique_items(m["parameters"], "id", "/model/parameters")
    reactions = P.unique_items(m["reactions"], "id", "/model/reactions")
    equations = P.unique_items(m["equations"], "state", "/model/equations")
    P.unique_items(m["observables"], "id", "/model/observables")
    for (collection, key, expected) in ((parameters, "parameters", Set(["alpha", "beta"])),
                                       (reactions, "reactions", Set(["production", "decay"])),
                                       (equations, "equations", Set(["x"])))
        if Set(keys(collection)) != expected
            key == "equations" && reject("REFERENCE", "/model/equations/0/state")
            reject("ROLE", "/model/" * key)
        end
    end
    for (i, p) in enumerate(m["parameters"])
        p["unit"] == (p["id"] == "alpha" ? "molecule/s" : "1/s") || reject("UNIT", "/model/parameters/$(i-1)/unit")
    end
    function references(expr, path)
        if expr["op"] in ("parameter", "state")
            namespace = expr["op"] == "parameter" ? parameters : states
            haskey(namespace, expr["id"]) || reject("REFERENCE", path * "/id")
        else
            references(expr["left"], path * "/left")
            references(expr["right"], path * "/right")
        end
    end
    for (collection, field) in (("reactions", "flux"), ("equations", "rhs"))
        for (i, item) in enumerate(m[collection])
            references(item[field], "/model/$collection/$(i-1)/$field")
        end
    end
    for (i, item) in enumerate(m["observables"])
        haskey(states, item["state"]) || reject("REFERENCE", "/model/observables/$(i-1)/state")
    end
    # Exact ratified trees; no evaluation, commutation or algebraic approximation.
    alpha = Dict("op" => "parameter", "id" => "alpha")
    decay = Dict("op" => "multiply", "left" => Dict("op" => "parameter", "id" => "beta"), "right" => Dict("op" => "state", "id" => "x"))
    rhs = Dict("op" => "subtract", "left" => alpha, "right" => decay)
    for (i, reaction) in enumerate(m["reactions"])
        production = reaction["id"] == "production"
        path = "/model/reactions/$(i-1)"
        reaction["stoichiometry"]["x"] == (production ? 1 : -1) || reject("STOICHIOMETRY", path * "/stoichiometry/x")
        reaction["flux"] == (production ? alpha : decay) || reject("TEMPLATE", path * "/flux")
    end
    m["equations"][1]["rhs"] == rhs || reject("TEMPLATE", "/model/equations/0/rhs")
    doc
end
function validate_producer(doc, design, experiment)
    m = doc["model"]
    haskey(doc, "provenance") || reject("SOURCE_REQUIRED", "/provenance")
    p = doc["provenance"]
    for key in ("design_digest", "experiment_digest", "symbol_map")
        haskey(p, key) || reject("SOURCE_REQUIRED", "/provenance/" * key)
    end
    for (key, source) in (("design_digest", design), ("experiment_digest", experiment))
        p[key] == source["digest"] || reject("SOURCE_DIGEST", "/provenance/" * key)
    end
    d, e = design["content"], experiment["content"]
    state = p["symbol_map"]["states"][1]
    path = "/provenance/symbol_map/states/0"
    species = Dict(s["id"] => s for s in d["species"])
    haskey(species, state["bioir_species_id"]) || reject("REFERENCE", path * "/bioir_species_id")
    s = species[state["bioir_species_id"]]
    state["bioir_port_id"] in [p["id"] for p in s["ports"]] || reject("REFERENCE", path * "/bioir_port_id")
    state["bioir_compartment_id"] == s["compartment"] || reject("REFERENCE", path * "/bioir_compartment_id")
    source_parameters = Dict(p["id"] => p for p in d["parameters"])
    functions = Dict(f["id"] => f for f in d["functions"])
    assignments = Dict(p["parameter"] => p["quantity"] for p in e["parameters"])
    fir_parameters = Dict(p["id"] => (i, p) for (i, p) in enumerate(m["parameters"]))
    for (i, entry) in enumerate(p["symbol_map"]["parameters"])
        path = "/provenance/symbol_map/parameters/$(i-1)"
        parameter, function_id = entry["bioir_parameter_id"], entry["bioir_function_id"]
        haskey(source_parameters, parameter) || reject("REFERENCE", path * "/bioir_parameter_id")
        haskey(functions, function_id) || reject("REFERENCE", path * "/bioir_function_id")
        f = functions[function_id]
        kind = entry["fir_parameter_id"] == "alpha" ? "constitutive_production" : "first_order_decay"
        (f["kind"] == kind && f["parameter"] == parameter &&
         f["target"] == Dict("species" => s["id"], "port" => state["bioir_port_id"])) || reject("SOURCE_ROLE", path * "/bioir_function_id")
        entry["bioir_function_kind"] == f["kind"] || reject("SOURCE_ROLE", path * "/bioir_function_kind")
        j, target = fir_parameters[entry["fir_parameter_id"]]
        target["unit"] == assignments[parameter]["unit"] || reject("UNIT", "/model/parameters/$(j-1)/unit")
        target["value"] == assignments[parameter]["value"] || reject("SOURCE_VALUE", "/model/parameters/$(j-1)/value")
    end
    initial = only([item["quantity"] for item in e["initial_counts"] if item["species"] == s["id"]])
    m["states"][1]["initial"] == initial["value"] || reject("SOURCE_VALUE", "/model/states/0/initial")
    m["states"][1]["unit"] == initial["unit"] || reject("UNIT", "/model/states/0/unit")
    source_observables = Dict(o["id"] => o for o in e["observables"])
    for (i, o) in enumerate(m["observables"])
        path = "/model/observables/$(i-1)"
        haskey(source_observables, o["id"]) || reject("SOURCE_OBSERVABLE", path * "/id")
        source = source_observables[o["id"]]
        (source["target"] == Dict("species" => s["id"], "port" => state["bioir_port_id"]) &&
         o["state"] == state["fir_state_id"]) || reject("SOURCE_OBSERVABLE", path * "/state")
        o["unit"] == m["states"][1]["unit"] || reject("UNIT", path * "/unit")
    end
    Set(o["id"] for o in m["observables"]) == Set(keys(source_observables)) || reject("SOURCE_OBSERVABLE", "/model/observables")
    for key in keys(get(get(p, "display_labels", Dict()), "observables", Dict()))
        key in [o["id"] for o in m["observables"]] || reject("REFERENCE", pointer("/provenance/display_labels/observables", key))
    end
end
function observe(case; root=ROOT)
    stage, document = "parse", "primary"
    try
        doc = parse_input(read_artifact(case["inputs"]["primary"]; root=root), case["contract"])
        op = case["operation"]
        dependencies = Dict{String,Any}()
        for identity in ("design", "experiment", "previous")
            if haskey(case["inputs"], identity)
                document, stage = identity, "parse"
                source = parse_input(read_artifact(case["inputs"][identity]; root=root), "P01")
                stage = "structure"; validate_structure(source, BIOIR)
                stage = "semantic"
                if identity == "experiment"
                    P.validate_experiment(source, dependencies["design"])
                else
                    P.validate_design(source)
                end
                dependencies[identity] = source
            end
        end
        document, stage = "primary", "structure"
        if op in ("design", "experiment", "revision")
            validate_structure(doc, BIOIR)
            stage = "semantic"
            if op == "design"
                P.validate_design(doc)
            elseif op == "experiment"
                P.validate_experiment(doc, dependencies["design"])
            else
                P.validate_revision(doc, dependencies["previous"])
            end
        elseif op in ("model", "producer", "capability")
            validate_structure(doc, FIR)
            stage = "semantic"; validate_model(doc)
            if op == "producer"
                stage = "producer"
                validate_producer(doc, dependencies["design"], dependencies["experiment"])
            elseif op == "capability"
                document, stage = "request", "parse"
                request = parse_input(read_artifact(case["inputs"]["request"]; root=root), "P03")
                (request isa AbstractDict && Set(keys(request)) == Set(["profile"]) && request["profile"] isa AbstractString) || error("Invalid reference-harness capability request")
                stage = "capability"
                get(doc["model"]["capabilities"], request["profile"], nothing) === true || reject("UNSUPPORTED_PROFILE", "/profile")
            end
        end
        Dict("outcome" => "accept")
    catch error
        error isa Rejection || rethrow()
        Dict("outcome" => "reject", "stage" => stage, "category" => error.category, "document" => document, "path" => error.path)
    end
end
end
