# Scientific evidence — pending

Document each supported model primitive/profile with mathematical definition, units, assumptions, analytical/invariant oracles, negative tests, numeric tolerances and any empirical applicability. Mathematical correctness is distinct from empirical predictive validity.

- [Production–decay analytical oracle](production-decay.md): integrating-factor
  derivation, fixed candidate values, precision study and draft error budget
  under ratified P02. The human PI accepted the concrete oracle and fixtures; numerical
  solver thresholds are defined by [ratified P04](../../spec/execution/proposals/ADR-P04.md).
  Independent native Python–Julia ODE acceptance remains #29. See the
  [executed verification record](../verification/ep01-production-decay-oracle.md).
