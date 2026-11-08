# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline source-receipt conservation: real HU22 geometry, fictional insurance."""
from pathlib import Path
import re
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "research/observations/rva_nrw_hu22_original_full_10k_53kreis_oed_research_v0.toml"
SQL = ROOT / "research_runners/sql/rva_solo_2025_neon_readiness_v0.sql"


class OriginalNRWHU22StudyReceiptTests(unittest.TestCase):
    def test_original_hu_source_and_fictional_county_conservation(self):
        r = tomllib.loads(RECEIPT.read_text(encoding="utf8"))
        self.assertEqual(r["full_original_source_zip_bytes"], 901092946)
        self.assertEqual(r["full_original_source_zip_sha256"],
                         "10e5b9fd1d299ef0efa883bfadce7c4c3fd2ed7b42076557cbdff887a0d277da")
        self.assertTrue(r["original_four_member_CRCs_verified"])
        self.assertEqual(r["source_original_crs"], "EPSG:4647")
        self.assertEqual(r["fictional_oed_output_crs"], "EPSG:4326")
        self.assertEqual(r["original_data_license"], "Datenlizenz Deutschland - Zero - Version 2.0")
        c = r["kreis"]
        self.assertEqual(len(c), 53)
        self.assertEqual(len(set(x["ags"] for x in c)), 53)
        self.assertTrue(all(re.fullmatch(r"05\d{3}", x["ags"]) for x in c))
        self.assertEqual(sum(x["fictional_contracts"] for x in c), 10000)
        self.assertEqual(sum(x["fictional_tiv_eur"] for x in c), 4826029500)

    def test_artifact_manifest_and_original_CSV_hashes_are_pinned(self):
        r = tomllib.loads(RECEIPT.read_text(encoding="utf8"))
        self.assertEqual(r["original_oed_artifact_id"], 13447603258)
        for name in ("oed_manifest_json_sha256", "oed_location_csv_sha256",
                     "oed_account_csv_sha256", "physical_candidate_evidence_csv_sha256"):
            with self.subTest(name=name):
                self.assertRegex(r[name], r"^[0-9a-f]{64}$")
        self.assertTrue(r["independent_artifact_ZIP_CSV_SHA_recheck_completed"])

    def test_hu22_geocoding_never_promotes_insurer_CAT_scope(self):
        r = tomllib.loads(RECEIPT.read_text(encoding="utf8"))
        for flag in ("real_RV_policy_geocodes_or_county_shares_observed",
                     "2022_original_GFK_codebook_exact_vintage_reconciled",
                     "fictional_sample_tiv_is_real_RV_insurance",
                     "science_CAT_model_input_admitted",
                     "native_German_CAT_GUL_IL_RI_OEP_AEP_verified"):
            self.assertFalse(r[flag])
        sql = SQL.read_text(encoding="utf8")
        for marker in ("source_admitted_synthetic_nrw_wgs84_units",
                       "ST_SRID(u.location)=4326",
                       "u.unit_type='asset'",
                       "source_2022_GFK_codebook_verified",
                       "oed_manifest_sha256'=v.scenario_hash",
                       "BLOCKED_FULL_ORIGINAL_HU_CRS_RIGHTS_AND_SCENARIO_PROVENANCE"):
            self.assertIn(marker, sql)


if __name__ == "__main__":
    unittest.main()
