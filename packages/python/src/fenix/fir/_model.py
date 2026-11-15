"""Immutable validated M0 FIR and the P03 mathematical identity boundary."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any

from fenix.bioir import BioIRValidationError
from fenix.bioir._json import canonical_bytes, parse_json

from ._errors import FIRValidationError
from ._validation import validate_model


@dataclass(frozen=True, slots=True)
class _Object(Mapping[str, object]):
    """Read-only object backed entirely by recursively immutable tuple values."""

    entries: tuple[tuple[str, object], ...]

    def __getitem__(self, key: str) -> object:
        for name, value in self.entries:
            if name == key:
                return value
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return (name for name, _ in self.entries)

    def __len__(self) -> int:
        return len(self.entries)


def _freeze(value: Any) -> object:
    if isinstance(value, dict):
        return _Object(tuple((key, _freeze(item)) for key, item in value.items()))
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: object) -> Any:
    if isinstance(value, _Object):
        return {name: _thaw(item) for name, item in value.entries}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def _parse(raw: str | bytes) -> Any:
    try:
        return parse_json(raw, numeric_policy="p03")
    except BioIRValidationError as error:
        raise FIRValidationError(error.category, error.path, str(error)) from error


def _utf16(value: str) -> bytes:
    return value.encode("utf-16-be")


@dataclass(frozen=True, slots=True, init=False)
class FIRModel:
    """Validated M0 mathematics, independent of provenance and execution settings.

    Use from_dict for native finite binary64 inputs or from_json for P03 tokens.
    Construction always validates before normalization or identity generation.
    """

    _data: _Object

    def __init__(self) -> None:
        raise TypeError("use FIRModel.from_dict or FIRModel.from_json")

    @classmethod
    def from_dict(cls, raw: object) -> FIRModel:
        model = validate_model(raw)
        frozen = _freeze(model)
        assert isinstance(frozen, _Object)
        result = object.__new__(cls)
        object.__setattr__(result, "_data", frozen)
        return result

    @classmethod
    def from_json(cls, raw: str | bytes) -> FIRModel:
        return cls.from_dict(_parse(raw))

    def to_dict(self) -> dict[str, Any]:
        """Fresh native model data in the original declaration order."""
        result = _thaw(self._data)
        assert isinstance(result, dict)
        return result

    def to_json(self) -> str:
        """Ordinary model transport JSON, preserving declaration order."""
        return json.dumps(self.to_dict(), allow_nan=False)

    def normalized(self) -> FIRModel:
        """Sort exactly the six ratified collections on a fresh validated copy."""
        model = self.to_dict()
        for name in ("states", "parameters", "reactions", "observables"):
            model[name].sort(key=lambda item: _utf16(item["id"]))
        model["equations"].sort(key=lambda item: _utf16(item["state"]))
        model["assumptions"].sort(key=_utf16)
        return FIRModel.from_dict(model)

    def canonical_model_bytes(self) -> bytes:
        """JCS(N(model)); not the digest preimage."""
        return canonical_bytes(self.normalized().to_dict())

    def identity_bytes(self) -> bytes:
        """P03 domain/version identity wrapper containing the normalized model."""
        return canonical_bytes(
            {
                "domain": "fenix.fir",
                "canonicalization_version": "0.1.0",
                "model": self.normalized().to_dict(),
            }
        )

    @property
    def digest(self) -> str:
        """Lowercase SHA-256 over identity_bytes(), excluding provenance."""
        return hashlib.sha256(self.identity_bytes()).hexdigest()

    def require_capability(self, profile: str) -> None:
        if profile != "ode":
            raise FIRValidationError(
                "UNSUPPORTED_PROFILE",
                "/profile",
                "this M0 contract supports only ode requests",
            )
