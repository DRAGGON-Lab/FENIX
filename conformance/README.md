# Scientific conformance fixtures — pending

Planned independent analytical production/degradation reference, invalid/unsupported-model cases, canonicalization vectors, community conservation, numerical validation and restricted SSA distribution-level tests. Golden expectations require human scientific approval; neither compiler may solely generate its own expected values. Passing package smoke tests is not scientific conformance.

Development tools are available through Python's locked development group and
the separately pinned [Julia environment](julia/README.md). These environments
provide tooling only; no normative fixtures or scientific validators exist yet.
