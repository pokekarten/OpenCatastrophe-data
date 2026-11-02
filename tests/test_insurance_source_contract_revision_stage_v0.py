# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-only contract invariants; the real PostgreSQL guard is tested on isolated Neon."""
from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

SQL = (
    Path(__file__).resolve().parents[1]
    / "research_runners/sql/insurance_source_contract_revision_stage_v0.sql"
)


class SourceRevisionStageContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")

    def test_snapshot_and_post_insert_guards_are_inside_one_transaction(self):
        sql = self.sql
        self.assertEqual(sql.count("BEGIN;"), 1)
        self.assertEqual(sql.count("COMMIT;"), 1)
        self.assertLess(sql.index("BEGIN;"), sql.index("DO $snapshot_guard$"))
        self.assertLess(sql.index("DO $snapshot_guard$"), sql.index("CREATE TABLE"))
        self.assertLess(sql.index("CREATE TABLE"), sql.index("DO $schema_guard$"))
        self.assertLess(sql.index("DO $schema_guard$"), sql.index("INSERT INTO"))
        self.assertLess(sql.rindex("INSERT INTO"), sql.index("DO $revision_guard$"))
        self.assertLess(sql.index("DO $revision_guard$"), sql.index("COMMIT;"))
        self.assertIn("RAISE EXCEPTION 'Pinned source-registry snapshot drift", sql)
        self.assertIn("RAISE EXCEPTION 'Source revision evidence conflicts", sql)

    def test_pinned_entire_source_registry_sha256_before_any_ddl(self):
        # Source inventory audit is exact to every contract revision field,
        # not only the current row count or one WorldCover SHA.
        sql = self.sql
        guard = sql.split("DO $snapshot_guard$", 1)[1].split("$snapshot_guard$;", 1)[0]
        self.assertIn("sha256(convert_to(", guard)
        self.assertIn("string_agg(jsonb_build_object(", guard)
        self.assertIn("ORDER BY source_key", guard)
        for key in (
            "source_key", "git_commit_sha", "git_blob_sha", "git_path",
            "raw_metadata", "review_status",
        ):
            with self.subTest(key=key):
                self.assertIn(f"'{key}', {key}", guard)
        self.assertIn(
            "dce4e12c3aa9385c4a5b6805b1ad13682e2f7f91969eb1b7ed302c14c78fa822",
            guard,
        )
        self.assertLess(sql.index("DO $snapshot_guard$"), sql.index("CREATE TABLE"))

    def test_preexisting_permissive_schema_is_rejected_before_any_insert(self):
        sql = self.sql
        guard = sql.split("DO $schema_guard$", 1)[1].split("$schema_guard$;", 1)[0]
        self.assertIn("pg_catalog.pg_constraint", guard)
        self.assertIn("pg_catalog.pg_get_constraintdef", guard)
        self.assertIn("source_contract_revision_v0_pkey", guard)
        self.assertIn("source_contract_revision_v0_source_key_fkey", guard)
        self.assertIn("source_contract_revision_v0_raw_import_allowed_check", guard)
        self.assertIn("source_contract_revision_v0_model_input_approved_check", guard)
        self.assertIn("a.attnotnull IS TRUE", guard)
        self.assertIn("RAISE EXCEPTION 'Source revision table lacks", guard)

    def test_pinned_worldcover_metadata_compared_exactly_not_just_status(self):
        # SQL literals are self-authored evidence metadata, never provider data.
        literals = re.findall(r"'(\{\"access_id\":\"esa[.]worldcover[.]2021[.]v200\"[^']*\})'::jsonb", self.sql)
        self.assertEqual(len(literals), 2, "Require the same entire JSON in INSERT and guard")
        receipt, expected = (json.loads(raw) for raw in literals)
        self.assertEqual(receipt, expected)
        self.assertEqual(
            expected,
            {
                "access_id": "esa.worldcover.2021.v200",
                "status": "probe_ready",
                "provider": "ESA WorldCover / VITO",
                "source": "pinned_original_github_json",
                "raw_data_import": "prohibited",
                "model_admission": "prohibited",
                "bounded_one_block_canary": True,
            },
        )
        self.assertIn("AND contract_record='", self.sql)
        self.assertIn("AND git_path='access/esa.worldcover.2021.v200.json'", self.sql)
        self.assertIn("AND raw_import_allowed IS FALSE", self.sql)
        self.assertIn("AND model_input_approved IS FALSE", self.sql)

    def test_synthetic_metadata_tampering_breaks_exact_value_comparison(self):
        literals = re.findall(r"'(\{\"access_id\":\"esa[.]worldcover[.]2021[.]v200\"[^']*\})'::jsonb", self.sql)
        self.assertEqual(len(literals), 2)
        expected = json.loads(literals[1])
        for key, tamper in (
            ("raw_data_import", "allowed"),
            ("model_admission", "approved"),
            ("provider", "FORGED"),
            ("bounded_one_block_canary", False),
            ("source", "unverified_url"),
        ):
            with self.subTest(key=key):
                altered = dict(expected)
                altered[key] = tamper
                self.assertNotEqual(altered, expected)

    def test_append_only_and_non_admission_schema_constraints(self):
        self.assertIn("PRIMARY KEY(source_key,git_blob_sha)", self.sql)
        self.assertIn("ON CONFLICT DO NOTHING", self.sql)
        self.assertIn("CHECK (raw_import_allowed IS FALSE)", self.sql)
        self.assertIn("CHECK (model_input_approved IS FALSE)", self.sql)
        self.assertNotIn("UPDATE registry.source_record", self.sql)
        self.assertNotIn("DELETE FROM registry.source_record", self.sql)


if __name__ == "__main__":
    unittest.main()
