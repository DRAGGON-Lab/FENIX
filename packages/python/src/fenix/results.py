"""P07 source-linked ODE capture and strict, non-executing verified readback.

Checksums establish artifact consistency against supplied expectations, not
execution authenticity, numerical correctness or biological validity.
"""

from __future__ import annotations

import hashlib
import json
import math
import platform
import re
import struct
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from importlib.metadata import version
from time import monotonic_ns
from typing import Any, NoReturn

from fenix.bioir import ExperimentDocument
from fenix.compiler import compile_experiment
from fenix.execution import ODEExecutionSpec, solve_ode
from fenix.fir import FIRDocument, FIRValidationError

__all__ = [
    "ODEResult",
    "ResultValidationError",
    "RunManifest",
    "RunRecord",
    "run_experiment",
]


class ResultValidationError(ValueError):
    """Invalid artifact with a category and artifact-prefixed JSON Pointer."""

    def __init__(self, category: str, path: str, message: str) -> None:
        self.category = category
        self.path = path
        super().__init__(f"{category} at {path}: {message}")


def _fail(path: str, message: str, category: str = "SCHEMA") -> NoReturn:
    raise ResultValidationError(category, path, message)


def _pointer(path: str, key: str | int) -> str:
    return path + "/" + str(key).replace("~", "~0").replace("/", "~1")


@dataclass(frozen=True, slots=True)
class _Number:
    token: str


@dataclass(frozen=True, slots=True)
class _Pairs:
    entries: list[tuple[str, Any]]


def _text(raw: str | bytes, path: str) -> str:
    try:
        if type(raw) is bytes:
            return raw.decode("utf-8", errors="strict")
        if type(raw) is str:
            raw.encode("utf-8", errors="strict")
            return raw
    except UnicodeError:
        _fail(path, "require strict UTF-8 Unicode scalars", "INVALID_UNICODE")
    _fail(path, "require JSON text or UTF-8 bytes")


def _parse(text: str, path: str) -> Any:
    def invalid_constant(token: str) -> NoReturn:
        _fail(path, "non-JSON numeric literal: " + token, "JSON")

    def visit(value: Any, at: str) -> Any:
        if isinstance(value, _Pairs):
            result: dict[str, Any] = {}
            for key, item in value.entries:
                child = _pointer(at, key)
                visit(key, child)
                if key in result:
                    _fail(child, "duplicate decoded object key", "DUPLICATE_KEY")
                result[key] = visit(item, child)
            return result
        if type(value) is list:
            return [visit(item, _pointer(at, i)) for i, item in enumerate(value)]
        if type(value) is str:
            try:
                value.encode("utf-8", errors="strict")
            except UnicodeError:
                _fail(at, "unpaired Unicode surrogate", "INVALID_UNICODE")
        return value

    try:
        return visit(
            json.loads(
                text,
                parse_int=_Number,
                parse_float=_Number,
                parse_constant=invalid_constant,
                object_pairs_hook=_Pairs,
            ),
            path,
        )
    except (json.JSONDecodeError, RecursionError) as error:
        _fail(path, str(error), "JSON")


def _object(raw: Any, path: str, keys: str) -> dict[str, Any]:
    if type(raw) is not dict:
        _fail(path, "require an object")
    expected = keys.split()
    for key in raw:
        if key not in expected:
            _fail(_pointer(path, key), "unknown member")
    for key in expected:
        if key not in raw:
            _fail(_pointer(path, key), "missing member")
    return raw


def _equal(raw: Any, expected: Any, path: str, category: str = "SCHEMA") -> None:
    if type(raw) is not type(expected) or raw != expected:
        _fail(path, "differs from required value", category)


def _string(raw: Any, path: str) -> str:
    if type(raw) is not str or not raw:
        _fail(path, "require a nonempty string")
    return raw


def _checksum(raw: Any, path: str) -> str:
    value = _string(raw, path)
    if re.fullmatch(r"[0-9a-f]{64}", value) is None:
        _fail(path, "require lowercase hexadecimal SHA-256", "CHECKSUM")
    return value


def _float(raw: Any, path: str, *, positive: bool = False) -> float:
    if not isinstance(raw, _Number):
        _fail(path, "require a JSON number", "NUMBER")
    value = float(raw.token)
    # Inspect the significand without imposing Decimal's exponent range on JSON.
    nonzero = any(c in "123456789" for c in raw.token.lower().split("e", 1)[0])
    if not math.isfinite(value) or (value == 0 and nonzero):
        _fail(path, "overflow, nonfinite value or nonzero token underflow", "NUMBER")
    if value < 0 or (positive and value == 0):
        _fail(
            path, "require a positive value" if positive else "negative value", "NUMBER"
        )
    return value


