"""M0 observations, not performance targets. Run one case/method per process."""

import argparse
import hashlib
import json
import math
import os
import platform
import runpy
import statistics
import subprocess
import time
from decimal import Decimal, localcontext
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Verbatim bounded decimal references from the APPROVED production-decay catalog.
EXPECTED = {
    "baseline-five": (
        "5.0000000000000000000000000000000000000000000000000E+0",
        "1.4040445286583840498309275603109457596127989442110E+1",
        "6.5051453088712977879485320987896138779345130140148E+1",
        "9.9995687006672558390635208165519821728469934817363E+1",
    ),
    "linear-production": ("0.5", "1.5", "2.5", "20.5"),
}


def validate_values(case, values):
    """Apply unchanged P04 B at 100 decimal digits, outside timed regions."""
    if len(values) != len(EXPECTED[case]):
        raise ValueError("incomplete sampled output")
    with localcontext() as ctx:
        ctx.prec = 100
        for actual, expected in zip(values, EXPECTED[case], strict=True):
            if not math.isfinite(actual) or actual < 0:
                raise ValueError("nonfinite or negative output")
            reference = Decimal(expected)
            bound = Decimal("1e-9") + Decimal("1e-8") * abs(reference)
            if abs(Decimal.from_float(actual) - reference) > bound:
                raise ValueError("sample exceeds approved P04 bound")


def summary(samples):
    if not samples or any(not math.isfinite(x) or x < 0 for x in samples):
        raise ValueError("require finite nonnegative timing observations")
    return {
        "seconds": samples,
        "median": statistics.median(samples),
        "min": min(samples),
        "max": max(samples),
    }


def fingerprints():
    paths = [
        ROOT / "packages/python/uv.lock",
        ROOT / "conformance/julia_ode/Project.toml",
        ROOT / "conformance/julia_ode/Manifest.toml",
        ROOT / "conformance/production_decay/catalog.json",
    ]
    for directory in (
        "packages/python/src",
        "packages/julia/src",
        "examples/m0",
        "benchmarks/m0",
    ):
        paths.extend(
            p for p in (ROOT / directory).rglob("*") if p.suffix in (".py", ".jl")
        )
    return {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(paths)
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=EXPECTED, required=True)
    parser.add_argument("--method", choices=("DOP853", "Radau"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=20)
    args = parser.parse_args()
    if args.warmups < 0 or args.repeats < 1:
        parser.error("warmups must be nonnegative; repeats must be positive")
    if len(args.source_revision) != 40 or any(
        c not in "0123456789abcdef" for c in args.source_revision
    ):
        parser.error("source revision must be a full lowercase commit SHA")
    started = time.perf_counter()
    example = runpy.run_path(str(ROOT / "examples/m0/production_decay.py"))
    from fenix.compiler import compile_experiment
    from fenix.execution import solve_ode
    from fenix.results import RunRecord, run_experiment

    package_load = time.perf_counter() - started
    experiment = example["build_experiment"](args.case)
    spec = example["execution_settings"](args.case, args.method)
    started = time.perf_counter()
    compiled = compile_experiment(experiment)
    first_compile = time.perf_counter() - started

    def check_compiled(value):
        if value.model.identity_bytes() != compiled.model.identity_bytes():
            raise ValueError("compilation changed FIR identity")

    def check_trajectory(value):
        if value.times != spec.time_grid:
            raise ValueError("incorrect sampling times")
        validate_values(args.case, [row[0] for row in value.state_values])

    def check_record(value):
        loaded = RunRecord.from_json(
            value.manifest.to_json(), value.result_bytes, experiment=experiment
        )
        if loaded.result_bytes != value.result_bytes:
            raise ValueError("readback changed result bytes")
        check_trajectory(value.result)

    operations = {
        "compile": (lambda: compile_experiment(experiment), check_compiled),
        "solve": (lambda: solve_ode(compiled.model, spec), check_trajectory),
        "capture": (lambda: run_experiment(experiment, spec), check_record),
    }
    first = {"compile": first_compile}
    timings = {}
    for name, (operation, check) in operations.items():
        if name != "compile":
            start = time.perf_counter()
            value = operation()
            first[name] = time.perf_counter() - start
            check(value)
        for _ in range(args.warmups):
            check(operation())
        samples = []
        for _ in range(args.repeats):
            start = time.perf_counter()
            value = operation()
            samples.append(time.perf_counter() - start)
            check(value)
        timings[name] = summary(samples)
    try:
        cpu = (
            subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            if platform.system() == "Darwin"
            else Path("/proc/cpuinfo").read_text()
        )
    except (OSError, subprocess.SubprocessError):
        cpu = platform.processor()
    import fenix

    report = {
        "package_path": str(Path(fenix.__file__).resolve()),
        "format": "m0-benchmark-v1",
        "language": "python",
        "case": args.case,
        "method": args.method,
        "source_revision": args.source_revision,
        "settings": {
            name: getattr(spec, name)
            for name in ("time_grid", "rtol", "atol", "max_step", "max_nfev")
        },
        "warmups": args.warmups,
        "repeats": args.repeats,
        "package_load_seconds": package_load,
        "first_seconds": first,
        "timings": timings,
        "runtime": {
            "language_version": platform.python_version(),
            "dependencies": {
                p: version(p) for p in ("fenix-bio", "numpy", "scipy", "rfc8785")
            },
        },
        "hardware": {
            "os": platform.platform(),
            "machine": platform.machine(),
            "cpu": cpu,
            "threads": {
                k: os.environ.get(k, "unset")
                for k in (
                    "OMP_NUM_THREADS",
                    "OPENBLAS_NUM_THREADS",
                    "MKL_NUM_THREADS",
                    "JULIA_NUM_THREADS",
                )
            },
            "logical_cpus": os.cpu_count(),
            "runner_image": {
                k: os.environ.get(k, "local") for k in ("ImageOS", "ImageVersion")
            },
        },
        "fingerprints": fingerprints(),
        "identities": {
            "design": experiment.source_design.digest,
            "experiment": experiment.digest,
            "fir": compiled.digest,
        },
        "validation": "PASS",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(
        f"PASS: {args.case}/{args.method}, {args.repeats} validated repetitions per phase"
    )


if __name__ == "__main__":
    main()
