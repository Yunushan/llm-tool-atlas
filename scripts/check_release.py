#!/usr/bin/env python3
"""Verify that release metadata and an optional Git tag agree."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\."
    r"(0|[1-9][0-9]*)\."
    r"(0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
CHANGELOG_RELEASE_RE = re.compile(
    r"^## \[([^]]+)] - ([0-9]{4}-[0-9]{2}-[0-9]{2})$", re.MULTILINE
)


@dataclass(frozen=True)
class ReleaseMetadata:
    """Canonical release identity shared by release tooling."""

    version: str
    release_date: str

    @property
    def tag(self) -> str:
        return f"v{self.version}"


def is_semver(value: str) -> bool:
    """Return whether a value follows SemVer, including identifier zero rules."""

    match = SEMVER_RE.fullmatch(value)
    if match is None:
        return False
    prerelease = match.group(4)
    if prerelease is None:
        return True
    return all(
        not (identifier.isdigit() and len(identifier) > 1 and identifier.startswith("0"))
        for identifier in prerelease.split(".")
    )


def _top_level_cff_fields(text: str) -> tuple[dict[str, str], list[str]]:
    """Read the simple top-level scalar fields used by CITATION.cff."""

    fields: dict[str, str] = {}
    errors: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line or line[0].isspace() or ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        if key in fields:
            errors.append(f"CITATION.cff:{line_number}: duplicate top-level field {key!r}")
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        fields[key] = value
    return fields, errors


def validate_release(
    root: Path = ROOT,
    tag: str | None = None,
    today: date | None = None,
) -> tuple[ReleaseMetadata | None, list[str]]:
    """Return parsed metadata and every release-consistency error."""

    errors: list[str] = []
    version_path = root / "VERSION"
    citation_path = root / "CITATION.cff"
    changelog_path = root / "CHANGELOG.md"

    try:
        version_raw = version_path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, [f"cannot read VERSION: {exc}"]
    version = version_raw.strip()
    if version_raw != f"{version}\n":
        errors.append("VERSION must contain only the version and one trailing LF")
    if not is_semver(version):
        errors.append(f"VERSION is not valid SemVer: {version!r}")

    try:
        citation_text = citation_path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, errors + [f"cannot read CITATION.cff: {exc}"]
    cff, cff_errors = _top_level_cff_fields(citation_text)
    errors.extend(cff_errors)
    cff_version = cff.get("version")
    release_date = cff.get("date-released")
    if cff_version != version:
        errors.append(
            f"CITATION.cff version {cff_version!r} does not match VERSION {version!r}"
        )
    if cff.get("license") != "0BSD":
        errors.append("CITATION.cff license must be 0BSD")

    parsed_release_date: date | None = None
    if release_date is None:
        errors.append("CITATION.cff is missing date-released")
    else:
        try:
            parsed_release_date = date.fromisoformat(release_date)
        except ValueError:
            errors.append(
                f"CITATION.cff date-released must use YYYY-MM-DD: {release_date!r}"
            )
        else:
            if parsed_release_date > (today or date.today()):
                errors.append(f"CITATION.cff date-released is in the future: {release_date}")

    try:
        changelog_text = changelog_path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, errors + [f"cannot read CHANGELOG.md: {exc}"]
    releases = CHANGELOG_RELEASE_RE.findall(changelog_text)
    matching_dates = [item_date for item_version, item_date in releases if item_version == version]
    if not matching_dates:
        errors.append(f"CHANGELOG.md has no release heading for {version}")
    elif len(matching_dates) > 1:
        errors.append(f"CHANGELOG.md has multiple release headings for {version}")
    elif release_date is not None and matching_dates[0] != release_date:
        errors.append(
            "CHANGELOG.md release date "
            f"{matching_dates[0]!r} does not match CITATION.cff {release_date!r}"
        )
    if releases and releases[0][0] != version:
        errors.append(
            f"latest CHANGELOG.md release {releases[0][0]!r} does not match VERSION {version!r}"
        )
    for item_version, item_date in releases:
        if not is_semver(item_version):
            errors.append(f"CHANGELOG.md release is not valid SemVer: {item_version!r}")
        try:
            date.fromisoformat(item_date)
        except ValueError:
            errors.append(f"CHANGELOG.md release date is invalid: {item_date!r}")

    if tag is not None:
        expected = f"v{version}"
        if tag != expected:
            errors.append(f"release tag {tag!r} does not match expected tag {expected!r}")

    metadata = (
        ReleaseMetadata(version=version, release_date=release_date)
        if is_semver(version) and parsed_release_date is not None and release_date is not None
        else None
    )
    return metadata, errors


def require_release(root: Path = ROOT, tag: str | None = None) -> ReleaseMetadata:
    """Return valid release metadata or raise a human-readable ValueError."""

    metadata, errors = validate_release(root=root, tag=tag)
    if errors or metadata is None:
        raise ValueError("release metadata is inconsistent:\n- " + "\n- ".join(errors))
    return metadata


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tag",
        help="require this Git tag to equal v<VERSION> (used by the release workflow)",
    )
    args = parser.parse_args(argv)

    metadata, errors = validate_release(tag=args.tag)
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors or metadata is None:
        print(f"release metadata check failed: {len(errors)} error(s)", file=sys.stderr)
        return 1
    suffix = f", tag={args.tag}" if args.tag else ""
    print(
        f"release metadata valid: version={metadata.version}, "
        f"date={metadata.release_date}{suffix}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
