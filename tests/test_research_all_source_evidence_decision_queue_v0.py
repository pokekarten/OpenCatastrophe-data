# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline invariants for the separate insurance Neon source-evidence queue.

The query is checked syntactically here. The actual 707-entry SELECT was
validated separately against the authorized research Neon database; the
repository CI never connects to Neon and never requests provider data.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / "sql" / "research_all_source_evidence_decision_queue_v0.sql"


class SourceEvidenceQueueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.query = QUERY.read_text(encoding="utf-8")
        cls.body = re.sub(r"(?m)^\s*--[^\n]*$", "", cls.query)

    def test_single_read_only_statement(self):
        self.assertTrue(self.body.lstrip().startswith("WITH\n"))
        # Ignore a semicolon used as a quoted SQL string delimiter.
        self.assertEqual(len(re.findall(r";\s*$", self.body, re.MULTILINE)), 1)
        self.assertTrue(self.body.rstrip().endswith(";"))
        self.assertIsNone(
            re.search(
                r"\b(INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE|"
                r"COPY|GRANT|REVOKE|EXECUTE|CALL|DO)\b",
                self.body, re.IGNORECASE,
            )
        )

    def test_canonical_all_source_inventory_both_record_types(self):
        self.assertIn("research.all_source_inventory_v0", self.query)
        self.assertIn("i.record_type", self.query)
        self.assertIn("i.source_registry_path", self.query)
        self.assertIn("record_type='admitted_manifest'", self.query)
        self.assertIn("source_id,record_type,source_registry_path", self.query)

    def test_source_receipts_join_after_aggregation(self):
        self.assertIn("research.source_sample_v0", self.query)
        self.assertIn("research.source_api_smoke_receipt_v0", self.query)
        self.assertIn("research.source_usage_rights_v0", self.query)
        self.assertIn("LEFT JOIN sample_evidence s ON s.source_id=i.source_id", self.query)
        self.assertIn("LEFT JOIN rights_evidence e ON e.source_id=i.source_id", self.query)
        self.assertIn("LEFT JOIN api_totals a ON a.registry_source_id=i.source_id", self.query)
        self.assertIn("LEFT JOIN api_recent r ON r.registry_source_id=i.source_id", self.query)

    def test_wsv_receipt_alias_is_explicit_and_one_way(self):
        self.assertIn("wsv.pegelonline.rest-v2.dresden", self.query)
        self.assertIn("wsv.pegelonline.elbe-dresden-discharge.2020-2023", self.query)
        self.assertIn("AS registry_source_id", self.query)

    def test_original_response_sha_not_confused_with_sample_json_hash(self):
        self.assertIn("sha256(convert_to(sample_json::text,'UTF8'))", self.query)
        self.assertIn("bad_sample_json_hashes", self.query)
        self.assertIn("sample_sha256 IS DISTINCT FROM", self.query)
        self.assertNotIn("provider_response_sha256 = sample_sha256", self.query)
        self.assertIn("sample_model_approvals", self.query)
        self.assertIn("strict_runner_receipts", self.query)

    def test_unverified_or_noncommercial_rights_not_auto_approved(self):
        self.assertIn("registry_commercial_verdict='prohibited'", self.query)
        self.assertIn("registry_commercial_verdict='restricted'", self.query)
        self.assertIn("registry_commercial_verdict='unresolved'", self.query)
        self.assertIn("P1_retest_provider_with_trusted_runner", self.query)
        self.assertIn("P5_commercial_use_prohibited", self.query)
        self.assertIn("P4_commercial_use_restricted", self.query)
        self.assertIn("P2_scientific_native_sample_validation", self.query)
        self.assertNotIn("SET model_input_approved", self.query)

    def test_native_tiff_values_in_preview_are_not_mistaken_for_wms(self):
        self.assertIn("native_geotiff_lzw_window%", self.query)
        self.assertIn("native_pixels_verified", self.query)
        self.assertIn("native_class_values_decoded", self.query)
        self.assertIn("provider_response_sha256 ~ '^[0-9a-f]{64}
        self.assertIn("COUNT(DISTINCT product_scope)", self.query)
        self.assertIn("FILTER(WHERE use_case='commercial_cat_modelling')", self.query)
        self.assertIn("FILTER(WHERE use_case='automated_api_access')", self.query)
        self.assertIn("candidate_snapshot_stale", self.query)
        self.assertIn("i.actual_sample_state='not_collected'", self.query)
        self.assertIn("P2_reconcile_candidate_snapshot", self.query)


if __name__ == "__main__":
    unittest.main()
", self.query)
        self.assertIn("native_pixel_receipts_classified_preview", self.query)
        self.assertIn("P2_validate_native_pixel_preview_provenance", self.query)
        self.assertIn("P2_review_native_observation_sample", self.query)

    def test_product_scoped_rights_and_stale_candidate_status_are_separate(self):
        self.assertIn("COUNT(DISTINCT product_scope)", self.query)
        self.assertIn("FILTER(WHERE use_case='commercial_cat_modelling')", self.query)
        self.assertIn("FILTER(WHERE use_case='automated_api_access')", self.query)
        self.assertIn("candidate_snapshot_stale", self.query)
        self.assertIn("i.actual_sample_state='not_collected'", self.query)
        self.assertIn("P2_reconcile_candidate_snapshot", self.query)


if __name__ == "__main__":
    unittest.main()
