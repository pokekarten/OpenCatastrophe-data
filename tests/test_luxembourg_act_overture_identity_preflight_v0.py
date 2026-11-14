# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""All-synthetic ACT GeoBase / Overture national-grid candidate tests."""
import copy
import json
import unittest

from pyproj import Transformer
from shapely.geometry import Polygon, mapping
from shapely.ops import transform

from research_runners.luxembourg_act_overture_identity_preflight_v0 import (
    ACT_GPKG_SHA256, ACT_ZIP_SHA256, CandidateError, SCHEMA, compare
)

TO_WGS = Transformer.from_crs("EPSG:2169", "EPSG:4326", always_xy=True)
SOURCE_KEY = ("release/2026-10-21.0/theme=buildings/type=building/"
              "part-00226-f2e989f6-97e6-5afe-b3d2-cfd2e6228d37-c000.zstd.parquet")


def square(x=77240, y=75040, side=10):
    return Polygon([(x, y), (x + side, y), (x + side, y + side), (x, y + side)])


def geometry(polygon):
    return json.loads(json.dumps(mapping(polygon)))


def sample(act=None, overture=None):
    a = act if act is not None else square()
    b = overture if overture is not None else a
    return {
        "schema": SCHEMA, "act_release": "2026-10-01",
        "act_zip_sha256": ACT_ZIP_SHA256, "act_gpkg_sha256": ACT_GPKG_SHA256,
        "act_crs": "EPSG:2169", "overture_release": "2026-10-21.0",
        "overture_source_key": SOURCE_KEY, "overture_crs": "EPSG:4326",
        "act_buildings": [{"source_id": "ACT-SYNTH-1", "geometry": geometry(a)}],
        "overture_buildings": [{
            "gers_id": "fea28f69-7afa-460c-b270-61ef74cd340c",
            "source_families": ["synthetic"], "geometry": geometry(transform(TO_WGS.transform, b))
        }]
    }


def audit(data):
    return compare(data, local_sample_sha256="0" * 64)


