# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed tests for observed carrier accounts × independent public dwellings."""
from __future__ import annotations

import copy
import hashlib
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))

from public_named_insurer_berlin_corporate_stock_report_v0 import (  # noqa: E402
    build, run, COMPANY_TO_STOCK,
)
from rva_berlin_named_corporate_borough_opportunity_sensitivity_v0 import (  # noqa: E402
    INSURER, STOCK,
)

def load():
    return (
        tomllib.loads(STOCK.read_text(encoding="utf-8")),
        tomllib.loads(INSURER.read_text(encoding="utf-8")),
    )


class CrossInsurerCorporateStockReference(unittest.TestCase):
    def setUp(self):
        self.stock, self.insurer = load()

    def report(self, stock=None, insurer=None):
        return build(
            self.stock if stock is None else stock,
            self.insurer if insurer is None else insurer,
            insurer_sha256="a" * 64, stock_sha256="b" * 64,
        )

    def by_label(self, report):
        return {x["original_reported_carrier_label"]: x
                for x in report["carrier_views"]}

    def test_actual_pinned_original_pdf_receipt_required(self):
        report = run()
        self.assertTrue(report["source_provenance"][
            "existing_independent_original_source_pdf_receipt_checked"])
        self.assertFalse(report["source_provenance"][
            "original_pdfs_redownloaded_by_this_export"])
        self.assertEqual(report["source_provenance"]["insurer_observation_sha256"],
                         hashlib.sha256(INSURER.read_bytes()).hexdigest())
        self.assertEqual(report["source_provenance"]["dwelling_stock_observation_sha256"],
                         hashlib.sha256(STOCK.read_bytes()).hexdigest())

    def test_six_corporations_five_carrier_views_eight_nonunique_links(self):
        report = self.report()
        self.assertEqual(report["separate_carrier_name_count"], 5)
        self.assertEqual(report["named_company_count"], 6)
        self.assertEqual(report["named_carrier_company_association_count"], 8)
        self.assertEqual(set(COMPANY_TO_STOCK), {
            company for view in report["carrier_views"]
            for company in view["named_corporate_accounts"]})
        self.assertEqual(len(report["carrier_views"]), 5)

    def test_rva_published_stock_scope_not_covered_risk(self):
        x = self.by_label(self.report())["R+V Allgemeine Versicherung AG"]
        self.assertEqual(x["public_stock_corporate_dwelling_total_including_unassigned"], 165731)
        self.assertEqual(x["public_stock_corporate_dwelling_total_in_12_berlin_boroughs"], 162883)
        self.assertEqual(x["public_stock_corporate_dwelling_total_unassigned_other"], 2848)
        self.assertEqual(x["source_reported_coinsurance_consortium_accounts"], ["degewo AG"])

    def test_allianz_stock_and_consortium_overlap(self):
        x = self.by_label(self.report())["Allianz AG"]
        self.assertEqual(x["public_stock_corporate_dwelling_total_including_unassigned"], 135941)
        self.assertEqual(x["public_stock_corporate_dwelling_total_in_12_berlin_boroughs"], 132334)
        self.assertEqual(x["source_reported_coinsurance_consortium_accounts"], ["degewo AG"])

    def test_ergo_generali_both_reference_same_gewobag_stock(self):
        views = self.by_label(self.report())
        for carrier in ("ERGO", "Generali"):
            view = views[carrier]
            self.assertEqual(view["named_corporate_accounts"],
                             ["Gewobag Wohnungsbau-Aktiengesellschaft Berlin"])
            self.assertEqual(view["public_stock_corporate_dwelling_total_including_unassigned"], 75091)
            self.assertEqual(view["source_reported_coinsurance_consortium_accounts"], [])
        self.assertFalse(self.report()["aggregation_restrictions"]["across_carriers_additive"])

    def test_provinzial_howoge_public_stock(self):
        view = self.by_label(self.report())["Westfälische Provinzial Versicherung AG"]
        self.assertEqual(view["public_stock_corporate_dwelling_total_including_unassigned"], 82152)
        self.assertEqual(view["public_stock_corporate_dwelling_total_in_12_berlin_boroughs"], 81876)

    def test_borough_rows_reconcile_exactly_by_carrier(self):
        report = self.report()
        for view in report["carrier_views"]:
            self.assertEqual(len(view["boroughs"]), 12)
            assert_all = sum(row["published_corporate_dwelling_count_for_named_accounts"]
                             for row in view["boroughs"])
            self.assertEqual(assert_all + view["public_stock_corporate_dwelling_total_unassigned_other"],
                             view["public_stock_corporate_dwelling_total_including_unassigned"])
            self.assertEqual(assert_all, view["public_stock_corporate_dwelling_total_in_12_berlin_boroughs"])
            for row in view["boroughs"]:
                self.assertEqual(sum(row["per_company_published_corporate_dwelling_count"].values()),
                                 row["published_corporate_dwelling_count_for_named_accounts"])
                self.assertFalse(row["number_of_carrier_insured_dwellings_observed"])

    def test_no_insured_exposure_or_entity_crosswalk_in_output(self):
        r = self.report()
        self.assertEqual(r["report_status"], "research_only_not_insured_exposure_not_admitted")
        self.assertFalse(any(r["aggregation_restrictions"].values()))
        for view in r["carrier_views"]:
            for field in ("carrier_lei_verified", "carrier_real_insured_location_count_observed",
                          "carrier_real_insured_tiv_observed",
                          "carrier_real_coinsurance_share_observed",
                          "carrier_2026_policy_renewal_observed"):
                self.assertFalse(view[field])

    def test_input_order_does_not_affect_export(self):
        base = self.report()
        s = copy.deepcopy(self.stock)
        i = copy.deepcopy(self.insurer)
        s["boroughs"].reverse()
        i["housing_companies"].reverse()
        self.assertEqual(self.report(s, i), base)

    def test_forged_insured_buildings_rejected(self):
        s = copy.deepcopy(self.stock)
        s["insured_site_address_or_geocode_observed"] = True
        with self.assertRaises(ValueError):
            self.report(s)
        i = copy.deepcopy(self.insurer)
        i["housing_companies"][0]["covered_property_tiv_known"] = True
        with self.assertRaises(ValueError):
            self.report(insurer=i)

    def test_borough_numeric_drift_rejected(self):
        s = copy.deepcopy(self.stock)
        s["boroughs"][0]["degewo"] += 1
        with self.assertRaises(ValueError):
            self.report(s)

    def test_missing_housing_corporation_rejected(self):
        i = copy.deepcopy(self.insurer)
        i["housing_companies"].pop()
        with self.assertRaises(ValueError):
            self.report(insurer=i)

    def test_forged_second_insurer_consoritum_rejected(self):
        i = copy.deepcopy(self.insurer)
        x = next(x for x in i["housing_companies"] if x["legal_name"].startswith("Gewobag"))
        x["insurance_relation_type"] = "named_member_of_coinsurance_consortium"
        with self.assertRaises(ValueError):
            self.report(insurer=i)

    def test_missing_source_and_dates_rejected(self):
        s = copy.deepcopy(self.stock)
        s["source_answer_date"] = "2026-11-05"
        with self.assertRaises(ValueError):
            self.report(s)
        i = copy.deepcopy(self.insurer)
        i["source_official_url"] = "https://example.org/incorrect.pdf"
        with self.assertRaises(ValueError):
            self.report(insurer=i)

if __name__ == "__main__":
    unittest.main()
