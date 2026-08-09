#!/usr/bin/env python3
"""Audit official-source URLs with retries and private-network safeguards."""

from __future__ import annotations

import argparse
from http.client import HTTPException, HTTPSConnection
import ipaddress
import json
import math
import socket
import ssl
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit

from validate_catalog import load_json
from url_safety import static_https_url_error


ROOT = Path(__file__).resolve().parents[1]
CATALOGS = ("tools", "gateways", "models")
RESTRICTED_STATUSES = frozenset({401, 403, 405, 429})
TRANSIENT_STATUSES = frozenset({408, 425})
MAX_WORKERS = 64
MAX_RETRIES = 5
MAX_REDIRECTS = 8
USER_AGENT = (
    "llm-tool-atlas-link-audit/0.1 "
    "(+https://github.com/Yunushan/llm-tool-atlas)"
)


@dataclass(frozen=True)
class CheckResult:
    """A normalized reachability result."""

    url: str
    status: int | None
    outcome: str
    message: str
    attempts: int


def positive_float(value: str) -> float:
    """Parse a positive command-line float."""

    parsed = float(value)
    if not math.isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("must be finite and greater than zero")
    return parsed


def bounded_int(minimum: int, maximum: int) -> Callable[[str], int]:
    """Return an argparse parser for an inclusive integer range."""

    def parse(value: str) -> int:
        parsed = int(value)
        if not minimum <= parsed <= maximum:
            raise argparse.ArgumentTypeError(
                f"must be between {minimum} and {maximum}"
            )
        return parsed

    return parse


def urls() -> list[str]:
    """Return the sorted, de-duplicated official-source URLs."""

    found: set[str] = set()
    for name in CATALOGS:
        path = ROOT / "data" / f"{name}.json"
        records = load_json(path)
        for record in records:
            found.update(source["url"] for source in record["official_sources"])
    return sorted(found)


def static_target_error(url: str) -> str | None:
    """Return why a URL is unsafe before any DNS or network access."""

    return static_https_url_error(url)


def public_addresses(url: str) -> tuple[str, ...]:
    """Resolve a URL once and return only globally routable addresses."""

    problem = static_target_error(url)
    if problem:
        raise URLError(problem)

    parsed = urlsplit(url)
    assert parsed.hostname is not None
    hostname = parsed.hostname.rstrip(".")
    try:
        literal = ipaddress.ip_address(hostname)
    except ValueError:
        try:
            resolved = socket.getaddrinfo(
                hostname,
                443,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP,
            )
        except socket.gaierror as exc:
            raise URLError(f"DNS resolution failed: {exc}") from exc
        addresses = {
            ipaddress.ip_address(str(result[4][0]).split("%", 1)[0])
            for result in resolved
        }
    else:
        addresses = {literal}

    if not addresses:
        raise URLError("DNS resolution returned no addresses")
    unsafe = sorted(
        str(address)
        for address in addresses
        if (
            not address.is_global
            or address.is_private
            or address.is_reserved
            or address.is_loopback
            or address.is_link_local
            or address.is_multicast
            or address.is_unspecified
        )
    )
    if unsafe:
        raise URLError("hostname resolves to non-public address(es): " + ", ".join(unsafe))
    return tuple(sorted(str(address) for address in addresses))


def validate_network_target(url: str) -> None:
    """Reject non-public URL targets before opening a connection."""

    public_addresses(url)


class PinnedHTTPSConnection(HTTPSConnection):
    """Connect to the address validated for this request, preserving TLS SNI."""

    def __init__(
        self,
        hostname: str,
        address: str,
        timeout: float,
        context: ssl.SSLContext,
    ) -> None:
        super().__init__(hostname, 443, timeout=timeout, context=context)
        self._pinned_address = address
        self._pinned_context = context

    def connect(self) -> None:
        raw_socket = socket.create_connection(
            (self._pinned_address, self.port),
            self.timeout,
            None,
        )
        try:
            self.sock = self._pinned_context.wrap_socket(
                raw_socket,
                server_hostname=self.host,
            )
        except BaseException:
            raw_socket.close()
            raise


def request_once(url: str, timeout: float, context: ssl.SSLContext) -> int:
    """Perform a bounded GET, pinning each validated redirect target to its IP."""

    current = url
    for redirect_number in range(MAX_REDIRECTS + 1):
        parsed = urlsplit(current)
        if parsed.hostname is None:
            raise URLError("redirect target has no hostname")
        addresses = public_addresses(current)
        target = parsed.path or "/"
        if parsed.query:
            target += "?" + parsed.query
        last_error: BaseException | None = None
        for address in addresses:
            connection = PinnedHTTPSConnection(
                parsed.hostname,
                address,
                timeout,
                context,
            )
            try:
                connection.request(
                    "GET",
                    target,
                    headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*"},
                )
                response = connection.getresponse()
                status = int(response.status)
                location = response.getheader("Location")
                response.read(4096)
                connection.close()
            except (HTTPException, OSError, ssl.SSLError, TimeoutError) as exc:
                last_error = exc
                connection.close()
                continue

            if 300 <= status < 400 and location:
                if redirect_number >= MAX_REDIRECTS:
                    raise URLError("too many HTTPS redirects")
                current = urljoin(current, location)
                break
            return status
        else:
            reason = str(last_error) if last_error is not None else "connection failed"
            raise URLError(reason)
        if not (300 <= status < 400 and location):
            return status

    raise URLError("too many HTTPS redirects")


