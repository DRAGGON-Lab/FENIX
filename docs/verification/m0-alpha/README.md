# M0 repository alpha candidate — issue #30

**Status: bounded M0 repository alpha accepted by the human PI.**
The PI separately accepted the [EP-04 parent](../ep04-m0-acceptance.md) on
2026-11-26, based on completed child issues #28–#30. The child evidence and
its original acceptance scope below are retained.
No registry release or package version change is proposed. Package identifiers
remain provisional at `0.0.0` pending P06. This repository candidate is identified
by its reviewed Git revision and artifact checksums, not a new version promise.

## Accepted supported-profile inventory

This inventory summarizes existing ratified rules; it adds no capabilities.

| Boundary | Candidate support and authority |
| --- | --- |
| Authoring | Immutable separate Design and Experiment; exact local verified Design reference; bounded M0 production/degradation under P01 |
| Mathematics | One well-mixed representative-cell molecular-count state, constitutive production and first-order decay; P02 |
| Units | Time seconds, volume litres, intracellular expected molecules per representative cell; no implicit conversions |
| Identity | P03-normalized JCS mathematical FIR and SHA-256 identity; metadata and execution settings excluded |
| Python execution | SciPy DOP853 and Radau; explicit P04 execution settings |
| Julia execution | Direct SciML Tsit5 and Rodas5P; explicit P04 execution settings |
| Results | P07 source-linked results/manifests and ratified Julia supplement; exact result-byte checksums |
| Readback | Python accepts Python/SciPy records; Julia accepts Python/SciPy and Julia/SciML records |
| Tested runtimes | CPython 3.12.13, Julia 1.10.13, uv 0.11.29; committed dependency locks for reproducible evidence |
| Exclusions | SSA, community/spatial/hybrid profiles, implicit conversions, executable serialized callbacks and unsupported biology |

P04 requires finite nonnegative sampled counts, including rejection of negative
subnormals without clipping. Agreement means bounded numerical agreement, not
identical trajectories or result hashes. Hash/source consistency does not prove
authenticated execution or biological prediction. Platform coverage is limited
to actual local/CI receipts; broader declared package compatibility is not a
claim of testing every supported runtime.

## Run and verify

See [paired examples](../../../examples/README.md),
[benchmarks](../../../benchmarks/m0/README.md), and the
[alpha workflow](../../../.github/workflows/m0-alpha.yml) for executable commands.
The workflow builds a Python wheel and extracts a source archive for Julia;
examples run outside the development checkout. Dependency installation can use
network access. After installation, execution uses offline environments.

The independent verifier derives expectations from the unchanged approved
production–decay catalog and #29 reference builder, not either native compiler.
It checks the two scenarios across all four methods, source/model identities,
result checksums and P04 numerical bounds. The existing full FIR and ODE scientific
gates remain required evidence; these two teaching scenarios do not replace them.

## Performance protocol

Each case/method runs in a fresh process, recording package load and first calls
separately from three warmups and twenty measured repetitions. Compilation,
solving an existing FIR, and full result capture are distinct operations. File
writing and independent output checks are outside timing. Full capture includes
its own compilation/validation and must not be described as solver-only time.
Package load excludes interpreter startup and dependency installation.

Raw durations and median/minimum/maximum accompany runtime/dependency versions,
hardware, OS/image, thread settings, workload settings, source/lock fingerprints
and source/FIR identities. CI machines can vary even with a fixed OS label;
actual runner image and CPU receipts identify the observed run. Timings impose
no speed target and support no general Python-versus-Julia superiority claim.
Local and CI results are separate observations. Raw JSON receipts are retained
beside this document; full CI artifacts include emitted result/manifest pairs.

See the executed [verification receipt](verification.md) and retained local/CI JSON reports.

## Merged alpha candidate evidence

[PR #75](https://github.com/DRAGGON-Lab/FENIX/pull/75) merged reviewed head
`566ba94bf1814fdf7bcae10db4ebcbf8688a3b53` at
`ddb298ce85f81e69eb6c6f3b67b1dee9501fb0d5`. Both commits identify tree
`d13d478a67f6050397461f13b70cad4a6fda5634`. All 17 [candidate checks](https://github.com/DRAGGON-Lab/FENIX/commit/566ba94bf1814fdf7bcae10db4ebcbf8688a3b53/checks)
passed. The [alpha run](https://github.com/DRAGGON-Lab/FENIX/actions/runs/45690506447)
published the Python, Julia and comparison artifacts covering both scenarios
and all four native methods.

| Dependency input | SHA-256 at the reviewed tree |
| --- | --- |
| Python uv.lock | `0a02d80325600c4610e8541b3255f5ab7b283438e6bb04c02348a9d2ca00cfb8` |
| Julia native Project.toml | `bc8f951f11988d9443d3960ed02500d4227428f100cf86591d2a11ee56d616ca` |
| Julia native Manifest.toml | `4624b98301546ce12f4b583e7954d3845a70b2b200b0bd11ec70d26059944855` |

## PI decision

In response to the request for PI acceptance of the bounded M0 alpha profile
and evidence at `566ba94bf1814fdf7bcae10db4ebcbf8688a3b53`, the PI stated
“I accept tye bounded M0 alpha”. This covers the profile inventory and bounded
candidate evidence identified above. EP-04 parent acceptance has its own gate.

## Manual release checklist

- [x] Record the exact final candidate commit and source/lock fingerprints.
- [x] Verify independent Python wheel installation and Julia source installation.
- [x] Execute both scenarios with both native methods per language offline.
- [x] Verify source/FIR identity against independent expectations and native parity.
- [x] Verify analytical bounds, result-byte checksums and native readback.
- [x] Retain local and CI raw benchmark receipts with hardware/settings.
- [x] Pass repository/package/reference checks and existing native FIR/ODE gates on the candidate revision.
- [x] Inspect the final `M0 alpha candidate` CI status and downloadable artifacts.
- [x] Record independent engineering/numerical review and any remaining limitations.
- [x] PI approves this bounded supported-profile inventory and candidate evidence at an exact reviewed revision.
- [x] Record PI alpha acceptance for #30.

#28 merged in PR #73. The PI-accepted #29 scientific gate merged in PR #74 at
`ba943e6882e7301f2356139df7010ff141494b7f`; issue tracking may lag this evidence.
Branch-protection activation remains deferred by the PI's single-maintainer
policy. No registry publication, automatic merge, release tag, or parent-epic
closure is authorized by this checklist. Refs #30.
