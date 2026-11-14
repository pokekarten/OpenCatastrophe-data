# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only regression of MAS detail-page label scopes against CAT-Neon.

The same SELECT-only SQL file is executed with SQLite ATTACH. No real MAS
source rows, names, original provider bytes, or Neon credentials are used.
"""
from pathlib import Path
import re
import sqlite3
import unittest

SQL = (
    Path(__file__).resolve().parents[1]
    / "research_runners/sql/mas_20_incorporation_scope_readonly_v0.sql"
).read_text(encoding="utf-8")

EXPECTED_KEYS = {
    "general_001", "general_002", "general_004", "general_005",
    "general_006", "general_007", "general_009", "general_011",
    "general_013", "general_016", "general_018", "general_021",
    "general_022", "other_001", "other_003", "other_004",
    "other_005", "other_006", "other_010", "other_011",
}
WITHOUT_EXPLICIT_BRANCH_NAME = {
    "general_006", "general_009", "general_013", "other_011",
}


def build_db(skip=None, corrupt_category=None, link_legal=None):
    db = sqlite3.connect(":memory:")
    db.execute("ATTACH DATABASE ':memory:' AS entity")
    db.executescript("""
        CREATE TABLE entity.licence_observation (
            observation_id TEXT,
            observed_record_key TEXT NOT NULL,
            feed_id TEXT NOT NULL,
            listed_name TEXT,
            licence_class TEXT,
            jurisdiction TEXT,
            home_country TEXT,
            organization_id TEXT,
            identity_resolution_status TEXT
        );
    """)
    entries = []
    for index, key in enumerate(sorted(EXPECTED_KEYS)):
        if key == skip:
            continue
        if key.startswith("general_"):
            category = "Reinsurer (General)"
        elif key == "other_010":
            category = "Direct Insurer (General)"
        elif key == "other_011":
            category = "Direct Insurer (Composite)"
        else:
            category = "Reinsurer (Composite)"
        if key == corrupt_category:
            category = "Direct Insurer (Life)"
        name = (
            f"Synthetic Test {index}"
            if key in WITHOUT_EXPLICIT_BRANCH_NAME
            else f"Synthetic Test {index} Singapore Branch"
        )
        entries.append((
            f"synthetic-id-{index}", key, "ffbk_mas_curated_20261030",
            name, category, "SG", None,
            "synthetic-organization-id" if key == link_legal else None,
            "unmatched",
        ))
    db.executemany(
        "INSERT INTO entity.licence_observation VALUES (?,?,?,?,?,?,?,?,?)",
        entries,
    )
    db.row_factory = sqlite3.Row
    return db


def run_sql(db):
    return dict(db.execute(SQL).fetchone())


class MASIncorporationScopeTests(unittest.TestCase):
    def test_20_explicit_source_keys_and_fixed_merchant_scope(self):
        self.assertEqual(len(EXPECTED_KEYS), 20)
        self.assertEqual(len(WITHOUT_EXPLICIT_BRANCH_NAME), 4)
        for key in EXPECTED_KEYS:
            with self.subTest(key=key):
                self.assertIn("'" + key + "'", SQL)
        self.assertIn("https://eservices.mas.gov.sg/fid/institution/detail/", SQL)
        self.assertIn("6354005OC5UTPXJQ9E28", SQL)

    def test_complete_synthetic_cohort_preserves_legal_identity_boundaries(self):
        db = build_db()
        try:
            result = run_sql(db)
        finally:
            db.close()
        self.assertEqual(result["source_detail_pages"], 20)
        self.assertEqual(result["matching_neon_observations"], 20)
        self.assertEqual(result["unique_mas_record_keys"], 20)
        self.assertEqual(result["missing_or_wrong_licence_category"], 0)
        self.assertEqual(result["research_rows_already_admitted_or_linked"], 0)
        self.assertEqual(result["neon_home_country_still_unknown"], 20)
        self.assertEqual(result["observation_names_explicit_sg_branch"], 16)
        self.assertEqual(result["mas_label_incorporated_outside_sg"], 18)
        self.assertEqual(result["mas_label_incorporated_in_sg"], 2)
        self.assertEqual(result["xl_re_europe_parent_branch_scope_conflicts"], 1)
        for key in (
            "parent_legal_entity_country_auto_applied",
            "new_organization_link_created",
            "insurer_exposure_verified",
            "model_input_approved",
        ):
            self.assertFalse(result[key])

    def test_missing_neon_observation_fails_completeness(self):
        db = build_db(skip="general_022")
        try:
            result = run_sql(db)
        finally:
            db.close()
        self.assertEqual(result["matching_neon_observations"], 19)
        self.assertEqual(result["missing_or_wrong_licence_category"], 1)

    def test_mismatched_regulatory_licence_is_not_silently_treated_as_match(self):
        db = build_db(corrupt_category="other_011")
        try:
            result = run_sql(db)
        finally:
            db.close()
        self.assertEqual(result["matching_neon_observations"], 20)
        self.assertEqual(result["missing_or_wrong_licence_category"], 1)

    def test_existing_legal_entity_link_requires_separate_review(self):
        db = build_db(link_legal="other_001")
        try:
            result = run_sql(db)
        finally:
            db.close()
        self.assertEqual(result["research_rows_already_admitted_or_linked"], 1)


if __name__ == "__main__":
    unittest.main()
