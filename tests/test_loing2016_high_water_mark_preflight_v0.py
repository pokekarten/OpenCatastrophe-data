# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic, network-free Loing 2016 water-surface QA tests."""
import copy
import unittest
from research_runners.loing2016_high_water_mark_preflight_v0 import (
    WatermarkBlocked, review_marks,
)


def mark():
    return {
        "site_id": "SYNTHETIC_SITE_A", "mark_id": "SYNTHETIC_MARK_A",
        "source_site_url": "https://www.reperesdecrues.developpement-durable.gouv.fr/site/example-0",
        "watercourse": "Le Loing", "event_date": "2016-06-01",
        "survey_date": "2016-06-08", "mark_evidence": "physical_flood_trace",
        "event_maximum_flag": True,
        "survey_method": "GPS", "vertical_datum": "NGF IGN 1969",
        "longitude_wgs84": 2.72, "latitude_wgs84": 48.01,
        "reference_kind": "external_reference", "reference_elevation_m": "100.375",
        "water_offset_from_reference_m": "0.250",
        "published_water_surface_elevation_m": "100.625",
    }


class WatermarkPreflightTest(unittest.TestCase):
    def test_exact_addition_reconciles_but_never_becomes_depth(self):
        r = review_marks([mark()])
        self.assertEqual(r["marks"][0]["water_surface_m_ngf_ign1969"], "100.625")
        self.assertTrue(r["marks"][0]["physical_event_maximum_trace_candidate"])
        self.assertFalse(r["marks"][0]["independent_physical_trace_candidate"])
        self.assertFalse(r["marks"][0]["independent_atlas_holdout_established"])
        self.assertEqual(r["independent_atlas_holdout_candidates"], 0)
        self.assertFalse(r["marks"][0]["inundation_depth_at_building_established"])
        self.assertFalse(r["risk_or_insured_loss_model_admitted"])

    def test_nonmaximum_mark_is_context_not_peak_validation(self):
        x = mark()
        x["event_maximum_flag"] = False
        r = review_marks([x])
        self.assertFalse(r["marks"][0]["physical_event_maximum_trace_candidate"])
        self.assertFalse(r["marks"][0]["independent_physical_trace_candidate"])
        self.assertEqual(r["physical_trace_candidates"], 0)

    def test_invalid_peak_flag_blocks(self):
        for value in (1, None, "yes"):
            with self.subTest(value=value), self.assertRaises(WatermarkBlocked):
                x = mark()
                x["event_maximum_flag"] = value
                review_marks([x])

    def test_observed_mark_cannot_be_2017_atlas_holdout_without_lineage(self):
        r = review_marks([mark()])
        mark_result = r["marks"][0]
        self.assertTrue(mark_result["physical_event_maximum_trace_candidate"])
        self.assertFalse(mark_result["independent_atlas_holdout_established"])
        self.assertEqual(mark_result["atlas_2017_calibration_membership"], "unknown")
        self.assertEqual(mark_result["atlas_2021_revision_calibration_membership"], "unknown")
        self.assertFalse(r["2017_atlas_input_mark_identity_list_attested"])
        self.assertEqual(r["used_2017_driee_calibration_mark_count_documented"], 68)
        self.assertFalse(r["2021_ddt_zi_challenge_lineage_attested"])

    def test_no_caller_can_inject_false_holdout_certification(self):
        x = mark()
        x["atlas_2017_calibration_membership"] = "verified_not_used"
        with self.assertRaises(WatermarkBlocked):
            review_marks([x])

    def test_self_referenced_flood_mark_no_invented_zero_offset(self):
        x = mark()
        x["reference_kind"] = "flood_mark"
        x["water_offset_from_reference_m"] = None
        x["published_water_surface_elevation_m"] = "100.375"
        self.assertTrue(review_marks([x])["marks"][0]["arithmetic_reconciled"])

    def test_bad_survey_offset_or_water_math_block(self):
        for offset, water in (("0.250", "100.635"), (None, "100.625"),
                              ("0.25m", "100.625")):
            with self.subTest(offset=offset, water=water), self.assertRaises(WatermarkBlocked):
                x = mark()
                x["water_offset_from_reference_m"] = offset
                x["published_water_surface_elevation_m"] = water
                review_marks([x])

    def test_missing_and_wrong_vertical_datum_block(self):
        for datum in (None, "NGF IGN 1978", "unknown", "ETRS89"):
            x = mark()
            x["vertical_datum"] = datum
            with self.subTest(datum=datum), self.assertRaises(WatermarkBlocked):
                review_marks([x])

    def test_event_and_survey_dates_distinct(self):
        for ev, survey in (("1910-01-20", "2016-06-08"),
                           ("2016-06-08", "2016-06-08"),
                           ("2016-06-01", "2016-05-20"),
                           ("2016-02-30", "2016-06-08")):
            x = mark()
            x["event_date"], x["survey_date"] = ev, survey
            with self.subTest(ev=ev, survey=survey), self.assertRaises(WatermarkBlocked):
                review_marks([x])

    def test_wrong_river_and_coords_block(self):
        for field, value in (("watercourse", "Le Puiseaux"),
                             ("longitude_wgs84", True),
                             ("latitude_wgs84", 10 ** 3000),
                             ("longitude_wgs84", float("nan")),
                             ("latitude_wgs84", -90)):
            x = mark()
            x[field] = value
            with self.subTest(field=field), self.assertRaises(WatermarkBlocked):
                review_marks([x])

    def test_oral_testimony_remains_weaker_context(self):
        x = mark()
        x["mark_evidence"] = "oral_testimony"
        r = review_marks([x])
        self.assertFalse(r["marks"][0]["physical_event_maximum_trace_candidate"])
        self.assertFalse(r["marks"][0]["independent_physical_trace_candidate"])

    def test_untrusted_provider_host_and_query_block(self):
        for url in ("https://example.net/site/example-0",
                    "https://www.reperesdecrues.developpement-durable.gouv.fr/site/example-0?token=1",
                    "http://www.reperesdecrues.developpement-durable.gouv.fr/site/example-0"):
            x = mark()
            x["source_site_url"] = url
            with self.subTest(url=url), self.assertRaises(WatermarkBlocked):
                review_marks([x])

    def test_duplicates_rejected(self):
        with self.assertRaises(WatermarkBlocked):
            review_marks([mark(), copy.deepcopy(mark())])

    def test_no_provider_or_model_approval_fields_accepted(self):
        x = mark()
        x["hazard_model_input_admitted"] = True
        with self.assertRaises(WatermarkBlocked):
            review_marks([x])

    def test_incorrect_number_precision_and_bad_strings(self):
        for value in (100.375, "100.3758", "NaN", "-1", "1e2"):
            x = mark()
            x["reference_elevation_m"] = value
            with self.subTest(value=value), self.assertRaises(WatermarkBlocked):
                review_marks([x])

    def test_empty_or_oversized_cohort_blocks(self):
        for cohort in ([], [mark()] * 51, {}):
            with self.assertRaises(WatermarkBlocked):
                review_marks(cohort)


if __name__ == "__main__":
    unittest.main()
