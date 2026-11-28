"""Produce native Python artifacts or verify Julia artifacts through Python readback."""

import argparse
import hashlib
import json
from itertools import product
from pathlib import Path

from fenix.community import (
    Design,
    Experiment,
    RunRecord,
    compile_experiment,
    run_experiment,
)
from fenix.execution import ODEExecutionSpec

METHODS = {"python": ("DOP853", "Radau"), "julia": ("Tsit5", "Rodas5P")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("produce", "read"))
    parser.add_argument("root", type=Path)
    parser.add_argument("exchange", type=Path)
    parser.add_argument("revision")
    args = parser.parse_args()
    inputs = args.root / "spec/community/wire-candidates"
    catalog = json.loads((args.root / "conformance/community/cases.json").read_bytes())
    settings = json.loads(
        (args.root / "conformance/community/feasibility/settings.json").read_bytes()
    )
    rows = []
    source = "python" if args.mode == "produce" else "julia"
    for case in catalog["cases"]:
        folder = inputs / case["id"]
        design = Design.from_json((folder / "design.json").read_bytes())
        experiment = Experiment.from_json(
            (folder / "experiment.json").read_bytes(), design=design
        )
        fir = compile_experiment(experiment)
        for method, setting in product(METHODS[source], settings["settings"]):
            key = f"{case['id']}/{method}/{setting['id']}"
            output = args.exchange / key
            if args.mode == "produce":
                output.mkdir(parents=True, exist_ok=False)
                spec = ODEExecutionSpec(
                    time_grid=tuple(map(float, case["times"])),
                    method=method,
                    rtol=setting["rtol"],
                    atol=setting["atol"],
                    max_step=settings["reference_max_step"],
                    max_nfev=settings["max_rhs_calls"],
                )
                record = run_experiment(experiment, spec)
                for name, data in (
                    ("model.jcs", fir.model_bytes()),
                    ("identity.jcs", fir.identity_bytes()),
                    ("result.json", record.result_bytes),
                    ("manifest.json", record.manifest_bytes),
                ):
                    (output / name).write_bytes(data)
            else:
                raw = (output / "result.json").read_bytes()
                manifest = (output / "manifest.json").read_bytes()
                record = RunRecord.from_json(raw, manifest, experiment=experiment)
                assert record.result_bytes == raw and record.manifest_bytes == manifest
                assert fir.model_bytes() == (output / "model.jcs").read_bytes()
                assert fir.identity_bytes() == (output / "identity.jcs").read_bytes()
            rows.append(
                {
                    "key": key,
                    "result_sha256": hashlib.sha256(record.result_bytes).hexdigest(),
                    "manifest_sha256": hashlib.sha256(
                        record.manifest_bytes
                    ).hexdigest(),
                    "fir_digest": fir.digest,
                }
            )
    report = {
        "runtime": "python",
        "mode": args.mode,
        "source_revision": args.revision,
        "rows": rows,
    }
    (args.exchange / f"python-{args.mode}.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(f"PASS native Python {args.mode}: {len(rows)} records")


if __name__ == "__main__":
    main()
