# Native Julia M0 FIR conformance

From the repository root, using Julia 1.10.13 and the pinned reference environment:

```sh
julia --project=conformance/julia packages/julia/test_native_fir/runtests.jl --report artifacts/julia-native-fir.json
```

The adapter dispatches native APIs against unchanged approved artifacts. All 207
rejection cases check outcomes, diagnostic categories, JSON Pointer paths and
input-document labels; reference-only stage names are not native API promises.
All 84 P03 cases check the applicable raw input/JCS/semantic identity behavior,
including expected normalized objects, model bytes, wrapped identity bytes,
digests, idempotence and round trips. Nine accepted producer controls compile
verified sources and compare complete normalized models/identities with fixed
FIR references, then check output schema and source correspondence.

The compiler/oracle bridge authors ten scenarios using exact approved binary64
input triples. It verifies bits extracted from compiled FIR, units,
stoichiometry and exact AST templates, then supplies those extracted parameters
to the unchanged independent Julia BigFloat oracle. All 40 fixed samples are
checked at 512 and 1024 bits, with precision agreement at 70 significant digits.
There is no solver implementation, Python invocation or generated golden value.
The sets overlap and do not represent exhaustive input validation.

The optional report records actual outcomes and runtime/source/catalog/
evaluator/contract/dependency identities after all checks pass. In-repository
reports must be under `artifacts/`; source and fixture aliases are protected.
Historical reference reports and their `NOT_RUN` rows remain unchanged. CI
uploads this report separately. Package tests use local authored examples and
remain independent of repository fixtures. Human implementation acceptance,
later native numerical execution and cross-language acceptance are separate.
