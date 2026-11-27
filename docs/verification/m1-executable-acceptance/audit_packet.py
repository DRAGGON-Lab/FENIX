"""Verify retained commit/tree proof and packet bytes without ephemeral Git objects."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def object_id(kind, raw):
    return hashlib.sha1(
        kind.encode() + b" " + str(len(raw)).encode() + b"\0" + raw
    ).hexdigest()


def tree_id(rows):
    entries = {}
    directories = {}
    for row in rows:
        name, separator, rest = row["path"].partition("/")
        if separator:
            directories.setdefault(name, []).append(dict(row, path=rest))
        else:
            assert row["type"] == "blob"
            entries[name] = (row["mode"].lstrip("0"), row["oid"], False)
    for name, children in directories.items():
        entries[name] = ("40000", tree_id(children), True)
    ordered = sorted(
        entries, key=lambda name: (name + ("/" if entries[name][2] else "")).encode()
    )
    raw = b"".join(
        entries[name][0].encode()
        + b" "
        + name.encode()
        + b"\0"
        + bytes.fromhex(entries[name][1])
        for name in ordered
    )
    return object_id("tree", raw)


def main():
    trees = []
    for name, expected in (
        ("hosted-tested-merge", "35af5c3ad1bfe1c5208087ad2f96bf9a79fdb017"),
        ("landed-merge", "301dc0542a8bc08750de5796df3269881819b1ca"),
    ):
        raw = (HERE / (name + ".commit")).read_bytes()
        assert object_id("commit", raw) == expected
        assert raw.startswith(b"tree ")
        trees.append(raw.splitlines()[0].split()[1].decode())
    rows = json.loads((HERE / "reviewed-tree.json").read_bytes())
    assert len({row["path"] for row in rows}) == len(rows)
    assert trees[0] == trees[1] == tree_id(rows)
    inventory = {
        row["path"]
        for row in rows
        if row["path"].startswith(
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
    raw = (ROOT / "spec/community/review-manifest.json").read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "30255a118bcd17ba8f75d500eaec161bf9c1443f77c15ba74282e7c032f4da81"
    )
    fingerprints = json.loads(raw)["sha256"]
    assert set(fingerprints) == inventory
    for name, expected in fingerprints.items():
        path = ROOT / name
        assert not path.is_symlink() and path.resolve().is_relative_to(ROOT)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
    print(
        f"PASS retained commit/tree proof and all {len(inventory)} packet fingerprints (no Git or network)"
    )


if __name__ == "__main__":
    main()
