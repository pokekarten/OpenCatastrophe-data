# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic metadata checks; no provider requests."""
import unittest

from research_runners.vigicrues_stage_bracket_v0 import StageReviewError, review_stage

STATION = "F700000103"


def candidate(stage, evidence="official_pdf_metadata", product="ZICH"):
    url = (f"https://www.vigicrues.gouv.fr/ftp/pdf/{product}_{STATION}_{stage}.pdf"
           if evidence == "official_pdf_metadata"
           else "https://example.org/official-retrospective-study")
    return {"station": STATION, "stage_mm": stage, "product": product,
            "evidence": evidence, "source_url": url}


class StageBracketTests(unittest.TestCase):
    def test_pdf_bracket_is_not_loss_input(self):
        r = review_stage(6098, STATION, [candidate(5660), candidate(7190)])
        self.assertEqual((r["lower_gap_mm"], r["upper_gap_mm"]), (438, 1092))
        self.assertTrue(r["pdf_metadata_bracket_exists"])
        self.assertFalse(r["depth_interpolation_permitted"])
        self.assertFalse(r["asset_inundation_or_loss_calibration_permitted"])

    def test_retrospective_6310_does_not_make_provider_pdf(self):
        r = review_stage(6098, STATION, [
            candidate(5660), candidate(6310, "historical_report_only"),
            candidate(7190)])
        self.assertEqual(r["upper_pdf_metadata_stage_mm"], 7190)
        self.assertEqual(r["historical_report_only_stage_mm"], [6310])

    def test_report_only_upper_does_not_make_bracket(self):
        r = review_stage(6098, STATION, [
            candidate(5660), candidate(6310, "historical_report_only")])
        self.assertFalse(r["pdf_metadata_bracket_exists"])
        self.assertIsNone(r["upper_gap_mm"])

    def test_extrapolation_rejected_for_scientific_use(self):
        r = review_stage(8000, STATION, [candidate(5660), candidate(7190)])
        self.assertFalse(r["pdf_metadata_bracket_exists"])
        self.assertFalse(r["observed_2016_flood_geometry_validated"])

    def test_exact_stage_still_does_not_grant_model_input(self):
        r = review_stage(5660, STATION, [candidate(5660)])
        self.assertEqual((r["lower_gap_mm"], r["upper_gap_mm"]), (0, 0))
        self.assertFalse(r["asset_inundation_or_loss_calibration_permitted"])

    def test_cross_station_rejected(self):
        item = candidate(5660)
        item["station"] = "F700000102"
        with self.assertRaises(StageReviewError):
            review_stage(6098, STATION, [item])

    def test_unknown_evidence_rejected(self):
        item = candidate(5660)
        item["evidence"] = "fully_approved"
        with self.assertRaises(StageReviewError):
            review_stage(6098, STATION, [item])

    def test_duplicate_identity_rejected(self):
        with self.assertRaises(StageReviewError):
            review_stage(6098, STATION, [candidate(5660), candidate(5660)])

    def test_provider_pdf_stage_mismatch_rejected(self):
        item = candidate(5660)
        item["source_url"] = "https://www.vigicrues.gouv.fr/ftp/pdf/ZICH_F700000103_7190.pdf"
        with self.assertRaises(StageReviewError):
            review_stage(6098, STATION, [item])

    def test_wrong_provider_host_rejected(self):
        item = candidate(5660)
        item["source_url"] = "https://example.org/ftp/pdf/ZICH_F700000103_5660.pdf"
        with self.assertRaises(StageReviewError):
            review_stage(6098, STATION, [item])

    def test_metadata_cannot_supply_model_approval(self):
        item = candidate(5660)
        item["model_admitted"] = True
        with self.assertRaises(StageReviewError):
            review_stage(6098, STATION, [item])

    def test_invalid_numeric_stages_rejected(self):
        for value in (6098.0, True, 0, -1):
            with self.subTest(value=value), self.assertRaises(StageReviewError):
                review_stage(value, STATION, [candidate(5660)])

    def test_all_external_gates_remain_closed(self):
        r = review_stage(6098, STATION, [candidate(5660)])
        self.assertFalse(r["full_geodata_bytes_verified"])
        self.assertFalse(r["geodata_reuse_rights_established"])


if __name__ == "__main__":
    unittest.main()