def _integer(
    raw: Any, path: str, *, minimum: int = 0, maximum: int | None = None
) -> int:
    if (
        not isinstance(raw, _Number)
        or re.fullmatch(r"-?(0|[1-9][0-9]*)", raw.token) is None
    ):
        _fail(path, "require an integer-form JSON number", "INTEGER")
    # Exact even beyond Python's configurable decimal-string conversion limit.
    value = int(Decimal(raw.token))
    if value < minimum or (maximum is not None and value > maximum):
        _fail(path, "integer outside field range", "INTEGER")
    return value


def _array(raw: Any, path: str) -> list[Any]:
    if type(raw) is not list:
        _fail(path, "require an array")
    return raw


def _grid(raw: Any, path: str) -> list[float]:
    values = [
        _float(item, _pointer(path, i)) for i, item in enumerate(_array(raw, path))
    ]
    if not values:
        _fail(path, "require a nonempty time grid")
    for i in range(1, len(values)):
        if values[i] <= values[i - 1]:
            _fail(_pointer(path, i), "times must be strictly increasing", "GRID")
    return values


def _bits(value: float) -> bytes:
    return struct.pack(">d", value)


def _reference(document: Any) -> dict[str, Any]:
    return {
        "schema_version": document.content.schema_version,
        "id": document.content.id,
        "revision": document.content.revision,
        "digest": document.digest,
    }


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _timestamp(raw: Any, path: str) -> None:
    text = _string(raw, path)
    if (
        re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z", text
        )
        is None
    ):
        _fail(path, "require fixed microsecond UTC timestamp")
    try:
        datetime.strptime(text, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        _fail(path, "invalid Gregorian UTC timestamp")


def _options(method: str) -> dict[str, Any]:
    return {
        "first_step": None,
        "vectorized": False,
        "dense_output": False,
        "events": None,
        "jacobian": "constant_exact" if method == "Radau" else "not_supplied",
    }


def _manifest(
    raw: Any, experiment: ExperimentDocument, fir: FIRDocument
) -> dict[str, Any]:
    p = "/manifest"
    m = _object(
        raw,
        p,
        "kind schema_version status repeatability sources fir execution randomness evaluations timing integration output producer backend",
    )
    for key, value in (
        ("kind", "RunManifest"),
        ("schema_version", "0.1.0"),
        ("status", "success"),
        ("repeatability", "bounded_numerical_agreement"),
    ):
        _equal(
            m[key],
            value,
            p + "/" + key,
            "UNSUPPORTED_VERSION" if key == "schema_version" else "SCHEMA",
        )
    sources = _object(m["sources"], p + "/sources", "design experiment")
    for name, document in (
        ("design", experiment.source_design),
        ("experiment", experiment),
    ):
        at = p + "/sources/" + name
        ref = _object(sources[name], at, "schema_version id revision digest")
        ref["revision"] = _integer(
            ref["revision"], at + "/revision", minimum=1, maximum=9007199254740991
        )
        for key, value in _reference(document).items():
            _equal(ref[key], value, at + "/" + key, "REFERENCE")
    f = _object(m["fir"], p + "/fir", "schema_version canonicalization_version digest")
    for key, value in (
        ("schema_version", "0.1.0"),
        ("canonicalization_version", "0.1.0"),
        ("digest", fir.digest),
    ):
        _equal(f[key], value, p + "/fir/" + key, "IDENTITY")
    e = _object(
        m["execution"],
        p + "/execution",
        "profile time_grid rtol atol max_step max_nfev",
    )
    _equal(e["profile"], "ode", p + "/execution/profile", "UNSUPPORTED_PROFILE")
    e["time_grid"] = _grid(e["time_grid"], p + "/execution/time_grid")
    for key in ("rtol", "atol", "max_step"):
        e[key] = _float(e[key], p + "/execution/" + key, positive=True)
    if e["rtol"] < 100 * 2.0**-52:
        _fail(p + "/execution/rtol", "below SciPy's tolerance floor", "EXECUTION_SPEC")
    e["max_nfev"] = _integer(e["max_nfev"], p + "/execution/max_nfev", minimum=1)
    rng = _object(m["randomness"], p + "/randomness", "rng seed")
    _equal(rng["rng"], "none", p + "/randomness/rng")
    _equal(rng["seed"], None, p + "/randomness/seed")
    ev = _object(m["evaluations"], p + "/evaluations", "nfev")
    ev["nfev"] = _integer(ev["nfev"], p + "/evaluations/nfev")
    if ev["nfev"] > e["max_nfev"]:
        _fail(p + "/evaluations/nfev", "exceeds work budget", "COUNTERS")
    timing = _object(
        m["timing"], p + "/timing", "started_at_utc finished_at_utc elapsed_seconds"
    )
    for key in ("started_at_utc", "finished_at_utc"):
        _timestamp(timing[key], p + "/timing/" + key)
    timing["elapsed_seconds"] = _float(
        timing["elapsed_seconds"], p + "/timing/elapsed_seconds"
    )
    output = _object(
        m["output"], p + "/output", "schema_version media_type encoding sha256"
    )
    for key, value in (
        ("schema_version", "0.1.0"),
        ("media_type", "application/json"),
        ("encoding", "utf-8"),
    ):
        _equal(output[key], value, p + "/output/" + key)
    _checksum(output["sha256"], p + "/output/sha256")
    producer = _object(m["producer"], p + "/producer", "name version build_id")
    for key in ("name", "version", "build_id"):
        if key != "build_id" or producer[key] is not None:
            _string(producer[key], p + "/producer/" + key)
    backend = _object(
        m["backend"], p + "/backend", "profile solver environment evaluations"
    )
    _equal(
        backend["profile"],
        "python-scipy-ode/0.1.0",
        p + "/backend/profile",
        "UNSUPPORTED_PROFILE",
    )
    solver = _object(backend["solver"], p + "/backend/solver", "name method options")
    _equal(solver["name"], "scipy.integrate.solve_ivp", p + "/backend/solver/name")
    if type(solver["method"]) is not str or solver["method"] not in ("DOP853", "Radau"):
        _fail(p + "/backend/solver/method", "unsupported method", "UNSUPPORTED_METHOD")
    options = _object(
        solver["options"],
        p + "/backend/solver/options",
        "first_step vectorized dense_output events jacobian",
    )
    for key, value in _options(solver["method"]).items():
        _equal(options[key], value, p + "/backend/solver/options/" + key)
    env = _object(
        backend["environment"],
        p + "/backend/environment",
        "python_implementation python_version rfc8785_version numpy_version scipy_version",
    )
    for key, value in env.items():
        _string(value, p + "/backend/environment/" + key)
    bev = _object(backend["evaluations"], p + "/backend/evaluations", "njev nlu")
    for key in bev:
        bev[key] = _integer(bev[key], p + "/backend/evaluations/" + key)
    skipped = len(e["time_grid"]) == 1 and e["time_grid"][0] == 0
    _equal(
        m["integration"],
        "skipped_zero_grid" if skipped else "performed",
        p + "/integration",
    )
    if (skipped and ev["nfev"] != 0) or (not skipped and ev["nfev"] == 0):
        _fail(p + "/evaluations/nfev", "inconsistent integration counter", "COUNTERS")
    if skipped:
        for key in bev:
            if bev[key] != 0:
                _fail(
                    p + "/backend/evaluations/" + key,
                    "skipped integration requires zero counters",
                    "COUNTERS",
                )
    return m


def _result(raw: Any, manifest: dict[str, Any], fir: FIRDocument) -> dict[str, Any]:
    p = "/result"
    r = _object(
        raw,
        p,
        "kind schema_version fir_digest time_unit times state_ids state_units state_values observable_ids observable_state_ids observable_units observable_values",
    )
    for key, value in (
        ("kind", "ODEResult"),
        ("schema_version", "0.1.0"),
        ("fir_digest", fir.digest),
        ("time_unit", "s"),
    ):
        _equal(
            r[key],
            value,
            p + "/" + key,
            "UNSUPPORTED_VERSION" if key == "schema_version" else "IDENTITY",
        )
    model = fir.model.normalized().to_dict()
    states, obs = model["states"], model["observables"]
    for key, expected in (
        ("state_ids", [s["id"] for s in states]),
        ("state_units", [s["unit"] for s in states]),
        ("observable_ids", [o["id"] for o in obs]),
        ("observable_state_ids", [o["state"] for o in obs]),
        ("observable_units", [o["unit"] for o in obs]),
    ):
        _equal(r[key], expected, p + "/" + key, "COLUMNS")
    r["times"] = _grid(r["times"], p + "/times")
    grid = manifest["execution"]["time_grid"]
    if len(r["times"]) != len(grid):
        _fail(p + "/times", "grid length mismatch", "GRID")
    for i, (a, b) in enumerate(zip(r["times"], grid, strict=True)):
        if _bits(a) != _bits(b):
            _fail(f"{p}/times/{i}", "grid bits differ", "GRID")
    for key, columns in (
        ("state_values", len(states)),
        ("observable_values", len(obs)),
    ):
        rows = _array(r[key], p + "/" + key)
        if len(rows) != len(grid):
            _fail(p + "/" + key, "sample count mismatch", "DIMENSIONS")
        for i, row in enumerate(rows):
            at = f"{p}/{key}/{i}"
            row = _array(row, at)
            if len(row) != columns:
                _fail(at, "column count mismatch", "DIMENSIONS")
            rows[i] = [_float(value, f"{at}/{j}") for j, value in enumerate(row)]
    indices = {s["id"]: i for i, s in enumerate(states)}
    for i, time in enumerate(grid):
        for j, state in enumerate(states):
            if time == 0 and r["state_values"][i][j] != state["initial"]:
                _fail(
                    f"{p}/state_values/{i}/{j}",
                    "zero-time sample differs from initial state",
                    "INITIAL_STATE",
                )
        for j, observable in enumerate(obs):
            value = r["state_values"][i][indices[observable["state"]]]
            if _bits(r["observable_values"][i][j]) != _bits(value):
                _fail(
                    f"{p}/observable_values/{i}/{j}",
                    "observable bits differ from mapped state",
                    "OBSERVABLE",
                )
    return r


@dataclass(frozen=True, slots=True)
class _Object(Mapping[str, object]):
    entries: tuple[tuple[str, object], ...]

    def __getitem__(self, key: str) -> object:
        for name, value in self.entries:
            if key == name:
                return value
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return (name for name, _ in self.entries)

    def __len__(self) -> int:
        return len(self.entries)


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return _Object(tuple((k, _freeze(v)) for k, v in value.items()))
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, _Object):
        return {k: _thaw(v) for k, v in value.entries}
    if isinstance(value, tuple):
        return [_thaw(v) for v in value]
    return value


