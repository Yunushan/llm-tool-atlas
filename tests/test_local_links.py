from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_local_links", ROOT / "scripts" / "check_local_links.py"
)
assert SPEC and SPEC.loader
CHECKER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CHECKER
SPEC.loader.exec_module(CHECKER)


class ParserTests(unittest.TestCase):
    def test_balanced_and_angle_bracket_destinations(self) -> None:
        line = "[one](docs/a_(b).md) [two](<docs/file name.md>)"
        self.assertEqual(
            CHECKER.inline_destinations(line),
            ["docs/a_(b).md", "docs/file name.md"],
        )

    def test_code_spans_and_fences_are_ignored(self) -> None:
        text = "`[inline](missing.md)`\n```md\n[fenced](missing.md)\n```\n"
        visible = CHECKER.visible_lines(text)
        self.assertEqual(len(visible), 1)
        self.assertNotIn("missing.md", visible[0][1])

    def test_duplicate_heading_anchors_match_github_suffixes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "doc.md"
            path.write_text("# Hello, World!\n# Hello World\n", encoding="utf-8")
            self.assertEqual(
                CHECKER.markdown_anchors(path), {"hello-world", "hello-world-1"}
            )


class RepositoryLinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        (self.root / "docs").mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write(self, relative: str, content: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        return path

    def test_inline_links_with_spaces_parentheses_and_fragments(self) -> None:
        self.write("docs/file name.md", "# Install Now\n")
        self.write("docs/a_(b).md", "# Parentheses\n")
        self.write(
            "README.md",
            "[space](<docs/file name.md#install-now>)\n"
            "[paren](docs/a_(b).md#parentheses)\n",
        )
        problems, checked = CHECKER.check_links(self.root)
        self.assertEqual(problems, [])
        self.assertEqual(checked, 2)

    def test_reference_definition_and_undefined_reference(self) -> None:
        self.write("docs/guide.md", "# Guide\n")
        self.write(
            "README.md",
            "[Guide][docs]\n[Broken][missing]\n\n[docs]: docs/guide.md\n",
        )
        problems, checked = CHECKER.check_links(self.root)
        self.assertEqual(checked, 1)
        self.assertEqual(len(problems), 1)
        self.assertIn("undefined Markdown reference: missing", problems[0])

    def test_missing_fragment_is_reported(self) -> None:
        self.write("docs/guide.md", "# Existing\n")
        self.write("README.md", "[Guide](docs/guide.md#missing)\n")
        problems, _checked = CHECKER.check_links(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("missing Markdown heading fragment", problems[0])

    def test_repository_escape_is_reported(self) -> None:
        self.write("README.md", "[Outside](../outside.md)\n")
        problems, _checked = CHECKER.check_links(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("link escapes repository", problems[0])

    def test_invalid_local_path_is_reported_without_crashing(self) -> None:
        markdown = self.write("README.md", "")
        with patch.object(CHECKER.Path, "resolve", side_effect=ValueError("bad path")):
            problem = CHECKER.check_destination(
                "docs/broken.md", markdown, 1, self.root, {}
            )
        self.assertIsNotNone(problem)
        assert problem is not None
        self.assertIn("invalid local link path", problem)

    def test_unsafe_scheme_is_reported(self) -> None:
        self.write("README.md", "[Run](javascript:alert(1))\n")
        problems, checked = CHECKER.check_links(self.root)
        self.assertEqual(checked, 0)
        self.assertEqual(len(problems), 1)
        self.assertIn("unsafe or unsupported URL scheme", problems[0])

    def test_wrong_case_is_reported_portably(self) -> None:
        self.write("docs/Guide.md", "# Guide\n")
        self.write("README.md", "[Guide](docs/guide.md)\n")
        problems, _checked = CHECKER.check_links(self.root)
        self.assertEqual(len(problems), 1)
        self.assertTrue(
            "incorrect letter case" in problems[0] or "missing target" in problems[0]
        )


if __name__ == "__main__":
    unittest.main()
