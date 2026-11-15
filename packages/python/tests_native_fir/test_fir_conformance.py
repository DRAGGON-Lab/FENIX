"""Approved fixed inputs exercise native FIR parsing, validation and normalization.

No test adapter performs scientific validation. Reference-only stage labels are
not asserted as a native diagnostic API. Input/document identity is preserved.
"""

import hashlib
import json
import struct
import unittest
from pathlib import Path

from jsonschema import Draft7Validator

from fenix.bioir import BioIRValidationError, DesignDocument, ExperimentDocument
from fenix.bioir._json import canonical_bytes, parse_json
from fenix.compiler import compile_experiment
from fenix.fir import FIRDocument, FIRModel, FIRValidationError

ROOT = Path(__file__).resolve().parents[3]


def read(path, checksum=None):
    raw = (ROOT / path).read_bytes()
    if checksum is not None:
        assert hashlib.sha256(raw).hexdigest() == checksum
    return raw


class TestNativeFIR(unittest.TestCase):
    def test_all_207_rejection_cases(self):
        catalog = json.loads(read("conformance/rejections/catalog.json"))
        self.assertEqual(len(catalog["cases"]), 207)
        for case in catalog["cases"]:
            with self.subTest(case=case["id"]):
                document = "primary"
                try:
                    dependencies = {}
                    for key in ("design", "experiment", "previous"):
                        if key in case["inputs"]:
                            document = key
                            item = case["inputs"][key]
                            raw = read(item["path"], item["sha256"])
                            dependencies[key] = (
                                ExperimentDocument.from_json(
                                    raw, designs=(dependencies["design"],)
                                )
                                if key == "experiment"
                                else DesignDocument.from_json(raw)
                            )
                    document = "primary"
                    item = case["inputs"]["primary"]
                    raw = read(item["path"], item["sha256"])
                    op = case["operation"]
                    if op == "parse":
                        parse_json(raw, numeric_policy=case["contract"].lower())
                    elif op == "experiment":
                        ExperimentDocument.from_json(
                            raw, designs=(dependencies["design"],)
                        )
                    elif op in ("design", "revision"):
                        DesignDocument.from_json(
                            raw, previous=dependencies.get("previous")
                        )
                    elif op == "producer":
                        FIRDocument.from_json(
                            raw,
                            design=dependencies["design"],
                            experiment=dependencies["experiment"],
                        )
                    else:
                        result = FIRDocument.from_json(raw)
                        if op == "capability":
                            document = "request"
                            item = case["inputs"]["request"]
                            request = parse_json(
                                read(item["path"], item["sha256"]), numeric_policy="p03"
                            )
                            result.model.require_capability(request["profile"])
                except (BioIRValidationError, FIRValidationError) as error:
                    expected = case["expected"]
                    self.assertEqual(expected["outcome"], "reject")
                    self.assertEqual(
                        (error.category, error.path, document),
                        (expected["category"], expected["path"], expected["document"]),
                    )
                else:
                    self.assertEqual(case["expected"]["outcome"], "accept")

    def test_canonical_catalog(self):
        directory = "conformance/canonicalization/"
        catalog = json.loads(read(directory + "catalog.json"))
        self.assertEqual(len(catalog["cases"]), 84)
        for case in catalog["cases"]:
            with self.subTest(case=case["id"]):
                artifact = case["input"]
                raw = read(directory + artifact["path"], artifact["sha256"])
                if case["stage"] == "contract_only":
                    if case["expected_outcome"] == "reject":
                        with self.assertRaises(
                            (BioIRValidationError, FIRValidationError)
                        ):
                            if case["id"].startswith("fir-"):
                                FIRDocument.from_json(raw)
                            else:
                                parse_json(raw, numeric_policy="p03")
                    else:
                        if case["id"].startswith("fir-"):
                            FIRDocument.from_json(raw)
                        else:
                            parse_json(raw, numeric_policy="p03")
                    continue
                if case["stage"] == "fir_identity":
                    model = FIRDocument.from_json(raw).model
                    expected = case["normalized"]
                    self.assertEqual(
                        model.normalized().to_dict(),
                        parse_json(
                            read(directory + expected["path"], expected["sha256"]),
                            numeric_policy="p03",
                        ),
                    )
                    self.assertEqual(
                        model.normalized().normalized().to_dict(),
                        model.normalized().to_dict(),
                    )
                    expected = case["model_canonical"]
                    self.assertEqual(
                        model.canonical_model_bytes(),
                        read(directory + expected["path"], expected["sha256"]),
                    )
                    output = model.identity_bytes()
                    self.assertEqual(model.digest, case["canonical"]["sha256"])
                    self.assertEqual(
                        FIRModel.from_json(model.canonical_model_bytes()).digest,
                        model.digest,
                    )
                else:
                    if case["expected_outcome"] == "reject":
                        with self.assertRaises(ValueError):
                            value = (
                                struct.unpack(
                                    ">d", bytes.fromhex(case["binary64_bits"])
                                )[0]
                                if case["stage"] == "binary64_jcs"
                                else parse_json(raw, numeric_policy="p03")
                            )
                            canonical_bytes(value)
                        continue
                    value = (
                        struct.unpack(">d", bytes.fromhex(case["binary64_bits"]))[0]
                        if case["stage"] == "binary64_jcs"
                        else parse_json(raw, numeric_policy="p03")
                    )
                    output = canonical_bytes(value)
                expected = case["canonical"]
                self.assertEqual(
                    output, read(directory + expected["path"], expected["sha256"])
                )
                if "canonical_sha256" in case:
                    self.assertEqual(
                        hashlib.sha256(output).hexdigest(), case["canonical_sha256"]
                    )

    def test_compiler_producer_controls(self):
        catalog = json.loads(read("conformance/rejections/catalog.json"))
        count = 0
        for case in catalog["cases"]:
            if (
                case["operation"] != "producer"
                or case["expected"]["outcome"] != "accept"
            ):
                continue
            with self.subTest(case=case["id"]):
                sources = case["inputs"]
                design = DesignDocument.from_json(
                    read(sources["design"]["path"], sources["design"]["sha256"])
                )
                experiment = ExperimentDocument.from_json(
                    read(
                        sources["experiment"]["path"], sources["experiment"]["sha256"]
                    ),
                    designs=(design,),
                )
                expected = FIRDocument.from_json(
                    read(sources["primary"]["path"], sources["primary"]["sha256"]),
                    design=design,
                    experiment=experiment,
                )
                actual = compile_experiment(experiment)
                Draft7Validator(
                    json.loads(read("spec/fir/proposals/fir-m0.schema.json"))
                ).validate(actual.to_dict())
                self.assertEqual(
                    actual.model.normalized().to_dict(),
                    expected.model.normalized().to_dict(),
                )
                self.assertEqual(
                    actual.model.identity_bytes(), expected.model.identity_bytes()
                )
                self.assertEqual(actual.digest, expected.digest)
                actual.validate_sources(design, experiment)
                count += 1
        self.assertEqual(count, 9)
