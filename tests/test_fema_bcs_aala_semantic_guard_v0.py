# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Only independently synthetic fixtures; no provider source bytes."""
from __future__ import annotations

import copy
from fractions import Fraction
import unittest

from research_runners.fema_bcs_aala_semantic_guard_v0 import (
    SyntheticAALAError, check_synthetic_aala,
)


def fixture():
    return {
        "schema_version": "FEMA_BCS_SYNTHETIC_AALA_V0",
        "evidence_class": "synthetic_contract_test_only",
        "cases": [{
            "case_id": "SYNTH-1",
            "synthetic_region": "SYNTH-COUNTY-A",
            "peril": "hurricane_wind",
            "construction_year": 2010,
            "currency_year": 2020,
            "comparison_basis": "same_hazard_exposure_and_money_year_code_only_difference",
            "source_identity": "independently_synthetic_no_fema_bytes",
            "pre_icode_aal_usd_cents": 10000,
            "with_icode_aal_usd_cents": 7000,
        }],
    }


class SemanticGuardTests(unittest.TestCase):
    def test_aala_is_signed_difference_of_modelled_annual_losses(self):
        result = check_synthetic_aala(fixture())
        self.assertEqual(result["cases"][0]["aala_usd_cents_signed"], 3000)
        self.assertEqual(result["cases"][0]["with_code_to_pre_code_aal_ratio"], "7/10")
        self.assertEqual(7000 + result["cases"][0]["aala_usd_cents_signed"], 10000)
        self.assertIsNone(result["aggregate_aala"])
        self.assertFalse(result["independent_empirical_validation"])
        self.assertFalse(result["insured_or_event_loss_generated"])
        self.assertFalse(result["elt_ylt_aep_oep_generated"])
        self.assertFalse(result["fema_workbook_or_bcat_data_read"])

    def test_negative_avoided_loss_is_not_clipped(self):
        payload = fixture()
        payload["cases"][0]["with_icode_aal_usd_cents"] = 11000
        result = check_synthetic_aala(payload)
        self.assertEqual(result["cases"][0]["aala_usd_cents_signed"], -1000)
        self.assertEqual(result["cases"][0]["with_code_to_pre_code_aal_ratio"], "11/10")

    def test_zero_baseline_has_no_defined_ratio(self):
        payload = fixture()
        payload["cases"][0]["pre_icode_aal_usd_cents"] = 0
        self.assertIsNone(check_synthetic_aala(payload)["cases"][0]["with_code_to_pre_code_aal_ratio"])
        self.assertEqual(check_synthetic_aala(payload)["cases"][0]["aala_usd_cents_signed"], -7000)

    def test_results_deterministic_under_input_case_order(self):
        payload = fixture()
        second = copy.deepcopy(payload["cases"][0])
        second.update(case_id="SYNTH-2", synthetic_region="SYNTH-COUNTY-B", peril="flood")
        payload["cases"].append(second)
        a = check_synthetic_aala(payload)
        self.assertEqual(len(a["cases"]), 2)
        self.assertEqual(a["cases"][0]["case_id"], "SYNTH-1")
        self.assertEqual(check_synthetic_aala(payload), check_synthetic_aala(copy.deepcopy(payload)))
        reversed_input = copy.deepcopy(payload)
        reversed_input["cases"].reverse()
        self.assertEqual(a["cases"], check_synthetic_aala(reversed_input)["cases"])

    def test_no_claims_or_bcat_source_promotion(self):
        for change in [
            {"source_identity": "FEMA-0173"},
            {"comparison_basis": "observed_claims"},
            {"source_identity": "insurance_company_claims"},
        ]:
            with self.subTest(change=change):
                payload = fixture()
                payload["cases"][0].update(change)
                with self.assertRaises(SyntheticAALAError):
                    check_synthetic_aala(payload)
        for value in ("empirical", "production", None):
            with self.subTest(value=value):
                payload = fixture()
                payload["evidence_class"] = value
                with self.assertRaises(SyntheticAALAError):
                    check_synthetic_aala(payload)

    def test_missing_or_extra_fields_blocked(self):
        for key in list(fixture()["cases"][0]):
            with self.subTest(key=key):
                payload = fixture()
                del payload["cases"][0][key]
                with self.assertRaises(SyntheticAALAError):
                    check_synthetic_aala(payload)
        payload = fixture()
        payload["cases"][0]["insured_loss_usd_cents"] = 4
        with self.assertRaises(SyntheticAALAError):
            check_synthetic_aala(payload)
        payload = fixture()
        payload["source_url"] = "https://example.com"
        with self.assertRaises(SyntheticAALAError):
            check_synthetic_aala(payload)

    def test_non_integer_amounts_rejected(self):
        for value in (True, 0.01, "100", -1, float("inf"), float("nan"), 10**19):
            with self.subTest(value=value):
                payload = fixture()
                payload["cases"][0]["pre_icode_aal_usd_cents"] = value
                with self.assertRaises(SyntheticAALAError):
                    check_synthetic_aala(payload)

    def test_documented_cohort_endpoints_accepted(self):
        for year in (2000, 2016):
            payload = fixture()
            payload["cases"][0]["construction_year"] = year
            self.assertEqual(check_synthetic_aala(payload)["cases"][0]["construction_year"], year)

    def test_unbounded_year_and_unknown_peril_rejected(self):
        for key, value in (
            ("construction_year", 1999),
            ("construction_year", 2017),
            ("construction_year", 2018),
            ("construction_year", 2019),
            ("construction_year", 2010.0),
            ("currency_year", True),
            ("peril", "hail"),
            ("peril", "wildfire"),
        ):
            with self.subTest(key=key, value=value):
                payload = fixture()
                payload["cases"][0][key] = value
                with self.assertRaises(SyntheticAALAError):
                    check_synthetic_aala(payload)

    def test_duplicate_identity_or_population_blocked(self):
        payload = fixture()
        payload["cases"].append(copy.deepcopy(payload["cases"][0]))
        with self.assertRaisesRegex(SyntheticAALAError, "duplicate case_id"):
            check_synthetic_aala(payload)
        payload["cases"][1]["case_id"] = "SYNTH-2"
        with self.assertRaisesRegex(SyntheticAALAError, "duplicate region"):
            check_synthetic_aala(payload)

    def test_non_synthetic_region_rejected(self):
        payload = fixture()
        payload["cases"][0]["synthetic_region"] = "US-FL"
        with self.assertRaises(SyntheticAALAError):
            check_synthetic_aala(payload)

    def test_empty_and_excessive_cases_blocked(self):
        for n in (0,1001):
            payload = fixture()
            payload["cases"] = [copy.deepcopy(payload["cases"][0]) for _ in range(n)]
            with self.assertRaises(SyntheticAALAError):
                check_synthetic_aala(payload)


if __name__ == "__main__":
    unittest.main()
