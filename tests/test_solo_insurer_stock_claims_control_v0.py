# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Entirely invented premium/contract/claim tables, never real insurer rows."""

from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research_runners"))
from solo_insurer_gwp_control_v0 import GWPControlError
from solo_insurer_stock_claims_control_v0 import validate_solo_stock_claims


FAKE_PDF = b"%PDF-1.4\nindependently invented PDF-like test bytes\n%%EOF\n"


def fixtures():
    gwp = {
        "schema_version": "0.1.0",
        "input_class": "research_only_manual_transcription",
        "reporting_date": "2025-12-31",
        "issuer_key": "FICT_CARRIER",
        "premium_measure": "gross_written_premium",
        "country_location_evidence": "not_proven_by_this_report",
        "source": {
            "issuer_report_url": "https://example.org/fictional-local-report.pdf",
            "original_pdf_sha256": hashlib.sha256(FAKE_PDF).hexdigest(),
            "pdf_page_zero_based": 9, "reporting_basis": "local_statutory_gaap",
            "legal_entity_scope": "solo", "currency": "EUR", "amount_unit": "thousand_eur",
        },
        "direct_lob_rows": [
            {"lob_code": "FAKE_FIRE", "gross_written": "10.00"},
            {"lob_code": "FAKE_CONTENTS", "gross_written": "90.00"},
            {"lob_code": "FAKE_BUILDING", "gross_written": "200.00"},
            {"lob_code": "FAKE_OTHER_PROPERTY", "gross_written": "50.00"},
            {"lob_code": "FAKE_MOTOR", "gross_written": "100.00"},
        ],
        "reported_direct_total": "450.00",
        "reported_assumed_total": "10.00",
        "reported_combined_total": "460.00",
    }
    stock = {
        "schema_version": "0.1.0",
        "input_class": "research_only_manual_transcription",
        "issuer_key": "FICT_CARRIER",
        "reporting_date": "2025-12-31",
        "contract_population": "at_least_one_year_contracts_at_year_end",
        "claims_population": "all_reported_claims_for_reporting_year",
        "risk_situs_evidence": "not_observed",
        "stock_pdf_page_zero_based": 51,
        "lob_stock_rows": [
            {"lob_code": "FAKE_FIRE", "year_end_contracts": "10", "reported_claims": "1"},
            {"lob_code": "FAKE_CONTENTS", "year_end_contracts": "300", "reported_claims": "20"},
            {"lob_code": "FAKE_BUILDING", "year_end_contracts": "200", "reported_claims": "10"},
            {"lob_code": "FAKE_OTHER_PROPERTY", "year_end_contracts": "490", "reported_claims": "19"},
        ],
        "rollup_checks": [{
            "rollup_code": "FAKE_ALL_PROPERTY",
            "child_lob_codes": [
                "FAKE_FIRE", "FAKE_CONTENTS", "FAKE_BUILDING", "FAKE_OTHER_PROPERTY"
            ],
            "gross_written_thousand_eur": "350.00",
            "year_end_contracts": "1000",
            "reported_claims": "50",
        }],
    }
    return gwp, stock