def classify_status(status: int) -> tuple[str, str]:
    """Map an HTTP status to a stable outcome and message."""

    if 200 <= status < 400:
        return "ok", "reachable"
    if status in RESTRICTED_STATUSES:
        return "restricted", "reachable but access-restricted"
    if status in TRANSIENT_STATUSES or status >= 500:
        return "retry", "transient HTTP response"
    return "failed", "terminal HTTP response"


def check(
    url: str,
    timeout: float,
    context: ssl.SSLContext,
    retries: int = 1,
) -> CheckResult:
    """Check one URL, retrying only transient network and HTTP failures."""

    attempts = retries + 1
    last_status: int | None = None
    last_message = "unknown failure"

    for attempt in range(1, attempts + 1):
        try:
            status = request_once(url, timeout, context)
        except HTTPError as exc:
            try:
                status = exc.code
                outcome, message = classify_status(status)
                last_status = status
                last_message = str(exc.reason or message)
            finally:
                if exc.fp is not None:
                    exc.close()
        except (HTTPException, URLError, TimeoutError, OSError) as exc:
            outcome = "retry"
            reason = getattr(exc, "reason", exc)
            last_message = str(reason)
        else:
            outcome, message = classify_status(status)
            last_status = status
            last_message = message

        if outcome == "ok":
            return CheckResult(url, last_status, "ok", last_message, attempt)
        if outcome == "restricted":
            return CheckResult(url, last_status, "restricted", last_message, attempt)
        if outcome == "failed":
            return CheckResult(url, last_status, "failed", last_message, attempt)
        if attempt < attempts:
            time.sleep(min(0.25 * (2 ** (attempt - 1)), 1.0))

    return CheckResult(url, last_status, "failed", last_message, attempts)


def write_json_report(
    path: Path,
    source_urls: Sequence[str],
    results: dict[str, CheckResult],
) -> None:
    """Write a machine-readable audit report for CI retention."""

    counts = {"ok": 0, "restricted": 0, "failed": 0}
    ordered_results = []
    for url in source_urls:
        result = results[url]
        counts[result.outcome] += 1
        ordered_results.append(asdict(result))
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "summary": {"checked": len(source_urls), **counts},
        "results": ordered_results,
    }
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=positive_float, default=12.0)
    parser.add_argument("--workers", type=bounded_int(1, MAX_WORKERS), default=12)
    parser.add_argument("--retries", type=bounded_int(0, MAX_RETRIES), default=1)
    parser.add_argument(
        "--cafile",
        help="PEM CA bundle for an intercepting proxy or private trust store",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="also write a machine-readable JSON result report",
    )
    args = parser.parse_args(argv)

    try:
        context = ssl.create_default_context(cafile=args.cafile)
    except (OSError, ssl.SSLError) as exc:
        parser.error(f"cannot load CA bundle: {exc}")

    source_urls = urls()
    results: dict[str, CheckResult] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                check,
                url,
                args.timeout,
                context,
                args.retries,
            ): url
            for url in source_urls
        }
        for future in as_completed(futures):
            url = futures[future]
            try:
                results[url] = future.result()
            except Exception as exc:  # Defensive isolation between worker results.
                results[url] = CheckResult(url, None, "failed", str(exc), 1)

    counts = {"ok": 0, "restricted": 0, "failed": 0}
    markers = {"ok": "OK", "restricted": "WARN", "failed": "FAIL"}
    for url in source_urls:
        result = results[url]
        counts[result.outcome] += 1
        status = str(result.status) if result.status is not None else "-"
        print(
            f"{markers[result.outcome]:4} {status:>3} {url} "
            f"({result.message}; attempts={result.attempts})"
        )

    print(
        f"checked {len(source_urls)} URLs; ok={counts['ok']}; "
        f"restricted={counts['restricted']}; failures={counts['failed']}"
    )
    if args.json_output is not None:
        try:
            write_json_report(args.json_output, source_urls, results)
        except OSError as exc:
            print(f"error: cannot write JSON report: {exc}", file=sys.stderr)
            return 2
    if counts["failed"]:
        print(
            "hint: TLS interception requires a trusted PEM bundle via --cafile; "
            "certificate verification is never disabled",
            file=sys.stderr,
        )
    return 1 if counts["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
