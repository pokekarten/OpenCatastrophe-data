# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline exact-source technical provenance gate for NOAA RTSW and GFZ Kp.

The real query has been replayed against separate research Neon and actual
GitHub source PR-branch jobs inspected. This CI test does NOT use internet,
Neon credentials, provider source bytes, or approve insurance CAT models.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "sql" / "research_noaa_swpc_gfz_kp_direct_original_github_receipts_v0.sql"


class NOAAandGFZDirectProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SQL.read_text(encoding="utf-8")
        cls.body = re.sub(r"(?m)^\s*--[^\n]*$", "", cls.source)

    def test_one_pure_read_only_query_and_source_header(self):
        self.assertTrue(self.source.endswith("\n"))
        self.assertTrue(self.body.lstrip().startswith("WITH expected("))
        self.assertTrue(self.body.rstrip().endswith(";"))
        self.assertEqual(len(re.findall(r";\s*$", self.body, flags=re.MULTILINE)), 1)
        self.assertIsNone(re.search(
            r"\b(INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|COPY|TRUNCATE|"
            r"GRANT|REVOKE|EXECUTE|CALL|HTTP_GET|CURL)\b",
            self.body, flags=re.IGNORECASE,
        ))

    def test_exact_original_URL_SHA_bytes_and_actual_github_receipts(self):
        self.assertIn("https://services.swpc.noaa.gov/json/rtsw/rtsw_mag_1m.json", self.source)
        self.assertIn("https://kp.gfz.de/app/json/?start=2024-01-01T00:00:00Z&end=2024-01-01T23:59:59Z&index=Kp&status=def", self.source)
        self.assertIn("bc35b0a375b85efe559f132cfae46d8c79b7e8f19400299ae223d067f6091159", self.source)
        self.assertIn("f03506f678672a99c4c5a2c1d251740bd484b064853db18177b9b5ba4ad27d0a", self.source)
        self.assertIn("1719377::bigint", self.source)
        self.assertIn("361::bigint", self.source)
        self.assertIn("43489514680::bigint", self.source)
        self.assertIn("132106651956::bigint", self.source)
        self.assertIn("43491158483::bigint", self.source)
        self.assertIn("132112397671::bigint", self.source)
        self.assertIn("124::bigint", self.source)
        self.assertIn("126::bigint", self.source)
        self.assertIn("original_response_sha256", self.source)

    def test_canonical_receipt_integrity_rights_and_no_raw_approval(self):
        self.assertIn("sample_sha256=encode(sha256(convert_to(s.sample_json::text,'UTF8')),'hex')", self.source)
        self.assertIn("research.source_usage_rights_v0", self.source)
        self.assertIn("r.use_case='internal_neon_metadata'", self.source)
        self.assertIn("r.rights_result='allowed'", self.source)
        self.assertIn("r.scientific_model_admission IS FALSE", self.source)
        self.assertIn("s.model_input_approved IS FALSE", self.source)
        self.assertIn("s.source_byte_persistence_authorized IS FALSE", self.source)
        self.assertIn("s.sample_json->>'model_input_approved'='false'", self.source)
        self.assertIn("s.sample_json->>'insurer_cat_model_admitted'='false'", self.source)
        self.assertIn("s.sample_json->>'provider_body_or_sensor_rows_stored'='false'", self.source)
        self.assertIn("s.sample_json->>'original_provider_body_stored'='false'", self.source)

    def test_noaa_rolling_sensor_switching_and_gfz_historical_are_not_equated(self):
        self.assertIn("noaa_swpc_rtsw_mag_2026_multispacecraft", self.source)
        self.assertIn("gfz_definitive_kp_2024_01_01_eight_3h_bins", self.source)
        self.assertIn("s.sample_json->>'source_is_rolling'='true'", self.source)
        self.assertIn("s.sample_json->>'rolling_window_complete'='false'", self.source)
        self.assertIn("s.sample_json->>'sensor_lineage_verified'='false'", self.source)
        self.assertIn("s.sample_json->>'scientific_values_verified'='false'", self.source)
        self.assertIn("s.sample_json->>'full_source_sha256_verified'='false'", self.source)
        self.assertIn("s.sample_json->>'trusted_main_run'='false'", self.source)
        self.assertIn("s.sample_json->>'original_response_shape_verified'='true'", self.source)

    def test_source_revision_or_runner_drift_must_block(self):
        self.assertIn("s.sample_json->>'github_run_id'=e.gh_run::text", self.source)
        self.assertIn("s.sample_json->>'github_job_id'=e.gh_job::text", self.source)
        self.assertIn("s.sample_json->>'github_head_sha'=e.gh_head", self.source)
        self.assertIn("s.sample_json->>'request_sha256'", self.source)
        self.assertIn("s.sample_json->>'probe_code_sha256'", self.source)
        self.assertIn("s.sample_json->>'runner_code_sha256'", self.source)
        self.assertIn("BLOCKED_MISSING_INVALID_TECHNICAL_ORIGINAL_SOURCE_RECEIPT", self.source)
        self.assertIn("DIRECT_ORIGINAL_HTTP_SHAPE_RESEARCH_ONLY_NOT_MODEL_ADMITTED", self.source)


if __name__ == "__main__":
    unittest.main()
