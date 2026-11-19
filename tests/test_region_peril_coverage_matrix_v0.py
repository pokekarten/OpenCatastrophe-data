# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic matrix checks; no provider geography, model or rights admitted."""
from __future__ import annotations

from copy import deepcopy
import json
import unittest

from scripts.region_peril_coverage_matrix_v0 import (
    _load_json, build_matrix, VERSION, MAX_CELLS,
)
from scripts.region_peril_readiness_v0 import RegionPerilError, region_key


class RegionPerilMatrixTests(unittest.TestCase):
    @staticmethod
    def fixture():
        return {
            "schema_version": VERSION,
            "regions": [
                {"country_iso3": "USA", "admin_system": "US_CENSUS_TIGER_2026",
                 "admin_level": "ADM2", "admin_id": "22071",
                 "boundary_year": 2026},
                {"country_iso3": "USA", "admin_system": "US_CENSUS_TIGER_2026",
                 "admin_level": "ADM2", "admin_id": "22073",
                 "boundary_year": 2026},
            ],
            "perils": ["windstorm", "flood_river"],
            "evidence": [],
        }

    @staticmethod
    def original_boundary_evidence(doc, *, peril="flood_river", region_index=0):
        geo = doc["regions"][region_index]
        key = region_key({**geo, "peril": peril})
        return {
            "schema_version": "OC_REGION_PERIL_EVIDENCE_V0",
            "scope": {**geo, "peril": peril},
            "evidence": [
                {"role": "admin_boundary",
                 "source_id": "official.census.2026",
                 "source_sha256": "a"*64,
                 "region_key": key,
                 "peril": "all",
                 "evidence_level": "original_qc_claimed"},
            ],
        }

    def test_all_declared_cells_remain_visible_and_empty_when_no_evidence(self):
        out = build_matrix(self.fixture())
        self.assertEqual(out["target_region_count"], 2)
        self.assertEqual(out["target_peril_count"], 2)
        self.assertEqual(out["target_cell_count"], 4)
        self.assertEqual(out["no_evidence_cell_count"], 4)
        self.assertEqual(len(out["cells"]), 4)
        self.assertTrue(all(len(r["missing_catalogued_roles"]) == 8
                            for r in out["cells"]))
        self.assertFalse(out["true_global_geography_or_peril_coverage_proven"])

    def test_one_submitted_parish_peril_does_not_populate_other_three_cells(self):
        doc = self.fixture()
        doc["evidence"] = [self.original_boundary_evidence(doc)]
        out = build_matrix(doc)
        self.assertEqual(out["evidence_supplied_cell_count"], 1)
        self.assertEqual(out["no_evidence_cell_count"], 3)
        hit = [x for x in out["cells"] if x["source_receipt_count"]][0]
        self.assertEqual(hit["region_key"], "USA:US_CENSUS_TIGER_2026:ADM2:22071:2026")
        self.assertEqual(hit["peril"], "flood_river")
        self.assertEqual(hit["claimed_original_qc_roles"], ["admin_boundary"])
        self.assertEqual(hit["missing_catalogued_roles"],
                         sorted(set(["asset_geometry", "asset_values",
                                     "hazard_event_catalogue", "hazard_intensity",
                                     "vulnerability", "policy_terms", "validation_holdout"])))
        self.assertFalse(out["automatic_model_admission_allowed"])

    def test_original_claim_is_not_external_source_validation(self):
        doc = self.fixture()
        doc["evidence"] = [self.original_boundary_evidence(doc)]
        out = build_matrix(doc)
        self.assertFalse(out["independent_provider_bytes_or_licences_verified"])
        self.assertEqual(out["all_eight_roles_claimed_original_qc_cell_count"], 0)

    def test_input_region_order_and_peril_order_do_not_change_rows(self):
        doc = self.fixture()
        doc["evidence"] = [self.original_boundary_evidence(doc)]
        shuffled = deepcopy(doc)
        shuffled["regions"].reverse()
        shuffled["perils"].reverse()
        self.assertEqual(build_matrix(doc), build_matrix(shuffled))

    def test_repeated_peril_is_rejected(self):
        doc = self.fixture()
        doc["perils"] = ["windstorm", "windstorm"]
        with self.assertRaises(RegionPerilError):
            build_matrix(doc)

    def test_ambiguous_all_perils_is_rejected(self):
        doc = self.fixture()
        doc["perils"] = ["all"]
        with self.assertRaises(RegionPerilError):
            build_matrix(doc)

    def test_repeated_administrative_id_is_rejected(self):
        doc = self.fixture()
        doc["regions"].append(deepcopy(doc["regions"][0]))
        with self.assertRaises(RegionPerilError):
            build_matrix(doc)

    def test_outside_target_parish_or_different_vintage_rejected(self):
        for mutation in ("outside_parish", "different_year", "unlisted_peril"):
            doc = self.fixture()
            receipt = self.original_boundary_evidence(doc)
            if mutation == "outside_parish":
                receipt["scope"]["admin_id"] = "22075"
            elif mutation == "different_year":
                receipt["scope"]["boundary_year"] = 2025
                receipt["scope"]["admin_system"] = "OTHER_2025"
            else:
                receipt["scope"]["peril"] = "earthquake"
            receipt["evidence"] = []
            doc["evidence"] = [receipt]
            with self.subTest(mutation=mutation):
                with self.assertRaises(RegionPerilError):
                    build_matrix(doc)

    def test_duplicate_document_same_parish_peril_rejected(self):
        doc = self.fixture()
        receipt = self.original_boundary_evidence(doc)
        doc["evidence"] = [receipt, deepcopy(receipt)]
        with self.assertRaises(RegionPerilError):
            build_matrix(doc)

    def test_injected_claimed_model_status_cannot_grant_admission(self):
        doc = self.fixture()
        receipt = self.original_boundary_evidence(doc)
        receipt["evidence"][0]["evidence_level"] = "model_admitted"
        doc["evidence"] = [receipt]
        with self.assertRaises(RegionPerilError):
            build_matrix(doc)

    def test_cross_peril_reused_hazard_rejected(self):
        doc = self.fixture()
        receipt = self.original_boundary_evidence(doc)
        receipt["evidence"] = [
            {"role": "hazard_intensity",
             "source_id": "fictional.river-hazard", "source_sha256": None,
             "region_key": region_key(receipt["scope"]), "peril": "windstorm",
             "evidence_level": "catalogued"}
        ]
        doc["evidence"] = [receipt]
        with self.assertRaises(RegionPerilError):
            build_matrix(doc)

    def test_budget_blocks_large_cartesian_product(self):
        doc = self.fixture()
        doc["regions"] = [
            {**doc["regions"][0], "admin_id": f"{20000+i:05d}"}
            for i in range(200)
        ]
        doc["perils"] = [f"peril_{i:02d}" for i in range(24)]
        self.assertGreater(len(doc["regions"])*len(doc["perils"]), MAX_CELLS)
        with self.assertRaises(RegionPerilError):
            build_matrix(doc)

    def test_byte_parser_rejects_duplicate_json_keys(self):
        with self.assertRaises(RegionPerilError):
            _load_json(b'{"schema_version":"v1","schema_version":"v2"}')

    def test_byte_parser_rejects_nonfinite_numbers(self):
        with self.assertRaises(RegionPerilError):
            _load_json(b'{"value": NaN}')

    def test_byte_parser_rejects_oversized_and_invalid_utf8(self):
        for raw in (b"0" * 1_000_001, b"\xff"):
            with self.subTest(raw=raw[:8]):
                with self.assertRaises(RegionPerilError):
                    _load_json(raw)


if __name__ == "__main__":
    unittest.main()
