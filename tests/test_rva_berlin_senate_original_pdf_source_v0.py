# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No-network synthetic original Senate PDF source-provenance tests."""
import hashlib
import io
import copy
import tomllib
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
    def test_recorded_original_bytes_and_semantics_still_match_source(self):
        reg=tomllib.loads(m.REGISTER.read_text(encoding="utf-8"))
        rec=[{
            "original_sha256":x["original_sha256"],
            "original_bytes":x["original_bytes"],
            "source_pdf_pages_extracted":x["original_pages"],
            "semantic_marker_count":x["positive_semantic_marker_count"],
            "exact_source_sha_pinned":True,
            "raw_pdf_stored_or_exported":False,
            "CAT_model_exposure_admitted":False,
        } for x in reg["documents"]]
        self.assertTrue(m.verify_saved_exact_original_source_receipts(rec,register=reg)[
            "exact_official_original_sha_byte_page_marker_receipts_conserved"
        ])
        self.assertEqual(len(rec),2)

    def test_tampering_original_byte_size_is_rejected(self):
        reg=tomllib.loads(m.REGISTER.read_text(encoding="utf-8"))
        rec=[{
            "original_sha256":x["original_sha256"],
            "original_bytes":x["original_bytes"],
            "source_pdf_pages_extracted":x["original_pages"],
            "semantic_marker_count":x["positive_semantic_marker_count"],
            "exact_source_sha_pinned":True,
            "raw_pdf_stored_or_exported":False,
            "CAT_model_exposure_admitted":False,
        } for x in reg["documents"]]
        rec[0]["original_bytes"]+=1
        with self.assertRaisesRegex(ValueError,"VALUES_OR_SCOPE_DRIFT"):
            m.verify_saved_exact_original_source_receipts(rec,register=reg)

    def test_false_real_rv_insured_sites_source_claim_is_rejected(self):
        reg=tomllib.loads(m.REGISTER.read_text(encoding="utf-8"))
        reg["actual_RV_insured_berlin_building_sites_verified"]=True
        with self.assertRaisesRegex(ValueError,"RESEARCH_SCOPE_CHANGED"):
            m.verify_saved_exact_original_source_receipts([],register=reg)

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
        self.assertTrue(all(len(s["exact_original_sha256"])==64 for s in m.SOURCES))
        self.assertEqual([s["exact_original_bytes"] for s in m.SOURCES],[22528,21842])

    def test_wrong_but_valid_pdf_sha_is_rejected_before_text_extraction(self):
        raw=b"%PDF-1.4\\n"+b"x"*2500+b"%%EOF"
        with self.assertRaisesRegex(ValueError,"ORIGINAL_SHA_CHANGED"):
            m.inspect_original(m.SOURCES[0],raw,extractor="nonexistent")

    def test_wrong_byte_count_is_rejected_before_text_extraction(self):
        raw=b"%PDF-1.4\\n"+b"x"*2500+b"%%EOF"
        src=dict(m.SOURCES[0],exact_original_sha256=hashlib.sha256(raw).hexdigest())
        with self.assertRaisesRegex(ValueError,"BYTE_COUNT_CHANGED"):
            m.inspect_original(src,raw,extractor="nonexistent")


if __name__=="__main__":
    unittest.main()
