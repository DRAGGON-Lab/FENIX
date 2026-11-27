"""Finite P08 wire decoding and packaged-contract validation; no external resolver."""

from __future__ import annotations

import json
import math
import re
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any, NoReturn

SAFE = 2**53 - 1


class CommunityValidationError(ValueError):
    def __init__(self, category: str, path: str, message: str = "") -> None:
        self.category, self.path = category, path
        super().__init__(f"{category} at {path}: {message}")


def require(ok: object, category: str, path: str) -> None:
    if not ok:
        raise CommunityValidationError(category, path)


def child(path: str, key: object) -> str:
    return path + "/" + str(key).replace("~", "~0").replace("/", "~1")


def encode(value: Any) -> str:
    def check(node: Any) -> None:
        if type(node) is dict:
            require(all(type(k) is str for k in node), "SCHEMA", "")
            for key, item in node.items():
                check(key)
                check(item)
        elif type(node) is list:
            for item in node:
                check(item)
        elif type(node) is str:
            try:
                node.encode("utf-8", errors="strict")
            except UnicodeError as error:
                raise CommunityValidationError("UNICODE", "") from error
        elif type(node) not in (int, float, bool, type(None)):
            raise TypeError("require plain JSON data")
        elif type(node) is float:
            require(math.isfinite(node), "NUMBER_RANGE", "")

    check(value)

    def render(node: Any) -> str:
        if type(node) is int:
            return format(Decimal(node), "f")
        if type(node) is list:
            return "[" + ",".join(render(v) for v in node) + "]"
        if type(node) is dict:
            return (
                "{"
                + ",".join(
                    json.dumps(k, ensure_ascii=False) + ":" + render(v)
                    for k, v in node.items()
                )
                + "}"
            )
        return json.dumps(node, ensure_ascii=False, allow_nan=False)

    return render(value)


class _Token(str):
    pass


class _Pairs(list[tuple[str, Any]]):
    pass


def decode(raw: str | bytes, kind: str = "source") -> Any:
    def invalid(_: str) -> NoReturn:
        raise CommunityValidationError("NUMBER_RANGE", "")

    try:
        text = raw.decode("utf-8", errors="strict") if type(raw) is bytes else raw
        require(type(text) is str and not text.startswith("\ufeff"), "JSON", "")
        parsed = json.loads(
            text,
            parse_int=_Token,
            parse_float=_Token,
            object_pairs_hook=_Pairs,
            parse_constant=invalid,
        )
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise CommunityValidationError("JSON", "") from error

    def visit(node: Any, path: str = "") -> Any:
        exact = kind == "manifest" and (
            path
            in (
                "/execution/max_nfev",
                "/evaluations/nfev",
                "/backend/solver/options/maxiters",
                "/sources/design/revision",
                "/sources/experiment/revision",
            )
            or path.startswith("/backend/evaluations/")
        )
        if exact:
            require(
                isinstance(node, _Token)
                and "." not in node
                and "e" not in node.lower(),
                "INTEGER_TOKEN",
                path,
            )
            return int(Decimal(node))
        if isinstance(node, _Token):
            integral = "." not in node and "e" not in node.lower()
            if kind == "transport" and integral:
                return -0.0 if node == "-0" else int(Decimal(node))
            if kind == "source" and integral:
                require(
                    len(node.lstrip("-")) <= 16 and abs(int(node)) <= SAFE,
                    "SOURCE_INTEGER",
                    "",
                )
                return -0.0 if node == "-0" else int(node)
            try:
                value = float(node)
            except (OverflowError, ValueError) as error:
                raise CommunityValidationError("NUMBER_RANGE", path) from error
            require(
                math.isfinite(value),
                "NUMBER_RANGE",
                path if kind in ("result", "manifest") else "",
            )
            nonzero = any(c in "123456789" for c in node.lower().split("e")[0])
            require(value != 0 or not nonzero, "NUMBER_UNDERFLOW", "")
            return value
        if isinstance(node, _Pairs):
            result = {}
            for key, value in node:
                visit(key)
                require(key not in result, "DUPLICATE_KEY", "")
                result[key] = visit(value, child(path, key))
            return result
        if type(node) is list:
            return [visit(v, child(path, i)) for i, v in enumerate(node)]
        if type(node) is str:
            try:
                node.encode("utf-8", errors="strict")
            except UnicodeError as error:
                raise CommunityValidationError("UNICODE", "") from error
        return node

    return visit(parsed)


