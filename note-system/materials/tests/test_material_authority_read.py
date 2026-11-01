"""Synthetic transport failures must preserve authority uncertainty and privacy."""

import io
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from material_authority_read import AuthorityReadDenied, AuthorityReadUnavailable, read_authority_json


class AuthorityReadTests(unittest.TestCase):
    def test_success_returns_evidence_once_with_bounded_timeout(self):
        opener = Mock(return_value=io.BytesIO(b'{"ok": true, "grant": "read_only"}'))
        self.assertEqual(read_authority_json("fixture", opener=opener), {"ok": True, "grant": "read_only"})
        opener.assert_called_once_with("fixture", timeout=60)

    def test_transport_failure_is_not_permission_denial_or_legacy_false(self):
        failures = [(TimeoutError("private"), "timeout"),
                    (urllib.error.URLError(TimeoutError("private")), "timeout"),
                    (urllib.error.URLError("private"), "connection"),
                    (ConnectionResetError("private"), "connection")]
        for error, reason in failures:
            with self.subTest(error=type(error).__name__):
                opener = Mock(side_effect=error)
                with self.assertRaises(AuthorityReadUnavailable) as caught:
                    read_authority_json("private-url", opener=opener)
                self.assertEqual(caught.exception.reason, reason)
                self.assertNotIsInstance(caught.exception, (OSError, ValueError, AuthorityReadDenied))
                self.assertNotIn("private", str(caught.exception))
                self.assertIsNone(caught.exception.__cause__)
                self.assertTrue(caught.exception.__suppress_context__)
                opener.assert_called_once()

    def test_explicit_denial_never_retries_or_leaks_response(self):
        for status in (401, 403):
            with self.subTest(status=status):
                opener = Mock(side_effect=urllib.error.HTTPError("private-url", status, "private", {}, io.BytesIO(b"private")))
                with self.assertRaises(AuthorityReadDenied) as caught:
                    read_authority_json("private-url", opener=opener)
                self.assertEqual(caught.exception.status, status)
                self.assertNotIn("private", str(caught.exception))
                opener.assert_called_once()

    def test_service_error_is_unavailable_without_retry(self):
        opener = Mock(side_effect=urllib.error.HTTPError("private-url", 503, "private", {}, None))
        with self.assertRaises(AuthorityReadUnavailable) as caught:
            read_authority_json("private-url", opener=opener)
        self.assertEqual(caught.exception.reason, "http_503")
        opener.assert_called_once()

    def test_malformed_and_unsuccessful_evidence_cannot_authorize(self):
        for body in (b"private-invalid-json", b'"private"', b'{"ok": false, "error": "private"}', b'{"ok": 1}', b'{}', b'\xff'):
            with self.subTest(body=body):
                opener = Mock(return_value=io.BytesIO(body))
                with self.assertRaises(AuthorityReadUnavailable) as caught:
                    read_authority_json("private-url", opener=opener)
                self.assertNotIn("private", str(caught.exception))
                opener.assert_called_once()


if __name__ == "__main__":
    unittest.main()
