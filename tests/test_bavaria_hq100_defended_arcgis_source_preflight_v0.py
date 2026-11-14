# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Only synthetic ArcGIS JSON samples; no government polygon coordinates stored."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research_runners import bavaria_hq100_defended_arcgis_source_preflight_v0 as m

ROOT = Path(__file__).resolve().parents[1]


def metadata(layer_id):
    fields = [{"name": name, "type": "esriFieldTypeString"}
              for name in m.CORE_FIELDS]
    if layer_id == 14:
        fields.append({"name": "sl_wtiefe", "type": "esriFieldTypeString"})
    return {
        "name": m.LAYER_IDS[layer_id],
        "type": "Feature Layer",
        "geometryType": "esriGeometryPolygon",
        "extent": {
            "xmin": 572000.0, "ymin": 5260000.0,
            "xmax": 842000.0, "ymax": 5580000.0,
            "spatialReference": {"wkid": 25832},
        },
        "fields": fields,
        "maxRecordCount": 2000,
        "advancedQueryCapabilities": {"supportsPagination": True},
    }


def sample_polygon(layer_id, xy=None):
    xy = xy or [11.51, 48.27]
    x, y = xy
    properties = {
        "sl_gew_nam": "Synthetic Test River",
        "geb_hq": "HQ 100",
        "erm_datum": "01.02.2026",
    }
    if layer_id == 14:
        properties["sl_wtiefe"] = "greater than 0 - 0.5 m"
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": properties,
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": [[[
                        [x, y], [x+0.001, y], [x+0.001, y+0.001],
                        [x, y],
                    ]]],
                },
            }
        ],
    }


def original_source_mock():
    return {
        **{f"metadata_{layer}": metadata(layer) for layer in m.LAYER_IDS},
        "count_10": {"count": 3},
        "count_14": {"count": 4},
        "count_8": {"count": 10},
        "row_count_10": {"count": 2},
        "row_count_14": {"count": 3},
        "row_count_8": {"count": 4},
        "sample_10": sample_polygon(10),
        "sample_14": sample_polygon(14),
        "attributes_10": {
            "features": [
                {"attributes": {
                    "webgisid": i+1, "geb_hq": "HQ 100",
                    "erm_datum": year,
                }}
                for i, year in enumerate(
                    ("01.01.2006", "15.08.2026", ""))
            ]
        },
    }


