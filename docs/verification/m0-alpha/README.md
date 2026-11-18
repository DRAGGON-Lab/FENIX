# M0 repository alpha candidate — issue #30

**Status: candidate; human PI alpha-profile and release acceptance PENDING.**
No registry release or package version change is proposed. Package identifiers
remain provisional at `0.0.0` pending P06. This repository candidate is identified
by its reviewed Git revision and artifact checksums, not a new version promise.

## Supported-profile inventory for PI approval

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

## Manual release checklist

- [ ] Record the exact final candidate commit and source/lock fingerprints.
- [ ] Verify independent Python wheel installation and Julia source installation.
- [ ] Execute both scenarios with both native methods per language offline.
- [ ] Verify source/FIR identity against independent expectations and native parity.
- [ ] Verify analytical bounds, result-byte checksums and native readback.
- [ ] Retain local and CI raw benchmark receipts with hardware/settings.
- [ ] Pass repository/package/reference checks and existing native FIR/ODE gates on the candidate revision.
- [ ] Inspect the final `M0 alpha candidate` CI status and downloadable artifacts.
- [ ] Record independent engineering/numerical review and any remaining limitations.
- [ ] PI approves this bounded supported-profile inventory and candidate evidence at an exact reviewed revision.
- [ ] Record PI alpha acceptance before closing #30; request EP-04 parent acceptance separately.

#28 merged in PR #73. The PI-accepted #29 scientific gate merged in PR #74 at
`ba943e6882e7301f2356139df7010ff141494b7f`; issue tracking may lag this evidence.
Branch-protection activation remains deferred by the PI's single-maintainer
policy. No registry publication, automatic merge, release tag, or parent-epic
closure is authorized by this checklist. Refs #30.
