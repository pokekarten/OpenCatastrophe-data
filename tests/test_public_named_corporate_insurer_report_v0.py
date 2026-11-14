# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Negative and positive tests for a generic report view of public insurer accounts."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
from public_named_corporate_insurer_report_v0 import project, read_and_project  # noqa: E402

SOURCE = ROOT / "research/observations/rva_berlin_senate_housing_insurer_relations_2025_v0.toml"
RVA = "R+V Allgemeine Versicherung AG"


def load():
    return tomllib.loads(SOURCE.read_text(encoding="utf-8"))


class PublicNamedInsurerReport(unittest.TestCase):
    def setUp(self):
        self.record = load()

    def run_report(self, record=None):
        return project(self.record if record is None else record, source_sha256="a" * 64)

    def test_actual_source_and_document_hash_linked(self):
        out = read_and_project()
        self.assertEqual(out["source"]["typed_research_observation_sha256"],
                         hashlib.sha256(SOURCE.read_bytes()).hexdigest())
        self.assertFalse(out["source"]["original_pdf_bytes_verified_by_this_export"])
        self.assertEqual(out["source"]["reported_date"], "2025-04-01")

    def test_six_accounts_eight_edges_five_distinct_carrier_labels(self):
        out = self.run_report()
        self.assertEqual(out["named_corporate_accounts_count"], 6)
        self.assertEqual(out["named_carrier_account_associations_count"], 8)
        self.assertEqual(out["carrier_label_count"], 5)
        self.assertEqual(len(out["carrier_account_edges"]), 8)
        self.assertEqual(sum(x["reported_carrier_label"] == RVA
                             for x in out["carrier_account_edges"]), 3)

    def test_only_degewo_is_proven_consortium(self):
        out = self.run_report()
        co = [x for x in out["carrier_account_edges"]
              if x["member_of_insurer_consortium_explicitly_reported"]]
        self.assertEqual({x["reported_carrier_label"] for x in co}, {RVA, "Allianz AG"})
        self.assertEqual({x["reported_corporate_account"] for x in co}, {"degewo AG"})
        self.assertEqual({x["relationship_evidence_class"] for x in co},
                         {"named_member_of_consortium"})

    def test_all_competitor_carriers_stay_visible(self):
        out = self.run_report()
        labels = set(out["reported_carrier_labels"])
        self.assertEqual(labels, {RVA, "Allianz AG", "ERGO", "Generali",
                                  "Westfälische Provinzial Versicherung AG"})
        self.assertTrue(all(x["reported_carrier_label"] in labels
                            for x in out["carrier_account_edges"]))

    def test_report_never_invents_insured_site_or_2026_coverage(self):
        out = self.run_report()
        self.assertTrue(out["research_only_not_admitted"])
        for edge in out["carrier_account_edges"]:
            self.assertFalse(edge["individual_insured_buildings_observed"])
            self.assertFalse(edge["insured_asset_tiv_observed"])
            self.assertFalse(edge["carrier_share_or_cession_observed"])
            self.assertFalse(edge["carrier_current_as_of_2026_confirmed"])
            self.assertFalse(edge["carrier_identity_leicode_verified"])
        self.assertNotIn("insured_building_count", json.dumps(out))
        self.assertNotIn("insured_asset_address", json.dumps(out))

    def test_output_order_independent_of_input_order(self):
        a = self.run_report()
        b = copy.deepcopy(self.record)
        b["housing_companies"].reverse()
        self.assertEqual(a, self.run_report(b))

    def test_false_original_date_and_url_fail(self):
        for k, v in (("source_statement_date", "2026-01-01"),
                     ("source_official_url", "https://example.org/incorrect.pdf"),
                     ("source_document_number", "wrong")):
            x = copy.deepcopy(self.record)
            x[k] = v
            with self.subTest(k=k), self.assertRaises(ValueError):
                self.run_report(x)

    def test_tampered_real_risk_sites_are_rejected(self):
        for k in ("risk_addresses_known", "insured_building_count_known",
                  "covered_property_tiv_known", "carrier_2026_still_current_confirmed",
                  "individual_building_is_separate_insurance_contract"):
            x = copy.deepcopy(self.record)
            x["housing_companies"][0][k] = True
            with self.subTest(k=k), self.assertRaises(ValueError):
                self.run_report(x)

    def test_wrong_global_risk_claims_rejected(self):
        for k in ("company_2026_renewal_or_current_carrier_observed",
                  "degewo_rva_coinsurance_fraction_observed",
                  "model_real_rva_exposure_site_admitted"):
            x = copy.deepcopy(self.record)
            x[k] = True
            with self.subTest(k=k), self.assertRaises(ValueError):
                self.run_report(x)

    def test_wrong_company_rva_flag_rejected(self):
        x = copy.deepcopy(self.record)
        x["housing_companies"][1]["rva_allgemeine_explicitly_named"] = False
        with self.assertRaises(ValueError):
            self.run_report(x)

    def test_wrong_consortium_and_missing_member_rejected(self):
        x = copy.deepcopy(self.record)
        x["housing_companies"][0]["named_insurers"] = [RVA]
        with self.assertRaises(ValueError):
            self.run_report(x)
        x = copy.deepcopy(self.record)
        x["housing_companies"][0]["insurance_relation_type"] = "named_building_insurance_contract_counterparty"
        with self.assertRaises(ValueError):
            self.run_report(x)

    def test_rva_marked_as_competitor_rejected(self):
        x = copy.deepcopy(self.record)
        x["housing_companies"][3]["named_insurers"].append(RVA)
        with self.assertRaises(ValueError):
            self.run_report(x)

    def test_duplicate_names_or_labels_rejected(self):
        x = copy.deepcopy(self.record)
        x["housing_companies"][1]["legal_name"] = x["housing_companies"][0]["legal_name"]
        with self.assertRaises(ValueError):
            self.run_report(x)
        x = copy.deepcopy(self.record)
        x["housing_companies"][3]["named_insurers"] = ["ERGO", "ERGO"]
        with self.assertRaises(ValueError):
            self.run_report(x)

    def test_missing_company_and_missing_carrier_rejected(self):
        x = copy.deepcopy(self.record)
        x["housing_companies"].pop()
        with self.assertRaises(ValueError):
            self.run_report(x)
        x = copy.deepcopy(self.record)
        x["housing_companies"][1]["named_insurers"] = []
        with self.assertRaises(ValueError):
            self.run_report(x)


if __name__ == "__main__":
    unittest.main()
