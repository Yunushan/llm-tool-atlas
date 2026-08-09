#!/usr/bin/env python3
"""Render deterministic Markdown tables from the JSON catalogs."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Sequence

from validate_catalog import load_json
from url_safety import static_https_url_error


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUT = ROOT / "docs" / "generated"
MARKDOWN_META_RE = re.compile(r"([\\`*_{}\[\]<>#!|~])")
PLATFORM_LABELS = {
    "windows": "Windows",
    "macos": "macOS",
    "linux": "Linux",
    "freebsd": "FreeBSD",
    "ios": "iOS",
    "vs-code": "VS Code",
    "visual-studio": "Visual Studio",
    "jetbrains": "JetBrains",
    "xcode": "Xcode",
    "neovim": "Neovim",
    "vim": "Vim",
    "eclipse": "Eclipse",
    "zed": "Zed",
    "jupyter": "Jupyter",
    "wsl": "WSL",
    "containers": "Containers",
    "kubernetes": "Kubernetes",
    "managed-cloud": "Managed cloud",
    "managed-workspace": "Managed workspace",
    "github": "GitHub",
    "github-actions": "GitHub Actions",
    "gitlab": "GitLab",
    "bitbucket": "Bitbucket",
    "slack": "Slack",
    "claude-desktop": "Claude Desktop",
    "sourcegraph-enterprise": "Sourcegraph Enterprise",
}


class TrustedMarkdown(str):
    """Markdown assembled from escaped text and a validated destination."""


def load(name: str) -> list[dict[str, Any]]:
    # Use the same duplicate-key and finite-number policy as the validator so
    # standalone rendering cannot silently normalize malformed catalog JSON.
    value = load_json(DATA / f"{name}.json")
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError(f"data/{name}.json must contain an array of objects")
    return value


def escape_markdown_text(value: str) -> str:
    """Escape untrusted catalog text for a GitHub Markdown table cell."""

    flattened = " ".join(value.splitlines()).strip()
    return MARKDOWN_META_RE.sub(r"\\\1", flattened)


def markdown_url(value: str) -> str:
    """Return a safe angle-bracket Markdown destination."""

    problem = static_https_url_error(value)
    if problem:
        raise ValueError(f"{problem}: {value!r}")
    return f"<{value}>"


def bold(value: str) -> TrustedMarkdown:
    return TrustedMarkdown(f"**{escape_markdown_text(value)}**")


def cell(value: Any) -> str:
    if isinstance(value, TrustedMarkdown):
        return str(value)
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, list):
        value = ", ".join(str(item) for item in value)
    return escape_markdown_text(str(value))


def sources(record: dict[str, Any]) -> TrustedMarkdown:
    return TrustedMarkdown(" · ".join(
        f"[{escape_markdown_text(source['label'])}]({markdown_url(source['url'])})"
        for source in record["official_sources"]
    ))


def availability(record: dict[str, Any]) -> str:
    """Render the structured platform matrix without conflating dimensions."""

    platforms = record["platforms"]
    segments: list[str] = []
    dimensions = (
        ("OS", "operating_systems"),
        ("Editors", "editors"),
        ("Deploy", "deployment"),
        ("Integrations", "integrations"),
    )
    for label, field in dimensions:
        values = platforms[field]
        if values:
            segments.append(
                f"{label}: " + ", ".join(PLATFORM_LABELS[value] for value in values)
            )
    segments.extend(platforms["notes"])
    return "; ".join(segments)


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(cell(item) for item in row) + " |" for row in rows)
    return "\n".join(lines)


def render_tools(records: list[dict[str, Any]]) -> str:
    rows = []
    for record in sorted(records, key=lambda item: item["name"].casefold()):
        pricing = record["pricing"]
        start = pricing["starting_price_usd_month"]
        price = "Free" if pricing["model"] == "free" else (
            f"${start:g}/mo" if start is not None else pricing["model"].replace("-", " ").title()
        )
        rows.append([
            bold(record["name"]),
            record["status"],
            record["category"].replace("-", " "),
            record["interfaces"],
            availability(record),
            record["model_policy"].replace("-", " "),
            record.get("byok", False),
            record["open_source"],
            price,
            "; ".join(record["best_for"]),
            record["last_verified"],
            sources(record),
        ])
    return generated_header("Tool catalog", records) + markdown_table(
        ["Tool", "Status", "Category", "Interfaces", "Availability", "Model policy", "BYOK", "Open source", "Starts", "Best for", "Verified", "Official sources"],
        rows,
    ) + "\n"


def render_gateways(records: list[dict[str, Any]]) -> str:
    rows = []
    for record in sorted(records, key=lambda item: item["name"].casefold()):
        rows.append([
            bold(record["name"]),
            record["kind"].replace("-", " "),
            record["delivery"].replace("-", " "),
            record["byok"],
            record["self_host"],
            record["open_source"],
            record["pricing_note"],
            "; ".join(record["strengths"]),
            record["last_verified"],
            sources(record),
        ])
    return generated_header("Gateway and inference-platform catalog", records) + markdown_table(
        ["Platform", "Kind", "Delivery", "BYOK", "Self-host", "Open source", "Pricing basis", "Notable strengths", "Verified", "Official sources"],
        rows,
    ) + "\n"


def render_models(records: list[dict[str, Any]]) -> str:
    rows = []
    for record in sorted(records, key=lambda item: (item["provider"].casefold(), item["family"].casefold())):
        pricing = record.get("api_pricing")
        if pricing:
            i = pricing["input_usd_per_million"]
            o = pricing["output_usd_per_million"]
            price = f"{pricing['model']}: " + (
                f"${i:g} in / ${o:g} out" if i is not None and o is not None else pricing["note"]
            )
        else:
            price = "See official pricing"
        rows.append([
            bold(record["provider"]),
            record["family"],
            record["representative_models"],
            record["input_modalities"],
            record["output_modalities"],
            record["capabilities"],
            record["open_weights"],
            price,
            "; ".join(record["coding_notes"]),
            record["last_verified"],
            sources(record),
        ])
    return generated_header("Coding-relevant model-family catalog", records) + markdown_table(
        ["Provider", "Family", "Representative models", "Inputs", "Outputs", "Capabilities", "Open weights", "Representative API price / 1M tokens", "Coding notes", "Verified", "Official sources"],
        rows,
    ) + "\n"


def generated_header(title: str, records: list[dict[str, Any]]) -> str:
    newest = max(record["last_verified"] for record in records)
    return (
        f"# {title}\n\n"
        "> Generated from the canonical JSON data. Do not edit this file by hand. "
        f"Prices exclude tax unless noted. Entries: **{len(records)}**. "
        f"Newest source check: **{newest}**.\n\n"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated files differ")
    args = parser.parse_args(argv)

    rendered = {
        "tools.md": render_tools(load("tools")),
        "gateways.md": render_gateways(load("gateways")),
        "models.md": render_models(load("models")),
    }

    stale: list[str] = []
    if not args.check:
        OUTPUT.mkdir(parents=True, exist_ok=True)
    for filename, content in rendered.items():
        path = OUTPUT / filename
        if args.check:
            current = path.read_text(encoding="utf-8") if path.exists() else None
            if current != content:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.write_text(content, encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)}")

    if stale:
        print("generated files are stale: " + ", ".join(stale), file=sys.stderr)
        print("run: python3 scripts/render_catalog.py", file=sys.stderr)
        return 1
    if args.check:
        print("generated files are current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
