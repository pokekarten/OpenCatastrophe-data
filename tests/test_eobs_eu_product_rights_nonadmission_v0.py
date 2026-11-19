# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, source-scoped checks for the new E-OBS_EU research candidate.

These tests verify declared rights boundaries, not provider availability or legal
admission. The canonical JSON is the only product-identity authority here.
"""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "landscape/sources-eobs-eu-commercial-20261112.json"
VIEW = SOURCE.with_suffix(".md")
LICENCE = "https://cds.climate.copernicus.eu/licences/licence-to-use-E-OBS-and-E-OBS-EU-products"


class EobsEuProductRightsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = json.loads(SOURCE.read_text(encoding="utf-8"))["entries"]
        cls.entry = cls.entries[0]
        cls.view = VIEW.read_text(encoding="utf-8")

    def test_single_separate_original_product(self):
        self.assertEqual(len(self.entries), 1)
        self.assertEqual(self.entry["candidate_id"], "copernicus.c3s.e-obs-eu.open-20261104")
        for country in ("Norway", "Switzerland", "Iceland", "United Kingdom"):
            self.assertIn(country, self.entry["spatial_scope"])
        self.assertIn("E-OBS_EU", self.entry["name"])
        self.assertNotEqual(self.entry["candidate_id"], "copernicus.c3s.e-obs.v33.0e")

    def test_licence_is_product_scoped(self):
        note = self.entry["note"]
        self.assertIn(LICENCE, note)
        self.assertIn("E-OBS_EU CC BY 4.0", note)
        self.assertIn("E-OBS is separate and strictly non-commercial", note)
        self.assertIn("old API request syntax must not be assumed valid", note)
        self.assertIn("Station-network lineage is shared", note)

    def test_fail_closed_review_and_science(self):
        self.assertEqual(self.entry["candidate_status"], "evidence_checked")
        self.assertEqual(self.entry["rights_review_status"], "not_reviewed")
        self.assertEqual(self.entry["scientific_review_status"], "not_reviewed")
        self.assertEqual(self.entry["admission_status"], "not_admitted")
        self.assertIn("licence_acceptance_required", self.entry["access_class_hint"])
        self.assertIn("not verified API execution", self.entry["note"])
        self.assertIn("not yet an authorized source sample", self.entry["note"])

    def test_projection_is_not_independent_authority(self):
        self.assertIn("GENERATED FILE — DO NOT EDIT DIRECTLY", self.view)
        self.assertIn(SOURCE.name, self.view)
        self.assertIn(self.entry["candidate_id"], self.view)
        self.assertIn("rights `not_reviewed`", self.view)
        self.assertIn("admission `not_admitted`", self.view)


if __name__ == "__main__":
    unittest.main()
