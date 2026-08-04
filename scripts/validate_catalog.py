#!/usr/bin/env python3
"""Validate the atlas catalogs without third-party dependencies."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

CATALOGS = {
    "tools": {
        "path": ROOT / "data" / "tools.json",
        "required": {
            "id", "name", "vendor", "status", "category", "interfaces", "execution", "model_policy",
            "open_source", "pricing", "best_for", "strengths", "limitations",
            "official_sources", "last_verified",
        },
        "enums": {
            "category": {
                "cli-agent", "ide-extension", "ai-editor", "cloud-agent",
                "local-runtime", "web-gui",
            },
            "status": {"active", "legacy", "discontinued"},
            "execution": {"local-tools", "cloud-agent", "hybrid"},
            "model_policy": {
                "vendor-models", "curated-multi-model", "provider-agnostic",
                "local-only",
            },
        },
    },
    "gateways": {
        "path": ROOT / "data" / "gateways.json",
        "required": {
            "id", "name", "vendor", "kind", "delivery", "byok", "self_host",
            "open_source", "pricing_note", "strengths", "limitations",
            "official_sources", "last_verified",
        },
        "enums": {
            "kind": {
                "model-marketplace", "api-gateway", "inference-platform",
                "cloud-model-platform",
            },
            "delivery": {"managed", "self-hosted", "managed-and-self-hosted"},
        },
    },
    "models": {
        "path": ROOT / "data" / "models.json",
        "required": {
            "id", "provider", "family", "representative_models", "access",
            "open_weights", "modalities", "coding_notes", "limitations",
            "official_sources", "last_verified",
        },
        "enums": {},
    },
}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"missing file: {path.relative_to(ROOT)}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"invalid JSON in {path.relative_to(ROOT)}:{exc.lineno}:{exc.colno}: {exc.msg}"
        ) from exc


def validate_source(source: Any, where: str, errors: list[str]) -> None:
    if not isinstance(source, dict):
        errors.append(f"{where}: source must be an object")
        return
    if set(source) != {"label", "url"}:
        errors.append(f"{where}: source must contain only label and url")
        return
    if not isinstance(source["label"], str) or not source["label"].strip():
        errors.append(f"{where}: source label must be a non-empty string")
    if not isinstance(source["url"], str):
        errors.append(f"{where}: source URL must be a string")
        return
    parsed = urlparse(source["url"])
    if parsed.scheme != "https" or not parsed.netloc:
        errors.append(f"{where}: source URL must be absolute HTTPS: {source['url']!r}")


def validate_pricing(pricing: Any, where: str, errors: list[str]) -> None:
    required = {"model", "free_tier", "starting_price_usd_month", "note"}
    if not isinstance(pricing, dict) or set(pricing) != required:
        errors.append(f"{where}: pricing must contain exactly {sorted(required)}")
        return
    if pricing["model"] not in {"free", "subscription", "usage-based", "hybrid", "contact-sales"}:
        errors.append(f"{where}: unknown pricing model {pricing['model']!r}")
    if pricing["free_tier"] not in {True, False, None}:
        errors.append(f"{where}: free_tier must be true, false, or null")
    price = pricing["starting_price_usd_month"]
    if price is not None and (isinstance(price, bool) or not isinstance(price, (int, float)) or price < 0):
        errors.append(f"{where}: starting price must be a non-negative number or null")
    if not isinstance(pricing["note"], str) or not pricing["note"].strip():
        errors.append(f"{where}: pricing note must be non-empty")


def validate_record(
    catalog: str,
    record: Any,
    index: int,
    config: dict[str, Any],
    today: date,
    max_age_days: int | None,
    errors: list[str],
    warnings: list[str],
) -> None:
    where = f"{catalog}[{index}]"
    if not isinstance(record, dict):
        errors.append(f"{where}: record must be an object")
        return

    missing = config["required"] - set(record)
    if missing:
        errors.append(f"{where}: missing fields: {', '.join(sorted(missing))}")
        return

    record_id = record["id"]
    if not isinstance(record_id, str) or not ID_RE.fullmatch(record_id):
        errors.append(f"{where}: invalid id {record_id!r}")
    else:
        where = f"{catalog}:{record_id}"

    for field, allowed in config["enums"].items():
        if record.get(field) not in allowed:
            errors.append(f"{where}: invalid {field} {record.get(field)!r}")

    descriptive_fields = ("coding_notes", "limitations") if catalog == "models" else ("strengths", "limitations")
    for field in descriptive_fields:
        value = record.get(field)
        if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
            errors.append(f"{where}: {field} must be a non-empty string array")

    sources = record.get("official_sources")
    if not isinstance(sources, list) or not sources:
        errors.append(f"{where}: at least one official source is required")
    else:
        urls: set[str] = set()
        for source_index, source in enumerate(sources):
            validate_source(source, f"{where}.official_sources[{source_index}]", errors)
            if isinstance(source, dict) and isinstance(source.get("url"), str):
                if source["url"] in urls:
                    errors.append(f"{where}: duplicate source URL {source['url']}")
                urls.add(source["url"])

    try:
        verified = date.fromisoformat(record.get("last_verified", ""))
    except (TypeError, ValueError):
        errors.append(f"{where}: last_verified must use YYYY-MM-DD")
    else:
        if verified > today:
            errors.append(f"{where}: last_verified is in the future ({verified})")
        age = (today - verified).days
        if age > 90:
            warnings.append(f"{where}: source check is {age} days old")
        if max_age_days is not None and age > max_age_days:
            errors.append(f"{where}: source check exceeds MAX_AGE_DAYS={max_age_days}")

    if catalog == "tools":
        validate_pricing(record.get("pricing"), f"{where}.pricing", errors)
        interfaces = record.get("interfaces")
        allowed_interfaces = {"cli", "ide", "desktop", "web", "api", "ci", "mobile"}
        if not isinstance(interfaces, list) or not interfaces or len(interfaces) != len(set(interfaces)):
            errors.append(f"{where}: interfaces must be a non-empty unique array")
        elif set(interfaces) - allowed_interfaces:
            errors.append(f"{where}: unknown interfaces {sorted(set(interfaces) - allowed_interfaces)}")

    if catalog == "models":
        access = record.get("access")
        allowed_access = {"first-party-api", "cloud-platform", "gateway", "download"}
        if not isinstance(access, list) or not access or set(access) - allowed_access:
            errors.append(f"{where}: invalid access list {access!r}")
        pricing = record.get("api_pricing")
        if pricing is not None:
            fields = {
                "input_usd_per_million", "cached_input_usd_per_million",
                "output_usd_per_million", "model", "note",
            }
            if not isinstance(pricing, dict) or set(pricing) != fields:
                errors.append(f"{where}: api_pricing must contain exactly {sorted(fields)}")
            else:
                for field in (
                    "input_usd_per_million", "cached_input_usd_per_million",
                    "output_usd_per_million",
                ):
                    value = pricing[field]
                    if value is not None and (
                        isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0
                    ):
                        errors.append(f"{where}: {field} must be non-negative or null")


def validate_all(max_age_days: int | None = None) -> tuple[list[str], list[str], dict[str, int]]:
    errors: list[str] = []
    warnings: list[str] = []
    counts: dict[str, int] = {}
    today = date.today()

    for catalog, config in CATALOGS.items():
        try:
            records = load_json(config["path"])
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not isinstance(records, list) or not records:
            errors.append(f"{catalog}: root must be a non-empty array")
            continue
        counts[catalog] = len(records)
        seen: set[str] = set()
        for index, record in enumerate(records):
            validate_record(catalog, record, index, config, today, max_age_days, errors, warnings)
            if isinstance(record, dict) and isinstance(record.get("id"), str):
                if record["id"] in seen:
                    errors.append(f"{catalog}: duplicate id {record['id']!r}")
                seen.add(record["id"])

    return errors, warnings, counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=int(os.environ["MAX_AGE_DAYS"]) if os.getenv("MAX_AGE_DAYS") else None,
        help="fail records older than this many days",
    )
    args = parser.parse_args()

    errors, warnings, counts = validate_all(args.max_age_days)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    for error in errors:
        print(f"error: {error}", file=sys.stderr)

    if errors:
        print(f"validation failed with {len(errors)} error(s)", file=sys.stderr)
        return 1
    summary = ", ".join(f"{name}={count}" for name, count in sorted(counts.items()))
    print(f"catalog valid: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
