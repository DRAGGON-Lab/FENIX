# Issue #27 — proposed Julia/SciML results profile evidence

Refs [#27](https://github.com/DRAGGON-Lab/FENIX/issues/27). Base `56ad188`
(merged #25/#26), isolated branch `proposal/27-julia-results-profile`.
**PROPOSED; human PI ratification and bounded expectation acceptance PENDING.**
This is the contract/evidence PR. Native capture/readback implementation and its
separate human acceptance are gated on explicit ratification of the reviewed
[supplement](../../spec/results/proposals/ADR-P07-Julia.md),
[additive schema](../../spec/results/proposals/run-manifest-julia-sciml-m0.schema.json)
and bounded expectations. The original P07 approval covers Python/SciPy only.

The new schema reuses the unchanged P07 core by its canonical URN and leaves
both approved schemas and all original example/result bytes unchanged. Four
new manifests pair with the original late-first, zero-only, empty-observable and
reordered multi-observable result bytes. They describe synthetic configurations,
counters, versions and clocks, not observed executions. One intentionally uses
limits above 64-bit Int to exercise portable readback; current native capture
cannot emit it. JSON Schema alone cannot establish token or semantic fidelity.

## Executed independent evidence

The [Python audit](../../spec/results/proposals/review_p07_julia.py) uses the
standard Draft7 validator with an explicit offline schema registry. It checks
four pairs, ten binary64 probes, 103 structural rejections, five semantic
rejections and 22 numeric rejections. It checks source references by comparison
with the approved manifests. The original read-only `review_p07.py` was also
replayed and passes: it independently verifies the referenced source content
hashes, FIR identities, three analytical sample roundings, two same-FIR source
counterexamples and the accepted original examples. Neither imports production
results code or executes a solver.

The separately authored [Julia audit](../../spec/results/proposals/review_p07_julia.jl)
uses the unchanged pinned independent reference environment, local allowlisted
schema expansion and the independent P01 encoder. It verifies source content
and complete references, normalized FIR digests, hashes, interfaces and direct
observable mappings; three analytical sample roundings; ten binary64 probes;
97 structural, 18 numeric and five semantic rejection controls. Exact rational
neighborhoods independently check nearest/ties-even rounding, including two
midpoint probes. Its lexical checks are bounded numeric converters and scans
of fixed manifest fields, not a general raw JSON parser. No Fenix or Python
runtime and no solver is used by this audit.

Both audits accept Julia positive tolerances below the SciPy floor while
rejecting such Python records. Both exercise limits beyond Int, integer-form
versus binary64 decoding, signed zero, subnormals, overflow and nonzero lexical
underflow. Counts differ because the audits independently choose rejection
controls; the counts are not coverage claims. System `shasum -a 256` separately
checks raw artifact hashes. Receipts retain exact source/schema/catalog/lock
identities and runtime observations in the [machine report](ep03-julia-results-profile.json).

CI runs both proposal audits using existing locked development/reference
environments and uploads separate artifacts. It also replays the original P07
Python audit. No dependency, package version, approved catalog or lock changes.

## Independent review and limitations

Separate engineering and scientific agents reviewed the contract, source
configuration and bounded evidence. Engineering review identified relative
schema references under an opaque URN that the initial custom audit resolver
masked. The correction uses the approved schema's absolute canonical URN;
a standard offline registry now resolves all four examples. The reviewer
rechecked the correction. Scientific review found no blocking scientific
contract issue and confirmed SciML's `nw` denotes W-matrix constructions,
separate from SciPy LU counts. Agent reviews are independent checks, not PI
ratification, human implementation acceptance or biological validation.

Verification outcomes and exact commands are in the machine report. An early
repository check failed while the Julia audit and this evidence document were
still being authored; it is rerun on the complete change. The first sandboxed
Python sync could not obtain setuptools because network/cache access was
restricted; the locked sync succeeded with permitted access. Those failures
were not counted as passes. A Julia audit syntax error during authoring was
corrected before its successful run. No approved value or threshold was weakened.

Native Julia results capture/readback, its proposed 40-sample capture matrix,
solver traps and mutation-isolation tests: **NOT RUN**, because implementation
is gated on approval. Existing package tests are regressions, not implementation
of that gated feature. #29 independent cross-language acceptance, SSA, archives,
signatures, parent epic acceptance and release authorization remain outside this
PR. Checksums establish byte consistency, not execution authenticity or numerical
correctness. No solver rerun was used to generate reference expectations.
