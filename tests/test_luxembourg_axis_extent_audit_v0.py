# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic aggregate-only EPSG:2169 axis-screen tests; no provider rows."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest

from research_runners.luxembourg_axis_extent_audit_v0 import (
    geographic_screen, audit_gpkg, audit_zip, AxisAuditError,
)


@unittest.skipIf(importlib.util.find_spec('pyproj') is None, 'Optional pinned spatial profile only')
class TestLuxembourgAxisScreen(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "synthetic.gpkg"

    def build_gpkg(self, extent=(48000., 56000., 106000., 140000.),
                   *, epsg=2169, geom="MULTIPOLYGON", appid=0x47504B47):
        con = sqlite3.connect(self.path)
        con.execute(f"PRAGMA application_id={appid}")
        con.execute("CREATE TABLE gpkg_contents (table_name TEXT, data_type TEXT, srs_id INTEGER, min_x REAL, min_y REAL, max_x REAL, max_y REAL)")
        con.execute("CREATE TABLE gpkg_geometry_columns (table_name TEXT, column_name TEXT, geometry_type_name TEXT, srs_id INTEGER)")
        con.execute("INSERT INTO gpkg_contents VALUES (?,?,?,?,?,?,?)", ("synthetic", "features", epsg, *extent))
        con.execute("INSERT INTO gpkg_geometry_columns VALUES (?,?,?,?)", ("synthetic", "geom", geom, epsg))
        con.commit()
        con.close()
        return hashlib.sha256(self.path.read_bytes()).hexdigest()

    def test_full_luxembourg_envelope_native_fits_and_swap_fails(self):
        result = geographic_screen((48000, 56000, 106000, 140000))
        self.assertEqual(result["screen_finding"], "native_only_plausible")
        self.assertFalse(result["coordinate_order_verified"])
        self.assertFalse(result["building_match_authorised"])

    def test_inverse_variant_is_flagged_without_auto_swap(self):
        result = geographic_screen((110000, 55000, 125000, 70000))
        self.assertEqual(result["screen_finding"], "swapped_only_plausible")
        self.assertFalse(result["coordinate_order_verified"])

    def test_ambiguous_extents_fail_to_prove_axis(self):
        result = geographic_screen((79000, 99000, 81000, 101000))
        self.assertEqual(result["screen_finding"], "ambiguous_both_plausible")
        self.assertFalse(result["coordinate_order_verified"])

    def test_nonsensical_extent_is_not_repaired(self):
        self.assertEqual(geographic_screen((0, 0, 1000, 1000))["screen_finding"], "neither_plausible")
        for values in ((1, 2, 1, 3), (0, 0, float("nan"), 100), ("a", 1, 2, 3)):
            with self.assertRaises(AxisAuditError):
                geographic_screen(values)

    def test_pin_and_only_metadata_read_for_valid_synthetic_gpkg(self):
        digest = self.build_gpkg()
        result = audit_gpkg(self.path, expected_gpkg_sha256=digest)
        self.assertEqual(result["raw_feature_rows_read"], 0)
        self.assertEqual(result["screen_finding"], "native_only_plausible")
        self.assertFalse(result["source_rights_and_science_approved"])
        self.assertEqual(result, audit_gpkg(self.path, expected_gpkg_sha256=digest))

    def test_wrong_hash_blocks(self):
        self.build_gpkg()
        with self.assertRaisesRegex(AxisAuditError, "hash"):
            audit_gpkg(self.path, expected_gpkg_sha256="0" * 64)

    def test_wrong_srs_blocks(self):
        digest = self.build_gpkg(epsg=3857)
        with self.assertRaisesRegex(AxisAuditError, "CRS"):
            audit_gpkg(self.path, expected_gpkg_sha256=digest)

    def test_nonpolygon_blocks(self):
        digest = self.build_gpkg(geom="POINT")
        with self.assertRaisesRegex(AxisAuditError, "polygon"):
            audit_gpkg(self.path, expected_gpkg_sha256=digest)

    def test_wrong_application_id_blocks(self):
        digest = self.build_gpkg(appid=0)
        with self.assertRaisesRegex(AxisAuditError, "application ID"):
            audit_gpkg(self.path, expected_gpkg_sha256=digest)

    def test_original_zip_must_pass_existing_preflight_first(self):
        with self.assertRaisesRegex(AxisAuditError, "preflight"):
            audit_zip(self.path)


if __name__ == "__main__":
    unittest.main()
