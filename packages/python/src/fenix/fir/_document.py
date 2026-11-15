"""Validated FIR envelopes with separate immutable provenance."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from fenix.bioir import DesignDocument, ExperimentDocument

from ._errors import FIRValidationError
from ._model import FIRModel, _freeze, _Object, _parse, _thaw
from ._validation import validate_envelope, validate_labels, validate_sources


@dataclass(frozen=True, slots=True, init=False)
class FIRDocument:
    """Standalone or producer-checked FIR, without a persistence/authenticity claim.

    Supplying both source documents checks exact P02 producer correspondence;
    omitted context checks mathematical and provenance structure only.
    """

    model: FIRModel
    provenance: _Object | None

    def __init__(self) -> None:
        raise TypeError("use FIRDocument.from_dict or FIRDocument.from_json")

    @classmethod
    def from_dict(
        cls,
        raw: object,
        *,
        design: DesignDocument | None = None,
        experiment: ExperimentDocument | None = None,
    ) -> FIRDocument:
        envelope = validate_envelope(raw)
        if (design is None) != (experiment is None):
            raise FIRValidationError(
                "SOURCE_REQUIRED",
                "/provenance",
                "both Design and Experiment contexts are required",
            )
        if design is not None and experiment is not None:
            validate_sources(envelope, design, experiment)
        else:
            validate_labels(envelope)
        model = FIRModel.from_dict(envelope["model"])
        provenance = (
            _freeze(envelope["provenance"]) if "provenance" in envelope else None
        )
        assert provenance is None or isinstance(provenance, _Object)
        result = object.__new__(cls)
        object.__setattr__(result, "model", model)
        object.__setattr__(result, "provenance", provenance)
        return result

    @classmethod
    def from_json(
        cls,
        raw: str | bytes,
        *,
        design: DesignDocument | None = None,
        experiment: ExperimentDocument | None = None,
    ) -> FIRDocument:
        return cls.from_dict(_parse(raw), design=design, experiment=experiment)

    def validate_sources(
        self, design: DesignDocument, experiment: ExperimentDocument
    ) -> None:
        """Check source agreement separately; never infer it from a model digest."""
        validate_sources(self.to_dict(), design, experiment)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"model": self.model.to_dict()}
        if self.provenance is not None:
            result["provenance"] = _thaw(self.provenance)
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), allow_nan=False)

    @property
    def digest(self) -> str:
        return self.model.digest
