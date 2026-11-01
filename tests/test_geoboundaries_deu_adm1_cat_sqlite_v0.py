# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only isolated CAT geography RTree point-join regression tests."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest

from research_runners.geoboundaries_deu_adm1_cat_sqlite_v0 import (
    CAT_APP_ID, CAT_SCHEMA_VERSION, ROOT, SpatialStageError,
    _check_destination, build_staging_from_bytes, lookup_admin1,
    open_cat_index,
)
from tests.test_geoboundaries_deu_adm1_original_geojson_v0 import (
    raw, valid_collection,
)

HAS_SHAPELY = importlib.util.find_spec("shapely") is not None


def make_db(parent: Path, doc: dict, name: str = "deu-adm1.cat.sqlite") -> Path:
    data = raw(doc)
    output = parent / name
    row = build_staging_from_bytes(
        data, expected_sha256=hashlib.sha256(data).hexdigest(),
        expected_size=len(data), output_path=output,
    )
    assert row["indexed_polygons"] == 16
    assert row["separate_cat_staging_file_created"] is True
    return output


class PathAndSchemaSafety(unittest.TestCase):
    def test_file_must_be_new_cat_specific_absolute_path_outside_checkout(self):
        for path in (
            Path("deu-adm1.cat.sqlite"),
            Path("/tmp/generic.sqlite"),
            ROOT / "cannot-write-in-git.cat.sqlite",
        ):
            with self.subTest(path=str(path)), self.assertRaises(SpatialStageError):
                _check_destination(path)

    def test_refuse_existing_file_before_build(self):
        with tempfile.TemporaryDirectory(prefix="oc-cat-stage-") as tmp:
            existing = Path(tmp) / "already.cat.sqlite"
            existing.write_bytes(b"DO NOT OVERWRITE")
            with self.assertRaises(SpatialStageError):
                _check_destination(existing)
            self.assertEqual(existing.read_bytes(), b"DO NOT OVERWRITE")

    def test_foreign_database_cannot_be_queried_as_cat(self):
        with tempfile.TemporaryDirectory(prefix="oc-cat-stage-") as tmp:
            file = Path(tmp) / "other.cat.sqlite"
            with sqlite3.connect(file) as conn:
                conn.execute("CREATE TABLE private_data (value TEXT)")
                conn.execute("INSERT INTO private_data VALUES ('DO NOT TOUCH')")
            with self.assertRaisesRegex(SpatialStageError, "not the reviewed"):
                open_cat_index(file)
            with sqlite3.connect(file) as conn:
                self.assertEqual(conn.execute("SELECT value FROM private_data").fetchone()[0],
                                 "DO NOT TOUCH")


@unittest.skipUnless(HAS_SHAPELY, "Spatial regression job installs reviewed Shapely")
class CatSpatialIndexTests(unittest.TestCase):
    def test_16_shapes_rtree_exact_query_and_source_provenance(self):
        with tempfile.TemporaryDirectory(prefix="oc-cat-stage-") as tmp:
            db = make_db(Path(tmp), valid_collection())
            with open_cat_index(db) as conn:
                self.assertEqual(conn.execute("PRAGMA application_id").fetchone()[0], CAT_APP_ID)
                self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], CAT_SCHEMA_VERSION)
                self.assertEqual(conn.execute("SELECT count(*) FROM admin1_polygon").fetchone()[0], 16)
                self.assertEqual(conn.execute("SELECT count(*) FROM admin1_bbox").fetchone()[0], 16)
                provenance = conn.execute(
                    "SELECT boundary_id, represented_year, original_license, status "
                    "FROM source_provenance"
                ).fetchone()
                self.assertEqual(provenance[0], "DEU-ADM1-10402087")
                self.assertEqual(provenance[1], 2021)
                self.assertIn("Attribution", provenance[2])
                self.assertEqual(provenance[3], "isolated_research_staging_not_model_admitted")
                match = lookup_admin1(conn, 6.25, 48.25)
                self.assertEqual(match["shape_id"], "synthetic-test-00")
                self.assertFalse(match["official_nuts_crosswalk_verified"])
                self.assertIsNone(lookup_admin1(conn, 20.0, 60.0))
                with self.assertRaises(sqlite3.OperationalError):
                    conn.execute("DELETE FROM admin1_polygon")

    def test_rtree_bbox_candidate_does_not_imply_polygon_containment(self):
        doc = valid_collection()
        doc["features"][0]["geometry"]["coordinates"] = [[
            [6.0, 48.0], [6.7, 48.0], [6.7, 48.2], [6.2, 48.2],
            [6.2, 48.7], [6.0, 48.7], [6.0, 48.0],
        ]]
        with tempfile.TemporaryDirectory(prefix="oc-cat-stage-") as tmp:
            db = make_db(Path(tmp), doc)
            with open_cat_index(db) as conn:
                self.assertIsNone(lookup_admin1(conn, 6.5, 48.5))
                self.assertEqual(lookup_admin1(conn, 6.1, 48.5)["shape_id"],
                                 "synthetic-test-00")

    def test_shared_boundary_is_ambiguous_not_assigned_arbitrarily(self):
        doc = valid_collection()
        doc["features"][1]["geometry"]["coordinates"] = [[
            [6.7, 48.0], [7.4, 48.0], [7.4, 48.7],
            [6.7, 48.7], [6.7, 48.0],
        ]]
        with tempfile.TemporaryDirectory(prefix="oc-cat-stage-") as tmp:
            db = make_db(Path(tmp), doc)
            with open_cat_index(db) as conn:
                with self.assertRaisesRegex(SpatialStageError, "several"):
                    lookup_admin1(conn, 6.7, 48.35)

    def test_invalid_point_input_is_refused(self):
        with tempfile.TemporaryDirectory(prefix="oc-cat-stage-") as tmp:
            db = make_db(Path(tmp), valid_collection())
            with open_cat_index(db) as conn:
                for point in ((float("nan"), 50.0), (12.0, float("inf")),
                              (181.0, 50.0), (12.0, -91.0), (True, 50.0)):
                    with self.subTest(point=point), self.assertRaises(SpatialStageError):
                        lookup_admin1(conn, *point)


if __name__ == "__main__":
    unittest.main()
