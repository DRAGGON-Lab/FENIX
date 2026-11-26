"""Seeded, bounded P01/P02/P03 interaction checks. Never writes oracle fixtures."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import struct
import subprocess
import sys
import traceback
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path

from fenix.bioir import BioIRValidationError, DesignDocument, ExperimentDocument
from fenix.compiler import compile_experiment
from fenix.fir import FIRDocument, FIRModel, FIRValidationError

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
# Literal tokens selected from ratified P01/P03 boundary rules. Python's float
# parser is not used to compute the expected JCS or source digest.
TOKENS = (
    "0",
    "-0.0",
    "0e-999999",
    "1",
    "1.0",
    "1e0",
    "0.1",
    "5e-324",
    "2.2250738585072014e-308",
    "9007199254740991",
    "9007199254740992.0",
    "1000000000000000128.0",
    "1e20",
    "1e21",
    "1.7976931348623157e308",
)
VOLUMES = ("1e-15", "2e-15", "5e-324", "1.7976931348623157e308")
COLLECTIONS = (
    "states",
    "parameters",
    "reactions",
    "observables",
    "equations",
    "assumptions",
)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


class Oracle:
    """One offline ECMAScript process; its serializer is checked by fixed P03 CI."""

    def __enter__(self):
        self.process = subprocess.Popen(
            ["node", str(HERE / "oracle.cjs")],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return self

    def canonical(self, raw: str) -> bytes:
        self.process.stdin.write(json.dumps({"raw": raw}) + "\n")
        self.process.stdin.flush()
        response = self.process.stdout.readline()
        if not response:
            raise RuntimeError("independent Node oracle terminated")
        result = json.loads(response)
        if "error" in result:
            raise RuntimeError("independent Node oracle: " + result["error"])
        return result["canonical"].encode("utf-8")

    def __exit__(self, *args):
        self.process.stdin.close()
        self.process.wait(timeout=10)
        self.process.stdout.close()
        self.process.stderr.close()


@dataclass(frozen=True)
class Scenario:
    alpha: int = 0
    beta: int = 0
    initial: int = 0
    volume: int = 0
    mask: int = 0
    observables: int = 0
    revision: int = 1

    @classmethod
    def decode(cls, data):
        if type(data) is not dict or set(data) != {f.name for f in fields(cls)}:
            raise ValueError("unexpected scenario fields")
        if any(type(value) is not int for value in data.values()):
            raise ValueError("scenario coordinates must be integers")
        value = cls(**data)
        if not (
            all(
                0 <= index < len(TOKENS)
                for index in (value.alpha, value.beta, value.initial)
            )
            and 0 <= value.volume < len(VOLUMES)
            and 0 <= value.mask < 256
            and 0 <= value.observables <= 3
            and 1 <= value.revision < 2**53 - 1
        ):
            raise ValueError("scenario coordinate out of range")
        return value


def scenarios(seed: int, count: int):
    rng = random.Random(seed)
    for index in range(count):
        # Cycling guarantees each numeric atom appears in every quantity role;
        # the seed combines it with declaration/transport/source variations.
        yield Scenario(
            alpha=index % len(TOKENS)
            if index < len(TOKENS)
            else rng.randrange(len(TOKENS)),
            beta=(index * 7) % len(TOKENS)
            if index < len(TOKENS)
            else rng.randrange(len(TOKENS)),
            initial=(index * 11) % len(TOKENS)
            if index < len(TOKENS)
            else rng.randrange(len(TOKENS)),
            volume=index % len(VOLUMES),
            mask=rng.randrange(256),
            observables=index % 4,
            revision=(1, 2, 2**53 - 2)[index % 3],
        )


def render(value, spec: Scenario) -> str:
    def ordered(item):
        if isinstance(item, dict):
            keys = list(item)
            if spec.mask & 16:
                keys.reverse()
            return {key: ordered(item[key]) for key in keys}
        if isinstance(item, list):
            return [ordered(child) for child in item]
        return item

    raw = json.dumps(
        ordered(value),
        ensure_ascii=bool(spec.mask & 64),
        indent=2 if spec.mask & 32 else None,
        allow_nan=False,
    )
    for name, token in (
        ("alpha", TOKENS[spec.alpha]),
        ("beta", TOKENS[spec.beta]),
        ("initial", TOKENS[spec.initial]),
        ("volume", VOLUMES[spec.volume]),
    ):
        raw = raw.replace(json.dumps("@" + name + "@"), token)
    return raw


def signed(content, spec, oracle, metadata=None):
    digest = sha(oracle.canonical(render(content, spec)))
    envelope = {"content": content, "digest": digest}
    if metadata is not None:
        envelope["metadata"] = metadata
    return render(envelope, spec)


def fixtures():
    rejection = json.loads((ROOT / "conformance/rejections/catalog.json").read_bytes())
    canonical = json.loads(
        (ROOT / "conformance/canonicalization/catalog.json").read_bytes()
    )
    if rejection["status"] != "APPROVED" or canonical["status"] != "APPROVED":
        raise ValueError("generated checks require approved fixed references")
    source = next(c for c in rejection["cases"] if c["id"] == "p02-display-label-a")
    model = next(c for c in canonical["cases"] if c["id"] == "fir-base")

    def read(record, prefix=ROOT):
        raw = (prefix / record["path"]).read_bytes()
        if sha(raw) != record["sha256"]:
            raise ValueError("fixed fixture digest mismatch: " + record["path"])
        return json.loads(raw)

    return (
        read(source["inputs"]["design"])["content"],
        read(source["inputs"]["experiment"])["content"],
        read(model["normalized"], ROOT / "conformance/canonicalization"),
    )


@dataclass
class Bundle:
    design_content: dict
    experiment_content: dict
    design_raw: str
    experiment_raw: str
    model: dict
    parameter_names: tuple[str, str]
    function_names: tuple[str, str]
    species: str
    port: str
    compartment: str


def materialize(spec, oracle, bases):
    d, e, model = copy.deepcopy(bases)
    renamed = bool(spec.mask & 128)
    # Deliberately misleading names ensure kind, rather than spelling/position,
    # determines production and decay roles.
    names = ("loss_name", "production_name") if renamed else ("alpha", "beta")
    functions = ("loss_fn", "production_fn") if renamed else ("production", "decay")
    species, port, compartment = (
        ("signal", "readout", "host") if renamed else ("x", "amount", "cell")
    )
    d["id"] = "renamed_design" if renamed else d["id"]
    d["revision"] = e["revision"] = spec.revision
    d["compartments"][0]["id"] = compartment
    d["compartments"][0]["volume"]["value"] = "@volume@"
    d["species"][0].update(id=species, compartment=compartment)
    d["species"][0]["ports"][0]["id"] = port
    for index, (parameter, function, assignment) in enumerate(
        zip(d["parameters"], d["functions"], e["parameters"], strict=True)
    ):
        parameter["id"] = function["parameter"] = assignment["parameter"] = names[index]
        function["id"] = functions[index]
        function["target"] = {"species": species, "port": port}
        assignment["quantity"]["value"] = "@alpha@" if index == 0 else "@beta@"
    e["initial_counts"][0].update(species=species)
    e["initial_counts"][0]["quantity"]["value"] = "@initial@"
    observable_ids = ("z", "A", "a")[: spec.observables]
    e["observables"] = [
        {"id": name, "target": {"species": species, "port": port}}
        for name in observable_ids
    ]
    for bit, owner, key in (
        (1, d, "parameters"),
        (2, d, "functions"),
        (4, e, "parameters"),
        (8, e, "observables"),
    ):
        if spec.mask & bit:
            owner[key].reverse()
    metadata = {
        "name": "é/é/😀",
        "description": "generated replay; no biological claim",
    }
    d_raw = signed(d, spec, oracle, metadata)
    d_digest = json.loads(d_raw)["digest"]
    e["design"] = {"id": d["id"], "revision": spec.revision, "digest": d_digest}
    e_raw = signed(e, spec, oracle, metadata)
    model["states"][0]["initial"] = "@initial@"
    for parameter in model["parameters"]:
        parameter["value"] = "@" + parameter["id"] + "@"
    model["observables"] = [
        {"id": name, "state": "x", "unit": "molecule"}
        for name in sorted(observable_ids)
    ]
    return Bundle(
        d, e, d_raw, e_raw, model, names, functions, species, port, compartment
    )


class Failure(AssertionError):
    def __init__(self, property_name, detail, witness=None):
        self.property_name = property_name
        self.detail = detail
        self.witness = witness or {}
        super().__init__(property_name + ": " + detail)


def equal(actual, expected, name, witness=None):
    if actual != expected:
        raise Failure(name, f"expected {expected!r}, received {actual!r}", witness)


def rejected(fn, category, path, name, raw):
    witness = {"raw_hex": raw.hex()} if isinstance(raw, bytes) else {"raw": raw}
    try:
        fn()
    except (BioIRValidationError, FIRValidationError) as error:
        equal((error.category, error.path), (category, path), name, witness)
    else:
        raise Failure(name, f"expected rejection {category} at {path}", witness)


def check_documents(spec, oracle, b, d, e):
    for label, document, content in (
        ("design", d, b.design_content),
        ("experiment", e, b.experiment_content),
    ):
        expected = oracle.canonical(render(content, spec))
        equal(document.canonical_content_bytes(), expected, label + ".independent-jcs")
        equal(document.digest, sha(expected), label + ".independent-digest")
        reload = (
            DesignDocument.from_json(
                document.to_json(), previous=d, expected_digest=d.digest
            )
            if label == "design"
            else ExperimentDocument.from_json(
                document.to_json(), designs=(d,), previous=e, expected_digest=e.digest
            )
        )
        equal(reload.canonical_content_bytes(), expected, label + ".transport-readback")
        annotated = json.loads(document.to_json())
        annotated["metadata"] = {"description": "different é/é/😀"}
        raw = render(annotated, replace(spec, mask=spec.mask ^ 112))
        reloaded = (
            DesignDocument.from_json(raw, previous=d)
            if label == "design"
            else ExperimentDocument.from_json(raw, designs=(d,), previous=e)
        )
        equal(
            reloaded.digest,
            document.digest,
            label + ".metadata-object-order-whitespace",
        )


def check_compiler(spec, oracle, b, d, e):
    # Exact represented bits, including negative zero, must survive source and
    # compiler transport. The expected values come from the original raw tokens.
    fir = compile_experiment(e)
    source_values = {a.parameter: a.quantity.value for a in e.content.parameters}
    parameters = {a["id"]: a["value"] for a in fir.model.to_dict()["parameters"]}
    for role, source_name, index in zip(
        ("alpha", "beta"), b.parameter_names, (spec.alpha, spec.beta), strict=True
    ):
        expected_bits = struct.pack(">d", float(TOKENS[index]))
        equal(
            struct.pack(">d", float(source_values[source_name])),
            expected_bits,
            role + ".source-bits",
        )
        equal(
            struct.pack(">d", parameters[role]), expected_bits, role + ".compiler-bits"
        )
    equal(
        struct.pack(">d", fir.model.to_dict()["states"][0]["initial"]),
        struct.pack(">d", float(TOKENS[spec.initial])),
        "initial.compiler-bits",
    )
    expected_model = oracle.canonical(render(b.model, spec))
    expected_identity = oracle.canonical(
        render(
            {
                "domain": "fenix.fir",
                "canonicalization_version": "0.1.0",
                "model": b.model,
            },
            spec,
        )
    )
    equal(
        fir.model.canonical_model_bytes(), expected_model, "compiler.independent-model"
    )
    equal(
        fir.model.identity_bytes(), expected_identity, "compiler.independent-identity"
    )
    equal(fir.digest, sha(expected_identity), "compiler.independent-digest")
    equal(
        fir.model.normalized().normalized(),
        fir.model.normalized(),
        "fir.normalization-idempotence",
    )
    equal(
        FIRModel.from_json(expected_model).canonical_model_bytes(),
        expected_model,
        "fir.canonical-readback",
    )
    equal(
        FIRDocument.from_json(fir.to_json(), design=d, experiment=e).digest,
        fir.digest,
        "producer.transport-readback",
    )

    p = fir.to_dict()["provenance"]
    equal(p["design_digest"], d.digest, "producer.design-identity")
    equal(p["experiment_digest"], e.digest, "producer.experiment-identity")
    equal(
        p["symbol_map"]["states"],
        [
            {
                "fir_state_id": "x",
                "bioir_species_id": b.species,
                "bioir_port_id": b.port,
                "bioir_compartment_id": b.compartment,
            }
        ],
        "producer.state-map",
    )
    expected_map = [
        {
            "fir_parameter_id": role,
            "bioir_parameter_id": source_name,
            "bioir_function_id": fn,
            "bioir_function_kind": kind,
        }
        for role, source_name, fn, kind in zip(
            ("alpha", "beta"),
            b.parameter_names,
            b.function_names,
            ("constitutive_production", "first_order_decay"),
            strict=True,
        )
    ]
    equal(
        sorted(
            p["symbol_map"]["parameters"], key=lambda item: item["fir_parameter_id"]
        ),
        expected_map,
        "producer.complete-role-map",
    )

    # Reverse each of exactly six declaration collections, separately and together.
    for collection in (*COLLECTIONS, "all"):
        model = json.loads(render(b.model, spec))
        for key in COLLECTIONS if collection == "all" else (collection,):
            model[key].reverse()
        actual = FIRModel.from_json(json.dumps(model))
        equal(
            actual.canonical_model_bytes(), expected_model, "fir.permute-" + collection
        )

    return fir


def check_source_interactions(spec, oracle, bases, b, d, e, fir):
    # Combine source renaming, reversed declarations and different transport.
    alternate = materialize(replace(spec, mask=spec.mask ^ 255), oracle, bases)
    alternate_d = DesignDocument.from_json(alternate.design_raw)
    alternate_e = ExperimentDocument.from_json(
        alternate.experiment_raw, designs=(alternate_d,)
    )
    equal(alternate_d.digest != d.digest, True, "design.renaming-significant")
    equal(
        compile_experiment(alternate_e).digest,
        fir.digest,
        "compiler.renaming-order-invariance",
    )
    for content, field, previous in (
        (b.design_content, "functions", d),
        (b.experiment_content, "parameters", e),
        (b.experiment_content, "observables", e),
    ):
        if len(content[field]) < 2:
            continue
        mutated = copy.deepcopy(content)
        mutated[field].reverse()
        raw = signed(mutated, spec, oracle)
        current = (
            DesignDocument.from_json(raw)
            if previous is d
            else ExperimentDocument.from_json(raw, designs=(d,))
        )
        equal(
            current.digest != previous.digest, True, content["kind"] + ".order-" + field
        )

    # P01 arrays remain scientific content even when P03 produces the same model.
    content = copy.deepcopy(b.design_content)
    content["parameters"].reverse()
    raw = signed(content, spec, oracle)
    changed = DesignDocument.from_json(raw)
    equal(changed.digest != d.digest, True, "design.array-order-significant")
    rejected(
        lambda: DesignDocument.from_json(raw, previous=d),
        "IMMUTABLE_REVISION",
        "/content/revision",
        "design.trusted-predecessor",
        raw,
    )
    rejected(
        lambda: DesignDocument.from_json(raw, expected_digest=d.digest),
        "DIGEST",
        "/digest",
        "design.trusted-digest",
        raw,
    )
    # Revision/source renaming, volume and source declaration order are excluded
    # from FIR mathematical identity for this fixed M0 profile.
    content["revision"] += 1
    raw = signed(content, spec, oracle)
    next_d = DesignDocument.from_json(raw, previous=d)
    rejected(
        lambda: ExperimentDocument.from_json(b.experiment_raw, designs=(next_d,)),
        "DESIGN_REFERENCE",
        "/content/design/revision",
        "experiment.stale-revision",
        b.experiment_raw,
    )
    e_content = copy.deepcopy(b.experiment_content)
    e_content["design"] = {
        "id": next_d.content.id,
        "revision": next_d.content.revision,
        "digest": next_d.digest,
    }
    e_content["revision"] += 1
    raw = signed(e_content, spec, oracle)
    next_e = ExperimentDocument.from_json(raw, designs=(next_d, d), previous=e)
    equal(
        compile_experiment(next_e).digest,
        fir.digest,
        "compiler.revision-order-invariance",
    )
    equal(
        ExperimentDocument.from_json(e.to_json(), designs=(next_d, d)).digest,
        e.digest,
        "experiment.exact-candidate-selection",
    )
    rejected(
        lambda: ExperimentDocument.from_json(e.to_json(), designs=()),
        "DESIGN_REFERENCE",
        "/content/design/id",
        "experiment.missing-design",
        e.to_json(),
    )
    content = copy.deepcopy(b.design_content)
    content["compartments"][0]["volume"]["value"] = 3.0
    wrong_d = DesignDocument.from_json(signed(content, spec, oracle))
    rejected(
        lambda: ExperimentDocument.from_json(e.to_json(), designs=(wrong_d,)),
        "DESIGN_REFERENCE",
        "/content/design/digest",
        "experiment.stale-digest",
        e.to_json(),
    )
    e_content = copy.deepcopy(b.experiment_content)
    e_content["design"]["digest"] = wrong_d.digest
    volume_e = ExperimentDocument.from_json(
        signed(e_content, spec, oracle), designs=(wrong_d,)
    )
    equal(
        compile_experiment(volume_e).digest, fir.digest, "compiler.no-volume-rescaling"
    )

    # A self-consistent changed source is not the trusted original, and a stale
    # Experiment envelope must fail even when no Design context is supplied.
    content = json.loads(e.to_json())
    content["content"]["revision"] += 1
    raw = json.dumps(content)
    rejected(
        lambda: ExperimentDocument.from_json(raw, designs=()),
        "DIGEST",
        "/digest",
        "experiment.digest-before-resolution",
        raw,
    )
    content = copy.deepcopy(b.experiment_content)
    assignment = next(
        a for a in content["parameters"] if a["parameter"] == b.parameter_names[0]
    )
    assignment["quantity"]["value"] = 7.0
    raw = signed(content, spec, oracle)
    changed_e = ExperimentDocument.from_json(raw, designs=(d,))
    equal(changed_e.digest != e.digest, True, "experiment.value-significant")
    rejected(
        lambda: ExperimentDocument.from_json(raw, designs=(d,), previous=e),
        "IMMUTABLE_REVISION",
        "/content/revision",
        "experiment.trusted-predecessor",
        raw,
    )
    rejected(
        lambda: ExperimentDocument.from_json(
            raw, designs=(d,), expected_digest=e.digest
        ),
        "DIGEST",
        "/digest",
        "experiment.trusted-digest",
        raw,
    )
    content = copy.deepcopy(b.experiment_content)
    content["observables"].append(
        {"id": "new_interface", "target": {"species": b.species, "port": b.port}}
    )
    observable_e = ExperimentDocument.from_json(
        signed(content, spec, oracle), designs=(d,)
    )
    equal(
        compile_experiment(observable_e).digest != fir.digest,
        True,
        "compiler.observable-id-significant",
    )
    changed_model = copy.deepcopy(b.model)
    changed_model["parameters"][0]["value"] = 7.0
    equal(
        compile_experiment(changed_e).model.canonical_model_bytes(),
        oracle.canonical(render(changed_model, spec)),
        "compiler.changed-scientific-value",
    )


def check_raw_inputs(spec, oracle, b, d, e):
    # Numeric raw-token validation precedes hashing. Keep every other generated
    # feature, so these are interaction checks rather than isolated primitives.
    for token, category in (
        ("9007199254740992", "INTEGER_RANGE"),
        ("1e4000", "NUMBER_RANGE"),
        ("1e-4000", "NUMBER_UNDERFLOW"),
        ("true", "SCHEMA"),
        ("-1", "SCHEMA"),
    ):
        # Replace only the initial quantity, before placeholder substitution.
        broken = copy.deepcopy(b.experiment_content)
        broken["initial_counts"][0]["quantity"]["value"] = "@bad@"
        raw = render({"content": broken, "digest": e.digest}, spec).replace(
            '"@bad@"', token
        )
        rejected(
            lambda raw=raw: ExperimentDocument.from_json(raw, designs=(d,)),
            category,
            "/content/initial_counts/0/quantity/value",
            "raw.numeric-" + token,
            raw,
        )
    for fragment, category, path in (
        ('"metadata":{"name":"\\ud800"}', "INVALID_UNICODE", "/metadata/name"),
        ('"\\u0064igest":"' + e.digest + '"', "DUPLICATE_KEY", "/digest"),
    ):
        raw = (
            '{"content":'
            + render(b.experiment_content, spec)
            + ',"digest":"'
            + e.digest
            + '",'
            + fragment
            + "}"
        )
        rejected(
            lambda raw=raw: ExperimentDocument.from_json(raw, designs=(d,)),
            category,
            path,
            "raw." + category,
            raw,
        )

    invalid_utf8 = b.experiment_raw.encode("utf-8") + b"\xff"
    rejected(
        lambda: ExperimentDocument.from_json(invalid_utf8, designs=(d,)),
        "INVALID_UNICODE",
        "",
        "raw.invalid-utf8",
        invalid_utf8,
    )

    # P03 intentionally accepts integer tokens that P01 rejects before rounding.
    large_model = copy.deepcopy(b.model)
    large_model["states"][0]["initial"] = "@large@"
    large_raw = render(large_model, spec).replace('"@large@"', "9007199254740993")
    equal(
        FIRModel.from_json(large_raw).canonical_model_bytes(),
        oracle.canonical(large_raw),
        "fir.large-integer-token-policy",
    )


def check_producer(b, d, e, fir):
    # A standalone valid model/provenance shape is not exact producer agreement.
    for key in ("design_digest", "experiment_digest"):
        envelope = fir.to_dict()
        envelope["provenance"][key] = "f" * 64
        equal(
            FIRDocument.from_dict(envelope).digest,
            fir.digest,
            "fir.provenance-excluded",
        )
        rejected(
            lambda envelope=envelope: FIRDocument.from_dict(
                envelope, design=d, experiment=e
            ),
            "SOURCE_DIGEST",
            "/provenance/" + key,
            "producer.stale-" + key,
            json.dumps(envelope),
        )
    envelope = fir.to_dict()
    envelope["provenance"]["symbol_map"]["states"][0]["bioir_species_id"] = (
        "nonexistent"
    )
    equal(FIRDocument.from_dict(envelope).digest, fir.digest, "fir.source-map-excluded")
    rejected(
        lambda: FIRDocument.from_dict(envelope, design=d, experiment=e),
        "REFERENCE",
        "/provenance/symbol_map/states/0/bioir_species_id",
        "producer.wrong-state-map",
        json.dumps(envelope),
    )
    envelope = fir.to_dict()
    entry = envelope["provenance"]["symbol_map"]["parameters"][0]
    entry["bioir_function_id"] = b.function_names[1]
    rejected(
        lambda: FIRDocument.from_dict(envelope, design=d, experiment=e),
        "SOURCE_ROLE",
        "/provenance/symbol_map/parameters/0/bioir_function_id",
        "producer.swapped-role",
        json.dumps(envelope),
    )
    envelope = fir.to_dict()
    envelope["model"]["parameters"][0]["value"] = 7.0
    FIRDocument.from_dict(envelope)  # Valid mathematics can disagree with sources.
    rejected(
        lambda: FIRDocument.from_dict(envelope, design=d, experiment=e),
        "SOURCE_VALUE",
        "/model/parameters/0/value",
        "producer.wrong-value",
        json.dumps(envelope),
    )
    envelope = fir.to_dict()
    envelope["model"]["observables"].append(
        {"id": "invented", "state": "x", "unit": "molecule"}
    )
    FIRDocument.from_dict(envelope)
    rejected(
        lambda: FIRDocument.from_dict(envelope, design=d, experiment=e),
        "SOURCE_OBSERVABLE",
        f"/model/observables/{len(e.content.observables)}/id",
        "producer.invented-observable",
        json.dumps(envelope),
    )
    model = fir.model.to_dict()
    rhs = model["equations"][0]["rhs"]
    rhs["left"], rhs["right"] = rhs["right"], rhs["left"]
    rejected(
        lambda: FIRModel.from_json(json.dumps(model)),
        "TEMPLATE",
        "/model/equations/0/rhs",
        "fir.no-operand-normalization",
        json.dumps(model),
    )


def _verify(spec, oracle, bases):
    b = materialize(spec, oracle, bases)
    d = DesignDocument.from_json(b.design_raw)
    e = ExperimentDocument.from_json(b.experiment_raw, designs=(d,))
    equal(d.metadata.name, "é/é/😀", "design.unicode-preserved")
    equal(e.metadata.name, "é/é/😀", "experiment.unicode-preserved")
    check_documents(spec, oracle, b, d, e)
    fir = check_compiler(spec, oracle, b, d, e)
    check_source_interactions(spec, oracle, bases, b, d, e, fir)
    check_raw_inputs(spec, oracle, b, d, e)
    check_producer(b, d, e, fir)
    return {
        "design_digest": d.digest,
        "experiment_digest": e.digest,
        "fir_digest": fir.digest,
    }


def verify(spec, oracle, bases):
    try:
        return _verify(spec, oracle, bases)
    except (BioIRValidationError, FIRValidationError) as error:
        # Positive generated inputs must not silently escape failure capture.
        raise Failure(
            "unexpected-diagnostic." + error.category + error.path, str(error)
        ) from error
    except Failure:
        raise
    except Exception as error:
        site = traceback.extract_tb(error.__traceback__)[-1]
        raise Failure(
            f"unexpected-exception.{type(error).__name__}@{Path(site.filename).name}:{site.lineno}",
            str(error),
        ) from error


def reduce_failure(spec, property_name, predicate):
    """Coordinate/bit deletion to a 1-minimal scenario; never shrinks expectations."""
    defaults = Scenario()
    changed = True
    while changed:
        changed = False
        for field in fields(spec):
            current = getattr(spec, field.name)
            targets = (
                [current & ~(1 << bit) for bit in range(8) if current & (1 << bit)]
                if field.name == "mask"
                else [getattr(defaults, field.name)]
            )
            for target in targets:
                if target == current:
                    continue
                candidate = replace(spec, **{field.name: target})
                try:
                    predicate(candidate)
                except Failure as error:
                    if error.property_name == property_name:
                        spec = candidate
                        changed = True
                        break
    return spec


def output_directory(path):
    destination = Path(path).resolve()
    if destination.is_relative_to(ROOT) and not destination.is_relative_to(
        ROOT / "artifacts"
    ):
        raise ValueError("output inside the checkout must be under artifacts/")
    destination.mkdir(parents=True, exist_ok=False)
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=5901)
    parser.add_argument("--cases", type=int, default=64)
    parser.add_argument("--replay", type=Path)
    parser.add_argument(
        "--save-examples",
        action="store_true",
        help="save the first 15 passing source/FIR examples",
    )
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    if not 1 <= args.cases <= 10000:
        parser.error("--cases must be between 1 and 10000")
    destination = output_directory(args.output_dir)
    bases = fixtures()
    replay = json.loads(args.replay.read_text()) if args.replay else None
    if replay is not None and (
        type(replay) is not dict
        or replay.get("format") != "fenix.generated-m0-failure/1"
    ):
        parser.error("unsupported replay format")
    if replay is not None:
        if type(replay.get("seed")) is not int:
            parser.error("replay seed must be an integer")
        args.seed = replay["seed"]
    specs = (
        [Scenario.decode(replay["minimized_scenario"])]
        if replay is not None
        else scenarios(args.seed, args.cases)
    )
    report = {
        "format": "fenix.generated-m0/1",
        "status": "RUNNING",
        "seed": args.seed,
        "python": sys.version,
        "node": subprocess.check_output(["node", "--version"], text=True).strip(),
        "sources": {
            str(p.relative_to(ROOT)): sha(p.read_bytes())
            for p in (
                HERE / "run.py",
                HERE / "oracle.cjs",
                ROOT / "conformance/canonicalization/review_p03.cjs",
                ROOT / "conformance/bioir/catalog.json",
                ROOT / "conformance/rejections/catalog.json",
                ROOT / "conformance/canonicalization/catalog.json",
                *sorted((ROOT / "packages/python/src/fenix/bioir").glob("*.py")),
                *sorted((ROOT / "packages/python/src/fenix/fir").glob("*.py")),
                ROOT / "packages/python/src/fenix/compiler.py",
            )
        },
        "cases": [],
    }
    with Oracle() as oracle:
        for index, spec in enumerate(specs):
            try:
                identities = verify(spec, oracle, bases)
            except Failure as error:
                minimal = reduce_failure(
                    spec, error.property_name, lambda s: verify(s, oracle, bases)
                )
                witness, minimized_detail = error.witness, error.detail
                try:
                    verify(minimal, oracle, bases)
                except Failure as reduced:
                    witness = reduced.witness
                    minimized_detail = reduced.detail
                bundle = materialize(minimal, oracle, bases)
                failure = {
                    "format": "fenix.generated-m0-failure/1",
                    "seed": args.seed,
                    "index": index,
                    "property": error.property_name,
                    "detail": error.detail,
                    "minimized_detail": minimized_detail,
                    "original_scenario": asdict(spec),
                    "minimized_scenario": asdict(minimal),
                    "witness": witness,
                }
                (destination / "failure.json").write_text(
                    json.dumps(failure, indent=2) + "\n"
                )
                (destination / "design.json").write_text(bundle.design_raw)
                (destination / "experiment.json").write_text(bundle.experiment_raw)
                (destination / "expected-model.json").write_text(
                    render(bundle.model, minimal)
                )
                report["status"] = "FAIL"
                (destination / "report.json").write_text(
                    json.dumps(report, indent=2) + "\n"
                )
                print(
                    f"FAIL: {error}; replay {destination / 'failure.json'}",
                    file=sys.stderr,
                )
                return 1
            row = {"index": index, "scenario": asdict(spec), **identities}
            if args.save_examples and index < len(TOKENS):
                example = destination / "examples" / f"case-{index:04d}"
                example.mkdir(parents=True)
                bundle = materialize(spec, oracle, bases)
                source = DesignDocument.from_json(bundle.design_raw)
                experiment = ExperimentDocument.from_json(
                    bundle.experiment_raw, designs=(source,)
                )
                observed = compile_experiment(experiment)
                for filename, raw in (
                    ("design.json", bundle.design_raw),
                    ("experiment.json", bundle.experiment_raw),
                    ("fir.json", observed.to_json()),
                    ("expected-model.json", render(bundle.model, spec)),
                ):
                    (example / filename).write_text(raw)
                row["example"] = str(example.relative_to(destination))
            report["cases"].append(row)
    report["status"] = "PASS"
    (destination / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        f"PASS: {len(report['cases'])} bounded generated M0 scenarios; seed={args.seed}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
