# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline tamper tests for recorded three-contract official WBM award graph."""
from __future__ import annotations

import copy
import tomllib
import unittest

from research_runners import ted_wbm_original_award_graph_receipt_v0 as m
from research_runners import ted_wbm_eforms_winner_role_v0 as role


def receipt():
    return tomllib.loads(m.REGISTER.read_text(encoding="utf-8"))


def report_from_recorded_source(reg):
    awards = []
    for x in reg["contract_awards"]:
        row = {k: x[k] for k in m.FIELDS}
        row["winning_party_member_organizations"] = [{
            "xml_organization_id": x["winning_organization_id"],
            "source_company_name": x["winning_organization_source_name"],
        }]
        row.update({
            "this_group_documents_insured_object_allocations": False,
            "this_group_documents_coinsurance_percentages": False,
            "this_group_documents_reinsurance_or_net_retention": False,
            "contract_signatories_are_automatically_winning_underwriters": False,
        })
        awards.append(row)
    return {
        "schema_version": role.REPORT_SCOPE,
        "notice": role.NOTICE,
        "official_xml_sha256": reg["source_original_xml_sha256"],
        "official_original_xml_url": reg["official_original_xml_url"],
        "exact_original_xml_sha256_and_bytes_pin_matched_this_execution": True,
        "actual_award_buyer_original_organization_name": reg["buyer_source_name"],
        "winner_lot_result_count": 3,
        "settled_contracts_linked_to_winning_results": 3,
        "winning_result_contract_tender_links": 3,
        "won_tenders_selected_by_settled_contract_not_received_tender_list": True,
        "source_winner_names_exactly_match_secondary_mirror_names": True,
        "claimed_carrier_insured_buildings": False,
        "known_insurance_contract_coin_shares": False,
        "known_peril_sublimits_deductibles_or_tiv": False,
        "actual_carrier_by_location_CAT_exposures_admitted": False,
        "award_role_paths": awards,
    }


