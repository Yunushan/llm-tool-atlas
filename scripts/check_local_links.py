#!/usr/bin/env python3
"""Check Markdown file links, reference targets, and local heading fragments."""

from __future__ import annotations

import html
import os
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
REFERENCE_DEFINITION_RE = re.compile(
    r"^\s{0,3}\[([^\]]+)\]:\s*(?:<([^>]+)>|(\S+))"
)
REFERENCE_USE_RE = re.compile(r"!?\[([^\]]+)\]\[([^\]]*)\]")
CODE_SPAN_RE = re.compile(r"(`+).*?\1")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}(?:\s+|$)(.*?)\s*#*\s*$")
HTML_ID_RE = re.compile(r"\b(?:id|name)=[\"']([^\"']+)[\"']", re.IGNORECASE)
HTML_TAG_RE = re.compile(r"<[^>]+>")
INLINE_LINK_LABEL_RE = re.compile(r"!?(?<!\\)\[[^\]]*\]$")
SAFE_EXTERNAL_SCHEMES = frozenset({"http", "https", "mailto"})


def normalize_reference(value: str) -> str:
    return " ".join(value.split()).casefold()


def visible_lines(text: str) -> list[tuple[int, str]]:
    """Return lines outside fenced code blocks with inline code masked."""

    visible: list[tuple[int, str]] = []
    fence_character: str | None = None
    fence_length = 0
    for line_number, line in enumerate(text.splitlines(), start=1):
        fence = FENCE_RE.match(line)
        if fence:
            marker = fence.group(1)
            if fence_character is None:
                fence_character = marker[0]
                fence_length = len(marker)
                continue
            if marker[0] == fence_character and len(marker) >= fence_length:
                fence_character = None
                fence_length = 0
                continue
        if fence_character is not None:
            continue
        masked = CODE_SPAN_RE.sub(lambda match: " " * len(match.group(0)), line)
        visible.append((line_number, masked))
    return visible


def inline_destinations(line: str) -> list[str]:
    """Extract inline Markdown link destinations with balanced parentheses."""

    destinations: list[str] = []
    position = 0
    while True:
        marker = line.find("](", position)
        if marker < 0:
            return destinations
        if not INLINE_LINK_LABEL_RE.search(line[: marker + 1]):
            position = marker + 2
            continue

        cursor = marker + 2
        while cursor < len(line) and line[cursor].isspace():
            cursor += 1
        if cursor >= len(line):
            return destinations

        if line[cursor] == "<":
            end = cursor + 1
            while end < len(line) and line[end] != ">":
                end += 1
            if end < len(line):
                destinations.append(line[cursor + 1 : end])
                position = end + 1
            else:
                position = cursor + 1
            continue

        start = cursor
        depth = 0
        escaped = False
        destination: list[str] = []
        while cursor < len(line):
            character = line[cursor]
            if escaped:
                destination.append(character)
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == "(":
                depth += 1
                destination.append(character)
            elif character == ")":
                if depth == 0:
                    break
                depth -= 1
                destination.append(character)
            elif character.isspace() and depth == 0:
                break
            else:
                destination.append(character)
            cursor += 1
        if cursor > start and destination:
            destinations.append("".join(destination))
        position = max(cursor + 1, marker + 2)


def github_heading_slug(value: str) -> str:
    """Approximate GitHub's documented heading-anchor normalization."""

    value = html.unescape(HTML_TAG_RE.sub("", value)).casefold().strip()
    value = re.sub(r"!?\[([^\]]+)\]\([^)]*\)", r"\1", value)
    value = value.replace("`", "").replace("*", "").replace("_", "")
    characters = []
    for character in value:
        category = unicodedata.category(character)
        if character.isspace():
            characters.append("-")
        elif character in {"-", "_"} or category[0] in {"L", "N"}:
            characters.append(character)
    return re.sub(r"-+", "-", "".join(characters)).strip("-")


def markdown_anchors(path: Path) -> set[str]:
    """Collect heading and explicit HTML anchors from a Markdown file."""

    text = path.read_text(encoding="utf-8")
    anchors: set[str] = set()
    occurrences: dict[str, int] = {}
    for _line_number, line in visible_lines(text):
        for match in HTML_ID_RE.finditer(line):
            anchors.add(unquote(match.group(1)).casefold())
        heading = HEADING_RE.match(line)
        if not heading:
            continue
        base = github_heading_slug(heading.group(1))
        if not base:
            continue
        occurrence = occurrences.get(base, 0)
        occurrences[base] = occurrence + 1
        anchors.add(base if occurrence == 0 else f"{base}-{occurrence}")
    return anchors


