"""Independently validate native ODE reports before same-study pair comparisons."""

import argparse
import json

from common import read_report, report_destination
from ode_common import compare_ode

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--references", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("reports", nargs=2)
    args = parser.parse_args()
    report = compare_ode(
        [read_report(p) for p in args.reports],
        args.source_revision,
        read_report(args.references),
    )
    path = report_destination(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")
    if not report["passed"]:
        for row in report["failures"]:
            print(json.dumps(row))
        raise SystemExit(1)
    print(
        "PASS: 320 required reference + 320 required pairwise comparisons; 160 coarse comparisons of each kind reported"
    )
