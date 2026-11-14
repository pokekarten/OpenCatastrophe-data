# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Issuer IFRS and procurement source cross-check: NO automatic insurer exposure.

The public 2024 Gewobag ADO stock is an opportunity *subset candidate*, and
the WBM 2026 nine-commercial-object tender is not its 2025 residential stock.
Read-only deterministic JSON; requires existing original Senate PDF receipts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tomllib
from pathlib import Path

from rva_berlin_named_corporate_borough_opportunity_sensitivity_v0 import (
    STOCK, INSURER, validate as validate_senate,
)

ROOT = Path(__file__).resolve().parents[1]
SEGMENTS = ROOT / "research/observations/berlin_lwu_procurement_named_property_segments_20261105_v0.toml"
MAX_BYTES = 250_000
TENDER_ID = "558592-2024"
AWARD_ID = "668506-2026"
IFRS_URL = "https://berichte.gewobag.de/fileadmin/assets_2024/PDFs/Gewobag-Geschaefts-und-Nachhaltigkeitsbericht-2024-IFRS.pdf"
WINNERS = ("HDI Global SE", "Helvetia Schweizerische Versicherungsgesellschaft AG",
           "R+V Allgemeine Versicherung AG")


def reject(reason: str):
    raise ValueError(reason)


def checked(source: dict, stock: dict, insurer: dict,
            *, hashes: dict[str, str]) -> dict:
    audit = validate_senate(stock, insurer)
    if (source.get("schema_version") != "BERLIN_LWU_PROCUREMENT_NAMED_PROPERTY_SEGMENTS_V0"
            or source.get("review_date") != "2026-11-05"):
        reject("source scope or version changed")
    for field in (
        "source_original_ted_http_bytes_checked_this_run",
        "source_original_ifrs_pdf_sha256_checked_this_run",
        "source_broker_or_award_mirror_is_primary_contract",
        "public_stock_cohorts_independent_of_2025_lwu_stock_verified",
        "individual_insured_buildings_observed",
        "insured_site_geocodes_observed",
        "carrier_specific_building_allocation_observed",
        "market_fair_value_equals_cat_reinstatement_tiv",
        "awarded_named_insurers_equal_coverage_per_object",
        "model_cat_exposure_admitted",
    ):
        if source.get(field) is not False:
            reject("public tender/market value promoted into measured insurance exposure")

    tender = source.get("gewobag_2024_tender")
    if not isinstance(tender, dict) or (
        tender.get("buyer") != "Gewobag Wohnungsbau-Aktiengesellschaft Berlin"
        or tender.get("procurement_reference") != "Gewobag 221-24"
        or tender.get("ted_notice_id") != TENDER_ID
        or tender.get("ted_notice_url") != "https://ted.europa.eu/en/notice/-/detail/" + TENDER_ID
        or tender.get("public_notice_mirror_url") !=
        "https://de.openprocurements.com/tender/2024-gebaudeversicherung-mkn/"
        or tender.get("notice_published") != "2024-09-13"
        or tender.get("bid_deadline") != "2024-10-16"
        or tender.get("historical_ado_purchase_date") != "2019-12-01"
        or tender.get("historical_ado_dwellings_rounded_in_notice") != 6000
        or tender.get("historical_ado_named_boroughs") != ["Spandau", "Reinickendorf"]
        or tender.get("tender_option_increase_usable_floor_area_pct_max") != 10
        or tender.get("main_contract_and_separate_acquired_stock_contract_described") is not True
        or tender.get("historical_2024_01_01_main_contract_conditions_changed") is not True
    ):
        reject("2024 Gewobag 221-24 source or historical ADO cohort drift")
    for field in (
        "original_ted_notice_download_sha256_verified",
        "actual_awarded_carrier_legal_names_verified_from_this_notice",
        "contract_ended_and_2026_carrier_coverage_verified",
        "historical_ado_rounded_count_is_exact_2024_dwellings",
        "tender_option_is_realised_growth_or_2025_insured_risk",
    ):
        if tender.get(field) is not False:
            reject("2024 Gewobag tender overclaimed as award, exact cohort or coverage")

    ifrs = source.get("gewobag_2024_ado_issuer_ifrs")
    if not isinstance(ifrs, dict) or (
        ifrs.get("issuer") != "Gewobag Wohnungsbau-Aktiengesellschaft Berlin"
        or ifrs.get("report_url") != IFRS_URL
        or ifrs.get("report_printed_page") != 54
        or ifrs.get("valuation_date") != "2024-12-31"
        or ifrs.get("acquisition_origin") != "ADO Properties S.A."
        or ifrs.get("acquisition_year") != 2019
        or ifrs.get("reported_property_objects") != 21
        or ifrs.get("reported_residential_dwellings") != 5894
        or ifrs.get("reported_commercial_units") != 65
        or ifrs.get("reported_parking_spaces") != 1433
        or ifrs.get("reported_other_units") != 139
        or ifrs.get("reported_market_fair_value_eur_thousand") != 821190
        or ifrs.get("reported_prior_year_market_fair_value_eur_thousand") != 819481
        or ifrs.get("reported_potential_densification_component_eur_thousand") != 15010
        or ifrs.get("valuation_company") != "CBRE GmbH"
        or ifrs.get("2019_acquisition_rounded_tender_6000_must_not_be_added_to_5894") is not True
        or ifrs.get("source_report_is_2024_ifrs_not_2025_insurer_policy_schedule") is not True
    ):
        reject("publisher original 2024 IFRS ADO segment numbers or accounting scope changed")
    for field in (
        "reported_market_value_is_insured_tiv",
        "reported_property_objects_are_verified_individual_building_footprints",
        "source_original_pdf_sha256_verified",
    ):
        if ifrs.get(field) is not False:
            reject("market value or original PDF provenance incorrectly represented as insurer TIV")

    award = source.get("wbm_2026_commercial_award")
    if not isinstance(award, dict) or (
        award.get("buyer") != "WBM Wohnungsbaugesellschaft Berlin-Mitte mbH"
        or award.get("ted_notice_id") != AWARD_ID
        or award.get("ted_notice_url") != "https://ted.europa.eu/en/notice/-/detail/" + AWARD_ID
        or award.get("public_notice_mirror_url") !=
        "https://auftragsatlas.de/ausschreibung/industrielle-sachversicherung-fuer-reine-gewerbeobjekte-1172391"
        or award.get("award_date") != "2026-09-21"
        or award.get("publication_date") != "2026-09-29"
        or award.get("reported_pure_commercial_objects") != 9
        or award.get("reported_award_value_eur") != 0
        or set(award.get("reported_winners", [])) != set(WINNERS)
        or len(award.get("reported_winners", [])) != len(WINNERS)
        or award.get("reported_zero_is_placeholder_not_contract_premium_or_insured_tiv") is not True
    ):
        reject("WBM September 2026 commercial award original notice metadata changed")
    for field in (
        "official_ted_eforms_original_http_bytes_verified",
        "each_winner_covers_all_nine_objects_proven",
        "carrier_share_and_policy_limits_disclosed",
        "actual_location_coordinates_known",
        "commercial_objects_are_2025_wbm_residential_dwellings",
        "award_date_proves_2025_residential_carrier_contract",
    ):
        if award.get(field) is not False:
            reject("commercial award wrongly projected to 2025 residential risks")

    if (audit["published_company_totals"]["gewobag"] != 75091
            or audit["published_company_totals"]["wbm"] != 34040
            or audit["official_source_pdf_provenance"].get(
                "official_2025_senate_two_original_pdf_hashes_matched") is not True):
        reject("2025 housing stock and original PDF provenance not reconciled")

    return {
        "schema_version": "BERLIN_PUBLIC_HOUSING_PROPERTY_SEGMENT_CROSSCHECK_V0",
        "research_only_not_admitted": True,
        "typed_source_sha256": hashes,
        "independent_official_senate_original_pdf_receipt_checked": True,
        "original_ted_or_ifrs_external_source_bytes_verified_this_run": False,
        "segments": {
            "gewobag_2019_ado_2024_ifrs": {
                "property_objects": 21,
                "dwellings": 5894,
                "commercial_units": 65,
                "parking_spaces": 1433,
                "other_units": 139,
                "year_end_2024_market_fair_value_eur_thousand": 821190,
                "potential_development_component_in_market_value_eur_thousand": 15010,
                "2024_report_url": IFRS_URL,
                "tender_2024_reference": TENDER_ID,
                "independently_observed_2025_gewobag_corporate_dwelling_total": 75091,
                "ado_2024_subset_membership_in_2025_total_individually_crosswalk_verified": False,
                "market_fair_value_means_insured_reinstatement_tiv": False,
                "tender_rounded_six_thousand_dwellings_is_separate_added_stock": False,
                "claim_of_2026_insurer_winning_this_tender": False,
            },
            "wbm_september_2026_pure_commercial": {
                "tender_award_id": AWARD_ID,
                "pure_commercial_objects_described": 9,
                "named_awardees": sorted(WINNERS),
                "independently_observed_2025_wbm_corporate_residential_dwelling_total": 34040,
                "exact_carrier_allocation_of_nine_objects_observed": False,
                "nine_objects_are_2025_residential_dwelling_policy_count": False,
                "three_awardees_means_twenty_seven_distinct_insured_objects": False,
                "2026_zero_award_value_is_actual_tiv_or_premium": False,
            },
        },
        "unresolved": [
            "2024 Gewobag tender winner and any 2025/2026 actual insurer contract allocation are not verified.",
            "ADO purchased cohort is not additive to 2025 Gewobag stock; exact same-asset mapping and insured status remain unknown.",
            "2024 investment-property IFRS market fair value is not replacement value or an insurance limit.",
            "WBM 2026 award reports three names and nine commercial objects but not per-carrier object allocation, limit or net/gross TIV.",
            "2026 WBM commercial property segment is separate from 2025 Senate residential dwelling totals.",
        ],
    }


def run(segment_path: Path = SEGMENTS, stock_path: Path = STOCK,
        insurer_path: Path = INSURER) -> dict:
    paths = {"segments": segment_path, "stock": stock_path, "insurer": insurer_path}
    contents = {name: path.read_bytes() for name, path in paths.items()}
    if any(not 0 < len(value) <= MAX_BYTES for value in contents.values()):
        reject("missing or oversized bounded observation")
    decoded = {name: tomllib.loads(value.decode("utf-8")) for name, value in contents.items()}
    return checked(decoded["segments"], decoded["stock"], decoded["insurer"],
                   hashes={name: hashlib.sha256(value).hexdigest()
                           for name, value in contents.items()})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--segments", type=Path, default=SEGMENTS)
    ap.add_argument("--stock", type=Path, default=STOCK)
    ap.add_argument("--insurer", type=Path, default=INSURER)
    args = ap.parse_args(argv)
    try:
        print(json.dumps(run(args.segments, args.stock, args.insurer),
                         ensure_ascii=False, sort_keys=True, indent=2))
    except (OSError, UnicodeError, ValueError, tomllib.TOMLDecodeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
