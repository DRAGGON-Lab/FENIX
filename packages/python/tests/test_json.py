"""Native P01 raw-input boundary regressions, independent of reference tools."""

import unittest

from fenix.bioir import BioIRValidationError
from fenix.bioir._decode import decode_envelope
from fenix.bioir._json import canonical_bytes, parse_json


class TestJSON(unittest.TestCase):
    def test_token_failures_have_paths(self):
        cases = [
            (b'{"a/b~":[1,9007199254740992]}', "INTEGER_RANGE", "/a~1b~0/1"),
            (b'{"x":1e400}', "NUMBER_RANGE", "/x"),
            (b'{"x":1e-4000}', "NUMBER_UNDERFLOW", "/x"),
            (b'{"x":1,"\\u0078":2}', "DUPLICATE_KEY", "/x"),
            (b'"\\ud800"', "INVALID_UNICODE", ""),
            (b"\xff", "INVALID_UNICODE", ""),
            (b"NaN", "JSON_SYNTAX", ""),
        ]
        for raw, category, path in cases:
            with self.subTest(raw=raw), self.assertRaises(BioIRValidationError) as got:
                parse_json(raw)
            self.assertEqual(
                (got.exception.category, got.exception.path), (category, path)
            )

    def test_numbers_and_unicode(self):
        self.assertEqual(parse_json("9007199254740992e0"), 9007199254740992.0)
        self.assertEqual(parse_json("0e-99999999999"), 0)
        self.assertEqual(parse_json("5e-324"), 5e-324)
        self.assertEqual(parse_json('"\\ud83d\\ude00"'), "😀")
        self.assertEqual(
            canonical_bytes(parse_json("[-0.0,1e20]")), b"[0,100000000000000000000]"
        )

    def test_required_envelope_members(self):
        for value, path in [({}, "/content"), ({"content": {}}, "/digest")]:
            with self.assertRaises(BioIRValidationError) as got:
                decode_envelope(value, "Design")
            self.assertEqual(
                (got.exception.category, got.exception.path), ("SCHEMA", path)
            )


def _design_content():
    return {
        "kind": "Design",
        "schema_version": "0.1.0",
        "id": "d",
        "revision": 1,
        "compartments": [
            {
                "id": "c",
                "kind": "representative_cell",
                "volume": {"value": 1, "unit": "L"},
            }
        ],
        "species": [
            {
                "id": "s",
                "compartment": "c",
                "ports": [{"id": "amount", "kind": "molecular_count"}],
            }
        ],
        "parameters": [{"id": "a", "unit": "molecule/s"}, {"id": "b", "unit": "1/s"}],
        "functions": [
            {
                "id": "p",
                "kind": "constitutive_production",
                "parameter": "a",
                "target": {"species": "s", "port": "amount"},
            },
            {
                "id": "q",
                "kind": "first_order_decay",
                "parameter": "b",
                "target": {"species": "s", "port": "amount"},
            },
        ],
    }


class TestWireStructure(unittest.TestCase):
    def test_defaults_do_not_repair_missing_wire_fields(self):
        for field in ("kind", "schema_version", "id", "revision", "functions"):
            content = _design_content()
            del content[field]
            with self.assertRaises(BioIRValidationError) as got:
                decode_envelope({"content": content, "digest": "0" * 64}, "Design")
            self.assertEqual(got.exception.path, "/content/" + field)

    def test_metadata_omitted_empty_and_invalid(self):
        envelope = {"content": _design_content(), "digest": "0" * 64}
        self.assertIsNone(decode_envelope(envelope, "Design")[2])
        self.assertEqual(decode_envelope({**envelope, "metadata": {}}, "Design")[2], {})
        for metadata, path in [
            (None, "/metadata"),
            ({"name": None}, "/metadata/name"),
            ({"extra": "x"}, "/metadata/extra"),
        ]:
            with self.assertRaises(BioIRValidationError) as got:
                decode_envelope({**envelope, "metadata": metadata}, "Design")
            self.assertEqual(got.exception.path, path)

    def test_integer_valued_revision_mapping_is_field_local(self):
        from fenix.bioir._decode import decode_design

        content = _design_content()
        content["revision"] = 1.0
        content["compartments"][0]["volume"]["value"] = 9007199254740992.0
        result = decode_design(content)
        self.assertIs(type(result.revision), int)
        self.assertIs(type(result.compartments[0].volume.value), float)
        self.assertEqual(result.compartments[0].volume.value, 9007199254740992.0)
        content["revision"] = 1.5
        with self.assertRaises(BioIRValidationError) as got:
            decode_design(content)
        self.assertEqual(got.exception.path, "/content/revision")

    def test_structure_precedes_reference_resolution(self):
        from fenix.bioir._decode import decode_design

        content = _design_content()
        content["functions"][0]["target"]["port"] = "unknown"
        self.assertEqual(
            decode_envelope({"content": content, "digest": "0" * 64}, "Design")[0],
            content,
        )
        with self.assertRaises(BioIRValidationError) as got:
            decode_design(content)
        self.assertEqual(
            (got.exception.category, got.exception.path),
            ("REFERENCE", "/content/functions/0/target/port"),
        )
