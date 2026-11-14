# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed regression for exact product-scope vs source-wide sample evidence.

These tests use only checked-in SQL text. They do not contact Neon or providers.
The separately performed live SQL audit confirms PostgreSQL execution semantics.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest


SQL_PATH = (
    Path(__file__).resolve().parents[1]
    / "research_runners/sql/insurance_candidate_manifest_preflight_v0.sql"
)


class CandidateManifestPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL_PATH.read_text(encoding="utf-8")
        cls.body = re.sub(r"^\s*--[^\n]*$", "", cls.sql, flags=re.MULTILINE)

    def test_read_only_source_evidence_preflight(self):
        self.assertTrue(cls_starts_with_select(self.body))
        self.assertEqual(len(re.findall(r";\s*$", self.body, re.MULTILINE)), 1)
        self.assertTrue(self.body.rstrip().endswith(";"))
        self.assertIsNone(re.search(
            r"\b(?:INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE|"
            r"COPY|GRANT|REVOKE|EXECUTE|CALL|DO)\b",
            self.body, flags=re.IGNORECASE,
        ))

    def test_rights_keep_exact_product_scope(self):
        self.assertIn("m.product_scope", self.body)
        self.assertIn("FROM research.source_rights_matrix_v0 AS m", self.body)
        self.assertIn("COUNT(*) OVER (PARTITION BY source_id)", self.body)
        self.assertIn("MULTIPLE_PRODUCT_SCOPES_REVIEW_EACH", self.body)
        self.assertIn("WHEN commercial_cat_modelling = 'prohibited'", self.body)
        self.assertIn("WHEN automated_api_access = 'prohibited'", self.body)

    def test_source_wide_sample_cannot_prove_each_product(self):
        # This ordering is crucial: multi-product evidence needs an exact
        # source URL/product identity join before a generic observed-value label.
        scope = self.body.split("END AS research_sample_gate")[0].rsplit("CASE", 1)[-1]
        self.assertIn("WHEN samples = 0", scope)
        self.assertIn("WHEN verified_sample_hashes <> samples", scope)
        self.assertIn("WHEN COUNT(*) OVER (PARTITION BY source_id) > 1", scope)
        self.assertIn("MULTI_PRODUCT_SAMPLE_SCOPE_NOT_VERIFIED", scope)
        self.assertIn("WHEN observational_previews = 0", scope)
        self.assertLess(
            scope.index("WHEN COUNT(*) OVER (PARTITION BY source_id) > 1"),
            scope.index("WHEN observational_previews = 0"),
        )
        self.assertIn("SOURCE_ID_AGGREGATE_NOT_PRODUCT_SCOPE_PROOF", self.body)

    def test_hashes_are_not_original_provider_attestation(self):
        self.assertIn("sha256(convert_to(sample_json::text, 'UTF8'))", self.body)
        self.assertIn("verified_sample_hashes <> samples", self.body)
        self.assertIn("false AS model_input_admitted_by_this_audit", self.body)
        self.assertIn("SOURCE_SPECIFIC_SCIENCE_REVIEW_AND_EXACT_ARTIFACT_GATE_REQUIRED", self.body)


def cls_starts_with_select(sql: str) -> bool:
    return sql.lstrip().startswith("WITH ")


if __name__ == "__main__":
    unittest.main()
