# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic checks: directory names are NOT unique legal entities."""
import sqlite3
from pathlib import Path
import unittest

SQL = (
    Path(__file__).resolve().parents[1]
    / "research_runners/sql/insurer_directory_identity_ambiguity_v0.sql"
).read_text(encoding="utf-8")


def synthetic_readback():
    with sqlite3.connect(":memory:") as db:
        db.execute("ATTACH DATABASE ':memory:' AS research")
        db.execute("ATTACH DATABASE ':memory:' AS entity")
        db.executescript("""
            CREATE TABLE research.insurer_directory_candidate_v0 (
                source_slug TEXT, country_slug TEXT, display_name TEXT
            );
            CREATE TABLE entity.organization (
                organization_id TEXT, legal_name TEXT, domicile_country TEXT
            );
            CREATE TABLE entity.licence_observation (
                organization_id TEXT
            );
            CREATE TABLE entity.regulator_registration_crosswalk (
                lei_verified_against_registration INTEGER
            );
        """)
        db.executemany(
            "INSERT INTO research.insurer_directory_candidate_v0 VALUES (?,?,?)",
            [
                ("fr-scor", "france", "SCOR SE"),
                ("uk-scor", "united-kingdom", "SCOR SE"),
                ("fr-scor-global", "france", "SCOR GLOBAL REINSURANCE France"),
                ("fr-scor-global-2", "france", "SCOR GLOBAL REINSURANCE France"),
                ("de-allianz", "germany", "Allianz SE"),
                ("de-allianz-2", "germany", "Allianz SE"),
            ],
        )
        db.executemany(
            "INSERT INTO entity.organization VALUES (?,?,?)",
            [
                ("fr01", "SCOR SE", "FR"),
                ("de01", "Allianz SE", "DE"),
                ("sg01", "Synthetic Re Pte. Ltd.", "SG"),
            ],
        )
        db.executemany(
            "INSERT INTO entity.licence_observation VALUES (?)",
            [("fr01",), (None,), (None,)],
        )
        db.executemany(
            "INSERT INTO entity.regulator_registration_crosswalk VALUES (?)",
            [(1,), (0,)],
        )
        db.row_factory = sqlite3.Row
        return dict(db.execute(SQL).fetchone())


class DirectoryIdentityAmbiguityTests(unittest.TestCase):
    def test_slugs_are_not_legal_entity_count(self):
        result = synthetic_readback()
        self.assertEqual(result["directory_entries"], 6)
        self.assertEqual(result["directory_distinct_slugs"], 6)
        self.assertEqual(result["directory_distinct_global_name_strings"], 3)
        self.assertEqual(result["distinct_market_name_strings"], 4)

    def test_same_market_duplicates_are_visible(self):
        result = synthetic_readback()
        self.assertEqual(result["repeat_market_name_groups"], 2)
        self.assertEqual(result["repeat_market_name_excess_entries"], 2)

    def test_country_listing_does_not_create_new_legal_entity(self):
        result = synthetic_readback()
        self.assertEqual(result["lexical_match_directory_rows"], 4)
        self.assertEqual(result["lexical_match_verified_organizations"], 2)
        self.assertEqual(result["lexical_home_market_match_rows_de_fr_sg"], 3)
        self.assertEqual(result["lexical_home_market_matched_orgs_de_fr_sg"], 2)

    def test_licence_and_verified_lei_gaps_stay_visible(self):
        result = synthetic_readback()
        self.assertEqual(result["regulator_licences_unlinked"], 2)
        self.assertEqual(result["registration_crosswalks_without_verified_lei"], 1)


if __name__ == "__main__":
    unittest.main()
