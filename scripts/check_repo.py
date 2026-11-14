"""Offline FENIX agentic repository checks; not scientific conformance."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "README.md",
    "PRODUCT.md",
    "ARCHITECTURE.md",
    "AGENTS.md",
    "docs/approved-decisions.md",
    "docs/DEVELOPMENT_WORKFLOW.md",
    "packages/python/AGENTS.md",
    "packages/julia/AGENTS.md",
    "spec/AGENTS.md",
)
IGNORED_DIRS = {".git", ".venv", "venv", "node_modules", "build", "dist", ".julia"}
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def markdown_targets(content: str):
    """Yield inline Markdown destinations outside fenced code blocks."""
    fence = None
    for line in content.splitlines():
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            char = marker.group(1)[0]
            if fence is None:
                fence = char
            elif fence == char:
                fence = None
            continue
        if fence:
            continue
        for match in LINK.finditer(line):
            yield match.group(1).strip().split(" ", 1)[0].strip("<>")


def audit(root: Path) -> list[str]:
    """Check core agent docs and local links without network calls."""
    root = root.resolve()
    errors: list[str] = []
    for relative in REQUIRED:
        if not (root / relative).is_file():
            errors.append(f"required file missing: {relative}")

    if (root / "AGENT.md").exists():
        errors.append("legacy AGENT.md duplicates policy; use docs/DEVELOPMENT_WORKFLOW.md")

    claude = root / "CLAUDE.md"
    if claude.is_file() and "@AGENTS.md" not in claude.read_text(encoding="utf-8"):
        errors.append("CLAUDE.md must import @AGENTS.md to preserve one instruction source")

    for path in sorted(root.rglob("*.md")):
        if any(part in IGNORED_DIRS for part in path.relative_to(root).parts):
            continue
        rel = path.relative_to(root).as_posix()
        for raw in markdown_targets(path.read_text(encoding="utf-8")):
            if not raw or raw.startswith(("#", "//", "/")) or SCHEME.match(raw):
                continue
            local = unquote(raw.split("#", 1)[0].split("?", 1)[0])
            if not local:
                continue
            target = (path.parent / local).resolve()
            if not target.is_relative_to(root):
                errors.append(f"link escapes repository: {rel}: {raw}")
            elif not target.exists():
                errors.append(f"broken relative link: {rel}: {raw}")
    return errors


def main() -> int:
    errors = audit(ROOT)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("Repository harness checks passed (not scientific conformance).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
