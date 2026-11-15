# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only ACT GeoBase 2026 building source-ID quality tests."""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from research_runners.luxembourg_geobase_2026_id_quality_v0 import (
    GeoBaseError, audit, profile,
)


def sample_database() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.execute('CREATE TABLE "Buildings_BU_Building" '
               '(id INTEGER PRIMARY KEY, geom BLOB, BU_BuildingID TEXT, Source TEXT)')
    db.executemany('INSERT INTO "Buildings_BU_Building" VALUES (?,?,?,?)', [
        (1, b"synthetic-polygon", "B1", "official"),
        (2, b"synthetic-polygon", "B1", "official"),
        (3, None, None, "historic"),
        (4, b"synthetic-polygon", "B4", ""),
    ])
    return db


class GeoBaseIDQualityTests(unittest.TestCase):
    def test_aggregate_id_and_source_quality_no_identifiers_exported(self):
        db = sample_database()
        self.addCleanup(db.close)
        report = profile(db, expected_rows=4)
        self.assertEqual(report, {
            "source_object_rows": 4,
            "sqlite_primary_id_unique": 4,
            "geometry_null_rows": 1,
            "building_id_blank_rows": 1,
            "building_id_nonblank_rows": 3,
            "building_id_distinct_nonblank": 2,
            "building_id_duplicate_excess_rows": 1,
            "source_label_blank_rows": 1,
            "source_label_nonblank_rows": 3,
            "source_label_distinct_nonblank": 2,
        })
        self.assertNotIn("B1", json.dumps(report))
        self.assertNotIn("official", json.dumps(report))

    def test_missing_original_field_fails_closed(self):
        db = sqlite3.connect(":memory:")
        self.addCleanup(db.close)
        db.execute('CREATE TABLE "Buildings_BU_Building" '
                   '(id INTEGER PRIMARY KEY, geom BLOB, BU_BuildingID TEXT)')
        with self.assertRaisesRegex(GeoBaseError, "schema drifted"):
            profile(db, expected_rows=0)

    def test_missing_original_table_fails_closed(self):
        db = sqlite3.connect(":memory:")
        self.addCleanup(db.close)
        with self.assertRaisesRegex(GeoBaseError, "feature layer missing"):
            profile(db, expected_rows=0)

    def test_wrong_total_feature_count_fails_closed(self):
        db = sample_database()
        self.addCleanup(db.close)
        with self.assertRaisesRegex(GeoBaseError, "feature count drifted"):
            profile(db, expected_rows=5)

    def test_case_and_whitespace_do_not_become_distinct_identities(self):
        db = sample_database()
        self.addCleanup(db.close)
        db.execute('UPDATE "Buildings_BU_Building" SET BU_BuildingID=" B4 " WHERE id=4')
        result = profile(db, expected_rows=4)
        self.assertEqual(result["building_id_distinct_nonblank"], 2)
        self.assertEqual(result["building_id_duplicate_excess_rows"], 1)

    def test_null_and_blank_labels_not_stored_in_output(self):
        db = sample_database()
        self.addCleanup(db.close)
        db.execute('UPDATE "Buildings_BU_Building" SET Source=NULL WHERE id=1')
        report = profile(db, expected_rows=4)
        self.assertEqual(report["source_label_blank_rows"], 2)
        self.assertEqual(report["source_label_distinct_nonblank"], 2)

    def test_untrusted_or_unpinned_original_cannot_be_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "fake.zip"
            raw.write_bytes(b"this is not the pinned original archive")
            with self.assertRaisesRegex(GeoBaseError, "SHA-256 mismatch"):
                audit(raw)

    def test_symlink_input_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / "fake.zip"
            original.write_bytes(b"not original")
            alias = Path(tmp) / "alias.zip"
            alias.symlink_to(original)
            with self.assertRaisesRegex(GeoBaseError, "regular local"):
                audit(alias)


if __name__ == "__main__":
    unittest.main()
