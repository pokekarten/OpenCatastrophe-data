# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No-network synthetic original Senate PDF source-provenance tests."""
import hashlib
import io
import unittest
from unittest.mock import patch

from research_runners import rva_berlin_senate_original_pdf_source_v0 as m


class FakeResponse:
    def __init__(self, raw:bytes,url:str):
        self.source=io.BytesIO(raw)
        self.url=url
    def geturl(self):
        return self.url
    def read(self, count:int):
        return self.source.read(count)
    def __enter__(self):return self
    def __exit__(self,*args):pass


class BerlinSenateOriginalPDFSourceTests(unittest.TestCase):
    def test_two_exact_official_pdf_sources(self):
        self.assertEqual(len(m.SOURCES),2)
        self.assertTrue(all(x["url"].startswith(
            "https://pardok.parlament-berlin.de/") for x in m.SOURCES))

    def test_no_unreviewed_publisher_url(self):
        with self.assertRaisesRegex(ValueError,"NOT_ALLOWLISTED"):
            m.fetch_original("https://other.example/senate.pdf")

    def test_fetch_bounded_official_pdf_simulation(self):
        source=m.SOURCES[0]["url"]
        data=b"%PDF-1.4\n"+b"a"*1700+b"%%EOF"
        result=m.fetch_original(source,opener=lambda req,timeout:FakeResponse(data,source))
        self.assertEqual(result,data)

    def test_redirect_to_nonpublisher_blocks(self):
        source=m.SOURCES[1]["url"]
        data=b"%PDF-1.4\n"+b"a"*1700+b"%%EOF"
        with self.assertRaisesRegex(ValueError,"REDIRECT_NOT_PUBLISHER"):
            m.fetch_original(source,opener=lambda req,timeout:FakeResponse(data,"https://example.com/a.pdf"))

    def test_truncated_pdf_blocks(self):
        source=m.SOURCES[0]["url"]
        data=b"%PDF-1.4\n"+b"a"*1700+b"UNFINISHED"
        with self.assertRaisesRegex(ValueError,"NOT_COMPLETE"):
            m.fetch_original(source,opener=lambda req,timeout:FakeResponse(data,source))

    def test_large_pdf_blocks(self):
        source=m.SOURCES[0]["url"]
        data=b"%PDF-1.4\n"+b"a"*(m.MAX_BYTES+20)+b"%%EOF"
        with self.assertRaisesRegex(ValueError,"OVERSIZE"):
            m.fetch_original(source,opener=lambda req,timeout:FakeResponse(data,source))

    def test_all_claimed_original_semantic_markers_need_presence(self):
        source=m.SOURCES[0]
        good="19 / 22 033 ... degewo ... GESOBAU WBM Allianz AG R+V Allgemeine Versicherung AG Sturm / Hagel"
        self.assertEqual(m.audit_text(good,source["markers"])["required_semantic_marker_count"],7)
        with self.assertRaisesRegex(ValueError,"REQUIRED_FACT_NOT_LOCATED"):
            m.audit_text("GESOBAU and WBM but not the insurer or the Berlin Senate",source["markers"])

    def test_borough_source_semantics_not_relabelled_insurer_cover(self):
        source=m.SOURCES[1]
        good=("19 / 24 229 Degewo Gesobau Gewobag HOWOGE "
              "82.637 49.054 34.040 376.278 18.666 Charlottenburg-Wilmersdorf")
        self.assertEqual(m.audit_text(good,source["markers"])["required_semantic_marker_count"],8)
        self.assertNotIn("covered_insurer_addresses",m.audit_text(good,source["markers"]))

    def test_truncated_semantics_text_fails(self):
        with self.assertRaisesRegex(ValueError,"TEXT_EXTRACTION_INVALID"):
            m.audit_text("x"*(m.MAX_EXTRACTED_TEXT+1),m.SOURCES[0]["markers"])

    def test_pdf_sharing_no_raw_path_in_receipt_contract(self):
        source=m.SOURCES[0]
        for forbidden in ("insured_locations","geocoded_addresses","actual_tiv"):
            self.assertNotIn(forbidden,source)

    def test_publisher_dates_differ_and_not_insurer_renewal(self):
        self.assertEqual(m.SOURCES[0]["pages_expected"],6)
        self.assertEqual(m.SOURCES[1]["pages_expected"],5)
        self.assertFalse(any(s["exact_original_sha256"] for s in m.SOURCES))


if __name__=="__main__":
    unittest.main()
