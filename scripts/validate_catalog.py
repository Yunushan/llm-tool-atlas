#!/usr/bin/env python3
"""Validate the atlas catalogs without third-party dependencies."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, TypedDict

from url_safety import static_https_url_error


ROOT = Path(__file__).resolve().parents[1]
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAX_CATALOG_NUMBER = 1_000_000_000
PLATFORM_ENUMS: dict[str, frozenset[str]] = {
    "operating_systems": frozenset({"windows", "macos", "linux", "freebsd", "ios"}),
    "editors": frozenset({
        "vs-code", "visual-studio", "jetbrains", "xcode", "neovim", "vim",
        "eclipse", "zed", "jupyter",
    }),
    "deployment": frozenset({
        "wsl", "containers", "kubernetes", "managed-cloud", "managed-workspace",
    }),
    "integrations": frozenset({
        "github", "github-actions", "gitlab", "bitbucket", "slack", "claude-desktop",
        "sourcegraph-enterprise",
    }),
}
PLATFORM_FIELDS = frozenset({*PLATFORM_ENUMS, "notes"})


class CatalogConfig(TypedDict):
    path: Path
    required: frozenset[str]
    optional: frozenset[str]
    enums: dict[str, frozenset[str]]


CATALOGS: dict[str, CatalogConfig] = {
    "tools": {
        "path": ROOT / "data" / "tools.json",
        "required": frozenset({
            "id", "name", "vendor", "status", "category", "interfaces",
            "execution", "platforms", "model_policy", "byok", "self_host",
            "open_source", "pricing", "best_for", "strengths", "limitations",
            "official_sources", "last_verified",
        }),
        "optional": frozenset({"license"}),
        "enums": {
            "category": frozenset({
                "cli-agent", "ide-extension", "ai-editor", "cloud-agent",
                "local-runtime", "web-gui",
            }),
            "status": frozenset({"active", "legacy", "discontinued"}),
            "execution": frozenset({"local-tools", "cloud-agent", "hybrid"}),
            "model_policy": frozenset({
                "vendor-models", "curated-multi-model", "provider-agnostic",
                "local-only",
            }),
            "interfaces": frozenset({"cli", "ide", "desktop", "web", "api", "ci", "mobile"}),
        },
    },
    "gateways": {
        "path": ROOT / "data" / "gateways.json",
        "required": frozenset({
            "id", "name", "vendor", "kind", "delivery", "byok", "self_host",
            "open_source", "pricing_note", "strengths", "limitations",
            "official_sources", "last_verified",
        }),
        "optional": frozenset({"license"}),
        "enums": {
            "kind": frozenset({
                "model-marketplace", "api-gateway", "inference-platform",
                "cloud-model-platform",
            }),
            "delivery": frozenset({"managed", "self-hosted", "managed-and-self-hosted"}),
        },
    },
    "models": {
        "path": ROOT / "data" / "models.json",
        "required": frozenset({
            "id", "provider", "family", "representative_models", "access",
            "open_weights", "input_modalities", "output_modalities",
            "capabilities", "coding_notes", "limitations", "official_sources",
            "last_verified",
        }),
        "optional": frozenset({"weight_license", "context_note", "api_pricing"}),
        "enums": {
            "access": frozenset({"first-party-api", "cloud-platform", "gateway", "download"}),
            "input_modalities": frozenset({"text", "image", "video", "audio", "document"}),
            "output_modalities": frozenset({"text", "image", "audio", "video"}),
            "capabilities": frozenset({"code-generation", "computer-use"}),
        },
    },
}


class _CatalogJSONError(ValueError):
    """Raised for JSON accepted by Python but forbidden by the catalog contract."""


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _CatalogJSONError(f"duplicate object key {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> Any:
    raise _CatalogJSONError(f"non-finite number {value!r} is not valid catalog JSON")


def _finite_json_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise _CatalogJSONError(f"non-finite number {value!r} is not valid catalog JSON")
    return parsed


def load_json(path: Path) -> Any:
    display_path = _display_path(path)
    try:
        text = path.read_text(encoding="utf-8")
        return json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_json_constant,
            parse_float=_finite_json_float,
        )
    except FileNotFoundError:
        raise ValueError(f"missing file: {display_path}") from None
    except UnicodeDecodeError as exc:
        raise ValueError(f"invalid UTF-8 in {display_path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"invalid JSON in {display_path}:{exc.lineno}:{exc.colno}: {exc.msg}"
        ) from exc
    except _CatalogJSONError as exc:
        raise ValueError(f"invalid JSON in {display_path}: {exc}") from exc
    except ValueError as exc:
        # Python can raise plain ValueError for resource-limit violations such
        # as an integer literal with too many digits.
        raise ValueError(f"invalid JSON in {display_path}: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"cannot read {display_path}: {exc}") from exc


def _validate_non_empty_string(value: Any, where: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{where}: must be a non-empty string")


def _validate_nullable_string(value: Any, where: str, errors: list[str]) -> None:
    if value is not None:
        _validate_non_empty_string(value, where, errors)


def _validate_boolean(value: Any, where: str, errors: list[str]) -> None:
    if type(value) is not bool:
        errors.append(f"{where}: must be a boolean")


def _validate_enum(
    value: Any,
    allowed: frozenset[str],
    where: str,
    errors: list[str],
) -> None:
    if not isinstance(value, str) or value not in allowed:
        errors.append(f"{where}: invalid value {value!r}; expected one of {sorted(allowed)}")


def _validate_non_negative_number_or_null(
    value: Any,
    where: str,
    errors: list[str],
) -> None:
    if value is None:
        return
    invalid = isinstance(value, bool) or not isinstance(value, (int, float))
    if not invalid:
        invalid = (
            value < 0
            or value > MAX_CATALOG_NUMBER
            or (isinstance(value, float) and not math.isfinite(value))
        )
    if invalid:
        errors.append(
            f"{where}: must be a finite non-negative number or null no greater "
            f"than {MAX_CATALOG_NUMBER}"
        )


def _validate_string_array(
    value: Any,
    where: str,
    errors: list[str],
    *,
    allowed: frozenset[str] | None = None,
    allow_empty: bool = False,
) -> None:
    if not isinstance(value, list):
        qualifier = "unique" if allow_empty else "non-empty unique"
        errors.append(f"{where}: must be a {qualifier} string array")
        return
    if not value:
        if not allow_empty:
            errors.append(f"{where}: must be a non-empty unique string array")
        return

    seen: set[str] = set()
    for index, item in enumerate(value):
        item_where = f"{where}[{index}]"
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{item_where}: must be a non-empty string")
            continue
        if item in seen:
            errors.append(f"{where}: duplicate item {item!r}")
        seen.add(item)
        if allowed is not None and item not in allowed:
            errors.append(f"{item_where}: invalid value {item!r}; expected one of {sorted(allowed)}")


def _validate_source_url(value: Any, where: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{where}: source URL must be a string")
        return
    problem = static_https_url_error(value)
    if problem:
        errors.append(f"{where}: {problem}: {value!r}")


def validate_source(source: Any, where: str, errors: list[str]) -> None:
    if not isinstance(source, dict):
        errors.append(f"{where}: source must be an object")
        return

    required = {"label", "url"}
    missing = required - set(source)
    unknown = set(source) - required
    if missing:
        errors.append(f"{where}: missing fields: {', '.join(sorted(missing))}")
    if unknown:
        errors.append(f"{where}: unknown fields: {', '.join(sorted(unknown))}")
    if "label" in source:
        _validate_non_empty_string(source["label"], f"{where}.label", errors)
    if "url" in source:
        _validate_source_url(source["url"], f"{where}.url", errors)


def _validate_sources(value: Any, where: str, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{where}: must be a non-empty unique source array")
        return

    seen_urls: set[str] = set()
    for index, source in enumerate(value):
        validate_source(source, f"{where}[{index}]", errors)
        if isinstance(source, dict) and isinstance(source.get("url"), str):
            url = source["url"]
            if url in seen_urls:
                errors.append(f"{where}: duplicate source URL {url!r}")
            seen_urls.add(url)


def validate_pricing(pricing: Any, where: str, errors: list[str]) -> None:
    required = {"model", "free_tier", "starting_price_usd_month", "note"}
    if not isinstance(pricing, dict):
        errors.append(f"{where}: pricing must be an object")
        return
    missing = required - set(pricing)
    unknown = set(pricing) - required
    if missing:
        errors.append(f"{where}: missing fields: {', '.join(sorted(missing))}")
    if unknown:
        errors.append(f"{where}: unknown fields: {', '.join(sorted(unknown))}")
    if "model" in pricing:
        _validate_enum(
            pricing["model"],
            frozenset({"free", "subscription", "usage-based", "hybrid", "contact-sales"}),
            f"{where}.model",
            errors,
        )
    if "free_tier" in pricing and pricing["free_tier"] is not None and type(pricing["free_tier"]) is not bool:
        errors.append(f"{where}.free_tier: must be a boolean or null")
    if "starting_price_usd_month" in pricing:
        _validate_non_negative_number_or_null(
            pricing["starting_price_usd_month"],
            f"{where}.starting_price_usd_month",
            errors,
        )
    if (
        pricing.get("model") == "free"
        and pricing.get("starting_price_usd_month") != 0
    ):
        errors.append(
            f"{where}.starting_price_usd_month: free products must use 0"
        )
    if pricing.get("model") == "free" and pricing.get("free_tier") is not True:
        errors.append(f"{where}.free_tier: free products must use true")
    if "note" in pricing:
        _validate_non_empty_string(pricing["note"], f"{where}.note", errors)


def _validate_api_pricing(pricing: Any, where: str, errors: list[str]) -> None:
    if pricing is None:
        return
    required = {
        "input_usd_per_million", "cached_input_usd_per_million",
        "output_usd_per_million", "model", "note",
    }
    if not isinstance(pricing, dict):
        errors.append(f"{where}: api_pricing must be an object or null")
        return
    missing = required - set(pricing)
    unknown = set(pricing) - required
    if missing:
        errors.append(f"{where}: missing fields: {', '.join(sorted(missing))}")
    if unknown:
        errors.append(f"{where}: unknown fields: {', '.join(sorted(unknown))}")
    for field in (
        "input_usd_per_million", "cached_input_usd_per_million",
        "output_usd_per_million",
    ):
        if field in pricing:
            _validate_non_negative_number_or_null(pricing[field], f"{where}.{field}", errors)
    for field in ("model", "note"):
        if field in pricing:
            _validate_non_empty_string(pricing[field], f"{where}.{field}", errors)


def _validate_last_verified(
    value: Any,
    where: str,
    today: date,
    max_age_days: int | None,
    errors: list[str],
    warnings: list[str],
) -> None:
    if not isinstance(value, str) or not DATE_RE.fullmatch(value):
        errors.append(f"{where}: last_verified must use YYYY-MM-DD")
        return
    try:
        verified = date.fromisoformat(value)
    except ValueError:
        errors.append(f"{where}: last_verified must be a real calendar date in YYYY-MM-DD form")
        return

    if verified > today:
        errors.append(f"{where}: last_verified is in the future ({verified})")
        return
    age = (today - verified).days
    if age > 90:
        warnings.append(f"{where}: source check is {age} days old")
    if max_age_days is not None and age > max_age_days:
        errors.append(f"{where}: source check exceeds MAX_AGE_DAYS={max_age_days}")


def _validate_tool(
    record: dict[str, Any],
    config: CatalogConfig,
    where: str,
    errors: list[str],
) -> None:
    for field in ("name", "vendor"):
        if field in record:
            _validate_non_empty_string(record[field], f"{where}.{field}", errors)
    for field in ("status", "category", "execution", "model_policy"):
        if field in record:
            _validate_enum(record[field], config["enums"][field], f"{where}.{field}", errors)
    if "interfaces" in record:
        _validate_string_array(
            record["interfaces"], f"{where}.interfaces", errors,
            allowed=config["enums"]["interfaces"],
        )
    if "platforms" in record:
        _validate_tool_platforms(record["platforms"], f"{where}.platforms", errors)
    for field in ("open_source", "byok", "self_host"):
        if field in record:
            _validate_boolean(record[field], f"{where}.{field}", errors)
    if "license" in record:
        _validate_nullable_string(record["license"], f"{where}.license", errors)
    if "pricing" in record:
        validate_pricing(record["pricing"], f"{where}.pricing", errors)
    for field in ("best_for", "strengths", "limitations"):
        if field in record:
            _validate_string_array(record[field], f"{where}.{field}", errors)


def _validate_tool_platforms(value: Any, where: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{where}: must be an object")
        return

    missing = PLATFORM_FIELDS - set(value)
    unknown = set(value) - PLATFORM_FIELDS
    if missing:
        errors.append(f"{where}: missing fields: {', '.join(sorted(missing))}")
    if unknown:
        errors.append(f"{where}: unknown fields: {', '.join(sorted(unknown))}")

    for field, allowed in PLATFORM_ENUMS.items():
        if field in value:
            _validate_string_array(
                value[field],
                f"{where}.{field}",
                errors,
                allowed=allowed,
                allow_empty=True,
            )
    if "notes" in value:
        _validate_string_array(value["notes"], f"{where}.notes", errors, allow_empty=True)

    if not any(isinstance(value.get(field), list) and value[field] for field in PLATFORM_FIELDS):
        errors.append(f"{where}: at least one platform dimension must be non-empty")


def _validate_gateway(
    record: dict[str, Any],
    config: CatalogConfig,
    where: str,
    errors: list[str],
) -> None:
    for field in ("name", "vendor", "pricing_note"):
        if field in record:
            _validate_non_empty_string(record[field], f"{where}.{field}", errors)
    for field in ("kind", "delivery"):
        if field in record:
            _validate_enum(record[field], config["enums"][field], f"{where}.{field}", errors)
    for field in ("byok", "self_host", "open_source"):
        if field in record:
            _validate_boolean(record[field], f"{where}.{field}", errors)
    if "license" in record:
        _validate_nullable_string(record["license"], f"{where}.license", errors)
    for field in ("strengths", "limitations"):
        if field in record:
            _validate_string_array(record[field], f"{where}.{field}", errors)


def _validate_model(
    record: dict[str, Any],
    config: CatalogConfig,
    where: str,
    errors: list[str],
) -> None:
    for field in ("provider", "family"):
        if field in record:
            _validate_non_empty_string(record[field], f"{where}.{field}", errors)
    for field in ("representative_models", "coding_notes", "limitations"):
        if field in record:
            _validate_string_array(record[field], f"{where}.{field}", errors)
    for field in ("input_modalities", "output_modalities", "capabilities"):
        if field in record:
            _validate_string_array(
                record[field],
                f"{where}.{field}",
                errors,
                allowed=config["enums"][field],
            )
    if (
        isinstance(record.get("capabilities"), list)
        and "code-generation" not in record["capabilities"]
    ):
        errors.append(f"{where}.capabilities: must include 'code-generation'")
    if "access" in record:
        _validate_string_array(
            record["access"], f"{where}.access", errors,
            allowed=config["enums"]["access"],
        )
    if "open_weights" in record:
        _validate_boolean(record["open_weights"], f"{where}.open_weights", errors)
    for field in ("weight_license", "context_note"):
        if field in record:
            _validate_nullable_string(record[field], f"{where}.{field}", errors)
    if "api_pricing" in record:
        _validate_api_pricing(record["api_pricing"], f"{where}.api_pricing", errors)


def validate_record(
    catalog: str,
    record: Any,
    index: int,
    config: CatalogConfig,
    today: date,
    max_age_days: int | None,
    errors: list[str],
    warnings: list[str],
) -> None:
    where = f"{catalog}[{index}]"
    if not isinstance(record, dict):
        errors.append(f"{where}: record must be an object")
        return

    allowed_fields = config["required"] | config["optional"]
    missing = config["required"] - set(record)
    unknown = set(record) - allowed_fields
    if missing:
        errors.append(f"{where}: missing fields: {', '.join(sorted(missing))}")
    if unknown:
        errors.append(f"{where}: unknown fields: {', '.join(sorted(unknown))}")

    if "id" in record:
        record_id = record["id"]
        if not isinstance(record_id, str) or not ID_RE.fullmatch(record_id):
            errors.append(f"{where}.id: invalid id {record_id!r}")
        else:
            where = f"{catalog}:{record_id}"

    if catalog == "tools":
        _validate_tool(record, config, where, errors)
    elif catalog == "gateways":
        _validate_gateway(record, config, where, errors)
    elif catalog == "models":
        _validate_model(record, config, where, errors)
    else:
        errors.append(f"{where}: unknown catalog {catalog!r}")

    if "official_sources" in record:
        _validate_sources(record["official_sources"], f"{where}.official_sources", errors)
    if "last_verified" in record:
        _validate_last_verified(
            record["last_verified"],
            where,
            today,
            max_age_days,
            errors,
            warnings,
        )


def validate_all(max_age_days: int | None = None) -> tuple[list[str], list[str], dict[str, int]]:
    if (
        max_age_days is not None
        and (type(max_age_days) is not int or max_age_days < 0)
    ):
        raise ValueError("max_age_days must be a non-negative integer or None")

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
        seen_ids: set[str] = set()
        seen_records: set[str] = set()
        for index, record in enumerate(records):
            fingerprint = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            if fingerprint in seen_records:
                errors.append(f"{catalog}[{index}]: duplicate record")
            seen_records.add(fingerprint)

            validate_record(catalog, record, index, config, today, max_age_days, errors, warnings)
            if isinstance(record, dict) and isinstance(record.get("id"), str):
                record_id = record["id"]
                if record_id in seen_ids:
                    errors.append(f"{catalog}: duplicate id {record_id!r}")
                seen_ids.add(record_id)

    return errors, warnings, counts


def _non_negative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return parsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    env_max_age = os.getenv("MAX_AGE_DAYS") or None
    if env_max_age is not None:
        try:
            default_max_age = _non_negative_int(env_max_age)
        except argparse.ArgumentTypeError as exc:
            parser.error(f"MAX_AGE_DAYS {exc}")
    else:
        default_max_age = None
    parser.add_argument(
        "--max-age-days",
        type=_non_negative_int,
        default=default_max_age,
        help="fail records older than this many days",
    )
    args = parser.parse_args(argv)

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
