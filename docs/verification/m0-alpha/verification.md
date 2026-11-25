# Local verification receipt

Implementation source: `bd1b291` (first implementation commit), based on merged
#29 `ba943e6`. The eight `local-*.json` receipts were generated before committing,
so they declare base revision `ba943e6882e7301f2356139df7010ff141494b7f` and retain
complete source/lock fingerprints identifying the implemented contents. All eight
share identical fingerprints. They are local observations, not golden references.
Fresh-install receipts additionally identify the selected committed archive.

Environment: macOS x86_64, CPython 3.12.13, Julia 1.10.13, uv 0.11.29.
Local Julia used `/private/tmp/julia-1.10.13/bin/julia` with an existing depot for
native regressions; the source-archive installation uses a separate fresh depot.
Every raw report includes the actual CPU, OS, thread settings and dependencies.

## Median warmed durations (milliseconds)

Each phase has 3 warmups and 20 measured repetitions. First-call and package-load
observations and all raw samples are in the corresponding JSON reports. Do not
compare these measurements as a general language performance ranking.

| Language | Case | Method | Compile | Solve | Full capture |
| --- | --- | --- | ---: | ---: | ---: |
| julia | baseline-five | Rodas5P | 3.8281 | 0.8589 | 8.2125 |
| julia | baseline-five | Tsit5 | 4.1256 | 0.6703 | 8.4389 |
| julia | linear-production | Rodas5P | 5.2065 | 0.6281 | 7.4811 |
| julia | linear-production | Tsit5 | 6.7666 | 0.7202 | 9.7089 |
| python | baseline-five | DOP853 | 2.3004 | 21.2736 | 25.0367 |
| python | baseline-five | Radau | 2.6503 | 180.6391 | 199.3992 |
| python | linear-production | DOP853 | 2.6041 | 2.9213 | 11.3291 |
| python | linear-production | Radau | 2.6178 | 8.5977 | 16.6560 |

## Executed checks

| Check | Result |
| --- | --- |
| Locked Python install (`uv sync --project packages/python --locked`) | PASS after cache sandbox escalation |
| Repository checker and `unittest discover -s scripts/tests -v` | PASS; 6 harness tests |
| `unittest discover -s packages/python/tests -v` | PASS; 88 package tests |
| Standalone Julia `Pkg.instantiate(); Pkg.test()` | PASS |
| Native Python FIR suite; strict mypy | PASS; 3 catalog/control tests, 14 typed source modules |
| Both native FIR producers and independent comparator | PASS; 300 rows/language, 13 reference identities and 9 producer models |
| Both native ODE producers and independent comparator | PASS; 60 runs/240 samples per language, 320 required reference and 320 pairwise comparisons |
| `unittest discover -s conformance/native/tests -v` | PASS; 29 gate regressions |
| All example case/method executions and saved readbacks | PASS; eight combinations, exact independent source/model/identity bytes |
| Both native full benchmark matrices | PASS; eight combinations |
| Benchmark failure controls | PASS; 4 Python tests, 11 Julia assertions |
| `unittest discover -s scripts/m0_alpha/tests -v` | PASS; 7 verifier regressions |
| Ruff check/format; `git diff --check` | PASS |
| Fresh archived Python wheel install and full matrix | PASS at bd1b291 |
| Fresh Julia archive installation and full matrix | PASS at bd1b291; empty depot, offline example execution |
| Hosted alpha CI | PASS at bd1b291; [run 44423030522](https://github.com/DRAGGON-Lab/FENIX/actions/runs/44423030522); final head assessed separately |
| Human PI alpha-profile/release acceptance | NOT RUN; pending explicit reviewed-candidate acceptance |

Earlier failures are retained in this receipt: initial uv installation could not
write its default cache in the sandbox and succeeded after escalation. Initial
Julia script entrypoint guards required parentheses and were corrected before
successful smoke tests. A preliminary benchmark test command targeted a directory
that did not exist; the documented `discover -s benchmarks/m0` passed. Initial
verifier formatting was corrected. Engineering review found archive-wheel source
selection ambiguity, corrected before the implementation commit. Numerical review
found unchecked FIR transport source digests; a new corruption test failed before
the verifier correction and passed afterward. No scientific threshold, production
API, approved fixture or dependency lock was changed to pass these checks.

Across-ownership engineering review found no remaining blocking issue after the
archive fix. Across-ownership numerical review checked oracle bounds and artifact
coverage and identified the corrected provenance gap. Agent review is not human
scientific or release acceptance.


## Retained CI baseline

The eight `ci-*.json` reports are from successful alpha run
[44423030522](https://github.com/DRAGGON-Lab/FENIX/actions/runs/44423030522)
on implementation commit `bd1b29170cf3964aa73df7626b9cef36328fd76f`.
These are Ubuntu 24.04 runner observations; actual image and CPU are in each raw
report. They remain separate from the macOS local baseline. Source revisions in
reports can identify GitHub's tested PR merge revision; fingerprints bind the
actual package/driver/lock contents. The final verifier provenance regression
changes no benchmark or native source fingerprint.

Both local archived producers and all eight artifact/benchmark combinations
also passed the strengthened independent verifier after the provenance fix.
An initial manually copied revision argument was malformed and rejected;
deriving it with `git rev-parse bd1b291` succeeded. Artifact download initially
failed during its storage redirect; a fresh redirect without forwarding GitHub
authentication retrieved all eight reports. No missing result was counted as PASS.

## Follow-up review of the alpha verifier

The PI approved PR #75 at revision `53415f1a21cf6117cbd64ad7f94f6884db7fbe23`
in the working conversation. The subsequent verifier correction addresses the
[provenance review finding](https://github.com/DRAGGON-Lab/FENIX/pull/75#discussion_r4622682981).
The independent rejection reference checks the FIR envelope and its source
mappings. The alpha verifier also matches the compiler and manifest producer to
the native package metadata.

Local regression verification passed all eight alpha verifier tests. Before
the correction, all ten new corruption cases passed verification incorrectly
after their artifact checksums were recomputed. The corrected verifier rejects
all ten and accepts reordered parameter mappings and a valid observable label.
The corrected candidate requires review against its own revision.