class LuxembourgPairTests(unittest.TestCase):
    def test_identical_polygons_one_candidate(self):
        out = audit(sample())
        self.assertEqual(out["reciprocal_one_to_one_geometric_candidates"], 1)
        self.assertEqual(out["area_overlap_method"], "EPSG:2169_projected_planar_IoU")
        self.assertNotIn("ACT-SYNTH-1", str(out))

    def test_distant_buildings_do_not_join(self):
        out = audit(sample(overture=square(x=77290)))
        self.assertEqual(out["act_features_without_above_threshold_match_in_slice"], 1)

    def test_boundary_touch_suppresses_round_trip_numeric_sliver(self):
        out = audit(sample(overture=square(x=77250)))
        self.assertEqual(out["positive_area_overlap_pairs"], 0)

    def test_half_overlap_below_threshold(self):
        out = audit(sample(overture=square(x=77245)))
        self.assertEqual(out["reciprocal_one_to_one_geometric_candidates"], 0)

    def test_two_overture_features_for_one_act_quarantine(self):
        p = sample()
        extra = copy.deepcopy(p["overture_buildings"][0])
        extra["gers_id"] = "fae28f69-7afa-460c-b270-61ef74cd340c"
        p["overture_buildings"].append(extra)
        out = audit(p)
        self.assertEqual(out["ambiguous_act_features_quarantined"], 1)
        self.assertEqual(out["reciprocal_one_to_one_geometric_candidates"], 0)

    def test_two_act_features_for_one_overture_quarantine(self):
        p = sample()
        extra = copy.deepcopy(p["act_buildings"][0])
        extra["source_id"] = "ACT-SYNTH-2"
        p["act_buildings"].append(extra)
        out = audit(p)
        self.assertEqual(out["ambiguous_act_features_quarantined"], 2)
        self.assertEqual(out["reciprocal_one_to_one_geometric_candidates"], 0)

    def test_commercial_and_model_permissions_remain_false(self):
        result = audit(sample())
        for flag in (
            "source_coordinate_epoch_accuracy_verified", "overture_original_file_sha256_verified",
            "overture_gers_registry_membership_verified", "real_original_rows_verified_in_this_run",
            "source_license_and_derivative_use_approved", "geometries_admitted_to_insurance_db",
            "insured_value_inferred", "cat_model_input_approved"
        ):
            self.assertIs(result[flag], False)

    def test_reject_unpinned_release(self):
        p = sample()
        p["overture_release"] = "latest"
        with self.assertRaises(CandidateError):
            audit(p)

    def test_reject_act_zip_sha_mismatch(self):
        p = sample()
        p["act_zip_sha256"] = "0" * 64
        with self.assertRaises(CandidateError):
            audit(p)

    def test_reject_act_gpkg_sha_mismatch(self):
        p = sample()
        p["act_gpkg_sha256"] = "0" * 64
        with self.assertRaises(CandidateError):
            audit(p)

    def test_reject_wrong_overture_partition(self):
        p = sample()
        p["overture_source_key"] = SOURCE_KEY.replace("type=building/", "type=building_part/")
        with self.assertRaises(CandidateError):
            audit(p)

    def test_other_valid_overture_part_is_not_luxembourg_city_source(self):
        p = sample()
        p["overture_source_key"] = SOURCE_KEY.replace(
            "part-00226-f2e989f6-97e6-5afe-b3d2-cfd2e6228d37",
            "part-00000-85375c54-5dfb-57c7-b21d-8b5e5245ad06")
        with self.assertRaises(CandidateError):
            audit(p)

    def test_reject_impossible_act_coordinate(self):
        with self.assertRaises(CandidateError):
            audit(sample(act=square(x=772400)))

    def test_reject_geometry_outside_luxembourg(self):
        with self.assertRaises(CandidateError):
            audit(sample(act=square(x=70000, y=25000)))

    def test_reject_self_crossing_polygon(self):
        p = sample()
        p["act_buildings"][0]["geometry"] = {
            "type": "Polygon", "coordinates": [[
                [77240,75040], [77250,75050], [77240,75050],
                [77250,75040], [77240,75040]
            ]]
        }
        with self.assertRaises(CandidateError):
            audit(p)

    def test_reject_invalid_overture_uuid(self):
        p = sample()
        p["overture_buildings"][0]["gers_id"] = "not-a-uuid"
        with self.assertRaises(CandidateError):
            audit(p)

    def test_reject_duplicate_act_id(self):
        p = sample()
        p["act_buildings"].append(copy.deepcopy(p["act_buildings"][0]))
        with self.assertRaises(CandidateError):
            audit(p)

    def test_reject_insurer_data_in_source_contract(self):
        p = sample()
        p["tiv"] = 123
        with self.assertRaises(CandidateError):
            audit(p)

    def test_reject_unhashable_lineage(self):
        p = sample()
        p["overture_buildings"][0]["source_families"] = [{"dataset": "OSM"}]
        with self.assertRaises(CandidateError):
            audit(p)

    def test_reject_wrong_source_crs(self):
        p = sample()
        p["act_crs"] = "EPSG:4326"
        with self.assertRaises(CandidateError):
            audit(p)

    def test_reject_oversized_building(self):
        with self.assertRaises(CandidateError):
            audit(sample(act=square(side=1200)))

    def test_reject_nonfinite_coordinate(self):
        p = sample()
        p["act_buildings"][0]["geometry"]["coordinates"][0][0][0] = float("nan")
        with self.assertRaises(CandidateError):
            audit(p)

    def test_sample_not_global_or_country_wide_proof(self):
        out = audit(sample())
        self.assertEqual(out["act_source_features_in_local_sample"], 1)
        self.assertEqual(out["overture_features_in_local_sample"], 1)
        self.assertFalse(out["source_coordinate_epoch_accuracy_verified"])


if __name__ == "__main__":
    unittest.main()
