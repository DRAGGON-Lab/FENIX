"""Committed identity behavior; uses only installed runtime dependencies."""

import dataclasses
import json
import unittest
from typing import Any

from test_bioir import design, experiment

from fenix.bioir import (
    BioIRValidationError,
    DesignDocument,
    ExperimentDocument,
    Metadata,
    ParameterAssignment,
    Quantity,
)


def pair() -> tuple[DesignDocument, ExperimentDocument]:
    d = DesignDocument(content=design())
    e = ExperimentDocument(content=experiment(design=d.reference), source_design=d)
    return d, e


class TestDocuments(unittest.TestCase):
    def error(
        self, category: str, path: str, fn: Any, *args: Any, **kwargs: Any
    ) -> None:
        with self.assertRaises(BioIRValidationError) as caught:
            fn(*args, **kwargs)
        self.assertEqual(
            (caught.exception.category, caught.exception.path), (category, path)
        )

    def test_verified_pair_and_transport(self) -> None:
        d, e = pair()
        self.assertEqual(d.reference.digest, d.digest)
        for document in (d, e):
            loaded = (
                DesignDocument.from_json(
                    document.to_json(), expected_digest=document.digest
                )
                if document is d
                else ExperimentDocument.from_json(
                    document.to_json().encode(),
                    designs=(d,),
                    expected_digest=document.digest,
                )
            )
            self.assertEqual(loaded.to_dict(), document.to_dict())
            self.assertEqual(
                loaded.canonical_content_bytes(), document.canonical_content_bytes()
            )
            self.assertNotIn("source_design", document.to_dict())
        self.assertEqual(e.source_design, d)

    def test_wrong_design_digest_rejected(self) -> None:
        d, e = pair()
        self.error(
            "DESIGN_REFERENCE",
            "/content/design/digest",
            ExperimentDocument,
            content=experiment(),
            source_design=d,
        )
        mutated = json.loads(e.to_json())
        mutated["content"]["design"]["digest"] = "f" * 64
        # Stale Experiment envelope must fail before reference resolution.
        self.error(
            "DIGEST",
            "/digest",
            ExperimentDocument.from_json,
            json.dumps(mutated),
            designs=(),
        )

    def test_expected_and_stale_digests(self) -> None:
        d, _ = pair()
        self.error(
            "DIGEST",
            "/digest",
            DesignDocument.from_json,
            d.to_json(),
            expected_digest="f" * 64,
        )
        raw = json.loads(d.to_json())
        raw["content"]["revision"] = 2
        self.error("DIGEST", "/digest", DesignDocument.from_json, json.dumps(raw))

    def test_missing_stale_and_multiple_designs(self) -> None:
        d, e = pair()
        self.error(
            "DESIGN_REFERENCE",
            "/content/design/id",
            ExperimentDocument.from_json,
            e.to_json(),
            designs=(),
        )
        newer = d.replace_content(dataclasses.replace(d.content, revision=2))
        self.error(
            "DESIGN_REFERENCE",
            "/content/design/revision",
            ExperimentDocument.from_json,
            e.to_json(),
            designs=(newer,),
        )
        changed = dataclasses.replace(
            d.content,
            compartments=(
                dataclasses.replace(
                    d.content.compartments[0], volume=Quantity(value=2e-15, unit="L")
                ),
            ),
        )
        replacement = DesignDocument(content=changed)
        self.error(
            "DESIGN_REFERENCE",
            "/content/design/digest",
            ExperimentDocument.from_json,
            e.to_json(),
            designs=(replacement,),
        )
        self.assertEqual(
            ExperimentDocument.from_json(e.to_json(), designs=(newer, d)).source_design,
            d,
        )

    def test_explicit_revision_replacement(self) -> None:
        d, e = pair()
        changed = dataclasses.replace(
            d.content,
            compartments=(
                dataclasses.replace(
                    d.content.compartments[0], volume=Quantity(value=2e-15, unit="L")
                ),
            ),
        )
        self.error(
            "IMMUTABLE_REVISION", "/content/revision", d.replace_content, changed
        )
        next_d = d.replace_content(dataclasses.replace(changed, revision=2))
        self.assertNotEqual(next_d.digest, d.digest)
        self.assertEqual(d.content.revision, 1)
        self.error(
            "REFERENCE",
            "/content/id",
            d.replace_content,
            dataclasses.replace(d.content, id="other", revision=2),
        )
        self.error(
            "IMMUTABLE_REVISION",
            "/content/revision",
            DesignDocument.from_json,
            DesignDocument(content=changed).to_json(),
            previous=d,
        )
        self.assertEqual(DesignDocument.from_json(next_d.to_json(), previous=d), next_d)
        next_content = dataclasses.replace(
            e.content, revision=2, source_design=d.content
        )
        self.assertEqual(e.replace_content(next_content).content.revision, 2)

    def test_revalidates_content_against_actual_design(self) -> None:
        d, e = pair()
        alternate = dataclasses.replace(
            d.content,
            parameters=(
                dataclasses.replace(d.content.parameters[0], unit="1/s"),
                dataclasses.replace(d.content.parameters[1], unit="molecule/s"),
            ),
            functions=(
                dataclasses.replace(d.content.functions[0], parameter="beta"),
                dataclasses.replace(d.content.functions[1], parameter="alpha"),
            ),
        )
        # The uncommitted builder accepts the same ID/revision and this local
        # context. Committing must check against the actual referenced Design.
        content = dataclasses.replace(
            e.content,
            source_design=alternate,
            parameters=(
                ParameterAssignment(
                    parameter="alpha", quantity=Quantity(value=1, unit="1/s")
                ),
                ParameterAssignment(
                    parameter="beta", quantity=Quantity(value=1, unit="molecule/s")
                ),
            ),
        )
        self.error(
            "UNIT",
            "/content/parameters/0/quantity/unit",
            ExperimentDocument,
            content=content,
            source_design=d,
        )

    def test_experiment_replacement_and_previous(self) -> None:
        d, e = pair()
        newer = d.replace_content(dataclasses.replace(d.content, revision=2))
        content = dataclasses.replace(
            e.content, revision=2, design=newer.reference, source_design=newer.content
        )
        self.error(
            "DESIGN_REFERENCE", "/content/design/revision", e.replace_content, content
        )
        next_e = e.replace_content(content, source_design=newer)
        loaded = ExperimentDocument.from_json(
            next_e.to_json(), designs=(newer,), previous=e
        )
        self.assertEqual(loaded.digest, next_e.digest)
        self.assertEqual(e.content.revision, 1)
        self.error(
            "IMMUTABLE_REVISION",
            "/content/revision",
            next_e.replace_content,
            e.content,
            source_design=d,
        )
        self.error(
            "IMMUTABLE_REVISION",
            "/content/revision",
            ExperimentDocument.from_json,
            e.to_json(),
            designs=(d,),
            previous=next_e,
        )

    def test_metadata_is_separate_and_frozen(self) -> None:
        d, _ = pair()
        empty = d.with_metadata(Metadata())
        annotated = d.with_metadata(Metadata(name="é😀", description="provenance"))
        self.assertNotIn("metadata", d.to_dict())
        self.assertEqual(empty.to_dict()["metadata"], {})
        self.assertEqual(d.digest, annotated.digest)
        self.assertEqual(
            d.canonical_content_bytes(), annotated.canonical_content_bytes()
        )
        self.assertEqual(
            DesignDocument.from_json(annotated.to_json()).metadata, annotated.metadata
        )
        self.assertEqual(DesignDocument.from_json(empty.to_json(), previous=d), empty)
        output = annotated.to_dict()
        output["metadata"]["name"] = "changed"
        self.assertEqual(annotated.metadata.name, "é😀")
        for value, field in ((d, "digest"), (annotated.metadata, "name")):
            with self.assertRaises(dataclasses.FrozenInstanceError):
                setattr(value, field, "changed")
            self.assertFalse(hasattr(value, "__dict__"))
        self.error("INVALID_UNICODE", "/name", Metadata, name="\ud800")
        raw = d.to_dict()
        raw["metadata"] = None
        self.error("SCHEMA", "/metadata", DesignDocument.from_json, json.dumps(raw))

    def test_large_float_transport_and_canonical_distinction(self) -> None:
        d, e = pair()
        content = dataclasses.replace(
            e.content,
            source_design=d.content,
            parameters=(
                ParameterAssignment(
                    parameter="alpha",
                    quantity=Quantity(value=9007199254740992.0, unit="molecule/s"),
                ),
                e.content.parameters[1],
            ),
        )
        large = ExperimentDocument(content=content, source_design=d)
        self.assertIn(b"9007199254740992", large.canonical_content_bytes())
        self.assertIn("9007199254740992.0", large.to_json())
        self.assertEqual(
            ExperimentDocument.from_json(large.to_json(), designs=(d,)).digest,
            large.digest,
        )
        canonical_envelope = large.to_json().replace(
            "9007199254740992.0", "9007199254740992"
        )
        self.error(
            "INTEGER_RANGE",
            "/content/parameters/0/quantity/value",
            ExperimentDocument.from_json,
            canonical_envelope,
            designs=(d,),
        )

    def test_programmatic_types_and_binding(self) -> None:
        d, e = pair()
        self.error("SCHEMA", "/content", DesignDocument, content={})
        self.error(
            "SCHEMA", "/metadata", DesignDocument, content=d.content, metadata={}
        )
        self.error(
            "SCHEMA",
            "/source_design",
            ExperimentDocument,
            content=e.content,
            source_design=d.content,
        )
        self.error(
            "SCHEMA", "/designs", ExperimentDocument.from_json, e.to_json(), designs=[d]
        )
        with self.assertRaises(TypeError):
            DesignDocument(content=d.content, digest=d.digest)


if __name__ == "__main__":
    unittest.main()
