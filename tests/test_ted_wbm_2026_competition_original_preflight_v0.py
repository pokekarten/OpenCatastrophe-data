# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline-only primary TED WBM 2026 competition provenance refusals."""
from __future__ import annotations

import hashlib
import io
import unittest

from research_runners import ted_wbm_2026_competition_original_preflight_v0 as m


def synthetic() -> bytes:
    return (f"""<?xml version="1.0" encoding="UTF-8"?>
<ContractNotice>
  <PublicationNumber>{m.NOTICE}</PublicationNumber>
  <Buyer>WBM Wohnungsbaugesellschaft Berlin-Mitte mbH</Buyer>
  <Title>Industrielle Sachversicherung für neun reine Gewerbeobjekte</Title>
  <Info>Für ein Führungsangebot wird eine Zeichnungsquote von mindestens 30 % vorausgesetzt, für ein Beteiligungsangebot mindestens 15 %</Info>
  <Perils>Sturm Hagel Überschwemmung Erdbeben Feuer</Perils>
</ContractNotice>""").encode("utf-8")


class Response:
    def __init__(self, status=200, data=b"", url=m.URL):
        self.status = status
        self.stream = io.BytesIO(data)
        self.url = url
    def __enter__(self):
        return self
    def __exit__(self, *x):
        return False
    def geturl(self):
        return self.url
    def read(self, n):
        return self.stream.read(n)


class OfficialWBMCompetitionSourceTests(unittest.TestCase):
    def test_original_source_exact_markers_and_metadata_receipt(self):
        raw = synthetic()
        x = m.inspect(raw)
        self.assertEqual(x["original_source_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertTrue(x["lead_writing_minimum_30_percent_in_2026_tender_text"])
        self.assertTrue(x["follower_writing_minimum_15_percent_in_2026_tender_text"])
        self.assertFalse(x["final_policy_coverage_quotas_or_rv_10_percent_verified"])
        self.assertFalse(x["original_xml_retrieval_independently_rechecked_against_reviewed_sha"])
        self.assertEqual(x["commercial_object_count_described_not_geocoded"], 9)

    def test_official_http_200_from_exact_source_only(self):
        raw = synthetic()
        calls = []
        def opener(req, timeout):
            calls.append((req.full_url, timeout))
            return Response(data=raw)
        self.assertEqual(m.fetch(opener=opener), raw)
        self.assertEqual(calls, [(m.URL, 35)])

    def test_http202_may_be_pending_then_a_complete_200(self):
        chunks = [Response(202, b"pending"), Response(200, synthetic())]
        self.assertEqual(m.fetch(opener=lambda req, timeout: chunks.pop(0)), synthetic())

    def test_http202_exhausted_fails_closed(self):
        items = [Response(202, synthetic()), Response(202, synthetic())]
        with self.assertRaisesRegex(ValueError, "HTTP_202_NO_ORIGINAL"):
            m.fetch(opener=lambda req, timeout: items.pop(0))

    def test_unrelated_publisher_host_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "NONOFFICIAL_REDIRECT"):
            m.fetch(opener=lambda req, timeout:
                    Response(200, synthetic(), "https://mirror.example/copy"))

    def test_publisher_changed_notice_path_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "NONOFFICIAL_REDIRECT"):
            m.fetch(opener=lambda req, timeout:
                    Response(200, synthetic(),
                             "https://ted.europa.eu/en/notice/668506-2026/xml"))

    def test_http404_is_not_a_valid_xml_notice(self):
        with self.assertRaisesRegex(ValueError, "HTTP_NON200_404"):
            m.fetch(opener=lambda req, timeout: Response(404, synthetic()))

    def test_contract_award_root_is_not_competition_source(self):
        raw = synthetic().replace(b"<ContractNotice>", b"<ContractAwardNotice>").replace(
            b"</ContractNotice>", b"</ContractAwardNotice>")
        with self.assertRaisesRegex(ValueError, "NOT_COMPETITION_NOTICE"):
            m.inspect(raw)

    def test_missing_30_percent_condition_fails_source_preflight(self):
        raw = synthetic().replace(b"30 %", b"20 %")
        with self.assertRaisesRegex(ValueError, "MISSING_SOURCE_MARKER_lead_minimum_30"):
            m.inspect(raw)

    def test_missing_15_percent_condition_fails_source_preflight(self):
        raw = synthetic().replace(b"15 %", b"14 %")
        with self.assertRaisesRegex(ValueError, "MISSING_SOURCE_MARKER_participating_minimum_15"):
            m.inspect(raw)

    def test_wrong_notice_id_fails_preflight(self):
        raw = synthetic().replace(b"286307-2026", b"999999-2026")
        with self.assertRaisesRegex(ValueError, "WRONG_PUBLICATION_ID"):
            m.inspect(raw)

    def test_no_unsourced_flood_or_earthquake_assumptions(self):
        raw = synthetic().replace("Überschwemmung".encode(), b"Frost")
        with self.assertRaisesRegex(ValueError, "MISSING_SOURCE_MARKER_flood"):
            m.inspect(raw)

    def test_xml_dtd_not_consumed(self):
        raw = synthetic().replace(
            b"<ContractNotice>", b'<!DOCTYPE ContractNotice [<!ENTITY x "y">]><ContractNotice>')
        with self.assertRaisesRegex(ValueError, "XML_DTD_FORBIDDEN"):
            m.inspect(raw)


if __name__ == "__main__":
    unittest.main()
