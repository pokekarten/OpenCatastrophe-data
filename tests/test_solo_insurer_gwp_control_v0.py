# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests: NO issuer PDF, company premium or source text in Git."""

from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research_runners"))

from solo_insurer_gwp_control_v0 import GWPControlError, validate_solo_gwp


FAKE_PDF = b"%PDF-1.4\nsynthetic-no-real-publisher-data\n%%EOF\n"


def fixture():
    return {
        "schema_version": "0.1.0",
        "input_class": "research_only_manual_transcription",
        "reporting_date": "2025-12-31",
        "issuer_key": "FAKE_CARRIER",
        "premium_measure": "gross_written_premium",
        "country_location_evidence": "not_proven_by_this_report",
        "source": {
            "issuer_report_url": "https://example.org/example-annual-report.pdf",
            "original_pdf_sha256": hashlib.sha256(FAKE_PDF).hexdigest(),
            "pdf_page_zero_based": 9,
            "reporting_basis": "local_statutory_gaap",
            "legal_entity_scope": "solo",
            "currency": "EUR",
            "amount_unit": "thousand_eur",
        },
        "direct_lob_rows": [
            {"lob_code": "FAKE_PROPERTY", "gross_written": "40.00"},
            {"lob_code": "FAKE_MOTOR", "gross_written": "60.00"}
        ],
        "reported_direct_total": "100.00",
        "reported_assumed_total": "7.00",
        "reported_combined_total": "107.00",
    }


