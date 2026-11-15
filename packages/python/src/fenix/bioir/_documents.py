"""Immutable scientific document identities; no persistence or authenticity claim."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from typing import Any, Self

from ._content import (
    _DIGEST,
    BioIRValidationError,
    DesignContent,
    DesignReference,
    ExperimentContent,
    _Content,
    _require,
    _typed,
)
from ._decode import decode_design, decode_envelope, decode_experiment
from ._json import canonical_bytes, parse_json


@dataclass(frozen=True, slots=True, kw_only=True)
class Metadata:
    """Descriptive envelope fields; None means omitted, never JSON null."""

    name: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        for name in ("name", "description"):
            value = getattr(self, name)
            if value is None:
                continue
            _require(type(value) is str, "/" + name, "expected a string")
            try:
                value.encode("utf-8", errors="strict")
            except UnicodeEncodeError:
                raise BioIRValidationError(
                    "INVALID_UNICODE", "/" + name, "unpaired Unicode surrogate"
                ) from None

    def to_dict(self) -> dict[str, str]:
        return {
            name: value
            for name in ("name", "description")
            if (value := getattr(self, name)) is not None
        }


def _metadata(raw: object) -> Metadata | None:
    if raw is None:
        return None
    # decode_envelope has checked members/types, including explicit JSON null.
    assert isinstance(raw, dict)
    return Metadata(**raw)


def _verify_digest(
    content_bytes: bytes, claimed: str, expected: str | None = None
) -> None:
    actual = hashlib.sha256(content_bytes).hexdigest()
    _require(
        actual == claimed,
        "/digest",
        "digest differs from canonical scientific content",
        "DIGEST",
    )
    if expected is not None:
        _require(
            type(expected) is str and _DIGEST.fullmatch(expected) is not None,
            "/digest",
            "expected_digest must be lowercase hexadecimal SHA-256",
        )
        _require(
            actual == expected,
            "/digest",
            "digest differs from caller's trusted expectation",
            "DIGEST",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class _Document[T: _Content]:
    content: T
    metadata: Metadata | None = None
    digest: str = field(init=False)
    _canonical: bytes = field(init=False, repr=False, compare=False)

    def _finish(self) -> None:
        if self.metadata is not None:
            _require(
                type(self.metadata) is Metadata,
                "/metadata",
                "expected a Metadata value",
            )
        encoded = canonical_bytes(self.content.to_dict())
        object.__setattr__(self, "_canonical", encoded)
        object.__setattr__(self, "digest", hashlib.sha256(encoded).hexdigest())

    def canonical_content_bytes(self) -> bytes:
        """Direct P01 JCS content bytes, excluding digest and metadata."""
        return self._canonical

    def to_dict(self) -> dict[str, Any]:
        """A fresh document envelope; its digest identifies content only."""
        result: dict[str, Any] = {
            "content": self.content.to_dict(),
            "digest": self.digest,
        }
        if self.metadata is not None:
            result["metadata"] = self.metadata.to_dict()
        return result

    def to_json(self) -> str:
        """Ordinary transport JSON that preserves digest on P01 readback.

        Canonical numeric spellings can violate P01's integer-token input bound,
        so canonical_content_bytes is deliberately separate from this transport.
        """
        return json.dumps(self.to_dict(), allow_nan=False)

    def with_metadata(self, metadata: Metadata | None) -> Self:
        """Create a new envelope without changing scientific revision identity."""
        return replace(self, metadata=metadata)


def _check_previous(current: _Document[Any], previous: _Document[Any] | None) -> None:
    if previous is None:
        return
    _require(
        type(previous) is type(current), "/previous", "expected the same document type"
    )
    _require(
        current.content.id == previous.content.id,
        "/content/id",
        "replacement changes logical ID",
        "REFERENCE",
    )
    _require(
        current.digest == previous.digest
        or current.content.revision > previous.content.revision,
        "/content/revision",
        "changed content must advance the trusted previous revision",
        "IMMUTABLE_REVISION",
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class DesignDocument(_Document[DesignContent]):
    """Verified immutable Design identity, independent of archive/trust mechanisms."""

    def __post_init__(self) -> None:
        _typed(self.content, DesignContent, "/content")
        self._finish()

    @property
    def reference(self) -> DesignReference:
        return DesignReference(
            id=self.content.id, revision=self.content.revision, digest=self.digest
        )

    @classmethod
    def from_json(
        cls,
        raw: str | bytes,
        *,
        expected_digest: str | None = None,
        previous: DesignDocument | None = None,
    ) -> DesignDocument:
        content, claimed, metadata = decode_envelope(parse_json(raw), "Design")
        _verify_digest(canonical_bytes(content), claimed, expected_digest)
        result = cls(content=decode_design(content), metadata=_metadata(metadata))
        _check_previous(result, previous)
        return result

    def replace_content(self, content: DesignContent) -> DesignDocument:
        result = DesignDocument(content=content, metadata=self.metadata)
        _check_previous(result, self)
        return result


def _resolve(
    content: dict[str, Any], designs: tuple[DesignDocument, ...]
) -> DesignDocument:
    _require(type(designs) is tuple, "/designs", "expected a tuple of verified Designs")
    for item in designs:
        _require(
            type(item) is DesignDocument,
            "/designs",
            "expected verified DesignDocument values",
        )
    candidates = list(designs)
    for name in ("id", "revision", "digest"):
        candidates = [
            item
            for item in candidates
            if (item.digest if name == "digest" else getattr(item.content, name))
            == content["design"][name]
        ]
        _require(
            bool(candidates),
            "/content/design/" + name,
            "no supplied Design matches the exact reference",
            "DESIGN_REFERENCE",
        )
    return candidates[0]


@dataclass(frozen=True, slots=True, kw_only=True)
class ExperimentDocument(_Document[ExperimentContent]):
    """Verified Experiment and exact, local Design context; neither implies origin."""

    source_design: DesignDocument = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        _typed(self.content, ExperimentContent, "/content")
        _require(
            type(self.source_design) is DesignDocument,
            "/source_design",
            "expected a verified DesignDocument",
        )
        for name in ("id", "revision", "digest"):
            _require(
                getattr(self.content.design, name)
                == getattr(self.source_design.reference, name),
                "/content/design/" + name,
                "reference differs from verified Design",
                "DESIGN_REFERENCE",
            )
        # An uncommitted Experiment may have been checked against a different
        # same-ID/revision Design. Revalidate its assignments and targets here.
        try:
            replace(self.content, source_design=self.source_design.content)
        except BioIRValidationError as error:
            raise BioIRValidationError(
                error.category, "/content" + error.path, str(error)
            ) from error
        self._finish()

    @classmethod
    def from_json(
        cls,
        raw: str | bytes,
        *,
        designs: tuple[DesignDocument, ...],
        expected_digest: str | None = None,
        previous: ExperimentDocument | None = None,
    ) -> ExperimentDocument:
        content, claimed, metadata = decode_envelope(parse_json(raw), "Experiment")
        # Check the Experiment before resolving any cross-document reference.
        _verify_digest(canonical_bytes(content), claimed, expected_digest)
        source = _resolve(content, designs)
        result = cls(
            content=decode_experiment(content, source.content),
            source_design=source,
            metadata=_metadata(metadata),
        )
        _check_previous(result, previous)
        return result

    def replace_content(
        self, content: ExperimentContent, *, source_design: DesignDocument | None = None
    ) -> ExperimentDocument:
        result = ExperimentDocument(
            content=content,
            source_design=self.source_design
            if source_design is None
            else source_design,
            metadata=self.metadata,
        )
        _check_previous(result, self)
        return result
