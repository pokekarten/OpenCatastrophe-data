# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No-network evidence-scope guards for TED WBM search index award candidates."""
from __future__ import annotations

import hashlib
import json
import unittest

from research_runners import ted_berlin_insurance_search_api_preflight_v0 as api
from research_runners import ted_wbm_contract_search_index_candidates_v0 as m


def fixture(*, fields=None, notice=m.NOTICE, buyer=None, title=None):
    row = {
        "publication-number": notice,
        "buyer-name": {"de": [buyer or "WBM Wohnungsbaugesellschaft Berlin-Mitte mbH"]},
        "notice-title": {"de": title or "Industrielle Sachversicherung für reine Gewerbeobjekte"},
        "publication-date": "2026-09-29",
    }
    if fields is None:
        row.update({
            "winner-name": {
                "de": ["HDI Global SE", "R+V Allgemeine Versicherung AG",
                       "Helvetia Schweizerische Versicherungsgesellschaft AG"],
                "en": ["R+V Allgemeine Versicherung AG"],
            },
            "winner-identifier": ["ID-for-some-bidder"],
            "winner-selection-status": ["selec-w"],
            "contract-identifier": ["2026-WBM-CO-1"],
            "contract-tender-id": ["TEN-0001"],
            "contract-conclusion-date": ["2026-09-21"],
            "winner-decision-date": ["2026-09-21"],
        })
    else:
        row.update(fields)
    return json.dumps({"totalNoticeCount": 1, "notices": [row]},
                      ensure_ascii=False).encode("utf-8")


