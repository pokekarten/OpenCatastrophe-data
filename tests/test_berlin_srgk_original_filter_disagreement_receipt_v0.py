# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-pinned Berlin WFS BBOX-hits versus FES-empty research-only receipt."""
from __future__ import annotations

import copy
from pathlib import Path
import re
import tomllib
import unittest

DOC = (Path(__file__).resolve().parents[1] / "docs/research" /
       "berlin-srgk-original-wfs-hits-fes-disagreement-20261101.toml")
SCHEMA_SHA = "8112bf8db14b7f3f1cb516717e128e0a450b643e645c29b1955e6c69bd57b87f"
HITS_SHA = "5d0bc8d8146d1debee8523867fcee89b96924d571b7a858e5034fff70f525e6c"
FES_SHA = "e2c6d7478391162bb8f89e2fb0c877013bac02fd12ff83b6084e14019d2b71a4"


def verify_receipt(d):
    expected = {
        "receipt_schema": "berlin-detailed-srgk-original-fes-empty-vs-bbox-hits-v0",
        "research_only": True,
        "original_source": "https://gdi.berlin.de/services/wfs/ua_srgk",
        "original_model_area_type": "ua_srgk:a_modellgebiete",
        "original_geometry_property": "geom",
        "frozen_pilot_bbox_epsg25833_m": [391700,5819950,391900,5820150],
        "original_schema_full_sha256": SCHEMA_SHA,
        "original_count_only_run_id": 41355919644,
        "original_count_only_main_commit": "eb1e37d3276b20a5587aab91ba6b4b4cdf0ba82e",
        "original_count_control_source_matches": 8,
        "original_count_pilot_bbox_source_matches": 1,
        "original_count_pilot_sha256": HITS_SHA,
        "original_count_pilot_bytes": 829,
        "original_fes_source_run_id": 41356416551,
        "original_fes_main_commit": "6dfecf2b12da1891e02dbde2ec01515aff6d788b",
        "original_fes_source_response_sha256": FES_SHA,
        "original_fes_source_response_bytes": 147,
        "original_fes_source_returned_features": 0,
        "original_fes_source_polygon_intersection_area_available": False,
        "original_fes_uses_geom_field_and_gml_envelope": True,
        "earlier_original_bbox_polygon_was_nonintersecting": True,
        "hits_and_fes_source_requests_not_atomic": True,
        "source_wfs_filter_semantics_or_geometry_reconciled": False,
        "pilot_model_area_coverage_proven": False,
        "pilot_no_model_area_coverage_proven": False,
        "pilot_has_no_flood_risk_proven": False,
        "actual_detailed_flood_depth_raster_found": False,
        "physical_water_depth_for_building_proven": False,
        "original_provider_xml_geojson_stored": False,
        "original_polygon_geometries_and_feature_ids_stored": False,
        "insurance_cat_model_input_admitted": False,
    }
    if type(d) is not dict:
        raise ValueError("invalid original-source receipt table")
    for name, value in expected.items():
        if type(d.get(name)) is not type(value) or d.get(name) != value:
            raise ValueError("original Berlin WFS mismatch receipt altered: "+name)
    for name in ("original_schema_full_sha256",
                 "original_count_pilot_sha256",
                 "original_fes_source_response_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", d[name]):
            raise ValueError("invalid source SHA")
    if d.get("original_count_only_run_url") != (
            "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41355919644"
        ) or d.get("original_fes_source_run_url") != (
            "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41356416551"):
        raise ValueError("source Actions evidence links changed")
    return {
        "original_count_bbox_hits": 1,
        "original_fes_geom_selected_features": 0,
        "pilot_model_area_coverage_proven": False,
        "no_model_area_or_dryness_proven": False,
        "original_source_payload_stored": False,
        "insurance_model_admitted": False,
    }


class BerlinOriginalFilterMismatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=tomllib.loads(DOC.read_text(encoding="utf-8"))

    def test_pinned_original_runs_and_negative_scientific_status(self):
        x=verify_receipt(self.original)
        self.assertEqual(x["original_count_bbox_hits"], 1)
        self.assertEqual(x["original_fes_geom_selected_features"], 0)
        self.assertFalse(x["pilot_model_area_coverage_proven"])
        self.assertFalse(x["no_model_area_or_dryness_proven"])
        self.assertFalse(x["insurance_model_admitted"])

    def test_cannot_fabricate_positive_intersection_or_zero_risk(self):
        for name in ("pilot_model_area_coverage_proven",
                     "pilot_no_model_area_coverage_proven",
                     "pilot_has_no_flood_risk_proven",
                     "source_wfs_filter_semantics_or_geometry_reconciled",
                     "insurance_cat_model_input_admitted"):
            with self.subTest(name=name):
                data=copy.deepcopy(self.original)
                data[name]=True
                with self.assertRaises(ValueError):
                    verify_receipt(data)

    def test_modifying_source_evidence_blocks_even_if_counts_are_still_conserved(self):
        for name,value in (
            ("original_count_pilot_bbox_source_matches",0),
            ("original_fes_source_returned_features",1),
            ("original_fes_source_response_sha256","0"*64),
            ("original_schema_full_sha256","1"*64),
            ("original_fes_source_run_id",1),
            ("original_fes_source_response_bytes",0),
            ("original_geometry_property","other"),
            ("original_count_only_main_commit","0"*40),
        ):
            with self.subTest(name=name):
                data=copy.deepcopy(self.original)
                data[name]=value
                with self.assertRaises(ValueError):
                    verify_receipt(data)

    def test_source_provenance_and_empty_response_not_geometries(self):
        self.assertTrue(self.original["hits_and_fes_source_requests_not_atomic"])
        self.assertFalse(self.original["original_provider_xml_geojson_stored"])
        self.assertFalse(self.original["original_polygon_geometries_and_feature_ids_stored"])
        self.assertIsInstance(self.original["interpretation"],str)
        self.assertIn("zero geometries",self.original["interpretation"])

    def test_toml_duplicate_source_keys_not_accepted(self):
        with self.assertRaises(tomllib.TOMLDecodeError):
            tomllib.loads("original_fes_source_returned_features=0\noriginal_fes_source_returned_features=1")


if __name__=="__main__":
    unittest.main()
