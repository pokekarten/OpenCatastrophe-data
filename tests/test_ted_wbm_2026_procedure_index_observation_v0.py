# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source register invariants: WBM indexed procedure ID mismatch != legal merge."""
from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

from research_runners import ted_wbm_2026_procedure_search_index_v0 as search
from research_runners import ted_wbm_2026_competition_original_preflight_v0 as comp
from research_runners import ted_berlin_insurance_original_xml_preflight_v0 as orig

RECEIPT = (
    Path(__file__).resolve().parents[1] / "research" / "observations" /
    "ted_wbm_2026_search_bt04_lineage_observation_v0.toml"
)
QUOTA = (
    Path(__file__).resolve().parents[1] / "research" / "observations" /
    "ted_wbm_2026_original_contract_share_labels_v0.toml"
)


class WBMOfficialIndexProcedureObservationTests(unittest.TestCase):
    def setUp(self):
        self.r = tomllib.loads(RECEIPT.read_text(encoding="utf-8"))
        self.q = tomllib.loads(QUOTA.read_text(encoding="utf-8"))

    def test_official_source_exact_notices_and_two_distinct_bt04(self):
        c, a = self.r["competition"], self.r["award"]
        self.assertEqual(c["publication_number"], search.NOTICES[0])
        self.assertEqual(a["publication_number"], search.NOTICES[1])
        self.assertEqual(c["indexed_BT04_procedure_uuid"],
                         "7df98c35-4cae-41ff-8385-141125426a4a")
        self.assertEqual(a["indexed_BT04_procedure_uuid"],
                         "0988b2e4-9489-4b3b-9487-cd3a2a624cf5")
        self.assertNotEqual(c["indexed_BT04_procedure_uuid"],
                            a["indexed_BT04_procedure_uuid"])

    def test_index_original_sha_receipts_kept_separate(self):
        c, a = self.r["competition"], self.r["award"]
        self.assertEqual(c["original_xml_source_sha256_pinned_separately"],
                         comp.PINNED_ORIGINAL_SHA256)
        self.assertEqual(c["original_xml_source_bytes_pinned_separately"],
                         comp.PINNED_ORIGINAL_BYTES)
        self.assertEqual(a["original_xml_source_sha256_pinned_separately"],
                         orig.SOURCES["668506-2026"]["original_xml_sha256_pinned"])
        self.assertEqual(a["original_xml_source_bytes_pinned_separately"],
                         orig.SOURCES["668506-2026"]["original_xml_bytes_pinned"])
        self.assertEqual(len(c["official_api_response_sha256"]), 64)
        self.assertEqual(len(a["official_api_response_sha256"]), 64)
        self.assertEqual(c["official_api_response_bytes"], 7127)
        self.assertEqual(a["official_api_response_bytes"], 7127)

    def test_source_only_index_not_original_ubl(self):
        self.assertFalse(self.r["api_payload_is_original_eforms_xml"])
        self.assertFalse(self.r["exact_original_xml_pair_rechecked_this_run"])
        self.assertEqual(
            self.r["classification"], "INDEXED_DIFFERENT_BT04_REQUIRES_ORIGINAL_REPLAY")
        self.assertFalse(self.r["indexed_procedure_ids_identical"])

    def test_missing_index_previous_ref_does_not_prove_no_original_ref(self):
        self.assertFalse(self.r["award_index_has_explicit_reference_to_competition_286307"])
        self.assertFalse(self.r["missing_search_reference_proves_absence_in_original_xml"])

    def test_april_rules_not_bound_to_september_label_claim(self):
        self.assertFalse(self.r["april_tender_requirements_govern_september_award_proved"])
        self.assertFalse(self.q["unresolved"]
                         ["april_procurement_conditions_proved_to_govern_september_award"])
        self.assertFalse(self.q["unresolved"]
                         ["award_and_april_competition_bt04_search_index_match"])

    def test_no_actual_coin_share_or_CAT_model_admission(self):
        self.assertFalse(self.r["CAT_model_insured_portfolio_admitted"])
        self.assertFalse(
            self.r["company_specific_signed_coinsurance_shares_or_risk_properties_proved"])
        self.assertFalse(self.q["CAT_model_actual_insurer_exposure_admitted"])

    def test_read_only_record_not_reconciled_from_title(self):
        self.assertFalse(self.r["title_or_buyer_matching_proves_same_procurement"])
        self.assertFalse(self.q["unresolved"]
                         ["september_award_undisputed_link_to_april_contract_notice"])

    def test_official_index_source_and_dated_run(self):
        self.assertEqual(self.r["official_search_api"], search.api.ENDPOINT)
        self.assertEqual(self.r["source_github_actions_run_id"], 42104879468)
        self.assertEqual(self.r["retrieval_date"], "2026-11-05")


if __name__ == "__main__":
    unittest.main()
