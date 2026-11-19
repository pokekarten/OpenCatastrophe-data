# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic only: exact-version fail-close, topology and false-match negative cases."""
import copy
import unittest

from research_runners.grwl_riveratlas_synthetic_crosswalk_v0 import (
    CrosswalkError, SCHEMA, SRC_RECORDS, crosswalk, strict_object,
)


def fixture():
    return {
        "schema": SCHEMA,
        "synthetic_only": True,
        "coordinate_frame": "LOCAL_METRIC_SYNTHETIC",
        "grwl_release": "2018",
        "grwl_archive": SRC_RECORDS["2018"][1],
        "grwl_provider_md5": SRC_RECORDS["2018"][2],
        "grwl": [{"id": "g1", "wkt": "LINESTRING (0 0, 100 0)", "width_mean_m": 40.0, "lakeflag": 0}],
        "riveratlas": [{"id": "r1", "wkt": "LINESTRING (0 2, 100 2)"}],
    }


class CrosswalkTests(unittest.TestCase):
    def test_unique_one_to_one_candidate_with_no_admission(self):
        result = crosswalk(fixture())
        self.assertEqual(result["results"], [{"grwl_synthetic_id": "g1", "candidate_riveratlas_synthetic_ids": ["r1"], "status": "one_to_one_candidate_only"}])
        self.assertTrue(result["synthetic_only"])
        for k in ("model_input_approved", "original_source_bytes_observed", "source_file_sha256_verified", "scientific_validation_completed", "licensing_admitted", "real_world_geometry_processed", "neon_production_modified"):
            self.assertIs(result[k], False)

    def test_reverse_direction_is_accepted(self):
        x = fixture(); x["riveratlas"][0]["wkt"] = "LINESTRING (100 2, 0 2)"
        self.assertEqual(crosswalk(x)["results"][0]["status"], "one_to_one_candidate_only")

    def test_crossing_not_accepted(self):
        x = fixture(); x["riveratlas"][0]["wkt"] = "LINESTRING (50 -50, 50 50)"
        self.assertEqual(crosswalk(x)["results"][0]["status"], "no_spatial_candidate")

    def test_remote_line_not_accepted(self):
        x = fixture(); x["riveratlas"][0]["wkt"] = "LINESTRING (0 50, 100 50)"
        self.assertEqual(crosswalk(x)["results"][0]["status"], "no_spatial_candidate")

    def test_split_reach_not_forced(self):
        x = fixture(); x["riveratlas"] = [{"id": "r1", "wkt": "LINESTRING (0 2, 50 2)"}, {"id": "r2", "wkt": "LINESTRING (50 2, 100 2)"}]
        self.assertNotEqual(crosswalk(x)["results"][0]["status"], "one_to_one_candidate_only")

    def test_ambiguous_two_near_identical_riveratlas(self):
        x = fixture(); x["riveratlas"].append({"id": "r2", "wkt": "LINESTRING (0 3, 100 3)"})
        self.assertEqual(crosswalk(x)["results"][0]["status"], "ambiguous_do_not_join")

    def test_reverse_many_to_one_flagged(self):
        x = fixture(); x["grwl"].append({"id":"g2", "wkt":"LINESTRING (0 3,100 3)", "width_mean_m":35, "lakeflag":0})
        self.assertTrue(all(y["status"] == "ambiguous_do_not_join" for y in crosswalk(x)["results"]))

    def test_lakeflag_not_promoted_to_river(self):
        x=fixture();x["grwl"][0]["lakeflag"]=1
        self.assertEqual(crosswalk(x)["results"][0]["status"], "excluded_non_river")

    def test_archive_release_must_not_cross_mix(self):
        x=fixture();x["grwl_release"]="2026"
        with self.assertRaises(CrosswalkError):crosswalk(x)
        x["grwl_archive"], x["grwl_provider_md5"] = SRC_RECORDS["2026"][1:]
        self.assertEqual(crosswalk(x)["release_metadata_identity"]["zenodo_record"],"18624542")

    def test_non_synthetic_rejected(self):
        x=fixture();x["synthetic_only"]=False
        with self.assertRaises(CrosswalkError):crosswalk(x)

    def test_wgs84_rejected(self):
        x=fixture();x["coordinate_frame"]="EPSG:4326"
        with self.assertRaises(CrosswalkError):crosswalk(x)

    def test_unknown_fields_rejected(self):
        x=fixture();x["secret"]="foo"
        with self.assertRaises(CrosswalkError):crosswalk(x)

    def test_invalid_geometries_rejected(self):
        for geom in ("POINT(0 0)", "LINESTRING(0 0, 0 0)", "LINESTRING Z(0 0 5,100 0 5)","LINESTRING (0 0, 100000000 0)", "LINESTRING(0 0, abc)"):
            x=fixture();x["grwl"][0]["wkt"]=geom
            with self.subTest(geom=geom),self.assertRaises(CrosswalkError): crosswalk(x)

    def test_invalid_width_and_flag_rejected(self):
        for invalid in (-1, float("nan"),"40", True,0):
            x=fixture();x["grwl"][0]["width_mean_m"]=invalid
            with self.subTest(invalid=invalid),self.assertRaises(CrosswalkError):crosswalk(x)
        x=fixture();x["grwl"][0]["lakeflag"]=4
        with self.assertRaises(CrosswalkError):crosswalk(x)

    def test_duplicate_grwl_id_rejected(self):
        x=fixture();x["grwl"].append(copy.deepcopy(x["grwl"][0]))
        with self.assertRaises(CrosswalkError):crosswalk(x)

    def test_no_nan_json_constants_or_duplicate_keys(self):
        with self.assertRaises(CrosswalkError):strict_object([("schema","a"),("schema","b")])


if __name__ == "__main__":
    unittest.main()
