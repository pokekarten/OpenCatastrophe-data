# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only, source-free regression tests for bounded original NBI crosswalk."""
from __future__ import annotations

import json
import unittest

from research_runners import fhwa_ntad_2025_cross_source_audit_v0 as proof
from research_runners.fhwa_nbi_socrata_metadata_gate_v0 import Blocked


def source_rows():
    return [
        {
            "year": "2025", "state_code_001": "6",
            "structure_number_008": f"SRC2025{i:08d}",
            "lat_016": "33452500", "long_017": "086300000",
            "year_built_027": "1970",
        }
        for i in range(proof.SAMPLE_COUNT)
    ]


def layer_features(source=None):
    source = source if source is not None else source_rows()
    return [
        {
            "attributes": {
                "STATE_CODE_001": "06",
                "STRUCTURE_NUMBER_008": row["structure_number_008"],
                "LAT_016": row["lat_016"],
                "LONG_017": row["long_017"],
                "YEAR_BUILT_027": 1970,
                "LATDD": 33 + 45 / 60 + 25 / 3600,
                "LONGDD": -(86 + 30 / 60),
            },
            "geometry": {
                "x": -(86 + 30 / 60),
                "y": 33 + 45 / 60 + 25 / 3600,
            },
        }
        for row in source
    ]


def arcgis(features=None):
    return {
        "spatialReference": {"wkid": 4326, "latestWkid": 4326},
        "features": layer_features() if features is None else features,
        "exceededTransferLimit": False,
    }


def wire(data):
    return json.dumps(data, separators=(",", ":"), allow_nan=False).encode("utf-8")


