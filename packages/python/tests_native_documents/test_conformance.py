"""Native P01 coverage: original 92 and rejection-suite P01 subset of 97.

Adapters dispatch operations and label supplied inputs; they perform no validation.
Legacy root-only structural paths are coarsened only for original catalog comparison.
"""

import hashlib
import json
import struct
import unittest
from pathlib import Path

from jsonschema import Draft7Validator

from fenix.bioir import BioIRValidationError, DesignDocument, ExperimentDocument
from fenix.bioir._json import canonical_bytes, parse_json

ROOT = Path(__file__).resolve().parents[3]


def read(path, digest=None):
    raw = (ROOT / path).read_bytes()
    if digest is not None:
        assert hashlib.sha256(raw).hexdigest() == digest
    return raw


class TestNativeConformance(unittest.TestCase):
    def test_serialized_envelopes_match_schema(self):
        schema = json.loads(read("spec/bioir/proposals/bioir-m0.schema.json"))
        design = DesignDocument.from_json(
            read("conformance/bioir/inputs/design-valid.input")
        )
        experiment = ExperimentDocument.from_json(
            read("conformance/bioir/inputs/experiment-valid.input"), designs=(design,)
        )
        for document in (design, experiment):
            Draft7Validator(schema).validate(document.to_dict())
            self.assertEqual(json.loads(document.to_json()), document.to_dict())

    def test_original_92(self):
        catalog = json.loads(read("conformance/bioir/catalog.json"))
        self.assertEqual(len(catalog["cases"]), 92)
        for case in catalog["cases"]:
            with self.subTest(case=case["id"]):
                raw = read("conformance/bioir/" + case["input"], case["input_sha256"])
                expected = case["expected"]
                try:
                    op = case["operation"]
                    if op in ("parse", "canonical"):
                        value = parse_json(raw)
                        if "value" in expected:
                            self.assertEqual(value, expected["value"])
                            if isinstance(expected["value"], bool):
                                self.assertIs(type(value), bool)
                        if "binary64_bits" in expected:
                            self.assertEqual(
                                struct.pack(">d", value).hex(),
                                expected["binary64_bits"],
                            )
                        if op == "canonical":
                            self.assertEqual(
                                canonical_bytes(value).decode(),
                                expected["canonical_utf8"],
                            )
                    elif op == "experiment":
                        design = DesignDocument.from_json(
                            read("conformance/bioir/" + case["design"])
                        )
                        ExperimentDocument.from_json(raw, designs=(design,))
                    else:
                        previous = (
                            DesignDocument.from_json(
                                read("conformance/bioir/" + case["previous"])
                            )
                            if op == "revision"
                            else None
                        )
                        DesignDocument.from_json(raw, previous=previous)
                except BioIRValidationError as error:
                    self.assertEqual(expected["outcome"], "reject")
                    self.assertEqual(error.category, expected["category"])
                    if "path" in expected:
                        path = (
                            ""
                            if error.category == "SCHEMA" and expected["path"] == ""
                            else error.path
                        )
                        self.assertEqual(path, expected["path"])
                else:
                    self.assertEqual(expected["outcome"], "accept")

    def test_rejection_catalog_97_p01(self):
        catalog = json.loads(read("conformance/rejections/catalog.json"))
        cases = [c for c in catalog["cases"] if c["contract"] == "P01"]
        self.assertEqual(len(cases), 97)
        self.assertEqual(len(catalog["cases"]) - len(cases), 110)
        for case in cases:
            with self.subTest(case=case["id"]):
                document = "primary"
                try:
                    dependencies = {}
                    for key in ("design", "previous"):
                        if key in case["inputs"]:
                            document = key
                            item = case["inputs"][key]
                            dependencies[key] = DesignDocument.from_json(
                                read(item["path"], item["sha256"])
                            )
                    document = "primary"
                    item = case["inputs"]["primary"]
                    raw = read(item["path"], item["sha256"])
                    if case["operation"] == "parse":
                        parse_json(raw)
                    elif case["operation"] == "experiment":
                        ExperimentDocument.from_json(
                            raw, designs=(dependencies["design"],)
                        )
                    else:
                        DesignDocument.from_json(
                            raw, previous=dependencies.get("previous")
                        )
                except BioIRValidationError as error:
                    expected = case["expected"]
                    self.assertEqual(expected["outcome"], "reject")
                    self.assertEqual(
                        (error.category, error.path, document),
                        (expected["category"], expected["path"], expected["document"]),
                    )
                else:
                    self.assertEqual(case["expected"]["outcome"], "accept")
