#!/usr/bin/env python3
"""Check that relative file links in Markdown resolve inside the repository."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def main() -> int:
    broken: list[str] = []
    checked = 0
    for markdown in sorted(ROOT.rglob("*.md")):
        if ".git" in markdown.parts:
            continue
        text = markdown.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in LINK_RE.finditer(line):
                raw = match.group(1).strip().split(maxsplit=1)[0].strip("<>")
                if not raw or raw.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                relative = unquote(raw.split("#", 1)[0].split("?", 1)[0])
                if not relative:
                    continue
                checked += 1
                target = (markdown.parent / relative).resolve()
                try:
                    target.relative_to(ROOT)
                except ValueError:
                    broken.append(
                        f"{markdown.relative_to(ROOT)}:{line_number}: link escapes repository: {raw}"
                    )
                    continue
                if not target.exists():
                    broken.append(
                        f"{markdown.relative_to(ROOT)}:{line_number}: missing target: {raw}"
                    )

    for problem in broken:
        print(f"error: {problem}", file=sys.stderr)
    if broken:
        print(f"local link check failed: {len(broken)} broken link(s)", file=sys.stderr)
        return 1
    print(f"local Markdown links valid: {checked} checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
