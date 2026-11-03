# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline source-receipt contract for read-only GLEIF -> Neon group triage.

No network, licensed provider payload, database connection, or write. Actual
database execution is separately documented in the 2026-11-03 research receipt.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest

from scripts.gleif_level2_relationship_pilot import PILOT


SQL_PATH = (
    Path(__file__).resolve().parents[1]
    / "research_runners"
    / "sql"
    / "insurer_gleif_level2_original_receipt_neon_readonly_v0.sql"
)
SHA_BY_SUBJECT = {
    "529900UCN37OZCXGVW88": (
        "88a2204b3721a1916b36a1f0df390c8b7a5c0c1ca5551abb1194bd7e1017af9c",
        1295,
    ),
    "529900KIN5BE45V5KB18": (
        "2ecb0188bd2ef2ebb2f8cfeed757fffc17e29e81638b4910f1bde8eb12b89653",
        1295,
    ),
    "529900MUF4C20K50JS49": (
        "df25b9584023978cb55ac6386d71e35ecd32a0071940453992fed961425008de",
        531,
    ),
    "549300KCPG3666EE4546": (
        "a45bc039db8eae386f59bae7a570eacc562e6c4c14bb87882d85e44a20b2c84c",
        533,
    ),
}

RECEIPT_ROW = re.compile(
    r"\('([0-9A-Z]{20})',\s*(NULL|'[0-9A-Z]{20}'),\s*"
    r"'([A-Z_]+)',\s*(NULL|'[A-Z_]+'),\s*"
    r"'([0-9a-f]{64})',\s*([0-9]+),"
)


def inspect_contract(sql: str) -> dict:
    """Independently fail closed if a source row changes or a write sneaks in."""
    uncom = re.sub(r"--[^\n]*", "", sql)
    rows = RECEIPT_ROW.findall(uncom)
    if len(rows) != 4:
        raise ValueError("expected exactly four source-original receipt rows")
    known = set(PILOT)
    checked = set()
    link_count = 0
    exception_count = 0
    for child, parent_text, kind, exception_text, digest, byte_count in rows:
        if child in checked:
            raise ValueError("duplicate child LEI in fixed evidence batch")
        checked.add(child)
        if SHA_BY_SUBJECT.get(child) != (digest, int(byte_count)):
            raise ValueError("original source SHA-256 or byte count drift")
        if kind == "IS_DIRECTLY_CONSOLIDATED_BY":
            if parent_text == "NULL" or exception_text != "NULL":
                raise ValueError("invalid direct-parent evidence")
            parent = parent_text.strip("'")
            if (child, "direct-parent-relationship", parent) not in known:
                raise ValueError("unapproved direct accounting parent edge")
            link_count += 1
        elif kind == "DIRECT_ACCOUNTING_CONSOLIDATION_PARENT_EXCEPTION":
            if parent_text != "NULL" or exception_text == "NULL":
                raise ValueError("reporting exception must never imply a parent")
            reason = exception_text.strip("'")
            if (child, "direct-parent-reporting-exception", reason) not in known:
                raise ValueError("unapproved parent reporting exception")
            exception_count += 1
        else:
            raise ValueError("unknown GLEIF Level-2 source class")
    if set(SHA_BY_SUBJECT) != checked or link_count != 2 or exception_count != 2:
        raise ValueError("fixed verified accounting/exception cohort changed")
    if re.search(r"\b(?:INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE|GRANT|COPY|CALL|DO)\b", uncom, re.I):
        raise ValueError("SQL must not mutate the independent Neon database")
    if (
        "i.identifier_scheme = 'GLEIF_LEI' AND i.is_verified IS TRUE" not in uncom
        or "o.identity_status = 'verified'" not in uncom
        or "r.child_verified_matches <> 1 OR r.parent_verified_matches <> 1" not in uncom
        or "false AS materialisation_authorized" not in uncom
        or "false AS neon_written" not in uncom
        or "false AS model_input_approved" not in uncom
        or "BLOCKED_GLEIF_REPORTING_EXCEPTION_NO_PARENT_EDGE" not in uncom
    ):
        raise ValueError("missing strict verified-identity / exception / nonadmission gate")
    return {"links": link_count, "exceptions": exception_count, "subjects": checked}


class OriginalGleifReceiptNeonReadonlyTests(unittest.TestCase):
    def setUp(self):
        self.sql = SQL_PATH.read_text(encoding="utf-8")

    def test_approved_original_source_metadata_and_no_promotion(self):
        observed = inspect_contract(self.sql)
        self.assertEqual(observed["links"], 2)
        self.assertEqual(observed["exceptions"], 2)
        self.assertEqual(len(observed["subjects"]), 4)

    def test_sha_drift_blocks(self):
        mutated = self.sql.replace("88a2204b3721a1916b36a1f0df390c8b7a5c0c1ca5551abb1194bd7e1017af9c", "f" * 64)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            inspect_contract(mutated)

    def test_unreviewed_new_parent_blocks(self):
        mutated = self.sql.replace(
            "('529900UCN37OZCXGVW88','529900KIN5BE45V5KB18',",
            "('529900UCN37OZCXGVW88','529900MUF4C20K50JS49',",
        )
        with self.assertRaisesRegex(ValueError, "unapproved direct"):
            inspect_contract(mutated)

    def test_reporting_exception_cannot_turn_into_parent(self):
        mutated = self.sql.replace(
            "('549300KCPG3666EE4546',NULL,",
            "('549300KCPG3666EE4546','96950056ULJ4JI7V3752',",
        )
        with self.assertRaisesRegex(ValueError, "reporting exception"):
            inspect_contract(mutated)

    def test_neon_mutation_blocks(self):
        with self.assertRaisesRegex(ValueError, "must not mutate"):
            inspect_contract(self.sql + "\nINSERT INTO entity.organization_relationship VALUES (1);\n")

    def test_missing_unique_match_gate_blocks(self):
        mutated = self.sql.replace("r.child_verified_matches <> 1 OR r.parent_verified_matches <> 1", "FALSE")
        with self.assertRaisesRegex(ValueError, "missing strict"):
            inspect_contract(mutated)

    def test_duplicate_source_receipt_blocks(self):
        mutated = self.sql.replace(
            "('529900KIN5BE45V5KB18','5299006ZIILJ6VJVSJ32',",
            "('529900UCN37OZCXGVW88','5299006ZIILJ6VJVSJ32',",
        )
        with self.assertRaisesRegex(ValueError, "duplicate child"):
            inspect_contract(mutated)


if __name__ == "__main__":
    unittest.main()