def _emit(value: Any) -> str:
    """Transport JSON preserving binary64 signs and arbitrarily large integers."""
    if type(value) is int:
        return str(Decimal(value))
    if type(value) is dict:
        return (
            "{"
            + ",".join(json.dumps(k) + ":" + _emit(v) for k, v in value.items())
            + "}"
        )
    if type(value) in (tuple, list):
        return "[" + ",".join(_emit(v) for v in value) + "]"
    return json.dumps(value, allow_nan=False)


@dataclass(frozen=True, slots=True, init=False)
class RunManifest:
    """Validated immutable observations; to_json retains original transport text."""

    _data: _Object
    _text: str

    def __init__(self) -> None:
        raise TypeError("use run_experiment or RunRecord.from_json")

    def to_dict(self) -> dict[str, Any]:
        return dict(_thaw(self._data))

    def to_json(self) -> str:
        return self._text


@dataclass(frozen=True, slots=True, init=False)
class ODEResult:
    """Validated sample-major values in normalized FIR declaration order."""

    kind: str
    schema_version: str
    fir_digest: str
    time_unit: str
    times: tuple[float, ...]
    state_ids: tuple[str, ...]
    state_units: tuple[str, ...]
    state_values: tuple[tuple[float, ...], ...]
    observable_ids: tuple[str, ...]
    observable_state_ids: tuple[str, ...]
    observable_units: tuple[str, ...]
    observable_values: tuple[tuple[float, ...], ...]

    def __init__(self) -> None:
        raise TypeError("use run_experiment or RunRecord.from_json")

    def to_dict(self) -> dict[str, Any]:
        return {name: _thaw(getattr(self, name)) for name in self.__dataclass_fields__}


