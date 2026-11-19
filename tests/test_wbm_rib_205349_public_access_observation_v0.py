# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""WBM public RIB 205349 access observation; source/permissions not invented."""
from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

from research_runners import wbm_rib_205349_public_documents_preflight_v0 as probe

DATA = (
    Path(__file__).resolve().parents[1] / "research" /
    "observations" / "wbm_2026_rib_205349_public_access_v0.toml"
)


class WBMRIBAccessObservationTests(unittest.TestCase):
    def setUp(self):
        self.r = tomllib.loads(DATA.read_text(encoding="utf-8"))

    def test_observed_rendered_public_unavailability_and_no_raw_sha(self):
        r = self.r
        self.assertEqual(r["official_rib_landing_url"], probe.OFFICIAL_URL)
        self.assertTrue(r["public_rendered_page_says_announcement_not_found"])
        self.assertTrue(r["public_rendered_page_says_no_longer_publicly_available"])
        self.assertEqual(r["observed_with"], "Exa public webpage fetch, rendered text")
        self.assertFalse(r["raw_rib_response_html_sha256_available"])

    def test_not_an_attachment_inventory(self):
        self.assertEqual(self.r["direct_downloaded_tender_document_count"], 0)
        self.assertFalse(self.r["any_tender_attachment_original_file_bytes_obtained"])
        self.assertFalse(self.r["full_insurance_technical_specification_obtained"])
        self.assertFalse(self.r["signed_final_coinsurance_policy_or_annex_obtained"])

    def test_official_berlin_policy_does_not_guarantee_expired_access(self):
        p = self.r["official_procurement_access_policy"]
        self.assertTrue(p["general_public_access_to_live_tender_documents_described"])
        self.assertFalse(p["expired_tender_documents_guaranteed_still_downloadable"])

    def test_public_buyer_is_not_evidence_of_received_sensitive_files(self):
        self.assertEqual(self.r["official_buyer"]["public_procurement_contact_email"],
                         "vergabe@wbm.de")
        self.assertFalse(self.r["official_buyer"]
                         ["buyer_has_provided_risk_schedules_to_this_research"])

    def test_april_rib_link_not_auto_proof_april_and_september_one_procedure(self):
        self.assertEqual(self.r["source_notice_publication_number_that_links_rib"],
                         "286307-2026")
        self.assertFalse(
            self.r["source_notice_reference_is_same_as_award_formal_BT04_confirmed"])
        self.assertFalse(self.r["april_competition"]
                         ["april_conditions_proven_applicable_to_september_award"])
        self.assertNotEqual(
            self.r["april_competition"]["BT04_index_uuid"],
            self.r["award_september"]["BT04_index_uuid"])

    def test_no_actual_rv_policy_share_or_site_values(self):
        self.assertFalse(self.r["policy_share_percentage_verified_from_signed_contract"])
        self.assertFalse(self.r["nine_individual_building_geocodes_or_insured_TIVs_obtained"])
        self.assertFalse(self.r["actual_insurer_portfolio_or_CAT_exposure_admitted"])
        self.assertFalse(self.r["award_september"]
                         ["contract_labels_are_a_signed_policy_share_schedule"])

    def test_001_eur_contract_value_not_used_as_risk_premium_or_tiv(self):
        self.assertFalse(self.r["award_september"]
                         ["public_001_eur_contract_value_is_usable_premium_or_tiv"])


if __name__ == "__main__":
    unittest.main()