class SoloStocksAndClaimsTests(unittest.TestCase):
    def test_three_independent_rollup_marginals_reconcile(self):
        g, s = fixtures()
        out = validate_solo_stock_claims(g, s, FAKE_PDF)
        self.assertEqual(out["matched_stock_lob_count"], 4)
        self.assertTrue(out["validated_rollups"][0]["three_independent_marginals_conserved"])
        self.assertFalse(out["actual_source_transcription_independently_verified"])
        self.assertFalse(out["model_input_approved"])
        self.assertFalse(out["cat_specific_claims_observed"])
        self.assertFalse(out["geolocated_insured_assets_observed"])
        self.assertFalse(out["tiv_from_premiums_observed"])
        self.assertTrue(out["source_fingerprint_matches_local_pdf"])

    def test_repeatable_order_and_reference_ratio_math(self):
        g, s = fixtures()
        out = validate_solo_stock_claims(g, s, FAKE_PDF)
        self.assertEqual(out, validate_solo_stock_claims(g, s, FAKE_PDF))
        vals = {x["lob_code"]: x for x in out["derived_reference_ratios"]}
        self.assertEqual(vals["FAKE_BUILDING"]["annual_written_eur_per_year_end_contract_reference"], "1000.00")
        self.assertEqual(vals["FAKE_BUILDING"]["reported_claims_per_year_end_contract_reference"], "0.050000")
        self.assertFalse(vals["FAKE_BUILDING"]["real_tariff_or_actuarial_frequency"])

    def test_premium_marginal_challenge_rejects_wrong_parent(self):
        g, s = fixtures()
        s["rollup_checks"][0]["gross_written_thousand_eur"] = "350.01"
        with self.assertRaisesRegex(GWPControlError, "premium subtotal mismatch"):
            validate_solo_stock_claims(g, s, FAKE_PDF)

    def test_stock_marginal_challenge_rejects_wrong_parent(self):
        g, s = fixtures()
        s["rollup_checks"][0]["year_end_contracts"] = "1001"
        with self.assertRaisesRegex(GWPControlError, "contract subtotal mismatch"):
            validate_solo_stock_claims(g, s, FAKE_PDF)

    def test_claim_marginal_challenge_rejects_wrong_parent(self):
        g, s = fixtures()
        s["rollup_checks"][0]["reported_claims"] = "51"
        with self.assertRaisesRegex(GWPControlError, "claim subtotal mismatch"):
            validate_solo_stock_claims(g, s, FAKE_PDF)

    def test_prohibits_atomic_premium_row_for_rollup_parent(self):
        g, s = fixtures()
        g["direct_lob_rows"].append(
            {"lob_code": "FAKE_ALL_PROPERTY", "gross_written": "350.00"})
        g["reported_direct_total"] = "800.00"
        g["reported_combined_total"] = "810.00"
        with self.assertRaisesRegex(GWPControlError, "subtotal counted as direct atomic"):
            validate_solo_stock_claims(g, s, FAKE_PDF)

    def test_unknown_lob_and_duplicate_stock_rows_rejected(self):
        g, s = fixtures()
        s["lob_stock_rows"][0]["lob_code"] = "FAKE_UNKNOWN"
        with self.assertRaisesRegex(GWPControlError, "unmatched"):
            validate_solo_stock_claims(g, s, FAKE_PDF)
        g, s = fixtures()
        s["lob_stock_rows"].append(deepcopy(s["lob_stock_rows"][0]))
        with self.assertRaisesRegex(GWPControlError, "duplicated"):
            validate_solo_stock_claims(g, s, FAKE_PDF)

    def test_rollup_duplicate_child_and_omitted_child_rejected(self):
        g, s = fixtures()
        s["rollup_checks"][0]["child_lob_codes"].append("FAKE_FIRE")
        with self.assertRaisesRegex(GWPControlError, "duplicate"):
            validate_solo_stock_claims(g, s, FAKE_PDF)
        g, s = fixtures()
        s["rollup_checks"][0]["child_lob_codes"] = ["FAKE_FIRE", "FAKE_MOTOR"]
        with self.assertRaisesRegex(GWPControlError, "without stock"):
            validate_solo_stock_claims(g, s, FAKE_PDF)

    def test_overlapping_parent_sets_cannot_duplicate_child(self):
        g, s = fixtures()
        second = deepcopy(s["rollup_checks"][0])
        second["rollup_code"] = "FAKE_OTHER_AGGREGATE"
        s["rollup_checks"].append(second)
        with self.assertRaisesRegex(GWPControlError, "overlapping"):
            validate_solo_stock_claims(g, s, FAKE_PDF)

    def test_invalid_claim_and_contract_counts_rejected(self):
        for bad in ("-1", None, False, 1, "1.5", "1,000", "NaN", "1e3"):
            with self.subTest(bad=bad):
                g, s = fixtures()
                s["lob_stock_rows"][0]["year_end_contracts"] = bad
                with self.assertRaises(GWPControlError):
                    validate_solo_stock_claims(g, s, FAKE_PDF)
                g, s = fixtures()
                s["lob_stock_rows"][0]["reported_claims"] = bad
                with self.assertRaises(GWPControlError):
                    validate_solo_stock_claims(g, s, FAKE_PDF)

    def test_valid_zero_stock_does_not_invent_tariff_or_frequency(self):
        g, s = fixtures()
        s["lob_stock_rows"][0]["year_end_contracts"] = "0"
        s["rollup_checks"][0]["year_end_contracts"] = "990"
        out = validate_solo_stock_claims(g, s, FAKE_PDF)
        fire = next(x for x in out["derived_reference_ratios"] if x["lob_code"] == "FAKE_FIRE")
        self.assertIsNone(fire["annual_written_eur_per_year_end_contract_reference"])
        self.assertIsNone(fire["reported_claims_per_year_end_contract_reference"])

    def test_multiple_claims_per_contract_are_possible(self):
        g, s = fixtures()
        s["lob_stock_rows"][0]["reported_claims"] = "20"
        s["rollup_checks"][0]["reported_claims"] = "69"
        out = validate_solo_stock_claims(g, s, FAKE_PDF)
        fire = next(x for x in out["derived_reference_ratios"] if x["lob_code"] == "FAKE_FIRE")
        self.assertEqual(fire["reported_claims_per_year_end_contract_reference"], "2.000000")
        self.assertFalse(fire["real_tariff_or_actuarial_frequency"])

    def test_no_country_or_cat_loss_promotion(self):
        g, s = fixtures()
        s["risk_situs_evidence"] = "DE_CONFIRMED_ALL"
        with self.assertRaisesRegex(GWPControlError, "not observed"):
            validate_solo_stock_claims(g, s, FAKE_PDF)
        g, s = fixtures()
        s["claims_population"] = "catastrophe_claims_only"
        with self.assertRaisesRegex(GWPControlError, "not CAT"):
            validate_solo_stock_claims(g, s, FAKE_PDF)

    def test_wrong_issuer_year_or_reporting_population(self):
        g, s = fixtures()
        s["issuer_key"] = "SOME_OTHER_COMPANY"
        with self.assertRaisesRegex(GWPControlError, "legal entity"):
            validate_solo_stock_claims(g, s, FAKE_PDF)
        g, s = fixtures()
        s["reporting_date"] = "2024-12-31"
        with self.assertRaisesRegex(GWPControlError, "reporting period"):
            validate_solo_stock_claims(g, s, FAKE_PDF)
        g, s = fixtures()
        s["contract_population"] = "unique_residential_buildings"
        with self.assertRaisesRegex(GWPControlError, "contract population"):
            validate_solo_stock_claims(g, s, FAKE_PDF)

    def test_reject_wrong_pdf_or_page_confusion(self):
        g, s = fixtures()
        with self.assertRaisesRegex(GWPControlError, "digest"):
            validate_solo_stock_claims(g, s, FAKE_PDF + b"x")
        g, s = fixtures()
        s["stock_pdf_page_zero_based"] = 9
        with self.assertRaisesRegex(GWPControlError, "separately identified"):
            validate_solo_stock_claims(g, s, FAKE_PDF)
        g, s = fixtures()
        s["stock_pdf_page_zero_based"] = True
        with self.assertRaisesRegex(GWPControlError, "zero-based"):
            validate_solo_stock_claims(g, s, FAKE_PDF)

    def test_schema_rejects_extra_authority_field(self):
        g, s = fixtures()
        s["rights_approved"] = True
        with self.assertRaisesRegex(GWPControlError, "schema"):
            validate_solo_stock_claims(g, s, FAKE_PDF)

    def test_empty_rollups_are_nonadmitted_partial_observations(self):
        g, s = fixtures()
        s["rollup_checks"] = []
        out = validate_solo_stock_claims(g, s, FAKE_PDF)
        self.assertEqual(out["validated_rollups"], [])
        self.assertFalse(out["model_input_approved"])


if __name__ == "__main__":
    unittest.main()
