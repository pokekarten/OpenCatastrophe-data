# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No-network HTTP 202 retry tests: only exact official HTTP 200 can be evidence."""
from __future__ import annotations

import hashlib
import io
import unittest
from unittest.mock import patch

from research_runners import ted_berlin_insurance_original_xml_preflight_v0 as m


def fake_xml(notice="668506-2026") -> bytes:
    root = "ContractAwardNotice" if notice == "668506-2026" else "ContractNotice"
    subject = ("WBM Industrielle Sachversicherung für neun reine Gewerbeobjekte"
               if notice == "668506-2026" else "Gewobag Gebäudeversicherung")
    return (f'<?xml version="1.0" encoding="UTF-8"?>'
            f'<{root}><ID>{notice}</ID><Description>{subject}</Description>'
            f'</{root}>').encode("utf-8")


class Response:
    def __init__(self, status, url, data=b"", *, headers=None):
        self.status = status
        self.url = url
        self.stream = io.BytesIO(data)
        self.headers = headers or {}
    def geturl(self):
        return self.url
    def read(self, count):
        return self.stream.read(count)
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False


class Source:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
    def __call__(self, request, timeout):
        self.calls.append((request.full_url, timeout))
        return self.responses.pop(0)


class TEDHTTP202BoundedRetryTests(unittest.TestCase):
    def url(self, notice="668506-2026"):
        return m.official_url(notice)

    def test_202_then_200_checked_against_exact_synthetic_sha_pin(self):
        notice = "668506-2026"
        data = fake_xml(notice)
        source = Source([
            Response(202, self.url(), b"Pending"),
            Response(200, self.url(), data),
        ])
        sleeps = []
        received = m.fetch(notice, opener=source, sleep_fn=sleeps.append)
        self.assertEqual(received, data)
        self.assertEqual(len(source.calls), 2)
        self.assertEqual(sleeps, [1])
        fixture = dict(m.SOURCES[notice],
                       original_xml_sha256_pinned=hashlib.sha256(data).hexdigest(),
                       original_xml_bytes_pinned=len(data))
        with patch.dict(m.SOURCES, {notice: fixture}):
            receipt = m.inspect(notice, received)
            self.assertTrue(receipt["original_sha256_immutable_pin_verified"])
            self.assertEqual(receipt["original_source_sha256"],
                             hashlib.sha256(data).hexdigest())

    def test_three_202_followed_by_200_never_uses_pending_bytes(self):
        source = Source([Response(202, self.url(), fake_xml()),
                         Response(202, self.url(), b"processing"),
                         Response(202, self.url(), b""),
                         Response(200, self.url(), fake_xml())])
        sleeps = []
        self.assertEqual(
            m.fetch("668506-2026", opener=source, sleep_fn=sleeps.append),
            fake_xml())
        self.assertEqual(sleeps, [1, 2, 2])
        self.assertEqual(len(source.calls), 4)

    def test_202_exhausted_blocks_no_fabricated_original(self):
        source = Source([Response(202, self.url(), fake_xml()) for _ in range(4)])
        sleeps = []
        with self.assertRaisesRegex(ValueError, "STATUS_202_RETRY_EXHAUSTED"):
            m.fetch("668506-2026", opener=source, sleep_fn=sleeps.append)
        self.assertEqual(len(source.calls), 4)
        self.assertEqual(sleeps, [1, 2, 2])

    def test_provider_retry_after_is_capped(self):
        source = Source([
            Response(202, self.url(), headers={"Retry-After": "9000000000"}),
            Response(200, self.url(), fake_xml()),
        ])
        delays = []
        m.fetch("668506-2026", opener=source, sleep_fn=delays.append)
        self.assertEqual(delays, [2])

    def test_retry_after_malformed_falls_back_to_bounded_delay(self):
        source = Source([
            Response(202, self.url(), headers={"Retry-After": "no-thanks"}),
            Response(200, self.url(), fake_xml()),
        ])
        delays = []
        m.fetch("668506-2026", opener=source, sleep_fn=delays.append)
        self.assertEqual(delays, [1])

    def test_retry_after_zero_respected_without_underflow(self):
        source = Source([
            Response(202, self.url(), headers={"Retry-After": "0"}),
            Response(200, self.url(), fake_xml()),
        ])
        delays = []
        m.fetch("668506-2026", opener=source, sleep_fn=delays.append)
        self.assertEqual(delays, [0])

    def test_no_sleep_on_immediate_200(self):
        source = Source([Response(200, self.url(), fake_xml())])
        delays = []
        received = m.fetch("668506-2026", opener=source, sleep_fn=delays.append)
        self.assertEqual(received, fake_xml())
        self.assertEqual(delays, [])

    def test_non202_206_is_terminal_not_retried(self):
        source = Source([
            Response(206, self.url(), fake_xml()),
            Response(200, self.url(), fake_xml()),
        ])
        delays = []
        with self.assertRaisesRegex(ValueError, "STATUS_206"):
            m.fetch("668506-2026", opener=source, sleep_fn=delays.append)
        self.assertEqual(len(source.calls), 1)
        self.assertEqual(delays, [])

    def test_non202_404_is_terminal_not_retried(self):
        source = Source([
            Response(404, self.url(), b"No original"),
            Response(200, self.url(), fake_xml()),
        ])
        with self.assertRaisesRegex(ValueError, "STATUS_404"):
            m.fetch("668506-2026", opener=source, sleep_fn=lambda _: None)
        self.assertEqual(len(source.calls), 1)

    def test_202_then_malicious_official_to_external_redirect_blocks(self):
        source = Source([
            Response(202, self.url()),
            Response(200, "https://untrusted.example/notice/668506-2026/xml", fake_xml()),
        ])
        with self.assertRaisesRegex(ValueError, "NOT_OFFICIAL"):
            m.fetch("668506-2026", opener=source, sleep_fn=lambda _: None)
        self.assertEqual(len(source.calls), 2)

    def test_202_then_wrong_notice_path_blocks(self):
        source = Source([
            Response(202, self.url()),
            Response(200, m.official_url("558592-2024"), fake_xml()),
        ])
        with self.assertRaisesRegex(ValueError, "NOT_OFFICIAL"):
            m.fetch("668506-2026", opener=source, sleep_fn=lambda _: None)

    def test_202_then_official_query_added_blocks(self):
        source = Source([
            Response(202, self.url()),
            Response(200, self.url() + "?redirect=true", fake_xml()),
        ])
        with self.assertRaisesRegex(ValueError, "NOT_OFFICIAL"):
            m.fetch("668506-2026", opener=source, sleep_fn=lambda _: None)

    def test_200_forged_body_rejected_by_exact_original_sha(self):
        data = fake_xml()
        source = Source([Response(200, self.url(), data)])
        x = dict(m.SOURCES["668506-2026"],
                 original_xml_sha256_pinned="f"*64,
                 original_xml_bytes_pinned=len(data))
        with patch.dict(m.SOURCES, {"668506-2026": x}):
            with self.assertRaisesRegex(ValueError, "PINNED_ORIGINAL_SHA256_MISMATCH"):
                m.inspect("668506-2026",
                          m.fetch("668506-2026", opener=source))

    def test_200_html_payload_cannot_be_accepted_as_xml(self):
        bad = "<html><body>Gewobag Gebäudeversicherung</body></html>".encode("utf-8") + b"x"*150
        source = Source([Response(200, m.official_url("558592-2024"), bad)])
        with self.assertRaisesRegex(ValueError, "INVALID_DOCUMENT"):
            m.inspect("558592-2024",
                      m.fetch("558592-2024", opener=source))

    def test_200_truncated_payload_rejected(self):
        source = Source([Response(200, self.url(), b"<xml/>")])
        with self.assertRaisesRegex(ValueError, "SOURCE_TRUNCATED"):
            m.fetch("668506-2026", opener=source)

    def test_200_oversized_original_blocks_without_secondary_fallback(self):
        source = Source([Response(200, self.url(), b"x"*(m.MAX_BYTES + 100))])
        with self.assertRaisesRegex(ValueError, "SOURCE_EXCEEDS_MAX_BYTES"):
            m.fetch("668506-2026", opener=source)

    def test_retry_budget_fails_closed_for_outside_bounds(self):
        for invalid in (0, 5, True, 1.5, "four"):
            with self.subTest(value=invalid), self.assertRaisesRegex(
                    ValueError, "RETRY_ATTEMPTS_OUT_OF_BOUNDS"):
                m.fetch("668506-2026", opener=lambda *args, **kw: None,
                        max_attempts=invalid)

    def test_unknown_notice_never_requested(self):
        source = Source([])
        with self.assertRaisesRegex(ValueError, "NOT_ALLOWLISTED"):
            m.fetch("123456-2026", opener=source)
        self.assertEqual(source.calls, [])

    def test_german_and_english_notice_ids_not_conflated(self):
        notice = "558592-2024"
        source = Source([Response(200, m.official_url(notice), fake_xml(notice))])
        self.assertEqual(m.fetch(notice, opener=source), fake_xml(notice))
        self.assertEqual(source.calls[0][0], m.official_url(notice))


if __name__ == "__main__":
    unittest.main()
