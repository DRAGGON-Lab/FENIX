"""Independently recompute hosted Julia samples using the Decimal reference laws."""

import argparse
import hashlib
import importlib.util
import json
from decimal import Decimal, localcontext
from pathlib import Path


def audit(root, receipt_path, expected_sha256):
    raw = receipt_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == expected_sha256, "receipt fingerprint differs"
    report = json.loads(raw)
    module_spec = importlib.util.spec_from_file_location(
        "m1_decimal_reference", root / "conformance/community/reference.py"
    )
    reference = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(reference)
    reference.validate_catalog(reference.catalog())
    reference.verify_laws()
    assert report["bounded_reference_matrix"] == "PASS"
    assert report["tail_reference_validation"] == "PASS"
    assert report["reference_state_ids"] == reference.catalog()["state_ids"]
    assert len(report["files_sha256"]) == 6
    for name, expected in report["files_sha256"].items():
        path = root / "conformance/community/feasibility" / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name

    cases = {case["id"]: case for case in reference.catalog()["cases"]}
    expected_runs = {
        (case_id, method, setting)
        for case_id in cases
        for method in ("Tsit5", "Rodas5P")
        for setting in ("baseline", "refined")
    }
    assert len(report["runs"]) == 40
    assert {
        (row["case"], row["method"], row["setting"]) for row in report["runs"]
    } == expected_runs
    max_component = Decimal(0)
    max_balance = Decimal(0)
    balanced = samples = 0
    with localcontext() as context:
        context.prec = 160
        for row in report["runs"]:
            assert row["outcome"] == "SUCCESS"
            case = cases[row["case"]]
            assert row["times"] == [0, 1, 4]
            assert len(row["states"]) == len(row["comparisons"]) == 3
            for time, values, claimed in zip(
                row["times"], row["states"], row["comparisons"], strict=True
            ):
                assert len(values) == 4
                expected = reference.state(row["case"], Decimal(time))
                observed = list(map(Decimal.from_float, values))
                assert all(value.is_finite() and value >= 0 for value in observed)
                bounds = [
                    Decimal("1e-9") + Decimal("1e-8") * abs(value) for value in expected
                ]
                ratios = [
                    abs(actual - target) / bound
                    for actual, target, bound in zip(
                        observed, expected, bounds, strict=True
                    )
                ]
                assert max(ratios) <= 1
                max_component = max(max_component, *ratios)
                samples += 1
                closed = all(
                    case["parameters"][name] == 0
                    for name in (
                        "sender_production",
                        "sender_decay",
                        "receiver_decay",
                        "env_decay",
                    )
                )
                if closed:
                    assert "balance_bound" in claimed
                    weights = list(map(Decimal, [*case["populations"], 1, 0]))
                    represented_initial = [
                        Decimal.from_float(float(value)) for value in case["initial"]
                    ]
                    reference_initial = reference.state(row["case"], Decimal(0))
                    initial_error = abs(
                        sum(
                            weight * (actual - target)
                            for weight, actual, target in zip(
                                weights,
                                represented_initial,
                                reference_initial,
                                strict=True,
                            )
                        )
                    )
                    drift = abs(
                        sum(
                            weight * (actual - initial)
                            for weight, actual, initial in zip(
                                weights, observed, represented_initial, strict=True
                            )
                        )
                    )
                    bound = (
                        sum(
                            weight * limit
                            for weight, limit in zip(weights, bounds, strict=True)
                        )
                        + initial_error
                    )
                    assert drift <= bound
                    max_balance = max(max_balance, drift / bound)
                    balanced += 1
                else:
                    assert "balance_bound" not in claimed

        tails = report["tail_controls"]
        assert len(tails) == 4
        assert {(row["method"], row["setting"]) for row in tails} == {
            (method, setting)
            for method in ("Tsit5", "Rodas5P")
            for setting in ("baseline", "refined")
        }
        for row in tails:
            assert row["outcome"] == "STAGE_DOMAIN"
            assert row["failure_environment"] < 0
            assert row["minimum_environment_stage"] < 0
            assert Decimal(row["analytical_environment_at_stop"]) > 0
            assert row["comparisons"] == []
            assert "states" not in row

    return {
        "outcome": "PASS",
        "input_sha256": digest,
        "source_revision": report["source_revision"],
        "source_files_verified": len(report["files_sha256"]),
        "integrations": len(report["runs"]),
        "samples": samples,
        "closed_balance_samples": balanced,
        "max_component_ratio": str(max_component),
        "max_closed_balance_ratio": str(max_balance),
        "tail_reference_validation": report["tail_reference_validation"],
        "negative_stage_tails": len(tails),
        "local_julia_execution": "NOT RUN",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    arguments = parser.parse_args()
    result = audit(
        arguments.root.resolve(),
        arguments.receipt.resolve(),
        arguments.expected_sha256,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
