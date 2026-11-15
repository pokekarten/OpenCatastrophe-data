# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic only: PDF candidate byte identity and source-QA fail closed."""
import gzip
import json
import unittest
from unittest.mock import patch
from research_runners import meteofrance_four_north_original_v0 as fr
from research_runners.meteofrance_ciara2020_duplicate_pdf_v0 import (
    compare_pdf_candidates, Blocked
)

STATION = "76001001"
HEAD = "NUM_POSTE;AAAAMMJJHH;FF;FXI;FXI3S;QFXI3S;STATUS_FXI3S;LAT\n"
PREFIX = ("https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/"
          "BASE/INFOS_POSTES/76/")


def original():
    return gzip.compress((HEAD + "".join(
        f"{STATION};202002{day:02d}{hour:02d};4;15;22.2;1;0;49.1\n"
        for day in (9, 10, 11) for hour in range(24)
    )).encode("utf-8"), mtime=0)


def pdf(ch=b"x", length=2048):
    head=b"%PDF-1.7\n"+ch
    end=b"\n%%EOF\n"
    return head + b"x"*(length-len(head)-len(end)) + end


def resource(n, name, url=None):
    return {
        "id": "aaaaaaaa-bbbb-cccc-dddd-" + str(n).zfill(12),
        "title": "Departement_76_station_" + STATION + "_commune_" + name,
        "url": url or PREFIX + STATION + "_76_" + name + ".pdf",
        "filesize": 2048,
    }


def run(entries, bodies=None):
    original_bytes=original()
    with patch.object(fr,"ASSETS",{"76": (fr.ASSETS["76"][0],len(original_bytes),None)}):
        return compare_pdf_candidates(
            original_bytes, json.dumps({"resources": entries}).encode(),
            fetch_pdf=lambda url, _limit: (bodies or {}).get(url,pdf()),
            min_resources=1
        )


class TestCiaraDuplicatePdf(unittest.TestCase):
    def test_identical_original_bytes_remain_unadmitted(self):
        a=run([resource(1,"ONE"),resource(2,"TWO")])
        self.assertEqual(a["candidate_pdf_resource_count"],2)
        self.assertTrue(a["all_original_pdfs_byte_identical"])
        self.assertEqual(a["unique_pdf_sha256_count"],1)
        self.assertFalse(a["unique_historical_pdf_version_admitted"])
        self.assertFalse(a["source_admitted"])
        self.assertNotIn(STATION,json.dumps(a))
        self.assertNotIn("INFOS_POSTES",json.dumps(a))

    def test_distinct_pdfs_are_detected(self):
        a,b=resource(1,"ONE"),resource(2,"TWO")
        value=run([a,b],{a["url"]:pdf(b"1"),b["url"]:pdf(b"2")})
        self.assertEqual(value["unique_pdf_sha256_count"],2)
        self.assertFalse(value["all_original_pdfs_byte_identical"])
        self.assertEqual(value["total_original_pdf_bytes_checked"],4096)

    def test_duplicate_source_UUID_blocked(self):
        with self.assertRaises(Blocked):
            run([resource(1,"ONE"),resource(1,"TWO")])

    def test_unapproved_PDF_URL_blocked(self):
        with self.assertRaises(Blocked):
            run([resource(1,"ONE"),resource(2,"TWO","https://unapproved.example/b.pdf")])

    def test_single_source_not_misrepresented_as_ambiguous(self):
        with self.assertRaises(Blocked):
            run([resource(1,"ONE")])

    def test_invalid_original_pdf_blocked(self):
        a,b=resource(1,"ONE"),resource(2,"TWO")
        with self.assertRaises(Blocked):
            run([a,b],{a["url"]:b"not a PDF" + b"x"*2039,b["url"]:pdf()})
        with self.assertRaises(Blocked):
            run([a,b],{a["url"]:pdf()[:-1],b["url"]:pdf()})

    def test_mismatched_source_SHA_blocked(self):
        raw=original()
        with patch.object(fr,"ASSETS",{"76":(fr.ASSETS["76"][0],len(raw),"0"*64)}):
            with self.assertRaises(Blocked):
                compare_pdf_candidates(raw,json.dumps({"resources":[resource(1,"ONE"),resource(2,"TWO")]}).encode(),
                                       fetch_pdf=lambda *_:pdf(),min_resources=1)


if __name__ == "__main__":
    unittest.main()
