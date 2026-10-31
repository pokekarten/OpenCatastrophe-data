# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests for GLEIF JSON:API source-identity and separate CAT DB."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from scripts.export_cat_source_registry_sqlite import materialize_source_catalog
from scripts.gleif_level1_insurer_identity_pilot import (
    API_BASE, GLEIFPilotError, PILOT_LEIS,
    ingest_verified_lei_pilot, parse_lei_response, valid_lei,
)


def payload(lei, name="Synthetic Holding Example", country="DE", registration_status="ISSUED"):
    return json.dumps({
        "meta": {"goldenCopy": {"publishDate": "2026-10-30T08:00:00Z"}},
        "data": {"id": lei, "type": "lei-records",
                 "attributes": {"lei": lei, "entity": {
                     "legalName": {"name": name}, "legalAddress": {"country": country},
                     "status": "ACTIVE"},
                     "registration": {"status": registration_status}}},
    }, separators=(",", ":")).encode("utf-8")


def example_source():
    return {
        "candidate_id": "test.insurance-source",
        "name": "Synthetic Market Data",
        "provider": "Synthetic",
        "categories": ["insurance"],
        "spatial_scope": "synthetic",
        "temporal_scope": "2026",
        "resolution_or_granularity": "synthetic",
        "potential_roles": ["entity_identity"],
        "authoritative_url": "https://example.org",
        "access_class_hint": "synthetic",
        "candidate_status": "evidence_checked",
        "rights_review_status": "not_reviewed",
        "scientific_review_status": "not_reviewed",
        "admission_status": "not_admitted",
        "note": "synthetic only",
    }


def build_db(root):
    land = root / "land"; land.mkdir()
    (land / "sources-example.json").write_text(json.dumps({
        "schema_version": "1.0.0",
        "purpose": "Non-admission discovery registry for synthetic tests",
        "review_date": "2026-10-31",
        "entries": [example_source()],
    }) + "\n", encoding="utf-8")
    db = root / "cat.sqlite"
    materialize_source_catalog(db, land)
    return db


class GLEIFLevel1IdentityPilotTests(unittest.TestCase):
    def test_curated_lei_iso_checksum_and_evidence_identity(self):
        self.assertEqual(len(PILOT_LEIS), 3)
        for lei in PILOT_LEIS:
            with self.subTest(lei=lei):
                self.assertTrue(valid_lei(lei))
                self.assertEqual(parse_lei_response(payload(lei), lei)["source_api_url"], API_BASE + lei)
        self.assertFalse(valid_lei("529900K9B0N5BT694848"))
        self.assertFalse(valid_lei("529900-K9B0N5BT694847"))

    def test_one_signed_identity_is_not_portfolio_or_ownership(self):
        lei = sorted(PILOT_LEIS)[0]
        out = parse_lei_response(payload(lei, name="Test Legal Entity"), lei)
        self.assertEqual(out["legal_name"], "Test Legal Entity")
        self.assertEqual(out["source_license"], "CC0-1.0")
        self.assertEqual(out["relationship_status"], "not_fetched")
        self.assertEqual(out["insured_exposure_status"], "not_available")

    def test_rejects_mismatching_leis_and_missing_registration(self):
        a, b = sorted(PILOT_LEIS)[:2]
        with self.assertRaises(GLEIFPilotError):
            parse_lei_response(payload(a), b)
        with self.assertRaises(GLEIFPilotError):
            parse_lei_response(b'{"data":{"id":"BAD","type":"lei-records"}}', a)

    def test_rejects_duplicate_json_keys(self):
        a = sorted(PILOT_LEIS)[0]
        bad = (f'{{"data":{{"id":"{a}","id":"{a}"}}}}').encode()
        with self.assertRaises(GLEIFPilotError):
            parse_lei_response(bad, a)

    def test_rejects_invalid_country_or_source_bytes(self):
        lei = sorted(PILOT_LEIS)[0]
        for bad in [payload(lei, country="Germany"), payload(lei, country=""),
                    b"not-json", b"", b"x" * 2_000_001]:
            with self.subTest(bad_length=len(bad)):
                with self.assertRaises(GLEIFPilotError):
                    parse_lei_response(bad, lei)

    def test_sqlite_pilot_import_works_and_remains_cat_scoped(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            db = build_db(root)
            blobs = {lei: payload(lei, name=f"Synthetic {i}") for i,lei in enumerate(sorted(PILOT_LEIS))}
            out = ingest_verified_lei_pilot(db, blobs, "2026-10-31T20:00:00+00:00")
            self.assertEqual(out["lei_records_verified"], 3)
            self.assertFalse(out["parent_relationships_verified"])
            self.assertFalse(out["portfolio_exposure_created"])
            with sqlite3.connect(db) as con:
                self.assertEqual(con.execute("SELECT count(*) FROM cat_gleif_legal_entity").fetchone()[0], 3)
                self.assertEqual(con.execute("SELECT count(*) FROM cat_source_candidate").fetchone()[0], 1)
                self.assertEqual(con.execute("SELECT count(*) FROM cat_gleif_legal_entity WHERE source_license='CC0-1.0' AND relationship_status='not_fetched'").fetchone()[0], 3)
            again = ingest_verified_lei_pilot(db, blobs, "2026-10-31T20:01:00+00:00")
            self.assertEqual(again["lei_records_verified"], 3)
            with sqlite3.connect(db) as con:
                self.assertEqual(con.execute("SELECT count(*) FROM cat_gleif_legal_entity").fetchone()[0], 3)

    def test_rejects_unknown_database_without_writing(self):
        with TemporaryDirectory() as d:
            db = Path(d) / "cards.sqlite"
            with sqlite3.connect(db) as con:
                con.execute("CREATE TABLE cards (name TEXT NOT NULL)")
                con.execute("INSERT INTO cards VALUES ('Pikachu')")
            blobs = {lei: payload(lei) for lei in PILOT_LEIS}
            with self.assertRaises(GLEIFPilotError):
                ingest_verified_lei_pilot(db, blobs, "2026-10-31T20:00:00+00:00")
            with sqlite3.connect(db) as con:
                self.assertEqual(con.execute("SELECT name FROM cards").fetchone()[0], "Pikachu")
                self.assertFalse(con.execute("SELECT name FROM sqlite_master WHERE name='cat_gleif_legal_entity'").fetchone())

    def test_fails_without_all_pinned_records_or_bad_capture_time(self):
        with TemporaryDirectory() as d:
            db = build_db(Path(d))
            blobs = {lei: payload(lei) for lei in PILOT_LEIS}
            with self.assertRaises(GLEIFPilotError):
                ingest_verified_lei_pilot(db, dict(list(blobs.items())[:2]), "2026-10-31T20:00:00+00:00")
            with self.assertRaises(GLEIFPilotError):
                ingest_verified_lei_pilot(db, blobs, "yesterday")
            with sqlite3.connect(db) as con:
                self.assertFalse(con.execute("SELECT name FROM sqlite_master WHERE name='cat_gleif_legal_entity'").fetchone())


if __name__ == "__main__":
    unittest.main()
