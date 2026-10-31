# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Deterministic synthetic-only tests for safe historic source overlap counts."""
import unittest

from research_runners.historical_country_year_availability_v0 import (
    AvailabilityError, audit_verified_rows,
)


def event(year=2025, country="DE", loss=""):
    return {"country_code": country, "start_date": f"{year}-02-03",
            "event_start_date_year": str(year), "economic_loss_value_eur": loss}


def indicator(country="DE", code="A1", **values):
    out = {"CountryCode": country, "IndicatorCode": code}
    out.update({str(y): "" for y in range(2000, 2025)})
    out.update(values)
    return out


class CountryLagAvailabilityTests(unittest.TestCase):
    def test_prior_year_2024_matches_2025_and_zero_is_present(self):
        r = audit_verified_rows([event(2025, loss="0")], [indicator(**{"2024": "0"})])
        self.assertEqual(r["event_count_with_exact_country_prior_year_indicator"], 1)
        self.assertEqual(r["matched_event_count_with_reported_economic_loss_field"], 1)
        self.assertFalse(r["insured_loss_created"])
        self.assertFalse(r["asset_exposure_created"])

    def test_current_year_only_must_not_be_used(self):
        r = audit_verified_rows([event(2024)], [indicator(**{"2024": "100"})])
        self.assertEqual(r["event_count_with_exact_country_prior_year_indicator"], 0)
        self.assertEqual(r["event_count_without_exact_country_prior_year_indicator"], 1)

    def test_year_boundaries(self):
        r = audit_verified_rows([event(2000), event(2001), event(2025), event(2026)],
                                [indicator(**{"2000": "10", "2024": "11"})])
        self.assertEqual(r["event_count_outside_2001_2025_eligibility"], 2)
        self.assertEqual(r["event_count_with_exact_country_prior_year_indicator"], 2)

    def test_exact_country_codes_no_fuzzy_aliases(self):
        r = audit_verified_rows([event(2025, country="GB")],
                                [indicator(country="UK", **{"2024": "9"})])
        self.assertEqual(r["event_count_with_exact_country_prior_year_indicator"], 0)

    def test_eu_aggregate_never_inflates_matches(self):
        r = audit_verified_rows([event(2025, country="EU"), event(2025, country="FR")],
                                [indicator(country="EU", **{"2024": "99"}),
                                 indicator(country="FR", **{"2024": "3"})])
        self.assertEqual(r["event_count_with_exact_country_prior_year_indicator"], 1)
        self.assertTrue(r["aggregate_EU_row_excluded"])

    def test_repeated_events_do_not_inflate_distinct_country_years(self):
        r = audit_verified_rows([event(2025), event(2025, loss="40")],
                                [indicator(**{"2024": "1"}),
                                 indicator(code="B2", **{"2024": "2"})])
        self.assertEqual(r["event_count_with_exact_country_prior_year_indicator"], 2)
        self.assertEqual(r["distinct_country_year_context_pairs"], 1)
        self.assertEqual(r["indicator_presence_event_multiplicity_not_stock"], 4)
        self.assertEqual(r["matched_event_count_with_reported_economic_loss_field"], 1)

    def test_missing_is_not_zero(self):
        r = audit_verified_rows([event(2025)], [indicator(**{"2023": "0"})])
        self.assertEqual(r["event_count_without_exact_country_prior_year_indicator"], 1)

    def test_duplicate_indicators_rejected(self):
        with self.assertRaises(AvailabilityError):
            audit_verified_rows([event()], [indicator(), indicator()])

    def test_invalid_dates_or_codes_rejected(self):
        for row in [event(country=" de"), event(year=2025)|{"start_date":"2025-02-30"},
                    event(year=2025)|{"event_start_date_year":"2024"}]:
            with self.subTest(row=row), self.assertRaises(AvailabilityError):
                audit_verified_rows([row], [indicator()])

    def test_no_provider_row_values_emitted(self):
        r = audit_verified_rows([event(2025, loss="1234567890")],
                                [indicator(**{"2024": "9876543210"})])
        self.assertNotIn("1234567890", str(r))
        self.assertNotIn("9876543210", str(r))
        self.assertFalse(r["source_rows_or_indicator_values_emitted"])
        self.assertFalse(r["source_admitted"])

    def test_empty_sources_rejected(self):
        with self.assertRaises(AvailabilityError):
            audit_verified_rows([], [indicator()])
        with self.assertRaises(AvailabilityError):
            audit_verified_rows([event()], [])


if __name__ == "__main__":
    unittest.main()
