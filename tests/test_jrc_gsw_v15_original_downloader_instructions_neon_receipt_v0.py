# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline validation: exact GSW JRC original download instructions metadata receipt.

No real provider requests, raster data acquisition, independent rights
promotion, scientific model admission or SQL mutation during offline tests.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "research_runners/sql/jrc_gsw_v15_original_downloader_instructions_neon_metadata_v0.sql"


class JRCPublisherInstructionsSQLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.query=PATH.read_text(encoding="utf-8")
        cls.body=re.sub(r"(?m)^\s*--[^\n]*$", "", cls.query)

    def test_exact_original_jrc_source_http_and_sha_pinned(self):
        for snippet in (
            "https://global-surface-water.appspot.com/gsw/Download_Instructions.html",
            "d6760ede56052bdda84ec5d069bd56ad0dc255ad522a60332b911cab57ccf994",
            "11638",
            "43609265244",
            "132490599513",
            "2026-11-14T15:16:47.965340+00:00",
            "8548e417827c72386a0b028ed425d1a15832906e",
            "downloadWaterData_Python3_v1_5.py",
        ):
            with self.subTest(snippet=snippet):
                self.assertIn(snippet,self.query)

    def test_unlimited_360_default_must_never_promote_source(self):
        for snippet in (
            "'publisher_aggregated_default_tiles',360",
            "'aggregated_single_tile_option_documented',false",
            "'monthlyhistory_unscoped_is_bulk',true",
            "'publisher_python_script_executed',false",
            "'cloudferro_original_tile_get_performed',false",
            "'original_source_asset_request_allowance',0",
            "'original_geo_tiff_persisted',false",
            "'original_tiff_correction_proved',false",
            "'original_raster_pixel_verified',false",
            "'scientific_cat_model_input_approved',false",
        ):
            with self.subTest(snippet=snippet):
                self.assertIn(snippet,self.query)

    def test_neon_previous_independent_jrc_html_and_scoped_rights_required(self):
        for snippet in (
            "previous.sample_id=130",
            "previous.sample_sha256=encode(sha256(convert_to(previous.sample_json::text,'UTF8')),'hex')",
            "previous.sample_json->>'profile'='jrc_gsw_v15_first_party_js_inline_route_github_trusted_html_proof_v0'",
            "previous.sample_json->'source_code_only_original_publisher_inline_js'->>'effective_download_host'='s3.waw4-1.cloudferro.com'",
            "permissions.use_case='internal_neon_metadata'",
            "permissions.rights_result='allowed'",
            "permissions.scientific_model_admission IS FALSE",
            "permissions.original_asset_admitted IS FALSE",
            "previous.source_byte_persistence_authorized IS FALSE",
        ):
            with self.subTest(snippet=snippet):
                self.assertIn(snippet,self.query)

    def test_single_append_only_idempotent_non_model_metadata_receipt(self):
        self.assertIn("INSERT INTO research.source_sample_v0",self.query)
        self.assertIn("AND NOT EXISTS",self.query)
        self.assertIn("s.sample_json->>'actual_github_run_id'='43609265244'",self.query)
        self.assertIn("r.original_get_at,TRUE,FALSE,FALSE",self.query)
        self.assertIn("sample_sha256,provider_license",self.query)
        self.assertIn("source_byte_persistence_authorized",self.query)
        self.assertTrue(self.body.rstrip().endswith(";"))
        self.assertEqual(self.body.upper().count("INSERT INTO "),1)
        self.assertIsNone(re.search(
            r"\b(UPDATE|DELETE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|"
            r"HTTP_GET|CURL|EXECUTE|COPY)\b",
            self.body,flags=re.IGNORECASE,
        ))


if __name__ == "__main__":
    unittest.main()
