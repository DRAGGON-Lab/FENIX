# Native Julia bounded M1 implementation

Refs #33. The [PI decision](m1-executable-acceptance.md) supplies the exact P08
specification, reference catalog, and numerical criteria for this implementation.
The Julia work is submitted after the Python implementation in PR #97. The
independent #35 conformance gate and EP-05 review are separate deliverables.

`Fenix.Community` adds immutable authoring and strict wire loading, exact
source-linked FIR compilation and identity, coupled Tsit5 and Rodas5P execution,
and scoped capture and readback. It reuses the native JSON tokenizer and JCS
serializer, along with the existing SciML solver options. The package includes
the four accepted finite schemas byte for byte, and resolves their internal
definitions locally. It uses Julia's existing dependencies.

The numerical kernel orders counts as `env.signal, receiver.reporter,
receiver.signal, sender.signal`. It passes the full in-place Jacobian and
zero time derivative to SciML. It rejects negative sensing stages and
nonfinite arithmetic, checks the requested grid and complete returned state
matrix, and skips execution for zero-only grids. Work budgets count RHS calls.
Capture records `nw` as defined by SciML.

The native test suite exercises 14 literal packets and 56 declared diagnostic
witnesses, including readback of illustrative Python and Julia artifacts.
It compares 40 integrations and 120 four-state samples against independently
derived BigFloat laws and checks 72 population-weighted balances including
initial representation error. Other tests cover lexical and transport
projections, collapsed grids, exact counters, immutable revision handling,
backend failure, and compile-once/solve-once capture. The kernel tests check
asymmetric BigFloat derivatives and successful-tail comparisons with
corrupted-output controls.

The [package guide](../../packages/julia/README.md) provides the API example and
local verification command. The [CI workflow](../../.github/workflows/native-community-julia.yml)
also runs the package and native suite from a separately extracted archive.
