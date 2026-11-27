# Accepted bounded nonlinear-cycle reference definitions

This study advances [issue #84](https://github.com/DRAGGON-Lab/FENIX/issues/84)
under the [ratified P09 equations](../../../spec/oscillators/ADR-P09.md).
The PI **accepted the bounded numerical reference definitions** at reviewed
commit `0ee6b42`; see the
[explicit decision](../../../docs/verification/p09-nonlinear-reference-acceptance.md).
It supplies neither certified error intervals nor accepted native tolerances.
No native FENIX profile is executed.

The original feasibility methods share SciPy and one count-space RHS. This
evaluator imports neither SciPy nor FENIX nor that RHS/Jacobian/classifier.
It independently derives density-coordinate equations and implements classical
fourth-order explicit Runge–Kutta with fixed steps. Both calculations still use
binary64, NumPy and the same reviewed model definitions; algorithm/coordinate
independence does not establish biological validity or eliminate shared errors.

## Independent coordinates and reference checks

Divide every intracellular count, including transcripts and proteins, by its
owner's constant volume. Divide medium totals by medium volume. Write transcript
and protein densities as u_i and w_i, intracellular signal densities as q_jk and
medium densities as e_k. P09 then gives

    u_i' = (b_i + h_i G_i(c_i))/v_i - gamma_m,i u_i
    w_i' = beta_i u_i - gamma_p,i w_i
    q_jk' = indicator(j=k) sigma_k w_k - gamma_a,jk q_jk
            - k_out,jk q_jk + k_in,jk e_k
    e_k' = sum_j (N_j v_j/V_e)(k_out,jk q_jk - k_in,jk e_k)
           - gamma_e,k e_k.

The single-cell sensor is w_prev(i); the community sensor is q_i,prev(i).
Medium transport therefore uses volume fractions weighted by population; no
volume conversion occurs in an intracellular density exchange term. Convert
back to counts only at output. This is a coordinate transformation of the
ratified mathematics, not new density-based BioIR/FIR semantics or units.

Before cycle integration, check all 11 independently derived analytical component
cases/33 samples (414 state/time comparisons) using step 1/256 s over four seconds.
The complete analytical catalog is pinned before evaluation. The comparison uses
the existing candidate bound `1e-9 + 1e-8*abs(analytical)`; its use here does not
approve a native solver tolerance. During development, step 1/64 s failed the
translation check (maximum error/bound 8.36); 1/128 and 1/256 reduced it to 0.513
and 0.032. The bound and reference values were preserved.

The complete primary-study catalog bytes are separately pinned. Any catalog
mutation, including whitespace, requires review of the pin. This evaluator is
bounded to those primary definitions and the analytical test definitions. It
does not offer a new general parser or validator. Nonlinear sensor stages must
be nonnegative; signed linear stages follow P09. Invalid/nonfinite returned
counts, unaligned grids and exhausted fixed-step budgets fail without clipping
or method substitution.

## Run and inspect

From repository root, after the existing locked study environment setup:

```sh
uv run --project conformance/oscillators --locked --offline python -m unittest discover -s conformance/oscillators/nonlinear -v
uv run --project conformance/oscillators --locked --offline python conformance/oscillators/study.py --output-dir artifacts/p09-density-comparison
uv run --project conformance/oscillators --locked --offline python conformance/oscillators/nonlinear/rk4.py --study-dir artifacts/p09-density-comparison --output-dir artifacts/p09-density-comparison/independent-rk4
```

Outputs must be new; checkout outputs must be under `artifacts/`. All four fixed
steps (2.5, 1.25, 0.625 and 0.3125 seconds) cover the full 80,000-second horizon
for each primary model, saving count-space traces at every five seconds.
The eight compressed CSVs have explicit time/state headers. `report.json`
retains the complete definitions, catalog/source/lock/input-report hashes,
environment versions, work counts, trace checksums, per-state step differences,
observed refinement orders and comparisons with all eight adaptive traces.

The candidate check requires successive maximum amplitude-scaled step differences
to decrease and the final difference to be at most 1e-5. Each adaptive comparison
must also be at most 1e-5, using max(1, peak absolute count) per state over the
whole trace. These investigation limits are accepted for this bounded reference
study; they are not error proofs or accepted native thresholds. Observed orders are reported without assuming
every coarse step lies in an asymptotic fourth-order regime. A decreasing gap
alone does not certify distance to the exact solution.

Independent linearly interpolated midpoint upcrossings report periods and count
extrema in both original analysis windows. They are observations, not a second
sustained-oscillation classifier. The original damped/drifting/broken-channel
controls and all existing feasibility gates remain required.

The input loader checks the exact source/catalog context, all expected run keys,
primary filenames, checksums, column metadata/headers, dimensions, complete grid,
initial states and finite nonnegative values. Integrity checks do not authenticate
execution. A plausible altered trace with recomputed checksums can pass those
transport checks; the independent numerical comparison must still reject it.
Tests exercise that distinction, wrong metadata/source/grids, duplicate runs,
numeric-domain failures, exact weighted-balance derivatives, population/volume
replication, read-only sensing, known fourth-order linear convergence and
synthetic cycle/no-cycle traces.

This reference study does not replace accepted component laws, M0 or M1 evidence.
The accepted scope includes the two primary definitions, four-step protocol and
1e-5 investigation limit. Certified error bounds, native tolerances, complete
wire/identity/rejection contracts, native Python/Julia implementation and its
acceptance remain separate. Historical PROPOSED labels in the byte-pinned inputs
and generated reports are preserved. No issue completion or release is implied.
