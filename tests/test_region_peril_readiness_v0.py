# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic contract challenges; never claim real CAT source admission."""
from __future__ import annotations

from copy import deepcopy
import unittest

from scripts.region_peril_readiness_v0 import (
    ROLES, RegionPerilError, assess, region_key,
)


class RegionPerilReadinessTests(unittest.TestCase):
    @staticmethod
    def fixture():
        scope = {
            "country_iso3": "USA", "admin_system": "US_CENSUS_TIGER_2026",
            "admin_level": "ADM2", "admin_id": "22071",
            "boundary_year": 2026, "peril": "flood_river",
        }
        return {"schema_version": "OC_REGION_PERIL_EVIDENCE_V0",
                "scope": scope, "evidence": []}

    def test_official_parish_code_is_scoped_but_no_sources_are_admitted(self):
        doc = self.fixture()
        self.assertEqual(region_key(doc["scope"]),
                         "USA:US_CENSUS_TIGER_2026:ADM2:22071:2026")
        r = assess(doc)
        self.assertEqual(r["missing_catalogued_roles"], sorted(ROLES))
        self.assertFalse(r["automatic_model_admission_allowed"])
        self.assertFalse(r["rights_and_scientific_sufficiency_established"])

    def test_catalogued_boundary_does_not_satisfy_original_or_policy(self):
        doc = self.fixture()
        doc["evidence"] = [self.receipt(doc, "admin_boundary", "all")]
        r = assess(doc)
        self.assertEqual(r["catalogued_roles"], ["admin_boundary"])
        self.assertEqual(r["claimed_original_qc_roles"], [])
        self.assertIn("policy_terms", r["missing_catalogued_roles"])
        self.assertIn("admin_boundary", r["missing_original_qc_roles"])

    @staticmethod
    def receipt(doc, role, peril, *, level="catalogued", sha=None, source="census.2026"):
        return {"role": role, "source_id": source, "source_sha256": sha,
                "region_key": region_key(doc["scope"]), "peril": peril,
                "evidence_level": level}

    def test_wrong_parish_or_boundary_year_is_not_silently_reused(self):
        doc = self.fixture()
        doc["evidence"] = [self.receipt(doc, "admin_boundary", "all")]
        for field, value in (("admin_id", "22073"), ("boundary_year", 2025)):
            changed = deepcopy(doc)
            changed["scope"][field] = value
            with self.subTest(field=field):
                with self.assertRaises(RegionPerilError):
                    assess(changed)

    def test_hazard_from_other_peril_cannot_substitute_for_flood(self):
        doc = self.fixture()
        for peril in ("windstorm", "all"):
            changed = deepcopy(doc)
            changed["evidence"] = [
                self.receipt(changed, "hazard_intensity", peril)]
            with self.subTest(peril=peril):
                with self.assertRaises(RegionPerilError):
                    assess(changed)

    def test_2026_census_scope_rejects_other_country_level_or_unsafe_id(self):
        for field, value in (("country_iso3", "DEU"),
                             ("admin_level", "ADM1"),
                             ("admin_id", "Orleans Parish")):
            changed = self.fixture()
            changed["scope"][field] = value
            with self.subTest(field=field):
                with self.assertRaises(RegionPerilError):
                    assess(changed)

    def test_raw_checksum_cannot_be_invented_from_catalogue(self):
        doc = self.fixture()
        doc["evidence"] = [
            self.receipt(doc, "admin_boundary", "all", sha="a"*64)]
        with self.assertRaises(RegionPerilError):
            assess(doc)

    def test_original_qc_claim_must_have_lowercase_exact_hash(self):
        doc = self.fixture()
        for sha in (None, "X"*64, "a"*40):
            changed = deepcopy(doc)
            changed["evidence"] = [self.receipt(
                changed, "admin_boundary", "all",
                level="original_qc_claimed", sha=sha)]
            with self.subTest(sha=sha):
                with self.assertRaises(RegionPerilError):
                    assess(changed)

    def test_all_eight_claimed_receipts_still_never_grant_admission(self):
        doc = self.fixture()
        doc["evidence"] = [
            self.receipt(doc, role,
                         "all" if role in ("admin_boundary", "asset_geometry",
                                           "asset_values") else "flood_river",
                         level="original_qc_claimed", sha="a"*64,
                         source="fictional."+role)
            for role in ROLES]
        result = assess(doc)
        self.assertEqual(result["missing_original_qc_roles"], [])
        self.assertEqual(result["source_receipt_count"], 8)
        self.assertFalse(result["automatic_model_admission_allowed"])
        self.assertFalse(result["rights_and_scientific_sufficiency_established"])

    def test_self_asserted_model_admission_is_rejected(self):
        doc = self.fixture()
        doc["evidence"] = [self.receipt(
            doc, "admin_boundary", "all", level="model_admitted")]
        with self.assertRaises(RegionPerilError):
            assess(doc)

    def test_duplicate_sources_and_unexpected_fields_rejected(self):
        doc = self.fixture()
        row = self.receipt(doc, "admin_boundary", "all")
        doc["evidence"] = [row, deepcopy(row)]
        with self.assertRaises(RegionPerilError):
            assess(doc)
        doc["evidence"] = [dict(row, private_token="never")]
        with self.assertRaises(RegionPerilError):
            assess(doc)

    def test_missing_or_forged_input_type_rejected(self):
        doc = self.fixture()
        for field, value in (("boundary_year", True),
                             ("peril", "all perils")):
            changed = self.fixture()
            changed["scope"][field] = value
            with self.subTest(field=field):
                with self.assertRaises(RegionPerilError):
                    assess(changed)


if __name__ == "__main__":
    unittest.main()