class SoloGWPControlTests(unittest.TestCase):
    def test_happy_path_is_local_arithmetic_only(self):
        result = validate_solo_gwp(fixture(), FAKE_PDF)
        self.assertTrue(result["line_and_direct_assumed_totals_conserved"])
        self.assertTrue(result["source_fingerprint_matches_local_pdf"])
        self.assertEqual(result["lob_row_count"], 2)
        for flag in (
            "extraction_verified_against_pdf_visuals",
            "original_issuer_authenticity_independently_verified",
            "rights_and_scientific_review_complete",
            "reported_country_by_lob_observed",
            "geolocated_insured_assets_observed",
            "insurance_tiv_observed",
            "underwriting_risk_bearer_net_position_observed",
            "model_input_approved",
        ):
            self.assertFalse(result[flag], flag)

    def test_repeatability(self):
        self.assertEqual(validate_solo_gwp(fixture(), FAKE_PDF),
                         validate_solo_gwp(fixture(), FAKE_PDF))

    def test_direct_reconciliation_mismatch(self):
        s = fixture()
        s["direct_lob_rows"][0]["gross_written"] = "39.99"
        with self.assertRaisesRegex(GWPControlError, "do not sum"):
            validate_solo_gwp(s, FAKE_PDF)

    def test_assumed_premium_not_silently_counted_twice(self):
        s = fixture()
        s["reported_combined_total"] = "100.00"
        with self.assertRaisesRegex(GWPControlError, "separately assumed"):
            validate_solo_gwp(s, FAKE_PDF)

    def test_missing_lob_row_fails_closed(self):
        s = fixture()
        s["direct_lob_rows"].pop()
        with self.assertRaisesRegex(GWPControlError, "direct LoB"):
            validate_solo_gwp(s, FAKE_PDF)

    def test_duplicate_lob_fails_closed(self):
        s = fixture()
        s["direct_lob_rows"][1]["lob_code"] = "FAKE_PROPERTY"
        with self.assertRaisesRegex(GWPControlError, "duplicate"):
            validate_solo_gwp(s, FAKE_PDF)

    def test_negative_missing_precision_or_non_numeric_rejected(self):
        for value in ("-1", "", None, 100, True, "1,000", "0.001", "NaN", "1e3"):
            with self.subTest(value=value):
                s = fixture()
                s["direct_lob_rows"][0]["gross_written"] = value
                with self.assertRaises(GWPControlError):
                    validate_solo_gwp(s, FAKE_PDF)

    def test_absence_of_country_report_must_remain_explicit(self):
        s = fixture()
        s["country_location_evidence"] = "DE"
        with self.assertRaisesRegex(GWPControlError, "risk situs"):
            validate_solo_gwp(s, FAKE_PDF)

    def test_fails_closed_on_earned_or_net_metric(self):
        for basis in ("net_earned_premium", "gross_earned_premium", "incurred_claim"):
            with self.subTest(basis=basis):
                s = fixture()
                s["premium_measure"] = basis
                with self.assertRaisesRegex(GWPControlError, "written"):
                    validate_solo_gwp(s, FAKE_PDF)

    def test_group_cannot_pass_solo_report(self):
        s = fixture()
        s["source"]["legal_entity_scope"] = "group"
        with self.assertRaisesRegex(GWPControlError, "group and solo"):
            validate_solo_gwp(s, FAKE_PDF)

    def test_ifrs_cannot_pass_local_statutory_basis(self):
        s = fixture()
        s["source"]["reporting_basis"] = "ifrs17"
        with self.assertRaisesRegex(GWPControlError, "Solvency II/IFRS"):
            validate_solo_gwp(s, FAKE_PDF)

    def test_wrong_currency_unit_and_non_calendar_year_rejected(self):
        for key, wrong in (("currency", "USD"), ("amount_unit", "euros")):
            s = fixture()
            s["source"][key] = wrong
            with self.assertRaisesRegex(GWPControlError, "EUR thousands"):
                validate_solo_gwp(s, FAKE_PDF)
        s = fixture()
        s["reporting_date"] = "2025-06-30"
        with self.assertRaisesRegex(GWPControlError, "December 31"):
            validate_solo_gwp(s, FAKE_PDF)

    def test_source_digest_mismatch_rejected(self):
        s = fixture()
        s["source"]["original_pdf_sha256"] = "0" * 64
        with self.assertRaisesRegex(GWPControlError, "digest"):
            validate_solo_gwp(s, FAKE_PDF)

    def test_missing_or_nonsensical_pdf_rejected(self):
        for bad in (b"", b"random", b"%PDF-1.4\nmissing-trailer"):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(GWPControlError, "PDF"):
                    validate_solo_gwp(fixture(), bad)

    def test_https_public_url_and_no_credentials(self):
        for url in ("http://example.org/x.pdf", "https://localhost/r.pdf",
                    "https://example.org/x?token=secret", "https://127.0.0.1/x"):
            with self.subTest(url=url):
                s = fixture()
                s["source"]["issuer_report_url"] = url
                with self.assertRaisesRegex(GWPControlError, "URL"):
                    validate_solo_gwp(s, FAKE_PDF)

    def test_wrong_page_missing_provenance_or_schema(self):
        s = fixture()
        s["source"]["pdf_page_zero_based"] = True
        with self.assertRaisesRegex(GWPControlError, "page"):
            validate_solo_gwp(s, FAKE_PDF)
        s = fixture()
        del s["source"]["original_pdf_sha256"]
        with self.assertRaisesRegex(GWPControlError, "identity"):
            validate_solo_gwp(s, FAKE_PDF)
        s = fixture()
        s["source"]["license_approved"] = True
        with self.assertRaisesRegex(GWPControlError, "identity"):
            validate_solo_gwp(s, FAKE_PDF)

    def test_hypothetical_reduction_of_grouped_values_is_not_permitted(self):
        s = fixture()
        s["direct_lob_rows"][0]["gross_written"] = "140.00"
        s["reported_direct_total"] = "200.00"
        s["reported_combined_total"] = "207.00"
        result = validate_solo_gwp(s, FAKE_PDF)
        self.assertFalse(result["reported_country_by_lob_observed"])
        self.assertFalse(result["model_input_approved"])


if __name__ == "__main__":
    unittest.main()
