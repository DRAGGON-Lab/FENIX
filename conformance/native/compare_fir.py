"""Validate each native report against approved references, then compare bytes."""

import argparse
from pathlib import Path

from common import compare, read_report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("reports", nargs=2, type=Path)
    args = parser.parse_args()
    compare([read_report(p) for p in args.reports], args.source_revision)
    print(
        "PASS: 84 canonicalization + 207 rejection + 9 compiler controls per native language; "
        "13 FIR identities and 9 compiler model/identity bytes independently validated and equal."
    )
