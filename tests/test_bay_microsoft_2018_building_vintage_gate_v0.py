# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline positive/negative metadata-only tests for Bay 2018 building sources."""

from __future__ import annotations

import copy
import unittest

from research_runners.bay_microsoft_2018_building_vintage_gate_v0 import (
    BuildingVintageGateError, BAY_ITEM, MS_COMMIT, MS_FLORIDA_DECLARED,
    MS_SOURCE_ZIP, audit_bay_current_footprints,
    audit_microsoft_2018_original_readme, bay_original_count_plan,
)

BAY_META = {
    "serviceItemId": BAY_ITEM,
    "name": "Building Footprints",
    "geometryType": "esriGeometryPolygon",
    "spatialReferenceLatestWkid": 2238,
    "isDataVersioned": False,
    "supportsHistoricMoment": False,
    "fields": ["objectid", "lastupdate", "create_date", "roof_type",
               "bldgheight", "numstories", "globalid"],
}

BAY_COUNTS = {
    "total": {"count": 117646},
    "lastupdate_null": {"count": 117500},
    "lastupdate_nonnull": {"count": 146},
    "lastupdate_before_event": {"count": 146},
    "create_date_before_event": {"count": 0},
}

MS_META = {
    "github_repository": "Microsoft/USBuildingFootprints",
    "pinned_commit": MS_COMMIT,
    "commit_date": "2018-10-09",
    "florida_original_release_url": MS_SOURCE_ZIP,
    "florida_readme_building_count": MS_FLORIDA_DECLARED,
    "readme_license": "ODbL-1.0",
    "license_file": "CC-BY-4.0",
    "original_zip_header_bytes_verified": False,
    "original_zip_whole_sha256_verified": False,
    "image_capture_vintage_per_building_verified": False,
}


class BayAndMicrosoftBuildingVintageTests(unittest.TestCase):
    def test_bay_live_117646_footprints_cannot_be_historicised(self):
        self.assertEqual(len(bay_original_count_plan()), 5)
        for query in bay_original_count_plan().values():
            self.assertEqual(set(query), {
                "where", "returnCountOnly", "returnGeometry", "f",
            })
            self.assertEqual(query["returnCountOnly"], "true")
            self.assertEqual(query["returnGeometry"], "false")
        result = audit_bay_current_footprints(BAY_META, BAY_COUNTS)
        self.assertEqual(result["current_source_building_polygon_feature_count"], 117646)
        self.assertEqual(result["lastupdate_null_count"], 117500)
        self.assertEqual(result["lastupdate_nonnull_count"], 146)
        self.assertEqual(result["lastupdate_before_hurricane_count"], 146)
        self.assertEqual(result["create_date_before_hurricane_count"], 0)
        for k in (
            "supports_historicMoment",
            "has_versioned_data",
            "feature_updated_before_event_proves_historical_shape",
            "precise_source_imagery_acquisition_vintage_proven",
            "pre_2018_geojson_building_snapshot_available",
            "individual_roof_geometry_processed",
            "model_input_admitted",
        ):
            self.assertFalse(result[k])
        self.assertNotIn("features", result)

    def test_2018_microsoft_commit_precedes_michael_but_no_raster_imagery_date(self):
        result = audit_microsoft_2018_original_readme(MS_META)
        self.assertTrue(result["repo_publication_before_hurricane"])
        self.assertTrue(result["historic_readme_and_license_file_disagree"])
        self.assertEqual(result["florida_readme_nominal_footprint_count"], 6903772)
        for flag in (
            "original_archive_byte_identity_verified",
            "exact_building_imagery_date_verified",
            "source_file_sha256_verified",
            "commercial_redistribution_rights_approved",
            "can_train_2018_damage_from_this_without_other_checks",
            "model_input_admitted",
        ):
            self.assertFalse(result[flag])

    def test_source_property_shape_and_timestamp_cannot_be_overridden(self):
        for key,val in (
            ("serviceItemId", "not-original"),
            ("name", "Parcels"),
            ("geometryType", "esriGeometryPoint"),
            ("spatialReferenceLatestWkid", 4326),
            ("isDataVersioned", True),
            ("supportsHistoricMoment", True),
            ("fields", ["objectid", "lastupdate", "create_date"]),
            ("fields", ["objectid", "lastupdate", "create_date",
                        "roof_type", "bldgheight", "numstories", ["name"]]),
        ):
            with self.subTest(k=key):
                with self.assertRaises(BuildingVintageGateError):
                    audit_bay_current_footprints({**BAY_META,key:val},BAY_COUNTS)

    def test_null_date_and_older_date_counts_are_only_stats_not_historical_shapes(self):
        for key,value in (
            ("total", {"count": 50}),
            ("lastupdate_null", {"count": 117501}),
            ("lastupdate_nonnull", {"count": -1}),
            ("lastupdate_nonnull", {"count": True}),
            ("lastupdate_nonnull", {"count": "146"}),
            ("create_date_before_event", {"count": 500000}),
            ("lastupdate_null", {"count": 1, "features": []}),
        ):
            with self.subTest(k=key):
                with self.assertRaises(BuildingVintageGateError):
                    audit_bay_current_footprints(BAY_META,{**BAY_COUNTS,key:value})
        with self.assertRaises(BuildingVintageGateError):
            audit_bay_current_footprints(BAY_META,{**BAY_COUNTS, "geometry": []})

    def test_microsoft_hist_release_fails_closed_on_license_or_fake_zip_access(self):
        for key,val in (
            ("pinned_commit", "master"),
            ("commit_date", "2018-10-11"),
            ("florida_original_release_url", "https://example.com"),
            ("florida_readme_building_count", "6903772"),
            ("florida_readme_building_count", True),
            ("readme_license", "CC-BY-4.0"),
            ("license_file", "ODbL-1.0"),
            ("original_zip_header_bytes_verified", True),
            ("original_zip_whole_sha256_verified", True),
            ("image_capture_vintage_per_building_verified", True),
        ):
            with self.subTest(k=key):
                with self.assertRaises(BuildingVintageGateError):
                    audit_microsoft_2018_original_readme({**MS_META,key:val})
        with self.assertRaises(BuildingVintageGateError):
            audit_microsoft_2018_original_readme({**MS_META,"owner": "private"})

    def test_no_feature_geometry_or_occupancy_claims(self):
        a=audit_bay_current_footprints(BAY_META,BAY_COUNTS)
        b=audit_microsoft_2018_original_readme(MS_META)
        for d in (a,b):
            self.assertFalse(d["model_input_admitted"])
            for k in ("geometry", "features", "owner", "address", "footprints"):
                self.assertNotIn(k,d)


if __name__ == "__main__":
    unittest.main()
