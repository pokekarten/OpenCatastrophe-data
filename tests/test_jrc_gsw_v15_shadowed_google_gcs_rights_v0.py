# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline safeguards for append-only Google shadowed-v1.5 JRC use-case rights.

Original first-party publisher HTML receipt #130 documents a Google Storage
v1.5 URL overwritten by the ACTIVE CloudFerro tile-click script. Generic
Google public-object GET documentation is NOT original TIFF provenance.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SQL = (
    ROOT / "research_runners" / "sql"
    / "jrc_gsw_v15_shadowed_google_gcs_rights_gate_v0.sql"
)


class JRCShadowedGoogleRightsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.query = SQL.read_text(encoding="utf-8")
        cls.body = re.sub(r"(?m)^\s*--[^\n]*$", "", cls.query)

    def test_exact_source_product_and_candidate_not_active(self):
        q = self.query
        self.assertIn("ec-jrc.global-surface-water.1984-2024", q)
        self.assertIn("shadowed Google water-world GeoTIFF Occurrence candidate", q)
        self.assertIn("NOT current publisher tile-click CloudFerro route", q)
        self.assertIn("https://global-surface-water.appspot.com/download", q)
        self.assertIn("https://docs.cloud.google.com/storage/docs/access-public-data", q)
        self.assertIn(
            "https://storage.googleapis.com/water-world/download2024/VER1-5/occurrence/"
            "occurrence_10E_50N_v1_5_2024.tif", q
        )

    def test_exact_seven_original_product_use_case_decisions(self):
        cases = {
            "automated_api_access": "unknown",
            "commercial_cat_modelling": "unknown",
            "external_raw_redistribution": "unknown",
            "internal_neon_metadata": "allowed",
            "internal_neon_source_sample": "unknown",
            "internal_research": "conditional",
            "published_derived_results": "conditional",
        }
        for name, status in cases.items():
            self.assertIn(f"('{name}','{status}',", self.query)
            self.assertEqual(self.query.count(f"('{name}','{status}',"), 1)
        self.assertEqual(len(re.findall(r"(?m)^ \('(?:automated_api_access|commercial_cat_modelling|"
                                        r"external_raw_redistribution|internal_neon_metadata|"
                                        r"internal_neon_source_sample|internal_research|"
                                        r"published_derived_results)'", self.query)), 7)
        self.assertIn("scientific_model_admission,original_asset_admitted", self.query)
        self.assertIn("DATE '2026-11-14'", self.query)

    def test_original_private_metadata_page_provenance_required(self):
        q = self.query
        self.assertIn("sample.sample_id=130", q)
        self.assertIn("sample.sample_kind='public_metadata'", q)
        self.assertIn("sample.sample_sha256=encode(sha256(convert_to(sample.sample_json::text,'UTF8')),'hex')", q)
        self.assertIn("sample.sample_json->>'profile'='jrc_gsw_v15_first_party_js_inline_route_github_trusted_html_proof_v0'", q)
        self.assertIn("sample.sample_json->>'verified_trusted_github_ci_run'='43606072894'", q)
        self.assertIn("sample.sample_json->>'verified_trusted_github_html_job'='132480916985'", q)
        self.assertIn("candidate_google_v15_tile_url_from_overwritten_JS_only", q)
        self.assertIn("google_v15_candidate_overwritten_before_tile_links'='true'", q)
        self.assertIn("sample.sample_json->>'source_original_data_asset_requests'='0'", q)
        self.assertIn("sample.sample_json->>'model_input_approved'='false'", q)

    def test_parent_jrc_publisher_metadata_rights_and_non_admission_required(self):
        q = self.query
        self.assertIn("research.source_usage_rights_v0 publisher_rights", q)
        self.assertIn("publisher_rights.use_case='internal_neon_metadata'", q)
        self.assertIn("publisher_rights.rights_result='allowed'", q)
        self.assertIn("publisher_rights.scientific_model_admission IS FALSE", q)
        self.assertIn("publisher_rights.original_asset_admitted IS FALSE", q)
        self.assertIn("sample.source_byte_persistence_authorized IS FALSE", q)
        self.assertIn("sample.model_input_approved IS FALSE", q)
        self.assertIn("DATE '2026-11-14'", q)

    def test_idempotent_append_only_new_rights_non_destructive_scope(self):
        self.assertIn("INSERT INTO research.source_usage_rights_v0", self.body)
        self.assertIn("AND NOT EXISTS", self.body)
        self.assertIn("existing.product_scope=f.product_scope", self.body)
        self.assertIn("existing.use_case=d.use_case", self.body)
        self.assertIn("scientific_model_admission,original_asset_admitted", self.body)
        self.assertIn("DATE '2026-11-14',d.rationale,FALSE,FALSE", self.body)
        self.assertIsNone(re.search(
            r"\b(UPDATE|DELETE|DROP|ALTER|TRUNCATE|GRANT|REVOKE|"
            r"HTTP_GET|CURL|COPY|EXECUTE|CALL)\b",
            self.body, flags=re.IGNORECASE
        ))
        self.assertNotIn("SET model_input_approved", self.body)
        self.assertNotIn("source_byte_persistence_authorized=TRUE", self.body)
        self.assertTrue(self.body.rstrip().endswith(";"))


if __name__ == "__main__":
    unittest.main()
