# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline guard on original RVO/PDOK first-party metadata receipt and Neon staging."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"research_runners/sql"

class PDOKFirstPartyReceiptTests(unittest.TestCase):
    def test_exact_original_hash_and_github_main_identity(self):
        seed=(DIR/"insurance_pdok_brp_strict_metadata_receipt_v1_seed.sql").read_text()
        self.assertIn("99a64145c7b198bbe2e2a78f248c24845e212210d482e805cb581d6aaa61ca79",seed)
        self.assertIn("f50ae18fd344ff4c201dd3e1db6fd75f321bb302e4f84fda642d6a1750696eb2",seed)
        self.assertIn("7164465a21b3cfb7e0dae2b77e89e31fcfd034297a156c7781083e53717ad396",seed)
        self.assertIn("be00542bed9b6b5a2e41773a32421b41aba0d5b3b8ade4ca8d293c133eb10d66",seed)
        self.assertIn("526303e78974ed234610bf0a65fac4786512da13",seed)
        self.assertIn("43489886311",seed)
        self.assertIn("132108208702",seed)
        self.assertIn("ON CONFLICT",seed)

    def test_strict_json_receipt_disallows_source_bytes_and_model_admission(self):
        ddl=(DIR/"insurance_strict_metadata_probe_receipt_v1_schema.sql").read_text()
        for s in ("original_response_body_persisted = false","original_feature_rows_acquired = 0",
                  "raw_source_assets_admitted = false","model_input_approved = false",
                  "science_or_version_admission_verified = false",
                  "github_ref = 'refs/heads/main'",
                  "github_event = 'push'", "response_http_status = 200"):
            with self.subTest(s=s):self.assertIn(s,ddl)
        self.assertNotIn("ALTER TABLE research.source_api_smoke_receipt_v0",ddl)

    def test_sample_is_sanitized_original_metadata_only(self):
        s=(DIR/"insurance_pdok_brp_strict_metadata_sample_v1_seed.sql").read_text()
        self.assertIn("original_parcel_geometry_downloaded",s)
        self.assertIn("exact_final_2025_archive_verified",s)
        self.assertIn("frozen_2025_archive_not_verified",s)
        self.assertIn("source_byte_persistence_authorized",s)
        self.assertIn("internal_neon_source_sample",s)
        self.assertIn("encode(sha256(convert_to(c.sample_json::text",s)
        self.assertNotIn("INSERT INTO insured_",s)
        self.assertNotIn("INSERT INTO exposure",s)

if __name__ == "__main__":
    unittest.main()
