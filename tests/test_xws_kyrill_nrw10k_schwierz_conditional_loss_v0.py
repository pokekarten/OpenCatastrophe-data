# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline independent arithmetic and source-provenance negative controls."""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
import xws_kyrill_nrw10k_schwierz_conditional_loss_v0 as m


def three_site_fixture():
    counties=("05111","05362","05974")
    sites={}
    winds=[]
    for i,ags in enumerate(counties,1):
        k=f"SYN-NRW-{ags}-01-{i:06d}"
        sites[k]=(i*1000,ags)
        winds.append({
            "FictionalLocNumber":k,"KreisAGS2022":ags,
            "KyrillLower95GustMS":"19.000000",
            "KyrillRecalMeanGustMS":"30.000000",
            "KyrillUpper95GustMS":"42.000000",
            "KyrillRawUncontaminatedGustMS":"25.000000",
            "IsActualRVInsuredSite":"false",
            "WindVulnerabilityCalibrated":"false",
        })
    return winds,sites


class SchwierzConditionalTests(unittest.TestCase):
    def test_published_paa_and_mdd_are_interpolated_separately(self):
        self.assertEqual(len(m.KNOTS),12)
        self.assertEqual(m.impact_parts(Decimal("0")),(Decimal(0),Decimal(0)))
        self.assertEqual(m.impact_parts(Decimal("20")),(Decimal(0),Decimal(0)))
        self.assertEqual(m.impact_parts(Decimal("25")),(Decimal("0.001"),Decimal("0.001")))
        self.assertEqual(m.impact_parts(Decimal("30")),(Decimal("0.00676"),Decimal("0.00177515")))
        self.assertEqual(m.impact_parts(Decimal("27.5")),(Decimal("0.00388"),Decimal("0.001387575")))
        self.assertEqual(m.impact_parts(Decimal("100")),(Decimal("1"),Decimal("0.037253")))
        self.assertEqual(m.impact_parts(Decimal("149")),(Decimal("1"),Decimal("0.037253")))

    def test_conditional_one_site_loss_arithmetic_and_uncertainty_factor(self):
        # At 30 m/s: E[D]/TIV = 0.00676 * 0.00177515.
        raw=Decimal("100000000")*Decimal("0.00676")*Decimal("0.00177515")
        self.assertEqual(m.site_loss_cents(Decimal("30"),100000000,Decimal("1")),
                         int((raw*100).to_integral_value()))
        self.assertEqual(m.site_loss_cents(Decimal("30"),100000000,Decimal("0.5")),
                         int((raw*50).to_integral_value()))
        self.assertEqual(m.site_loss_cents(Decimal("30"),100000000,Decimal("2")),
                         int((raw*200).to_integral_value()))
        self.assertEqual(m.site_loss_cents(Decimal("20"),100000000,Decimal("1")),0)

    def test_fails_on_undeclared_multipliers_and_nonphysical_wind(self):
        with self.assertRaisesRegex(m.SensitivityBlocked,"undocumented"):
            m.site_loss_cents(Decimal("30"),1000,Decimal("10"))
        for gust in (Decimal("NaN"),Decimal("-2"),Decimal("151")):
            with self.subTest(gust=gust),self.assertRaises(m.SensitivityBlocked):
                m.impact_parts(gust)
        with self.assertRaises(m.SensitivityBlocked):
            m.site_loss_cents(Decimal("30"),-1,Decimal("1"))

    def test_three_site_county_conservation_all_twelve_counterfactuals(self):
        winds,sites=three_site_fixture()
        with patch.object(m,"EXPECTED_N",3),patch.object(m,"EXPECTED_COUNTIES",3),patch.object(m,"EXPECTED_TIV",6000):
            result=m.simulate(winds,sites)
        self.assertEqual(len(result["results"]),12)
        self.assertEqual(len(result["county_rows"]),36)
        self.assertEqual(result["county_count"],3)
        self.assertTrue(result["conditional_expected_groundup_is_not_stochastic_sampled_GUL"])
        self.assertFalse(result["annual_event_frequency_justified"])
        self.assertFalse(result["gross_net_OEP_AEP_calibrated"])
        totals={(r["historical_wind_source_variant"],r["hypothetical_damage_sensitivity"]):
                 Decimal(r["conditional_expected_groundup_eur"]) for r in result["results"]}
        for scenario in m.STRENGTHS:
            self.assertEqual(totals["recalibrated_lower95",scenario],Decimal("0.00"))
            self.assertGreater(totals["recalibrated_upper95",scenario],
                               totals["recalibrated_mean",scenario])
        for pair,national in totals.items():
            subset=[r for r in result["county_rows"] if
                    (r["HistoricalWindField"],r["SyntheticDamageSensitivity"])==pair]
            self.assertEqual(sum(Decimal(r["ConditionalExpectedGroundupEUR"]) for r in subset),national)

    def test_wrong_site_identity_or_wind_quantile_fails_closed(self):
        base,sites=three_site_fixture()
        bad=deepcopy(base);bad[0]["IsActualRVInsuredSite"]="true"
        wrong=deepcopy(base);wrong[1]["KyrillLower95GustMS"]="43"
        duplicate=deepcopy(base);duplicate[2]["FictionalLocNumber"]=duplicate[0]["FictionalLocNumber"]
        for item in (bad,wrong,duplicate):
            with self.subTest(kind=item),patch.object(m,"EXPECTED_N",3),patch.object(m,"EXPECTED_COUNTIES",3),patch.object(m,"EXPECTED_TIV",6000):
                with self.assertRaises(m.SensitivityBlocked):m.simulate(item,sites)

    def test_wrong_original_hazard_sha_rejected_before_zip_decode(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"bad.zip"
            p.write_bytes(b"hello unauthorized archive")
            with self.assertRaisesRegex(m.SensitivityBlocked,"SHA-256 mismatch"):
                m._zip(p,m.XWS_ZIP_SHA,{"any"},5000000)

    def test_no_site_level_hazard_republished_in_research_summary(self):
        wind,site=three_site_fixture()
        with tempfile.TemporaryDirectory() as td:
            o=Path(td)/"s.json";c=Path(td)/"county.csv"
            with patch.object(m,"EXPECTED_N",3),patch.object(m,"EXPECTED_COUNTIES",3),patch.object(m,"EXPECTED_TIV",6000):
                report=m.simulate(wind,site)
            m.write(o,c,report)
            self.assertTrue(o.exists() and c.exists())
            body=o.read_text()
            self.assertNotIn("FictionalLocNumber",body)
            self.assertNotIn("SYN-NRW-",body)
            self.assertIn('"site_level_original_hazard_and_policy_positions_published": false',body)
            with self.assertRaisesRegex(m.SensitivityBlocked,"fresh"):
                m.write(o,c,m.simulate(wind,site) if False else report)


if __name__=="__main__":
    unittest.main()
