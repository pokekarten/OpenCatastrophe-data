# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only strict source-year/NUTS ID lookup tests: not flood geometry."""
from __future__ import annotations

import unittest

from research_runners.dfo_floodrecords_csv_preflight_v0 import HEADER as DFO_HEADER
from research_runners.historical_cat_benchmark_csv_preflight_v0 import HANZE_COLUMNS
from research_runners.hanze_gisco_nuts2024_attribute_audit_v0 import (
    GISCO_HEADER, NUTS2024AuditError, nuts2024_index,
    audit_hanze_candidate_region_codes,
)
from tests.test_flood_event_link_candidates_v0 import (
    csv_blob, dfo_row, hanze_row, crosswalk, sha,
)
from research_runners.flood_event_link_candidates_v0 import link_candidates


def official_csv(**changes):
    rows = [
        {"CNTR_CODE": "DE", "NUTS_ID": "DE", "NAME_LATN": "Germany", "NUTS_NAME": "Deutschland",
         "MOUNT_TYPE": "0", "URBN_TYPE": "0", "COAST_TYPE": "0"},
        {"CNTR_CODE": "DE", "NUTS_ID": "DE111", "NAME_LATN": "Test County",
         "NUTS_NAME": "Test Kreis", "MOUNT_TYPE": "0", "URBN_TYPE": "0", "COAST_TYPE": "0"},
        {"CNTR_CODE": "FR", "NUTS_ID": "FR101", "NAME_LATN": "Fictional France",
         "NUTS_NAME": "Fictionnel", "MOUNT_TYPE": "0", "URBN_TYPE": "0", "COAST_TYPE": "0"},
    ]
    rows[1].update(changes)
    return csv_blob(GISCO_HEADER, rows)


def upstream(**hanze_changes):
    dfo = csv_blob(DFO_HEADER, [dfo_row()])
    hanze = csv_blob(HANZE_COLUMNS, [hanze_row(**{
        "admin_unit_nomenclature": "NUTS",
        "admin_unit_level": "3",
        "admin_unit_year": "2024",
        "admin_unit_code": "DE111",
        **hanze_changes,
    })])
    mapping = crosswalk()
    candidates = link_candidates(dfo, sha(dfo), hanze, sha(hanze), mapping, sha(mapping))
    return hanze, candidates


class NUTS2024AttributeAuditTests(unittest.TestCase):
    def test_strict_gisco_attributes_and_sha_bound(self):
        blob = official_csv()
        index, metadata = nuts2024_index(blob, expected_sha256=sha(blob))
        self.assertEqual(index["DE111"], "DE")
        self.assertEqual(metadata["official_attribute_rows"], 3)
        self.assertEqual(metadata["official_rows_by_nuts_level"]["3"], 2)
        self.assertTrue(metadata["original_file_sha256_pinned"])
        self.assertFalse(metadata["original_geometry_downloaded"])
        self.assertFalse(metadata["model_input_admitted"])
        with self.assertRaisesRegex(NUTS2024AuditError, "SHA256"):
            nuts2024_index(blob, expected_sha256="0"*64)

    def test_exact_one_code_nuts2024_match_no_footprint_inference(self):
        hanze, candidates = upstream()
        gis = official_csv()
        result = audit_hanze_candidate_region_codes(
            hanze, sha(hanze), candidates, gis, expected_gisco_sha256=sha(gis))
        self.assertEqual(result["candidate_pair_count"], 1)
        self.assertEqual(result["candidate_code_status_counts"]["exact_official_country_level_vintage_code_matches"], 1)
        self.assertTrue(result["historical_2024_nuts_code_existence_confirmed"])
        for field in ("verified_geographic_point_or_polygon_overlay",
                      "dfo_flood_extent_geolocated", "same_flood_event_identity_confirmed",
                      "source_or_region_values_exported", "insured_loss_or_tiv_estimated",
                      "third_party_rights_review_complete", "model_source_admitted"):
            self.assertFalse(result[field])
        self.assertNotIn("DE111", str(result))
        self.assertNotIn("Test County", str(result))

    def test_missing_code_or_non_nuts_nomenclature_not_forced(self):
        for change, expected in [
            ({"admin_unit_code": ""}, "missing_region_code"),
            ({"admin_unit_nomenclature": "ITL"}, "unsupported_or_non_nuts_nomenclature"),
            ({"admin_unit_code": "DE111, DE112"}, "multi_region_or_noncanonical_code_manual_review"),
            ({"admin_unit_code": "DE999"}, "canonical_hanze_code_absent_from_gisco"),
            ({"admin_unit_level": "2"}, "missing_or_mismatched_nuts_level"),
            ({"admin_unit_year": ""}, "unsupported_region_vintage"),
        ]:
            with self.subTest(change=change):
                hanze, candidates = upstream(**change)
                result = audit_hanze_candidate_region_codes(hanze, sha(hanze), candidates, official_csv())
                self.assertEqual(result["candidate_code_status_counts"][expected], 1)
                self.assertEqual(result["candidate_code_status_counts"]["exact_official_country_level_vintage_code_matches"], 0)

    def test_invalid_official_identity_or_duplicated_code_fails_closed(self):
        for bad, message in [
            ({"NUTS_ID": "DE111;DE112"}, "noncanonical"),
            ({"CNTR_CODE": "FR"}, "noncanonical"),
            ({"NUTS_ID": "FR101", "CNTR_CODE": "FR"}, "duplicate"),
        ]:
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(NUTS2024AuditError, message):
                    nuts2024_index(official_csv(**bad))
        with self.assertRaisesRegex(NUTS2024AuditError, "header"):
            nuts2024_index(csv_blob(GISCO_HEADER[:-1], [{"CNTR_CODE": "DE", "NUTS_ID": "DE"}]))
        with self.assertRaisesRegex(NUTS2024AuditError, "byte size invalid"):
            nuts2024_index(b"")

    def test_upstream_hanze_sha_and_model_identity_are_checked(self):
        hanze, candidates = upstream()
        with self.assertRaisesRegex(NUTS2024AuditError, "invalid upstream"):
            audit_hanze_candidate_region_codes(hanze, "0"*64, candidates, official_csv())
        candidates["common_event_identity_proven"] = True
        with self.assertRaisesRegex(NUTS2024AuditError, "upstream"):
            audit_hanze_candidate_region_codes(hanze, sha(hanze), candidates, official_csv())

    def test_zero_candidates_means_no_validated_join_not_no_floods(self):
        hanze, candidates = upstream()
        candidates["candidate_pairs"] = []
        candidates["candidate_pair_count"] = 0
        result = audit_hanze_candidate_region_codes(hanze, sha(hanze), candidates, official_csv())
        self.assertEqual(sum(result["candidate_code_status_counts"].values()), 0)
        self.assertFalse(result["same_flood_event_identity_confirmed"])


if __name__ == "__main__":
    unittest.main()