class WBMOriginalOfficialAwardGraphReceiptTests(unittest.TestCase):
    def setUp(self):
        self.reg = receipt()
        self.report = report_from_recorded_source(self.reg)

    def test_official_record_conserves_three_exact_distinct_awards(self):
        r = m.validate(self.report, register=self.reg)
        self.assertEqual(r["verified_settled_contract_to_tender_to_source_company_edges"], 3)
        self.assertTrue(r["named_awardees_are_official_original_eforms_contract_linked"])
        self.assertFalse(r["source_verified_insured_risk_locations_or_tiv"])
        self.assertEqual([x["settled_contract_id"] for x in self.reg["contract_awards"]],
                         ["CON-0001", "CON-0002", "CON-0003"])
        self.assertEqual([x["lot_id"] for x in self.reg["contract_awards"]],
                         ["LOT-0000"] * 3)

    def test_recorded_original_sha_or_byte_count_tamper_refused(self):
        for key, value in (
            ("source_original_xml_sha256", "0" * 64),
            ("source_original_xml_bytes", 12345),
        ):
            with self.subTest(key=key):
                tampered = copy.deepcopy(self.reg)
                tampered[key] = value
                with self.assertRaisesRegex(ValueError, "SOURCE_RECEIPT_MISMATCH"):
                    m.validate(self.report, register=tampered)

    def test_later_unpinned_xml_cannot_be_a_verified_source(self):
        changed = copy.deepcopy(self.report)
        changed["exact_original_xml_sha256_and_bytes_pin_matched_this_execution"] = False
        with self.assertRaisesRegex(ValueError, "LIVE_GRAPH_NOT_VERIFIED"):
            m.validate(changed, register=self.reg)

    def test_source_winner_to_contract_company_relabel_blocked(self):
        changed = copy.deepcopy(self.report)
        changed["award_role_paths"][0]["winning_party_member_organizations"][0][
            "source_company_name"] = "Another company"
        with self.assertRaisesRegex(ValueError, "WINNER_TO_CONTRACT_EDGE_DRIFT"):
            m.validate(changed, register=self.reg)

    def test_source_winner_org_reference_relabel_blocked(self):
        changed = copy.deepcopy(self.report)
        changed["award_role_paths"][0]["winning_party_member_organizations"][0][
            "xml_organization_id"] = "ORG-8888"
        with self.assertRaisesRegex(ValueError, "WINNER_TO_CONTRACT_EDGE_DRIFT"):
            m.validate(changed, register=self.reg)

    def test_source_contract_to_tender_edge_swap_blocked(self):
        changed = copy.deepcopy(self.report)
        changed["award_role_paths"][1]["winning_tender_id"] = "TEN-0001"
        with self.assertRaisesRegex(ValueError, "RESULT_TENDER_LOT_DRIFT"):
            m.validate(changed, register=self.reg)

    def test_source_result_to_contract_swap_blocked(self):
        changed = copy.deepcopy(self.report)
        changed["award_role_paths"][1]["settled_contract_id"] = "CON-0001"
        with self.assertRaisesRegex(ValueError, "DUPLICATE_ACTUAL_CONTRACT"):
            m.validate(changed, register=self.reg)

    def test_missing_or_extra_award_is_not_considered_complete(self):
        changed = copy.deepcopy(self.report)
        changed["award_role_paths"].pop()
        with self.assertRaisesRegex(ValueError, "EXPECTED_THREE_EXACT_CONTRACTS"):
            m.validate(changed, register=self.reg)

    def test_multiple_organizations_are_not_automatically_a_single_awardee(self):
        changed = copy.deepcopy(self.report)
        changed["award_role_paths"][0]["winning_party_member_organizations"].append(
            {"xml_organization_id": "ORG-8888", "source_company_name": "Extra company"})
        with self.assertRaisesRegex(ValueError, "WINNING_PARTY_MEMBERSHIP_DRIFT"):
            m.validate(changed, register=self.reg)

    def test_three_contracts_same_lot_are_not_three_disjoint_risks(self):
        self.assertEqual(self.reg["all_awards_share_technical_lot_id"], "LOT-0000")
        self.assertFalse(self.reg["real_insured_building_identifiers_or_coordinates_observed"])
        self.assertFalse(self.reg["per_company_coinsurance_percentage_observed"])
        self.assertFalse(self.reg["premium_policy_limit_deductible_or_reinstatement_tiv_observed"])

    def test_false_carrier_site_count_admission_blocked(self):
        changed = copy.deepcopy(self.report)
        changed["claimed_carrier_insured_buildings"] = True
        with self.assertRaisesRegex(ValueError, "REAL_EXPOSURE_CLAIM_FORBIDDEN"):
            m.validate(changed, register=self.reg)

    def test_actual_company_coinsurance_share_flag_refused(self):
        changed = copy.deepcopy(self.reg)
        changed["per_company_coinsurance_percentage_observed"] = True
        with self.assertRaisesRegex(ValueError, "MODEL_ADMISSION_FORBIDDEN"):
            m.validate(self.report, register=changed)

    def test_real_policy_effective_date_claim_refused(self):
        changed = copy.deepcopy(self.reg)
        changed["current_signed_policy_coverage_and_effective_dates_verified"] = True
        with self.assertRaisesRegex(ValueError, "MODEL_ADMISSION_FORBIDDEN"):
            m.validate(self.report, register=changed)

    def test_signatory_is_not_a_winning_underwriter(self):
        changed = copy.deepcopy(self.report)
        changed["award_role_paths"][0][
            "contract_signatories_are_automatically_winning_underwriters"] = True
        with self.assertRaisesRegex(ValueError, "SIGNATORY_IS_NOT_UNDERWRITER_PROOF"):
            m.validate(changed, register=self.reg)

    def test_wrong_original_publisher_document_id_blocked(self):
        changed = copy.deepcopy(self.reg)
        changed["notice_publication_number"] = "558592-2024"
        with self.assertRaisesRegex(ValueError, "SOURCE_RECEIPT_MISMATCH"):
            m.validate(self.report, register=changed)

    def test_duplicate_recorded_contract_is_rejected(self):
        changed = copy.deepcopy(self.reg)
        changed["contract_awards"][1]["settled_contract_id"] = "CON-0001"
        with self.assertRaisesRegex(ValueError, "DUPLICATE_REGISTERED_CONTRACT"):
            m.validate(self.report, register=changed)


if __name__ == "__main__":
    unittest.main()