def exact_path_case(path: Path, root: Path) -> bool:
    """Check path spelling exactly even on case-insensitive filesystems."""

    try:
        relative = path.relative_to(root)
    except ValueError:
        return False
    current = root
    for part in relative.parts:
        try:
            names = {child.name for child in current.iterdir()}
        except OSError:
            return False
        if part not in names:
            return False
        current = current / part
    return True


def check_destination(
    raw: str,
    markdown: Path,
    line_number: int,
    root: Path,
    anchor_cache: dict[Path, set[str]],
) -> str | None:
    """Return a diagnostic for one destination, or ``None`` when valid."""

    raw = raw.strip()
    if not raw:
        return None
    if raw.startswith("//"):
        return None
    parsed = urlsplit(raw)
    if parsed.scheme:
        if parsed.scheme.casefold() not in SAFE_EXTERNAL_SCHEMES:
            return (
                f"{markdown.relative_to(root)}:{line_number}: "
                f"unsafe or unsupported URL scheme: {raw}"
            )
        return None

    try:
        decoded_path = unquote(parsed.path)
        spelled_target = markdown if not decoded_path else markdown.parent / decoded_path
        spelled_target = Path(os.path.normpath(spelled_target.absolute()))
        target = spelled_target.resolve()
        target_exists = target.exists()
    except (OSError, RuntimeError, ValueError) as exc:
        return (
            f"{markdown.relative_to(root)}:{line_number}: "
            f"invalid local link path: {raw} ({exc})"
        )
    try:
        target.relative_to(root)
    except ValueError:
        return (
            f"{markdown.relative_to(root)}:{line_number}: "
            f"link escapes repository: {raw}"
        )
    if not target_exists:
        return (
            f"{markdown.relative_to(root)}:{line_number}: missing target: {raw}"
        )
    if not exact_path_case(spelled_target, root):
        return (
            f"{markdown.relative_to(root)}:{line_number}: "
            f"target path has incorrect letter case: {raw}"
        )

    fragment = unquote(parsed.fragment).casefold()
    if fragment and target.is_file() and target.suffix.casefold() == ".md":
        anchors = anchor_cache.setdefault(target, markdown_anchors(target))
        if fragment not in anchors:
            return (
                f"{markdown.relative_to(root)}:{line_number}: "
                f"missing Markdown heading fragment: {raw}"
            )
    return None


def is_local_destination(raw: str) -> bool:
    """Return whether a destination is meant to resolve inside the repository."""

    raw = raw.strip()
    return bool(raw) and not raw.startswith("//") and not urlsplit(raw).scheme


def check_links(root: Path = ROOT) -> tuple[list[str], int]:
    """Check every Markdown link below ``root``."""

    root = root.resolve()
    problems: list[str] = []
    checked = 0
    anchor_cache: dict[Path, set[str]] = {}

    for markdown in sorted(root.rglob("*.md")):
        if ".git" in markdown.parts:
            continue
        lines = visible_lines(markdown.read_text(encoding="utf-8"))
        references: dict[str, tuple[str, int]] = {}
        for line_number, line in lines:
            definition = REFERENCE_DEFINITION_RE.match(line)
            if definition:
                destination = definition.group(2) or definition.group(3)
                references[normalize_reference(definition.group(1))] = (
                    destination,
                    line_number,
                )

        for destination, line_number in references.values():
            if is_local_destination(destination):
                checked += 1
            problem = check_destination(
                destination, markdown, line_number, root, anchor_cache
            )
            if problem:
                problems.append(problem)

        for line_number, line in lines:
            if REFERENCE_DEFINITION_RE.match(line):
                continue
            for destination in inline_destinations(line):
                if is_local_destination(destination):
                    checked += 1
                problem = check_destination(
                    destination, markdown, line_number, root, anchor_cache
                )
                if problem:
                    problems.append(problem)
            for reference in REFERENCE_USE_RE.finditer(line):
                label = reference.group(2) or reference.group(1)
                if normalize_reference(label) not in references:
                    problems.append(
                        f"{markdown.relative_to(root)}:{line_number}: "
                        f"undefined Markdown reference: {label}"
                    )

    return problems, checked


def main() -> int:
    problems, checked = check_links()
    for problem in problems:
        print(f"error: {problem}", file=sys.stderr)
    if problems:
        print(
            f"local link check failed: {len(problems)} problem(s)",
            file=sys.stderr,
        )
        return 1
    print(f"local Markdown links valid: {checked} checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
