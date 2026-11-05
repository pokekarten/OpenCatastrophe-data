# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed static provenance for published WBM quota *labels*, not model shares."""
from __future__ import annotations

import re
import tomllib
import unittest
from pathlib import Path

from research_runners import ted_wbm_2026_competition_original_preflight_v0 as earlier
from research_runners import ted_berlin_insurance_original_xml_preflight_v0 as award


RECEIPT = (
    Path(__file__).resolve().parents[1] / "research" / "observations" /
    "ted_wbm_2026_original_contract_share_labels_v0.toml"
)


class OriginalContractQuotaLabelRegisterTests(unittest.TestCase):
    def setUp(self):
        self.reg = tomllib.loads(RECEIPT.read_text(encoding="utf-8"))

    def test_both_source_pins_match_independent_readers(self):
        x = self.reg
        self.assertEqual(x["source_award_original_sha256"],
                         award.SOURCES["668506-2026"]["original_xml_sha256_pinned"])
        self.assertEqual(x["source_award_original_bytes"],
                         award.SOURCES["668506-2026"]["original_xml_bytes_pinned"])
        self.assertEqual(x["source_competition_original_sha256"], earlier.PINNED_ORIGINAL_SHA256)
        self.assertEqual(x["source_competition_original_bytes"], earlier.PINNED_ORIGINAL_BYTES)

    def test_two_distinct_official_notice_ids(self):
        self.assertEqual(self.reg["source_award_notice"], "668506-2026")
        self.assertEqual(self.reg["source_competition_notice"], "286307-2026")
        self.assertEqual(self.reg["original_technical_procurement_lot_id"], "LOT-0000")

    def test_exact_three_hdi_helvetia_rv_tender_and_business_labels(self):
        rows = self.reg["contract_identifier_labels"]
        self.assertEqual([(r["settled_contract_id"], r["winning_tender_id"],
                           r["winning_organization_name"], r["percentage_in_identifier"])
                          for r in rows], [
            ("CON-0001", "TEN-0001", "HDI Global SE", 50),
            ("CON-0002", "TEN-0002",
             "Helvetia Schweizerische Versicherungsgesellschaft AG", 40),
            ("CON-0003", "TEN-0003", "R+V Allgemeine Versicherung AG", 10),
        ])
        self.assertEqual(len({r["winning_organization_id"] for r in rows}), 3)

    def test_no_legal_policy_share_from_100_percent_label_sum(self):
        nums = [int(x) for r in self.reg["contract_identifier_labels"]
                for x in re.findall(r"([0-9]{1,3})\s*%", r["original_Bt150_contract_identifier"])]
        self.assertEqual(nums, [50, 40, 10])
        self.assertEqual(sum(nums), self.reg["percent_label_numbers_sum"])
        self.assertFalse(self.reg["percent_labels_are_actual_signed_policy_participation_shares"])

    def test_tender_minimum_15_and_award_label_10_remain_unexplained(self):
        self.assertEqual(self.reg["competition_minimum"]
                         ["minimum_lead_offer_writing_percent_in_notice_text"], 30)
        self.assertEqual(self.reg["competition_minimum"]
                         ["minimum_participating_offer_writing_percent_in_notice_text"], 15)
        self.assertTrue(self.reg["unresolved"]
                        ["R_and_V_10_percent_label_below_15_percent_tender_minimum"])
        self.assertTrue(
            self.reg["competition_minimum"]["lead_offer_may_be_capped_at_50_if_cheaper_followers"])
        self.assertTrue(
            self.reg["competition_minimum"]["remaining_share_below_15_percent_may_be_awarded_to_follower"])
        self.assertTrue(
            self.reg["competition_minimum"]["rule_documented_in_original_competition_notice"])
        self.assertFalse(
            self.reg["competition_minimum"]["rv_actual_use_of_residual_exception_verified"])
        self.assertTrue(
            self.reg["unresolved"]["procurement_exemption_possible_but_application_not_proven"])
        self.assertFalse(
            self.reg["unresolved"]["specific_reason_for_rv_10_percent_allocation_verified"])

    def test_no_actual_exposure_tiv_or_retention_claim(self):
        for key in (
            "actual_per_insurer_insured_property_sites_verified",
            "actual_per_insurer_insured_sum_or_replacement_tiv_verified",
            "policy_terms_limits_deductibles_or_retention_verified",
            "signed_policy_currently_in_force_verified",
            "ceded_retention_or_NET_CAT_exposure_verified",
            "CAT_model_actual_insurer_exposure_admitted",
        ):
            with self.subTest(key=key):
                self.assertFalse(self.reg[key])
        self.assertFalse(
            self.reg["unresolved"]["insurer_share_weights_for_ACTUAL_CAT_portfolio_approved"])

    def test_requested_perils_are_not_actual_final_cover(self):
        perils = self.reg["requested_peril_markers"]
        for peril in ("storm", "hail", "flood", "earthquake", "fire"):
            self.assertTrue(perils[peril])
        self.assertFalse(perils["real_policy_peril_coverage_limits_verified"])

    def test_replacement_coordinates_and_raw_original_files_not_redistributed(self):
        self.assertEqual(self.reg["described_pure_commercial_property_count"], 9)
        self.assertFalse(self.reg["source_original_xml_bytes_committed"])

    def test_planned_contract_period_not_current_2026_in_force_proof(self):
        meta = self.reg["competition_minimum"]
        self.assertEqual(meta["planned_period_start"], "2027-01-01")
        self.assertEqual(meta["planned_period_end"], "2028-01-01")
        self.assertEqual(meta["planned_extension_count"], 7)
        self.assertFalse(meta["final_policy_terms_reflected_by_earlier_advertisement"])


if __name__ == "__main__":
    unittest.main()
