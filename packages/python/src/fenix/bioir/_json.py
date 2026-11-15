"""Strict P01 token decoding and direct RFC 8785 serialization."""

from __future__ import annotations

import json
import math
from typing import Any, Never

import rfc8785

from ._content import BioIRValidationError


class _NumberToken(str):
    pass


class _Pairs(list[tuple[str, Any]]):
    pass


def pointer(parent: str, key: str | int) -> str:
    return parent + "/" + str(key).replace("~", "~0").replace("/", "~1")


def _fail(category: str, path: str, message: str) -> Never:
    raise BioIRValidationError(category, path, message)


def _number(token: str, path: str) -> int | float:
    if "." not in token and "e" not in token.lower():
        digits = token.lstrip("-")
        if len(digits) > 16 or (len(digits) == 16 and digits > "9007199254740991"):
            _fail("INTEGER_RANGE", path, "integer token exceeds P01's safe range")
        return int(token)
    value = float(token)
    if not math.isfinite(value):
        _fail("NUMBER_RANGE", path, "number token overflows finite binary64")
    if value == 0 and any(c in "123456789" for c in token.lower().split("e")[0]):
        _fail("NUMBER_UNDERFLOW", path, "nonzero number token rounds to zero")
    return value


def _visit(value: Any, path: str = "") -> Any:
    if isinstance(value, _NumberToken):
        return _number(value, path)
    if isinstance(value, str):
        try:
            value.encode("utf-8", errors="strict")
        except UnicodeEncodeError:
            _fail("INVALID_UNICODE", path, "unpaired Unicode surrogate")
    elif isinstance(value, _Pairs):
        result: dict[str, Any] = {}
        for key, item in value:
            child = pointer(path, key)
            _visit(key, child)
            if key in result:
                _fail("DUPLICATE_KEY", child, "duplicate decoded object member")
            result[key] = _visit(item, child)
        return result
    elif isinstance(value, list):
        return [_visit(item, pointer(path, i)) for i, item in enumerate(value)]
    return value


def _constant(token: str) -> Never:
    _fail("JSON_SYNTAX", "", f"non-JSON numeric constant: {token}")


def parse_json(raw: str | bytes) -> Any:
    """Decode original JSON without discarding duplicate keys or numeric tokens."""
    if type(raw) is bytes:
        try:
            text = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            _fail("INVALID_UNICODE", "", "input is not strict UTF-8")
    elif type(raw) is str:
        text = raw
    else:
        raise TypeError("raw JSON must be a str or bytes value")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_Pairs,
            parse_int=_NumberToken,
            parse_float=_NumberToken,
            parse_constant=_constant,
        )
    except json.JSONDecodeError:
        _fail("JSON_SYNTAX", "", "invalid JSON grammar")
    return _visit(value)


def canonical_bytes(value: Any) -> bytes:
    """Direct JCS bytes; this is not a P01 transport-JSON serializer."""
    return rfc8785.dumps(value)
