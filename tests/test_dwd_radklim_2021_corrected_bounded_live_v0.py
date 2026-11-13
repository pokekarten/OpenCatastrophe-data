# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No-network synthetic request/response tests for the reviewed 2KiB DWD GET."""
from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from research_runners import dwd_radklim_2021_corrected_bounded_live_v0 as m


FAKE_BYTES = b"\x1f\x8b\x08" + b"synthetic-not-a-real-archive" * 81
# The fake body never matches original DWD SHA, and no original DWD data is
# placed in this test file, logs, or repository artifacts.


class FakeReply:
    def __init__(self, body=FAKE_BYTES, *, status=206, headers=None):
        self.status = status
        self.headers = {
            "Content-Range": m.EXPECTED_CONTENT_RANGE,
            "Content-Length": str(m.FROZEN_PREFIX_LENGTH),
            "Content-Type": "application/x-gzip",
            "Content-Encoding": "identity",
        }
        if headers:
            self.headers.update(headers)
        self.body = body
        self.read_calls = []

    def read(self, length):
        self.read_calls.append(length)
        return self.body[:length]

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class FakeClient:
    def __init__(self, reply):
        self.reply = reply
        self.requests = []

    def open(self, request, *, timeout):
        self.requests.append((request, timeout))
        return self.reply


class DWDOriginalHTTPRangeTests(unittest.TestCase):
    def test_explicit_opt_in_and_no_implicit_network(self):
        self.assertEqual(m.main([]), 2)

    def test_fixed_only_request_and_receipt_without_original_values(self):
        reply = FakeReply(body=b"X" * m.FROZEN_PREFIX_LENGTH)
        client = FakeClient(reply)
        fake_validation = {
            "source_id": "dwd.radklim.rw.v2017.002",
            "original_prefix_sha256": "0" * 64,
        }
        with patch.object(m, "inspect_frozen_original_prefix", return_value=fake_validation):
            result = m.one_fixed_range_probe(opener=client)
        self.assertEqual(len(client.requests), 1)
        request, timeout = client.requests[0]
        self.assertEqual(request.full_url, m.CORRECTED_URL)
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(request.get_header("Range"), m.RANGE_VALUE)
        self.assertEqual(request.get_header("Accept-encoding"), "identity")
        self.assertEqual(timeout, 25)
        self.assertEqual(reply.read_calls, [2049])
        self.assertEqual(result["http_status"], 206)
        self.assertEqual(result["original_response_bytes"], 2048)
        self.assertFalse(result["model_input_approved"])
        self.assertFalse(result["provider_bytes_persisted"])
        self.assertFalse(result["full_original_archive_downloaded"])
        self.assertFalse(result["original_month_precipitation_values_verified"])
        self.assertNotIn("synthetic-not-a-real-archive", json.dumps(result))
        self.assertNotIn("X" * 10, json.dumps(result))

    def test_reject_non_206_before_any_response_bytes_are_read(self):
        for code in (200, 204, 301, 404, 429, 503):
            with self.subTest(status=code):
                reply = FakeReply(status=code)
                client = FakeClient(reply)
                with self.assertRaisesRegex(m.ProviderProbeBlocked, "HTTP 206"):
                    m.one_fixed_range_probe(opener=client)
                self.assertEqual(reply.read_calls, [])
                self.assertEqual(len(client.requests), 1)

    def test_reject_content_range_type_encoding_length_and_size(self):
        invalid = [
            FakeReply(headers={"Content-Range": "bytes 0-2047/820110127"}),
            FakeReply(headers={"Content-Range": "bytes 1-2048/820143312"}),
            FakeReply(headers={"Content-Type": "text/html"}),
            FakeReply(headers={"Content-Encoding": "gzip"}),
            FakeReply(headers={"Content-Length": "820143312"}),
            FakeReply(headers={"Content-Length": "nonsense"}),
            FakeReply(body=b"x" * (m.FROZEN_PREFIX_LENGTH + 1)),
            FakeReply(body=b"x" * (m.FROZEN_PREFIX_LENGTH - 1)),
        ]
        for idx, reply in enumerate(invalid):
            with self.subTest(case=idx), self.assertRaises(m.ProviderProbeBlocked):
                m.one_fixed_range_probe(opener=FakeClient(reply))

    def test_fake_compressed_response_fails_original_digest(self):
        reply = FakeReply(body=b"x" * m.FROZEN_PREFIX_LENGTH)
        with self.assertRaisesRegex(m.ProviderProbeBlocked, "identity/shape"):
            m.one_fixed_range_probe(opener=FakeClient(reply))

    def test_redirect_always_blocked(self):
        with self.assertRaisesRegex(m.ProviderProbeBlocked, "redirect"):
            m.RefuseRedirect().redirect_request(
                None, None, 302, "", {}, "https://another.example/large-archive"
            )


if __name__ == "__main__":
    unittest.main()
