# Proposed independent P10 equation audit

This [issue #84](https://github.com/DRAGGON-Lab/FENIX/issues/84) follow-up checks
the proposed P10 FIR mathematics independently of its schema/example builders.
It is **PROPOSED bounded mathematical evidence**, not PI ratification, a native
implementation, an accepted new golden catalog or empirical biological validation.
The [P10 structural audit](examples/README.md) retains its separate scope.

## What is compared

`equation_audit.py` imports no FENIX, SciPy, NumPy, schema, example writer or
`wire_shapes` code. It reads the two literal candidate FIR models and evaluates
their reaction fluxes/signed updates and explicit RHS trees separately. The
small operation whitelist handles only the P10 data operations, with no `eval`,
serialized callback, arbitrary module selection or reaction-to-flux recursion.
It is a reference-only evaluator, not a new public expression language.

Expected derivatives come from the separately authored P09 count-space equations
in `conformance/oscillators/references/reference.py`, whose complete bytes are
pinned before loading. Its component-reference catalog is also pinned. Those
reference definitions have prior bounded PI acceptance; using their equation
code for the new P10 audit does not expand that acceptance automatically.
P09's ratified equations, quantities and domain policy remain the scientific rule.

The audit checks fifteen definitions:

- The exact two primary P09 case definitions, with values projected independently
  into the P10 parameter/geometry/population/initial-state roles. No expected
  numeric value is taken from the proposed model itself.
- All eleven analytical component cases through in-memory numeric rebindings
  of the same candidate ASTs. Their known states at t=0,1,4 are queried alongside
  four algebraic points. These are RHS evaluations, not numerical integration.
- Two complete [asymmetric input definitions](equation-probes.json), which remain
  proposed controls. Their differing rates, Hill exponents/thresholds, volumes,
  populations and signal counts expose dependencies concealed by symmetric data.

Numeric rebindings never rewrite the source catalogs, candidate FIR files or
approved fixtures. They do not claim those new views have accepted wire identities.
Every input scalar is interpreted as represented binary64, then lifted exactly
with `Decimal.from_float`. In particular, binary64 0.1 is not the exact decimal
real 0.1. The component input rates/geometry are binary-exact half-integers and
integers, so their accepted closed forms retain their reference definitions.
The output records each projected binary64 input in hexadecimal notation.

Reference vector names are mapped explicitly to canonical P10 IDs; the audit
never assumes the study's m/p/a/e position equals canonical a/e/m/p order.
Scalar values, scopes, units and quantity roles are checked before comparison.
Declaration permutations therefore do not change this mathematical comparison.

## Checks and proposed precision criterion

Both Decimal precisions, 80 and 160 digits, check:

1. Reaction-update sums versus the independent P09 RHS.
2. Explicit FIR equation RHS versus P09 and versus reaction-update sums.
3. The full population-weighted signal source/loss balance for each community
   signal, evaluated independently from synthesis and degradation roles.
4. Precision refinement of each equation vector between the two calculations.

The proposed algebra/precision criterion is scaled difference at most 1e-65,
with scale max(1, absolute expected derivative). This measures high-precision
arithmetic consistency; it is **not a native solver tolerance or trajectory bound**.
There are 186 precision/probe vectors and 2,316 state values per comparison path.
The report retains the complete input definitions, ID-mapped query counts, both
AST outputs, P09 derivatives, errors, precisions and code/catalog/FIR fingerprints.

Separately, `Fraction` arithmetic checks each transport reaction's signed
population-weighted coefficient for each of the three signals. All 432 checks
across the eight community definitions must be exactly zero, independent of
flux values or floating-point cancellation. Nonlinear sensing rejects negative
sensor stages; signed linear stages remain allowed under P09. No counts are clipped.

## Failure controls and limits

Nine tests cover wrong ring direction/medium sensing, catalytic sinks, wrong
synthesis target, swapped transport parameters, explicit-equation errors,
unweighted/wrong-sign population updates, exact input projection, source pins,
unknown operations/fields, forbidden flux recursion, stage domains and ID mapping.

One control deliberately keeps a wrong update and its RHS consistent. With the
primary community's three equal populations, wrong owner N_2 in place of N_1
has no numerical effect. The accepted heterogeneous closed-transport case rejects
it exactly. Wrong volume owner, transposed transport rate and wrong threshold
likewise pass at symmetric primary values and fail with asymmetric rebindings.
This demonstrates why primary trajectory agreement alone cannot establish role
correctness. The unmodified candidate passes all checks.

Mathematical agreement does not establish the serialized contract: a commuted
product can pass this audit while P10's exact template/identity rules reject it.
This audit neither normalizes nor assigns canonical identity, and finite probes
do not prove a general algebraic equivalence theorem. Raw-token, schema,
source-provenance, byte-vector, positive-time result, backend and native execution
requirements still need their own evidence and human approval.

## Run and inspect

The audit needs only Python 3.12's standard library and the fixed repository
reference source. From repository root:

```sh
python -m unittest discover -s spec/oscillators -p test_equations.py -v
python spec/oscillators/equation_audit.py --output /tmp/p10-equation-audit.json
```

The output must be new. Both commands also run under the locked Python package
environment if that is the selected interpreter. The dedicated CI context is
`Candidate P10 equation audit (not native conformance)`; its artifact is
`proposed-p10-equation-audit`. Original structural, numerical, native package,
FIR/ODE and installation checks remain enabled. Julia execution is not supplied
by this audit, and native oscillators remain **NOT RUN — unsupported profile**.
