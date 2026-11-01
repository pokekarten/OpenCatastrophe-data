# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic geometry QA tests; no original source assets stored."""
from __future__ import annotations

import json
import sqlite3
import struct
import tempfile
from pathlib import Path
import unittest

from shapely.geometry import Polygon, MultiPolygon
from shapely import wkb

from research_runners.luxembourg_geobase_2026_geometry_quality_v0 import (
    _decode_gpkg, profile, audit, GeoBaseError
)


def gpkg(geom, *, epsg=2169, envelope=0):
    flag = 1 | (envelope << 1)
    coords = b""
    if envelope == 1:
        xmin, ymin, xmax, ymax = geom.bounds
        coords = struct.pack("<dddd", xmin, xmax, ymin, ymax)
    return b"GP" + bytes([0, flag]) + struct.pack("<i", epsg) + coords + wkb.dumps(geom)


def synthetic_db():
    db = sqlite3.connect(":memory:")
    db.execute('CREATE TABLE "Buildings_BU_Building" '
               '(id integer primary key, geom blob, BU_BuildingID text, Source text)')
    good = MultiPolygon([Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])])
    bad = Polygon([(0, 0), (2, 2), (0, 2), (2, 0)])
    db.executemany('INSERT INTO "Buildings_BU_Building" VALUES (?,?,?,?)', [
        (1, gpkg(good), "B-01", "official"),
        (2, gpkg(good, envelope=1), "B-02", "official"),
        (3, gpkg(bad), "B-03", "official"),
        (4, None, "B-04", "official"),
    ])
    return db


class LuxembourgGeoBaseFullGeometryTests(unittest.TestCase):
    def test_gpkg_endian_and_envelope_and_projected_area(self):
        geom = Polygon([(1, 2), (4, 2), (4, 6), (1, 6)])
        self.assertEqual(_decode_gpkg(gpkg(geom)).area, 12)
        self.assertEqual(_decode_gpkg(gpkg(geom, envelope=1)).area, 12)

    def test_full_scan_partitions_original_source_and_exports_only_aggregates(self):
        db = synthetic_db()
        self.addCleanup(db.close)
        result = profile(db, expected_rows=4)
        self.assertEqual(result["original_objects"], 4)
        self.assertEqual(result["polygon_valid_positive_area"], 2)
        self.assertEqual(result["invalid_topology"], 1)
        self.assertEqual(result["malformed_gpkg_geometry"], 1)
        self.assertEqual(result["valid_polygon_area_sum_projected_m2"], 200)
        self.assertTrue(result["source_rows_conserved"])
        self.assertFalse(result["building_geometry_model_input_approved"])
        self.assertFalse(result["all_source_geometries_parseable"])
        self.assertNotIn("B-01", json.dumps(result))
        self.assertNotIn("official", json.dumps(result))

    def test_untrusted_geom_flags_srs_and_size_fail(self):
        geom = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        for value in (None, b"fake", gpkg(geom, epsg=4326),
                      gpkg(geom)[:9], gpkg(geom, envelope=5),
                      b"GP" + bytes([0, 0xE1]) + gpkg(geom)[4:]):
            with self.subTest(value=value):
                with self.assertRaises(GeoBaseError):
                    _decode_gpkg(value)

    def test_missing_or_changed_population_fails_closed(self):
        db = synthetic_db()
        self.addCleanup(db.close)
        with self.assertRaisesRegex(GeoBaseError, "population changed"):
            profile(db, expected_rows=3)
        db.execute('DROP TABLE "Buildings_BU_Building"')
        with self.assertRaisesRegex(GeoBaseError, "Unexpected source layer"):
            profile(db, expected_rows=4)

    def test_original_archive_must_be_pinned_and_not_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            false = Path(tmp) / "fake.zip"
            false.write_bytes(b"not-publisher-source")
            with self.assertRaises(GeoBaseError):
                audit(false)
            alias = Path(tmp) / "shortcut.zip"
            alias.symlink_to(false)
            with self.assertRaises(GeoBaseError):
                audit(alias)


if __name__ == "__main__":
    unittest.main()
