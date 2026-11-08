# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Entirely synthetic offline tests of the Polish original building window."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from urllib.parse import parse_qs, urlsplit

from scripts.probe_pl_egib_warsaw_building_window_v0 import (
    BuildingWindowError,
    CRS,
    _NoRedirect,
    inspect_original_geojson,
    request_url,
)

ROOT = Path(__file__).resolve().parents[1]


def fake_feature(num, *, x=636560, y=486560, has_floors=True):
    properties = {
        "ID_BUDYNKU": "SYNTHETIC-ID-" + str(num),
        "RODZAJ": "SYNTHETIC-TYPE",
        "KONDYGNACJE_NADZIEMNE": "2" if has_floors else None,
        "KONDYGNACJE_PODZIEMNE": None,
    }
    coordinates = [[[x, y], [x + 30, y], [x + 30, y + 30],
                    [x, y + 30], [x, y]]]
    return {"type": "Feature", "properties": properties,
            "geometry": {"type": "Polygon", "coordinates": coordinates}}


def fake_collection():
    return {
        "type": "FeatureCollection", "name": "budynki",
        "crs": {"type": "name", "properties": {"name": CRS}},
        "features": [fake_feature(1), fake_feature(2, x=636900, y=487300, has_floors=False)],
    }


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


class PolishBuildingWindowTests(unittest.TestCase):
    def test_fixed_2_feature_request_has_epsg_axis_order(self):
        url = request_url()
        parts = urlsplit(url)
        self.assertEqual(parts.scheme, "https")
        self.assertEqual(parts.hostname, "mapy.geoportal.gov.pl")
        args = parse_qs(parts.query)
        self.assertEqual(args["REQUEST"], ["GetFeature"])
        self.assertEqual(args["TYPENAMES"], ["ms:budynki"])
        self.assertEqual(args["COUNT"], ["2"])
        self.assertEqual(args["BBOX"],
                         ["486500,636500,487500,637500,EPSG:2180"])
        self.assertEqual(args["SRSNAME"], ["EPSG:2180"])
        self.assertEqual(args["OUTPUTFORMAT"], ["application/json"])

    def test_only_anonymized_original_receipt(self):
        sample = encoded(fake_collection())
        receipt = inspect_original_geojson(sample)
        self.assertEqual(receipt["verified_intersection_count"], 2)
        self.assertEqual(receipt["geometry_types_seen"], ["Polygon"])
        self.assertEqual(receipt["observed_nonempty_field_counts_sample_only"]
                         ["KONDYGNACJE_NADZIEMNE"], 1)
        self.assertEqual(receipt["observed_nonempty_field_counts_sample_only"]
                         ["ID_BUDYNKU"], 2)
        self.assertFalse(receipt["individual_building_ids_or_geometries_output"])
        self.assertFalse(receipt["model_input_admitted"])
        self.assertFalse(receipt["licensed_use_of_all_source_attributes_verified"])
        self.assertNotIn("SYNTHETIC-ID", str(receipt))
        self.assertNotIn("SYNTHETIC-TYPE", str(receipt))
        self.assertEqual(receipt, inspect_original_geojson(sample))

    def test_reject_axis_swapped_response_and_wrong_region(self):
        bad = fake_collection()
        for feature in bad["features"]:
            for pt in feature["geometry"]["coordinates"][0]:
                pt[0], pt[1] = pt[1], pt[0]
        with self.assertRaisesRegex(BuildingWindowError, "does not intersect"):
            inspect_original_geojson(encoded(bad))
        bad = fake_collection()
        bad["features"][0] = fake_feature(1, x=400000, y=500000)
        with self.assertRaisesRegex(BuildingWindowError, "does not intersect"):
            inspect_original_geojson(encoded(bad))

    def test_reject_bad_crs_wrong_layer_or_missing_id(self):
        for key in ("crs", "layer", "id"):
            sample = fake_collection()
            if key == "crs":
                sample["crs"]["properties"]["name"] = "urn:ogc:def:crs:EPSG::4326"
            elif key == "layer":
                sample["name"] = "dzialki"
            else:
                del sample["features"][0]["properties"]["ID_BUDYNKU"]
            with self.subTest(key=key), self.assertRaises(BuildingWindowError):
                inspect_original_geojson(encoded(sample))

    def test_reject_missing_zero_excessive_rows_and_malformed_geometry(self):
        cases = []
        empty = fake_collection()
        empty["features"] = []
        cases.append(empty)
        many = fake_collection()
        many["features"].append(fake_feature(3))
        cases.append(many)
        wrong = fake_collection()
        wrong["features"][0]["geometry"]["type"] = "Point"
        cases.append(wrong)
        not_closed = fake_collection()
        not_closed["features"][0]["geometry"]["coordinates"][0][-1] = [636560, 486561]
        cases.append(not_closed)
        degenerate = fake_collection()
        degenerate["features"][0]["geometry"]["coordinates"][0] = [[636500, 486500]] * 4
        cases.append(degenerate)
        for n, payload in enumerate(cases):
            with self.subTest(case=n), self.assertRaises(BuildingWindowError):
                inspect_original_geojson(encoded(payload))

    def test_reject_invalid_json_and_duplicate_object_keys(self):
        for raw in (b"", b"{", b'{"type":1,"type":2}',
                    b'{"type":NaN}', b"\xff" * 12, b"x" * (256 * 1024 + 1)):
            with self.subTest(payload=raw[:20]), self.assertRaises(BuildingWindowError):
                inspect_original_geojson(raw)

    def test_never_follow_redirect(self):
        with self.assertRaisesRegex(BuildingWindowError, "redirect"):
            _NoRedirect().redirect_request(
                None, None, 302, "Redirect", {},
                "https://mapy.geoportal.gov.pl/?REQUEST=GetFeature&COUNT=500")

    def test_offline_cli_does_not_emit_provider_rows_or_write_original(self):
        with TemporaryDirectory() as tmp:
            sample = Path(tmp) / "original.json"
            sample.write_bytes(encoded(fake_collection()))
            cmd = [sys.executable, "scripts/probe_pl_egib_warsaw_building_window_v0.py",
                   "--source-json", str(sample)]
            a = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True,
                               check=True, timeout=20)
            b = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True,
                               check=True, timeout=20)
            self.assertEqual(a.stdout, b.stdout)
            self.assertNotIn("SYNTHETIC-ID", a.stdout)
            self.assertIn('"model_input_admitted": false', a.stdout)
            self.assertIn('"verified_intersection_count": 2', a.stdout)
            self.assertEqual(json.loads(a.stdout)["original_response_bytes"],
                             sample.stat().st_size)
            wrong = subprocess.run(
                [sys.executable, cmd[1]], cwd=ROOT,
                text=True, capture_output=True, timeout=20)
            self.assertNotEqual(wrong.returncode, 0)


if __name__ == "__main__":
    unittest.main()
