# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline fail-closed guard for exact 2025 definitive/2026 provisional CBS permit means.

The research SQL was independently replayed in private Neon with ten
read-only results; CI never accesses either provider or database.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "sql" / "research_cbs_83673ned_2025_definitive_2026_preliminary_v0.sql"

PINS = [
    "70731cf7be6e73813059c250db9f1f21ad4024f0fb7cba5075ad8af666d90a5e",
    "7c9b9e307fd7fbf4ef8d5e9e26eaf3d9b9a991dd54a6b95c01409d22663c5908",
    "626dac3ab357839e615bcf0260237651d4a3983a88a0f18f6c8e3bfc24272c4d",
    "2b224f3f6546f7c5f5905a6b226a3471c986eaf2d7cd16b7001f720ff26e9fe0",
    "67a2647fc84a812569caf0d128d1b7f7cd8a3d8e2f427fc2ebe28ab68ed39ed3",
    "ebe2b837bc17b3b48b14df38c2abc078ea2da4056ff37f32b77653c3a85e6fe0",
]


class CBSPermitCostYearPairSQLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.body = re.sub(r"(?m)^\s*--[^\n]*$", "", cls.sql)

    def test_immutable_read_only_query_and_final_newline(self):
        self.assertTrue(self.sql.endswith("\n"))
        self.assertTrue(self.body.lstrip().startswith("WITH expected("))
        self.assertTrue(self.body.rstrip().endswith(";"))
        self.assertEqual(len(re.findall(r";\s*$", self.body, flags=re.MULTILINE)), 1)
        self.assertIsNone(re.search(
            r"\b(INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE|COPY|"
            r"GRANT|REVOKE|EXECUTE|CALL|HTTP_GET|CURL)\b",
            self.body, re.IGNORECASE,
        ))

    def test_six_complete_original_bounded_proofs_not_six_source_candidates(self):
        self.assertCountEqual(re.findall(r"\b[0-9a-f]{64}\b", self.sql), PINS)
        self.assertEqual(
            self.sql.count("https://opendata.cbs.nl/ODataApi/OData/83673NED/"),
            6,
        )
        self.assertEqual(
            self.sql.count("TypedDataSet?$filter=Perioden%20eq%20%27"),
            4,
        )
        self.assertEqual(
            self.sql.count("Perioden?$filter=Key%20eq%20%27"),
            2,
        )
        self.assertEqual(self.sql.count("&$top=5"), 4)
        self.assertIn("COUNT(*) FROM source_data)=4", self.sql)
        self.assertIn("COUNT(*) FROM source_status)=2", self.sql)

    def test_separate_original_body_and_canonical_jsonb_receipt_hashes(self):
        self.assertIn("provider_response_sha256=e.digest", self.sql)
        self.assertIn("sample_sha256=encode(sha256(convert_to(s.sample_json::text,'UTF8')),'hex')", self.sql)
        self.assertIn("s.sample_json->>'original_response_sha256'=e.digest", self.sql)
        self.assertIn("api.note LIKE '%'||e.digest||'%'", self.sql)
        self.assertIn("api.provider_bytes_persisted IS FALSE", self.sql)
        self.assertIn("api.strict_repository_runner_executed IS FALSE", self.sql)
        self.assertIn("s.source_byte_persistence_authorized IS FALSE", self.sql)
        self.assertIn("s.model_input_approved IS FALSE", self.sql)

    def test_six_independent_real_github_original_http_receipts_are_now_required(self):
        self.assertIn("trusted_direct AS (", self.sql)
        self.assertIn("oc-cbs-83673ned-2025-github-trusted-original-direct-https-proof-v0", self.sql)
        self.assertIn("oc-cbs-83673ned-2026-regional-two-github-trusted-original-direct-v0", self.sql)
        self.assertIn("oc-cbs-github-trusted-direct-original-20261113-v0", self.sql)
        self.assertIn("s.sample_json->>'trusted_github_run_id'='43500093202'", self.sql)
        self.assertIn("s.sample_json->>'github_run_id'='43580334849'", self.sql)
        self.assertIn("s.sample_json->>'trusted_github_ci_run_id'='43501313224'", self.sql)
        self.assertIn("s.sample_json->>'direct_http_200_exact_original_no_redirect'='true'", self.sql)
        self.assertIn("s.sample_json->>'genuine_direct_http_200_no_redirect_verified'='true'", self.sql)
        self.assertIn("s.sample_json->>'direct_github_runner_executed'='true'", self.sql)
        self.assertIn("s.sample_json->>'strict_repository_runner_executed'='true'", self.sql)
        self.assertIn("s.sample_json->>'source_raw_bytes_persisted'='false'", self.sql)
        self.assertIn("s.sample_json->>'raw_original_response_bytes_saved'='false'", self.sql)
        self.assertIn("s.sample_json->>'original_provider_bytes_persisted'='false'", self.sql)
        self.assertEqual(self.sql.count("SELECT 1 FROM trusted_direct t"), 2)
        self.assertEqual(self.sql.count("t.provider_response_sha256=e.digest"), 2)
        self.assertEqual(self.sql.count("t.direct_provider_bytes=e.byte_count"), 2)
        self.assertIn("BLOCKED_INCOMPLETE_OR_UNVERIFIED_SOURCE_EVIDENCE", self.sql)
        self.assertIn("q.is_complete IS NOT TRUE", self.sql)
        self.assertNotIn("model_input_approved IS TRUE", self.sql)

    def test_original_euro_units_resolve_source_native_suffix_trap(self):
        self.assertIn("GemiddeldeBouwkostenPerM_2", self.sql)
        self.assertIn("GemiddeldeBouwkostenPerM_3", self.sql)
        self.assertIn("EUR per m³ (cubic metre), NOT per square metre", self.sql)
        self.assertIn("EUR per m² (square metre), NOT per cubic metre", self.sql)
        self.assertIn("average_eur_per_m2", self.sql)
        self.assertIn("average_permitted_eur_per_m2", self.sql)
        self.assertIn("average_eur_per_m3", self.sql)
        self.assertIn("average_permitted_eur_per_m3", self.sql)

    def test_different_data_vintage_statuses_are_mandatory(self):
        self.assertIn("2026-08-20T02:00:00", self.sql)
        self.assertIn("2025VJ06", self.sql)
        self.assertIn("2026VJ06", self.sql)
        self.assertIn("Definitief", self.sql)
        self.assertIn("Voorlopig", self.sql)
        self.assertIn("provider_status", self.sql)
        self.assertIn("official_publication_modified", self.sql)
        self.assertIn("model_input_approved IS FALSE", self.sql)

    def test_completeness_and_nonidentical_housing_guard(self):
        self.assertIn("COUNT(*)=20", self.sql)
        self.assertIn("COUNT(DISTINCT (period,tenure,region_code))=20", self.sql)
        self.assertIn("COUNT(*) FROM paired)=10", self.sql)
        self.assertIn("region_code ~ '^(NL01|LD0[1-4])  $'", self.sql)
        self.assertIn("ABS(eur_m2*area_m2-cost_thousand*1000)<=3000", self.sql)
        self.assertIn("NULLIF(prev.eur_m2,0)", self.sql)
        self.assertIn("not building inflation or insured TIV", self.sql)

    def test_blocker_is_explicit_without_original_receipt_pairs(self):
        self.assertIn("q.is_complete IS TRUE", self.sql)
        self.assertIn("q.is_complete IS NOT TRUE", self.sql)
        self.assertIn("BLOCKED_INCOMPLETE_OR_UNVERIFIED_SOURCE_EVIDENCE", self.sql)
        self.assertIn("MODEL_NOT_ADMITTED", self.sql)
        self.assertIn("RESEARCH_ONLY_VALIDATED_ORIGINAL_RECEIPTS", self.sql)


if __name__ == "__main__":
    unittest.main()
