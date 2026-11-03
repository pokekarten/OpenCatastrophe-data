# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline fail-closed audit for the pinned 11-source GLEIF/Neon SELECT.

No external source bytes, browser calls or Neon credentials. The SQL query
was separately executed read-only against insurance-risk-core/main.
"""
from __future__ import annotations

import ast
from pathlib import Path
import re
import unittest


SOURCE = (
    Path(__file__).resolve().parents[1] /
    "research_runners/sql/gleif11_original_http_neon_branch_readonly_20261103.sql"
)
EXPECTED_SHA = {
    ("529900UCN37OZCXGVW88", "direct-parent-relationship"):
        "fb9787df6ecb6761ea28b35158f15fe7ac16b9be206a09bd4ef9e7eb37d38cf5",
    ("529900KIN5BE45V5KB18", "direct-parent-relationship"):
        "40d09bfeb68c37e27d1f78d07c9dc5a6e94148e7d03a998fdbd40f7a874b8499",
    ("5299006ZIILJ6VJVSJ32", "direct-parent-relationship"):
        "fdc53e938542980e3915784fe5c197c9644e090347bfae5aa2856cfe28547611",
    ("529900KIN5BE45V5KB18", "ultimate-parent-relationship"):
        "f6d69a570ade5258ed6c98ab78b36cab96af78040d037ac95be8d5868b5aea8b",
    ("529900UCN37OZCXGVW88", "ultimate-parent-relationship"):
        "b750d625adc41d665f17f6f6c4a4fe8a32c0e6774e17601757c8a8c7c5594c21",
    ("969500VV8Y4PQ7XJWE02", "direct-parent-relationship"):
        "b70f1f72dd6734e99001491d0899b8d4ee3877ee6a6d8be2e2d2998977db225d",
    ("969500VV8Y4PQ7XJWE02", "ultimate-parent-relationship"):
        "337388e1394038eb5a2c36b8aa3440add66da98f5030649ece387aef3e24c5eb",
    ("F240A7PWJB2BLKELB442", "direct-parent-relationship"):
        "5231655c385e79f8f0367f222f0041ca398ed26bf54d973e04acd7b06eb36ade",
    ("F240A7PWJB2BLKELB442", "ultimate-parent-relationship"):
        "ea55cc7b01b16102e29f625eaf9100a9f4cae68d16637c7b4898431733b54dd8",
    ("529900MUF4C20K50JS49", "direct-parent-reporting-exception"):
        "6af504fd9a84a42bffd4ba3f2be263821259a3dd08af79f194dcc76b73c50893",
    ("549300KCPG3666EE4546", "direct-parent-reporting-exception"):
        "55bb6867207c8b645af0ae43c0b3ee8a88754b0ae168adaf6807ceac215ff884",
}
KIND = {
    "direct-parent-relationship": ("DIRECT_ACCOUNTING_CONSOLIDATION", "ACTIVE"),
    "ultimate-parent-relationship": ("ULTIMATE_ACCOUNTING_CONSOLIDATION", "ACTIVE"),
    "direct-parent-reporting-exception": ("PARENT_REPORTING_EXCEPTION", "REPORTED"),
}


class EvidenceSourceContractError(ValueError):
    """The frozen official-source review lane changed without a new proof."""


def inspect_contract(sql: str) -> dict:
    body = re.sub(r"--[^\n]*", "", sql)
    parts = body.split(" VALUES\n", 1)
    if len(parts) != 2 or "\n), snapshot AS (" not in parts[1]:
        raise EvidenceSourceContractError("11 source receipt tuples not found")
    literal = parts[1].split("\n), snapshot AS (", 1)[0]
    if not re.fullmatch(r"[\s\(\),'A-Z0-9a-z.\-/:_&]+", literal):
        raise EvidenceSourceContractError("unexpected GLEIF source receipt grammar")
    try:
        rows = ast.literal_eval("[" + re.sub(r"\bNULL\b", "None", literal) + "]")
    except (ValueError, SyntaxError, MemoryError) as exc:
        raise EvidenceSourceContractError("invalid source-receipt tuples") from exc
    if len(rows) != 11 or any(len(row) != 9 for row in rows):
        raise EvidenceSourceContractError("expected eleven 9-field source receipts")
    found, edges, ultimates, exceptions = set(), {}, {}, set()
    for child, suffix, parent, kind, status, reason, digest, byte_length, period_start in rows:
        key = (child, suffix)
        if key in found or key not in EXPECTED_SHA:
            raise EvidenceSourceContractError("duplicate or unfamiliar source endpoint")
        found.add(key)
        if digest != EXPECTED_SHA[key] or not 0 < byte_length <= 2_000:
            raise EvidenceSourceContractError("GLEIF original source SHA or byte length changed")
        if (kind, status) != KIND[suffix]:
            raise EvidenceSourceContractError("GLEIF relationship kind or status changed")
        if suffix == "direct-parent-reporting-exception":
            if parent is not None or period_start is not None or reason not in (
                "NO_KNOWN_PERSON", "NON_CONSOLIDATING"
            ):
                raise EvidenceSourceContractError("GLEIF exception fabricated a parent")
            exceptions.add(child)
        else:
            if (not isinstance(parent, str) or len(parent) != 20 or
                    not isinstance(period_start, str) or not period_start.endswith("Z")
                    or reason is not None or parent == child):
                raise EvidenceSourceContractError("invalid GLEIF relationship and period")
            if suffix == "direct-parent-relationship":
                edges[child] = parent
            else:
                ultimates[child] = parent
    if set(EXPECTED_SHA) != found or len(edges) != 5 or len(ultimates) != 4 or len(exceptions) != 2:
        raise EvidenceSourceContractError("incomplete source-cohort composition")
    for child, ultimate in ultimates.items():
        seen, node = set(), child
        while node in edges:
            if node in seen:
                raise EvidenceSourceContractError("cyclic direct accounting consolidation")
            seen.add(node)
            node = edges[node]
        if node != ultimate:
            raise EvidenceSourceContractError("ultimate parent disagrees with direct-parent chain")
    clean = re.sub(r"'(?:''|[^'])*'", "''", body)
    if re.search(r"\b(?:INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE|COPY|DO|CALL|GRANT)\b",
                 clean, re.I):
        raise EvidenceSourceContractError("query is no longer read-only")
    required = (
        "entity.relationship_observation", "entity.foreign_branch_observation",
        "entity.organization_identifier", "registry.repository_asset",
        "registry.entity_feed", "source_asset_raw_import_allowed",
        "gleif_feed_automated_import_allowed", "child_identifier_scheme='GLEIF_LEI'",
        "source_uri=s.source_url", "o.identity_status='verified'",
        "relationship_period_match", "branch_country='FR'",
        "branch_semantics='eu_inward_passport'",
        "GLEIF_EXPLICIT_EXCEPTION_NO_PARENT_EDGE",
        "RESEARCH_FR_PASSPORT_BRANCH_NOT_DISTINCT_LEGAL_INSURER",
        "false AS authorized_to_materialize", "false AS neon_written",
        "false AS model_input_approved",
        "2026-11-03T08:00:00Z",
    )
    if any(needle not in body for needle in required):
        raise EvidenceSourceContractError("required fail-closed source/identity/rights rule missing")
    return {"source_count": len(rows), "direct": len(edges),
            "ultimate": len(ultimates), "exceptions": len(exceptions)}


class OfficialGleifElevenNeonReadOnlyTests(unittest.TestCase):
    def setUp(self):
        self.sql = SOURCE.read_text(encoding="utf-8")

    def test_exact_official_cohort(self):
        self.assertEqual(inspect_contract(self.sql),
                         {"source_count": 11, "direct": 5, "ultimate": 4, "exceptions": 2})

    def test_original_sha_drift_rejected(self):
        altered = self.sql.replace(next(iter(EXPECTED_SHA.values())), "0" * 64)
        with self.assertRaisesRegex(EvidenceSourceContractError, "SHA"):
            inspect_contract(altered)

    def test_duplicate_source_endpoint_rejected(self):
        altered = self.sql.replace(
            "('529900KIN5BE45V5KB18', 'ultimate-parent-relationship'",
            "('529900UCN37OZCXGVW88', 'ultimate-parent-relationship'",
        )
        with self.assertRaises(EvidenceSourceContractError):
            inspect_contract(altered)

    def test_branch_consolidation_cannot_be_flipped(self):
        altered = self.sql.replace(
            "('969500VV8Y4PQ7XJWE02', 'direct-parent-relationship', 'F240A7PWJB2BLKELB442'",
            "('969500VV8Y4PQ7XJWE02', 'direct-parent-relationship', '529900KIN5BE45V5KB18'",
        )
        with self.assertRaisesRegex(EvidenceSourceContractError, "ultimate parent disagrees"):
            inspect_contract(altered)

    def test_reporting_exception_must_not_be_edge(self):
        altered = self.sql.replace(
            "'direct-parent-reporting-exception', NULL, 'PARENT_REPORTING_EXCEPTION'",
            "'direct-parent-reporting-exception', '529900F2F9VZ5FRROH89', 'PARENT_REPORTING_EXCEPTION'",
        )
        with self.assertRaisesRegex(EvidenceSourceContractError, "exception fabricated"):
            inspect_contract(altered)

    def test_neon_writes_blocked(self):
        with self.assertRaisesRegex(EvidenceSourceContractError, "read-only"):
            inspect_contract(self.sql + "\nUPDATE entity.organization SET identity_status='verified';\n")

    def test_rights_flag_not_optional(self):
        altered = self.sql.replace("false AS authorized_to_materialize", "true AS authorized_to_materialize")
        with self.assertRaisesRegex(EvidenceSourceContractError, "required fail-closed"):
            inspect_contract(altered)

    def test_branch_regulator_evidence_mandatory(self):
        altered = self.sql.replace("branch_semantics='eu_inward_passport'", "branch_semantics='unknown'")
        with self.assertRaisesRegex(EvidenceSourceContractError, "required fail-closed"):
            inspect_contract(altered)


if __name__ == "__main__":
    unittest.main()
