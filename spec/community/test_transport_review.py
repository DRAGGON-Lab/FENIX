"""Independent representation witnesses; no candidate writer expectations."""

import copy
import hashlib
import json
import struct
import unittest
from pathlib import Path

import review_wire as review
import wire_contract as wire

HERE = Path(__file__).resolve().parent


class TransportReview(unittest.TestCase):
    def test_literal_vectors(self):
        vectors = json.loads(
            (HERE / "wire-candidates/transport-vectors.json").read_bytes()
        )
        for row in vectors:
            with self.subTest(row=row["id"]):
                decode = (
                    wire.decode_result
                    if row["kind"] == "result"
                    else wire.decode_manifest
                )
                if "category" in row:
                    with self.assertRaises(wire.Rejection) as caught:
                        decode(row["raw"])
                    self.assertEqual(
                        (caught.exception.category, caught.exception.path),
                        (row["category"], row["error_path"]),
                    )
                    continue
                value = decode(row["raw"])
                for key in row["path"]:
                    value = value[key]
                if "bits" in row:
                    self.assertIs(type(value), float)
                    self.assertEqual(struct.pack(">d", value).hex(), row["bits"])
                else:
                    self.assertIsInstance(value, int)
                    self.assertEqual(str(value), row["decimal"])

    def record(self, times, other):
        folder = review.FIXTURES / "threshold-n1"
        d, e, f = review.load(folder)
        label = "zero" if len(times) == 1 else "analytical"
        result = json.loads((folder / (label + ".result.json")).read_bytes())
        manifest = json.loads((folder / (label + ".python.manifest.json")).read_bytes())
        result["times"] = times
        manifest["execution"]["time_grid"] = other
        raw = json.dumps(result).encode()
        manifest["output"]["sha256"] = hashlib.sha256(raw).hexdigest()
        return wire.result_record(
            d,
            e,
            f,
            wire.decode_result(raw),
            wire.decode_manifest(json.dumps(manifest)),
            raw,
        )

    def test_collapsed_and_signed_grid_rejections(self):
        vectors = json.loads((HERE / "wire-candidates/grid-vectors.json").read_bytes())
        for row in vectors:
            if row["accepted"]:
                self.record(row["times"], row["manifest"])
            else:
                with self.assertRaises(wire.Rejection) as caught:
                    self.record(row["times"], row["manifest"])
                self.assertEqual(caught.exception.category, "GRID")

    def test_fingerprint_coverage(self):
        root = HERE.parents[1]
        manifest = json.loads((HERE / "review-manifest.json").read_bytes())
        for missing in (None, next(iter(manifest["sha256"]))):
            bad = copy.deepcopy(manifest)
            if missing is None:
                bad["sha256"] = {}
            else:
                del bad["sha256"][missing]
            with self.assertRaises(AssertionError):
                review.validate_fingerprints(root, bad)
        bad = copy.deepcopy(manifest)
        bad["sha256"]["unlisted-file"] = "0" * 64
        with self.assertRaises(AssertionError):
            review.validate_fingerprints(root, bad)
        bad = copy.deepcopy(manifest)
        bad["sha256"][next(iter(bad["sha256"]))] = "0" * 64
        with self.assertRaises(AssertionError):
            review.validate_fingerprints(root, bad)


if __name__ == "__main__":
    unittest.main()
