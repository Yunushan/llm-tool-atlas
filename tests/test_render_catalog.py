from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
SPEC = importlib.util.spec_from_file_location(
    "render_catalog", ROOT / "scripts" / "render_catalog.py"
)
assert SPEC and SPEC.loader
RENDERER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RENDERER
SPEC.loader.exec_module(RENDERER)


class EscapingTests(unittest.TestCase):
    def test_plain_text_cannot_create_markdown_or_html(self) -> None:
        payload = "[click](https://evil.invalid) ![track](x) <img> **bold** | cell"
        escaped = RENDERER.cell(payload)
        self.assertIn(r"\[click\]", escaped)
        self.assertIn(r"\!\[track\]", escaped)
        self.assertIn(r"\<img\>", escaped)
        self.assertIn(r"\*\*bold\*\*", escaped)
        self.assertIn(r"\|", escaped)
        self.assertNotIn("![track]", escaped)

    def test_multiline_text_is_flattened(self) -> None:
        self.assertEqual(RENDERER.cell("one\r\ntwo\nthree"), "one two three")

    def test_source_links_escape_labels_and_wrap_destinations(self) -> None:
        rendered = RENDERER.sources(
            {
                "official_sources": [
                    {
                        "label": "[Official] *docs*",
                        "url": "https://example.com/a_(b)",
                    }
                ]
            }
        )
        self.assertEqual(
            rendered,
            r"[\[Official\] \*docs\*](<https://example.com/a_(b)>)",
        )

    def test_unsafe_markdown_destinations_are_rejected(self) -> None:
        unsafe = (
            "http://example.com",
            "https://example.com/a b",
            "https://example.com/<script>",
            "https://example.com\\escape",
        )
        for url in unsafe:
            with self.subTest(url=url), self.assertRaises(ValueError):
                RENDERER.markdown_url(url)


class RenderingTests(unittest.TestCase):
    @staticmethod
    def tool(name: str) -> dict[str, object]:
        return {
            "id": name.casefold(),
            "name": name,
            "status": "active",
            "category": "cli-agent",
            "interfaces": ["cli"],
            "platforms": {
                "operating_systems": ["linux"],
                "editors": ["vs-code"],
                "deployment": ["containers"],
                "integrations": ["github"],
                "notes": ["Test-only note"],
            },
            "model_policy": "provider-agnostic",
            "byok": True,
            "open_source": True,
            "pricing": {
                "model": "free",
                "free_tier": True,
                "starting_price_usd_month": None,
                "note": "Free",
            },
            "best_for": ["Tests"],
            "last_verified": "2026-08-04",
            "official_sources": [
                {"label": "Docs", "url": "https://example.com/docs"}
            ],
        }

    def test_tool_rows_are_sorted_case_insensitively(self) -> None:
        rendered = RENDERER.render_tools([self.tool("Zulu"), self.tool("alpha")])
        self.assertLess(rendered.index("**alpha**"), rendered.index("**Zulu**"))
        self.assertIn(
            "OS: Linux; Editors: VS Code; Deploy: Containers; "
            "Integrations: GitHub; Test-only note",
            rendered,
        )

    def test_check_mode_does_not_create_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            test_root = Path(temporary)
            output = test_root / "does-not-exist"
            with (
                patch.object(RENDERER, "ROOT", test_root),
                patch.object(RENDERER, "OUTPUT", output),
                patch.object(RENDERER, "load", return_value=[]),
                patch.object(RENDERER, "render_tools", return_value="tools\n"),
                patch.object(RENDERER, "render_gateways", return_value="gateways\n"),
                patch.object(RENDERER, "render_models", return_value="models\n"),
            ):
                self.assertEqual(RENDERER.main(["--check"]), 1)
            self.assertFalse(output.exists())

    def test_load_uses_strict_catalog_json_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            data = Path(temporary)
            (data / "tools.json").write_text(
                '[{"id": "one", "id": "two"}]\n', encoding="utf-8"
            )
            with patch.object(RENDERER, "DATA", data):
                with self.assertRaisesRegex(ValueError, "duplicate object key"):
                    RENDERER.load("tools")


if __name__ == "__main__":
    unittest.main()
