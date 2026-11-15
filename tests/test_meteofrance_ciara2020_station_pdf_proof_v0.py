# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No network or source PDFs: fake original stations and tiny synthetic PDFs."""
from __future__ import annotations

import gzip
import json
import unittest
from unittest.mock import patch

from research_runners import meteofrance_four_north_original_v0 as fr
from research_runners.meteofrance_ciara2020_station_pdf_proof_v0 import (
    Blocked, complete_quality_station_ids, resolve_station_sheets,
    station_pdf_proof, verify_pdf_bytes, COMP_PREFIX,
)

HEADER = "NUM_POSTE;AAAAMMJJHH;FF;FXI;FXI3S;QFXI3S;STATUS_FXI3S;LAT\n"


def archive(quality="1", modified=None):
    rows = [
        f"62001001;202002{day:02d}{hour:02d};4;15;22.2;{quality};0;50.3\n"
        for day in (9, 10, 11) for hour in range(24)
    ]
    if modified is not None:
        rows[0] = modified
    return gzip.compress((HEADER + "".join(rows)).encode(), mtime=0)


def station_catalogue(*, rid="aaaaaaaa-bbbb-cccc-dddd-000000000001",
                      url=None, size=2048, duplicate=False):
    url = url or (
        "https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/BASE/"
        "INFOS_POSTES/62/62001001_62_TEST-VILLE.pdf"
    )
    row = {"title": "Departement_62_station_62001001_commune_TEST-VILLE",
           "id": rid, "url": url, "filesize": size, "format": "pdf"}
    return json.dumps({"resources": [row, row] if duplicate else [row]}).encode()


def synthetic_pdf(size=2048):
    base = b"%PDF-1.7\n" + b"x" * (size-20) + b"\n%%EOF\n"
    return base + b"y" * (size - len(base))


