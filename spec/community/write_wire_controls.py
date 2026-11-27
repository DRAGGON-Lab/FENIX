"""Additional literal PROPOSED source-identity and empty-observable controls."""

import copy
import hashlib
import json
from pathlib import Path

import rfc8785

HERE = Path(__file__).resolve().parent / "wire-candidates"


def main():
    catalog = json.loads((HERE / "catalog.json").read_bytes())
    if catalog["status"] != "PROPOSED":
        raise ValueError("refuse to regenerate accepted expectations")
    catalog["positive"] = [
        row
        for row in catalog["positive"]
        if row["id"] not in ("renamed", "permuted", "empty-observables", "late-first")
    ]
    base = HERE / "threshold-n1"
    for control in ("renamed", "permuted", "empty-observables", "late-first"):
        docs = {p.name: json.loads(p.read_bytes()) for p in base.glob("*.json")}
        d, e, f = (docs[key + ".json"] for key in ("design", "experiment", "fir"))
        if control == "renamed":
            rename = {
                "sender": "producer",
                "receiver": "sensor",
                "env": "medium",
                "a": "signalX",
                "b": "reportX",
                "out": "sendX",
                "in": "receiveX",
                "density": "senseX",
                "read": "readX",
            }
            d["content"]["id"] = "renamed-design"
            e["content"]["id"] = "renamed-scenario"
            for owner in d["content"]["owners"]:
                owner["id"] = rename[owner["id"]]
                for species in owner["species"]:
                    species["id"] = rename[species["id"]]
                    for port in species["ports"]:
                        port["id"] = rename[port["id"]]
            for edge in d["content"]["connections"]:
                for address in edge.values():
                    for key in address:
                        address[key] = rename[address[key]]
            for key in ("owners", "species"):
                f["provenance"][key] = {
                    k: rename[v] for k, v in f["provenance"][key].items()
                }
        elif control == "permuted":
            d["content"]["owners"].reverse()
            d["content"]["connections"].reverse()
            for owner in d["content"]["owners"]:
                owner["species"].reverse()
                for species in owner["species"]:
                    species["ports"].reverse()
            for key in ("reactions", "equations", "observables"):
                f["model"][key].reverse()
            e["content"]["observables"].reverse()
        elif control == "empty-observables":
            e["content"]["observables"] = []
            f["model"]["observables"] = []
        d["digest"] = hashlib.sha256(rfc8785.dumps(d["content"])).hexdigest()
        e["content"]["design"] = {
            "id": d["content"]["id"],
            "revision": d["content"]["revision"],
            "digest": d["digest"],
        }
        e["digest"] = hashlib.sha256(rfc8785.dumps(e["content"])).hexdigest()
        f["provenance"].update(design_digest=d["digest"], experiment_digest=e["digest"])
        model = copy.deepcopy(f["model"])
        for key, field in (
            ("reactions", "id"),
            ("equations", "state"),
            ("observables", "id"),
        ):
            model[key].sort(key=lambda item: item[field].encode("utf-16-be"))
        identity_bytes = rfc8785.dumps(
            {"domain": "fenix.fir", "canonicalization_version": "0.2.0", "model": model}
        )
        digest = hashlib.sha256(identity_bytes).hexdigest()
        docs["normalized.json"] = model
        for label in ("zero", "analytical"):
            result = docs[label + ".result.json"]
            result["fir_digest"] = digest
            if control == "late-first" and label == "analytical":
                for key in ("times", "state_values", "observable_values"):
                    result[key] = result[key][1:]
            if control == "empty-observables":
                for key in (
                    "observable_ids",
                    "observable_state_ids",
                    "observable_units",
                    "observable_owners",
                    "observable_scopes",
                ):
                    result[key] = []
                result["observable_values"] = [[] for _ in result["times"]]
            raw = (
                json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
            ).encode()
            for language in ("python", "julia"):
                manifest = docs[f"{label}.{language}.manifest.json"]
                manifest["fir"]["digest"] = digest
                manifest["output"]["sha256"] = hashlib.sha256(raw).hexdigest()
                manifest["execution"]["time_grid"] = result["times"]
                if language == "julia":
                    manifest["backend"]["solver"]["options"]["save_start"] = (
                        result["times"][0] == 0
                    )
                for kind, source in (("design", d), ("experiment", e)):
                    manifest["sources"][kind] = {
                        k: source["content"][k]
                        for k in ("schema_version", "id", "revision")
                    }
                    manifest["sources"][kind]["digest"] = source["digest"]
        folder = HERE / control
        folder.mkdir(exist_ok=True)
        for name, value in docs.items():
            (folder / name).write_text(
                json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
            )
        (folder / "model.jcs").write_bytes(rfc8785.dumps(model))
        (folder / "identity.jcs").write_bytes(identity_bytes)
        (folder / "digest.txt").write_text(digest + "\n")
        catalog["positive"].append(
            {
                "id": control,
                "folder": control,
                "reference_case": "threshold-n1",
                "same_fir_as": "threshold-n1"
                if control != "empty-observables"
                else None,
            }
        )
    (HERE / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n")


if __name__ == "__main__":
    main()
