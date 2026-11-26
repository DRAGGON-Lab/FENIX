"""Candidate study verification must detect plausible corruptions, not just types."""

import copy
import json
import unittest

import compare_study
import numpy as np
import reference


class TestStudyComparison(unittest.TestCase):
    def test_positive_and_corrupted_samples(self):
        reference.catalog()
        case = json.loads((reference.HERE / "cases.json").read_bytes())["cases"][8]
        times = np.arange(5)
        values = np.array(
            [[float(x) for x in reference.state(case["id"], t)] for t in range(5)]
        )
        self.assertEqual(compare_study.compare_samples(case, times, values)[0], 18)
        for kind in (
            "wrong_value",
            "wrong_column",
            "wrong_time",
            "nan",
            "negative",
            "short",
        ):
            changed, grid = values.copy(), times.copy()
            if kind == "wrong_value":
                changed[1, 0] += 0.001
            elif kind == "wrong_column":
                changed[:, [0, 1]] = changed[:, [1, 0]]
            elif kind == "wrong_time":
                grid[1] = 2
            elif kind == "nan":
                changed[1, 0] = np.nan
            elif kind == "negative":
                changed[1, 0] = -1
            else:
                changed = changed[:-1]
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                compare_study.compare_samples(case, grid, changed)

    def test_wrong_source_rate_fails_independent_comparison(self):
        original = json.loads((reference.HERE / "cases.json").read_bytes())["cases"][8]
        changed = {
            k: copy.deepcopy(v)
            for k, v in original.items()
            if k not in {"times", "state_ids"}
        }
        changed["parameters"]["translation"][0] += 1
        times, values, _ = compare_study.study.simulate(
            changed, compare_study.PROTOCOL, "Radau", True, False
        )
        with self.assertRaisesRegex(ValueError, "analytical disagreement"):
            compare_study.compare_samples(original, times, values)


if __name__ == "__main__":
    unittest.main()
