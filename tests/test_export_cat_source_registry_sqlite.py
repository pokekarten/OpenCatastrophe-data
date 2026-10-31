# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests for the CAT-only source discovery SQLite materialization."""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from scripts.export_cat_source_registry_sqlite import (
    CAT_APP_ID, CAT_SCHEMA_VERSION, CATSourceDBError,
    materialize_source_catalog,
)
from scripts.source_landscape_contract import (
    DEFAULT_LANDSCAPE_DIR, LandscapeContractError, load_landscape_shards,
)


def example(candidate_id="example.authoritative-source.2026"):
    return {
        "candidate_id": candidate_id, "name": "Safe Synthetic Source",
        "provider": "Synthetic Publisher", "categories": ["insurance", "exposure"],
        "spatial_scope": "synthetic",
        "temporal_scope": "synthetic 2026",
        "resolution_or_granularity": "only synthetic examples",
        "potential_roles": ["market_benchmark", "validation"],
        "authoritative_url": "https://example.org/official-public-catalog",
        "access_class_hint": "metadata_only",
        "candidate_status": "evidence_checked",
        "rights_review_status": "not_reviewed",
        "scientific_review_status": "not_reviewed",
        "admission_status": "not_admitted",
        "note": "No third-party source bytes involved",
    }


def write_shard(root: Path, entries: list[dict], suffix="synthetic"):
    path = root / f"sources-{suffix}.json"
    path.write_text(json.dumps({
        "schema_version": "1.0.0",
        "purpose": "Non-admission discovery registry for synthetic offline tests",
        "review_date": "2026-10-31",
        "entries": entries,
    }) + "\n", encoding="utf-8")
    return path


class CATSourceRegistrySQLiteTests(unittest.TestCase):
    def test_synthetic_projection_normalized_and_not_admitted(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            landscape = root / "landscape"
            landscape.mkdir()
            write_shard(landscape, [example()])
            db = root / "cat_metadata.sqlite"
            result = materialize_source_catalog(db, landscape)
            self.assertEqual(result["source_candidates"], 1)
            self.assertEqual(result["category_assignments"], 2)
            self.assertEqual(result["role_assignments"], 2)
            self.assertFalse(result["model_source_admission"])
            with sqlite3.connect(db) as con:
                self.assertEqual(con.execute("PRAGMA application_id").fetchone()[0], CAT_APP_ID)
                self.assertEqual(con.execute("PRAGMA user_version").fetchone()[0], CAT_SCHEMA_VERSION)
                r = con.execute("SELECT candidate_id, admission_status, discovery_scope, canonical_sha256 FROM cat_source_candidate").fetchone()
                self.assertEqual(r[0], example()["candidate_id"])
                self.assertEqual(r[1], "not_admitted")
                self.assertEqual(r[2], "non_admission_discovery_only")
                self.assertEqual(len(r[3]), 64)
                self.assertEqual(con.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_refresh_is_idempotent_and_reconciles_removed_sources(self):
        with TemporaryDirectory() as d:
            root = Path(d); landscape = root / "landscape"; landscape.mkdir()
            path = write_shard(landscape, [example("example.first"), example("example.second")])
            db = root / "cat.db"
            self.assertEqual(materialize_source_catalog(db, landscape)["source_candidates"], 2)
            self.assertEqual(materialize_source_catalog(db, landscape)["source_candidates"], 2)
            path.unlink()
            write_shard(landscape, [example("example.second")])
            self.assertEqual(materialize_source_catalog(db, landscape)["source_candidates"], 1)
            with sqlite3.connect(db) as con:
                self.assertEqual(con.execute("SELECT candidate_id FROM cat_source_candidate").fetchone()[0], "example.second")
                self.assertEqual(con.execute("SELECT count(*) FROM cat_source_role").fetchone()[0], 2)

    def test_refuses_existing_unrelated_database_without_mutation(self):
        with TemporaryDirectory() as d:
            root = Path(d); land = root / "land"; land.mkdir()
            write_shard(land, [example()])
            db = root / "pokemon.sqlite"
            with sqlite3.connect(db) as con:
                con.execute("CREATE TABLE cards (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
                con.execute("INSERT INTO cards(name) VALUES ('Pikachu')")
            with self.assertRaises(CATSourceDBError):
                materialize_source_catalog(db, land)
            with sqlite3.connect(db) as con:
                self.assertEqual(con.execute("SELECT name FROM cards").fetchone()[0], "Pikachu")
                self.assertEqual(con.execute("SELECT count(*) FROM sqlite_master WHERE name='cat_source_candidate'").fetchone()[0], 0)

    def test_invalid_state_or_duplicate_ids_are_fail_closed_before_database(self):
        with TemporaryDirectory() as d:
            root = Path(d); land = root / "land"; land.mkdir()
            bad = example(); bad["admission_status"] = "approved_raw"
            write_shard(land, [bad])
            db = root / "cat.sqlite"
            with self.assertRaises(LandscapeContractError):
                materialize_source_catalog(db, land)
            self.assertFalse(db.exists())
            write_shard(land, [example()])
            write_shard(land, [example()], "duplicate")
            with self.assertRaises(LandscapeContractError):
                materialize_source_catalog(db, land)
            self.assertFalse(db.exists())

    def test_refuses_non_sqlite_or_empty_landscape(self):
        with TemporaryDirectory() as d:
            root = Path(d); land = root / "land"; land.mkdir()
            write_shard(land, [example()])
            with self.assertRaises(CATSourceDBError):
                materialize_source_catalog(root / "maybe.csv", land)
            with self.assertRaises(LandscapeContractError):
                materialize_source_catalog(root / "cat.sqlite", root / "missing-landscape")

    def test_full_public_registry_can_be_materialized_as_metadata_only(self):
        # All project source shards are validated before generating the SQLite projection.
        shards = load_landscape_shards(DEFAULT_LANDSCAPE_DIR)
        expected = sum(len(payload["entries"]) for _, payload in shards)
        with TemporaryDirectory() as d:
            db = Path(d) / "cat_registry.sqlite"
            result = materialize_source_catalog(db)
            self.assertEqual(result["source_candidates"], expected)
            self.assertEqual(result["source_shards"], len(shards))
            self.assertGreaterEqual(result["source_candidates"], 20)
            with sqlite3.connect(db) as con:
                self.assertEqual(con.execute("SELECT count(DISTINCT candidate_id) FROM cat_source_candidate").fetchone()[0], expected)
                self.assertEqual(con.execute("SELECT count(*) FROM cat_source_candidate WHERE admission_status <> 'not_admitted'").fetchone()[0], 0)
                self.assertTrue(all("github" not in row[0] or row[0].startswith("https://") for row in con.execute("SELECT authoritative_url FROM cat_source_candidate")))


if __name__ == "__main__":
    unittest.main()