@dataclass(frozen=True, slots=True, init=False)
class RunRecord:
    """Source-verified artifact pair, with exact original result bytes.

    Use run_experiment to capture execution. Loading checks internal consistency
    and optional trusted manifest identity without executing a solver.
    """

    manifest: RunManifest
    result: ODEResult
    result_bytes: bytes

    def __init__(self) -> None:
        raise TypeError("use run_experiment or RunRecord.from_json")

    @classmethod
    def from_json(
        cls,
        manifest_json: str | bytes,
        result_bytes: bytes,
        *,
        experiment: ExperimentDocument,
        expected_manifest_sha256: str | None = None,
    ) -> RunRecord:
        text = _text(manifest_json, "/manifest")
        if expected_manifest_sha256 is not None:
            expected = _checksum(expected_manifest_sha256, "/manifest")
            if hashlib.sha256(text.encode("utf-8")).hexdigest() != expected:
                _fail("/manifest", "differs from trusted manifest checksum", "CHECKSUM")
        try:
            fir = compile_experiment(experiment)
        except FIRValidationError as error:
            _fail("/manifest/sources" + error.path, str(error), error.category)
        return _record(text, result_bytes, experiment, fir)


def _record(
    text: str, result_bytes: bytes, experiment: ExperimentDocument, fir: FIRDocument
) -> RunRecord:
    m = _manifest(_parse(text, "/manifest"), experiment, fir)
    if type(result_bytes) is not bytes:
        _fail("/result", "require exact immutable result bytes")
    if hashlib.sha256(result_bytes).hexdigest() != m["output"]["sha256"]:
        _fail("/manifest/output/sha256", "result byte checksum mismatch", "CHECKSUM")
    r = _result(_parse(_text(result_bytes, "/result"), "/result"), m, fir)
    manifest = object.__new__(RunManifest)
    object.__setattr__(manifest, "_data", _freeze(m))
    object.__setattr__(manifest, "_text", text)
    result = object.__new__(ODEResult)
    for key, value in r.items():
        object.__setattr__(result, key, _freeze(value))
    record = object.__new__(RunRecord)
    object.__setattr__(record, "manifest", manifest)
    object.__setattr__(record, "result", result)
    object.__setattr__(record, "result_bytes", result_bytes)
    return record


