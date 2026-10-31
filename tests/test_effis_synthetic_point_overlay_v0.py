# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests never access EFFIS network or user/insurer exposures."""
import json
import unittest

from scripts.effis_synthetic_point_overlay_v0 import (
    OverlayError, audit_synthetic_overlay, load_synthetic_sites, point_in_multipolygon,
)


def blob(value):
    return json.dumps(value, sort_keys=True).encode("utf-8")


def event():
    return {"count": 1, "results": [{
        "id": 42, "country": "NL", "firedate": "2026-08-25T13:01:00+02:00",
        "area_ha": "12",
        "shape": {"type": "MultiPolygon", "coordinates": [
            [
                [[0., 0.], [5., 0.], [5., 5.], [0., 5.], [0., 0.]],
                [[2., 2.], [3., 2.], [3., 3.], [2., 3.], [2., 2.]],
            ],
            [[[10., 10.], [11., 10.], [11., 11.], [10., 11.], [10., 10.]]]
        ]},
        "centroid": {"type": "Point", "coordinates": [1., 1.]},
        "bbox": [0., 0., 11., 11.]
    }]}


def point(name, x, y):
    return {"site_id": name, "longitude": x, "latitude": y}


def manifest(points):
    return {
        "schema_version": "oc-effis-synthetic-sites-v0",
        "crs": "OGC:CRS84",
        "synthetic_only": True,
        "sites": points
    }


class EFFISSyntheticPointOverlayTests(unittest.TestCase):
    def test_inside_outside_hole_second_polygon(self):
        result = audit_synthetic_overlay(
            blob(event()), 42, blob(manifest([
                point("Z_OUT", 20, 20),
                point("A_IN", 1, 1),
                point("B_HOLE", 2.5, 2.5),
                point("C_SECOND", 10.5, 10.5),
            ])))
        self.assertEqual(result["site_count"], 4)
        self.assertEqual(result["point_hits"], 2)
        self.assertEqual([x["within_observed_burnt_polygon"] for x in result["site_hits"]],
                         [True, False, True, False])
        for flag in ("site_coordinates_exported", "provider_geometry_exported",
                     "real_exposure_used", "vulnerability_applied",
                     "gross_loss_calculated", "insured_loss_calculated", "model_admitted"):
            self.assertFalse(result[flag])
        self.assertNotIn("coordinates", json.dumps(result))

    def test_source_identity_must_match(self):
        with self.assertRaises(ValueError):
            audit_synthetic_overlay(blob(event()), 999, blob(manifest([point("A", 1, 1)])))

    def test_outer_boundary_is_uncertain(self):
        with self.assertRaises(OverlayError):
            audit_synthetic_overlay(blob(event()), 42, blob(manifest([point("A", 0, 1)])))

    def test_hole_boundary_is_uncertain(self):
        with self.assertRaises(OverlayError):
            audit_synthetic_overlay(blob(event()), 42, blob(manifest([point("A", 2, 2.5)])))

    def test_missing_synthetic_declaration(self):
        data = manifest([point("A", 1, 1)])
        data["synthetic_only"] = False
        with self.assertRaises(OverlayError):
            load_synthetic_sites(blob(data))

    def test_rejects_insurer_fields(self):
        for key in ("cedant_id", "insured_tiv", "ground_up_loss"):
            data = point("A", 1, 1)
            data[key] = 123
            with self.subTest(field=key), self.assertRaises(OverlayError):
                load_synthetic_sites(blob(manifest([data])))

    def test_duplicate_site_id_rejected(self):
        with self.assertRaises(OverlayError):
            load_synthetic_sites(blob(manifest([point("A", 1, 1), point("A", 2, 2)])))

    def test_unknown_crs_rejected(self):
        data = manifest([point("A", 1, 1)])
        data["crs"] = "EPSG:3857"
        with self.assertRaises(OverlayError):
            load_synthetic_sites(blob(data))

    def test_wrong_coordinate_and_axis_rejected(self):
        with self.assertRaises(OverlayError):
            load_synthetic_sites(blob(manifest([point("A", 200, 1)])))

    def test_antimeridian_no_silent_shortcut(self):
        polygon = [[[179., 0.], [-179., 0.], [-179., 1.], [179., 1.], [179., 0.]]]
        with self.assertRaises(OverlayError):
            point_in_multipolygon((179.5, 0.5), [polygon])

    def test_zero_length_edges_rejected(self):
        polygon = [[[0., 0.], [0., 0.], [5., 0.], [5., 5.],
                    [0., 5.], [0., 0.]]]
        with self.assertRaises(OverlayError):
            point_in_multipolygon((1, 1), [polygon])

    def test_nonfinite_site_rejected(self):
        with self.assertRaises(OverlayError):
            load_synthetic_sites(blob(manifest([point("A", float("nan"), 1)])))

    def test_duplicate_json_key_rejected(self):
        raw = b'{"schema_version":"oc-effis-synthetic-sites-v0","crs":"OGC:CRS84","crs":"OGC:CRS84","synthetic_only":true,"sites":[]}'
        with self.assertRaises(OverlayError):
            load_synthetic_sites(raw)

    def test_source_geometry_must_be_multipolygon(self):
        obj = event()
        obj["results"][0]["shape"]["type"] = "Polygon"
        with self.assertRaises(ValueError):
            audit_synthetic_overlay(blob(obj), 42, blob(manifest([point("A", 1, 1)])))

    def test_missing_geometry_does_not_impute_zero(self):
        obj = event()
        obj["results"][0]["shape"]["coordinates"] = []
        with self.assertRaises(ValueError):
            audit_synthetic_overlay(blob(obj), 42, blob(manifest([point("A", 1, 1)])))


if __name__ == "__main__":
    unittest.main()
