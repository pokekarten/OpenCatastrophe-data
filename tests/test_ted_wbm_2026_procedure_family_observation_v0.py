# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Recorded TED WBM two single-notice procedure families remain separate."""
from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

from research_runners import ted_wbm_2026_procedure_family_discovery_v0 as m

DATA = (
    Path(__file__).resolve().parents[1] / "research" / "observations" /
    "ted_wbm_2026_bt04_procedure_family_members_v0.toml"
)


class ProcedureFamilyObservationTests(unittest.TestCase):
    def setUp(self):
        self.r = tomllib.loads(DATA.read_text(encoding="utf-8"))
        self.ids = m.known_procedures()

    def test_source_is_the_official_index_not_original_xml(self):
        self.assertEqual(self.r["official_source"], m.api.ENDPOINT)
        self.assertEqual(self.r["github_actions_run_id"], 42107358126)
        self.assertFalse(self.r["source_index_is_original_eforms_xml"])
        self.assertFalse(self.r["complete_original_xml_replayed_for_this_family_comparison"])

    def test_both_families_only_contain_their_anchor_as_of_observation(self):
        for role, key, anchor in (
            ("competition", "april_competition_family", "286307-2026"),
            ("award", "september_award_family", "668506-2026"),
        ):
            with self.subTest(role=role):
                row = self.r[key]
                self.assertEqual(row["BT04"], self.ids[role])
                self.assertEqual(row["indexed_notice_count"], 1)
                self.assertEqual(row["indexed_notice_numbers"], [anchor])
                self.assertEqual(row["known_notice_number"], anchor)
        self.assertTrue(self.r["publisher_index_contains_only_anchor_notice_for_each_family"])

    def test_original_api_response_receipts_have_bounded_bytes_and_sha(self):
        for key in ("april_competition_family", "september_award_family"):
            self.assertEqual(self.r[key]["official_search_api_json_bytes"], 7165)
            self.assertEqual(len(self.r[key]["official_search_api_json_sha256"]), 64)

    def test_no_siblings_indexed_does_not_prove_nonexistence(self):
        self.assertFalse(self.r["absence_of_indexed_siblings_proves_no_other_legal_notices"])
        self.assertFalse(self.r["absence_of_indexed_siblings_proves_no_private_procurement_documents"])

    def test_april_conditions_not_proven_applicable_to_september(self):
        self.assertFalse(self.r["april_15_percent_minimum_governs_september_award_verified"])

    def test_index_has_no_verified_coinsurance_policy_or_real_property_sites(self):
        self.assertFalse(self.r["signed_50_40_10_coinsurance_or_risk_locations_verified"])
        self.assertFalse(self.r["actual_insured_CAT_exposure_admitted"])

    def test_distinct_BT04_families_do_not_get_collapsed(self):
        self.assertNotEqual(self.r["april_competition_family"]["BT04"],
                            self.r["september_award_family"]["BT04"])
        self.assertNotEqual(self.r["april_competition_family"]["indexed_notice_numbers"],
                            self.r["september_award_family"]["indexed_notice_numbers"])


if __name__ == "__main__":
    unittest.main()
