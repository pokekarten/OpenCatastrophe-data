# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import io
import json
import unittest
from unittest import mock

from scripts import profile_esrm20_project278_manual as subject


class _Page:
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class _Reader:
    is_encrypted = False

    def __init__(self, _stream: io.BytesIO, *, strict: bool) -> None:
        assert strict is True
        self.pages = [
            _Page("Coordinate reference system EPSG:4326; WGS 84. Longitude and latitude."),
            _Page("Exposure-to-site tool: Vs30, xvf, slope, geology, region. NoData values."),
        ]


class _EncryptedReader(_Reader):
    is_encrypted = True


class Project278ManualContentProfileTests(unittest.TestCase):
    SHA = "a" * 40

    def _request(self) -> str:
        return subject.REQUEST_MARKER + "\n" + json.dumps(
            {
                "schema_version": subject.REQUEST_SCHEMA_VERSION,
                "action": subject.ACTION,
                "issue": subject.CONTROL_ISSUE,
                "target_sha": self.SHA,
                "dataset_id": subject.DATASET_ID,
                "requester": "TEST",
            },
            separators=(",", ":"),
        )

    def test_request_is_exact_and_sha_bound(self) -> None:
        parsed = subject.validate_request(
            self._request(), expected_issue=subject.CONTROL_ISSUE, execution_sha=self.SHA
        )
        self.assertEqual(parsed["target_sha"], self.SHA)
        with self.assertRaises(subject.Project278ManualContentProfileError):
            subject.validate_request(
                self._request(), expected_issue=subject.CONTROL_ISSUE, execution_sha="b" * 40
            )

    def test_bounded_profile_returns_tokens_not_source_text(self) -> None:
        payload = b"%PDF synthetic profile"
        profile = subject._profile_pdf_bytes_for_test(
            payload,
            expected_byte_count=len(payload),
            expected_sha256=hashlib.sha256(payload).hexdigest(),
            reader_factory=_Reader,
            parser_version="test",
        )
        self.assertEqual(profile["page_count"], 2)
        self.assertEqual(profile["mention_pages"]["epsg_4326"], [1])
        self.assertEqual(profile["mention_pages"]["wgs84"], [1])
        self.assertEqual(profile["mention_pages"]["vs30"], [2])
        self.assertEqual(profile["mention_pages"]["xvf"], [2])
        self.assertEqual(profile["mention_pages"]["nodata"], [2])
        self.assertIs(profile["raw_text_exposed"], False)
        serialized = json.dumps(profile, sort_keys=True)
        self.assertNotIn("Coordinate reference system", serialized)
        self.assertNotIn("Exposure-to-site tool", serialized)

    def test_profile_rejects_identity_drift_before_parser(self) -> None:
        payload = b"%PDF synthetic profile"
        called = False

        def reader_factory(*_args, **_kwargs):
            nonlocal called
            called = True
            return _Reader(io.BytesIO(payload), strict=True)

        with self.assertRaises(subject.Project278ManualContentProfileError):
            subject._profile_pdf_bytes_for_test(
                payload,
                expected_byte_count=len(payload),
                expected_sha256="0" * 64,
                reader_factory=reader_factory,
                parser_version="test",
            )
        self.assertIs(called, False)

    def test_encrypted_pdf_fails_closed(self) -> None:
        payload = b"%PDF synthetic profile"
        with self.assertRaises(subject.Project278ManualContentProfileError):
            subject._profile_pdf_bytes_for_test(
                payload,
                expected_byte_count=len(payload),
                expected_sha256=hashlib.sha256(payload).hexdigest(),
                reader_factory=_EncryptedReader,
                parser_version="test",
            )

    def test_run_blocks_acquisition_without_parsing(self) -> None:
        with mock.patch.object(
            subject,
            "acquire_verified_pdf_bytes",
            side_effect=subject.Project278ManualContentProfileError("blocked"),
        ), mock.patch.object(subject, "profile_verified_pdf_bytes") as parser:
            result = subject.run_content_profile(execution_sha=self.SHA)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failure")
        self.assertIs(result["pdf_content_profiled"], False)
        parser.assert_not_called()

    def test_terminal_pass_requires_closed_mention_surface(self) -> None:
        payload = b"%PDF synthetic profile"
        profile = subject._profile_pdf_bytes_for_test(
            payload,
            expected_byte_count=len(payload),
            expected_sha256=hashlib.sha256(payload).hexdigest(),
            reader_factory=_Reader,
            parser_version="test",
        )
        result = subject._base_result(execution_sha=self.SHA)
        result.update(
            {
                "status": "pass",
                "failure_class": None,
                "pdf_content_profiled": True,
                "content_profile": profile,
            }
        )
        self.assertTrue(subject._validate_terminal_payload(result, execution_sha=self.SHA))
        result["content_profile"]["mention_pages"]["provider_secret"] = [1]
        with self.assertRaises(subject.Project278ManualContentProfileError):
            subject._validate_terminal_payload(result, execution_sha=self.SHA)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
