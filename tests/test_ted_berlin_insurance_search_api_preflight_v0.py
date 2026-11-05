# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline official TED exact-publication metadata REST API negative checks."""
from __future__ import annotations

import hashlib
import io
import json
import unittest
from research_runners import ted_berlin_insurance_search_api_preflight_v0 as m


class FakeResponse:
    def __init__(self, data, url, status=200):
        self.data = io.BytesIO(data)
        self.url = url
        self.status = status
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def geturl(self):
        return self.url
    def read(self, count):
        return self.data.read(count)


def fixture(notice="668506-2026", *, buyer=None, title=None, row=None):
    b = buyer or ("Gewobag Wohnungsbau-Aktiengesellschaft Berlin" if notice == "558592-2024"
                  else "WBM Wohnungsbaugesellschaft Berlin-Mitte mbH")
    t = title or ("Gebäudeversicherung" if notice == "558592-2024"
                  else "Industrielle Sachversicherung für reine Gewerbeobjekte")
    if row is None:
        row = {
            "publication-number": notice,
            "buyer-name": {"de": [b]},
            "notice-title": {"de": t},
            "publication-date": "2026-09-29",
        }
    return json.dumps({"totalNoticeCount": 1, "notices": [row]},
                      ensure_ascii=False).encode("utf-8")


class TEDSearchAPIPrimaryReceiptTests(unittest.TestCase):
    def test_official_exact_post_request_not_broad_search(self):
        q = json.loads(m.query_body("558592-2024"))
        self.assertEqual(q["query"], "publication-number = 558592-2024")
        self.assertEqual(q["limit"], 2)
        self.assertEqual(q["scope"], "ALL")
        self.assertIn("buyer-name", q["fields"])

    def test_exact_records_pass_without_overclaiming_xml_or_insurer_tiv(self):
        for notice in ("558592-2024", "668506-2026"):
            with self.subTest(notice=notice):
                raw = fixture(notice)
                p = m.parse(notice, raw)
                self.assertTrue(p["publication_number_and_buyer_title_match"])
                self.assertEqual(p["structured_publisher_data_sha256"],
                                 hashlib.sha256(raw).hexdigest())
                for flag in ("original_eforms_xml_bytes_fetched_or_sha_pinned",
                             "awarded_underwriter_roles_extracted_from_original_eforms",
                             "insurer_site_allocation_or_tiv_observed",
                             "original_api_json_body_stored_or_logged"):
                    self.assertFalse(p[flag])

    def test_wrong_official_publication_refused(self):
        bad = fixture("668506-2026")
        with self.assertRaisesRegex(ValueError, "WRONG_PUBLICATION"):
            m.parse("558592-2024", bad)

    def test_zero_or_multiple_rows_not_exact_proof(self):
        empty = json.dumps({"notices": [], "padding": "synthetic source shape " * 4}).encode("utf-8")
        multi = json.dumps({"notices": [json.loads(fixture())["notices"][0]] * 2}).encode()
        with self.assertRaisesRegex(ValueError, "EXPECT_ONE_EXACT_PUBLICATION"):
            m.parse("668506-2026", empty)
        with self.assertRaisesRegex(ValueError, "EXPECT_ONE_EXACT_PUBLICATION"):
            m.parse("668506-2026", multi)

    def test_named_buyer_wrong_or_title_unrelated_rejected(self):
        for raw in (fixture(buyer="A different housing group"),
                    fixture(title="Kraftfahrzeugversicherung")):
            with self.assertRaises(ValueError):
                m.parse("668506-2026", raw)

    def test_no_buyer_or_title_makes_evidence_unknown_not_verified(self):
        x = {"publication-number": "668506-2026", "buyer-name": {},
             "notice-title": "Industrielle Sachversicherung"}
        with self.assertRaisesRegex(ValueError, "BUYER_OR_TITLE_FIELDS_ABSENT"):
            m.parse("668506-2026", fixture(row=x))

    def test_duplicate_keys_not_silently_accepted(self):
        raw = b'{"notices":[],"notices":[],"padding":"synthetic test duplicate key check"}'
        with self.assertRaisesRegex(ValueError, "DUPLICATE_JSON_KEY"):
            m.parse("668506-2026", raw)

    def test_wrong_host_from_valid_source_rejected(self):
        notice = "558592-2024"
        with self.assertRaisesRegex(ValueError, "NOT_FROM_OFFICIAL_HOST"):
            m.fetch(notice, opener=lambda req, timeout:
                    FakeResponse(fixture(notice), "https://example.org/notice"))

    def test_http_202_does_not_count_as_success(self):
        notice = "558592-2024"
        with self.assertRaisesRegex(ValueError, "HTTP_STATUS_202"):
            m.fetch(notice, opener=lambda req, timeout:
                    FakeResponse(fixture(notice), m.ENDPOINT, 202))

    def test_official_http_200_json_source_is_parseable(self):
        notice = "558592-2024"
        original = fixture(notice)
        out = m.fetch(notice, opener=lambda req, timeout:
                      FakeResponse(original, m.ENDPOINT))
        self.assertEqual(m.parse(notice, out)["publication_number"], notice)

    def test_unexpected_lookalike_lei_labels_not_exposure(self):
        x = m.parse("668506-2026", fixture())
        self.assertNotIn("carrier_LEI", x)
        self.assertNotIn("insured_location_count", x)

    def test_oversized_response_refused(self):
        notice = "668506-2026"
        with self.assertRaisesRegex(ValueError, "TOO_BIG_OR_MISSING"):
            m.fetch(notice, opener=lambda req, timeout:
                    FakeResponse(b"x" * (m.MAX_BYTES + 1), m.ENDPOINT))

    def test_wrong_syntax_or_nonfinite_json_rejected(self):
        bad = b'{"notices":[NaN],"padding":"synthetic source nonfinite numerical data"}'
        with self.assertRaisesRegex(ValueError, "NONFINITE"):
            m.parse("668506-2026", bad)

    def test_source_bounded_to_two_approved_notices(self):
        with self.assertRaisesRegex(ValueError, "NOT_ALLOWLISTED"):
            m.query_body("other-2026")
        with self.assertRaisesRegex(ValueError, "WRONG_NOTICE"):
            m.parse("other-2026", fixture())

    def test_original_primary_record_is_not_conflated_with_official_xml(self):
        x = m.parse("558592-2024", fixture("558592-2024"))
        self.assertFalse(x["original_eforms_xml_bytes_fetched_or_sha_pinned"])
        self.assertFalse(x["awarded_underwriter_roles_extracted_from_original_eforms"])


if __name__ == "__main__":
    unittest.main()
