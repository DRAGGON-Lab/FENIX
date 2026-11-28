"""Require the independent comparison to catch trace and state corruption."""

import argparse
import json
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from compare import compare, load, sha


def stamp(path, data):
    path.write_text(json.dumps(data) + "\n")


def require_rejection(root, exchange, revision, expected):
    try:
        compare(root, exchange, revision)
    except AssertionError as error:
        if expected:
            assert error.args and error.args[0][:2] == expected, error
    else:
        raise AssertionError("corrupted native evidence passed the comparison")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("exchange", type=Path)
    parser.add_argument("revision")
    args = parser.parse_args()
    with TemporaryDirectory() as path:
        copied = Path(path) / "exchange"
        shutil.copytree(args.exchange, copied)
        peer_path = copied / "julia-read.json"
        unmodified = peer_path.read_bytes()
        peer = load(peer_path)
        peer["rows"].pop()
        stamp(peer_path, peer)
        require_rejection(args.root, copied, args.revision, None)
        peer_path.write_bytes(unmodified)

        key = "threshold-n1/DOP853/baseline"
        folder = copied / key
        result_path = folder / "result.json"
        manifest_path = folder / "manifest.json"
        result, manifest = load(result_path), load(manifest_path)
        signal_column = result["state_ids"].index("sender.signal")
        result["state_values"][1][signal_column] += 1.0
        stamp(result_path, result)
        manifest["output"]["sha256"] = sha(result_path)
        stamp(manifest_path, manifest)
        # Synchronize the trace hashes to isolate numerical disagreement.
        for report_name in ("python-produce.json", "julia-read.json"):
            report_path = copied / report_name
            report = load(report_path)
            row = next(row for row in report["rows"] if row["key"] == key)
            row["result_sha256"], row["manifest_sha256"] = (
                sha(result_path),
                sha(manifest_path),
            )
            stamp(report_path, report)
        require_rejection(args.root, copied, args.revision, (key, 1))
    print("PASS missing peer receipt and rehashed state corruption rejected")


if __name__ == "__main__":
    main()
