# Candidate ADR-P08 analytical references

Status PROPOSED for #34. The PI approved reviewed ADR-P08 in PR #77.
The explicit [case inputs](cases.json) identify all rates, initial states,
populations, volumes, units and sample times. State ordering follows the catalog.
Each case includes all parameters, including zero rates on connected ports.
The population and volume entries follow sender, receiver and environment order.
A molecule/s parameter has the per-cell basis of its owner. Intracellular states
are per representative cell and the environment state is a total count.

## Analytical laws

Python Decimal and independently authored Julia BigFloat scripts evaluate thirty
samples from ten cases, at times 0, 1 and 4 seconds.

- Four equilibrium cases cover Hill exponents 1 through 4 at threshold. Unequal
  cell volumes and asymmetric import/export rates yield zero net exchange. The
  reporter solves y'=2-y/2 with y(0)=0, giving y=4(1-exp(-t/2)).
- A sender/environment exchange case has a disconnected receiver. Its laws are
  s=12/5+(8/5)exp(-5t/2), E=144/5-(24/5)exp(-5t/2), r=2 and y=0. Populations
  3 and 5 give the constant weighted signal 46.
- Four driven-reporter cases use E=48 exp(-t/2), K=2, V_e=12, beta=n/2,
  basal production 1, induced production 4 and y(0)=2. Let A=2^n and q=exp(-beta t).
  Integrating y'+beta y=1+4 H gives
  y=2q+(1-q)/beta+(4 A q/beta) log((exp(beta t)+A)/(1+A)).
  Python evaluates the growing exponential and logarithmic ratio. Julia uses
  log1p and the decaying exponential. Signal density crosses K between times
  1 and 4. Both strains have zero transfer rates in these isolated sensing cases.
- A two-strain transient has all four exchange rates equal to 1/s. Its volumes
  are 2, 3 and 12 L, populations 3 and 5, and initial counts 8, 12, 24 and 0.
  Initial intracellular densities coincide. For z=exp(-11t/4), the solution is
  s=(72+16z)/11, r=(108+24z)/11 and E=(432-168z)/11, giving total signal 108.
  Julia derives E first and recovers both cellular counts through mass balance.

## Checks and limits

Python computes at 80 and 160 decimal digits. Julia computes at 512 and 1024
bits. Both check refinement. Cross-evaluator agreement uses
1e-150 max(1, |reference|). This bound applies to reference calculations.
Native solver tolerances need their own evidence.

Python checks the initial states and independently differentiates the closed-form
laws using a central difference at 160 decimal digits, with h=1e-40 and a
1e-65 scaled residual bound. This connects each law to the fully specified case
inputs. Tests corrupt kinetic rates and initial conditions to verify detection.
Exact arithmetic checks cover open-system source/loss balance, read-only sensing,
population scaling, zero/threshold Hill responses, increased signal and dilution.
Missing population multipliers and inverted environmental signs supply explicit
nonconservative counterexamples.

Julia requires the complete ordered sample set and four finite nonnegative state
entries in every row. It verifies the catalog fingerprint before comparison.
Regression controls reject missing rows, truncated/empty rows, nonfinite/negative/
wrong counts, a Boolean time, stale catalog identity and invalid refinement data.

Run from the repository root

```sh
python3 -m unittest discover -s conformance/community -v
python3 conformance/community/reference.py > /tmp/community-reference.json
julia --project=conformance/julia -e 'using Pkg; Pkg.instantiate()'
julia --project=conformance/julia conformance/community/reference.jl /tmp/community-reference.json
julia --project=conformance/julia conformance/community/test_reference.jl /tmp/community-reference.json
```

Use Python 3.12.13 and Julia 1.10.13. The scripts import no native FENIX modules.
Python reference checks, its three regression tests and Ruff passed locally.
Julia execution is delegated to the pinned CI runtime because the previous local
runtime is unavailable. Candidate CI retains the raw Python report and compares
it with independently derived Julia values. Full numerical-stage feasibility,
complete source/profile rejections and canonical identity vectors retain the
ADR's further gates. This catalog establishes analytical special-case coverage.
