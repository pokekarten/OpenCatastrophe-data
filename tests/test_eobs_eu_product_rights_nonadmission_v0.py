# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline rights and science regression for the distinct C3S E-OBS_EU product.

This checks a versioned *discovery* record. CC BY 4.0 on E-OBS_EU does
not imply a provider GET, model admission, or identical rights for E-OBS.
No downloaded observations or external requests are used in these tests.
"""
from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "landscape/sources-eobs-eu-commercial-20261112.json"
PROJECTION = ROOT / "landscape/sources-eobs-eu-commercial-20261112.md"
RIGHTS_NOTE = ROOT / "docs/research/source-purpose-rights-audit-20261112.md"
RIGHTS_SCHEMA = ROOT / "sql/research_source_usage_rights_v0.sql"
ECMWF_LICENCE = (
    "https://cds.climate.copernicus.eu/licences/"
    "licence-to-use-E-OBS-and-E-OBS-EU-products"
)


class EobsEuProductBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.canonical = json.loads(CANONICAL.read_text(encoding="utf-8"))
        cls.entries = cls.canonical["entries"]
        cls.projection = PROJECTION.read_text(encoding="utf-8")
        cls.rights_note = RIGHTS_NOTE.read_text(encoding="utf-8")
        cls.rights_schema = RIGHTS_SCHEMA.read_text(encoding="utf-8")

    def test_exact_separately_licensed_source_identity_and_coverage(self):
        self.assertEqual(len(self.entries), 1)
        entry = self.entries[0]
        self.assertEqual(entry["candidate_id"], "copernicus.c3s.e-obs-eu.open-20261104")
        self.assertIn("E-OBS_EU", entry["name"])
        self.assertIn("Norway", entry["spatial_scope"])
        self.assertIn("Switzerland", entry["spatial_scope"])
        self.assertIn("Iceland", entry["spatial_scope"])
        self.assertIn("United Kingdom", entry["spatial_scope"])
        self.assertIn("e-obs-eu", entry["candidate_id"])
        self.assertNotEqual(entry["candidate_id"], "copernicus.c3s.e-obs.v33.0e")
        self.assertIn("commercial_use_candidate", entry["categories"])

    def test_public_licence_is_product_scoped_not_model_approval(self):
        entry = self.entries[0]
        self.assertIn(ECMWF_LICENCE, entry["note"])
        self.assertIn("CC BY 4.0", entry["note"])
        self.assertIn("non-commercial", entry["note"])
        self.assertIn("E-OBS_EU", self.rights_note)
        self.assertIn("E-OBS, Europe-wide", self.rights_note)
        self.assertIn("CC BY 4.0", self.rights_note)
        self.assertIn("Not permitted under public product licence", self.rights_note)
        self.assertIn("New CDS request syntax", self.rights_note)

    def test_remains_discovery_only_until_separate_rights_and_science(self):
        entry = self.entries[0]
        self.assertEqual(entry["candidate_status"], "evidence_checked")
        self.assertEqual(entry["rights_review_status"], "not_reviewed")
        self.assertEqual(entry["scientific_review_status"], "not_reviewed")
        self.assertEqual(entry["admission_status"], "not_admitted")
        self.assertIn("licence_acceptance_required", entry["access_class_hint"])
        self.assertIn("not verified API execution", entry["note"])
        self.assertIn("not yet an authorized source sample", entry["note"])

    def test_generated_projection_does_not_relabel_rights_or_admission(self):
        entry = self.entries[0]
        self.assertIn("GENERATED FILE", self.projection)
        self.assertIn(CANONICAL.name, self.projection)
        self.assertIn(entry["candidate_id"], self.projection)
        self.assertIn("rights `not_reviewed`", self.projection)
        self.assertIn("admission `not_admitted`", self.projection)

    def test_private_rights_schema_still_requires_use_case_and_rejects_admission(self):
        sql = self.rights_schema
        self.assertIn("PRIMARY KEY (source_id, product_scope, use_case)", sql)
        self.assertIn("CHECK (scientific_model_admission = false)", sql)
        self.assertIn("CHECK (original_asset_admitted = false)", sql)
        self.assertIn("'not_checked'", sql)
        self.assertIn("'commercial_cat_modelling'", sql)
        self.assertIn("'automated_api_access'", sql)
        self.assertIn("'external_raw_redistribution'", sql)
        self.assertNotIn("DROP TABLE", sql)
        self.assertNotIn("TRUNCATE", sql)


if __name__ == "__main__":
    unittest.main()
