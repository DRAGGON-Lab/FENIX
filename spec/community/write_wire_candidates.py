"""Write PROPOSED literal review candidates. Never run against accepted fixtures.

Construction is not independent certification: wire_contract.py checks binding
rules, existing Decimal/BigFloat laws supply samples, and identity_audit.cjs
independently checks normalized objects and ECMAScript JCS bytes.
"""

import copy
import hashlib
import json
import sys
from decimal import Decimal, localcontext
from pathlib import Path

import rfc8785

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "conformance/community"))
import reference

OUT = HERE / "wire-candidates"
STATES = ["env.signal", "receiver.reporter", "receiver.signal", "sender.signal"]
OWNER = ["env", "receiver", "receiver", "sender"]
SCOPE = [
    "environment_total",
    "representative_cell",
    "representative_cell",
    "representative_cell",
]


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )


def envelope(content):
    return {
        "content": content,
        "digest": hashlib.sha256(rfc8785.dumps(content)).hexdigest(),
    }


def schemas():
    result = read(ROOT / "spec/results/proposals/ode-result-m0.schema.json")
    result.update(
        {
            "$id": "urn:fenix:proposed:p08:ode-result-m1",
            "title": "PROPOSED P08 scoped ODE result 0.2.0",
            "$comment": "Finite M1 structure only; correspondence/raw transport checks are separate.",
        }
    )
    props = result["properties"]
    props["schema_version"] = {"const": "0.2.0"}
    props["state_ids"] = {"const": STATES}
    props["state_units"] = {"const": ["molecule"] * 4}
    props["state_values"]["items"] = {
        "type": "array",
        "items": {"type": "number", "minimum": 0},
        "minItems": 4,
        "maxItems": 4,
    }
    props["observable_state_ids"]["items"] = {"enum": STATES}
    # Scope is checked by canonical ID, not by declaration position alone.
    for key, values, size in (
        ("state_owners", OWNER, 4),
        ("state_scopes", SCOPE, 4),
        ("observable_owners", OWNER, None),
        ("observable_scopes", SCOPE, None),
    ):
        props[key] = {"type": "array", "items": {"enum": sorted(set(values))}}
        if size:
            props[key].update(minItems=size, maxItems=size)
        result["required"].append(key)
    write(HERE / "ode-result-m1.schema.json", result)
    manifest = read(
        ROOT / "spec/oscillators/schemas/run-manifest-oscillator.schema.json"
    )
    text = json.dumps(manifest).replace("oscillator-ode", "community-ode")
    manifest = json.loads(text)
    manifest.update(
        {
            "$id": "urn:fenix:proposed:p08:run-manifest-m1",
            "title": "PROPOSED P08 community run manifest 0.2.0",
        }
    )
    manifest["properties"]["fir"]["properties"]["schema_version"] = {"const": "0.2.0"}
    manifest["definitions"]["source"]["properties"]["schema_version"] = {
        "const": "0.2.0"
    }
    for key in ("started_at_utc", "finished_at_utc"):
        manifest["properties"]["timing"]["properties"][key]["pattern"] = (
            r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z$"
        )
    write(HERE / "run-manifest-m1.schema.json", manifest)


