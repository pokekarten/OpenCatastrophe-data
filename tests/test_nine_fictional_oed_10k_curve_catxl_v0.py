# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""10,000-year nine-site *toy* GUL/gross/ceded/net and AEP/OEP regressions."""
from __future__ import annotations

import copy
import unittest
from unittest.mock import patch

from research_runners import nine_fictional_oed_10k_curve_catxl_v0 as m


class NineFictionalOed10kCurveCatXLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = m.replay()

    def test_originates_from_exact_nine_oed_fixture(self):
        p = m.original_fictional_positions()
        self.assertEqual(list(p), [f"SYNTH-{i:02}" for i in range(1, 10)])
        self.assertEqual(list(p.values()), [4_000_000 + 2_000_000*i for i in range(9)])
        self.assertEqual(self.r["invented_asset_count"], 9)
        self.assertEqual(self.r["invented_building_total_eur"], 108_000_000)

    def test_10k_worlds_positive_events_and_complete_zero_years(self):
        r = self.r
        self.assertEqual(r["worlds"], 10000)
        self.assertGreater(r["zero_event_years"], 0)
        self.assertGreater(r["years_with_two_perils"], 0)
        self.assertEqual(r["fictional_event_count"],
                         sum(r["peril_event_counts"].values()))
        self.assertEqual(r["zero_event_years"] + r["fictional_event_count"]
                         - r["years_with_two_perils"], 10000)

    def test_gul_gross_is_explicit_only_fictional_convention(self):
        r = self.r
        self.assertEqual(r["toy_gul_aggregate_eur"],
                         r["toy_insured_gross_aggregate_eur"])
        self.assertTrue(r["toy_insured_gross_equals_gul_by_invented_zero_deductible_assumption"])
        self.assertFalse(r["real_insurer_or_policy_TIV_used"])

    def test_annual_and_peril_gul_gross_net_ceded_conservation(self):
        r = self.r
        self.assertEqual(r["toy_gross_aal_eur"],
                         str(m.Decimal(r["toy_gul_aggregate_eur"]) / 10000))
        self.assertEqual(r["toy_gul_aggregate_eur"],
                         r["toy_ceded_aggregate_eur"] + r["toy_net_aggregate_eur"])
        self.assertEqual(sum(r["peril_gul_totals_eur"].values()),
                         r["toy_gul_aggregate_eur"])
        self.assertGreater(r["toy_ceded_aggregate_eur"], 0)

    def test_gross_aep_oep_and_net_aep_oep_are_annual_not_event_percentiles(self):
        r = self.r
        for prefix in ("gross", "net"):
            self.assertGreaterEqual(r[f"toy_aep99_{prefix}_eur"],
                                    r[f"toy_oep99_{prefix}_eur"])
            self.assertGreaterEqual(r[f"toy_aep995_{prefix}_eur"],
                                    r[f"toy_oep995_{prefix}_eur"])
            self.assertGreaterEqual(r[f"toy_aep995_{prefix}_eur"],
                                    r[f"toy_aep99_{prefix}_eur"])
        for quantity in ("aep99", "aep995", "oep99", "oep995"):
            self.assertGreaterEqual(r[f"toy_{quantity}_gross_eur"],
                                    r[f"toy_{quantity}_net_eur"])

    def test_toy_financial_no_event_world_conserves_zero(self):
        y = m.toy_year_financial(())
        self.assertEqual((y["gross_eur"], y["ceded_eur"], y["net_eur"]), (0,0,0))
        self.assertEqual(y["occurrence_gross_max_eur"], 0)
        self.assertEqual(y["occurrence_net_max_eur"], 0)

    def test_below_attachment_and_full_5m_cover(self):
        a = m.toy_year_financial((("flood",4_000_000),))
        b = m.toy_year_financial((("flood",12_000_000),))
        self.assertEqual(a["ceded_eur"],0)
        self.assertEqual(b["ceded_eur"],5_000_000)
        self.assertEqual(b["net_eur"],7_000_000)

    def test_two_event_annual_10m_cession_cap_and_order(self):
        y = m.toy_year_financial((("flood",12_000_000),
                                  ("windstorm",17_000_000)))
        self.assertEqual((y["gross_eur"],y["ceded_eur"],y["net_eur"]),
                         (29_000_000,10_000_000,19_000_000))
        self.assertEqual(y["occurrence_gross_max_eur"],17_000_000)
        self.assertEqual(y["occurrence_net_max_eur"],12_000_000)
        self.assertEqual([v["ceded_eur"] for v in y["events"]],
                         [5_000_000,5_000_000])

    def test_wrong_annual_event_order_duplicates_or_unknown_peril_rejected(self):
        for events in (
            (("windstorm",1),("flood",2)),
            (("flood",1),("flood",2)),
            (("hail",1),),
            (("flood",1),("windstorm",2),("hail",3)),
        ):
            with self.subTest(events=events), self.assertRaises(ValueError):
                m.toy_year_financial(events)

    def test_unbounded_loss_or_boolean_invented_loss_refused(self):
        for amount in (-1,True,108_000_001,1.5,"8000000"):
            with self.subTest(amount=repr(amount)), self.assertRaises(ValueError):
                m.toy_year_financial((("flood",amount),))

    def test_fictional_manifest_tampering_fails_before_calculation(self):
        from research_runners import wbm_like_nine_fictional_oed_v0 as p
        source = p.prepare()
        bad = copy.deepcopy(source)
        bad[0][0]["BuildingTIV"] = "5900000000"
        with patch.object(m.portfolio, "prepare", return_value=bad):
            with self.assertRaises(ValueError):
                m.original_fictional_positions()

    def test_entire_result_denies_real_model_policy_coinsurance_and_source_auth(self):
        r = self.r
        for flag in (
            "toy_hash_event_probability_is_calibrated",
            "toy_curve_is_empirically_validated",
            "oasis_engine_executed",
            "actual_hazard_vulnerability_or_model_keys_used",
            "real_insurer_or_policy_TIV_used",
            "real_contract_coinsurance_or_reinsurance_verified",
            "physical_event_occurrence_hours_clause_verified",
            "commercial_or_real_CAT_model_input_approved",
            "md5_seed_is_provider_data_authentication",
        ):
            with self.subTest(flag=flag):
                self.assertFalse(r[flag])
        self.assertEqual(r["classification"],
                         "REPRODUCIBLE_TOY_ANNUAL_GUL_AND_CATXL_NOT_A_PHYSICAL_MODEL")

    def test_sha256_receipts_are_bounded_and_not_source_authentication(self):
        for key in ("toy_annual_rows_sha256", "toy_event_rows_sha256"):
            v = self.r[key]
            self.assertEqual(len(v), 64)
            self.assertTrue(all(c in "0123456789abcdef" for c in v))
        self.assertNotEqual(self.r["toy_annual_rows_sha256"],
                            self.r["toy_event_rows_sha256"])
        self.assertFalse(self.r["md5_seed_is_provider_data_authentication"])

    def test_fixed_toy_treaty_retention_and_aggregate_reset(self):
        r = self.r
        self.assertEqual(r["toy_catxl_attachment_per_event_eur"],5_000_000)
        self.assertEqual(r["toy_catxl_per_occurrence_limit_eur"],5_000_000)
        self.assertEqual(r["toy_catxl_annual_aggregate_limit_eur"],10_000_000)
        self.assertTrue(r["toy_annual_aggregate_resets_each_world"])


if __name__ == "__main__":
    unittest.main()