class BavariaDefendedHQ100SourceGateTests(unittest.TestCase):
    def test_correct_official_layer_identity_and_bbox(self):
        self.assertTrue(m.BASE_URL.endswith("wasser/naturgefahren_ftz/MapServer"))
        self.assertEqual(m.LAYER_IDS, {
            10: "hwgg_hq100", 14: "wt_hwgg_hq100", 8: "hwgf_hq100"
        })
        self.assertEqual(len(m.ROW5000_ENVELOPE), 4)
        self.assertEqual(len(m.EXPECTED_RESPONSE_FILES), 12)

    def test_all_synthetic_sources_valid_but_not_insurance_admitted(self):
        result = m.audit_original_service_responses(original_source_mock())
        self.assertEqual(result["source_provider_all_features_count"], {
            10: 3, 14: 4, 8: 10
        })
        self.assertEqual(result["row5000_envelope_intersection_feature_counts"], {
            10: 2, 14: 3, 8: 4
        })
        self.assertEqual(
            result["source_attributes_10_no_geometry"]["date_year_distribution"],
            {"2006": 1, "2026": 1}
        )
        self.assertEqual(
            result["source_attributes_10_no_geometry"]["missing_determination_dates"], 1)
        self.assertTrue(
            result["real_reprojected_polygon_samples"][14][
                "source_water_depth_class_is_categorical"])
        self.assertFalse(result["model_input_admitted"])
        self.assertFalse(result["defended_site_flood_depth_calculated"])
        self.assertFalse(result["defence_failure_probability_calibrated"])
        self.assertFalse(result["official_riverine_wri_depth_pixels_spatially_joined"])

    def test_wrong_polygon_name_or_native_crs_is_blocked(self):
        for mode in ("name", "geometryType", "crs", "pagination", "field"):
            with self.subTest(mode=mode):
                p = metadata(10)
                if mode == "name":
                    p["name"] = "wrong"
                elif mode == "geometryType":
                    p["geometryType"] = "esriGeometryPolyline"
                elif mode == "crs":
                    p["extent"]["spatialReference"]["wkid"] = 4326
                elif mode == "pagination":
                    p["advancedQueryCapabilities"]["supportsPagination"] = False
                else:
                    p["fields"] = p["fields"][1:]
                with self.assertRaises(m.DefendedArcgisGateError):
                    m.verify_layer_metadata(p, 10)

    def test_geojson_wrong_axis_unclosed_or_depth_missing_blocks(self):
        valid = m.verify_one_reprojected_provider_polygon(sample_polygon(10), 10)
        self.assertEqual(valid["sample_polygon_coordinate_pairs_verified"], 4)
        for problem in ("wrongtype", "unclosed", "wrongcoords", "nodepth"):
            with self.subTest(problem=problem):
                p = sample_polygon(14)
                f = p["features"][0]
                if problem == "wrongtype":
                    f["geometry"]["type"] = "Point"
                elif problem == "unclosed":
                    f["geometry"]["coordinates"][0][0][-1] = [11.49, 48.27]
                elif problem == "wrongcoords":
                    f["geometry"]["coordinates"][0][0][0] = [550000.0, 5340000.0]
                else:
                    del f["properties"]["sl_wtiefe"]
                with self.assertRaises(m.DefendedArcgisGateError):
                    m.verify_one_reprojected_provider_polygon(p, 14)

    def test_provider_counts_must_be_bounded_and_row_subset_consistent(self):
        for invalid in (-1, 0, "80", 500001, None):
            with self.subTest(value=invalid):
                with self.assertRaises(m.DefendedArcgisGateError):
                    m.validate_provider_count({"count": invalid})
        for invalid in (-1, "3", 11, None):
            with self.subTest(value=invalid):
                with self.assertRaises(m.DefendedArcgisGateError):
                    m.validate_row_envelope_count({"count": invalid}, 10)

    def test_duplicate_ids_truncation_and_bad_source_date_block(self):
        for problem in ("duplicate", "truncated", "bad_date", "bad_period"):
            with self.subTest(problem=problem):
                inp = original_source_mock()
                data = inp["attributes_10"]
                if problem == "duplicate":
                    data["features"][1]["attributes"]["webgisid"] = 1
                elif problem == "truncated":
                    data["features"].pop()
                elif problem == "bad_date":
                    data["features"][1]["attributes"]["erm_datum"] = "35.05.2027"
                else:
                    data["features"][2]["attributes"]["geb_hq"] = "HQextrem"
                with self.assertRaises(m.DefendedArcgisGateError):
                    m.audit_original_service_responses(inp)

    def test_wrong_original_JSON_and_missing_response_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "provider.json"
            for body in (b"", b"{this-is-not-json}", b'{"error":{"code":499}}'):
                file.write_bytes(body)
                with self.subTest(body=body):
                    with self.assertRaises(m.DefendedArcgisGateError):
                        m.read_original_json(file)
            with self.assertRaises(m.DefendedArcgisGateError):
                m.audit_original_service_responses({})

    def test_cli_preserves_original_files_and_does_not_use_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "provider"
            directory.mkdir()
            for filename in m.EXPECTED_RESPONSE_FILES.values():
                (directory / filename).write_text("not actual source; synthetic-only")
            original = directory / "layer-10-count.json"
            cmd = [
                sys.executable,
                str(ROOT /
                    "research_runners/bavaria_hq100_defended_arcgis_source_preflight_v0.py"),
                "--responses-dir", str(directory), "--out", str(original),
            ]
            p = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(p.returncode, 0)
            self.assertEqual(original.read_text(), "not actual source; synthetic-only")


if __name__ == "__main__":
    unittest.main()
