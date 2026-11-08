# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline tests: no brand-level LEI guessing, branch doubling or merged 2021 insurer."""
from __future__ import annotations

import copy
import hashlib
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
from public_named_insurer_lei_identity_gate_v0 import (  # noqa: E402
    PREFLIGHT, SENATE, validate, read_and_project,
)


def load():
    return (
        tomllib.loads(PREFLIGHT.read_text(encoding="utf-8")),
        tomllib.loads(SENATE.read_text(encoding="utf-8")),
    )


def row(records, label):
    return next(x for x in records["source_carriers"] if x["reported_label"] == label)


class BerlinCarrierLegalIdentityPreflightTests(unittest.TestCase):
    def setUp(self):
        self.preflight, self.senate = load()

    def check(self, preflight=None, senate=None):
        return validate(
            self.preflight if preflight is None else preflight,
            self.senate if senate is None else senate,
            senate_sha256="a" * 64,
            preflight_sha256="b" * 64,
        )

    def test_valid_original_source_preflight_and_hash_receipts(self):
        actual = read_and_project()
        self.assertEqual(actual["source_receipts"]["senate_toml_sha256"],
                         hashlib.sha256(SENATE.read_bytes()).hexdigest())
        self.assertEqual(actual["source_receipts"]["legal_identity_preflight_toml_sha256"],
                         hashlib.sha256(PREFLIGHT.read_bytes()).hexdigest())
        self.assertFalse(actual["source_receipts"]["original_GLEIF_regulator_http_body_hashed_this_run"])

    def test_only_one_distinct_source_carrier_name_regulator_matched(self):
        data = self.check()
        self.assertEqual(data["distinct_senate_carrier_names"], 5)
        self.assertEqual(data["resolved_distinct_senate_carrier_names"], 1)
        self.assertEqual(data["unresolved_or_legacy_distinct_senate_carrier_names"], 4)
        self.assertEqual(len(data["named_company_carrier_relationships"]), 8)
        self.assertEqual(sum(bool(x["regulator_identified_legal_entity_lei"])
                             for x in data["named_company_carrier_relationships"]), 3)

    def test_regulator_rva_german_lei_not_italian_branch(self):
        data = self.check()
        rva_edges = [x for x in data["named_company_carrier_relationships"]
                     if x["senate_reported_insurer"] == "R+V Allgemeine Versicherung AG"]
        self.assertEqual(len(rva_edges), 3)
        self.assertTrue(all(x["regulator_identified_legal_entity_lei"]
                            == "5299009UN4CBXZ336M65" for x in rva_edges))
        self.assertTrue(all(x["regulator_identified_legal_entity_lei"]
                            != "815600FA8F92119B8D12" for x in rva_edges))

    def test_all_other_insurer_links_remain_unknown(self):
        data = self.check()
        for x in data["named_company_carrier_relationships"]:
            if x["senate_reported_insurer"] != "R+V Allgemeine Versicherung AG":
                self.assertIsNone(x["regulator_identified_legal_entity_lei"])
            self.assertFalse(x["actual_covered_buildings_or_tiv_verified"])
            self.assertFalse(x["2026_contract_renewal_verified"])
            self.assertFalse(x["automatic_portfolio_or_group_aggregation_allowed"])

    def test_provinzial_legacy_merger_not_active_new_contract_evidence(self):
        edges = [x for x in self.check()["named_company_carrier_relationships"]
                 if x["senate_reported_insurer"] == "Westfälische Provinzial Versicherung AG"]
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["senate_reported_corporate_account"],
                         "HOWOGE Wohnungsbaugesellschaft mbH")
        self.assertEqual(edges[0]["source_documented_legal_successor_not_contract_verified"],
                         "Provinzial Versicherung AG")
        self.assertIsNone(edges[0]["regulator_identified_legal_entity_lei"])

    def test_all_eight_automatic_legal_and_portfolio_gates_false(self):
        result = self.check()
        self.assertTrue(all(v is False for v in
                            result["legal_identity_and_portfolio_safety"].values()))

    def test_deterministic_original_row_reordering(self):
        baseline = self.check()
        p = copy.deepcopy(self.preflight)
        i = copy.deepcopy(self.senate)
        p["source_carriers"].reverse()
        i["housing_companies"].reverse()
        self.assertEqual(baseline, self.check(p, i))

    def test_wrong_rva_head_lei_or_italian_branch_as_head_blocked(self):
        for value in ("815600FA8F92119B8D12", "529900Z5KBA9KJP6EK09"):
            p = copy.deepcopy(self.preflight)
            row(p, "R+V Allgemeine Versicherung AG")["resolved_lei"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.check(p)

    def test_mutated_rva_regulator_url_or_registered_name_blocked(self):
        for field, value in (
            ("resolved_legal_name", "R+V Versicherung AG"),
            ("resolved_jurisdiction", "IT"),
            ("regulator_identity_source_url", "https://example.org"),
        ):
            p = copy.deepcopy(self.preflight)
            row(p, "R+V Allgemeine Versicherung AG")[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.check(p)

    def test_short_allianz_ag_cannot_be_auto_joined_to_allianz_versicherungs_ag(self):
        p = copy.deepcopy(self.preflight)
        row(p, "Allianz AG")["resolved_lei"] = "529900X5FHSYN4P5R285"
        with self.assertRaises(ValueError):
            self.check(p)

    def test_generali_brand_cannot_be_joined_to_regulator_company(self):
        p = copy.deepcopy(self.preflight)
        row(p, "Generali")["resolved_lei"] = "5493007JO8UEQ68NG776"
        with self.assertRaises(ValueError):
            self.check(p)

    def test_ergo_brand_invented_lei_candidate_blocked(self):
        p = copy.deepcopy(self.preflight)
        row(p, "ERGO")["unassigned_similarly_named_lei"] = "529900X5FHSYN4P5R285"
        with self.assertRaises(ValueError):
            self.check(p)

    def test_missing_merger_and_legacy_lei_promotions_blocked(self):
        p = copy.deepcopy(self.preflight)
        row(p, "Westfälische Provinzial Versicherung AG")["historical_change_effective_date"] = ""
        with self.assertRaises(ValueError):
            self.check(p)
        p = copy.deepcopy(self.preflight)
        row(p, "Westfälische Provinzial Versicherung AG")["resolved_lei"] = "5493007JO8UEQ68NG776"
        with self.assertRaises(ValueError):
            self.check(p)

    def test_missing_fifth_label_or_unknown_senate_name_blocked(self):
        p = copy.deepcopy(self.preflight)
        p["source_carriers"].pop()
        with self.assertRaises(ValueError):
            self.check(p)
        i = copy.deepcopy(self.senate)
        i["housing_companies"][0]["named_insurers"] = ["Invented carrier", "Allianz AG"]
        with self.assertRaises(ValueError):
            self.check(senate=i)

    def test_unreviewed_http_source_cannot_be_reported_verified(self):
        p = copy.deepcopy(self.preflight)
        p["original_regulator_or_gleif_http_json_hashed_in_this_preflight"] = True
        with self.assertRaises(ValueError):
            self.check(p)
        p = copy.deepcopy(self.preflight)
        p["all_carrier_labels_resolution_complete"] = True
        with self.assertRaises(ValueError):
            self.check(p)

    def test_2026_renewal_and_real_asset_overclaim_blocked(self):
        p = copy.deepcopy(self.preflight)
        row(p, "R+V Allgemeine Versicherung AG")[
            "contracts_in_2026_independently_verified"] = True
        with self.assertRaises(ValueError):
            self.check(p)
        p = copy.deepcopy(self.preflight)
        row(p, "Allianz AG")["real_insured_buildings_observed"] = True
        with self.assertRaises(ValueError):
            self.check(p)

    def test_duplicate_label_or_invalid_lei_checksum_blocked(self):
        p = copy.deepcopy(self.preflight)
        p["source_carriers"][1]["reported_label"] = p["source_carriers"][0]["reported_label"]
        with self.assertRaises(ValueError):
            self.check(p)
        p = copy.deepcopy(self.preflight)
        row(p, "R+V Allgemeine Versicherung AG")["resolved_lei"] = "5299009UN4CBXZ336M64"
        with self.assertRaises(ValueError):
            self.check(p)


if __name__ == "__main__":
    unittest.main()
