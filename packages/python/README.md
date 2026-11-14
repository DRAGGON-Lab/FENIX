# Python scaffold (not yet a scientific library)

Provisional distribution `fenix-bio` and module `fenix` pending package governance ADR-P06. This package does not have BioIR/FIR APIs, solvers, validated mathematical behavior or Julia dependencies.

    uv sync --project packages/python --locked
    uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v

Smoke tests validate packaging only.
