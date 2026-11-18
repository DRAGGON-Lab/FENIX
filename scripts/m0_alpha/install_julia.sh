#!/usr/bin/env bash
set -euo pipefail
# No Python runtime or LOAD_PATH overrides are used in this producer.
revision=${1:?full source revision required}
output=${2:?absolute output directory required}
base=${ALPHA_WORK_ROOT:-/tmp}
archive=$base/fenix-alpha-julia
test ! -e "$archive"
mkdir -p "$archive" "$output"
git archive "$revision" | tar -x -C "$archive"
export JULIA_DEPOT_PATH=$base/fenix-alpha-julia-depot
test ! -e "$JULIA_DEPOT_PATH"
unset JULIA_LOAD_PATH
cd "$archive"
# First prove standalone package dependency resolution in a fresh depot.
julia --project=packages/julia -e 'using Pkg; Pkg.instantiate()'
JULIA_PKG_OFFLINE=true julia --project=packages/julia -e 'using Fenix; @assert startswith(realpath(pathof(Fenix)), realpath("packages/julia")*"/")'
JULIA_PKG_OFFLINE=true julia --project=packages/julia examples/m0/production_decay.jl --case baseline-five --method Tsit5 --output-dir "$output/julia-standalone"
# Benchmarks use the existing Pkg-generated locked native environment.
julia --project=conformance/julia_ode -e 'using Pkg; Pkg.instantiate()'
export JULIA_PKG_OFFLINE=true
julia --project=conformance/julia_ode benchmarks/m0/test_checks.jl
for case_id in baseline-five linear-production; do
  for method in Tsit5 Rodas5P; do
    directory="$output/julia/$case_id/$method"
    julia --project=conformance/julia_ode examples/m0/production_decay.jl --case "$case_id" --method "$method" --output-dir "$directory"
    julia --project=conformance/julia_ode benchmarks/m0/run.jl --case "$case_id" --method "$method" --source-revision "$revision" --output "$directory/benchmark.json"
  done
done
