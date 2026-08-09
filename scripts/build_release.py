#!/usr/bin/env python3
"""Build deterministic, versioned catalog archives and SHA256SUMS."""

from __future__ import annotations

import argparse
import binascii
import hashlib
import io
import json
import stat
import tarfile
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Sequence

from check_release import ReleaseMetadata, require_release


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "dist"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
FIXED_MODE = stat.S_IFREG | 0o644


def _normalized_text_bytes(path: Path) -> bytes:
    """Return UTF-8 text with platform-independent LF newlines."""

    text = path.read_text(encoding="utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def _source_files(root: Path) -> list[Path]:
    paths = [
        root / "VERSION",
        root / "LICENSE",
        root / "CITATION.cff",
        root / "data" / "README.md",
    ]
    paths.extend(sorted((root / "data").glob("*.json")))
    paths.extend(sorted((root / "schema").glob("*.json")))
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"release input must be a regular file: {path.relative_to(root)}")
    return paths


def _manifest(
    metadata: ReleaseMetadata, source_entries: dict[str, bytes]
) -> bytes:
    value = {
        "artifact": "llm-tool-atlas-data",
        "release_date": metadata.release_date,
        "version": metadata.version,
        "files": [
            {
                "path": name,
                "sha256": hashlib.sha256(content).hexdigest(),
                "size": len(content),
            }
            for name, content in sorted(source_entries.items())
        ],
    }
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def _zip_bytes(entries: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, mode="w", compression=zipfile.ZIP_STORED) as archive:
        for name, content in sorted(entries.items()):
            info = zipfile.ZipInfo(filename=name, date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = FIXED_MODE << 16
            info.flag_bits |= 0x800
            archive.writestr(info, content)
    return output.getvalue()


def _tar_gz_bytes(entries: dict[str, bytes]) -> bytes:
    tar_output = io.BytesIO()
    with tarfile.open(fileobj=tar_output, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for name, content in sorted(entries.items()):
            info = tarfile.TarInfo(name=name)
            info.size = len(content)
            info.mode = 0o644
            info.mtime = 0
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            archive.addfile(info, io.BytesIO(content))
    return _stored_gzip(tar_output.getvalue())


def _stored_gzip(content: bytes) -> bytes:
    """Encode a deterministic gzip stream without zlib-version variance."""

    output = bytearray(b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff")
    if not content:
        blocks = [b""]
    else:
        blocks = [content[offset : offset + 65535] for offset in range(0, len(content), 65535)]
    for index, block in enumerate(blocks):
        output.append(1 if index == len(blocks) - 1 else 0)
        length = len(block)
        output.extend(length.to_bytes(2, "little"))
        output.extend((length ^ 0xFFFF).to_bytes(2, "little"))
        output.extend(block)
    output.extend(binascii.crc32(content).to_bytes(4, "little"))
    output.extend((len(content) & 0xFFFFFFFF).to_bytes(4, "little"))
    return bytes(output)


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=f".{path.name}.", dir=path.parent, delete=False
        ) as handle:
            handle.write(content)
            handle.flush()
            temporary = Path(handle.name)
        temporary.replace(path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def build_release(
    output_dir: Path = DEFAULT_OUTPUT,
    root: Path = ROOT,
    tag: str | None = None,
) -> list[Path]:
    """Build release files and return them in checksum-file order."""

    metadata = require_release(root=root, tag=tag)
    source_entries = {
        PurePosixPath(path.relative_to(root)).as_posix(): _normalized_text_bytes(path)
        for path in _source_files(root)
    }
    manifest = _manifest(metadata, source_entries)
    prefix = f"llm-tool-atlas-data-v{metadata.version}"
    archive_entries = {
        f"{prefix}/{name}": content for name, content in source_entries.items()
    }
    archive_entries[f"{prefix}/MANIFEST.json"] = manifest

    artifacts = {
        f"{prefix}.manifest.json": manifest,
        f"{prefix}.tar.gz": _tar_gz_bytes(archive_entries),
        f"{prefix}.zip": _zip_bytes(archive_entries),
    }
    output_dir = output_dir.resolve()
    written: list[Path] = []
    for filename, content in sorted(artifacts.items()):
        path = output_dir / filename
        _atomic_write(path, content)
        written.append(path)

    checksums = "".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
        for path in written
    ).encode("ascii")
    checksum_path = output_dir / "SHA256SUMS"
    _atomic_write(checksum_path, checksums)
    written.append(checksum_path)
    return written


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="artifact directory (default: dist)",
    )
    parser.add_argument(
        "--tag",
        help="require this Git tag to equal v<VERSION> before building",
    )
    args = parser.parse_args(argv)

    try:
        artifacts = build_release(output_dir=args.output_dir, tag=args.tag)
    except (OSError, UnicodeError, ValueError) as exc:
        parser.error(str(exc))
    for artifact in artifacts:
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        print(f"{digest}  {artifact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
