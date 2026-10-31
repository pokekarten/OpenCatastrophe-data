# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic-only contract tests; never pretend region codes are footprints."""
from __future__ import annotations

import copy
import unittest

from research_runners.dfo_floodrecords_csv_preflight_v0 import HEADER as DFO_HEADER, parse_dfo_csv
from research_runners.historical_cat_benchmark_csv_preflight_v0 import HANZE_COLUMNS
from research_runners.flood_event_link_candidates_v0 import link_candidates
from research_runners.dfo_hanze_geographic_source_coverage_v0 import (
    GeographicCoverageError, FIELDS, survey_geographic_source_coverage,
)
from tests.test_flood_event_link_candidates_v0 import (
    csv_blob, dfo_row, hanze_row, crosswalk, sha,
)


def example(**hanze_changes):
    dfo = csv_blob(DFO_HEADER, [dfo_row(**{"Glide ﹟": "FL-2024-00001"})])
    hanze = csv_blob(HANZE_COLUMNS, [hanze_row(**{
        "admin_unit_nomenclature": "NUTS",
        "admin_unit_level": "3",
        "admin_unit_code": "DE123",
        "event_source": "Synthetic study",
        "sources_author_year": "Example 2024",
        "sources_impact_information": "",
        "hips_identifier": "SYNTH-HIPS",
        **hanze_changes,
    })])
    overlap = link_candidates(dfo, sha(dfo), hanze, sha(hanze), crosswalk(), sha(crosswalk()))
    dfo_data = parse_dfo_csv(dfo)
    return overlap, dfo_data, hanze


class DFOHANZEGeographicFieldCoverageTests(unittest.TestCase):
    def test_all_nine_boundary_claims_are_explicitly_false(self):
        overlap, dfo, hanze = example()
        result = survey_geographic_source_coverage(overlap, dfo, hanze, sha(hanze))
        self.assertEqual(result["candidate_pair_count"], 1)
        self.assertEqual(result["distinct_dfo_records_in_pairs"], 1)
        self.assertEqual(result["distinct_hanze_records_in_pairs"], 1)
        self.assertEqual(result["dfo_country_label_present_pairs"], 1)
        self.assertEqual(result["dfo_glide_identifier_present_pairs"], 1)
        self.assertEqual(result["hanze_nonempty_original_field_pair_counts"]["admin_unit_code"], 1)
        self.assertEqual(result["hanze_nonempty_original_field_pair_counts"]["sources_author_year"], 1)
        self.assertEqual(result["hanze_nonempty_original_field_pair_counts"]["sources_impact_information"], 0)
        self.assertEqual(set(result["hanze_nonempty_original_field_pair_counts"]), set(FIELDS))
        self.assertTrue(result["hanze_admin_codes_are_recorded_regions_not_flood_polygons"])
        self.assertTrue(result["dfo_record_has_no_geocoded_location_in_pinned_csv"])
        self.assertTrue(result["dfo_country_is_not_a_geographic_footprint"])
        for field in ("same_flood_event_identity_confirmed", "region_geometry_intersection_verified",
                      "hydrologic_event_causality_verified", "third_party_rights_review_complete",
                      "observed_insured_loss_computed", "model_input_admitted",
                      "provider_field_values_or_event_ids_emitted"):
            self.assertFalse(result[field])
        self.assertNotIn("DE123", str(result))
        self.assertNotIn("SYNTH-HIPS", str(result))
        self.assertNotIn("FL-2024-00001", str(result))
        self.assertNotIn("5500", str(result))

    def test_missingness_is_counted_not_imputed_or_mapped(self):
        overlap, dfo, hanze = example(admin_unit_code="  ", sources_author_year=" ")
        report = survey_geographic_source_coverage(overlap, dfo, hanze, sha(hanze))
        self.assertEqual(report["hanze_nonempty_original_field_pair_counts"]["admin_unit_code"], 0)
        self.assertEqual(report["hanze_nonempty_original_field_pair_counts"]["sources_author_year"], 0)
        self.assertFalse(report["same_flood_event_identity_confirmed"])

    def test_sha256_and_crosswalk_wrong_country_fail_closed(self):
        overlap, dfo, hanze = example()
        with self.assertRaisesRegex(GeographicCoverageError, "identity differs"):
            survey_geographic_source_coverage(overlap, dfo, hanze, "0"*64)
        broken = copy.deepcopy(overlap)
        broken["candidate_pairs"][0]["country_iso2_from_supplied_crosswalk"] = "FR"
        with self.assertRaisesRegex(GeographicCoverageError, "HANZE candidate country changed"):
            survey_geographic_source_coverage(broken, dfo, hanze, sha(hanze))
        broken = copy.deepcopy(overlap)
        broken["candidate_pairs"][0]["dfo_country_original"] = "France"
        with self.assertRaisesRegex(GeographicCoverageError, "DFO candidate country changed"):
            survey_geographic_source_coverage(broken, dfo, hanze, sha(hanze))

    def test_duplicated_or_missing_candidate_identity_fails_closed(self):
        overlap, dfo, hanze = example()
        overlap["candidate_pairs"].append(dict(overlap["candidate_pairs"][0]))
        overlap["candidate_pair_count"] += 1
        with self.assertRaisesRegex(GeographicCoverageError, "duplicate candidate pair"):
            survey_geographic_source_coverage(overlap, dfo, hanze, sha(hanze))
        overlap, dfo, hanze = example()
        overlap["candidate_pairs"][0]["hanze_event_id"] = "missing"
        with self.assertRaisesRegex(GeographicCoverageError, "candidate ID missing"):
            survey_geographic_source_coverage(overlap, dfo, hanze, sha(hanze))

    def test_empty_pairs_mean_no_linkage_not_no_disaster(self):
        overlap, dfo, hanze = example()
        overlap["candidate_pairs"] = []
        overlap["candidate_pair_count"] = 0
        report = survey_geographic_source_coverage(overlap, dfo, hanze, sha(hanze))
        self.assertEqual(report["candidate_pair_count"], 0)
        self.assertEqual(sum(report["hanze_nonempty_original_field_pair_counts"].values()), 0)
        self.assertFalse(report["model_input_admitted"])


if __name__ == "__main__":
    unittest.main()
