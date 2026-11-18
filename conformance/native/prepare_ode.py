"""Prepare independent derived reference artifacts, never native compiler output."""

import argparse
import json

from common import report_destination
from ode_common import make_references, validate_references

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    report = make_references(args.source_revision)
    validate_references(report, args.source_revision)
    path = report_destination(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")
    print("PASS: independently prepared 10 ODE scenarios and 40 approved samples")
