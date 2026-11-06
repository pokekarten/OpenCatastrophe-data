# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""The original regulator's Ciara 2020 note cannot become Daria 1990 loss."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
import eiopa_catastrophe_hub_2023_original_dossier_gate_v0 as gate


class EIOPAOriginalPublicationEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = tomllib.loads(gate.SOURCE.read_text(encoding="utf-8"))

    def test_authentic_publisher_metadata_has_no_unfetched_claim_data(self):
        report = gate.validate_evidence(self.original)
        self.assertEqual(report["public_original_publisher_attachments_named"], 3)
        self.assertTrue(report["wind_insured_loss_event_is_only_Ciara_2020"])
        self.assertTrue(report["original_loss_workbook_bytes_fetched_via_proxy"])
        self.assertTrue(report["original_exposure_workbook_complete_bytes_fetched"])
        self.assertTrue(report["original_exposure_workbook_sha256_verified"])
        self.assertFalse(report["original_exposure_OOXML_quarantine_passed"])
        self.assertEqual(
            report["original_exposure_workbook_sha256_from_official_TLS"],
            "f3ec03e25be247a798d94ea9d5ece8bd03a34bcc27b6faf99b597bbd863c3e79"
        )
        self.assertEqual(
            report["original_loss_workbook_sha256_from_source_proxy"],
            "201bef4a15dccf4cb56edfe80fd2327b9bcd51ce3d815befb0730ffec5394fd6"
        )
        for field in (
            "Daria_1990_insured_claims_provided",
            "German_insurer_site_loss_calibration_approved",
            "insured_GUL_IL_RI_OEP_AEP_model_executed",
        ):
            self.assertIs(report[field], False)

    def test_only_2020_ciara_not_daria_1990_or_other_nonwind_cat(self):
        for field, value in (
            ("insured_wind_claim_event", "DARIA_JANUARY_1990"),
            ("insured_wind_claim_event", "CIARA_AND_DARIA"),
            ("insurer_Daria_1990_claim_event_available", True),
            ("other_insured_claim_event_1", "WINDSTORM_DARIA_1990"),
            ("same_2020_wind_claim_event_and_1990_Daria_hazard", True),
        ):
            with self.subTest(field=field, value=value):
                doc = deepcopy(self.original)
                doc[field] = value
                with self.assertRaises(gate.EIOPAEvidenceBlocked):
                    gate.validate_evidence(doc)

    def test_insurer_sample_premium_coverage_not_policy_counts(self):
        cases = (
            ("sample_groups", 44),
            ("sample_solo_undertakings", 0),
            ("sample_EEA_2020_property_fire_GWP_coverage_numerator", "59PCT_ALL_BUILDINGS"),
            ("sample_Germany_2020_property_fire_GWP_coverage", "100PCT_NRW_RV_BOOK"),
            ("premium_share_can_be_treated_as_buildings_or_contracts_share", True),
            ("GWP_sample_covers_RV_geolocated_NRW_book", True),
            ("sample_is_100_percent_market", True),
        )
        for field, value in cases:
            with self.subTest(field=field):
                doc = deepcopy(self.original)
                doc[field] = value
                with self.assertRaises(gate.EIOPAEvidenceBlocked):
                    gate.validate_evidence(doc)

    def test_nuts2_anonymity_claims_and_coverage_scope_not_promotable(self):
        cases = (
            ("public_exposure_and_loss_resolution", "POSTCODE_OR_EXACT_NRW_SITE"),
            ("each_disclosed_data_point_minimum_independent_company_submissions", 1),
            ("residential_commercial_loss_split_always_available", True),
            ("original_exposure_resolution", "EXACT_GEOLOCATED_RV_HOMES"),
            ("building_sum_insured_basis", "GROSS_ACTUAL_RV_TIV"),
            ("direct_GUL_IL_RI_definition_usable_without_contract_terms", True),
        )
        for field, value in cases:
            with self.subTest(field=field):
                doc = deepcopy(self.original)
                doc[field] = value
                with self.assertRaises(gate.EIOPAEvidenceBlocked):
                    gate.validate_evidence(doc)

    def test_general_eiopa_copyright_cannot_promote_third_party_or_workbook_rights(self):
        cases = (
            ("publisher_general_reproduction_requires_credit", False),
            ("publisher_transformed_redistribution_requires_special_notice", False),
            ("publisher_third_party_rights_automatically_cleared", True),
            ("licence_workbook_specific_restrictions_checked", True),
            ("actual_eiopa_xlsx_bytes_obtained_in_this_research", False),
            ("historical_loss_workbook_sha256", "0"*64),
            ("exposure_workbook_sha256", "0"*64),
            ("exposure_OOXML_security_quarantine_passed", True),
        )
        for field, value in cases:
            with self.subTest(field=field):
                doc = deepcopy(self.original)
                doc[field] = value
                with self.assertRaises(gate.EIOPAEvidenceBlocked):
                    gate.validate_evidence(doc)

    def test_three_original_attachment_urls_and_digest_claims_fail_closed(self):
        for field, value in (
            ("original_url", "https://thirdparty.example/claims.xlsx"),
            ("source_sha256", "a"*64),
            ("publisher_size_label", "12.5 GB"),
            ("page", 99),
            ("id", "FAKE_RV_INSURER_CLAIMS_1990"),
        ):
            doc = deepcopy(self.original)
            doc["original_attachments"][1][field] = value
            with self.subTest(field=field):
                with self.assertRaises(gate.EIOPAEvidenceBlocked):
                    gate.validate_evidence(doc)
        for mutate in (
            lambda x: x["original_attachments"].pop(),
            lambda x: x["original_attachments"].append(deepcopy(x["original_attachments"][0])),
            lambda x: x.update({"Daria_1990_loss_in_eur": 900000}),
        ):
            doc = deepcopy(self.original)
            mutate(doc)
            with self.assertRaises(gate.EIOPAEvidenceBlocked):
                gate.validate_evidence(doc)

    def test_source_vintage_and_no_ep_admission_cannot_change(self):
        for field, value in (
            ("insured_exposure_reference_date", "1990-01-25"),
            ("insurer_site_data_or_German_model_calibration_admitted", True),
            ("reinsurance_treaty_or_annual_frequency_verified", True),
            ("publication_date", "2026-11-06"),
            ("admission", "APPROVED_RV_GROSS_NET_OEP_AEP"),
            ("insured_exposure_perils", ["WINDSTORM", "FLOOD", "EARTHQUAKE"]),
        ):
            with self.subTest(field=field):
                doc = deepcopy(self.original)
                doc[field] = value
                with self.assertRaises(gate.EIOPAEvidenceBlocked):
                    gate.validate_evidence(doc)


if __name__ == "__main__":
    unittest.main()
