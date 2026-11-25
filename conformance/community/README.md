# Candidate ADR-P08 analytical references

Status PROPOSED for #34. The PI approved reviewed ADR-P08 in PR #77.
These references require their own scientific acceptance.

Python Decimal and Julia BigFloat independently evaluate fifteen samples.
Four constant-density cases cover Hill exponents 1 through 4 at threshold.
Both strains have unequal cell volumes and asymmetric import/export rates,
with zero net exchange. The reporter solves y'=2-y/2 with y(0)=0.
A fifth case exercises sender/environment exchange with a disconnected receiver.
Its laws are s=12/5+(8/5)exp(-5t/2), E=144/5-(24/5)exp(-5t/2),
r=2 and y=0. Populations are 3 and 5, giving weighted signal 46.
All cases use times 0, 1 and 4 seconds.

Python computes at 80 and 160 decimal digits. Julia computes at 512 and 1024
bits, derives E first and recovers s through conservation. Both check refinement.
Cross-evaluator agreement uses 1e-150 max(1, |reference|). This bound applies
to reference calculations. Native solver tolerances need their own evidence.
Python also exercises exact rational zero/threshold Hill responses, increased
signal and dilution, and checks the transient weighted balance.

Run Python reference.py to write a JSON report, then run reference.jl with
that report path using the conformance/julia project. Neither script imports FENIX.

Python checks passed locally. Julia was NOT RUN locally because the previous
temporary runtime is unavailable. The candidate CI job installs pinned Julia.
The report is an observation of independent calculations and has candidate status.

Changing extracellular density driving reporter dynamics, full native method
feasibility, complete source/profile rejections, and canonical identity vectors
remain required follow-on evidence. This bounded contribution covers analytical
special cases. Issue #34 remains open.
