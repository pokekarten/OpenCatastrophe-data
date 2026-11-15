# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No provider bytes or real buildings: isolated synthetic CAT4/BLD4 provenance tests."""
from __future__ import annotations

from contextlib import closing
import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest

from scripts.verify_berlin_cat4_source_lineage_v0 import (
    BUILDING_BLD4_APP, BUILDING_PROFILE, CANONICAL_SHARD, CANDIDATE_ID,
    CATALOGUE, LineageError, PUBLISHER, RESEARCH_CAT4_APP,
    WFS_LAYER, WFS_ROOT, verify,
)


class BerlinResearchLineageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="oc-berlin-lineage-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.registry = self.root / "source-research.cat.sqlite"
        self.building = self.root / "building-stage.cat.sqlite"
        with closing(sqlite3.connect(self.registry)) as con:
            con.execute(f"PRAGMA application_id={RESEARCH_CAT4_APP}")
            con.execute("PRAGMA user_version=1")
            con.execute("""CREATE TABLE candidate (
                candidate_id TEXT PRIMARY KEY, provider TEXT, authoritative_url TEXT,
                canonical_shard TEXT, join_proven INTEGER, model_admitted INTEGER
            )""")
            con.execute("INSERT INTO candidate VALUES (?,?,?,?,0,0)",
                        (CANDIDATE_ID, PUBLISHER, CATALOGUE, CANONICAL_SHARD))
            con.commit()
        with closing(sqlite3.connect(self.building)) as con:
            con.execute(f"PRAGMA application_id={BUILDING_BLD4_APP}")
            con.execute("PRAGMA user_version=1")
            con.execute("""CREATE TABLE provenance (
                singleton INTEGER PRIMARY KEY, schema_id TEXT, source_service TEXT,
                source_feature_type TEXT, source_response_sha256 TEXT,
                retrieved_at_utc TEXT, source_rights TEXT, building_vintage TEXT,
                boundary_vintage INTEGER, region_source TEXT, model_admitted INTEGER
            )""")
            con.execute("""CREATE TABLE building_sample (
                ordinal INTEGER PRIMARY KEY,
                projected_epsg25833_geometry_wkb BLOB,
                footprint_area_m2 REAL, nuts1_region TEXT
            )""")
            con.execute("INSERT INTO provenance VALUES (1,?,?,?,?,?,?,?,?,?,0)", (
                BUILDING_PROFILE, WFS_ROOT, WFS_LAYER, "a" * 64,
                "2026-11-01T15:06:41+00:00", "dl-de-zero-2.0",
                "current_mutable_unknown_feature_date", 2021,
                "geoBoundaries 2021 + Eurostat NUTS2021 10M independently verified"
            ))
            con.execute("INSERT INTO building_sample VALUES (1,?,?,?)",
                        (bytes.fromhex("010300000000000000"), 400., "DE3"))
            con.commit()

    def change(self, path: Path, sql: str, params=()):
        with closing(sqlite3.connect(path)) as con:
            con.execute(sql, params)
            con.commit()

    def test_exact_metadata_identifiers_and_no_authority_uplift(self):
        before = tuple(hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (self.registry, self.building))
        result = verify(self.registry, self.building)
        self.assertEqual(result["candidate_id"], CANDIDATE_ID)
        self.assertEqual(result["staged_building_polygon_count"], 1)
        self.assertEqual(result["region_code"], "DE3")
        self.assertTrue(result["source_identity_metadata_consistent"])
        self.assertTrue(result["sqlite_application_ids_distinct"])
        for forbidden in (
            "physical_building_identity_proven", "independent_scientific_validation_proven",
            "insurer_exposure_or_tiv_inferred", "model_input_admitted",
            "source_bytes_revalidated_by_this_report", "database_modified",
        ):
            self.assertIs(result[forbidden], False)
        self.assertNotIn("projected_epsg25833_geometry_wkb", str(result))
        self.assertEqual(before, tuple(hashlib.sha256(p.read_bytes()).hexdigest()
                                       for p in (self.registry, self.building)))

    def rejected_mutation(self, path: Path, statement: str, expected: str, params=()):
        # A separate read-only SQLite connection must see committed mutations.
        original = path.read_bytes()
        try:
            self.change(path, statement, params)
            with self.assertRaisesRegex(LineageError, expected):
                verify(self.registry, self.building)
        finally:
            # Synthetic standalone fixture only. Restore before next case.
            path.write_bytes(original)

    def test_candidate_missing_or_swapped_provider_rejected(self):
        for statement in (
            "UPDATE candidate SET provider='Fake'",
            "UPDATE candidate SET authoritative_url='https://example.org/'",
            "UPDATE candidate SET canonical_shard='landscape/wrong.json'",
            "UPDATE candidate SET model_admitted=1",
            "UPDATE candidate SET join_proven=1",
            "DELETE FROM candidate",
        ):
            with self.subTest(sql=statement):
                self.rejected_mutation(self.registry, statement, "identity/admission")

    def test_research_db_cannot_be_confused_with_building_db(self):
        with self.assertRaisesRegex(LineageError, "distinct"):
            verify(self.registry, self.registry)
        with self.assertRaisesRegex(LineageError, "application identity"):
            verify(self.building, self.registry)
        with self.assertRaisesRegex(LineageError, "unsymlinked"):
            verify(self.registry, self.registry.with_name("other.cat.sqlite"))

    def test_provenance_mutations_fail_closed(self):
        mutations = [
            ("source_service", "https://example.org"),
            ("source_feature_type", "other:layer"),
            ("schema_id", "wrong-schema"),
            ("source_rights", "CC-BY-NC"),
            ("building_vintage", "2021"),
            ("boundary_vintage", 2024),
            ("region_source", "guessed-from-city-name"),
            ("model_admitted", 1),
        ]
        for key, bad in mutations:
            with self.subTest(field=key):
                self.rejected_mutation(
                    self.building, f"UPDATE provenance SET {key}=?",
                    "source/vintage/rights", (bad,),
                )

    def test_bad_sha_and_untrusted_time_rejected(self):
        for bad in ("xyz", "Z"*64, ""):
            with self.subTest(sha=bad):
                self.rejected_mutation(
                    self.building, "UPDATE provenance SET source_response_sha256=?",
                    "SHA-256", (bad,),
                )
        for bad in ("2026-11-01T15:06:41", "2026-11-01T16:06:41+01:00", "not-a-date"):
            with self.subTest(time=bad):
                self.rejected_mutation(
                    self.building, "UPDATE provenance SET retrieved_at_utc=?",
                    "UTC timestamp|not UTC", (bad,),
                )

    def test_unbounded_rows_or_wrong_region_not_represented_as_exposure(self):
        self.change(self.building, "UPDATE building_sample SET nuts1_region='DE2'")
        with self.assertRaisesRegex(LineageError, "rows/region/area"):
            verify(self.registry, self.building)
        self.change(self.building, "UPDATE building_sample SET nuts1_region='DE3'")
        for ordinal in range(2, 7):
            self.change(self.building, "INSERT INTO building_sample VALUES (?,?,?,?)",
                        (ordinal, b"0123456789", 500, "DE3"))
        with self.assertRaisesRegex(LineageError, "rows/region/area"):
            verify(self.registry, self.building)

    def test_zero_area_and_empty_geometry_rejected(self):
        self.change(self.building, "UPDATE building_sample SET footprint_area_m2=0")
        with self.assertRaisesRegex(LineageError, "rows/region/area"):
            verify(self.registry, self.building)
        self.change(self.building, "UPDATE building_sample SET footprint_area_m2=1, projected_epsg25833_geometry_wkb=x'01'")
        with self.assertRaisesRegex(LineageError, "rows/region/area"):
            verify(self.registry, self.building)

    def test_only_existing_regular_absolute_sqlite_files(self):
        with self.assertRaisesRegex(LineageError, "absolute"):
            verify(Path("relative.cat.sqlite"), self.building)
        with self.assertRaisesRegex(LineageError, "absolute"):
            verify(self.registry, Path("relative.cat.sqlite"))
        alias = self.root / "linked.cat.sqlite"
        alias.symlink_to(self.building)
        with self.assertRaisesRegex(LineageError, "unsymlinked"):
            verify(self.registry, alias)
        with self.assertRaisesRegex(LineageError, "unsymlinked"):
            verify(self.registry, self.root / "missing.cat.sqlite")


if __name__ == "__main__":
    unittest.main()
