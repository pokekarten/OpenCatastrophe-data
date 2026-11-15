# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic tests of an evidence-only three-case MAS-to-parent LEI SQL review.

Read-only: run the same SELECT statement under SQLite with PostgreSQL's
typed NULL casts normalised for portable synthetic fixtures.
"""
import sqlite3
from pathlib import Path
import unittest

SQL = (
    Path(__file__).resolve().parents[1]
    / "research_runners/sql/mas_three_verified_lei_branch_review_v0.sql"
).read_text(encoding="utf-8").replace("NULL::text", "NULL")

MAS = [
    ("other_001", "ALLIANZ SE, SINGAPORE BRANCH", "Reinsurer (Composite)",
     "529900K9B0N5BT694847", "Allianz SE"),
    ("other_010", "ALLIANZ GLOBAL CORPORATE & SPECIALTY SE SINGAPORE BRANCH",
     "Direct Insurer (General)", "F240A7PWJB2BLKELB442",
     "Allianz Global Corporate & Specialty SE"),
    ("other_006", "MUNCHENER RUCKVERSICHERUNGS-GESELLSCHAFT, SINGAPORE BRANCH",
     "Reinsurer (Composite)", "529900MUF4C20K50JS49",
     "Münchener Rückversicherungs-Gesellschaft Aktiengesellschaft in München"),
]


def synthetic_read(licence_bad=None, parent_bad=None, prelinked=None):
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute("ATTACH DATABASE ':memory:' AS entity")
    db.executescript("""
        CREATE TABLE entity.licence_observation(
            observation_id TEXT, feed_id TEXT, observed_record_key TEXT,
            listed_name TEXT, licence_class TEXT, jurisdiction TEXT,
            organization_id TEXT, identity_resolution_status TEXT,
            home_country TEXT
        );
        CREATE TABLE entity.organization(
            organization_id TEXT, legal_name TEXT, domicile_country TEXT,
            identity_status TEXT
        );
        CREATE TABLE entity.organization_identifier(
            organization_id TEXT, identifier_scheme TEXT, identifier_value TEXT,
            is_verified INTEGER
        );
    """)
    for idx, (key, listed, category, lei, parent) in enumerate(MAS):
        db.execute(
            "INSERT INTO entity.licence_observation VALUES (?,?,?,?,?,?,?,?,?)",
            (f"synthetic-observation-{idx}", "ffbk_mas_curated_20261030",
             key, listed,
             "Different licence" if key == licence_bad else category,
             "SG", "synthetic-prelinked" if key == prelinked else None,
             "unmatched", None),
        )
        db.execute(
            "INSERT INTO entity.organization VALUES (?,?,?,?)",
            (f"synthetic-parent-{idx}",
             "Wrong parent" if key == parent_bad else parent, "DE", "verified"),
        )
        db.execute(
            "INSERT INTO entity.organization_identifier VALUES (?,?,?,?)",
            (f"synthetic-parent-{idx}", "GLEIF_LEI", lei, 1),
        )
    try:
        return {
            row["mas_record_key"]: dict(row)
            for row in db.execute(SQL).fetchall()
        }
    finally:
        db.close()


class MASLEIParentCandidateTests(unittest.TestCase):
    def test_exact_synthetic_sources_are_three_non_admitted_candidates(self):
        rows = synthetic_read()
        self.assertEqual(set(rows), {"other_001", "other_006", "other_010"})
        for r in rows.values():
            self.assertEqual(r["mas_observation_eligible_for_review"], 1)
            self.assertEqual(r["parent_identity_independently_present"], 1)
            self.assertEqual(r["mas_home_country_not_overwritten"], 1)
            self.assertEqual(r["disposition"], "manual_branch_parent_identity_review_only")
            self.assertEqual(r["relationship_auto_created"], 0)
            self.assertEqual(r["new_cat_exposure_approved"], 0)
            self.assertEqual(r["original_branch_lei_currently_issued_claim"], 0)

    def test_allianz_commercial_branch_lei_has_distinct_lapsed_registration(self):
        row = synthetic_read()["other_010"]
        self.assertEqual(row["separate_branch_lei"], "984500D1360HXAUAEF86")
        self.assertEqual(row["separate_branch_register_id"], "T11FC0131K")
        self.assertEqual(row["branch_relationship_registration_state"], "LAPSED")
        self.assertEqual(row["expected_parent_lei"], "F240A7PWJB2BLKELB442")
        self.assertNotEqual(row["separate_branch_lei"], row["expected_parent_lei"])

    def test_wrong_mas_licence_detected_not_silently_promoted(self):
        rows = synthetic_read(licence_bad="other_006")
        self.assertEqual(rows["other_006"]["mas_observation_eligible_for_review"], 0)
        self.assertEqual(rows["other_001"]["mas_observation_eligible_for_review"], 1)

    def test_wrong_parent_legal_name_detected(self):
        rows = synthetic_read(parent_bad="other_001")
        self.assertEqual(rows["other_001"]["parent_identity_independently_present"], 0)
        self.assertEqual(rows["other_010"]["parent_identity_independently_present"], 1)

    def test_existing_legal_link_needs_a_separate_approval(self):
        rows = synthetic_read(prelinked="other_010")
        self.assertEqual(rows["other_010"]["mas_observation_eligible_for_review"], 0)
        self.assertEqual(rows["other_006"]["mas_observation_eligible_for_review"], 1)


if __name__ == "__main__":
    unittest.main()