def run_experiment(experiment: ExperimentDocument, spec: ODEExecutionSpec) -> RunRecord:
    """Revalidate sources, compile and execute normalized M0 FIR, then capture.

    Compiler/execution exceptions propagate unchanged; failed execution produces
    no successful record. Capture has no filesystem, VCS or network operations.
    """
    started, start_ns = _utc_now(), monotonic_ns()
    fir = compile_experiment(experiment)
    trajectory = solve_ode(fir.model.normalized(), spec)
    model = fir.model.normalized().to_dict()
    r = {
        "kind": "ODEResult",
        "schema_version": "0.1.0",
        "fir_digest": fir.digest,
        "time_unit": trajectory.time_unit,
        "times": trajectory.times,
        "state_ids": trajectory.state_ids,
        "state_units": trajectory.state_units,
        "state_values": trajectory.state_values,
        "observable_ids": trajectory.observable_ids,
        "observable_state_ids": [o["state"] for o in model["observables"]],
        "observable_units": trajectory.observable_units,
        "observable_values": trajectory.observable_values,
    }
    result_bytes = _emit(r).encode("utf-8")
    checksum = hashlib.sha256(result_bytes).hexdigest()
    finished, finish_ns = _utc_now(), monotonic_ns()
    backend_versions = dict(trajectory.backend_versions)
    manifest = {
        "kind": "RunManifest",
        "schema_version": "0.1.0",
        "status": "success",
        "repeatability": "bounded_numerical_agreement",
        "sources": {
            "design": _reference(experiment.source_design),
            "experiment": _reference(experiment),
        },
        "fir": {
            "schema_version": "0.1.0",
            "canonicalization_version": "0.1.0",
            "digest": fir.digest,
        },
        "execution": {
            "profile": spec.profile,
            "time_grid": spec.time_grid,
            "rtol": spec.rtol,
            "atol": spec.atol,
            "max_step": spec.max_step,
            "max_nfev": spec.max_nfev,
        },
        "randomness": {"rng": "none", "seed": None},
        "evaluations": {"nfev": trajectory.nfev},
        "timing": {
            "started_at_utc": started.isoformat(timespec="microseconds").replace(
                "+00:00", "Z"
            ),
            "finished_at_utc": finished.isoformat(timespec="microseconds").replace(
                "+00:00", "Z"
            ),
            "elapsed_seconds": (finish_ns - start_ns) / 1_000_000_000,
        },
        "integration": "skipped_zero_grid" if spec.time_grid[-1] == 0 else "performed",
        "output": {
            "schema_version": "0.1.0",
            "media_type": "application/json",
            "encoding": "utf-8",
            "sha256": checksum,
        },
        "producer": {
            "name": "fenix-bio",
            "version": version("fenix-bio"),
            "build_id": None,
        },
        "backend": {
            "profile": "python-scipy-ode/0.1.0",
            "solver": {
                "name": "scipy.integrate.solve_ivp",
                "method": spec.method,
                "options": _options(spec.method),
            },
            "environment": {
                "python_implementation": platform.python_implementation(),
                "python_version": platform.python_version(),
                "rfc8785_version": version("rfc8785"),
                "numpy_version": backend_versions["numpy"],
                "scipy_version": backend_versions["scipy"],
            },
            "evaluations": {"njev": trajectory.njev, "nlu": trajectory.nlu},
        },
    }
    return _record(_emit(manifest), result_bytes, experiment, fir)
