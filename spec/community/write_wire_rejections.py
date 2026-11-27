"""Write literal PROPOSED single-defect witnesses, never accepted fixtures.

Expectations below are explicit proposed diagnostic choices for review. This
writer does not call the validator or use its output to choose expectations.
"""

import copy
import hashlib
import json
from pathlib import Path

import rfc8785

HERE = Path(__file__).resolve().parent / "wire-candidates"
BASE = HERE / "threshold-n1"


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def main():
    catalog = json.loads((HERE / "catalog.json").read_bytes())
    if catalog["status"] != "PROPOSED":
        raise ValueError("refuse to regenerate accepted expectations")
    catalog["rejections"] = []
    values = {
        key: json.loads((BASE / name).read_bytes())
        for key, name in (
            ("design", "design.json"),
            ("experiment", "experiment.json"),
            ("fir", "fir.json"),
            ("result", "zero.result.json"),
            ("manifest", "zero.python.manifest.json"),
        )
    }

    def witness(name, target, change, category, path, resign=True):
        value = copy.deepcopy(values[target])
        change(value)
        if target in ("design", "experiment") and resign:
            value["digest"] = hashlib.sha256(
                rfc8785.dumps(value["content"])
            ).hexdigest()
        file = "reject/" + name + ".json"
        write(HERE / file, value)
        row = {
            "id": name,
            "base": "threshold-n1",
            "target": target,
            "file": file,
            "category": category,
            "path": path,
        }
        if target == "result":
            manifest = copy.deepcopy(values["manifest"])
            manifest["output"]["sha256"] = hashlib.sha256(
                (HERE / file).read_bytes()
            ).hexdigest()
            row["manifest"] = "reject/" + name + ".manifest.json"
            write(HERE / row["manifest"], manifest)
        catalog["rejections"].append(row)

    def set_at(path, value):
        def mutate(document):
            for key in path[:-1]:
                document = document[key]
            document[path[-1]] = value

        return mutate

    witness(
        "stale-design-digest",
        "design",
        set_at(["digest"], "0" * 64),
        "SOURCE_DIGEST",
        "/digest",
        False,
    )
    witness(
        "stale-experiment-digest",
        "experiment",
        set_at(["digest"], "0" * 64),
        "SOURCE_DIGEST",
        "/digest",
        False,
    )
    for key, bad in (("id", "other"), ("revision", 2), ("digest", "0" * 64)):
        witness(
            "wrong-design-link-" + key,
            "experiment",
            set_at(["content", "design", key], bad),
            "DESIGN_LINK",
            "/content/design",
        )
    for name, path, value, expected in (
        ("duplicate-owner-id", ["owners", 1, "id"], "sender", "/content/owners"),
        ("duplicate-owner-role", ["owners", 1, "role"], "sender", "/content/owners"),
        (
            "duplicate-species-id",
            ["owners", 1, "species", 1, "id"],
            "a",
            "/content/owners/1/species",
        ),
        (
            "duplicate-species-role",
            ["owners", 1, "species", 1, "role"],
            "signal",
            "/content/owners/1/species",
        ),
        (
            "duplicate-port-id",
            ["owners", 0, "species", 0, "ports", 1, "id"],
            "out",
            "/content/owners/0/species/0/ports",
        ),
    ):
        witness(
            name, "design", set_at(["content", *path], value), "DUPLICATE_ID", expected
        )
    witness(
        "wrong-port-kind",
        "design",
        set_at(["content", "owners", 0, "species", 0, "ports", 0, "kind"], "sensor_in"),
        "PORT_KINDS",
        "/content/owners/0/species/0/ports",
    )
    witness(
        "alias-endpoint",
        "design",
        set_at(["content", "connections", 0, "source", "owner"], "alias"),
        "ENDPOINT",
        "/content/connections/0/source",
    )
    witness(
        "reversed-edge",
        "design",
        set_at(
            ["content", "connections", 0], values["design"]["content"]["connections"][1]
        ),
        "BINDINGS",
        "/content/connections",
    )
    witness(
        "duplicate-observable",
        "experiment",
        lambda d: d["content"]["observables"].append(
            copy.deepcopy(d["content"]["observables"][0])
        ),
        "DUPLICATE_ID",
        "/content/observables",
    )
    for name, path, bad in (
        ("source-version", ["schema_version"], "0.1.0"),
        ("population-zero", ["populations", "sender"], 0),
        ("population-bool", ["populations", "sender"], True),
        ("population-fraction", ["populations", "sender"], 1.5),
        ("negative-count", ["initial_counts", "env.signal", "value"], -1),
        ("count-unit", ["initial_counts", "env.signal", "unit"], "molecule/L"),
        ("threshold-zero", ["parameters", "threshold", "value"], 0),
        ("hill-five", ["parameters", "hill_n", "value"], 5),
        ("hill-bool", ["parameters", "hill_n", "value"], True),
    ):
        witness(
            name, "experiment", set_at(["content", *path], bad), "SCHEMA", "/content"
        )
    for name, path, bad in (
        ("fir-source-population", ["model", "populations", "sender"], 7),
        ("fir-source-rate", ["model", "parameters", "sender_export", "value"], 7),
        (
            "fir-source-initial",
            ["model", "initial_counts", "sender.signal", "value"],
            7,
        ),
        ("fir-source-volume", ["model", "volumes", "sender", "value"], 7),
        (
            "fir-source-observable",
            ["model", "observables", 0, "state"],
            "sender.signal",
        ),
        ("fir-source-owner", ["provenance", "owners", "sender"], "alias"),
        ("fir-source-species", ["provenance", "species", "sender.signal"], "alias"),
        ("fir-stale-design", ["provenance", "design_digest"], "0" * 64),
    ):
        expected = "/" + "/".join(path[:2])
        witness(name, "fir", set_at(path, bad), "SOURCE_CORRESPONDENCE", expected)
    for name, path, bad, expected in (
        (
            "fir-wrong-version",
            ["model", "schema_version"],
            "0.1.0",
            "/model/schema_version",
        ),
        ("fir-ssa", ["model", "capabilities", "ssa"], True, "/model/capabilities"),
        (
            "fir-unweighted-export",
            ["model", "reactions", 0, "stoichiometry", "env.signal"],
            1,
            "/model/reactions/0",
        ),
        (
            "fir-free-expression",
            ["model", "reactions", 0, "flux"],
            {"op": "eval", "value": "attack()"},
            "/model/reactions/0",
        ),
    ):
        witness(name, "fir", set_at(path, bad), "SCHEMA", expected)
    for name, path, bad, category, expected in (
        (
            "result-scope-swap",
            ["state_scopes", 0],
            "representative_cell",
            "SCOPE_ALIGNMENT",
            "/state_scopes",
        ),
        (
            "result-owner-swap",
            ["state_owners", 0],
            "sender",
            "SCOPE_ALIGNMENT",
            "/state_owners",
        ),
        (
            "result-column-order",
            ["state_ids"],
            list(reversed(values["result"]["state_ids"])),
            "SCHEMA",
            "/state_ids",
        ),
        (
            "result-short-row",
            ["state_values", 0],
            [24, 0, 12],
            "SCHEMA",
            "/state_values/0",
        ),
        ("result-missing-row", ["state_values"], [], "SCHEMA", "/state_values"),
        ("result-stale-fir", ["fir_digest"], "0" * 64, "FIR_LINK", "/fir_digest"),
        (
            "result-observable-scope",
            ["observable_scopes", 0],
            "representative_cell",
            "OBSERVABLE_ALIGNMENT",
            "/observable_scopes",
        ),
        (
            "result-observable-owner",
            ["observable_owners", 0],
            "sender",
            "OBSERVABLE_ALIGNMENT",
            "/observable_owners",
        ),
        (
            "result-signed-zero-copy",
            ["observable_values", 0, 1],
            -0.0,
            "OBSERVABLE_COPY",
            "/observable_values/0/1",
        ),
        (
            "result-initial-sender",
            ["state_values", 0, 3],
            5,
            "INITIAL_SAMPLE",
            "/state_values/0",
        ),
    ):
        witness(name, "result", set_at(path, bad), category, expected)
    for name, path, bad, category, expected in (
        (
            "manifest-source",
            ["sources", "experiment", "digest"],
            "0" * 64,
            "SOURCE_LINK",
            "/sources/experiment",
        ),
        ("manifest-fir", ["fir", "digest"], "0" * 64, "FIR_LINK", "/fir/digest"),
        (
            "manifest-result-checksum",
            ["output", "sha256"],
            "0" * 64,
            "RESULT_CHECKSUM",
            "/output/sha256",
        ),
        (
            "manifest-grid",
            ["execution", "time_grid"],
            [1],
            "GRID",
            "/execution/time_grid",
        ),
        (
            "manifest-zero-work",
            ["evaluations", "nfev"],
            1,
            "WORK_COUNT",
            "/evaluations",
        ),
        (
            "manifest-integration",
            ["integration"],
            "performed",
            "INTEGRATION",
            "/integration",
        ),
        (
            "manifest-old-backend",
            ["backend", "profile"],
            "python-scipy-ode/0.1.0",
            "SCHEMA",
            "/backend",
        ),
        (
            "manifest-wrong-jacobian",
            ["backend", "solver", "options", "jacobian"],
            "not_supplied",
            "SCHEMA",
            "/backend",
        ),
        (
            "manifest-float-counter",
            ["evaluations", "nfev"],
            0.5,
            "SCHEMA",
            "/evaluations/nfev",
        ),
        (
            "manifest-integral-float-counter",
            ["evaluations", "nfev"],
            0.0,
            "INTEGER_TOKEN",
            "/evaluations/nfev",
        ),
        (
            "manifest-invalid-calendar",
            ["timing", "started_at_utc"],
            "2026-02-30T12:00:00.000000Z",
            "TIMESTAMP",
            "/timing/started_at_utc",
        ),
    ):
        witness(name, "manifest", set_at(path, bad), category, expected)
    raw_cases = (
        (
            "source-safe-max",
            "source",
            '{"value":9007199254740991}',
            {"value": 9007199254740991},
            None,
        ),
        (
            "source-unsafe-int",
            "source",
            '{"value":9007199254740992}',
            None,
            "SOURCE_INTEGER",
        ),
        (
            "fir-rounding-int",
            "fir",
            '{"value":9007199254740993}',
            {"value": 9007199254740992.0},
            None,
        ),
        (
            "transport-large-int",
            "transport",
            '{"value":9007199254740993}',
            {"value": 9007199254740993},
            None,
        ),
        ("source-subnormal", "source", '{"value":5e-324}', {"value": 5e-324}, None),
        ("underflow", "source", '{"value":1e-400}', None, "NUMBER_UNDERFLOW"),
        ("overflow", "source", '{"value":1e400}', None, "NUMBER_RANGE"),
        ("explicit-zero", "source", '{"value":0e-400}', {"value": 0.0}, None),
        ("negative-zero", "transport", '{"value":-0.0}', {"value": -0.0}, None),
        ("integer-negative-zero", "transport", '{"value":-0}', {"value": -0.0}, None),
        ("duplicate-key", "source", '{"value":1,"value":2}', None, "DUPLICATE_KEY"),
        (
            "escaped-duplicate",
            "source",
            '{"value":1,"\\u0076alue":2}',
            None,
            "DUPLICATE_KEY",
        ),
        ("surrogate", "source", '{"value":"\\ud800"}', None, "UNICODE"),
        ("nan", "source", '{"value":NaN}', None, "NUMBER_RANGE"),
        ("utf8-bom", "source", '\ufeff{"value":1}', None, "JSON"),
        (
            "fractional-population-token",
            "source",
            '{"value":3.0}',
            {"value": 3.0},
            None,
        ),
        ("exponent-population-token", "source", '{"value":3e0}', {"value": 3.0}, None),
    )
    catalog["raw_numbers"] = []
    for name, policy, raw, expected, category in raw_cases:
        file = "raw/" + name + ".json"
        (HERE / file).parent.mkdir(parents=True, exist_ok=True)
        (HERE / file).write_text(raw)
        catalog["raw_numbers"].append(
            {
                "id": name,
                "policy": policy,
                "file": file,
                "value": expected,
                "category": category,
                "path": "",
            }
        )
    write(HERE / "catalog.json", catalog)


if __name__ == "__main__":
    main()
