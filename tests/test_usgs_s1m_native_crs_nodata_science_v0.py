# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only USGS S1M CRS/NoData science checks; no original raster acquired."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from research_runners.usgs_s1m_native_raster_science_gate_v0 import (
    Blocked,
    PUBLISHED_S1M_HORIZONTAL_EPSG,
    PUBLISHED_S1M_VERTICAL_EPSG,
    PUBLISHED_S1M_NODATA,
    check_raster_science_profile,
)

ROOT = Path(__file__).resolve().parents[1]


def synthetic_profile() -> dict[str, object]:
    return {
        "product": "USGS 3DEP S1M",
        "raster_format": "COG GeoTIFF",
        "pixel_data_type": "Float32",
        "horizontal_epsg": 6350,
        "vertical_epsg": 5703,
        "geoid_model": "GEOID18",
        "horizontal_units": "m",
        "vertical_units": "m",
        "pixel_size_x_m": 1,
        "pixel_size_y_m": 1,
        "nodata_value": -999999,
    }


class S1MRasterScienceTests(unittest.TestCase):
    def test_declared_profile_not_original_or_model_admission(self):
        result = check_raster_science_profile(synthetic_profile())
        self.assertEqual(result["published_horizontal_epsg"], 6350)
        self.assertEqual(result["published_vertical_epsg"], 5703)
        self.assertEqual(result["published_nodata"], -999999)
        self.assertEqual(result["status"], "declared_profile_semantics_consistent_only")
        for field in (
            "original_tiff_bytes_verified", "source_lineage_gpkg_verified",
            "void_fill_and_blending_verified", "model_input_admitted",
        ):
            self.assertIs(result[field], False)

    def test_wrong_product_crs_datum_units_and_nodata_fail_closed(self):
        invalid = [
            ("product", "USGS 3DEP 1m legacy"),
            ("raster_format", "image/tiff"),
            ("pixel_data_type", "Int16"),
            ("horizontal_epsg", 26917),  # legacy/project UTM is not S1M Albers
            ("horizontal_epsg", True),
            ("vertical_epsg", 5702),
            ("vertical_epsg", "5703"),
            ("geoid_model", "GEOID12B"),
            ("horizontal_units", "ft"),
            ("vertical_units", "ft"),
            ("pixel_size_x_m", 0.5),
            ("pixel_size_y_m", float("nan")),
            ("pixel_size_y_m", float("inf")),
            ("pixel_size_x_m", 10 ** 1000),
            ("nodata_value", -32768),
            ("nodata_value", 10 ** 1000),
            ("nodata_value", 0),
            ("nodata_value", False),
            ("nodata_value", float("-inf")),
        ]
        for field, bad in invalid:
            with self.subTest(field=field, invalid=bad):
                profile = synthetic_profile()
                profile[field] = bad
                with self.assertRaises(Blocked):
                    check_raster_science_profile(profile)

    def test_missing_extra_and_non_object_profiles_fail_closed(self):
        profile = synthetic_profile()
        profile.pop("vertical_epsg")
        with self.assertRaises(Blocked):
            check_raster_science_profile(profile)
        profile = synthetic_profile()
        profile["unverified_model_approved"] = True
        with self.assertRaises(Blocked):
            check_raster_science_profile(profile)
        for bad in (None, [], "S1M", 1):
            with self.subTest(non_object=bad), self.assertRaises(Blocked):
                check_raster_science_profile(bad)

    def test_published_reference_matches_non_admitted_contract(self):
        contract = json.loads(
            (ROOT / "access/usgs.3dep.s1m.tnmaccess.json").read_text(encoding="utf-8")
        )
        semantics = contract["response_contract"]["scientific_semantics"]
        self.assertIn(f"EPSG:{PUBLISHED_S1M_HORIZONTAL_EPSG}", semantics)
        self.assertIn(f"EPSG:{PUBLISHED_S1M_VERTICAL_EPSG}", semantics)
        self.assertIn("GEOID18", semantics)
        self.assertIn(str(PUBLISHED_S1M_NODATA), semantics)
        self.assertIn("GeoPackage", semantics)
        self.assertEqual(contract["status"], "probe_ready")
        self.assertEqual(contract["probe_contract"]["mode"], "metadata_get")
        self.assertEqual(contract["access_scope"], ["metadata"])
        self.assertEqual(contract["rights_and_policy"]["redistribution_status"], "unknown")


if __name__ == "__main__":
    unittest.main()
