# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic NOAA/FEMA envelope counts and leakage rejection tests."""

from __future__ import annotations

from copy import deepcopy
import json
import unittest

from research_runners.noaa_fema_envelope_overlap_v0 import (
    COHORT_WHERE, EnvelopeOverlapError, build_queries, reconcile,
)
from research_runners.noaa_michael_stac_preflight_v0 import STAC_ROOT


def source_item() -> dict:
    """Synthetic STAC-shaped item with a real public tile ID and bbox."""
    tile = "20181011aC0853300w302100n"
    west, south, east, north = -85.5501, 30.3249, -85.5249, 30.3501
    return {
        "type": "Feature",
        "id": tile,
        "stac_version": "1.0.0",
        "bbox": [west, south, east, north],
        "geometry": {"type": "Polygon", "coordinates": [[
            [west, south], [west, north], [east, north],
            [east, south], [west, south],
        ]]},
        "properties": {
            "datetime": "2018-10-11T00:00:00Z",
            "start_datetime": "2018-10-11T00:00:00+00:00",
            "end_datetime": "2018-10-14T00:00:00+00:00",
            "license": "NLPL",
        },
        "assets": {
            tile: {
                "href": STAC_ROOT + tile + ".tif",
                "type": "image/tiff",
                "proj:epsg": 4326,
                "proj:shape": [9340, 9340],
                "proj:transform": [west, 0.0000026980728051, 0, north,
                                  0, -0.0000026980728051],
                "eo:bands": [{"description": x} for x in ("red", "green", "blue", "alpha")],
                "raster:bands": [{"data_type": "uint8"} for _ in range(4)],
            },
        },
        "links": [{"rel": "self", "href": STAC_ROOT + "stac/" + tile + ".json"}],
    }


class EnvelopeOverlapTests(unittest.TestCase):
    def test_exact_read_only_arcgis_queries_and_predicate(self):
        q = build_queries(source_item())
        self.assertTrue(q["endpoint"].endswith("/FeatureServer/0/query"))
        self.assertEqual(q["cohort_census"]["where"], COHORT_WHERE)
        self.assertEqual(q["cohort_census"]["geometry"],
                         "-85.5501,30.3249,-85.5249,30.3501")
        self.assertEqual(q["cohort_census"]["inSR"], "4326")
        self.assertEqual(q["cohort_census"]["returnGeometry"], "false")
        self.assertEqual(q["damage_level_groups"]["groupByFieldsForStatistics"], "DMG_LEVEL")
        self.assertEqual(q["disaster_census"]["where"], "DIS_NUMBER = 'DR-4399'")
        for key in ("cohort_census", "damage_level_groups", "disaster_census"):
            self.assertNotIn("outFields", q[key])
            self.assertNotIn("returnIdsOnly", q[key])
            self.assertNotIn("returnDistinctValues", q[key])

    def test_nonzero_cohort_aggregate_never_claims_observed_roof_or_independence(self):
        x = reconcile(source_item(), {"count": 8}, [{"DMG_LEVEL": "AFF", "n": 8}], {"count": 8})
        self.assertEqual(x["damage_points_in_tile_envelope"], 8)
        self.assertEqual(x["damage_level_counts"]["AFF"], 8)
        self.assertTrue(x["candidate_envelope_contains_assessment_point"])
        for field in ("source_api_replies_authenticated",
                      "original_raster_alpha_coverage_verified",
                      "same_building_identity_proven",
                      "source_image_fema_label_independence_proven",
                      "per_feature_geometry_retrieved", "model_input_admitted"):
            self.assertFalse(x[field])
        self.assertNotIn("bbox", json.dumps(x))
        self.assertNotIn("latitude", json.dumps(x))

    def test_zero_count_not_promoted_to_spatial_overlap(self):
        x = reconcile(source_item(), {"count": 0}, [], {"count": 0})
        self.assertFalse(x["candidate_envelope_contains_assessment_point"])
        self.assertEqual(sum(x["damage_level_counts"].values()), 0)

    def test_group_order_and_stac_keys_do_not_affect_counts(self):
        p = source_item()
        a = reconcile(p, {"count": 9},
                      [{"DMG_LEVEL": "AFF", "n": 8}, {"DMG_LEVEL": "DES", "n": 1}],
                      {"count": 11})
        b = reconcile(deepcopy(p), {"count": 9},
                      [{"DMG_LEVEL": "DES", "n": 1}, {"DMG_LEVEL": "AFF", "n": 8}],
                      {"count": 11})
        self.assertEqual(a, b)

    def test_bad_counts_and_mismatched_parent_fail_closed(self):
        for bad in (-1, True, 3.14, None, "8"):
            with self.subTest(value=bad):
                with self.assertRaises(EnvelopeOverlapError):
                    reconcile(source_item(), {"count": bad}, [], {"count": 0})
        with self.assertRaisesRegex(EnvelopeOverlapError, "larger"):
            reconcile(source_item(), {"count": 8}, [{"DMG_LEVEL": "AFF", "n": 8}],
                      {"count": 7})
        with self.assertRaisesRegex(EnvelopeOverlapError, "disagree"):
            reconcile(source_item(), {"count": 8}, [{"DMG_LEVEL": "AFF", "n": 7}],
                      {"count": 8})

    def test_duplicate_code_and_unknown_code_are_rejected(self):
        with self.assertRaisesRegex(EnvelopeOverlapError, "repeated"):
            reconcile(source_item(), {"count": 8},
                      [{"DMG_LEVEL": "AFF", "n": 4}, {"DMG_LEVEL": "AFF", "n": 4}],
                      {"count": 8})
        with self.assertRaisesRegex(EnvelopeOverlapError, "unknown"):
            reconcile(source_item(), {"count": 1},
                      [{"DMG_LEVEL": "UNKNOWN_NEW", "n": 1}], {"count": 1})

    def test_reject_leaked_feature_fields_and_polygon_geometry(self):
        with self.assertRaisesRegex(EnvelopeOverlapError, "individual data"):
            reconcile(source_item(), {"count": 8},
                      [{"DMG_LEVEL": "AFF", "n": 8, "OBJECTID": 123}], {"count": 8})
        with self.assertRaisesRegex(EnvelopeOverlapError, "only geometry-free"):
            reconcile(source_item(), {"count": 0, "features": []}, [], {"count": 0})
        p = source_item()
        p["geometry"]["type"] = "Point"
        with self.assertRaisesRegex(EnvelopeOverlapError, "STAC metadata"):
            reconcile(p, {"count": 0}, [], {"count": 0})

    def test_bad_provider_granularity_is_not_accepted(self):
        with self.assertRaisesRegex(EnvelopeOverlapError, "unbounded"):
            reconcile(source_item(), {"count": 8},
                      [{"DMG_LEVEL": "AFF", "n": 1}] * 7, {"count": 8})
        with self.assertRaisesRegex(EnvelopeOverlapError, "group fields"):
            reconcile(source_item(), {"count": 8},
                      [{"DMG_LEVEL": "AFF", "COUNTY": "Bay", "n": 8}],
                      {"count": 8})


if __name__ == "__main__":
    unittest.main()