class WBMSearchIndexCandidateTests(unittest.TestCase):
    def test_official_query_field_list_is_exact_and_research_only(self):
        query = json.loads(api.query_body(
            m.NOTICE, fields=api.WBM_AWARD_CANDIDATE_FIELDS))
        self.assertEqual(query["query"], "publication-number = 668506-2026")
        self.assertEqual(query["limit"], 2)
        self.assertEqual(query["fields"][-7:], list(m.FIELDS))
        self.assertFalse(query["checkQuerySyntax"])
        self.assertFalse(query["onlyLatestVersions"])

    def test_unapproved_field_selection_blocks(self):
        with self.assertRaisesRegex(ValueError, "UNAPPROVED_FIELD_SELECTION"):
            api.query_body(m.NOTICE, fields=("winner-name",))

    def test_no_award_fields_on_2024_competition(self):
        with self.assertRaisesRegex(ValueError, "AWARD_FIELDS_NOT_ALLOWED_FOR_TENDER"):
            api.query_body("558592-2024",
                           fields=api.WBM_AWARD_CANDIDATE_FIELDS)

    def test_primary_wbm_publisher_api_candidate_labels(self):
        raw = fixture()
        output = m.inspect_wbm(raw)
        self.assertEqual(output["official_metadata_json_sha256"],
                         hashlib.sha256(raw).hexdigest())
        self.assertEqual(len(output["indexed_winner_candidate_labels"]), 3)
        self.assertTrue(output["indexed_winner_labels_exactly_match_known_secondary_labels"])
        self.assertEqual(output["indexed_contract_tender_references_unpaired"], ["TEN-0001"])
        self.assertEqual(output["indexed_lot_winner_status_codes_unpaired"], ["selec-w"])
        for forbidden in (
            "source_api_index_fields_prove_contract_to_company_join",
            "original_ubl_eforms_settled_contract_edges_verified",
            "individual_insurer_policy_or_coverage_share_verified",
            "individual_insured_building_location_tiv_or_perils_verified",
            "admitted_to_company_specific_CAT_model_exposure",
            "source_api_response_raw_body_logged_or_committed",
        ):
            self.assertFalse(output[forbidden])

    def test_multilanguage_winners_deduplicate_without_guessing_shares(self):
        fields = {
            "winner-name": {"de": ["R+V Allgemeine Versicherung AG"],
                            "en": ["R+V Allgemeine Versicherung AG"]},
            "contract-tender-id": ["TEN-0003", "TEN-0001"],
        }
        r = m.inspect_wbm(fixture(fields=fields))
        self.assertEqual(r["indexed_winner_candidate_labels"],
                         ["R+V Allgemeine Versicherung AG"])
        self.assertEqual(r["indexed_contract_tender_references_unpaired"],
                         ["TEN-0001", "TEN-0003"])
        self.assertFalse(r["source_api_index_fields_prove_contract_to_company_join"])

    def test_received_loser_name_in_index_not_promoted_to_winner(self):
        r = m.inspect_wbm(fixture(fields={
            "winner-name": ["HDI Global SE", "Fictional underbid insurer"],
            "winner-selection-status": "selec-w",
            "contract-tender-id": ["TEN-0001"],
        }))
        self.assertIn("Fictional underbid insurer", r["indexed_winner_candidate_labels"])
        self.assertFalse(r["indexed_winner_labels_exactly_match_known_secondary_labels"])
        self.assertTrue(r["source_api_winner_label_may_contain_nonwinning_received_bidders"])
        self.assertFalse(r["original_ubl_eforms_settled_contract_edges_verified"])

    def test_missing_optional_fields_does_not_invent_zero_contracts(self):
        r = m.inspect_wbm(fixture(fields={}))
        self.assertFalse(r["indexed_winner_labels_present"])
        self.assertEqual(r["indexed_contract_identifier_count"], 0)
        self.assertFalse(r["individual_insurer_policy_or_coverage_share_verified"])

    def test_wrong_publication_id_blocked(self):
        with self.assertRaisesRegex(ValueError, "WRONG_PUBLICATION"):
            m.inspect_wbm(fixture(notice="000123-2026"))

    def test_wbm_buyer_required(self):
        with self.assertRaisesRegex(ValueError, "BUYER_MISMATCH"):
            m.inspect_wbm(fixture(buyer="Unrelated public buyer"))

    def test_product_title_required(self):
        with self.assertRaisesRegex(ValueError, "PRODUCT_MISMATCH"):
            m.inspect_wbm(fixture(title="Unrelated construction materials"))

    def test_unexpected_contract_tender_reference_refused(self):
        with self.assertRaisesRegex(ValueError, "UNEXPECTED_CONTRACT_TENDER_ID_SHAPE"):
            m.inspect_wbm(fixture(fields={"contract-tender-id": ["OTHER-0001"]}))

    def test_invalid_winner_status_not_silently_treated_as_award(self):
        with self.assertRaisesRegex(ValueError, "UNEXPECTED_LOT_STATUS"):
            m.inspect_wbm(fixture(fields={"winner-selection-status": ["maybe-winner"]}))

    def test_oversized_winner_name_refused(self):
        with self.assertRaisesRegex(ValueError, "INVALID_TEXT_VALUE"):
            m.inspect_wbm(fixture(fields={"winner-name": ["A" * 305]}))

    def test_unbounded_candidate_array_refused(self):
        with self.assertRaisesRegex(ValueError, "UNBOUNDED_FIELD_ARRAY"):
            m.inspect_wbm(fixture(fields={"winner-name": ["Carrier "+str(i) for i in range(25)]}))

    def test_excessive_nested_language_map_refused(self):
        x = "small"
        for i in range(6):
            x = {"de": x}
        with self.assertRaisesRegex(ValueError, "EXCESSIVE_NESTING"):
            m.inspect_wbm(fixture(fields={"winner-name": x}))

    def test_numeric_company_name_refused(self):
        with self.assertRaisesRegex(ValueError, "WRONG_FIELD_TYPE"):
            m.inspect_wbm(fixture(fields={"winner-name": [12345]}))

    def test_source_payload_duplicate_json_key_rejected(self):
        raw = fixture()
        duplicate = raw.replace(b'"notices":', b'"notices":[],"notices":', 1)
        with self.assertRaisesRegex(ValueError, "DUPLICATE_JSON_KEY"):
            m.inspect_wbm(duplicate)

    def test_no_synthetic_company_attribution_from_contract_ids(self):
        r = m.inspect_wbm(fixture(fields={
            "winner-name": ["HDI Global SE", "R+V Allgemeine Versicherung AG"],
            "contract-tender-id": ["TEN-0001", "TEN-0002"],
            "contract-identifier": ["CON-A", "CON-B"],
        }))
        self.assertEqual(r["indexed_contract_identifier_count"], 2)
        self.assertEqual(len(r["indexed_contract_tender_references_unpaired"]), 2)
        self.assertNotIn("insurer_to_contract_pairs", r)
        self.assertNotIn("insurer_to_object_pairs", r)
        self.assertFalse(r["admitted_to_company_specific_CAT_model_exposure"])


if __name__ == "__main__":
    unittest.main()