def equal(a: Any, b: Any) -> bool:
    if type(a) is bool or type(b) is bool:
        return type(a) is type(b) and a == b
    if type(a) is dict and type(b) is dict:
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if type(a) is list and type(b) is list:
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b, strict=True))
    return bool(a == b)


@lru_cache(maxsize=4)
def contract(name: str) -> dict[str, Any]:
    return dict(
        json.loads(
            (
                Path(__file__).parent / "schemas" / (name + "-m1.schema.json")
            ).read_bytes()
        )
    )


def validate(name: str, value: Any) -> None:
    """Only the closed grammar of four bundled, PI-accepted schemas is supported."""
    root = contract(name)

    def valid(schema: dict[str, Any], node: Any, path: str) -> bool:
        try:
            visit(schema, node, path)
        except CommunityValidationError:
            return False
        return True

    def visit(schema: dict[str, Any], node: Any, path: str) -> None:
        if "$ref" in schema:
            ref = schema["$ref"]
            if not ref.startswith("#/definitions/"):
                raise RuntimeError("external schema resolution is forbidden")
            visit(root["definitions"][ref.split("/")[-1]], node, path)
            return
        if "oneOf" in schema:
            require(
                sum(valid(s, node, path) for s in schema["oneOf"]) == 1, "SCHEMA", path
            )
        for s in schema.get("allOf", []):
            visit(s, node, path)
        if "if" in schema:
            visit(
                schema.get("then" if valid(schema["if"], node, path) else "else", {}),
                node,
                path,
            )
        if "not" in schema:
            require(not valid(schema["not"], node, path), "SCHEMA", path)
        if "const" in schema:
            require(equal(node, schema["const"]), "SCHEMA", path)
        if "enum" in schema:
            require(any(equal(node, x) for x in schema["enum"]), "SCHEMA", path)
        types = schema.get("type")
        if types:
            choices = types if type(types) is list else [types]
            matches = {
                "object": type(node) is dict,
                "array": type(node) is list,
                "string": type(node) is str,
                "boolean": type(node) is bool,
                "null": node is None,
                "number": type(node) in (int, float),
                "integer": type(node) is int
                or type(node) is float
                and node.is_integer(),
            }
            require(any(matches[t] for t in choices), "SCHEMA", path)
        if type(node) is dict:
            for key in schema.get("required", []):
                require(key in node, "SCHEMA", path)
            props = schema.get("properties", {})
            for key, item in node.items():
                require(
                    key in props or schema.get("additionalProperties", True),
                    "SCHEMA",
                    path,
                )
                if key in props:
                    visit(props[key], item, child(path, key))
        if type(node) is list:
            require(
                len(node) >= schema.get("minItems", 0)
                and len(node) <= schema.get("maxItems", math.inf),
                "SCHEMA",
                path,
            )
            if schema.get("uniqueItems"):
                require(
                    not any(equal(a, b) for i, a in enumerate(node) for b in node[:i]),
                    "SCHEMA",
                    path,
                )
            for i, item in enumerate(node):
                visit(schema.get("items", {}), item, child(path, i))
        if type(node) is str:
            require(
                len(node) >= schema.get("minLength", 0)
                and len(node) <= schema.get("maxLength", math.inf),
                "SCHEMA",
                path,
            )
            if "pattern" in schema:
                require(re.search(schema["pattern"], node) is not None, "SCHEMA", path)
        if type(node) in (int, float):
            require(type(node) is int or math.isfinite(node), "NUMBER_RANGE", path)
            for _key, ok in [
                ("minimum", node >= schema.get("minimum", -math.inf)),
                ("maximum", node <= schema.get("maximum", math.inf)),
                ("exclusiveMinimum", node > schema.get("exclusiveMinimum", -math.inf)),
            ]:
                require(ok, "SCHEMA", path)

    visit(root, value, "")
