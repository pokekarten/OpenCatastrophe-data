# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic tests for the USGS 3DEP reference/datum and upstream lineage gate."""

from __future__ import annotations

from copy import deepcopy
import json
import unittest

from research_runners.usgs_3dep_lineage_preflight_v0 import MetadataError, preflight


def fixture() -> dict:
    common = {
        "horizontal_crs": "EPSG:26915",
        "vertical_datum": "NAVD88",
        "vertical_realization": "NAVD88_2009",
        "geoid_model": "GEOID18",
        "elevation_unit": "metre",
        "source_vintage_start": "2018-05-03",
        "source_vintage_end": "2019-04-17",
    }
    return {
        "s1m": dict(common, dataset_id="usgs.3dep.seamless-1m-dem",
                    asset_id="synthetic_tile_01", sha256="a" * 64,
                    byte_count=10000, data_type="bare_earth_dem",
                    source_lidar_workunit_ids=["work.A", "work.B"]),
        "lidar": dict(common, dataset_id="usgs.3dep.lidar-point-cloud",
                      asset_id="synthetic_lidar_01", sha256="b" * 64,
                      byte_count=20000, data_type="classified_lidar_point_cloud",
                      source_lidar_workunit_ids=["work.B"]),
    }


class ThreeDEPLineagePreflightTests(unittest.TestCase):
    def test_shared_upstream_provenance_is_not_independent(self):
        report = preflight(fixture())
        self.assertEqual(report["upstream_relationship"], "shared_lidar_workunit")
        self.assertEqual(report["shared_lidar_workunit_count"], 1)
        self.assertTrue(report["horizontal_and_vertical_metadata_exact_match"])
        for name in ("scientific_independence_proven", "spatial_alignment_proven",
                     "numeric_height_comparison_permitted", "model_input_admitted",
                     "source_data_redistribution_permitted"):
            self.assertFalse(report[name])
        payload = json.dumps(report)
        self.assertNotIn("synthetic_tile", payload)
        self.assertNotIn("work.B", payload)
        self.assertNotIn("EPSG:26915", payload)

    def test_disjoint_work_units_do_not_prove_independent_sampling(self):
        p = fixture()
        p["lidar"]["source_lidar_workunit_ids"] = ["work.C"]
        r = preflight(p)
        self.assertEqual(r["upstream_relationship"], "not_proven_independent")
        self.assertEqual(r["shared_lidar_workunit_count"], 0)
        self.assertFalse(r["scientific_independence_proven"])

    def test_reference_datum_geoid_and_crs_mismatch_fail_closed(self):
        for field, bad in (
            ("horizontal_crs", "EPSG:4326"),
            ("vertical_datum", "NGVD29"),
            ("vertical_realization", "NAVD88_2012"),
            ("geoid_model", "GEOID12B"),
        ):
            with self.subTest(field=field):
                p = fixture()
                p["lidar"][field] = bad
                with self.assertRaisesRegex(MetadataError, field):
                    preflight(p)

    def test_missing_unknown_and_invalid_vertical_reference_fails(self):
        for field in ("vertical_datum", "vertical_realization", "geoid_model"):
            for value in (None, "", "unknown", "unspecified", "NAVD88 (assumed)"):
                with self.subTest(field=field, value=value):
                    p = fixture()
                    p["s1m"][field] = value
                    with self.assertRaisesRegex(MetadataError, field):
                        preflight(p)

    def test_no_silent_unit_conversion(self):
        for value in ("foot", "m", None):
            p = fixture()
            p["s1m"]["elevation_unit"] = value
            with self.assertRaisesRegex(MetadataError, "elevation_unit"):
                preflight(p)

    def test_bytes_sha_and_product_identity_require_proof(self):
        for field, bad in (("sha256", "0" * 64), ("sha256", "BAD"),
                           ("byte_count", 0), ("byte_count", True),
                           ("asset_id", "https://example.org/file"),
                           ("dataset_id", "usgs.3dep.other"),
                           ("data_type", "first_floor_height")):
            with self.subTest(field=field):
                p = fixture()
                p["lidar"][field] = bad
                with self.assertRaises(MetadataError):
                    preflight(p)

    def test_temporal_quality_and_source_ids(self):
        p = fixture()
        p["s1m"]["source_vintage_end"] = "2017-01-01"
        with self.assertRaisesRegex(MetadataError, "inverted"):
            preflight(p)
        p = fixture()
        p["lidar"]["source_vintage_start"] = "2026-02-30"
        with self.assertRaisesRegex(MetadataError, "calendar"):
            preflight(p)
        for bad in ([], ["work.A", "work.A"], ["url/to/work.A"], [0]):
            with self.subTest(bad=bad):
                p = fixture()
                p["s1m"]["source_lidar_workunit_ids"] = bad
                with self.assertRaisesRegex(MetadataError, "source_lidar_workunit_ids"):
                    preflight(p)

    def test_no_coordinates_urls_or_unknown_receipt_fields(self):
        for extra in ("latitude", "longitude", "source_url", "customer_address"):
            p = fixture()
            p["s1m"][extra] = "secret"
            with self.assertRaisesRegex(MetadataError, "unreviewed"):
                preflight(p)
        p = fixture()
        del p["s1m"]["sha256"]
        with self.assertRaisesRegex(MetadataError, "unreviewed"):
            preflight(p)

    def test_determinism_order_and_extra_top_level_fields(self):
        first = fixture()
        second = deepcopy(first)
        second["s1m"]["source_lidar_workunit_ids"].reverse()
        self.assertEqual(preflight(first), preflight(second))
        second["model_input_admitted"] = True
        with self.assertRaisesRegex(MetadataError, "expected only"):
            preflight(second)


if __name__ == "__main__":
    unittest.main()
