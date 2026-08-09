from __future__ import annotations

import copy
import importlib.util
import io
import json
import math
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
SPEC = importlib.util.spec_from_file_location(
    "validate_catalog", ROOT / "scripts" / "validate_catalog.py"
)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)

SCHEMA_FILES = {
    "tools": "tool.schema.json",
    "gateways": "gateway.schema.json",
    "models": "model-family.schema.json",
}
BASE_RECORDS = {
    name: VALIDATOR.load_json(config["path"])[0]
    for name, config in VALIDATOR.CATALOGS.items()
}
BASE_TODAY = max(
    date.today(),
    *(date.fromisoformat(record["last_verified"]) for record in BASE_RECORDS.values()),
)


class CatalogTests(unittest.TestCase):
    def validate_record(
        self,
        catalog: str,
        record: Any,
        *,
        today: date = BASE_TODAY,
        max_age_days: int | None = None,
    ) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []
        VALIDATOR.validate_record(
            catalog,
            record,
            0,
            VALIDATOR.CATALOGS[catalog],
            today,
            max_age_days,
            errors,
            warnings,
        )
        return errors, warnings

    def mutated_errors(
        self,
        catalog: str,
        mutate: Callable[[dict[str, Any]], None],
    ) -> list[str]:
        record = copy.deepcopy(BASE_RECORDS[catalog])
        mutate(record)
        errors, _warnings = self.validate_record(catalog, record)
        return errors

    def assert_invalid(
        self,
        catalog: str,
        description: str,
        mutate: Callable[[dict[str, Any]], None],
        fragment: str,
    ) -> None:
        with self.subTest(catalog=catalog, case=description):
            errors = self.mutated_errors(catalog, mutate)
            self.assertTrue(
                any(fragment in error for error in errors),
                f"expected {fragment!r}; got {errors!r}",
            )

    @staticmethod
    def set_path(record: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
        target: dict[str, Any] = record
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value

    @staticmethod
    def mutation(
        function: Callable[[dict[str, Any]], None],
    ) -> Callable[[dict[str, Any]], None]:
        """Give dynamic test mutations an explicit callable type."""

        return function

    @staticmethod
    def set_field_mutation(
        field: str,
        value: Any,
    ) -> Callable[[dict[str, Any]], None]:
        def mutate(record: dict[str, Any]) -> None:
            record[field] = value

        return mutate

    @staticmethod
    def set_path_mutation(
        path: tuple[str, ...],
        value: Any,
    ) -> Callable[[dict[str, Any]], None]:
        def mutate(record: dict[str, Any]) -> None:
            CatalogTests.set_path(record, path, value)

        return mutate

    @staticmethod
    def pop_path_mutation(path: tuple[str, ...]) -> Callable[[dict[str, Any]], None]:
        def mutate(record: dict[str, Any]) -> None:
            target: dict[str, Any] = record
            for key in path[:-1]:
                target = target[key]
            target.pop(path[-1])

        return mutate

    @staticmethod
    def duplicate_item_mutation(field: str) -> Callable[[dict[str, Any]], None]:
        def mutate(record: dict[str, Any]) -> None:
            record[field] = [
                copy.deepcopy(record[field][0]),
                copy.deepcopy(record[field][0]),
            ]

        return mutate

    @staticmethod
    def set_source_url_mutation(value: Any) -> Callable[[dict[str, Any]], None]:
        def mutate(record: dict[str, Any]) -> None:
            record["official_sources"][0]["url"] = value

        return mutate

    def test_catalogs_validate(self) -> None:
        errors, _warnings, counts = VALIDATOR.validate_all()
        self.assertEqual(errors, [])
        self.assertEqual(counts, {"tools": 33, "gateways": 13, "models": 14})

    def test_schemas_describe_complete_catalogs_and_match_validator_fields(self) -> None:
        for catalog, filename in SCHEMA_FILES.items():
            with self.subTest(catalog=catalog):
                schema = VALIDATOR.load_json(ROOT / "schema" / filename)
                item_schema = schema["items"]
                config = VALIDATOR.CATALOGS[catalog]
                self.assertEqual(schema["type"], "array")
                self.assertEqual(schema["minItems"], 1)
                self.assertIs(schema["uniqueItems"], True)
                self.assertEqual(item_schema["type"], "object")
                self.assertIs(item_schema["additionalProperties"], False)
                self.assertEqual(set(item_schema["required"]), set(config["required"]))
                self.assertEqual(
                    set(item_schema["properties"]),
                    set(config["required"] | config["optional"]),
                )
                self.assertEqual(
                    schema["$id"],
                    f"https://raw.githubusercontent.com/Yunushan/llm-tool-atlas/main/schema/{filename}",
                )
                for field, allowed in config["enums"].items():
                    property_schema = item_schema["properties"][field]
                    schema_values = (
                        property_schema["items"]["enum"]
                        if property_schema.get("type") == "array"
                        else property_schema["enum"]
                    )
                    self.assertEqual(set(schema_values), set(allowed))

                if catalog == "tools":
                    platform_schema = item_schema["properties"]["platforms"]
                    self.assertEqual(set(platform_schema["required"]), set(VALIDATOR.PLATFORM_FIELDS))
                    self.assertIs(platform_schema["additionalProperties"], False)
                    for field, allowed in VALIDATOR.PLATFORM_ENUMS.items():
                        self.assertEqual(
                            set(platform_schema["properties"][field]["items"]["enum"]),
                            set(allowed),
                        )
                    price_schema = item_schema["properties"]["pricing"]
                    self.assertEqual(
                        price_schema["properties"]["starting_price_usd_month"][
                            "maximum"
                        ],
                        VALIDATOR.MAX_CATALOG_NUMBER,
                    )
                    self.assertEqual(
                        price_schema["allOf"][0]["then"]["properties"][
                            "free_tier"
                        ]["const"],
                        True,
                    )
                elif catalog == "models":
                    pricing_properties = item_schema["properties"]["api_pricing"][
                        "properties"
                    ]
                    for price_field in (
                        "input_usd_per_million",
                        "cached_input_usd_per_million",
                        "output_usd_per_million",
                    ):
                        self.assertEqual(
                            pricing_properties[price_field]["maximum"],
                            VALIDATOR.MAX_CATALOG_NUMBER,
                        )
                    self.assertEqual(
                        item_schema["properties"]["capabilities"]["contains"][
                            "const"
                        ],
                        "code-generation",
                    )

    def test_optional_fields_may_be_omitted_or_nullable_when_declared(self) -> None:
        for catalog, config in VALIDATOR.CATALOGS.items():
            for field in config["optional"]:
                with self.subTest(catalog=catalog, field=field, case="omitted"):
                    record = copy.deepcopy(BASE_RECORDS[catalog])
                    record.pop(field, None)
                    errors, _warnings = self.validate_record(catalog, record)
                    self.assertEqual(errors, [])

        nullable_fields = {
            "tools": ("license",),
            "gateways": ("license",),
            "models": ("weight_license", "context_note", "api_pricing"),
        }
        for catalog, fields in nullable_fields.items():
            for field in fields:
                with self.subTest(catalog=catalog, field=field, case="null"):
                    record = copy.deepcopy(BASE_RECORDS[catalog])
                    record[field] = None
                    errors, _warnings = self.validate_record(catalog, record)
                    self.assertEqual(errors, [])

    def test_record_shape_id_and_required_fields(self) -> None:
        errors, _warnings = self.validate_record("tools", "not an object")
        self.assertTrue(any("record must be an object" in error for error in errors))

        cases = [
            ("tools", "missing field", self.mutation(lambda r: r.pop("name")), "missing fields: name"),
            ("tools", "unknown field", self.mutation(lambda r: r.__setitem__("vendro", "typo")), "unknown fields: vendro"),
            ("tools", "invalid id syntax", self.mutation(lambda r: r.__setitem__("id", "Bad ID")), "invalid id"),
            ("gateways", "id wrong type", self.mutation(lambda r: r.__setitem__("id", 123)), "invalid id"),
            ("models", "empty id", self.mutation(lambda r: r.__setitem__("id", "")), "invalid id"),
        ]
        for case in cases:
            self.assert_invalid(*case)

    def test_all_scalar_string_fields_reject_wrong_types_and_whitespace(self) -> None:
        paths = {
            "tools": (
                ("name",), ("vendor",), ("license",), ("pricing", "note"),
            ),
            "gateways": (
                ("name",), ("vendor",), ("license",), ("pricing_note",),
            ),
            "models": (
                ("provider",), ("family",), ("weight_license",), ("context_note",),
                ("api_pricing", "model"), ("api_pricing", "note"),
            ),
        }
        for catalog, field_paths in paths.items():
            for field_path in field_paths:
                for invalid in (123, "   "):
                    self.assert_invalid(
                        catalog,
                        f"{'.'.join(field_path)}={invalid!r}",
                        self.set_path_mutation(field_path, invalid),
                        "must be a non-empty string",
                    )

    def test_all_boolean_fields_require_actual_booleans(self) -> None:
        fields = {
            "tools": ("open_source", "byok", "self_host"),
            "gateways": ("byok", "self_host", "open_source"),
            "models": ("open_weights",),
        }
        for catalog, catalog_fields in fields.items():
            for field in catalog_fields:
                self.assert_invalid(
                    catalog,
                    f"{field} integer masquerading as boolean",
                    self.set_field_mutation(field, 1),
                    "must be a boolean",
                )

    def test_all_enums_reject_unknown_values(self) -> None:
        scalar_fields = {
            "tools": ("status", "category", "execution", "model_policy"),
            "gateways": ("kind", "delivery"),
        }
        for catalog, fields in scalar_fields.items():
            for field in fields:
                self.assert_invalid(
                    catalog,
                    f"unknown {field}",
                    self.set_field_mutation(field, "not-a-valid-value"),
                    "invalid value",
                )

        self.assert_invalid(
            "tools",
            "unknown interface",
            self.set_field_mutation("interfaces", ["telepathy"]),
            "invalid value",
        )
        self.assert_invalid(
            "models",
            "unknown access mode",
            self.set_field_mutation("access", ["sneakernet"]),
            "invalid value",
        )
        self.assert_invalid(
            "tools",
            "unknown pricing model",
            self.set_path_mutation(("pricing", "model"), "mystery"),
            "invalid value",
        )

    def test_every_array_rejects_empty_duplicate_wrong_container_and_bad_items(self) -> None:
        fields = {
            "tools": (
                "interfaces", "best_for", "strengths", "limitations", "official_sources",
            ),
            "gateways": ("strengths", "limitations", "official_sources"),
            "models": (
                "representative_models", "access", "input_modalities",
                "output_modalities", "capabilities", "coding_notes", "limitations",
                "official_sources",
            ),
        }
        for catalog, catalog_fields in fields.items():
            for field in catalog_fields:
                self.assert_invalid(
                    catalog,
                    f"empty {field}",
                    self.set_field_mutation(field, []),
                    "non-empty",
                )
                self.assert_invalid(
                    catalog,
                    f"non-array {field}",
                    self.set_field_mutation(field, "not-an-array"),
                    "non-empty",
                )
                duplicate_fragment = "duplicate source URL" if field == "official_sources" else "duplicate item"
                self.assert_invalid(
                    catalog,
                    f"duplicate {field}",
                    self.duplicate_item_mutation(field),
                    duplicate_fragment,
                )
                bad_item_fragment = "source must be an object" if field == "official_sources" else "must be a non-empty string"
                self.assert_invalid(
                    catalog,
                    f"wrong item type in {field}",
                    self.set_field_mutation(field, [123]),
                    bad_item_fragment,
                )

    def test_structured_tool_platform_matrix_contract(self) -> None:
        valid_platforms = {
            "operating_systems": ["windows"],
            "editors": [],
            "deployment": [],
            "integrations": [],
            "notes": [],
        }
        record = copy.deepcopy(BASE_RECORDS["tools"])
        record["platforms"] = copy.deepcopy(valid_platforms)
        errors, _warnings = self.validate_record("tools", record)
        self.assertEqual(errors, [])

        self.assert_invalid(
            "tools",
            "platform matrix wrong type",
            self.set_field_mutation("platforms", []),
            "platforms: must be an object",
        )
        for field in VALIDATOR.PLATFORM_FIELDS:
            self.assert_invalid(
                "tools",
                f"missing platform field {field}",
                self.set_field_mutation(
                    "platforms",
                    {key: copy.deepcopy(value) for key, value in valid_platforms.items() if key != field},
                ),
                f"missing fields: {field}",
            )
            self.assert_invalid(
                "tools",
                f"platform field {field} wrong type",
                self.set_field_mutation(
                    "platforms",
                    {**copy.deepcopy(valid_platforms), field: "not-an-array"},
                ),
                "unique string array",
            )

        self.assert_invalid(
            "tools",
            "unknown platform field",
            self.set_field_mutation(
                "platforms", {**copy.deepcopy(valid_platforms), "other": []}
            ),
            "unknown fields: other",
        )
        self.assert_invalid(
            "tools",
            "all platform dimensions empty",
            self.set_field_mutation(
                "platforms", {field: [] for field in VALIDATOR.PLATFORM_FIELDS}
            ),
            "at least one platform dimension must be non-empty",
        )

        valid_values = {
            "operating_systems": "windows",
            "editors": "vs-code",
            "deployment": "wsl",
            "integrations": "github",
            "notes": "Vendor documentation does not state broader support.",
        }
        for field, value in valid_values.items():
            self.assert_invalid(
                "tools",
                f"duplicate platform item in {field}",
                self.set_field_mutation(
                    "platforms", {**copy.deepcopy(valid_platforms), field: [value, value]}
                ),
                "duplicate item",
            )

        for field in VALIDATOR.PLATFORM_ENUMS:
            self.assert_invalid(
                "tools",
                f"unknown platform enum in {field}",
                self.set_field_mutation(
                    "platforms", {**copy.deepcopy(valid_platforms), field: ["unknown"]}
                ),
                "invalid value",
            )
        self.assert_invalid(
            "tools",
            "empty platform note",
            self.set_field_mutation(
                "platforms", {**copy.deepcopy(valid_platforms), "notes": [" "]}
            ),
            "must be a non-empty string",
        )

    def test_tool_pricing_contract_and_finite_numbers(self) -> None:
        cases = [
            ("non-object", lambda r: r.__setitem__("pricing", []), "pricing must be an object"),
            ("missing key", lambda r: r["pricing"].pop("note"), "missing fields: note"),
            ("unknown key", lambda r: r["pricing"].__setitem__("currency", "USD"), "unknown fields: currency"),
            ("integer free_tier", lambda r: r["pricing"].__setitem__("free_tier", 1), "boolean or null"),
            ("string free_tier", lambda r: r["pricing"].__setitem__("free_tier", "yes"), "boolean or null"),
        ]
        for description, mutate, fragment in cases:
            self.assert_invalid("tools", description, mutate, fragment)

        for invalid in (
            True,
            "1.0",
            -0.01,
            math.nan,
            math.inf,
            -math.inf,
            10**400,
        ):
            self.assert_invalid(
                "tools",
                f"invalid starting price {invalid!r}",
                self.set_path_mutation(
                    ("pricing", "starting_price_usd_month"), invalid
                ),
                "finite non-negative number or null",
            )

        self.assert_invalid(
            "tools",
            "free product without zero entry price",
            lambda record: record["pricing"].__setitem__(
                "starting_price_usd_month", None
            ),
            "free products must use 0",
        )
        self.assert_invalid(
            "tools",
            "free product without a free tier",
            lambda record: record["pricing"].__setitem__("free_tier", False),
            "free products must use true",
        )

    def test_model_modality_and_capability_vocabulary(self) -> None:
        for field in ("input_modalities", "output_modalities", "capabilities"):
            self.assert_invalid(
                "models",
                f"unknown {field}",
                self.set_field_mutation(field, ["unknown"]),
                "invalid value",
            )
        self.assert_invalid(
            "models",
            "missing code-generation capability",
            self.set_field_mutation("capabilities", ["computer-use"]),
            "must include 'code-generation'",
        )

    def test_model_api_pricing_contract_and_finite_numbers(self) -> None:
        cases = [
            ("non-object", lambda r: r.__setitem__("api_pricing", []), "object or null"),
            ("missing key", lambda r: r["api_pricing"].pop("note"), "missing fields: note"),
            ("unknown key", lambda r: r["api_pricing"].__setitem__("currency", "USD"), "unknown fields: currency"),
        ]
        for description, mutate, fragment in cases:
            self.assert_invalid("models", description, mutate, fragment)

        numeric_fields = (
            "input_usd_per_million",
            "cached_input_usd_per_million",
            "output_usd_per_million",
        )
        for field in numeric_fields:
            for invalid in (False, "1.0", -1, math.nan, math.inf, 10**400):
                self.assert_invalid(
                    "models",
                    f"{field}={invalid!r}",
                    self.set_path_mutation(("api_pricing", field), invalid),
                    "finite non-negative number or null",
                )

    def test_sources_require_safe_absolute_https_urls(self) -> None:
        valid_urls = (
            "https://example.com/path?query=yes#section",
            "https://example.com:443/path",
            "https://8.8.8.8/",
            "https://[2606:4700:4700::1111]/",
        )
        for url in valid_urls:
            with self.subTest(url=url, expected="valid"):
                record = copy.deepcopy(BASE_RECORDS["tools"])
                record["official_sources"][0]["url"] = url
                errors, _warnings = self.validate_record("tools", record)
                self.assertEqual(errors, [])

        invalid_urls = {
            "http://example.com": "absolute HTTPS",
            "HTTPS://example.com": "absolute HTTPS",
            "/relative/path": "absolute HTTPS",
            "https://user@example.com/path": "credentials",
            "https://user:secret@example.com/path": "credentials",
            "https://example.com:444/path": "port 443",
            "https://example.com:bad/path": "invalid source URL",
            "https://localhost/path": "localhost",
            "https://service.localhost/path": "localhost",
            "https://metadata.internal/path": "special-use hostname",
            "https://singlelabel/path": "fully qualified",
            "https://example.com\\@127.0.0.1/path": "backslashes",
            "https://example.com/<unsafe>": "angle brackets",
            "https://127.0.0.1/path": "private or reserved",
            "https://10.0.0.1/path": "private or reserved",
            "https://169.254.169.254/path": "private or reserved",
            "https://192.0.2.1/path": "private or reserved",
            "https://0.0.0.0/path": "private or reserved",
            "https://100.64.0.1/path": "private or reserved",
            "https://224.0.0.1/path": "private or reserved",
            "https://[::1]/path": "private or reserved",
            "https://[fc00::1]/path": "private or reserved",
            "https://[ff02::1]/path": "private or reserved",
            "https://127.1/path": "non-canonical IP literal",
            "https://2130706433/path": "non-canonical IP literal",
            " https://example.com": "whitespace",
        }
        for url, fragment in invalid_urls.items():
            self.assert_invalid(
                "tools",
                f"unsafe URL {url}",
                self.set_source_url_mutation(url),
                fragment,
            )

        source_cases = [
            ("missing label", lambda r: r["official_sources"][0].pop("label"), "missing fields: label"),
            ("unknown source field", lambda r: r["official_sources"][0].__setitem__("note", "x"), "unknown fields: note"),
            ("empty label", lambda r: r["official_sources"][0].__setitem__("label", " "), "non-empty string"),
            ("URL wrong type", lambda r: r["official_sources"][0].__setitem__("url", 42), "URL must be a string"),
        ]
        for description, mutate, fragment in source_cases:
            self.assert_invalid("tools", description, mutate, fragment)

    def test_dates_are_strict_real_and_respect_freshness_limits(self) -> None:
        invalid_values = ("20260804", "2026-W32-2", "2026-02-30", 20260804)
        for value in invalid_values:
            self.assert_invalid(
                "tools",
                f"invalid date {value!r}",
                self.set_field_mutation("last_verified", value),
                "last_verified",
            )

        today = date(2026, 8, 4)
        record = copy.deepcopy(BASE_RECORDS["tools"])
        record["last_verified"] = (today + timedelta(days=1)).isoformat()
        errors, _warnings = self.validate_record("tools", record, today=today)
        self.assertTrue(any("in the future" in error for error in errors))

        record["last_verified"] = (today - timedelta(days=91)).isoformat()
        errors, warnings = self.validate_record("tools", record, today=today, max_age_days=90)
        self.assertTrue(any("MAX_AGE_DAYS=90" in error for error in errors))
        self.assertTrue(any("91 days old" in warning for warning in warnings))

    def test_strict_json_loader_rejects_duplicates_and_non_finite_numbers(self) -> None:
        cases = {
            '[{"id": "first", "id": "second"}]': "duplicate object key",
            "[NaN]": "non-finite number",
            "[Infinity]": "non-finite number",
            "[-Infinity]": "non-finite number",
            "[1e999]": "non-finite number",
            '[{"broken":]': "invalid JSON",
        }
        cases["[" + "1" * 5000 + "]"] = "invalid JSON"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            for content, fragment in cases.items():
                with self.subTest(content=content):
                    path.write_text(content, encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, fragment):
                        VALIDATOR.load_json(path)

            path.write_bytes(b"\xff")
            with self.assertRaisesRegex(ValueError, "invalid UTF-8"):
                VALIDATOR.load_json(path)
            with self.assertRaisesRegex(ValueError, "missing file"):
                VALIDATOR.load_json(Path(directory) / "missing.json")

    def test_catalog_root_array_duplicate_record_and_duplicate_id_contracts(self) -> None:
        config = copy.deepcopy(VALIDATOR.CATALOGS["tools"])
        base = copy.deepcopy(BASE_RECORDS["tools"])
        cases = [
            (json.dumps({"not": "an array"}), "root must be a non-empty array"),
            ("[]", "root must be a non-empty array"),
            (json.dumps([base, base]), "duplicate record"),
            (
                json.dumps([base, {**base, "name": f"{base['name']} renamed"}]),
                "duplicate id",
            ),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tools.json"
            config["path"] = path
            for content, fragment in cases:
                with self.subTest(fragment=fragment):
                    path.write_text(content, encoding="utf-8")
                    with patch.dict(VALIDATOR.CATALOGS, {"tools": config}, clear=True):
                        errors, _warnings, _counts = VALIDATOR.validate_all()
                    self.assertTrue(
                        any(fragment in error for error in errors),
                        f"expected {fragment!r}; got {errors!r}",
                    )

    def test_max_age_configuration_rejects_invalid_values_cleanly(self) -> None:
        self.assertEqual(VALIDATOR._non_negative_int("0"), 0)
        self.assertEqual(VALIDATOR._non_negative_int("120"), 120)
        with self.assertRaises(ValueError):
            VALIDATOR.validate_all(-1)
        with self.assertRaises(ValueError):
            VALIDATOR.validate_all(True)

        for env_value in ("not-a-number", "-1"):
            with self.subTest(source="environment", value=env_value):
                stderr = io.StringIO()
                with patch.dict(os.environ, {"MAX_AGE_DAYS": env_value}), redirect_stderr(stderr):
                    with self.assertRaises(SystemExit) as raised:
                        VALIDATOR.main([])
                self.assertEqual(raised.exception.code, 2)
                self.assertIn("MAX_AGE_DAYS must be a non-negative integer", stderr.getvalue())
                self.assertNotIn("Traceback", stderr.getvalue())

        stderr = io.StringIO()
        with patch.dict(os.environ, {"MAX_AGE_DAYS": ""}), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                VALIDATOR.main(["--max-age-days", "-1"])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("must be a non-negative integer", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.dict(os.environ, {"MAX_AGE_DAYS": ""}), redirect_stdout(stdout), redirect_stderr(stderr):
            result = VALIDATOR.main([])
        self.assertEqual(result, 0)
        self.assertIn("catalog valid", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
