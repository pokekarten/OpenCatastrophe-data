# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline safety/audit review of *executed* HTML-only Neon metadata seed.

The SQL runs against the authorized private research database ONLY when
separately executed; unit tests never connect to Neon or external sources.
"""
from __future__ import annotations

from pathlib import Path
import unittest


ROOT=Path(__file__).resolve().parents[1]
SEED=ROOT/"research_runners/sql/jrc_gsw_v15_publisher_page_one_shot_neon_metadata_v0.sql"


class JRCPublisherNeonMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql=SEED.read_text(encoding="utf-8")

    def test_real_original_html_response_provenance_must_match_job(self):
        for value in (
            "jrc_gsw_v15_original_publisher_html_one_shot_metadata_v0",
            "510b4bc273c743b8789afb3ffa57db31077e1f2ac617aca4869870c123995a08",
            "85581", "43591889218", "132438178397",
            "bf9f5a729bebb069492d1fc94e4d0db6cababd74",
            "d2ba746281468b520c5ac3b73db8f40f2d1438d471b2a08c385fbb71b6cfd3f7",
            "https://global-surface-water.appspot.com/download",
            "https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/",
            "2026-11-14T11:50:14.612603+00:00",
        ):
            with self.subTest(value=value):
                self.assertIn(value,self.sql)

    def test_original_website_not_misidentified_as_raster_or_catalogue(self):
        for evidence in (
            "'source_original_catalogue_bytes_hashed',false",
            "'source_original_catalogue_complete',false",
            "'individual_tile_path_in_html_proven',false",
            "'individual_tile_original_bytes_hashed',false",
            "'individual_tile_post_correction_bytes_verified',false",
            "'pixel_values_verified',false",
            "'cloudferro_service_api_terms_reviewed',false",
            "'source_model_input_approved',false",
            "'original_asset_admitted',false",
            "'scientific_model_admission',false",
            "'trusted_main_original_probe',false",
        ):
            with self.subTest(evidence=evidence):
                self.assertIn(evidence,self.sql)

    def test_immutable_canonical_jsonb_and_licence_gate(self):
        for evidence in (
            "research.source_sample_v0",
            "research.source_usage_rights_v0",
            "rights.use_case='internal_neon_metadata'",
            "rights.product_scope=r.product_scope",
            "rights.rights_result='allowed'",
            "NOT rights.scientific_model_admission",
            "NOT rights.original_asset_admitted",
            "sha256(convert_to(r.receipt_json::text,'UTF8'))",
            "'public_metadata'",
            "true,false,false",
            "NOT EXISTS (",
            "ON CONFLICT DO NOTHING",
            "RETURNING sample_id",
        ):
            with self.subTest(evidence=evidence):
                self.assertIn(evidence,self.sql)
        self.assertNotIn("OVERRIDING SYSTEM VALUE",self.sql)
        self.assertNotIn("DELETE FROM ",self.sql.upper())
        self.assertNotIn("UPDATE RESEARCH.",self.sql.upper())
        self.assertNotIn("DROP TABLE ",self.sql.upper())
        self.assertNotIn("CREATE TABLE ",self.sql.upper())
        self.assertNotIn("GRANT ",self.sql.upper())
        self.assertNotIn("source_byte_persistence_authorized,true",self.sql.replace(" ",""))


if __name__=="__main__":
    unittest.main()
