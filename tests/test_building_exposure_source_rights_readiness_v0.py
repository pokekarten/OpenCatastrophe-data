# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Deterministic read-only SQL contract tests for building exposure source rights.

Live SQL readbacks and query-local synthetic challenges are separately recorded
in the PR. No Neon or third-party service is contacted by this test module.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest


SQL = (
    Path(__file__).resolve().parents[1]
    / "research_runners/sql/building_exposure_source_rights_readiness_v0.sql"
).read_text(encoding="utf-8")
CODE = "\n".join(
    line for line in SQL.splitlines() if not line.lstrip().startswith("--")
)


class BuildingExposureSourceRightsReadinessTests(unittest.TestCase):
    def test_exact_three_products_and_their_disjoint_licence_sources(self):
        for source in (
            "de.bayern.hausumringe",
            "dlr.wsf.2019",
            "overture.maps.buildings",
        ):
            self.assertIn(f"'{source}'", CODE)
        self.assertIn("WSF2019_v1_10_48.tif", CODE)
        self.assertIn("2026-10-21.0", CODE)
        self.assertIn("ODbL (Buildings theme)", CODE)
        self.assertIn("CC BY 4.0", CODE)

    def test_read_only_no_store_no_mutation_no_network(self):
        self.assertRegex(CODE.lstrip(), r"^WITH\s+targets\s+AS")
        for keyword in ("INSERT", "UPDATE", "DELETE", "TRUNCATE", "DROP",
                        "ALTER", "CREATE", "COPY", "GRANT", "REVOKE",
                        "CALL", "DO", "EXECUTE", "pg_read_file", "dblink"):
            self.assertNotRegex(CODE, rf"\b{keyword}\b")
        self.assertNotIn("postgres_fdw", CODE)
        self.assertNotIn("raw_provider_geometry", CODE)

    def test_source_ledger_exact_product_scope_not_provider_wide_rights(self):
        self.assertIn("r.source_id=b.source_id", CODE)
        self.assertIn("r.product_scope=b.product_scope", CODE)
        self.assertIn("source_wide_samples", CODE)
        self.assertIn("sample_sha256", CODE)
        self.assertIn("sha256(convert_to(sample_json::text,'UTF8'))", CODE)
        self.assertIn("matrix_scope_rows=1", CODE)
        self.assertIn("position(b.required_review_scope_marker IN b.product_scope)>0", CODE)

    def test_seven_distinct_cases_and_duplicate_evidence_host_preflight(self):
        for use in (
            "internal_research", "commercial_cat_modelling",
            "automated_api_access", "internal_neon_metadata",
            "internal_neon_source_sample", "published_derived_results",
            "external_raw_redistribution",
        ):
            self.assertIn(f"('{use}'", CODE)
        self.assertIn("ledger_entries=7", CODE)
        self.assertIn("unique_use_cases=7", CODE)
        self.assertIn("provider_host_evidence_entries=7", CODE)
        self.assertIn("missing_product_scoped_use_cases", CODE)
        self.assertIn("https://www.geodaten.bayern.de/%", CODE)
        self.assertIn("https://catalogue.geoservice.dlr.de/%", CODE)
        self.assertIn("https://docs.overturemaps.org/%", CODE)

    def test_matrix_cannot_be_overridden_by_synthetic_ledger_grants(self):
        for required in (
            "commercial_cat_modelling='allowed'",
            "automated_api_access='allowed'",
            "internal_neon_metadata='allowed'",
            "internal_neon_source_sample='allowed'",
            "published_derived_results='allowed'",
            "external_raw_redistribution='allowed'",
        ):
            self.assertIn(required, CODE)
        for dimension in (
            "commercial_automated_research_rights_complete",
            "derived_publication_rights_complete",
            "raw_redistribution_rights_complete",
        ):
            self.assertIn(dimension, CODE)
        self.assertIn("FALSE AS cat_model_input_approved_by_this_audit", CODE)
        self.assertIn("FALSE AS insurer_policy_or_tiv_available", CODE)
        self.assertIn("FALSE AS independent_building_identity_verified", CODE)

    def test_unreviewed_or_conflicting_rights_are_not_silent_success(self):
        for blocker in (
            "REVIEW_EXACT_PRODUCT_AND_RELEASE_RIGHTS",
            "REVIEW_SEVEN_USE_CASES_AND_AUTHORITY_EVIDENCE",
            "REVIEW_COMMERCIAL_CAT_USE",
            "REVIEW_EXACT_API_OR_FILE_SERVICE_AUTOMATION",
            "REVIEW_INTERNAL_RESEARCH_AND_NEON_USE",
            "BLOCK_INVALID_SAMPLE_SHA",
            "RIGHTS_ONLY_COMPLETE_SCIENCE_AND_ASSET_REVIEW_STILL_REQUIRED",
        ):
            self.assertIn(blocker, CODE)


if __name__ == "__main__":
    unittest.main()