class TestStationPdfProvenance(unittest.TestCase):
    def test_complete_gust_station_filter(self):
        self.assertEqual(complete_quality_station_ids(archive()), {"62001001"})
        self.assertEqual(complete_quality_station_ids(archive("9")), set())

    def test_exact_official_station_sheet_identity(self):
        selected, digest = resolve_station_sheets(
            station_catalogue(), {"62001001"}, "62", min_resources=1
        )
        self.assertEqual(len(selected), 1)
        self.assertEqual(len(digest), 64)
        self.assertEqual(verify_pdf_bytes(synthetic_pdf(), selected["62001001"]),
                         __import__("hashlib").sha256(synthetic_pdf()).hexdigest())

    def test_duplicate_and_missing_station_sheet_fail(self):
        with self.assertRaisesRegex(Blocked, "ambiguous"):
            resolve_station_sheets(station_catalogue(duplicate=True),
                                   {"62001001"}, "62", min_resources=1)
        with self.assertRaisesRegex(Blocked, "no exact"):
            resolve_station_sheets(station_catalogue(),
                                   {"62001002"}, "62", min_resources=1)

    def test_partial_exact_title_match_is_explicitly_unadmitted(self):
        matched, _catalogue_digest, unmatched = resolve_station_sheets(
            station_catalogue(), {"62001001", "62001002"}, "62",
            min_resources=1, allow_unmatched=True
        )
        self.assertEqual(len(matched), 1)
        self.assertEqual(unmatched, 1)
        source = archive()
        assets = {"62": (fr.ASSETS["62"][0], len(source), None)}
        # This separate test also verifies a partial metadata catalogue never
        # falsely upgrades source, site or instrument review status.
        with patch.object(fr, "ASSETS", assets):
            receipt = station_pdf_proof(
                "62", source, station_catalogue(),
                download_pdf=lambda *_: synthetic_pdf(), min_resources=1
            )
        self.assertEqual(receipt["eligible_station_pdf_unmatched_exact_title_count"], 0)
        self.assertTrue(receipt["eligible_station_pdf_exact_match_complete"])
        self.assertFalse(receipt["station_site_and_instrument_history_verified_for_2020"])

    def test_duplicate_titles_remain_unusable_with_partial_ambiguity_report(self):
        matched, digest, unmatched, ambiguity = resolve_station_sheets(
            station_catalogue(duplicate=True), {"62001001"}, "62",
            min_resources=1, allow_unmatched=True, report_ambiguous=True
        )
        self.assertEqual(matched, {})
        self.assertEqual(unmatched, 0)
        self.assertEqual(len(ambiguity), 1)
        self.assertEqual(len(digest), 64)

    def test_complementary_publisher_assets_require_exact_id_and_path(self):
        alt = ("https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/"
               "BASE/INFOS_POSTES_COMP/62/62001001_62_TEST-VILLE.pdf")
        matches, digest = resolve_station_sheets(
            station_catalogue(url=alt), {"62001001"}, "62",
            min_resources=1, prefix=COMP_PREFIX
        )
        self.assertEqual(len(matches), 1)
        self.assertEqual(len(digest), 64)
        with self.assertRaises(Blocked):
            resolve_station_sheets(station_catalogue(), {"62001001"}, "62",
                                   min_resources=1, prefix=COMP_PREFIX)

    def test_missing_primary_can_only_match_exact_complementary_station(self):
        source = archive()
        assets = {"62": (fr.ASSETS["62"][0], len(source), None)}
        primary = json.dumps({"resources": [
            {"title":"Departement_62_station_62001002_commune_OTHER",
             "id":"aaaaaaaa-bbbb-cccc-dddd-000000000002",
             "url":"https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/"
                   "BASE/INFOS_POSTES/62/62001002_62_OTHER.pdf",
             "filesize":2048}
        ]}).encode()
        alt = ("https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/"
               "BASE/INFOS_POSTES_COMP/62/62001001_62_TEST-VILLE.pdf")
        with patch.object(fr,"ASSETS",assets):
            result = station_pdf_proof(
                "62", source, primary,
                supplemental_catalogue=station_catalogue(url=alt),
                download_pdf=lambda *_: synthetic_pdf(),
                min_resources=1, min_supplemental_resources=1
            )
        self.assertEqual(result["official_station_pdf_primary_count"],0)
        self.assertEqual(result["official_station_pdf_complementary_count"],1)
        self.assertEqual(result["eligible_station_pdf_unmatched_exact_title_count"],0)
        self.assertFalse(result["station_site_and_instrument_history_verified_for_2020"])
        self.assertNotIn("62001001",json.dumps(result))

    def test_wrong_host_and_station_path_block(self):
        bad = "https://unapproved.example/62/62001001.pdf"
        with self.assertRaises(Blocked):
            resolve_station_sheets(station_catalogue(url=bad),
                                   {"62001001"}, "62", min_resources=1)
        wrong = ("https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/"
                 "BASE/INFOS_POSTES/76/62001001_62_TEST-VILLE.pdf")
        with self.assertRaises(Blocked):
            resolve_station_sheets(station_catalogue(url=wrong),
                                   {"62001001"}, "62", min_resources=1)

    def test_oversized_or_truncated_station_pdf_fails(self):
        with self.assertRaises(Blocked):
            resolve_station_sheets(station_catalogue(size=7_000_000),
                                   {"62001001"}, "62", min_resources=1)
        records, _ = resolve_station_sheets(station_catalogue(),
                                            {"62001001"}, "62", min_resources=1)
        with self.assertRaises(Blocked):
            verify_pdf_bytes(b"%PDF-1.7\n%%EOF", records["62001001"])
        with self.assertRaises(Blocked):
            verify_pdf_bytes(b"a" * 2048, records["62001001"])

    def test_event_station_match_and_no_station_information_logged(self):
        source = archive()
        assets = {"62": (fr.ASSETS["62"][0], len(source), None)}
        pdf = synthetic_pdf()
        called = []
        def fake_fetch(url, bound):
            called.append((url, bound))
            return pdf
        with patch.object(fr, "ASSETS", assets):
            result = station_pdf_proof(
                "62", source, station_catalogue(), download_pdf=fake_fetch,
                min_resources=1
            )
        self.assertEqual(result["official_station_catalogue_pdf_resource_count"], 1)
        self.assertEqual(result["pdf_original_bytes_verified"], 2048)
        self.assertEqual(len(called), 1)
        self.assertFalse(result["station_site_and_instrument_history_verified_for_2020"])
        self.assertFalse(result["source_admitted"])
        self.assertNotIn("62001001", json.dumps(result))
        self.assertNotIn("TEST-VILLE", json.dumps(result))

    def test_window_gust_missing_blocks_match_but_not_confused_with_pdf(self):
        source = archive("9")
        assets = {"62": (fr.ASSETS["62"][0], len(source), None)}
        with patch.object(fr, "ASSETS", assets), self.assertRaises(Blocked):
            station_pdf_proof("62", source, station_catalogue(),
                              download_pdf=lambda *_: synthetic_pdf(),
                              min_resources=1)


if __name__ == "__main__":
    unittest.main()
