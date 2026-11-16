# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic station PDFs; no external network or PDF dependency in normal CI."""
from __future__ import annotations

import gzip
import json
import unittest
from unittest.mock import patch

from research_runners import meteofrance_four_north_original_v0 as fr
from research_runners.meteofrance_ciara2020_pdf_text_diff_v0 import (
    Blocked, compare_pdf_text, normalized_text, text_profile
)
from tests.test_meteofrance_ciara2020_duplicate_pdf_v0 import (
    original, resource, pdf
)


def run(profile_a, profile_b):
    raw=original()
    r1,r2=resource(1,"ONE"),resource(2,"TWO")
    profile_by_bytes={pdf(b"1"):profile_a,pdf(b"2"):profile_b}
    with patch.object(fr,"ASSETS",{"76":(fr.ASSETS["76"][0],len(raw),None)}):
        from research_runners.meteofrance_ciara2020_duplicate_pdf_v0 import compare_pdf_candidates
        rec=compare_pdf_candidates(
            raw,json.dumps({"resources":[r1,r2]}).encode(),
            fetch_pdf=lambda u,_: pdf(b"1") if u==r1["url"] else pdf(b"2"),
            min_resources=1
        )
        return compare_pdf_text(
            raw,json.dumps({"resources":[r1,r2]}).encode(),
            download_pdf=lambda u,_: pdf(b"1") if u==r1["url"] else pdf(b"2"),
            extractor=lambda content: profile_by_bytes[content],
            min_resources=1,
            expected_cohort_sha256=rec["station_bound_pdf_cohort_digest"]
        )


class TestOriginalPdfTextDiff(unittest.TestCase):
    def test_unicode_whitespace_normalize(self):
        self.assertEqual(normalized_text("  VENT \n  2020  "),"vent 2020")
        self.assertEqual(normalized_text("CAFÉ"),normalized_text("cafe\u0301"))

    def test_text_signal_is_not_instrument_attestation(self):
        p=text_profile(["Station: Vent, anémomètre, implantation, hauteur, 2020. "*4])
        self.assertEqual(p["pages_with_extracted_text"],1)
        self.assertTrue(p["has_substantive_extracted_text"])
        self.assertTrue(p["possible_review_subjects"]["mentions_2020"])
        self.assertTrue(p["possible_review_subjects"]["mentions_instrument_word"])
        self.assertNotIn("Station:",str(p))

    def test_pdf_text_limits_fail_closed(self):
        with self.assertRaises(Blocked):
            text_profile([])
        with self.assertRaises(Blocked):
            text_profile(["x"]*33)
        with self.assertRaises(Blocked):
            text_profile(["x"*75001])
        with self.assertRaises(Blocked):
            text_profile(["x"*60000]*5)

    def test_2020_and_wind_words_do_not_imply_site_validation(self):
        p=text_profile(["Site anémomètre, vent 2020 et hauteur. "*10])
        self.assertTrue(p["possible_review_subjects"]["mentions_site_word"])
        self.assertTrue(p["possible_review_subjects"]["mentions_height_word"])
        self.assertFalse("source_admitted" in p)

    def test_equal_extracted_text_but_unequal_original_bytes(self):
        p=text_profile(["Rafale d'une station: Vent 2020. "*6])
        r=run(p,p)
        self.assertTrue(r["normalized_extracted_text_equal"])
        self.assertFalse(r["text_content_disagreement_detected"])
        self.assertTrue(r["source_pdf_bytes_are_different"])
        self.assertFalse(r["historical_source_version_safely_selected"])
        self.assertFalse(r["source_admitted"])

    def test_different_extracted_text(self):
        x=text_profile(["Wind station source version A. "*7])
        y=text_profile(["Wind station source version B. "*7])
        r=run(x,y)
        self.assertFalse(r["normalized_extracted_text_equal"])
        self.assertTrue(r["text_content_disagreement_detected"])
        self.assertEqual(len(r["pdf_content_profiles"]),2)

    def test_textless_scanned_pdf_is_not_falsely_equal(self):
        x=text_profile([""])
        y=text_profile([""])
        r=run(x,y)
        self.assertIsNone(r["normalized_extracted_text_equal"])
        self.assertIsNone(r["text_content_disagreement_detected"])
        self.assertFalse(r["both_original_pdfs_have_extractable_text"])

    def test_output_leaks_no_pdf_text_or_station_id(self):
        p=text_profile(["A detailed meteorological station vent 2020. "*6])
        r=run(p,p)
        v=json.dumps(r)
        self.assertNotIn("76001001",v)
        self.assertNotIn("A detailed meteorological",v)
        self.assertNotIn("INFOS_POSTES",v)

    def test_bad_original_and_cohort_digest_block(self):
        p=text_profile(["Relevant text. "*25])
        raw=original()
        with patch.object(fr,"ASSETS",{"76":(fr.ASSETS["76"][0],len(raw),"0"*64)}):
            with self.assertRaisesRegex(Blocked,"SHA-256"):
                compare_pdf_text(raw,b"{}",min_resources=1)
        with self.assertRaisesRegex(Blocked,"cohort"):
            run_bad_cohort(p)


def run_bad_cohort(p):
    raw=original()
    r1,r2=resource(1,"ONE"),resource(2,"TWO")
    with patch.object(fr,"ASSETS",{"76":(fr.ASSETS["76"][0],len(raw),None)}):
        return compare_pdf_text(
            raw,json.dumps({"resources":[r1,r2]}).encode(),
            download_pdf=lambda u,_: pdf(b"1") if u==r1["url"] else pdf(b"2"),
            extractor=lambda _:p,
            min_resources=1,
            expected_cohort_sha256="0"*64
        )


if __name__=="__main__":
    unittest.main()
