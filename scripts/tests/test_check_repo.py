"""Unit tests for offline repository-harness checks."""

import tempfile
import unittest
from pathlib import Path

from scripts.check_repo import REQUIRED, audit, markdown_targets


class TestRepositoryHarness(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for relative in REQUIRED:
            file = self.root / relative
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text("# Placeholder\n", encoding="utf-8")

    def test_valid_structure(self):
        self.assertEqual(audit(self.root), [])

    def test_missing_required_file(self):
        (self.root / "AGENTS.md").unlink()
        self.assertTrue(any("required file missing: AGENTS.md" in e for e in audit(self.root)))

    def test_duplicate_legacy_agent(self):
        (self.root / "AGENT.md").write_text("# Legacy\n", encoding="utf-8")
        self.assertTrue(any("legacy AGENT.md" in e for e in audit(self.root)))

    def test_claude_import_requirements(self):
        claude = self.root / "CLAUDE.md"
        claude.write_text("# Different instructions\n", encoding="utf-8")
        self.assertTrue(any("must import @AGENTS.md" in e for e in audit(self.root)))
        claude.write_text("@AGENTS.md\n", encoding="utf-8")
        self.assertEqual(audit(self.root), [])

    def test_relative_links(self):
        readme = self.root / "README.md"
        readme.write_text("[doc](docs/approved-decisions.md#anchor) [external](https://example.org)\n")
        self.assertEqual(audit(self.root), [])
        readme.write_text("[broken](docs/MISSING.md)\n")
        self.assertTrue(any("broken relative link" in e for e in audit(self.root)))

    def test_ignores_links_inside_code_fences(self):
        self.assertEqual(list(markdown_targets("```markdown\n[example](MISSING.md)\n```")), [])


if __name__ == "__main__":
    unittest.main()
