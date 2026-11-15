"""Approved P01 content projections, with independently accepted diagnostics."""

import hashlib
import json
import unittest
from pathlib import Path

from adapter import ProjectionError, construct
from jsonschema import Draft7Validator

from fenix.bioir import DesignContent, ExperimentContent

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BIOIR = ROOT / "conformance/bioir"


class TestNativeProjections(unittest.TestCase):
    def test_coverage_partition(self) -> None:
        catalog = json.loads((BIOIR / "catalog.json").read_bytes())
        coverage = json.loads((HERE / "coverage.json").read_bytes())["cases"]
        self.assertEqual(
            [c["id"] for c in coverage], [c["id"] for c in catalog["cases"]]
        )
        self.assertEqual(sum(c["status"] == "PROJECTED" for c in coverage), 29)
        self.assertEqual(sum(c["status"] == "DEFERRED" for c in coverage), 63)
        self.assertTrue(all(c["reason"] for c in coverage))

    def test_approved_projections(self) -> None:
        catalog = json.loads((BIOIR / "catalog.json").read_bytes())
        rejections = json.loads(
            (ROOT / "conformance/rejections/catalog.json").read_bytes()
        )
        diagnostics = {c["id"]: c for c in rejections["cases"]}
        coverage = json.loads((HERE / "coverage.json").read_bytes())["cases"]
        projected = {c["id"] for c in coverage if c["status"] == "PROJECTED"}
        schema = json.loads(
            (ROOT / "spec/bioir/proposals/bioir-m0.schema.json").read_bytes()
        )
        for case in catalog["cases"]:
            if case["id"] not in projected:
                continue
            with self.subTest(case=case["id"]):
                raw = (BIOIR / case["input"]).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), case["input_sha256"])
                document = json.loads(raw)
                context = {}
                if case["operation"] == "experiment":
                    design_raw = (BIOIR / case["design"]).read_bytes()
                    dependency = diagnostics["p01-" + case["id"]]["inputs"]["design"]
                    self.assertEqual(
                        hashlib.sha256(design_raw).hexdigest(), dependency["sha256"]
                    )
                    context["source_design"] = construct(
                        DesignContent, json.loads(design_raw)["content"]
                    )
                cls = (
                    DesignContent
                    if case["operation"] == "design"
                    else ExperimentContent
                )
                try:
                    content = construct(cls, document["content"], **context)
                except ProjectionError as failure:
                    self.assertEqual(case["expected"]["outcome"], "reject")
                    self.assertEqual(
                        failure.error.category, case["expected"]["category"]
                    )
                    detailed = diagnostics["p01-" + case["id"]]["expected"]
                    self.assertEqual(detailed["document"], "primary")
                    self.assertEqual(detailed["category"], failure.error.category)
                    # Root content errors use /content; leaves add their constructor
                    # location (e.g. /content/parameters/0/quantity + /value).
                    self.assertEqual(
                        failure.prefix.removeprefix("/content") + failure.error.path,
                        detailed["path"].removeprefix("/content"),
                    )
                else:
                    self.assertEqual(case["expected"]["outcome"], "accept")
                    output = content.to_dict()
                    self.assertEqual(output, document["content"])
                    self.assertEqual(json.loads(content.to_json()), output)
                    definition = "design" if cls is DesignContent else "experiment"
                    validator = Draft7Validator(
                        {
                            "$ref": "#/definitions/" + definition,
                            "definitions": schema["definitions"],
                        }
                    )
                    validator.validate(output)


if __name__ == "__main__":
    unittest.main()
