# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only exact-version Luxembourg ACT / GeoBase namespace diagnostics."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from research_runners import luxembourg_act_geobase_id_overlap_v0 as mod


def build(path: Path, table: str, field: str, ids: list, *, epsg=2169) -> None:
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA application_id=1196444487")  # GPKG
        db.executescript("""
        CREATE TABLE gpkg_contents(table_name TEXT,data_type TEXT,srs_id INTEGER);
        CREATE TABLE gpkg_geometry_columns(table_name TEXT,geometry_type_name TEXT);
        """)
        db.execute("INSERT INTO gpkg_contents VALUES(?,?,?)", (table, "features", epsg))
        db.execute("INSERT INTO gpkg_geometry_columns VALUES(?,?)", (table, "MULTIPOLYGON"))
        db.execute(f'CREATE TABLE "{table}" ("{field}" TEXT)')
        db.executemany(f'INSERT INTO "{table}" VALUES (?)', [(x,) for x in ids])


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class OriginalActIDOverlapTests(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.act = Path(d.name)/"act.gpkg"
        self.geo = Path(d.name)/"geobase.gpkg"
        build(self.act, mod.ACT_LAYER, mod.ACT_COL, ["SYN-ONE", "SYN-TWO", "SYN-TWO", None])
        build(self.geo, mod.GEOBASE_LAYER, mod.GEOBASE_COL, ["SYN-ONE", "SYN-THREE", " ", None])

    def run_report(self):
        with (patch.object(mod, "ACT_SHA", sha(self.act)),
              patch.object(mod, "GEOBASE_SHA", sha(self.geo)),
              patch.object(mod, "ACT_COUNT", 4),
              patch.object(mod, "GEOBASE_COUNT", 4)):
            return mod.inspect(self.act, self.geo, act_sha=sha(self.act),
                               geobase_sha=sha(self.geo))

    def test_exact_string_overlap_only_not_authorised_join(self):
        result = self.run_report()
        self.assertEqual(result["exact_normalized_string_id_intersection"], 1)
        self.assertEqual(result["act2023_only_distinct_ids"], 1)
        self.assertEqual(result["geobase2026_only_distinct_ids"], 1)
        self.assertEqual(result["act2023v2"]["duplicate_nonblank_rows"], 1)
        self.assertEqual(result["act2023v2"]["missing_or_blank_identifiers"], 1)
        self.assertEqual(result["geobase20261001"]["missing_or_blank_identifiers"], 2)
        self.assertFalse(result["id_namespace_equivalence_proven"])
        self.assertFalse(result["building_stock_change_inferred"])
        self.assertFalse(result["per_building_ids_or_crosswalk_exported"])
        self.assertNotIn("SYN-ONE", str(result))
        self.assertNotIn("SYN-THREE", str(result))

    def test_wrong_sha_blocks(self):
        with self.assertRaisesRegex(mod.ActIdentityError, "version pin"):
            mod.inspect(self.act, self.geo, act_sha="0"*64)

    def test_source_byte_drift_detected(self):
        with (patch.object(mod, "ACT_SHA", "0"*64),
              patch.object(mod, "GEOBASE_SHA", sha(self.geo))):
            with self.assertRaisesRegex(mod.ActIdentityError, "SHA-256"):
                mod.inspect(self.act, self.geo, act_sha="0"*64, geobase_sha=sha(self.geo))

    def test_geometry_crs_metadata_drift(self):
        self.geo.unlink()
        build(self.geo, mod.GEOBASE_LAYER, mod.GEOBASE_COL,
              ["SYN-ONE", "SYN-THREE", " ", None], epsg=4326)
        with self.assertRaisesRegex(mod.ActIdentityError, "EPSG"):
            self.run_report()

    def test_malformed_identifier_fails_closed(self):
        self.geo.unlink()
        build(self.geo, mod.GEOBASE_LAYER, mod.GEOBASE_COL,
              ["SYN-ONE", " SYN-WHITESPACE", " ", None])
        with self.assertRaisesRegex(mod.ActIdentityError, "noncanonical"):
            self.run_report()

    def test_population_drift_blocks(self):
        with (patch.object(mod, "ACT_SHA", sha(self.act)),
              patch.object(mod, "GEOBASE_SHA", sha(self.geo)),
              patch.object(mod, "ACT_COUNT", 10)):
            with self.assertRaisesRegex(mod.ActIdentityError, "population"):
                mod.inspect(self.act, self.geo, act_sha=sha(self.act),
                            geobase_sha=sha(self.geo))


if __name__ == "__main__":
    unittest.main()
