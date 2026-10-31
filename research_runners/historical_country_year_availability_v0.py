#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Non-loss, previous-year availability comparison of two *already verified* CSVs.

This diagnostic is intentionally not a flood-impact/exposure model join. A country
and calendar-year match does not identify event-footprint exposure, property sums,
insurance coverage, peril-specific vulnerability or time-of-day loss. The calling
provider-byte verifier must validate the exact original bytes first.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date
import re
from typing import Mapping, Iterable


class AvailabilityError(ValueError):
    """A supposedly verified source row violates the safe comparison contract."""


COUNTRY_CODE = re.compile(r"[A-Z][A-Z0-9]{1,7}\Z", re.ASCII)
YEAR_START, YEAR_END = 2000, 2024


def audit_verified_rows(
    event_rows: Iterable[Mapping[str, str]],
    exposure_rows: Iterable[Mapping[str, str]],
) -> dict:
    """Count exact country/prior-year *availability*, never output source values.

    Call only AFTER the version-pinned HANZE v3.0.2 beta and European residential
    v2025 CSV preflights have both passed (including byte SHA-256 checks). Annual
    building-value indicators are checked only for presence; their values, units
    and individual country/event records are neither returned nor aggregated.
    """
    available: dict[tuple[str, int], set[str]] = defaultdict(set)
    observed_indicator_keys: set[tuple[str, str]] = set()
    exposure_count = 0
    for row in exposure_rows:
        exposure_count += 1
        country_raw = row.get("CountryCode")
        indicator_raw = row.get("IndicatorCode")
        country = country_raw.strip() if isinstance(country_raw, str) else ""
        indicator = indicator_raw.strip() if isinstance(indicator_raw, str) else ""
        if not COUNTRY_CODE.fullmatch(country):
            raise AvailabilityError("invalid residential source geography")
        if not indicator:
            raise AvailabilityError("invalid residential indicator identity")
        identity = (country, indicator)
        if identity in observed_indicator_keys:
            raise AvailabilityError("duplicate country/indicator identity")
        observed_indicator_keys.add(identity)
        # EU is a group total, not an additional country exposure observation.
        if country == "EU":
            continue
        for year in range(YEAR_START, YEAR_END + 1):
            raw = row.get(str(year))
            if not isinstance(raw, str):
                raise AvailabilityError("missing/malformed residential annual cell")
            if raw.strip() != "":
                # Values are independently validated in the pinned provider preflight.
                # The string "0" is present and must not be treated as missing.
                available[(country, year)].add(indicator)

    if not exposure_count:
        raise AvailabilityError("empty residential source")

    events = eligible = matched = unmatched = outside = 0
    losses_present_matched = 0
    matched_year_countries: set[tuple[str, int]] = set()
    matched_countries: set[str] = set()
    total_indicator_presence_event_multiplicity = 0
    for row in event_rows:
        events += 1
        country = row.get("country_code")
        start = row.get("start_date")
        raw_year = row.get("event_start_date_year")
        if not isinstance(country, str) or not COUNTRY_CODE.fullmatch(country):
            raise AvailabilityError("invalid event country identity")
        if not isinstance(start, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", start):
            raise AvailabilityError("invalid event start date")
        if not isinstance(raw_year, str) or not re.fullmatch(r"[0-9]{4}", raw_year):
            raise AvailabilityError("invalid event year")
        try:
            observed_year = date.fromisoformat(start).year
        except ValueError as exc:
            raise AvailabilityError("invalid Gregorian event date") from exc
        if observed_year != int(raw_year):
            raise AvailabilityError("inconsistent event year and start date")
        reference_year = observed_year - 1
        if reference_year < YEAR_START or reference_year > YEAR_END:
            outside += 1
            continue
        eligible += 1
        present = available.get((country, reference_year), set()) if country != "EU" else set()
        if not present:
            unmatched += 1
            continue
        matched += 1
        matched_countries.add(country)
        matched_year_countries.add((country, reference_year))
        total_indicator_presence_event_multiplicity += len(present)
        # A whitespace-only CSV cell is missing, exactly like an empty
        # cell. Zero ("0") is a genuinely reported value, not missing.
        # The independent provider preflight already validated finite
        # numeric content; this diagnostic records presence only.
        economic_loss = row.get("economic_loss_value_eur")
        if economic_loss is not None and not isinstance(economic_loss, str):
            raise AvailabilityError("invalid event economic-loss field type")
        if economic_loss is not None and economic_loss.strip() != "":
            losses_present_matched += 1

    if not events:
        raise AvailabilityError("empty event source")
    assert events == outside + matched + unmatched
    return {
        "schema_version": "historical-country-year-availability-v0",
        "evidence_class": "NON_ADMITTED_COUNTRY_LAG_YEAR_INDICATOR_PRESENCE_ONLY",
        "event_count": events,
        "event_count_outside_2001_2025_eligibility": outside,
        "event_count_eligible_for_previous_year": eligible,
        "event_count_with_exact_country_prior_year_indicator": matched,
        "event_count_without_exact_country_prior_year_indicator": unmatched,
        "matched_event_count_with_reported_economic_loss_field": losses_present_matched,
        "distinct_country_year_context_pairs": len(matched_year_countries),
        "distinct_matched_country_codes": len(matched_countries),
        "indicator_presence_event_multiplicity_not_stock": total_indicator_presence_event_multiplicity,
        "previous_year_rule": "event_start_year_minus_1",
        "country_identity_rule": "literal_codes_only_no_crosswalk_or_imputation",
        "aggregate_EU_row_excluded": True,
        "missing_is_not_zero": True,
        "modelled_flood_footprint": False,
        "asset_exposure_created": False,
        "insured_tiv_created": False,
        "insured_loss_created": False,
        "event_economic_loss_aggregated": False,
        "source_rows_or_indicator_values_emitted": False,
        "source_admitted": False,
        "limitations": [
            "Previous-year national indicator presence is not verified point-in-time exposure for an event.",
            "Country-level matches do not locate flooded assets or create a NUTS3 hazard footprint.",
            "Economic disaster impacts are not insured claims or insured sums.",
            "Only exactly equal country codes are compared; codes needing a crosswalk remain unmatched.",
        ],
    }
