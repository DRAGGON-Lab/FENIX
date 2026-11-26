#!/usr/bin/env bash
set -euo pipefail
# Run at repository root. Every executed example imports the installed wheel.
revision=${1:?full source revision required}
output=${2:?absolute output directory required}
root=$PWD
base=${ALPHA_WORK_ROOT:-/tmp}
archive=$base/fenix-alpha-python
wheel=$base/fenix-alpha-wheel
test ! -e "$archive"
test ! -e "$wheel"
mkdir -p "$archive" "$output"
git archive "$revision" | tar -x -C "$archive"
cd "$archive"
unset PYTHONPATH
uv build --project packages/python
uv venv --python 3.12.13 "$wheel"
uv export --project packages/python --locked --no-dev --no-emit-project -o "$archive/runtime.txt"
uv pip install --python "$wheel/bin/python" --require-hashes -r "$archive/runtime.txt"
uv pip install --python "$wheel/bin/python" --no-deps packages/python/dist/*.whl
"$wheel/bin/python" -I -c 'import fenix, pathlib, sys; assert pathlib.Path(fenix.__file__).resolve().is_relative_to(pathlib.Path(sys.prefix).resolve())'
"$wheel/bin/python" -m unittest discover -s benchmarks/m0 -p test_benchmarks.py -v
for case_id in baseline-five linear-production; do
  for method in DOP853 Radau; do
    directory="$output/python/$case_id/$method"
    "$wheel/bin/python" examples/m0/production_decay.py --case "$case_id" --method "$method" --output-dir "$directory"
    "$wheel/bin/python" examples/m0/source_revisions.py --case "$case_id" --method "$method" --output-dir "$output/source-revisions/python/$case_id/$method"
    "$wheel/bin/python" benchmarks/m0/run.py --case "$case_id" --method "$method" --source-revision "$revision" --output "$directory/benchmark.json"
  done
done
test "$root" != "$PWD"
