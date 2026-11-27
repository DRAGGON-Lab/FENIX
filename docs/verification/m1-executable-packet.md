# M1 executable review packet — implementation handoff

Refs #31 and #34. Base `61395717984a9f7a5000eadb0ce37bb6b0b1a5f3`, containing
merged PR #94 and the PI's bounded completion-scope decision. This change
implements the executable review prerequisites that remain explicitly ahead of
native #32/#33 in the approved delivery plan. It records no new PI approval.

Scope: `spec/community/` candidate schemas, validators, literal positive and
rejection/identity catalogs, independent ECMAScript identity audit; independent
Julia feasibility probe under `conformance/community/feasibility/`; additional
community CI jobs and navigation/documentation. No native package API, accepted
fixture, original ten-case reference, numerical setting, P08 equation, M0/P10
format or package dependency is changed. No issue closure or merge is requested.

The [complete profile proposal](../../spec/community/executable-profile-proposal.md)
specifies the finite source/FIR formats, source correspondence, numeric policies,
version-specific normalization and scoped result/backend contracts. The
[literal catalog](../../spec/community/wire-candidates/README.md) contains 14
positive packets, 56 rejection witnesses and 17 lexical projections. Schema and
byte artifacts are candidate expectations for independent review, not accepted
golden values. The analytical result/manifest examples are explicitly
illustrative, not source-linked evidence of native solver execution.

The [artifact manifest](../../spec/community/review-manifest.json) fingerprints
the complete contract/candidate/tool set, unchanged analytical references,
frozen settings and dependency locks. The wire auditor verifies these hashes
before processing the catalog. Exact-revision review must include that manifest
and the separately revision-bound hosted numerical receipts.

| Unchanged reference artifact | SHA-256 |
|---|---|
| `conformance/community/cases.json` | `af83c53f942e21b63f87519b8540145e627c9082462fc9aeb3d9937329c6aa6b` |
| `conformance/community/reference.py` | `075e9dd3207a0d45bf5665ea17f0cd581d6ad2aa76252db0c5c6dcdf2167630f` |
| `conformance/community/reference.jl` | `04c7712400cbc4512ca06454e7215085b1e310dc929e628dc89fd230e654729b` |
| `conformance/community/feasibility/settings.json` | `a39091f231a5b101c1e430d53eec6327e337b0e3f04a2870473bcfbc64ef3fc8` |

## Verification

| Check | Outcome |
|---|---|
| Eight wire-packet control tests | PASS locally |
| Python literal validator / analytical sample mapping | PASS locally — all 87 catalog rows |
| Independent ECMAScript source/model/identity bytes | PASS locally — 14 positive packets |
| Every rate/count/population/volume changes mathematical identity | PASS locally |
| Reaction/equation AST vs independent laws and asymmetric open-system probes | PASS locally |
| Ruff on new Python review/writer/test files | PASS locally |
| Repository checker, harness and existing Python package regressions | PASS locally — checker / 6 harness / 88 package tests |
| Original community and retained SciPy feasibility suites | PASS locally — 8 reference / 9 feasibility tests |
| Julia stage feasibility and kernel derivative regressions | NOT RUN locally — runtime unavailable; hosted result pending |
| Native M1 authoring/compile/solve/capture/readback and clean installations | NOT RUN — exact packet acceptance pending |

Local Python environment uses locked dependencies, Python 3.12.16 and uv 0.13.10;
CI pins Python 3.12.13, uv 0.11.29, Node 22 and Julia 1.10.13. The Julia probe
loads SciML package identities from the unchanged pinned conformance environment
without importing Fenix or calling Python. It uses independently written
count-balance RHS/Jacobian, checks derivatives using 512-bit differences and
checks 40 bounded integrations/120 samples against the independent 1024-bit
BigFloat laws. Reports retain exact source/lock hashes, observed versions,
sample errors, weighted-balance bounds, first domain failures and work counts.

Julia tail outcomes are observations, not copied SciPy expectations. The strict
failure scope already approved by the PI remains intact. A missing or failing
hosted Julia result leaves method feasibility open. No passing wire test can
substitute for that evidence or for exact-revision human acceptance.

## Remaining human and native gates

The PI must accept the exact reviewed packet, its literal input/identity/
rejection artifacts, unchanged ten analytical definitions/30 samples and full
bounded numerical evidence/criteria. The existing approval of completion scope
does not supply this separate decision. After acceptance, Python #32 proceeds
first, then Julia #33, then independent integration/installation gate #35.
Oscillator delivery #84 and its separate P10 contract remain downstream.
