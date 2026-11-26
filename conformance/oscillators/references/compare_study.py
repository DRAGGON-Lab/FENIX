"""Check the candidate SciPy study against independent analytical P09 cases."""

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import reference
import scipy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import study

PROTOCOL = {
    "horizon_s": 4,
    "sample_step_s": 1,
    "max_nfev": 200000,
    "max_step_s": 0.05,
    "rtol": 1e-10,
    "atol": 1e-11,
    "refined_rtol": 1e-12,
    "refined_atol": 1e-13,
}


def compare_samples(case, times, values):
    reference.require(np.array_equal(times, np.arange(5)), "wrong study grid")
    reference.require(
        values.shape == (5, len(case["initial_counts"])), "wrong study shape"
    )
    reference.require(
        np.all(np.isfinite(values)) and np.all(values >= 0), "invalid study samples"
    )
    worst, comparisons = 0.0, 0
    for time in case["times"]:
        expected = np.array([float(x) for x in reference.state(case["id"], time)])
        error = np.abs(values[time] - expected)
        # Candidate-only comparison threshold; no new native P04 policy.
        bound = 1e-9 + 1e-8 * np.abs(expected)
        reference.require(
            np.all(error <= bound), f"analytical disagreement: {case['id']} t={time}"
        )
        worst = max(worst, float(np.max(error / bound)))
        comparisons += len(expected)
    return comparisons, worst


def report():
    reference.catalog()  # Complete byte pin precedes loading ordinary binary64 inputs.
    cases = json.loads((reference.HERE / "cases.json").read_bytes())["cases"]
    runs = []
    for case in cases:
        model_case = {k: v for k, v in case.items() if k not in {"times", "state_ids"}}
        for method in ("DOP853", "Radau"):
            times, values, work = study.simulate(
                model_case, PROTOCOL, method, True, False
            )
            count, worst = compare_samples(case, times, values)
            runs.append(
                {
                    "case": case["id"],
                    "method": method,
                    "comparisons": count,
                    "max_error_to_candidate_bound": worst,
                    "work": work,
                }
            )
    paths = {
        "reference": reference.__file__,
        "study": study.__file__,
        "comparison": __file__,
    }
    return {
        "status": "PASS_CANDIDATE_STUDY_ONLY",
        "native_fenix": "NOT_RUN_UNSUPPORTED_PROFILE",
        "catalog_sha256": reference.CATALOG_SHA256,
        "source_sha256": {
            name: hashlib.sha256(Path(path).read_bytes()).hexdigest()
            for name, path in paths.items()
        },
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "protocol": PROTOCOL,
        "comparison_bound": "1e-9 + 1e-8 * abs(analytical)",
        "runs": runs,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = report()
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(
        f"PASS: {sum(r['comparisons'] for r in result['runs'])} candidate analytical sample comparisons"
    )
