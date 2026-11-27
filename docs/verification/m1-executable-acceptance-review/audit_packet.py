"""Read-only acceptance-review inventory check, independent of packet tooling."""

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HEAD = "7a90803f852da9b7cd7593f7d8dc54380cbe445d"
MERGE = "301dc0542a8bc08750de5796df3269881819b1ca"
TESTED = "35af5c3ad1bfe1c5208087ad2f96bf9a79fdb017"


def main():
    tracked = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", MERGE], cwd=ROOT, text=True
    ).splitlines()
    inventory = {
        name
        for name in tracked
        if name.startswith(
            (
                "spec/community/",
                "conformance/community/",
                "docs/verification/m1-executable-packet/",
            )
        )
    }
    inventory.discard("spec/community/review-manifest.json")
    inventory.update(
        (
            "docs/verification/m1-executable-packet.md",
            ".github/workflows/community-reference.yml",
            "conformance/julia_ode/Project.toml",
            "conformance/julia_ode/Manifest.toml",
            "packages/python/uv.lock",
        )
    )
    manifest = json.loads((ROOT / "spec/community/review-manifest.json").read_bytes())
    assert set(manifest["sha256"]) == inventory
    for name in sorted(inventory):
        path = ROOT / name
        assert not path.is_symlink()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest["sha256"][name]
    for revision in (HEAD, TESTED):
        assert not subprocess.check_output(
            ["git", "diff", "--name-only", revision, MERGE], cwd=ROOT
        ), f"reviewed tree differs from {revision}"
    print(f"PASS independent tracked-tree coverage: {len(inventory)} artifacts")
    print("PASS reviewed head, hosted test merge and landed merge have equal trees")


if __name__ == "__main__":
    main()
