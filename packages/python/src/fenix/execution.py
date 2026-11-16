"""P04 M0 ODE execution with bounded numerical agreement, not bitwise replay.

Tiny negative sampled counts fail even for mathematically well-posed models.
No clipping, automatic fallback, or analytical replacement is performed. The
in-memory trajectory is not a P07 result serialization or authenticated manifest.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import scipy
from numpy.typing import NDArray
from scipy.integrate import solve_ivp

from fenix.fir import FIRModel


class ExecutionValidationError(ValueError):
    """One invalid execution setting, with a field-relative JSON Pointer."""

    def __init__(self, category: str, path: str, message: str) -> None:
        self.category = category
        self.path = path
        super().__init__(f"{category} at {path}: {message}")


def _invalid(path: str, message: str) -> None:
    raise ExecutionValidationError("EXECUTION_SPEC", path, message)


@dataclass(frozen=True, slots=True, kw_only=True)
class ODEExecutionSpec:
    """Explicit P04 settings; first_step=None selects SciPy's initial step.

    Tolerances are local error controls, not certified global error bounds.
    Repeated runs promise bounded numerical agreement, not identical sample bits.
    max_nfev bounds RHS evaluations, not wall time or memory.
    """

    time_grid: tuple[float, ...]
    method: str
    rtol: float
    atol: float
    max_step: float
    max_nfev: int
    profile: str = "ode"

    def __post_init__(self) -> None:
        if type(self.time_grid) is not tuple or not self.time_grid:
            _invalid("/time_grid", "require a nonempty tuple of binary64 times")
        previous = -1.0
        for index, value in enumerate(self.time_grid):
            path = f"/time_grid/{index}"
            if type(value) is not float or not math.isfinite(value) or value < 0:
                _invalid(path, "require a finite nonnegative built-in float")
            if value <= previous:
                _invalid(path, "times must be strictly increasing")
            previous = value
        if type(self.method) is not str or self.method not in ("DOP853", "Radau"):
            raise ExecutionValidationError(
                "UNSUPPORTED_METHOD", "/method", "require DOP853 or Radau"
            )
        for name in ("rtol", "atol", "max_step"):
            value = getattr(self, name)
            if type(value) is not float or not math.isfinite(value) or value <= 0:
                _invalid("/" + name, "require a positive finite built-in float")
        if self.rtol < 100 * 2.0**-52:
            _invalid("/rtol", "below SciPy's effective relative-tolerance floor")
        if type(self.max_nfev) is not int or self.max_nfev <= 0:
            _invalid("/max_nfev", "require a positive built-in integer")
        if type(self.profile) is not str:
            _invalid("/profile", "require a profile string")


class ODEExecutionError(RuntimeError):
    """An unsuccessful run, never a successful partial trajectory."""

    def __init__(
        self, category: str, spec: ODEExecutionSpec, nfev: int, message: str
    ) -> None:
        self.category = category
        self.spec = spec
        self.nfev = nfev
        super().__init__(f"{category} ({spec.method}, RHS calls={nfev}): {message}")


@dataclass(frozen=True, slots=True, kw_only=True)
class ODETrajectory:
    """Immutable sampled output of solve_ode, without a bitwise replay guarantee.

    Values are sample-major rows aligned with times and their corresponding IDs.
    Backend versions/settings describe the computation; future P07 manifests must
    preserve the distinction between bounded accuracy and byte-identical replay.
    """

    times: tuple[float, ...]
    state_ids: tuple[str, ...]
    state_values: tuple[tuple[float, ...], ...]
    state_units: tuple[str, ...]
    observable_ids: tuple[str, ...]
    observable_values: tuple[tuple[float, ...], ...]
    observable_units: tuple[str, ...]
    time_unit: str
    fir_digest: str
    spec: ODEExecutionSpec
    nfev: int
    njev: int
    nlu: int
    backend_versions: tuple[tuple[str, str], ...]


def solve_ode(model: FIRModel, spec: ODEExecutionSpec) -> ODETrajectory:
    """Execute validated M0 mathematics under P04 without mutating its identity.

    Tiny negative samples are rejected, including interpolation excursions near
    zero. No claim of successful execution for all finite FIR inputs is made.
    """
    if type(model) is not FIRModel:
        raise TypeError("model must be an exact validated FIRModel")
    if type(spec) is not ODEExecutionSpec:
        raise TypeError("spec must be an exact ODEExecutionSpec")
    model.require_capability(spec.profile)
    data = model.to_dict()
    parameters = {p["id"]: p["value"] for p in data["parameters"]}
    state = {s["id"]: s for s in data["states"]}["x"]
    alpha, beta, x0 = parameters["alpha"], parameters["beta"], state["initial"]
    calls = 0

    def fail(category: str, message: str) -> None:
        raise ODEExecutionError(category, spec, calls, message)

    def rhs(t: float, y: NDArray[np.float64]) -> NDArray[np.float64]:
        nonlocal calls
        if calls >= spec.max_nfev:
            fail("WORK_LIMIT", "RHS evaluation budget exhausted")
        calls += 1
        derivative = np.array([alpha - beta * y[0]], dtype=np.float64)
        if not np.isfinite(derivative).all():
            fail("NONFINITE", "nonfinite RHS arithmetic")
        return derivative

    samples: tuple[float, ...]
    njev = nlu = 0
    if spec.time_grid[-1] == 0.0:
        samples = (float(x0),)
    else:
        try:
            with np.errstate(
                over="raise", invalid="raise", divide="raise", under="ignore"
            ):
                if spec.method == "Radau":
                    result = solve_ivp(
                        rhs,
                        (0.0, spec.time_grid[-1]),
                        [x0],
                        method="Radau",
                        t_eval=spec.time_grid,
                        rtol=spec.rtol,
                        atol=spec.atol,
                        max_step=spec.max_step,
                        first_step=None,
                        vectorized=False,
                        dense_output=False,
                        events=None,
                        jac=np.array([[-beta]], dtype=np.float64),
                    )
                else:
                    result = solve_ivp(
                        rhs,
                        (0.0, spec.time_grid[-1]),
                        [x0],
                        method="DOP853",
                        t_eval=spec.time_grid,
                        rtol=spec.rtol,
                        atol=spec.atol,
                        max_step=spec.max_step,
                        first_step=None,
                        vectorized=False,
                        dense_output=False,
                        events=None,
                    )
        except FloatingPointError as error:
            raise ODEExecutionError("NONFINITE", spec, calls, str(error)) from error
        except (ValueError, OverflowError, np.linalg.LinAlgError) as error:
            raise ODEExecutionError(
                "SOLVER_FAILURE", spec, calls, str(error)
            ) from error
        if not result.success or result.status != 0:
            fail("SOLVER_FAILURE", str(result.message))
        times = np.asarray(result.t)
        values = np.asarray(result.y)
        if (
            times.shape != (len(spec.time_grid),)
            or values.shape != (1, len(spec.time_grid))
            or not np.array_equal(times, spec.time_grid)
        ):
            fail("INVALID_OUTPUT", "incomplete or misaligned sampled output")
        if values.dtype.kind != "f":
            fail("INVALID_OUTPUT", "expected real binary64 sampled output")
        if not np.isfinite(values).all():
            fail("NONFINITE", "nonfinite sampled output")
        if (values < 0).any():
            fail("NEGATIVE_STATE", "negative sampled count; no clipping is permitted")
        samples = tuple(float(v) for v in values[0])
        njev, nlu = int(result.njev), int(result.nlu)
    observables = data["observables"]
    return ODETrajectory(
        times=spec.time_grid,
        state_ids=("x",),
        state_values=tuple((value,) for value in samples),
        state_units=(state["unit"],),
        observable_ids=tuple(o["id"] for o in observables),
        observable_values=tuple(tuple(value for _ in observables) for value in samples),
        observable_units=tuple(o["unit"] for o in observables),
        time_unit=data["time_unit"],
        fir_digest=model.digest,
        spec=spec,
        nfev=calls,
        njev=njev,
        nlu=nlu,
        backend_versions=(("numpy", np.__version__), ("scipy", scipy.__version__)),
    )
