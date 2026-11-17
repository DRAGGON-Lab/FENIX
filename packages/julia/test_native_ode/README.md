# Native SciML P04 conformance

Run with the [pinned native environment](../../../conformance/julia_ode/README.md):

```sh
julia --project=conformance/julia_ode packages/julia/test_native_ode/runtests.jl --report artifacts/julia-native-ode.json
```

Both Tsit5 and Rodas5P execute every one of the 40 approved production-decay
samples at P04 coarse, baseline and refined settings. Inputs decode exact
binary64 bits, are authored/compiled natively, and leave source/FIR values
unchanged. Each output is converted exactly to 512-bit BigFloat and compared
to the unchanged 50-digit decimal reference, with the fixed bound
`1e-9 + 1e-8*abs(reference)` molecules. The comparison precision exceeds 100
decimal digits and is separate from binary64 numerical integration.

Individual actual bits, absolute/scaled errors, settings, RHS/Jacobian/W-matrix
counts and backend versions are reported. A stiff exploratory control compares
against the unchanged independent analytical law; it does not add a golden
fixture. Its explicit method run must exhaust the declared budget; the stiff
method must satisfy the same global output bound. Refinement does not imply
monotonic error reduction or establish method order.

The optional report is emitted after all checks pass and protects repository
sources/fixtures and aliases using the existing native report-path guard.
Historical reports, fixtures and Python implementations remain unchanged.
No empirical biological validity, portable P07 results or independent #29
cross-language acceptance follows from this bounded numerical matrix.
