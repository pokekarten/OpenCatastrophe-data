# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only source ZIP/GPKG test; no original provider data."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile, ZIP_DEFLATED

from scripts.luxembourg_gpkg_zip_preflight_v0 import OriginalPreflightError, preflight

ROOT = Path(__file__).resolve().parents[1]


def synthetic_zip(root: Path, *, epsg=2169, geom="MULTIPOLYGON", appid=0x47504B47,
                  member="original.gpkg") -> Path:
    source = root / "fake.gpkg"
    if source.exists():
        source.unlink()
    with sqlite3.connect(source) as db:
        db.execute(f"PRAGMA application_id={appid}")
        db.executescript("""
            CREATE TABLE gpkg_spatial_ref_sys (
              srs_name TEXT, srs_id INTEGER PRIMARY KEY, organization TEXT,
              organization_coordsys_id INTEGER, definition TEXT, description TEXT);
            CREATE TABLE gpkg_contents (
              table_name TEXT PRIMARY KEY, data_type TEXT, identifier TEXT,
              description TEXT, last_change TEXT, min_x REAL, min_y REAL,
              max_x REAL, max_y REAL, srs_id INTEGER);
            CREATE TABLE gpkg_geometry_columns (
              table_name TEXT, column_name TEXT, geometry_type_name TEXT,
              srs_id INTEGER, z INTEGER, m INTEGER);
            CREATE TABLE "Synthetic Buildings" (fid INTEGER PRIMARY KEY,
              geom BLOB, private_building_reference TEXT);
        """)
        db.execute("INSERT INTO gpkg_spatial_ref_sys VALUES (?,?,?,?,?,?)",
                   ("fake", epsg, "EPSG", epsg, "synthetic", "none"))
        db.execute("INSERT INTO gpkg_contents VALUES (?,?,?,?,?,?,?,?,?,?)",
                   ("Synthetic Buildings", "features", "Synthetic Buildings", "",
                    "2026-03-17T00:00:00Z", 0, 0, 1, 1, epsg))
        db.execute("INSERT INTO gpkg_geometry_columns VALUES (?,?,?,?,?,?)",
                   ("Synthetic Buildings", "geom", geom, epsg, 0, 0))
        db.execute('INSERT INTO "Synthetic Buildings" VALUES (1,?,?)',
                   (b"SYNTHETIC", "PRIVATE-ID"))
    archive = root / "fake.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as z:
        z.writestr(member, source.read_bytes())
    return archive


class LuxembourgGPKGReceiptTests(unittest.TestCase):
    def setUp(self):
        t = TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.dir = Path(t.name)

    def test_metadata_sha_and_nonadmission(self):
        archive = synthetic_zip(self.dir)
        pin = hashlib.sha256(archive.read_bytes()).hexdigest()
        report = preflight(archive, expected_sha256=pin)
        self.assertEqual(report["zip_sha256"], pin)
        self.assertTrue(report["verified_against_independent_prior_sha256"])
        self.assertEqual(report["gpkg_metadata"]["layers"][0]["provider_feature_rows"], 1)
        self.assertEqual(report["gpkg_metadata"]["layers"][0]["declared_epsg"], 2169)
        self.assertFalse(report["model_input_admitted"])
        self.assertFalse(report["raw_building_records_exported"])
        self.assertNotIn("PRIVATE-ID", str(report))
        self.assertEqual(report, preflight(archive, expected_sha256=pin))

    def test_unpinned_and_wrong_hash(self):
        archive = synthetic_zip(self.dir)
        self.assertFalse(preflight(archive)["verified_against_independent_prior_sha256"])
        with self.assertRaisesRegex(OriginalPreflightError, "SHA-256 mismatch"):
            preflight(archive, expected_sha256="0" * 64)

    def test_reject_wrong_source_crs_geometry_and_application_id(self):
        for params in ({"epsg": 4326}, {"geom": "POINT"}, {"appid": 0}):
            with self.subTest(params=params):
                with self.assertRaises(OriginalPreflightError):
                    preflight(synthetic_zip(self.dir, **params))

    def test_zip_traversal_double_gpkg_and_non_sqlite(self):
        for name in ("../escape.gpkg", "/escape.gpkg", "a\\b.gpkg"):
            with self.subTest(name=name):
                with self.assertRaises(OriginalPreflightError):
                    preflight(synthetic_zip(self.dir, member=name))
        archive = synthetic_zip(self.dir)
        with ZipFile(archive, "a") as z:
            z.writestr("another.gpkg", (self.dir / "fake.gpkg").read_bytes())
        with self.assertRaisesRegex(OriginalPreflightError, "exactly one"):
            preflight(archive)
        with ZipFile(archive, "w") as z:
            z.writestr("invalid.gpkg", "not a database")
        with self.assertRaisesRegex(OriginalPreflightError, "not SQLite"):
            preflight(archive)

    def test_source_symlink_blocked(self):
        original = synthetic_zip(self.dir)
        alias = self.dir / "alias.zip"
        try:
            alias.symlink_to(original)
        except OSError:
            self.skipTest("symlinks unavailable")
        with self.assertRaisesRegex(OriginalPreflightError, "non-symlink"):
            preflight(alias)

    def test_cli_deterministic_and_no_provider_rows(self):
        archive = synthetic_zip(self.dir)
        args = [sys.executable, "scripts/luxembourg_gpkg_zip_preflight_v0.py",
                "--source-zip", str(archive)]
        one = subprocess.run(args, cwd=ROOT, text=True, capture_output=True,
                             timeout=30, check=True)
        two = subprocess.run(args, cwd=ROOT, text=True, capture_output=True,
                             timeout=30, check=True)
        self.assertEqual(one.stdout, two.stdout)
        self.assertNotIn("PRIVATE-ID", one.stdout)
        self.assertIn('"model_input_admitted": false', one.stdout)


if __name__ == "__main__":
    unittest.main()
