"""Check both native producers against the accepted packet and each other."""

import argparse
import hashlib
import json
from decimal import Decimal, localcontext
from itertools import product
from pathlib import Path

from reference import state, validate_catalog

METHODS = {"python": ("DOP853", "Radau"), "julia": ("Tsit5", "Rodas5P")}


def load(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def weighted(weights, values):
    return sum(w * value for w, value in zip(weights, values, strict=True))


def compare(root, exchange, revision):
    packet = root / "spec/community/wire-candidates"
    catalog = load(root / "conformance/community/cases.json")
    validate_catalog(catalog)
    settings = load(root / "conformance/community/feasibility/settings.json")
    producers = {}
    for runtime, methods in METHODS.items():
        peer = "julia" if runtime == "python" else "python"
        expected = {
            f"{case['id']}/{method}/{setting['id']}"
            for case, method, setting in product(
                catalog["cases"], methods, settings["settings"]
            )
        }
        contributions = []
        for label, phase in ((runtime, "produce"), (peer, "read")):
            info = load(exchange / f"{label}-{phase}.json")
            assert (info["runtime"], info["mode"], info["source_revision"]) == (
                label,
                phase,
                revision,
            )
            rows = {row["key"]: row for row in info["rows"]}
            assert set(rows) == expected and len(info["rows"]) == len(expected)
            contributions.append(rows)
        assert contributions[0] == contributions[1]
        producers[runtime] = contributions[0]

    max_ratio = {"python": Decimal(0), "julia": Decimal(0)}
    max_pair = Decimal(0)
    max_drift = Decimal(0)
    samples = balances = pairs = 0
    with localcontext() as ctx:
        ctx.prec = 160
        for case in catalog["cases"]:
            case_id = case["id"]
            ref_initial = state(case_id, Decimal(0))
            repr_initial = [
                Decimal.from_float(float(number)) for number in case["initial"]
            ]
            weights = [*map(Decimal, case["populations"]), Decimal(1), Decimal(0)]
            initial_error = abs(
                weighted(weights, repr_initial) - weighted(weights, ref_initial)
            )
            closed = all(
                case["parameters"][key] == 0
                for key in (
                    "sender_production",
                    "sender_decay",
                    "receiver_decay",
                    "env_decay",
                )
            )
            expected_model = (packet / case_id / "model.jcs").read_bytes()
            expected_identity = (packet / case_id / "identity.jcs").read_bytes()
            for setting in settings["settings"]:
                observed = {name: [] for name in METHODS}
                for runtime, methods in METHODS.items():
                    for method in methods:
                        key = f"{case_id}/{method}/{setting['id']}"
                        directory = exchange / key
                        row = producers[runtime][key]
                        assert (
                            directory / "model.jcs"
                        ).read_bytes() == expected_model, key
                        assert (
                            directory / "identity.jcs"
                        ).read_bytes() == expected_identity, key
                        assert (
                            row["fir_digest"]
                            == hashlib.sha256(expected_identity).hexdigest()
                        )
                        result_path = directory / "result.json"
                        manifest_path = directory / "manifest.json"
                        assert sha(result_path) == row["result_sha256"], key
                        assert sha(manifest_path) == row["manifest_sha256"], key
                        result, manifest = load(result_path), load(manifest_path)
                        assert manifest["backend"]["solver"]["method"] == method
                        assert manifest["output"]["sha256"] == row["result_sha256"]
                        expected_backend = (
                            "python-scipy" if runtime == "python" else "julia-sciml"
                        ) + "-community-ode/0.1.0"
                        assert manifest["backend"]["profile"] == expected_backend
                        assert (
                            result["times"]
                            == manifest["execution"]["time_grid"]
                            == case["times"]
                        )
                        assert manifest["execution"]["rtol"] == setting["rtol"]
                        assert manifest["execution"]["atol"] == setting["atol"]
                        assert (
                            manifest["execution"]["max_step"]
                            == settings["reference_max_step"]
                        )
                        assert (
                            manifest["execution"]["max_nfev"]
                            == settings["max_rhs_calls"]
                        )
                        indices = [
                            result["state_ids"].index(id_)
                            for id_ in catalog["state_ids"]
                        ]
                        trajectory = []
                        for time, values in zip(
                            case["times"], result["state_values"], strict=True
                        ):
                            expected = state(case_id, Decimal(time))
                            bounds = [
                                Decimal("1e-9") + Decimal("1e-8") * abs(x)
                                for x in expected
                            ]
                            mapped = [
                                Decimal.from_float(float(values[i])) for i in indices
                            ]
                            ratio = max(
                                abs(a - b) / limit
                                for a, b, limit in zip(
                                    mapped, expected, bounds, strict=True
                                )
                            )
                            assert ratio <= 1, (key, time, ratio)
                            samples += 1
                            max_ratio[runtime] = max(max_ratio[runtime], ratio)
                            trajectory.append((mapped, bounds))
                            if closed:
                                drift = abs(
                                    weighted(weights, mapped)
                                    - weighted(weights, repr_initial)
                                )
                                ratio = drift / (
                                    weighted(weights, bounds) + initial_error
                                )
                                assert ratio <= 1, (key, time, ratio)
                                max_drift = max(max_drift, ratio)
                                balances += 1
                        observed[runtime].append(trajectory)
                for left, right in product(observed["python"], observed["julia"]):
                    for (a, bounds), (b, _) in zip(left, right, strict=True):
                        # Triangle inequality from the two independently accepted state bounds.
                        ratio = max(
                            abs(x - y) / (2 * limit)
                            for x, y, limit in zip(a, b, bounds, strict=True)
                        )
                        assert ratio <= 1, (case_id, setting["id"], ratio)
                        max_pair = max(max_pair, ratio)
                        pairs += 1
    assert samples == 240 and pairs == 240 and balances == 144
    return {
        "status": "PASS",
        "source_revision": revision,
        "source_inputs_sha256": {
            name: sha(root / name)
            for name in (
                "spec/community/review-manifest.json",
                "conformance/community/cases.json",
                "conformance/community/reference.py",
                "conformance/community/reference.jl",
                "conformance/community/feasibility/settings.json",
                "packages/python/uv.lock",
                "conformance/julia_ode/Manifest.toml",
            )
        },
        "native_runs": sum(len(rows) for rows in producers.values()),
        "peer_readbacks": 80,
        "state_samples": samples,
        "weighted_balance_samples": balances,
        "pairwise_samples": pairs,
        "maximum_state_ratios": {
            runtime: str(value) for runtime, value in max_ratio.items()
        },
        "maximum_balance_ratio": str(max_drift),
        "maximum_pairwise_ratio": str(max_pair),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("exchange", type=Path)
    parser.add_argument("revision")
    args = parser.parse_args()
    result = compare(args.root, args.exchange, args.revision)
    (args.exchange / "comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        "PASS exact FIR parity, peer readback, independent samples and weighted balances"
    )
