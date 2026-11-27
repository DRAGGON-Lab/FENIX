"""Reproduce PR96 offline-audit success and corrupted-proof rejection."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


class OfflineProofTests(unittest.TestCase):
    def test_export_without_git_and_corrupted_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            exported = Path(directory)
            manifest = "spec/community/review-manifest.json"
            names = list(json.loads((ROOT / manifest).read_bytes())["sha256"])
            for name in [manifest, *names]:
                target = exported / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            proof = exported / HERE.relative_to(ROOT)
            shutil.copytree(HERE, proof)
            self.assertFalse((exported / ".git").exists())
            command = [sys.executable, str(proof / "audit_packet.py")]
            good = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(good.returncode, 0, good.stderr)
            inventory = proof / "reviewed-tree.json"
            rows = json.loads(inventory.read_bytes())
            rows[0]["oid"] = "0" * 40
            inventory.write_text(json.dumps(rows))
            bad = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn("AssertionError", bad.stderr)


if __name__ == "__main__":
    unittest.main()
