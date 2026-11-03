# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Regression checks for event-geocoding and infrastructure source boundaries.

Research-only catalogue metadata; never treats a provider URL or rights hint
as proof of an admissible hazard field, insurer portfolio or claim.
"""
from __future__ import annotations

import json
from pathlib import Path
import unittest

SOURCE = (
    Path(__file__).resolve().parents[1]
    / "landscape/sources-global-event-geocoding-infra-20261103.json"
)
EXPECTED = {
    "nasa.sedac.gdis.v1.00",
    "emdat.llm-geodis.2025",
    "vub.hydr.wikimpacts.v1.0.final",
    "seerai.hifld.archive.2025",
    "earthgenome.noaa.storm-events.geoparquet.2025",
}


class EventGeocodingSourceBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = json.loads(SOURCE.read_text(encoding="utf-8"))["entries"]
        cls.by_id = {item["candidate_id"]: item for item in cls.entries}

    def test_only_five_unique_research_candidates(self):
        self.assertEqual(set(self.by_id), EXPECTED)
        self.assertEqual(len(self.entries), len(self.by_id))
        urls = [item["authoritative_url"].rstrip("/") for item in self.entries]
        self.assertEqual(len(urls), len(set(urls)))

    def test_no_rights_or_scientific_admission(self):
        for item in self.entries:
            with self.subTest(source=item["candidate_id"]):
                self.assertEqual(item["admission_status"], "not_admitted")
                self.assertEqual(item["rights_review_status"], "not_reviewed")
                self.assertEqual(item["scientific_review_status"], "not_reviewed")

    def test_emdat_derivatives_are_not_independent_hazard_footprints(self):
        for key in ("nasa.sedac.gdis.v1.00", "emdat.llm-geodis.2025"):
            note = self.by_id[key]["note"].lower()
            self.assertIn("em-dat", note)
            self.assertTrue(
                "not independent" in note or "neither independent" in note,
                f"missing independence disclaimer for {key}",
            )
        self.assertIn("administrative", self.by_id["nasa.sedac.gdis.v1.00"]["note"].lower())

    def test_wikimpacts_noncommercial_and_no_automatic_insurer_reuse(self):
        x = self.by_id["vub.hydr.wikimpacts.v1.0.final"]
        self.assertIn("CC_BY_NC_SA_4_0", x["access_class_hint"])
        self.assertIn("not authorized", x["note"].lower())

    def test_noaa_derivative_points_not_storm_footprints_or_insured_losses(self):
        x = self.by_id["earthgenome.noaa.storm-events.geoparquet.2025"]
        note = x["note"].lower()
        self.assertIn("noaa", note)
        self.assertIn("not", note)
        self.assertIn("insured losses", note)
        self.assertIn("footprints", note)

    def test_hifld_archive_not_verified_insured_asset_inventory(self):
        x = self.by_id["seerai.hifld.archive.2025"]
        self.assertIn("historical", x["categories"][x["categories"].index("historical_archive")])
        self.assertIn("not insured", x["note"].lower())


if __name__ == "__main__":
    unittest.main()
