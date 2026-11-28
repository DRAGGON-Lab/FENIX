"""Read-only independent Draft7/native finite-schema mutation comparison."""

import argparse
import copy
import json
from pathlib import Path
from jsonschema import Draft7Validator
from fenix.community._wire import CommunityValidationError, contract, validate

parser = argparse.ArgumentParser()
parser.add_argument("--root", type=Path, default=Path("."))
args = parser.parse_args()
folder = args.root / "spec/community/wire-candidates/threshold-n1"
report = []
for kind, filename in [
    ("ode-result", "zero.result.json"),
    ("run-manifest", "zero.python.manifest.json"),
    ("bioir", "design.json"),
    ("fir", "fir.json"),
]:
    data = json.loads((folder / filename).read_bytes())
    schema = contract(kind)
    differences = []
    attempts = [0]

    def visit(value, path=()):
        if isinstance(value, dict):
            for key, v in value.items():
                for candidate in (None, True, False, 0, -1, "", [], {}, "x"):
                    changed = copy.deepcopy(data)
                    container = changed
                    for part in path:
                        container = container[part]
                    container[key] = candidate
                    expected = Draft7Validator(schema).is_valid(changed)
                    try:
                        validate(kind, changed)
                        actual = True
                    except CommunityValidationError:
                        actual = False
                    attempts[0] += 1
                    if expected != actual:
                        differences.append(
                            [list(path + (key,)), repr(candidate), expected, actual]
                        )
                visit(v, path + (key,))
        elif isinstance(value, list):
            for index, v in enumerate(value):
                visit(v, path + (index,))

    visit(data)
    report.append(
        dict(
            schema=kind,
            mutations=attempts[0],
            differences=differences,
            status="PASS" if not differences else "FAIL",
        )
    )
print(json.dumps(report, indent=2))
assert all(not row["differences"] for row in report)
