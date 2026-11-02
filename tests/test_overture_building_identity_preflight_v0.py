# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict synthetic-only tests of Overture footprint matching and non-admission."""
import copy
import tempfile
import unittest
from pathlib import Path
from scripts.overture_building_identity_preflight_v0 import CrosswalkError, SCHEMA, _read, crosswalk

RELEASE = "2026-10-21.0"


def square(x=10.0, y=50.0, size=.001):
    return {"type": "Polygon", "coordinates": [[[x,y],[x+size,y],[x+size,y+size],[x,y+size],[x,y]]]}


def base():
    return {"schema":SCHEMA,"overture_release":RELEASE,"geometry_crs":"EPSG:4326", "local_source":"cadastre",
            "local_buildings":[{"local_id":"BLD-1","source_vintage":"2026-10-21","geometry":square()}],
            "overture_buildings":[{"gers_id":"fea28f69-7afa-460c-b270-61ef74cd340c", "source_families":["OSM"], "geometry":square()}]}


class CrosswalkTests(unittest.TestCase):
    def test_candidate_but_no_model_admission(self):
        result = crosswalk(base(), expected_release=RELEASE)
        self.assertEqual(len(result["one_to_one_geometric_candidates"]), 1)
        self.assertEqual(result["one_to_one_geometric_candidates"][0]["overlap_score"], 1)
        for key in ("gers_registry_membership_verified", "geometry_crs_evidence_verified", "independent_validation_approved", "raw_data_import_authorized", "model_input_approved", "insured_value_estimated"):
            self.assertFalse(result[key])

    def test_detect_shared_lineage(self):
        payload=base();payload["local_source"]="OSM"
        self.assertTrue(crosswalk(payload,expected_release=RELEASE)["one_to_one_geometric_candidates"][0]["shared_upstream_possible"])

    def test_mismatched_release(self):
        payload=base();payload["overture_release"]="2026-09-01.0"
        with self.assertRaises(CrosswalkError): crosswalk(payload,expected_release=RELEASE)

    def test_reject_moving_release(self):
        with self.assertRaises(CrosswalkError): crosswalk(base(),expected_release="latest")

    def test_reject_extra_insurer_value_field(self):
        p=base();p["local_buildings"][0]["insured_value"]=123456
        with self.assertRaises(CrosswalkError): crosswalk(p,expected_release=RELEASE)

    def test_reject_duplicate_local_id(self):
        p=base();p["local_buildings"].append(copy.deepcopy(p["local_buildings"][0]))
        with self.assertRaises(CrosswalkError): crosswalk(p,expected_release=RELEASE)

    def test_reject_duplicate_overture_id(self):
        p=base();p["overture_buildings"].append(copy.deepcopy(p["overture_buildings"][0]))
        with self.assertRaises(CrosswalkError): crosswalk(p,expected_release=RELEASE)

    def test_ambiguous_one_local_two_overture(self):
        p=base();v=copy.deepcopy(p["overture_buildings"][0]);v["gers_id"]="fae28f69-7afa-460c-b270-61ef74cd340c";p["overture_buildings"].append(v)
        o=crosswalk(p,expected_release=RELEASE)
        self.assertEqual(o["ambiguous_local_ids"],["BLD-1"])
        self.assertFalse(o["one_to_one_geometric_candidates"])

    def test_ambiguous_two_local_one_overture(self):
        p=base();v=copy.deepcopy(p["local_buildings"][0]);v["local_id"]="BLD-2";p["local_buildings"].append(v)
        o=crosswalk(p,expected_release=RELEASE)
        self.assertEqual(o["ambiguous_local_ids"],["BLD-1","BLD-2"])

    def test_far_away_unmatched(self):
        p=base();p["overture_buildings"][0]["geometry"]=square(20,60)
        o=crosswalk(p,expected_release=RELEASE)
        self.assertEqual(o["unmatched_local_ids"],["BLD-1"])

    def test_reject_self_intersecting_polygon(self):
        p=base();p["overture_buildings"][0]["geometry"]={"type":"Polygon","coordinates":[[[0,0],[1,1],[0,1],[1,0],[0,0]]]}
        with self.assertRaises(CrosswalkError): crosswalk(p,expected_release=RELEASE)

    def test_reject_false_gers(self):
        p=base();p["overture_buildings"][0]["gers_id"]="not-real"
        with self.assertRaises(CrosswalkError): crosswalk(p,expected_release=RELEASE)

    def test_reject_coordinate_lat_outside(self):
        p=base();p["local_buildings"][0]["geometry"]=square(10,95)
        with self.assertRaises(CrosswalkError): crosswalk(p,expected_release=RELEASE)

    def test_reject_boolean_coordinate(self):
        p=base();p["local_buildings"][0]["geometry"]["coordinates"][0][0][0]=True
        with self.assertRaises(CrosswalkError): crosswalk(p,expected_release=RELEASE)

    def test_reject_non_epsg(self):
        p=base();p["geometry_crs"]="EPSG:3857"
        with self.assertRaises(CrosswalkError): crosswalk(p,expected_release=RELEASE)

    def test_reject_untrusted_registry_claim(self):
        p=base();p["gers_registry_membership_verified"]=True
        with self.assertRaises(CrosswalkError): crosswalk(p,expected_release=RELEASE)

    def test_reject_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"a.json";f.write_text('{"a":1,"a":2}')
            with self.assertRaises(CrosswalkError): _read(f)

    def test_reject_nan_json(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"a.json";f.write_text('{"a":NaN}')
            with self.assertRaises(CrosswalkError): _read(f)

    def test_reject_too_many(self):
        p=base();p["local_buildings"]*=101
        with self.assertRaises(CrosswalkError): crosswalk(p,expected_release=RELEASE)

    def test_reject_polygon_span(self):
        p=base();p["local_buildings"][0]["geometry"]=square(10,50,.5)
        with self.assertRaises(CrosswalkError): crosswalk(p,expected_release=RELEASE)


if __name__ == '__main__':
    unittest.main()
