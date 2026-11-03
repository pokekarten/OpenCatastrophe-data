# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline check that dated 2021 ThinkHazard scores never impersonate 2026 portal."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ACCESS = ROOT / "access/worldbank.gfdrr.thinkhazard.screening-scores.2021-wb-catalogue.json"
REGISTER = ROOT / "landscape/sources-peer-cat-repositories-20261102.json"
NOTE = ROOT / "docs/research/thinkhazard-vintage-2021-vs-2026-boundary-20261103.md"
ID = "worldbank.gfdrr.thinkhazard.screening-scores"


class ThinkHazardVintageBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.access = json.loads(ACCESS.read_text(encoding="utf-8"))
        cls.registry = json.loads(REGISTER.read_text(encoding="utf-8"))
        cls.source = next(e for e in cls.registry["entries"] if e["candidate_id"] == ID)

    def test_exact_2021_product_and_no_2026_substitution(self):
        a = self.access
        self.assertEqual(a["source_ids"], [ID])
        self.assertIn("0060151", a["documentation_url"])
        self.assertIn("2021-11-29", a["api_version"])
        self.assertIn("2026", self.source["temporal_scope"])
        self.assertIn("production equivalence unverified", self.source["temporal_scope"])
        self.assertIn("2021", self.source["temporal_scope"])
        self.assertIn("2025-03-07", self.source["note"])
        self.assertIn("2026-09-18", self.source["note"])

    def test_rights_for_specific_dated_dataset_only(self):
        a=self.access
        self.assertEqual(a["rights_and_policy"]["dataset_rights_status"],"verified")
        self.assertEqual(a["rights_and_policy"]["api_terms_status"],"unknown")
        self.assertEqual(a["rights_and_policy"]["commercial_automation_status"],"unknown")
        self.assertEqual(a["rights_and_policy"]["redistribution_status"],"allowed")
        self.assertIn("2021", a["rights_and_policy"]["notes"])

    def test_no_download_or_live_api_path_authorized(self):
        a=self.access
        self.assertEqual(a["status"],"documented_only")
        self.assertEqual(a["implementation_decision"],"document_only")
        self.assertEqual(a["probe_contract"]["mode"],"none")
        self.assertIsNone(a["probe_contract"]["operation"])
        self.assertFalse(a["probe_contract"]["requires_credentials"])
        self.assertEqual(a["request_contract"]["path_templates"],
            ["/search/dataset/0060151/thinkhazard-hazard-ranking"])

    def test_not_admitted_to_scientific_hazard_or_loss(self):
        e=self.source
        self.assertEqual(e["admission_status"],"not_admitted")
        self.assertEqual(e["scientific_review_status"],"not_reviewed")
        self.assertIn("never physical ground intensity", e["note"])

    def test_no_new_duplicate_source_entry(self):
        self.assertEqual([e["candidate_id"] for e in self.registry["entries"]].count(ID),1)

    def test_research_note_separates_publication_and_catalogue_metadata(self):
        note=NOTE.read_text(encoding="utf-8")
        for marker in ("2021-11-29","2025-03-07","2026-09-18","CC BY 4.0",
                       "not", "not_admitted"):
            with self.subTest(marker=marker):
                self.assertIn(marker,note)


if __name__=="__main__":
    unittest.main()
