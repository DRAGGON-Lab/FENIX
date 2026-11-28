"""P08 capture and offline, source-verified scoped result readback."""

from __future__ import annotations

import hashlib
import platform
import struct
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import version
from time import monotonic_ns
from typing import Any, ClassVar

from fenix import __version__
from fenix.execution import ODEExecutionSpec

from ._documents import (
    FIR,
    OWNERS,
    SCOPES,
    STATES,
    Blob,
    Experiment,
    compile_experiment,
)
from ._execution import solve_ode
from ._wire import CommunityValidationError, decode, encode, equal, require, validate


def bits(a: float, b: float) -> bool:
    return struct.pack(">d", a) == struct.pack(">d", b)


def _validate_record(
    experiment: Experiment,
    fir: FIR,
    result: dict[str, Any],
    manifest: dict[str, Any],
    raw_result: bytes,
) -> None:
    validate("ode-result", result)
    validate("run-manifest", manifest)
    require(result["fir_digest"] == fir.digest, "FIR_LINK", "/fir_digest")
    require(manifest["fir"]["digest"] == fir.digest, "FIR_LINK", "/fir/digest")
    for label, document in (("design", experiment.design), ("experiment", experiment)):
        expected_source = dict(schema_version="0.2.0", **document.reference)
        require(
            equal(manifest["sources"][label], expected_source),
            "SOURCE_LINK",
            "/sources/" + label,
        )
    require(
        manifest["output"]["sha256"] == hashlib.sha256(raw_result).hexdigest(),
        "RESULT_CHECKSUM",
        "/output/sha256",
    )
    times = result["times"]
    grid = manifest["execution"]["time_grid"]
    require(
        all(b > a for a, b in zip(times, times[1:], strict=False)), "GRID", "/times"
    )
    require(
        len(grid) == len(times)
        and all(bits(a, b) for a, b in zip(grid, times, strict=True)),
        "GRID",
        "/execution/time_grid",
    )
    require(result["state_owners"] == list(OWNERS), "SCOPE_ALIGNMENT", "/state_owners")
    require(result["state_scopes"] == list(SCOPES), "SCOPE_ALIGNMENT", "/state_scopes")
    model = fir.normalized_model()
    observations = model["observables"]
    expected_columns = {
        "observable_ids": [o["id"] for o in observations],
        "observable_state_ids": [o["state"] for o in observations],
        "observable_units": ["molecule"] * len(observations),
        "observable_owners": [OWNERS[STATES.index(o["state"])] for o in observations],
        "observable_scopes": [SCOPES[STATES.index(o["state"])] for o in observations],
    }
    for key, expected in expected_columns.items():
        require(result[key] == expected, "OBSERVABLE_ALIGNMENT", "/" + key)
    for key in ("state_values", "observable_values"):
        require(len(result[key]) == len(times), "DIMENSIONS", "/" + key)
    for i, (states, values) in enumerate(
        zip(result["state_values"], result["observable_values"], strict=True)
    ):
        require(
            len(values) == len(observations), "DIMENSIONS", f"/observable_values/{i}"
        )
        for j, obs in enumerate(observations):
            require(
                bits(values[j], states[STATES.index(obs["state"])]),
                "OBSERVABLE_COPY",
                f"/observable_values/{i}/{j}",
            )
        if times[i] == 0:
            require(
                all(
                    value == model["initial_counts"][state]["value"]
                    for state, value in zip(STATES, states, strict=True)
                ),
                "INITIAL_SAMPLE",
                f"/state_values/{i}",
            )
    execution, backend = manifest["execution"], manifest["backend"]
    require(
        manifest["evaluations"]["nfev"] <= execution["max_nfev"],
        "WORK_COUNT",
        "/evaluations/nfev",
    )
    zero = len(times) == 1 and times[0] == 0
    require(
        manifest["integration"] == ("skipped_zero_grid" if zero else "performed"),
        "INTEGRATION",
        "/integration",
    )
    if zero:
        require(
            manifest["evaluations"]["nfev"] == 0
            and all(v == 0 for v in backend["evaluations"].values()),
            "WORK_COUNT",
            "/evaluations",
        )
    else:
        require(manifest["evaluations"]["nfev"] > 0, "WORK_COUNT", "/evaluations/nfev")
    if backend["profile"].startswith("julia-"):
        require(
            backend["solver"]["options"]["save_start"] == (times[0] == 0),
            "BACKEND_OPTIONS",
            "/backend/solver/options/save_start",
        )
        require(
            backend["solver"]["options"]["maxiters"] == 9223372036854775807,
            "BACKEND_OPTIONS",
            "/backend/solver/options/maxiters",
        )
    for key in ("started_at_utc", "finished_at_utc"):
        try:
            datetime.strptime(manifest["timing"][key], "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            require(False, "TIMESTAMP", "/timing/" + key)


@dataclass(frozen=True, slots=True, init=False)
class ODEResult(Blob):
    _policy: ClassVar[str] = "result"


@dataclass(frozen=True, slots=True, init=False)
class RunManifest(Blob):
    _policy: ClassVar[str] = "manifest"


@dataclass(frozen=True, slots=True, init=False)
class RunRecord:
    result: ODEResult
    manifest: RunManifest
    result_bytes: bytes
    manifest_bytes: bytes

    def __init__(self) -> None:
        raise TypeError("use run_experiment or RunRecord.from_json")

    @classmethod
    def _create(
        cls, experiment: Experiment, fir: FIR, result_raw: bytes, manifest_raw: bytes
    ) -> RunRecord:
        result, manifest = (
            decode(result_raw, "result"),
            decode(manifest_raw, "manifest"),
        )
        _validate_record(experiment, fir, result, manifest, result_raw)
        obj = object.__new__(cls)
        object.__setattr__(obj, "result", ODEResult._store(result, raw=result_raw))
        object.__setattr__(
            obj, "manifest", RunManifest._store(manifest, raw=manifest_raw)
        )
        object.__setattr__(obj, "result_bytes", result_raw)
        object.__setattr__(obj, "manifest_bytes", manifest_raw)
        return obj

    @classmethod
    def from_json(
        cls,
        result_raw: str | bytes,
        manifest_raw: str | bytes,
        *,
        experiment: Experiment,
        expected_manifest_sha256: str | None = None,
    ) -> RunRecord:
        try:
            r = (
                result_raw.encode("utf-8")
                if isinstance(result_raw, str)
                else result_raw
            )
            m = (
                manifest_raw.encode("utf-8")
                if isinstance(manifest_raw, str)
                else manifest_raw
            )
        except UnicodeError as error:
            raise CommunityValidationError("UNICODE", "") from error
        if expected_manifest_sha256 is not None:
            require(
                hashlib.sha256(m).hexdigest() == expected_manifest_sha256,
                "MANIFEST_CHECKSUM",
                "",
            )
        fir = compile_experiment(experiment)
        return cls._create(experiment, fir, r, m)


def run_experiment(
    experiment: Experiment, spec: ODEExecutionSpec, *, build_id: str | None = None
) -> RunRecord:
    if type(spec) is not ODEExecutionSpec:
        raise TypeError("spec must be an ODEExecutionSpec")
    require(
        build_id is None or type(build_id) is str and len(build_id) > 0,
        "SCHEMA",
        "/producer/build_id",
    )
    encode(
        {"build_id": build_id}
    )  # Reject malformed Unicode before compilation/integration.
    # Compile once, solve once. Validation below reuses this verified FIR.
    started = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    start = monotonic_ns()
    fir = compile_experiment(experiment)
    trajectory = solve_ode(fir, spec)
    elapsed = (monotonic_ns() - start) / 1e9
    finished = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    observations = fir.normalized_model()["observables"]
    result = dict(
        kind="ODEResult",
        schema_version="0.2.0",
        fir_digest=fir.digest,
        time_unit="s",
        times=list(trajectory.times),
        state_ids=list(STATES),
        state_units=["molecule"] * 4,
        state_owners=list(OWNERS),
        state_scopes=list(SCOPES),
        state_values=[list(row) for row in trajectory.state_values],
        observable_ids=list(trajectory.observable_ids),
        observable_state_ids=[o["state"] for o in observations],
        observable_units=list(trajectory.observable_units),
        observable_owners=[OWNERS[STATES.index(o["state"])] for o in observations],
        observable_scopes=[SCOPES[STATES.index(o["state"])] for o in observations],
        observable_values=[list(row) for row in trajectory.observable_values],
    )
    raw_result = ODEResult._store(result).to_bytes()
    manifest = dict(
        kind="RunManifest",
        schema_version="0.2.0",
        status="success",
        repeatability="bounded_numerical_agreement",
        sources={
            name: dict(schema_version="0.2.0", **source.reference)
            for name, source in (
                ("design", experiment.design),
                ("experiment", experiment),
            )
        },
        fir=dict(
            schema_version="0.2.0", canonicalization_version="0.2.0", digest=fir.digest
        ),
        execution=dict(
            profile="ode",
            time_grid=list(spec.time_grid),
            rtol=spec.rtol,
            atol=spec.atol,
            max_step=spec.max_step,
            max_nfev=spec.max_nfev,
        ),
        randomness=dict(rng="none", seed=None),
        evaluations=dict(nfev=trajectory.nfev),
        timing=dict(
            started_at_utc=started, finished_at_utc=finished, elapsed_seconds=elapsed
        ),
        integration="skipped_zero_grid" if spec.time_grid[-1] == 0 else "performed",
        output=dict(
            schema_version="0.2.0",
            media_type="application/json",
            encoding="utf-8",
            sha256=hashlib.sha256(raw_result).hexdigest(),
        ),
        producer=dict(name="fenix-bio", version=__version__, build_id=build_id),
        backend=dict(
            profile="python-scipy-community-ode/0.1.0",
            solver=dict(
                name="scipy.integrate.solve_ivp",
                method=spec.method,
                options=dict(
                    first_step=None,
                    vectorized=False,
                    dense_output=False,
                    events=None,
                    jacobian="state_dependent_exact"
                    if spec.method == "Radau"
                    else "not_supplied",
                ),
            ),
            environment=dict(
                python_implementation=platform.python_implementation(),
                python_version=platform.python_version(),
                rfc8785_version=version("rfc8785"),
                numpy_version=dict(trajectory.backend_versions)["numpy"],
                scipy_version=dict(trajectory.backend_versions)["scipy"],
            ),
            evaluations=dict(njev=trajectory.njev, nlu=trajectory.nlu),
        ),
    )
    return RunRecord._create(
        experiment, fir, raw_result, RunManifest._store(manifest).to_bytes()
    )
