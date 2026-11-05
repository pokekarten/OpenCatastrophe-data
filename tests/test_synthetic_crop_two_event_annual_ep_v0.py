# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic two-event annual direct-impact OEP/AEP analytical parity tests."""
from __future__ import annotations

from fractions import Fraction
from unittest import TestCase
from unittest.mock import patch

from research_runners import synthetic_crop_two_event_annual_ep_v0 as m


class SyntheticCropAnnualExceedanceTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = m.compute()

    def test_exact_two_event_source_chain(self):
        events = m.build_events()
        self.assertEqual([(e["event_id"], e["peril"]) for e in events],
                         [("SYNTH-EVENT-001", "flood"), ("SYNTH-EVENT-002", "hail")])
        self.assertEqual([(e["lower_cents"], e["upper_cents"]) for e in events],
                         [(490000, 1190000), (225000, 225000)])

    def test_exact_four_worlds_conserve_probability(self):
        worlds = m.enumerate_year_worlds(m.build_events())
        self.assertEqual(len(worlds), 4)
        self.assertEqual(sum((x["weight"] for x in worlds), Fraction()), 1)
        both = next(w for w in worlds if w["presence"] == (True, True))
        self.assertEqual(both["weight"], Fraction(169, 32768))
        self.assertEqual((both["oep_lower"], both["aep_lower"]),
                         (490000, 715000))
        self.assertEqual((both["oep_upper"], both["aep_upper"]),
                         (1190000, 1415000))

    def test_aep_can_exceed_when_oep_does_not(self):
        row = next(x for x in self.report["strict_annual_exceedance_curves"]
                   if x["threshold_eur_strictly_exceeded"] == "5000")
        self.assertEqual(row["oep_lower"]["analytic_probability_fraction"], "0/1")
        self.assertEqual(row["aep_lower"]["analytic_probability_fraction"],
                         "169/32768")
        self.assertEqual(row["oep_upper"]["analytic_probability_fraction"],
                         "13/128")
        self.assertEqual(row["aep_upper"]["analytic_probability_fraction"],
                         "13/128")

    def test_strict_equality_does_not_exceed(self):
        row = next(x for x in self.report["strict_annual_exceedance_curves"]
                   if x["threshold_eur_strictly_exceeded"] == "11900")
        self.assertEqual(row["oep_upper"]["analytic_probability_fraction"], "0/1")
        self.assertEqual(row["aep_upper"]["analytic_probability_fraction"],
                         "169/32768")

    def test_toy_expected_annual_impact_is_not_real_aal(self):
        self.assertEqual(
            self.report["invented_exact_expected_annual_direct_impact_lower_eur"], "611.91")
        self.assertEqual(
            self.report["invented_exact_expected_annual_direct_impact_upper_eur"], "1322.85")
        self.assertFalse(self.report["real_insured_aal_oep_aep_or_gross_net"])

    def test_seed_and_10k_year_sample_reproducible(self):
        other = m.compute()
        self.assertEqual(other["annual_receipt_sha256_not_source_authentication"],
                         self.report["annual_receipt_sha256_not_source_authentication"])
        self.assertEqual(other["strict_annual_exceedance_curves"],
                         self.report["strict_annual_exceedance_curves"])
        self.assertEqual(other["yearly_event_counts"], self.report["yearly_event_counts"])
        self.assertEqual(self.report["sample_years"], 10000)
        self.assertTrue(self.report["years_with_both_event_types"] > 0)

    def test_empirical_probabilities_consistent_with_exact(self):
        rows = self.report["strict_annual_exceedance_curves"]
        for row in rows:
            for key in ("oep_lower", "oep_upper", "aep_lower", "aep_upper"):
                self.assertLess(
                    abs(row[key]["analytic_probability"] - row[key]["sample_probability"]),
                    0.03,
                )

    def test_ordering_and_monotonicity_at_all_thresholds(self):
        rows = self.report["strict_annual_exceedance_curves"]
        for row in rows:
            for family in ("oep", "aep"):
                self.assertLessEqual(
                    row[family + "_lower"]["analytic_probability"],
                    row[family + "_upper"]["analytic_probability"],
                )
            for side in ("lower", "upper"):
                self.assertLessEqual(
                    row["oep_" + side]["analytic_probability"],
                    row["aep_" + side]["analytic_probability"],
                )
        for former, later in zip(rows, rows[1:]):
            for key in ("oep_lower", "oep_upper", "aep_lower", "aep_upper"):
                self.assertGreaterEqual(
                    former[key]["analytic_probability"],
                    later[key]["analytic_probability"],
                )

    def test_invalid_probabilities_rejected(self):
        events = m.build_events()
        events[0]["annual_presence_p"] = Fraction(3, 2)
        with self.assertRaisesRegex(m.AnnualCurveError, "Bernoulli probability"):
            m.enumerate_year_worlds(events)
        events[0]["annual_presence_p"] = Fraction(-1, 2)
        with self.assertRaises(m.AnnualCurveError):
            m.enumerate_year_worlds(events)

    def test_tampered_synthetic_impact_chain_rejected(self):
        fake = {"event_id": "SYNTH-EVENT-001", "peril": "flood",
                "source_observed_crop_or_hazard_rows_used": 1,
                "underwriting_or_insured_tiv": False,
                "admitted_cat_model_input": False}
        with patch.object(m, "hypothetical_impact", return_value=fake):
            with self.assertRaisesRegex(m.AnnualCurveError, "source identity"):
                m.build_events()

    def test_no_real_data_or_insurer_claim(self):
        self.assertFalse(self.report["source_crop_or_hazard_rows_used"])
        self.assertFalse(self.report["real_event_frequency_dependence_or_cat_model_calibrated"])
        self.assertFalse(self.report["original_dataset_admitted"])
        self.assertTrue(self.report["all_loss_values_and_probabilities_invented"])
        with self.assertRaises(m.AnnualCurveError):
            m._hazard("SYNTH-EVENT-888", "flood")
        with self.assertRaises(m.AnnualCurveError):
            m.exceedance_probability([], "insured_net_oep", 0)
