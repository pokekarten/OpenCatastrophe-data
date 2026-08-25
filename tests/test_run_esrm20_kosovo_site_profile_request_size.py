# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import run_esrm20_kosovo_site_profile_action as subject


SHA = "a" * 40


def _request_body(*, requester: str, ensure_ascii: bool = True) -> str:
    payload = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": subject.CONTROL_ISSUE,
        "target_sha": SHA,
        "dataset_id": subject.DATASET_ID,
        "requester": requester,
    }
    return subject.REQUEST_MARKER + "\n" + json.dumps(
        payload,
        separators=(",", ":"),
        ensure_ascii=ensure_ascii,
    )


class KosovoSiteProfileRequestSizeTests(unittest.TestCase):
    def test_canonical_request_still_passes(self):
        result = subject.validate_request(
            _request_body(requester="unit-test"),
            expected_issue=subject.CONTROL_ISSUE,
            execution_sha=SHA,
        )
        self.assertEqual(result["requester"], "unit-test")

    def test_oversized_ascii_request_is_rejected_before_json_decode(self):
        body = _request_body(requester="a" * subject.MAX_REQUEST_UTF8_BYTES)
        self.assertGreater(len(body.encode("utf-8")), subject.MAX_REQUEST_UTF8_BYTES)
        with mock.patch.object(
            subject.json,
            "loads",
            side_effect=AssertionError("oversized request reached json.loads"),
        ):
            with self.assertRaisesRegex(subject.SiteProfileActionError, "request exceeds limit"):
                subject.validate_request(
                    body,
                    expected_issue=subject.CONTROL_ISSUE,
                    execution_sha=SHA,
                )

    def test_oversized_multibyte_request_uses_utf8_byte_count(self):
        body = _request_body(requester="é" * 2_000, ensure_ascii=False)
        self.assertLess(len(body), subject.MAX_REQUEST_UTF8_BYTES)
        self.assertGreater(len(body.encode("utf-8")), subject.MAX_REQUEST_UTF8_BYTES)
        with mock.patch.object(
            subject.json,
            "loads",
            side_effect=AssertionError("oversized request reached json.loads"),
        ):
            with self.assertRaisesRegex(subject.SiteProfileActionError, "request exceeds limit"):
                subject.validate_request(
                    body,
                    expected_issue=subject.CONTROL_ISSUE,
                    execution_sha=SHA,
                )

    def test_non_utf8_encodable_request_is_rejected_before_json_decode(self):
        body = subject.REQUEST_MARKER + "\n" + chr(0xD800)
        with mock.patch.object(
            subject.json,
            "loads",
            side_effect=AssertionError("non-UTF8 request reached json.loads"),
        ):
            with self.assertRaisesRegex(subject.SiteProfileActionError, "not UTF-8 encodable"):
                subject.validate_request(
                    body,
                    expected_issue=subject.CONTROL_ISSUE,
                    execution_sha=SHA,
                )


if __name__ == "__main__":
    unittest.main()
