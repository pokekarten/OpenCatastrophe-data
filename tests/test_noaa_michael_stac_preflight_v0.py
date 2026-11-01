# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic NOAA Michael item-source, temporal, imagery and license negatives."""

from __future__ import annotations

from copy import deepcopy
import json
import unittest

from research_runners.noaa_michael_stac_preflight_v0 import (
    STACPreflightError, STAC_ROOT, preflight,
)


def fixture() -> dict:
    """Small source-shaped synthetic record; no original image is included."""
    tile = "20181011aC0855400w301330n"
    west, south, east, north = (-85.9001, 30.1999, -85.8749, 30.2251)
    return {
        "type": "Feature",
        "id": tile,
        "stac_version": "1.0.0",
        "bbox": [west, south, east, north],
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[west, south], [west, north], [east, north],
                             [east, south], [west, south]]],
        },
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
                "proj:transform": [west, 0.0000026980728051, 0, north, 0, -0.0000026980728051],
                "eo:bands": [
                    {"description": "red"}, {"description": "green"},
                    {"description": "blue"}, {"description": "alpha"},
                ],
                "raster:bands": [{"data_type": "uint8"} for _ in range(4)],
            },
        },
        "links": [
            {"rel": "self", "href": STAC_ROOT + "stac/" + tile + ".json"}
        ],
    }


class NOAAHurricaneMichaelSTACTests(unittest.TestCase):
    def test_positive_metadata_gate_does_not_admit_image_or_rights(self):
        output = preflight(fixture())
        self.assertTrue(output["source_item_metadata_valid"])
        self.assertEqual(output["tile_id"], "20181011aC0855400w301330n")
        self.assertEqual(output["raster_dimensions"], [9340, 9340])
        self.assertEqual(output["declared_crs"], "EPSG:4326")
        self.assertEqual(output["declared_acquisition_day"], "2018-10-11")
        self.assertEqual(output["inport_dataset_license_claim"], "CC0-1.0")
        self.assertEqual(output["stac_item_license_claim"], "NLPL")
        self.assertEqual(output["stac_license_spdx_full_name"], "No Limit Public License")
        self.assertTrue(output["stac_license_spdx_identifier_recognized"])
        self.assertTrue(output["source_license_identifiers_differ"])
        self.assertFalse(output["license_difference_is_proven_restriction"])
        self.assertFalse(output["asset_specific_licensing_review_completed"])
        for prop in ("exact_capture_time_verified", "pixel_coverage_verified",
                     "independent_of_fema_rs_labels_proven",
                     "source_image_bytes_downloaded_or_verified",
                     "automatic_fema_building_join_allowed",
                     "commercial_model_input_admitted"):
            self.assertFalse(output[prop])
        self.assertNotIn("https://", json.dumps(output))
        self.assertNotIn("bbox", json.dumps(output))

    def test_reproducible_and_unaffected_by_field_order(self):
        p = fixture()
        before = preflight(p)
        reverse = dict(reversed(list(p.items())))
        self.assertEqual(before, preflight(reverse))
        self.assertEqual(before, preflight(deepcopy(p)))

    def test_reject_wrong_item_identity_and_version(self):
        for field, val in (("id", "another-dataset"),
                           ("id", "20181010aC0855400w301330n"),
                           ("type", "Catalog"), ("stac_version", "1.1.0")):
            with self.subTest(field=field):
                p = fixture()
                p[field] = val
                with self.assertRaises(STACPreflightError):
                    preflight(p)

    def test_provider_license_identifier_change_is_not_silently_accepted(self):
        p = fixture()
        p["properties"]["license"] = "CC0-1.0"
        with self.assertRaisesRegex(STACPreflightError, "license"):
            preflight(p)

    def test_bad_date_shift_or_missing_utc_is_rejected(self):
        for bad in ("2018-10-10T00:00:00Z", "2018-10-11T00:00:00",
                    "2018-10-11T00:00:00+02:00", None):
            with self.subTest(datetime=bad):
                p = fixture()
                p["properties"]["datetime"] = bad
                with self.assertRaises(STACPreflightError):
                    preflight(p)

    def test_source_bounding_box_must_match_polygon(self):
        p = fixture()
        p["bbox"][0] -= 0.3
        with self.assertRaises(STACPreflightError):
            preflight(p)
        p = fixture()
        p["geometry"]["coordinates"] = []
        with self.assertRaisesRegex(STACPreflightError, "polygon"):
            preflight(p)
        p = fixture()
        p["geometry"]["coordinates"][0][-1] = [0, 0]
        with self.assertRaisesRegex(STACPreflightError, "closed"):
            preflight(p)

    def test_bad_source_asset_host_or_file_extension(self):
        p = fixture()
        tile = p["id"]
        p["assets"][tile]["href"] = "https://other.example/" + tile + ".tif"
        with self.assertRaisesRegex(STACPreflightError, "origin"):
            preflight(p)
        p = fixture()
        p["assets"][p["id"]]["href"] += "?download=everything"
        with self.assertRaises(STACPreflightError):
            preflight(p)

    def test_shape_transform_crs_mismatch(self):
        for prop, bad in (("proj:epsg", 32616), ("proj:shape", [2, 2]),
                          ("proj:shape", [30000, 30000]),
                          ("proj:transform", [-85.0, 0.0000026980728051, 0,
                                             30.2251, 0, -0.0000026980728051])):
            with self.subTest(prop=prop):
                p = fixture()
                p["assets"][p["id"]][prop] = bad
                with self.assertRaises(STACPreflightError):
                    preflight(p)

    def test_bad_color_and_raster_channel_definitions(self):
        p = fixture()
        p["assets"][p["id"]]["eo:bands"][-1]["description"] = "near-infrared"
        with self.assertRaisesRegex(STACPreflightError, "alpha"):
            preflight(p)
        p = fixture()
        p["assets"][p["id"]]["raster:bands"][1]["data_type"] = "float32"
        with self.assertRaisesRegex(STACPreflightError, "raster band"):
            preflight(p)

    def test_no_unreviewed_stac_origin_or_missing_mandatory_data(self):
        p = fixture()
        p["links"][0]["href"] = "https://example.org/fake.json"
        with self.assertRaisesRegex(STACPreflightError, "self-link"):
            preflight(p)
        p = fixture()
        del p["properties"]
        with self.assertRaises(STACPreflightError):
            preflight(p)


if __name__ == "__main__":
    unittest.main()
