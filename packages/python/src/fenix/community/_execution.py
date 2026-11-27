"""P08 coupled SciPy execution in canonical wire-state order."""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
import scipy
from numpy.typing import NDArray
from scipy.integrate import solve_ivp

from fenix.execution import ODEExecutionError, ODEExecutionSpec, ODETrajectory

from ._documents import FIR, STATES


class Kernel:
    def __init__(self, model: FIR, spec: ODEExecutionSpec) -> None:
        m = model.normalized_model()
        self.p = {k: float(q["value"]) for k, q in m["parameters"].items()}
        self.v = {k: float(q["value"]) for k, q in m["volumes"].items()}
        self.n = {k: float(v) for k, v in m["populations"].items()}
        self.spec, self.calls = spec, 0

    def fail(self, category: str, message: str) -> None:
        raise ODEExecutionError(category, self.spec, self.calls, message)

    def domain(self, t: float, values: NDArray[np.float64]) -> None:
        if not np.isfinite(t) or not np.isfinite(values).all():
            self.fail("NONFINITE", "nonfinite stage")
        if values[0] < 0:
            self.fail("STAGE_DOMAIN", f"negative extracellular sensing stage at {t!r}")

    def hill(self, e: float) -> float:
        c, k, n = e / self.v["env"], self.p["threshold"], self.p["hill_n"]
        if not np.isfinite(c):
            self.fail("NONFINITE", "nonfinite sensing density")
        if c <= k:
            z = (c / k) ** n
            return float(z / (1 + z))
        return float(1 / (1 + (k / c) ** n))

    def rhs(self, t: float, values: NDArray[np.float64]) -> NDArray[np.float64]:
        if self.calls >= self.spec.max_nfev:
            self.fail("WORK_LIMIT", "RHS evaluation budget exhausted")
        self.calls += 1
        self.domain(t, values)
        e, y, r, s = values
        p, v, n = self.p, self.v, self.n
        js = p["sender_export"] * s - p["sender_import"] * v["sender"] * (e / v["env"])
        jr = p["receiver_export"] * r - p["receiver_import"] * v["receiver"] * (
            e / v["env"]
        )
        result = np.array(
            [
                n["sender"] * js + n["receiver"] * jr - p["env_decay"] * e,
                p["reporter_basal"]
                + p["reporter_induced"] * self.hill(float(e))
                - p["reporter_decay"] * y,
                -p["receiver_decay"] * r - jr,
                p["sender_production"] - p["sender_decay"] * s - js,
            ],
            dtype=np.float64,
        )
        if not np.isfinite(result).all():
            self.fail("NONFINITE", "nonfinite RHS arithmetic")
        return result

    def jacobian(self, t: float, values: NDArray[np.float64]) -> NDArray[np.float64]:
        self.domain(t, values)
        e, p, v, n = float(values[0]), self.p, self.v, self.n
        si, ri = (
            p["sender_import"] * v["sender"] / v["env"],
            p["receiver_import"] * v["receiver"] / v["env"],
        )
        so, ro = p["sender_export"], p["receiver_export"]
        h = self.hill(e)
        if e == 0:
            derivative = 0.0
            if p["hill_n"] == 1:
                denominator = p["threshold"] * v["env"]
                if not np.isfinite(denominator) or denominator == 0:
                    self.fail("NONFINITE", "invalid zero-signal Jacobian denominator")
                derivative = 1 / denominator
        else:
            derivative = p["hill_n"] * h * (1 - h) / e
        matrix = np.array(
            [
                [
                    -n["sender"] * si - n["receiver"] * ri - p["env_decay"],
                    0,
                    n["receiver"] * ro,
                    n["sender"] * so,
                ],
                [p["reporter_induced"] * derivative, -p["reporter_decay"], 0, 0],
                [ri, 0, -p["receiver_decay"] - ro, 0],
                [si, 0, 0, -p["sender_decay"] - so],
            ],
            dtype=np.float64,
        )
        if not np.isfinite(matrix).all():
            self.fail("NONFINITE", "nonfinite Jacobian arithmetic")
        return matrix


def solve_ode(model: FIR, spec: ODEExecutionSpec) -> ODETrajectory:
    if type(model) is not FIR or type(spec) is not ODEExecutionSpec:
        raise TypeError("require verified community FIR and ODEExecutionSpec")
    if spec.profile != "ode":
        raise ODEExecutionError(
            "UNSUPPORTED_PROFILE", spec, 0, "M1 supports deterministic ode only"
        )
    kernel = Kernel(model, spec)
    m = model.normalized_model()
    initial = [float(m["initial_counts"][state]["value"]) for state in STATES]
    njev = nlu = 0
    rows: tuple[tuple[float, ...], ...]
    method: Literal["DOP853", "Radau"] = "Radau" if spec.method == "Radau" else "DOP853"
    if spec.time_grid[-1] == 0.0:
        rows = (tuple(initial),)
    else:
        try:
            with np.errstate(
                over="raise", invalid="raise", divide="raise", under="ignore"
            ):
                options: dict[str, Any] = (
                    {"jac": kernel.jacobian} if spec.method == "Radau" else {}
                )
                result = solve_ivp(
                    kernel.rhs,
                    (0.0, spec.time_grid[-1]),
                    initial,
                    method=method,
                    t_eval=spec.time_grid,
                    rtol=spec.rtol,
                    atol=spec.atol,
                    max_step=spec.max_step,
                    first_step=None,
                    vectorized=False,
                    dense_output=False,
                    events=None,
                    **options,
                )
                if not result.success:
                    kernel.fail("INTEGRATION_FAILURE", "backend did not complete")
                if not np.array_equal(result.t, spec.time_grid) or result.y.shape != (
                    4,
                    len(spec.time_grid),
                ):
                    kernel.fail(
                        "INCOMPLETE_OUTPUT",
                        "backend returned incomplete grid or state columns",
                    )
                if not np.isfinite(result.y).all():
                    kernel.fail("NONFINITE", "nonfinite returned counts")
                if np.any(result.y < 0):
                    kernel.fail("NEGATIVE_OUTPUT", "negative returned counts")
                rows = tuple(tuple(float(x) for x in row) for row in result.y.T)
                njev, nlu = int(result.njev), int(result.nlu)
        except (ArithmeticError, ValueError) as error:
            kernel.fail("NONFINITE", str(error))
            raise AssertionError("unreachable") from error
    observations = m["observables"]
    return ODETrajectory(
        times=spec.time_grid,
        state_ids=STATES,
        state_values=rows,
        state_units=("molecule",) * 4,
        observable_ids=tuple(o["id"] for o in observations),
        observable_values=tuple(
            tuple(row[STATES.index(o["state"])] for o in observations) for row in rows
        ),
        observable_units=("molecule",) * len(observations),
        time_unit="s",
        fir_digest=model.digest,
        spec=spec,
        nfev=kernel.calls,
        njev=njev,
        nlu=nlu,
        backend_versions=(("numpy", np.__version__), ("scipy", scipy.__version__)),
    )