def candidates():
    base_d, base_e, base_f = (
        read(HERE / "examples" / (kind + ".json"))
        for kind in ("design", "experiment", "fir")
    )
    data = reference.catalog()
    reference.validate_catalog(data)
    catalog = {
        "status": "PROPOSED",
        "base_revision": "61395717984a9f7a5000eadb0ce37bb6b0b1a5f3",
        "positive": [],
        "rejections": [],
        "raw_numbers": [],
    }
    for case in data["cases"]:
        d = copy.deepcopy(base_d)
        d["content"]["id"] = "community-" + case["id"]
        d = envelope(d["content"])
        e = copy.deepcopy(base_e["content"])
        e.update(
            id=case["id"],
            design={"id": d["content"]["id"], "revision": 1, "digest": d["digest"]},
        )
        e["populations"] = dict(
            zip(("sender", "receiver"), case["populations"], strict=True)
        )
        e["initial_counts"] = {
            k: {"value": v, "unit": "molecule"}
            for k, v in zip(data["state_ids"], case["initial"], strict=True)
        }
        e["parameters"] = {
            k: {"value": v, "unit": data["parameter_units"][k]}
            for k, v in case["parameters"].items()
        }
        # Observe both scopes; canonical declaration order differs from reference order.
        e["observables"] = [
            {"id": "reporter", "state": "receiver.reporter"},
            {"id": "external", "state": "env.signal"},
        ]
        e = envelope(e)
        f = copy.deepcopy(base_f)
        for key in ("parameters", "initial_counts", "populations", "observables"):
            f["model"][key] = copy.deepcopy(e["content"][key])
        f["provenance"].update(design_digest=d["digest"], experiment_digest=e["digest"])
        folder = OUT / case["id"]
        for kind, value in (("design", d), ("experiment", e), ("fir", f)):
            write(folder / (kind + ".json"), value)
        # Candidate bytes constructed here, independently rechecked in Node.
        model = copy.deepcopy(f["model"])
        for key, field in (
            ("reactions", "id"),
            ("equations", "state"),
            ("observables", "id"),
        ):
            model[key].sort(key=lambda x: x[field].encode("utf-16-be"))
        model_bytes = rfc8785.dumps(model)
        identity_bytes = rfc8785.dumps(
            {"domain": "fenix.fir", "canonicalization_version": "0.2.0", "model": model}
        )
        fir_digest = hashlib.sha256(identity_bytes).hexdigest()
        write(folder / "normalized.json", model)
        (folder / "model.jcs").write_bytes(model_bytes)
        (folder / "identity.jcs").write_bytes(identity_bytes)
        (folder / "digest.txt").write_text(fir_digest + "\n")
        for zero in (True, False):
            times = [0] if zero else case["times"]
            with localcontext() as ctx:
                ctx.prec = 160
                matrix = [
                    [
                        float(
                            reference.state(case["id"], Decimal(t))[
                                data["state_ids"].index(k)
                            ]
                        )
                        for k in STATES
                    ]
                    for t in times
                ]
            r = {
                "kind": "ODEResult",
                "schema_version": "0.2.0",
                "fir_digest": fir_digest,
                "time_unit": "s",
                "times": times,
                "state_ids": STATES,
                "state_units": ["molecule"] * 4,
                "state_values": matrix,
                "state_owners": OWNER,
                "state_scopes": SCOPE,
                "observable_ids": ["external", "reporter"],
                "observable_state_ids": ["env.signal", "receiver.reporter"],
                "observable_units": ["molecule"] * 2,
                "observable_owners": ["env", "receiver"],
                "observable_scopes": ["environment_total", "representative_cell"],
                "observable_values": [[row[0], row[1]] for row in matrix],
            }
            label = "zero" if zero else "analytical"
            write(folder / (label + ".result.json"), r)
            raw = (folder / (label + ".result.json")).read_bytes()
            for language in ("python", "julia"):
                m = read(
                    ROOT
                    / f"spec/oscillators/examples/single-cell/zero-grid.{language}.manifest.json"
                )
                m["fir"].update(schema_version="0.2.0", digest=fir_digest)
                for kind, source in (("design", d), ("experiment", e)):
                    m["sources"][kind] = {
                        k: source["content"][k]
                        for k in ("schema_version", "id", "revision")
                    }
                    m["sources"][kind]["digest"] = source["digest"]
                m["execution"].update(
                    time_grid=times, rtol=1e-9, atol=1e-11, max_step=1.0
                )
                m["output"]["sha256"] = hashlib.sha256(raw).hexdigest()
                m["integration"] = "skipped_zero_grid" if zero else "performed"
                m["evaluations"]["nfev"] = 0 if zero else 1
                m["producer"]["name"] = "P08-analytical-illustration-not-a-native-run"
                m["backend"]["profile"] = m["backend"]["profile"].replace(
                    "oscillator", "community"
                )
                if language == "julia":
                    m["backend"]["solver"]["options"]["maxiters"] = 9223372036854775807
                write(folder / f"{label}.{language}.manifest.json", m)
        catalog["positive"].append(
            {"id": case["id"], "folder": case["id"], "reference_case": case["id"]}
        )
    write(OUT / "catalog.json", catalog)


if __name__ == "__main__":
    if (OUT / "catalog.json").exists() and read(OUT / "catalog.json")[
        "status"
    ] != "PROPOSED":
        raise ValueError("refuse to regenerate accepted expectations")
    schemas()
    candidates()
