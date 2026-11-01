# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only spatial cell-index proof; source original bytes never needed."""
from __future__ import annotations

from copy import deepcopy
import math
import unittest

from scripts.worldcover_header_cell_index_v0 import (
    CellIndexBlocked, ORIGINAL_HEADER_SHA256, validate_source_header,
    wgs84_lonlat_to_cell,
)


def reviewed_receipt():
    """Reconstruct only metadata values from public frozen receipt, not provider bytes."""
    return {
        "profile": "oc-esa-worldcover-v200-tiff-header-v0",
        "source_id": "esa.worldcover.2021.v200",
        "tile_id": "N48E009",
        "sample_sha256": ORIGINAL_HEADER_SHA256,
        "sample_bytes": 4096,
        "geo_grid_verified_from_prefix_only": True,
        "geokey_geographic_crs_if_complete": 4326,
        "geokey_model_type_if_complete": 2,
        "geokey_raster_type_if_complete": 1,
        "header_tile_bounds_lonlat_if_verified": [9.0, 48.0, 12.0, 51.0],
        "image_width_if_inline": 36000,
        "image_length_if_inline": 36000,
        "tile_width_if_inline": 1024,
        "tile_length_if_inline": 1024,
        "pixel_scale_degrees_if_complete": [3.0 / 36000, 3.0 / 36000],
        "external_bytes_persisted": False,
        "raster_values_inspected": False,
        "model_input_approved": False,
        "full_original_sha256_verified": False,
    }


class WorldCoverCellIndexTests(unittest.TestCase):
    def test_metadata_identity_is_valid_without_original_raster(self):
        self.assertIsNone(validate_source_header(reviewed_receipt()))

    def test_wgs84_grid_corners_and_internal_tile_block(self):
        receipt = reviewed_receipt()
        first = wgs84_lonlat_to_cell(receipt, 9.0, 51.0)
        self.assertTrue(first["inside_verified_tile"])
        self.assertEqual((first["pixel_row"], first["pixel_column"]), (0, 0))
        self.assertEqual((first["internal_tile_row"], first["internal_tile_column"]), (0, 0))
        center = wgs84_lonlat_to_cell(receipt, 9.5, 50.5)
        self.assertEqual((center["pixel_row"], center["pixel_column"]), (6000, 6000))
        self.assertEqual((center["internal_tile_row"], center["internal_tile_column"]), (5, 5))
        self.assertEqual((center["row_within_internal_tile"], center["column_within_internal_tile"]), (880, 880))
        self.assertFalse(center["raster_pixel_value_retrieved"])
        self.assertFalse(center["model_input_approved"])

    def test_pixel_is_area_east_and_south_edges_are_exclusive(self):
        receipt = reviewed_receipt()
        for lon, lat in ((12.0, 50.0), (9.5, 48.0), (8.9, 50.0),
                         (9.5, 51.00001), (15.0, 49.0)):
            with self.subTest(lon=lon, lat=lat):
                out = wgs84_lonlat_to_cell(receipt, lon, lat)
                self.assertFalse(out["inside_verified_tile"])
                self.assertIsNone(out["pixel_row"])
                self.assertIsNone(out["pixel_column"])
        last = wgs84_lonlat_to_cell(receipt, 11.99999, 48.00001)
        self.assertTrue(last["inside_verified_tile"])
        self.assertEqual(last["pixel_row"], 35999)
        self.assertEqual(last["pixel_column"], 35999)

    def test_unverified_or_mutated_header_is_rejected_not_rounded(self):
        base = reviewed_receipt()
        cases = [
            ("sample_sha256", "0" * 64),
            ("source_id", "worldcover.v100"),
            ("tile_id", "N51E009"),
            ("geokey_geographic_crs_if_complete", 3857),
            ("geokey_model_type_if_complete", 1),
            ("geokey_raster_type_if_complete", 2),
            ("geo_grid_verified_from_prefix_only", False),
            ("header_tile_bounds_lonlat_if_verified", [9., 48., 12.1, 51.]),
            ("image_width_if_inline", 35999),
            ("tile_width_if_inline", 512),
            ("pixel_scale_degrees_if_complete", [0.0001, 0.0001]),
            ("model_input_approved", True),
            ("raster_values_inspected", True),
        ]
        for field, value in cases:
            with self.subTest(field=field):
                receipt = deepcopy(base)
                receipt[field] = value
                with self.assertRaises(CellIndexBlocked):
                    wgs84_lonlat_to_cell(receipt, 9.5, 50.5)

    def test_invalid_lat_lon_values_fail_closed(self):
        receipt = reviewed_receipt()
        for lon, lat in ((True, 50.), (float("nan"), 50.),
                         (float("inf"), 50.), (190., 50.), (9.5, 91.),
                         (9.5, None), ("9.5", 50.)):
            with self.subTest(lon=str(lon), lat=str(lat)):
                with self.assertRaises(CellIndexBlocked):
                    wgs84_lonlat_to_cell(receipt, lon, lat)


if __name__ == "__main__":
    unittest.main()
