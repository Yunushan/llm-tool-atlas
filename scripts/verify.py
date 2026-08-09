#!/usr/bin/env python3
"""Run the complete, cross-platform repository verification suite."""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def commands(max_age_days: int | None = None, tag: str | None = None) -> list[list[str]]:
    python = sys.executable
    validate = [python, "scripts/validate_catalog.py"]
    if max_age_days is not None:
        validate.extend(["--max-age-days", str(max_age_days)])
    release = [python, "scripts/check_release.py"]
    if tag is not None:
        release.extend(["--tag", tag])
    return [
        validate,
        [python, "scripts/render_catalog.py", "--check"],
        [python, "scripts/check_local_links.py"],
        release,
        [python, "-m", "unittest", "discover", "-s", "tests", "-v"],
    ]


def run_all(max_age_days: int | None = None, tag: str | None = None) -> int:
    if sys.version_info < (3, 10):
        print("error: Python 3.10 or newer is required", file=sys.stderr)
        return 2
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONUTF8"] = "1"
    for command in commands(max_age_days=max_age_days, tag=tag):
        print(f"+ {shlex.join(command)}", flush=True)
        completed = subprocess.run(command, cwd=ROOT, env=environment, check=False)
        if completed.returncode:
            print(
                f"verification stopped: command exited {completed.returncode}",
                file=sys.stderr,
            )
            return completed.returncode
    print("repository verification passed")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-age-days",
        type=positive_int,
        help="also fail catalog records older than this threshold",
    )
    parser.add_argument(
        "--tag",
        help="also require this release tag to equal v<VERSION>",
    )
    args = parser.parse_args(argv)
    return run_all(max_age_days=args.max_age_days, tag=args.tag)


if __name__ == "__main__":
    raise SystemExit(main())
