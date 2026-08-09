from __future__ import annotations

import importlib.util
import io
import socket
import ssl
import sys
import tempfile
import unittest
import json
from http.client import HTTPMessage, IncompleteRead
from pathlib import Path
from typing import Any
from unittest.mock import patch
from urllib.error import HTTPError, URLError


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
SPEC = importlib.util.spec_from_file_location(
    "audit_links", ROOT / "scripts" / "audit_links.py"
)
assert SPEC and SPEC.loader
AUDITOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDITOR
SPEC.loader.exec_module(AUDITOR)


class StatusClassificationTests(unittest.TestCase):
    def test_success_and_redirect_statuses_pass(self) -> None:
        for status in (200, 204, 301, 308):
            with self.subTest(status=status):
                self.assertEqual(AUDITOR.classify_status(status)[0], "ok")

    def test_access_restrictions_are_reachable_but_unverified(self) -> None:
        for status in (401, 403, 405, 429):
            with self.subTest(status=status):
                self.assertEqual(AUDITOR.classify_status(status)[0], "restricted")

    def test_terminal_client_errors_fail(self) -> None:
        for status in (400, 404, 410, 451):
            with self.subTest(status=status):
                self.assertEqual(AUDITOR.classify_status(status)[0], "failed")

    def test_transient_errors_retry(self) -> None:
        for status in (408, 425, 500, 503):
            with self.subTest(status=status):
                self.assertEqual(AUDITOR.classify_status(status)[0], "retry")


class TargetSafetyTests(unittest.TestCase):
    def test_static_validation_accepts_public_https_hostname(self) -> None:
        self.assertIsNone(AUDITOR.static_target_error("https://docs.example.com/path"))

    def test_static_validation_rejects_unsafe_targets(self) -> None:
        unsafe = (
            "http://example.com",
            "file:///etc/passwd",
            "https://user:secret@example.com",
            "https://example.com:8443/path",
            "https://localhost/path",
            "https://service.internal/path",
            "https://127.0.0.1/path",
            "https://169.254.169.254/latest/meta-data",
            "https://[::1]/path",
            "https://example.com\\@127.0.0.1/path",
            "https://example.com\r\nX-Test: injected",
        )
        for url in unsafe:
            with self.subTest(url=url):
                self.assertIsNotNone(AUDITOR.static_target_error(url))

    @patch.object(AUDITOR.socket, "getaddrinfo")
    def test_dns_validation_accepts_only_public_addresses(self, resolve: Any) -> None:
        resolve.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ]
        AUDITOR.validate_network_target("https://example.com/path")

    @patch.object(AUDITOR.socket, "getaddrinfo")
    def test_dns_validation_rejects_any_private_answer(self, resolve: Any) -> None:
        resolve.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.8", 443)),
        ]
        with self.assertRaises(URLError):
            AUDITOR.validate_network_target("https://example.com/path")


class RetryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = ssl.create_default_context()
        self.url = "https://example.com/path"

    @patch.object(AUDITOR.time, "sleep", return_value=None)
    @patch.object(AUDITOR, "request_once", return_value=200)
    def test_success_returns_normalized_result(self, request_once: Any, _sleep: Any) -> None:
        result = AUDITOR.check(self.url, 1.0, self.context, retries=2)
        self.assertEqual(result.outcome, "ok")
        self.assertEqual(result.status, 200)
        self.assertEqual(result.attempts, 1)
        request_once.assert_called_once()

    @patch.object(AUDITOR.time, "sleep", return_value=None)
    @patch.object(AUDITOR, "request_once")
    def test_404_fails_without_retry(self, request_once: Any, _sleep: Any) -> None:
        request_once.side_effect = HTTPError(
            self.url, 404, "Not Found", hdrs=HTTPMessage(), fp=io.BytesIO()
        )
        result = AUDITOR.check(self.url, 1.0, self.context, retries=2)
        self.assertEqual(result.outcome, "failed")
        self.assertEqual(result.status, 404)
        self.assertEqual(result.attempts, 1)
        request_once.assert_called_once()

    @patch.object(AUDITOR.time, "sleep", return_value=None)
    @patch.object(AUDITOR, "request_once", side_effect=[503, 200])
    def test_transient_http_status_is_retried(self, request_once: Any, sleep: Any) -> None:
        result = AUDITOR.check(self.url, 1.0, self.context, retries=2)
        self.assertEqual(result.outcome, "ok")
        self.assertEqual(result.attempts, 2)
        self.assertEqual(request_once.call_count, 2)
        sleep.assert_called_once()

    @patch.object(AUDITOR.time, "sleep", return_value=None)
    @patch.object(AUDITOR, "request_once", side_effect=URLError("temporary DNS error"))
    def test_network_failure_exhausts_retry_budget(self, request_once: Any, sleep: Any) -> None:
        result = AUDITOR.check(self.url, 1.0, self.context, retries=2)
        self.assertEqual(result.outcome, "failed")
        self.assertIsNone(result.status)
        self.assertEqual(result.attempts, 3)
        self.assertEqual(request_once.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    @patch.object(AUDITOR.time, "sleep", return_value=None)
    @patch.object(AUDITOR, "request_once", side_effect=[IncompleteRead(b"partial"), 200])
    def test_incomplete_http_response_uses_retry_budget(self, request_once: Any, sleep: Any) -> None:
        result = AUDITOR.check(self.url, 1.0, self.context, retries=1)
        self.assertEqual(result.outcome, "ok")
        self.assertEqual(result.status, 200)
        self.assertEqual(result.attempts, 2)
        self.assertEqual(request_once.call_count, 2)
        sleep.assert_called_once()


class ArgumentValidationTests(unittest.TestCase):
    def test_positive_float(self) -> None:
        self.assertEqual(AUDITOR.positive_float("0.5"), 0.5)
        for value in ("0", "nan", "inf", "-inf"):
            with self.subTest(value=value), self.assertRaises(Exception):
                AUDITOR.positive_float(value)

    def test_bounded_integer(self) -> None:
        parser = AUDITOR.bounded_int(1, 4)
        self.assertEqual(parser("4"), 4)
        with self.assertRaises(Exception):
            parser("0")


class ReportTests(unittest.TestCase):
    def test_json_report_is_ordered_and_summarized(self) -> None:
        source_urls = ["https://a.example/", "https://b.example/"]
        results = {
            source_urls[0]: AUDITOR.CheckResult(
                source_urls[0], 200, "ok", "reachable", 1
            ),
            source_urls[1]: AUDITOR.CheckResult(
                source_urls[1], 403, "restricted", "access-restricted", 1
            ),
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            AUDITOR.write_json_report(path, source_urls, results)
            report = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(
            report["summary"],
            {"checked": 2, "failed": 0, "ok": 1, "restricted": 1},
        )
        self.assertEqual(
            [result["url"] for result in report["results"]], source_urls
        )
        self.assertTrue(report["generated_at"].endswith("Z"))


if __name__ == "__main__":
    unittest.main()
