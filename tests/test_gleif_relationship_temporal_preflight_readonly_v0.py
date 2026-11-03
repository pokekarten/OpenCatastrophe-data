# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic/fail-closed guard for GLEIF Level-2 temporal research preflight.

The SQL was executed read-only against the explicitly selected Neon
insurance database. Tests are network-free and never open a database.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest

SQL = (
    Path(__file__).resolve().parents[1]
    / "research_runners/sql/gleif_relationship_temporal_preflight_readonly_v0.sql"
)
FORBIDDEN = re.compile(
    r"\b(?:INSERT|UPDATE|DELETE|UPSERT|MERGE|CREATE|ALTER|DROP|TRUNCATE|COPY|CALL|DO|GRANT|REVOKE)\b",
    re.IGNORECASE,
)
MANDATORY = (
    "entity.relationship_observation",
    "registry.repository_asset",
    "entity.organization_identifier",
    "entity.foreign_branch_observation",
    "registry.entity_feed",
    "r.child_identifier_scheme='GLEIF_LEI'",
    "r.source_asset_id IN (21,28)",
    "r.source_uri LIKE 'https://api.gleif.org/api/v1/lei-records/%'",
    "i.identifier_scheme='GLEIF_LEI' AND i.is_verified IS TRUE",
    "o.identity_status='verified'",
    "jsonb_array_elements(r.periods)",
    "'RELATIONSHIP_PERIOD'",
    "'ACCOUNTING_PERIOD'",
    "'DOCUMENT_FILING_PERIOD'",
    "n_relationship<>1 OR relationship_start IS NULL",
    "n_accounting<>1 OR accounting_start IS NULL",
    "accounting_end IS NULL OR accounting_end<accounting_start",
    "n_filing<>1 OR filing_start IS NULL",
    "branch_semantics='eu_inward_passport'",
    "branch_regulator_country='FR'",
    "verified_branch_head_leis=1 AND verified_parent_leis=1",
    "source_raw_import_allowed IS DISTINCT FROM TRUE",
    "gleif_automated_import_allowed IS DISTINCT FROM TRUE",
    "relation_kind='PARENT_REPORTING_EXCEPTION'",
    "NO_EDGE_REPORTED_EXCEPTION",
    "BRANCH_NOT_A_SECOND_LEGAL_INSURER",
    "REVIEW_LEGAL_EDGE_MISSING_COMPLETE_ACCOUNTING_PERIOD",
    "REVIEW_LEGAL_EDGE_EXACT_PERIODS_BUT_IMPORT_NOT_AUTHORIZED",
    "false AS safe_to_coerce_source_timestamp_into_date_only_effective_from",
    "false AS materialization_authorized",
    "false AS neon_written",
    "false AS nextgen_cat_exposure_admitted",
    "LIMIT 100",
)


def validate_readonly_temporal_contract(sql: str) -> None:
    # Remove SQL literals so 'original' sources or diagnostic string labels
    # cannot be confused with executable SQL verbs.
    code = re.sub(r"--[^\n]*", "", sql)
    code_no_literals = re.sub(r"'(?:''|[^'])*'", "''", code)
    if FORBIDDEN.search(code_no_literals):
        raise ValueError("SQL preflight unexpectedly performs a database write")
    if not re.search(r"^\s*WITH\b", code_no_literals, re.IGNORECASE):
        raise ValueError("SQL preflight must be a single CTE SELECT")
    if code_no_literals.count(";") != 1 or not code_no_literals.strip().endswith(";"):
        raise ValueError("SQL preflight must contain exactly one SELECT statement")
    if not re.search(r"\bSELECT\b", code_no_literals):
        raise ValueError("SQL preflight must return audit observations")
    if any(needle not in code for needle in MANDATORY):
        raise ValueError("Missing strict legal/temporal/rights/branch research gate")


class GleifTemporalPreflightTests(unittest.TestCase):
    def setUp(self):
        self.sql = SQL.read_text(encoding="utf-8")

    def test_original_query_still_fail_closed(self):
        validate_readonly_temporal_contract(self.sql)

    def test_period_type_must_not_be_replaced(self):
        mutated = self.sql.replace("'ACCOUNTING_PERIOD'", "'RELATIONSHIP_PERIOD'")
        with self.assertRaisesRegex(ValueError, "temporal"):
            validate_readonly_temporal_contract(mutated)

    def test_missing_accounting_period_must_remain_a_hold(self):
        mutated = self.sql.replace("n_accounting<>1 OR accounting_start IS NULL", "false")
        with self.assertRaisesRegex(ValueError, "temporal"):
            validate_readonly_temporal_contract(mutated)

    def test_source_write_rejected(self):
        mutated = self.sql + "\nINSERT INTO entity.organization_relationship DEFAULT VALUES;\n"
        with self.assertRaisesRegex(ValueError, "database write"):
            validate_readonly_temporal_contract(mutated)

    def test_multiple_statements_rejected(self):
        mutated = self.sql + "\nSELECT 1;\n"
        with self.assertRaisesRegex(ValueError, "exactly one"):
            validate_readonly_temporal_contract(mutated)

    def test_branch_identity_must_not_be_new_insurer(self):
        mutated = self.sql.replace("branch_semantics='eu_inward_passport'", "branch_semantics='unknown'")
        with self.assertRaisesRegex(ValueError, "branch"):
            validate_readonly_temporal_contract(mutated)

    def test_missing_permission_checks_rejected(self):
        mutated = self.sql.replace(
            "gleif_automated_import_allowed IS DISTINCT FROM TRUE", "false"
        )
        with self.assertRaisesRegex(ValueError, "rights"):
            validate_readonly_temporal_contract(mutated)

    def test_no_implicit_time_to_date_cast(self):
        mutated = self.sql.replace(
            "false AS safe_to_coerce_source_timestamp_into_date_only_effective_from",
            "true AS safe_to_coerce_source_timestamp_into_date_only_effective_from",
        )
        with self.assertRaisesRegex(ValueError, "temporal"):
            validate_readonly_temporal_contract(mutated)

    def test_no_model_approval(self):
        mutated = self.sql.replace(
            "false AS nextgen_cat_exposure_admitted",
            "true AS nextgen_cat_exposure_admitted",
        )
        with self.assertRaisesRegex(ValueError, "gate"):
            validate_readonly_temporal_contract(mutated)


if __name__ == "__main__":
    unittest.main()
