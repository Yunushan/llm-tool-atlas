from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_catalog", ROOT / "scripts" / "validate_catalog.py"
)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class CatalogTests(unittest.TestCase):
    def test_catalogs_validate(self) -> None:
        errors, _warnings, _counts = VALIDATOR.validate_all()
        self.assertEqual(errors, [])

    def test_broad_initial_coverage(self) -> None:
        errors, _warnings, counts = VALIDATOR.validate_all()
        self.assertEqual(errors, [])
        self.assertGreaterEqual(counts["tools"], 25)
        self.assertGreaterEqual(counts["gateways"], 10)
        self.assertGreaterEqual(counts["models"], 12)


if __name__ == "__main__":
    unittest.main()
