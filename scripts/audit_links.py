#!/usr/bin/env python3
"""Best-effort audit of official-source URLs in the catalogs."""

from __future__ import annotations

import argparse
import json
import ssl
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
CATALOGS = ("tools", "gateways", "models")


def urls() -> list[str]:
    found: set[str] = set()
    for name in CATALOGS:
        path = ROOT / "data" / f"{name}.json"
        records = json.loads(path.read_text(encoding="utf-8"))
        for record in records:
            found.update(source["url"] for source in record["official_sources"])
    return sorted(found)


def check(url: str, timeout: float) -> tuple[str, int | None, str]:
    request = Request(
        url,
        method="GET",
        headers={
            "User-Agent": "llm-tool-atlas-link-audit/0.1 (+https://github.com/Yunushan/llm-tool-atlas)",
            "Range": "bytes=0-1023",
        },
    )
    try:
        with urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
            return url, response.status, "ok"
    except HTTPError as exc:
        # Auth and bot-protection responses still establish that the host/path exists.
        if exc.code in {401, 403, 405, 429}:
            return url, exc.code, "reachable but restricted"
        return url, exc.code, str(exc.reason)
    except (URLError, TimeoutError, OSError) as exc:
        return url, None, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=12.0)
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()

    failures = 0
    source_urls = urls()
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(check, url, args.timeout): url for url in source_urls}
        for future in as_completed(futures):
            url, status, message = future.result()
            marker = "OK" if status is not None and status < 500 else "FAIL"
            print(f"{marker:4} {status or '-':>3} {url} ({message})")
            if marker == "FAIL":
                failures += 1

    print(f"checked {len(source_urls)} URLs; failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
