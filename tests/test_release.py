from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):  # type: ignore[no-untyped-def]
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


CHECK_RELEASE = load_script("check_release")
BUILD_RELEASE = load_script("build_release")
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
TAG = f"v{VERSION}"


class ReleaseMetadataTests(unittest.TestCase):
    def test_all_workflow_actions_are_full_sha_pinned(self) -> None:
        pattern = re.compile(r"^\s*uses:\s+[^\s@]+@([0-9a-f]{40})(?:\s+#.*)?$")
        workflow_dir = ROOT / ".github" / "workflows"
        workflow_files = sorted({*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")})
        self.assertGreaterEqual(len(workflow_files), 4)
        for workflow in workflow_files:
            for line_number, line in enumerate(
                workflow.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if "uses:" not in line:
                    continue
                self.assertRegex(
                    line,
                    pattern,
                    f"un-pinned action at {workflow.relative_to(ROOT)}:{line_number}",
                )

    def test_codeql_components_use_one_pinned_release(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "codeql.yml").read_text(
            encoding="utf-8"
        )
        refs = re.findall(
            r"uses:\s+github/codeql-action/(?:init|analyze)@([0-9a-f]{40})",
            workflow,
        )
        self.assertEqual(len(refs), 2)
        self.assertEqual(len(set(refs)), 1)

    def test_release_workflow_avoids_ref_injection_and_requires_main_ancestry(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )
        self.assertNotIn('--tag "${{ github.ref_name }}"', workflow)
        self.assertIn("RELEASE_TAG: ${{ github.ref_name }}", workflow)
        self.assertIn(
            'git merge-base --is-ancestor "$RELEASE_TAG^{commit}" origin/main',
            workflow,
        )

    def test_repository_release_metadata_is_consistent(self) -> None:
        metadata, errors = CHECK_RELEASE.validate_release(ROOT)
        self.assertEqual(errors, [])
        self.assertIsNotNone(metadata)
        assert metadata is not None
        self.assertEqual(metadata.version, VERSION)
        self.assertEqual(metadata.tag, TAG)

    def test_tag_must_exactly_match_version(self) -> None:
        _metadata, errors = CHECK_RELEASE.validate_release(ROOT, tag="v999.999.999")
        self.assertTrue(any("does not match expected tag" in error for error in errors))

    def test_version_citation_and_changelog_must_all_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "VERSION").write_text("1.2.3\n", encoding="utf-8", newline="\n")
            (root / "CITATION.cff").write_text(
                "cff-version: 1.2.0\n"
                "version: 1.2.4\n"
                "date-released: 2026-01-02\n"
                "license: 0BSD\n",
                encoding="utf-8",
                newline="\n",
            )
            (root / "CHANGELOG.md").write_text(
                "# Changelog\n\n## [Unreleased]\n\n## [1.2.3] - 2026-01-03\n",
                encoding="utf-8",
                newline="\n",
            )
            _metadata, errors = CHECK_RELEASE.validate_release(root)
            self.assertTrue(any("does not match VERSION" in error for error in errors))
            self.assertTrue(any("does not match CITATION.cff" in error for error in errors))

    def test_semver_rejects_numeric_prerelease_leading_zeroes(self) -> None:
        self.assertTrue(CHECK_RELEASE.is_semver("1.2.3-rc.1+build.5"))
        self.assertFalse(CHECK_RELEASE.is_semver("1.2.3-rc.01"))

    def test_release_archives_are_reproducible_and_self_describing(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_paths = BUILD_RELEASE.build_release(
                output_dir=Path(first), root=ROOT, tag=TAG
            )
            second_paths = BUILD_RELEASE.build_release(
                output_dir=Path(second), root=ROOT, tag=TAG
            )
            self.assertEqual(
                [path.name for path in first_paths], [path.name for path in second_paths]
            )
            for left, right in zip(first_paths, second_paths):
                self.assertEqual(left.read_bytes(), right.read_bytes(), left.name)

            checksum_path = Path(first) / "SHA256SUMS"
            checksum_lines = checksum_path.read_text(encoding="ascii").splitlines()
            self.assertEqual(len(checksum_lines), 3)
            for line in checksum_lines:
                digest, filename = line.split("  ", 1)
                self.assertEqual(
                    digest, hashlib.sha256((Path(first) / filename).read_bytes()).hexdigest()
                )

            prefix = f"llm-tool-atlas-data-v{VERSION}/"
            zip_path = Path(first) / f"llm-tool-atlas-data-v{VERSION}.zip"
            with zipfile.ZipFile(zip_path) as archive:
                names = archive.namelist()
                self.assertEqual(names, sorted(names))
                self.assertIn(prefix + "MANIFEST.json", names)
                tools = archive.read(prefix + "data/tools.json")
                self.assertNotIn(b"\r\n", tools)
                manifest = json.loads(archive.read(prefix + "MANIFEST.json"))
                self.assertEqual(manifest["version"], VERSION)

            tar_path = Path(first) / f"llm-tool-atlas-data-v{VERSION}.tar.gz"
            with tarfile.open(tar_path, mode="r:gz") as archive:
                names = archive.getnames()
                self.assertEqual(names, sorted(names))
                self.assertIn(prefix + "MANIFEST.json", names)

    def test_release_bytes_ignore_checkout_newline_style(self) -> None:
        with (
            tempfile.TemporaryDirectory() as mirror_directory,
            tempfile.TemporaryDirectory() as first_output,
            tempfile.TemporaryDirectory() as second_output,
        ):
            mirror = Path(mirror_directory)
            for filename in ("VERSION", "LICENSE", "CITATION.cff", "CHANGELOG.md"):
                shutil.copy2(ROOT / filename, mirror / filename)
            shutil.copytree(ROOT / "data", mirror / "data")
            shutil.copytree(ROOT / "schema", mirror / "schema")
            for path in mirror.rglob("*"):
                if path.is_file():
                    normalized = path.read_text(encoding="utf-8").replace("\r\n", "\n")
                    path.write_bytes(normalized.replace("\n", "\r\n").encode("utf-8"))

            original = BUILD_RELEASE.build_release(
                output_dir=Path(first_output), root=ROOT, tag=TAG
            )
            mirrored = BUILD_RELEASE.build_release(
                output_dir=Path(second_output), root=mirror, tag=TAG
            )
            self.assertEqual([path.name for path in original], [path.name for path in mirrored])
            for left, right in zip(original, mirrored):
                self.assertEqual(left.read_bytes(), right.read_bytes(), left.name)


if __name__ == "__main__":
    unittest.main()