class IndependentNBI2025CrossSourceTests(unittest.TestCase):
    def test_exact_identity_25_bridge_magnitude_agreement_not_admission(self):
        report = proof.compare_sources(wire(source_rows()), wire(arcgis()))
        self.assertEqual(report["socrata_selected_bridge_rows"], 25)
        self.assertEqual(report["ntad_source_feature_rows"], 25)
        self.assertEqual(report["matched_unique_bridge_state_ids"], 25)
        self.assertEqual(report["source_ids_absent_in_bounded_ntad_response"], 0)
        self.assertEqual(report["approx_delta_up_to_25_m"], 25)
        self.assertEqual(report["approx_north_component_over_25_m"], 0)
        self.assertEqual(report["approx_east_component_over_25_m"], 0)
        self.assertEqual(report["approx_both_components_over_25_m"], 0)
        self.assertEqual(
            report["approx_combined_over_25_m_with_each_component_at_most_25_m"], 0)
        self.assertEqual(report["matched_source_year_built_equal"], 25)
        self.assertEqual(report["matched_nbi_coded_coordinate_strings_equal"], 25)
        self.assertEqual(report["ntad_decimal_LATDD_LONGDD_available"], 25)
        self.assertEqual(report["ntad_decimal_vs_source_legacy_over_25_m"], 0)
        self.assertEqual(report["ntad_decimal_vs_point_geometry_over_25_m"], 0)
        self.assertFalse(report["model_input_admitted"])
        self.assertFalse(report["longitude_sign_or_geodetic_datum_independently_proven"])
        self.assertNotIn("SRC2025", json.dumps(report))
        self.assertNotIn("33452500", json.dumps(report))
        self.assertNotIn("-86.5", json.dumps(report))

    def test_query_allowlist_preserves_string_identity_and_rejects_injection(self):
        base = source_rows()
        clause = proof.arcgis_where_from_exact_source_rows(base)
        self.assertIn("STATE_CODE_001 IN ('06','6')", clause)
        self.assertIn("'SRC202500000000'", clause)
        self.assertEqual(clause.count("'SRC2025"), proof.SAMPLE_COUNT)
        base[2]["structure_number_008"] = "' OR 1=1 --"
        with self.assertRaisesRegex(Blocked, "unsafe original bridge identifier"):
            proof.arcgis_where_from_exact_source_rows(base)

    def test_2025_source_selection_must_have_original_year_and_state(self):
        x = source_rows()
        x[0]["year"] = 2024
        with self.assertRaisesRegex(Blocked, "explicit year selector"):
            proof.compare_sources(wire(x), wire(arcgis()))
        x = source_rows()
        x[0]["state_code_001"] = 36
        with self.assertRaisesRegex(Blocked, "explicit state selector"):
            proof.compare_sources(wire(x), wire(arcgis()))

    def test_duplicate_ntad_identity_never_counts_as_exact_join(self):
        f = layer_features()
        f.append(f[0].copy())
        report = proof.compare_sources(wire(source_rows()), wire(arcgis(f)))
        self.assertEqual(report["source_ids_ambiguous_ntad_multiple_features"], 1)
        self.assertEqual(report["matched_unique_bridge_state_ids"], 24)
        self.assertEqual(report["angular_magnitude_comparisons"], 24)
        self.assertFalse(report["model_input_admitted"])

    def test_missing_and_wrong_state_ntad_features_do_not_generate_matches(self):
        f = layer_features()
        f[0]["attributes"]["STATE_CODE_001"] = "36"
        f[1]["attributes"]["STATE_CODE_001"] = "unknown"
        report = proof.compare_sources(wire(source_rows()), wire(arcgis(f)))
        self.assertEqual(report["matched_unique_bridge_state_ids"], 23)
        self.assertEqual(report["source_ids_absent_in_bounded_ntad_response"], 2)
        self.assertEqual(report["ntad_feature_identifiers_not_requested"], 1)
        self.assertEqual(report["invalid_ntad_feature_identifiers"], 1)

    def test_fractional_boolean_and_invalid_years_cannot_fake_concordance(self):
        rows = source_rows()
        features = layer_features(rows)
        features[0]["attributes"]["YEAR_BUILT_027"] = 1970.9
        features[1]["attributes"]["YEAR_BUILT_027"] = True
        features[2]["attributes"]["YEAR_BUILT_027"] = 2026
        rows[3]["year_built_027"] = 1970.7
        rows[4]["year_built_027"] = "unknown"
        features[5]["attributes"]["YEAR_BUILT_027"] = 1969
        report = proof.compare_sources(wire(rows), wire(arcgis(features)))
        self.assertEqual(report["matched_source_year_built_equal"], 19)
        self.assertEqual(report["matched_source_year_built_different"], 1)
        self.assertEqual(report["matched_source_year_built_unavailable"], 5)
        self.assertEqual(report["matched_unique_bridge_state_ids"], 25)
        self.assertFalse(report["model_input_admitted"])
        self.assertNotIn("SRC2025", json.dumps(report))

    def test_coordinate_disagreement_reported_without_leaking_its_location(self):
        f = layer_features()
        f[0]["geometry"]["x"] = -80.0
        f[1]["geometry"] = None
        f[2]["attributes"]["LAT_016"] = "33452520"
        f[3]["attributes"]["YEAR_BUILT_027"] = 1950
        report = proof.compare_sources(wire(source_rows()), wire(arcgis(f)))
        self.assertEqual(report["matched_ntad_missing_invalid_geometry"], 1)
        self.assertEqual(report["matched_nbi_coded_coordinate_strings_different"], 1)
        self.assertEqual(report["matched_source_year_built_different"], 1)
        self.assertEqual(report["approx_delta_over_250_m"], 1)
        self.assertEqual(report["approx_east_component_over_25_m"], 1)
        self.assertEqual(report["approx_north_component_over_25_m"], 0)
        self.assertEqual(report["approx_only_east_component_over_25_m"], 1)
        self.assertEqual(report["ntad_decimal_vs_source_legacy_over_25_m"], 0)
        self.assertEqual(report["ntad_decimal_vs_point_geometry_over_25_m"], 1)
        self.assertEqual(report["angular_magnitude_comparisons"], 24)
        self.assertNotIn("-80.0", json.dumps(report))
        self.assertFalse(report["independent_official_survey_validation"])

    def test_unmatched_snapshot_is_valid_negative_result_not_false_success(self):
        report = proof.compare_sources(wire(source_rows()), wire(arcgis([])))
        self.assertEqual(report["matched_unique_bridge_state_ids"], 0)
        self.assertEqual(report["source_ids_absent_in_bounded_ntad_response"], 25)
        self.assertIsNone(report["max_approx_angular_delta_m"])
        self.assertFalse(report["model_input_admitted"])

    def test_incomplete_or_wrong_ntad_query_is_hard_error(self):
        base = wire(source_rows())
        cases = (
            {"error": {"code": 400}},
            {"features": []},
            {"features": [], "spatialReference": {"wkid": 3857}},
            {"features": [], "spatialReference": {"wkid": 4326},
             "exceededTransferLimit": True},
            {"features": [{}], "spatialReference": {"wkid": 4326}},
        )
        for case in cases:
            with self.subTest(case=case), self.assertRaises(Blocked):
                proof.compare_sources(base, wire(case))

    def test_duplicate_original_json_keys_and_invalid_float_rejected(self):
        base = wire(source_rows())
        malformed = (
            wire(arcgis()).replace(b'"features":', b'"features":[],"features":', 1),
            b'{"spatialReference":{"wkid":4326},"features": NaN}',
            b'<html>' * 50,
        )
        for original in malformed:
            with self.subTest(original=original[:40]), self.assertRaises(Blocked):
                proof.compare_sources(base, original)

    def test_arcgis_query_and_source_URL_are_fixed_HTTPS_hosts(self):
        self.assertEqual(proof.STATE, 6)
        self.assertEqual(proof.YEAR, 2025)
        self.assertTrue(proof.SOCRATA_API.startswith("https://data.transportation.gov/"))
        self.assertTrue(proof.NTAD_API.startswith("https://services.arcgis.com/"))
        self.assertEqual(proof.MAX_SAMPLES, 100)


    def test_ntad_decimal_fields_can_diverge_from_legacy_codes_independently(self):
        f = layer_features()
        f[0]["attributes"]["LATDD"] = 34.3
        report = proof.compare_sources(wire(source_rows()), wire(arcgis(f)))
        self.assertEqual(report["matched_unique_bridge_state_ids"], 25)
        self.assertEqual(report["matched_nbi_coded_coordinate_strings_equal"], 25)
        self.assertEqual(report["ntad_decimal_vs_source_legacy_over_25_m"], 1)
        self.assertEqual(report["ntad_decimal_vs_point_geometry_over_25_m"], 1)
        self.assertEqual(report["approx_delta_over_250_m"], 0)
        self.assertFalse(report["independent_point_geometry_agreement_admitted"])

    def test_ntad_signed_decimal_to_point_hemisphere_flip_is_visible(self):
        features = layer_features()
        # Two false positives under the prior unsigned decimal/geometry gate.
        # Historical DMS remains unsigned and must not be reinterpreted.
        features[0]["geometry"]["x"] *= -1
        features[1]["geometry"]["y"] *= -1
        report = proof.compare_sources(wire(source_rows()), wire(arcgis(features)))
        self.assertEqual(report["ntad_decimal_vs_point_geometry_over_25_m"], 2)
        self.assertEqual(report["ntad_decimal_vs_source_legacy_over_25_m"], 0)
        self.assertEqual(report["approx_delta_up_to_25_m"], 25)
        self.assertFalse(report["independent_point_geometry_agreement_admitted"])
        self.assertFalse(report["model_input_admitted"])
        self.assertNotIn("SRC2025", json.dumps(report))

    def test_missing_ntad_decimal_columns_do_not_invent_concordance(self):
        f = layer_features()
        f[0]["attributes"].pop("LATDD")
        f[1]["attributes"]["LONGDD"] = None
        proof_result = proof.compare_sources(wire(source_rows()), wire(arcgis(f)))
        self.assertEqual(proof_result["ntad_decimal_LATDD_LONGDD_available"], 23)
        self.assertEqual(proof_result["ntad_decimal_LATDD_LONGDD_missing_invalid"], 2)
        self.assertEqual(proof_result["ntad_decimal_vs_point_geometry_comparisons"], 23)
        self.assertEqual(proof_result["angular_magnitude_comparisons"], 25)

    def test_independently_selected_second_state_36_preserves_full_source_identity(self):
        rows = source_rows()
        for row in rows:
            row["state_code_001"] = "36"
        features = layer_features()
        for feature in features:
            feature["attributes"]["STATE_CODE_001"] = "36"
        clause = proof.arcgis_where_from_exact_source_rows(rows, state=36)
        self.assertIn("STATE_CODE_001 IN ('36')", clause)
        report = proof.compare_sources(wire(rows), wire(arcgis(features)), state=36)
        self.assertEqual(report["source_state_code"], 36)
        self.assertEqual(report["matched_unique_bridge_state_ids"], 25)
        self.assertEqual(report["ntad_decimal_vs_source_legacy_over_25_m"], 0)
        self.assertFalse(report["model_input_admitted"])

    def test_unreviewed_states_cannot_expand_original_data_harvest(self):
        for unreviewed in (0, 1, 37, 99, True, "6"):
            with self.subTest(state=unreviewed):
                with self.assertRaises(Blocked):
                    proof.compare_sources(wire(source_rows()), wire(arcgis()),
                                          state=unreviewed)
                with self.assertRaises(Blocked):
                    proof.arcgis_where_from_exact_source_rows(source_rows(),
                                                              state=unreviewed)

    def test_different_north_east_and_dual_axis_source_discrepancies(self):
        features = layer_features()
        # Only north component exceeds 25 m.
        features[0]["geometry"]["y"] += 0.002
        # Only east component exceeds 25 m.
        features[1]["geometry"]["x"] -= 0.003
        # Both components exceed 25 m.
        features[2]["geometry"]["x"] -= 0.002
        features[2]["geometry"]["y"] += 0.002
        audited = proof.compare_sources(wire(source_rows()), wire(arcgis(features)))
        self.assertEqual(audited["approx_north_component_over_25_m"], 2)
        self.assertEqual(audited["approx_east_component_over_25_m"], 2)
        self.assertEqual(audited["approx_only_north_component_over_25_m"], 1)
        self.assertEqual(audited["approx_only_east_component_over_25_m"], 1)
        self.assertEqual(audited["approx_both_components_over_25_m"], 1)
        self.assertEqual(
            audited["approx_combined_over_25_m_with_each_component_at_most_25_m"], 0)
        self.assertGreater(audited["max_approx_north_component_m"], 25)
        self.assertGreater(audited["max_approx_east_component_m"], 25)
        self.assertFalse(audited["model_input_admitted"])
        self.assertNotIn("SRC2025", json.dumps(audited))

    def test_small_diagonal_deltas_do_not_falsely_mark_single_axis(self):
        f = layer_features()
        # About 16.7 m per axis: combined hypotenuse > 25? Here 23.6 m.
        f[0]["geometry"]["y"] += 0.00015
        f[0]["geometry"]["x"] -= 0.00018
        row = proof.compare_sources(wire(source_rows()), wire(arcgis(f)))
        self.assertEqual(row["approx_north_component_over_25_m"], 0)
        self.assertEqual(row["approx_east_component_over_25_m"], 0)
        self.assertEqual(row["approx_both_components_over_25_m"], 0)
        self.assertEqual(
            row["approx_combined_over_25_m_with_each_component_at_most_25_m"], 0)

    def test_diagonal_vector_above_25_with_both_axes_below_threshold(self):
        f = layer_features()
        # ~21m north and ~20m east, but ~29m combined.
        f[0]["geometry"]["y"] += 0.00019
        f[0]["geometry"]["x"] -= 0.00021
        result = proof.compare_sources(wire(source_rows()), wire(arcgis(f)))
        self.assertEqual(result["approx_delta_over_25_up_to_250_m"], 1)
        self.assertEqual(result["approx_only_north_component_over_25_m"], 0)
        self.assertEqual(result["approx_only_east_component_over_25_m"], 0)
        self.assertEqual(result["approx_both_components_over_25_m"], 0)
        self.assertEqual(
            result["approx_combined_over_25_m_with_each_component_at_most_25_m"], 1)
        self.assertFalse(result["model_input_admitted"])

if __name__ == "__main__":
    unittest.main()
