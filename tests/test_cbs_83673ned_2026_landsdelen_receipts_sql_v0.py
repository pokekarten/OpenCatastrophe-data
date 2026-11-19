# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline fail-closed guards for CBS 83673NED regional receipts SELECT.

The SQL is independently verified by actual SELECT against the private
insurance research Neon DB; this CI test never connects to CBS or Neon.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL_PATH = ROOT / "sql" / "research_cbs_83673ned_2026_landsdelen_receipts_v0.sql"


class CBSRegionalOriginalReceiptSQLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL_PATH.read_text(encoding="utf-8")
        cls.body = re.sub(r"(?m)^\s*--[^\n]*$", "", cls.sql)

    def test_only_one_read_only_statement_and_no_network_or_ddl(self):
        self.assertTrue(self.body.lstrip().startswith("WITH "))
        self.assertTrue(self.body.rstrip().endswith(";"))
        self.assertEqual(len(re.findall(r";\s*$", self.body, re.MULTILINE)), 1)
        self.assertIsNone(
            re.search(
                r"\b(INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE|"
                r"COPY|GRANT|REVOKE|EXECUTE|CALL|DO|HTTP_GET|CURL)\b",
                self.body, re.IGNORECASE,
            ),
        )

    def test_exact_product_and_original_two_immutable_urls(self):
        self.assertIn("nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned", self.sql)
        self.assertEqual(self.sql.count("https://opendata.cbs.nl/ODataApi/OData/83673NED/TypedDataSet?"), 2)
        self.assertIn("and%20Eigendom%20eq%20%27A028867%27&$top=5", self.sql)
        self.assertIn("and%20Eigendom%20eq%20%27A028868%27&$top=5", self.sql)
        self.assertNotIn("ODataFeed", self.sql)

    def test_both_original_body_hashes_are_pinned_separately(self):
        pins = re.findall(r"\b[0-9a-f]{64}\b", self.sql)
        self.assertCountEqual(pins, [
            "2b224f3f6546f7c5f5905a6b226a3471c986eaf2d7cd16b7001f720ff26e9fe0",
            "67a2647fc84a812569caf0d128d1b7f7cd8a3d8e2f427fc2ebe28ab68ed39ed3",
        ])
        self.assertIn("sample_json->>'original_response_bytes' = '1457'", self.sql)
        self.assertIn("sample_json->>'original_response_bytes' = '1459'", self.sql)
        self.assertIn("provider_response_sha256", self.sql)

    def test_json_receipt_hash_is_not_original_response_hash(self):
        self.assertIn("s.sample_sha256 = encode(sha256(convert_to(s.sample_json::text, 'UTF8')), 'hex')", self.sql)
        self.assertIn("s.provider_response_sha256 AS bounded_response_sha256", self.sql)
        self.assertNotIn("s.sample_sha256 = s.provider_response_sha256", self.sql)

    def test_cannot_promote_a_sample_or_unverified_direct_github_runner(self):
        self.assertIn("s.research_only IS TRUE", self.sql)
        self.assertIn("s.model_input_approved IS FALSE", self.sql)
        self.assertIn("s.source_byte_persistence_authorized IS FALSE", self.sql)
        self.assertIn("s.sample_json->>'direct_trusted_repository_runner_executed' = 'false'", self.sql)
        self.assertIn("trusted_original_github AS (", self.sql)
        self.assertIn("s.sample_json->>'profile' =", self.sql)
        self.assertIn("oc-cbs-83673ned-2026-regional-two-github-trusted-original-direct-v0", self.sql)
        self.assertIn("s.sample_json->>'github_run_id' = '43580334849'", self.sql)
        self.assertIn("s.sample_json->>'github_job_id' = '132403533534'", self.sql)
        self.assertIn("s.sample_json->>'github_job_conclusion' = 'success'", self.sql)
        self.assertIn("s.sample_json->>'direct_github_runner_executed' = 'true'", self.sql)
        self.assertIn("s.sample_json->>'strict_repository_runner_executed' = 'true'", self.sql)
        self.assertIn("s.sample_json->>'raw_original_response_bytes_saved' = 'false'", self.sql)
        self.assertIn("d.provider_response_sha256 = p.provider_response_sha256", self.sql)
        self.assertIn("d.original_response_bytes = p.sample_json->>'original_response_bytes'", self.sql)
        self.assertIn("q.passes_completeness_and_units IS TRUE", self.sql)
        self.assertIn("q.passes_completeness_and_units IS NOT TRUE", self.sql)
        self.assertIn("NOT model approved", self.sql)
        self.assertIn("BLOCKED_missing_or_malformed_research_evidence_or_direct_original_proof", self.sql)

    def test_complete_four_landsdelen_two_tenures_no_duplicate(self):
        self.assertIn("COUNT(*) = 10", self.sql)
        self.assertIn("COUNT(DISTINCT sample_id) = 2", self.sql)
        self.assertIn("COUNT(DISTINCT (region_code, tenure)) = 10", self.sql)
        self.assertIn("COUNT(DISTINCT region_code) = 5", self.sql)
        self.assertIn("COUNT(*) FILTER (WHERE tenure = 'rental') = 5", self.sql)
        self.assertIn("COUNT(*) FILTER (WHERE tenure = 'owner') = 5", self.sql)
        self.assertIn("region_code ~ '^(NL01|LD0[1-4])  $'", self.sql)
        self.assertIn("version_rank = 1", self.sql)

    def test_provisional_vintage_and_source_native_correct_unit_mappings(self):
        self.assertIn("2026-08-20T02:00:00", self.sql)
        self.assertIn("2026VJ06", self.sql)
        self.assertIn("Voorlopig", self.sql)
        self.assertIn("average_permitted_eur_per_m3", self.sql)
        self.assertIn("average_permitted_eur_per_m2", self.sql)
        self.assertIn("mean_permitted_dwelling_floor_area_m2", self.sql)
        self.assertIn("mean_permitted_dwelling_volume_m3", self.sql)
        self.assertIn("source_native_field_crosswalk", self.sql)
        self.assertIn("'GemiddeldeBouwkostenPerM_2' = 'EUR per m³ (cubic metre), NOT per square metre'", self.sql)
        self.assertIn("'GemiddeldeBouwkostenPerM_3' = 'EUR per m² (square metre), NOT per cubic metre'", self.sql)
        self.assertIn("ABS(eur_per_m3 * mean_m3", self.sql)
        self.assertIn("ABS(eur_per_m2 * mean_m2", self.sql)


if __name__ == "__main__":
    unittest.main()
