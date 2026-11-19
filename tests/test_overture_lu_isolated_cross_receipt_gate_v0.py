# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline contract tests: isolated Overture Luxembourg receipt cannot imply model admission.

Actual read-only execution and the nine query-local synthetic challenges are
separately exercised against the isolated Neon research branch. Never touch
a production database or Overture source storage from this module.
"""
from pathlib import Path
import re
import unittest

SQL = (Path(__file__).resolve().parents[1] /
       "research_runners/sql/overture_lu_isolated_cross_receipt_fail_closed_v0.sql"
       ).read_text(encoding="utf-8")
CODE = "\n".join(line for line in SQL.splitlines()
                 if not line.lstrip().startswith("--"))


class OvertureIsolatedReceiptGateTests(unittest.TestCase):
    def test_exact_releases_and_bounded_original_window(self):
        for field in (
            "overture_release", "2026-10-21.0", "act_release", "2026-10-01",
            "row_group_ordinal", "19095", "69", "139", "geometric_one_to_one_candidates",
            "osm_dataset_label_rows", "microsoft_ml_dataset_label_rows",
            "original_odbl_license_tag_rows", "parquet_rows_across_three_files",
        ):
            self.assertIn(field, CODE)

    def test_missing_original_receipt_never_silently_vanishes(self):
        self.assertIn("COUNT(*)::integer AS n", CODE)
        self.assertIn("COALESCE(jsonb_agg(to_jsonb(v))->0,'{}'::jsonb)", CODE)
        self.assertIn("synthetic_missing_view_row", CODE)
        self.assertIn("n=1", CODE)
        self.assertIn("gate_pass=expected_pass AS control_pass", CODE)

    def test_all_nine_synthetic_challenges_are_present(self):
        for name in (
            "synthetic_missing_view_row", "synthetic_wrong_release",
            "synthetic_wrong_city_count", "synthetic_bad_source_lineage",
            "synthetic_false_identity", "synthetic_false_rights",
            "synthetic_false_full_parquet_sha",
            "synthetic_false_global_coverage", "synthetic_false_model_admission",
        ):
            self.assertIn(name, CODE)
        self.assertEqual(CODE.count("('observed_isolated_original_metadata',true)"), 1)

    def test_separation_of_rights_identity_and_scientific_admission(self):
        for field in (
            "complete_global_footprint_coverage_verified",
            "original_source_files_complete_sha256_verified",
            "physical_same_building_identity_verified",
            "independent_source_rights_approved",
            "cat_model_input_approved",
        ):
            self.assertIn(f"j->>'{field}'='false'", CODE)
        self.assertIn("false AS original_data_approved", CODE)
        self.assertIn("false AS insurer_building_exposure_or_cat_input_admitted", CODE)

    def test_read_only_isolated_view_no_original_records_exported(self):
        self.assertRegex(CODE.strip(), r"^WITH\s+receipt\s+AS")
        for word in (
            "INSERT", "UPDATE", "DELETE", "TRUNCATE", "DROP", "CREATE",
            "ALTER", "GRANT", "REVOKE", "COPY", "EXECUTE", "dblink",
        ):
            self.assertNotRegex(CODE, rf"\b{word}\b")
        self.assertIn("FROM research.lu_act_overture_geometry_readiness_v0", CODE)
        self.assertNotIn("SELECT * FROM research.overture_original_building", CODE)


if __name__ == "__main__":
    unittest.main()
