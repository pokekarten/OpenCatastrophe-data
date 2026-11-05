# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Compare observed corporate dwelling stocks across *named* insurers.

The output is a RESEARCH REFERENCE to public company housing stock and source-
named company insurance contracts, never an insured building, policy or TIV.
Overlapping corporate stock occurs under multiple carriers; sums across
carrier names are prohibited. No source download or DB write is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tomllib
from pathlib import Path

from public_named_corporate_insurer_report_v0 import project as project_accounts
from rva_berlin_named_corporate_borough_opportunity_sensitivity_v0 import (
    INSURER, STOCK, validate as validate_borough_stock,
)

COMPANY_TO_STOCK = {
    "degewo AG": "degewo",
    "GESOBAU AG": "gesobau",
    "WBM Wohnungsbaugesellschaft Berlin-Mitte mbH": "wbm",
    "Gewobag Wohnungsbau-Aktiengesellschaft Berlin": "gewobag",
    "HOWOGE Wohnungsbaugesellschaft mbH": "howoge",
    "STADT UND LAND Wohnbauten-Gesellschaft mbH": "stadt_und_land",
}
MAX_BYTES = 256_000


def build(stock: dict, insurer: dict, *, insurer_sha256: str, stock_sha256: str) -> dict:
    # The existing validated R+V runner checks the independent original PDF
    # receipt alongside all seven 2025 stock columns, all 12 borough rows and
    # the six company-insurer relationships; it does not assert insured sites.
    validated = validate_borough_stock(stock, insurer)
    named = project_accounts(insurer, source_sha256=insurer_sha256)
    if (named["named_corporate_accounts_count"] != 6
            or set(COMPANY_TO_STOCK) !=
            {e["reported_corporate_account"] for e in named["carrier_account_edges"]}):
        raise ValueError("named corporate insurer accounts do not match stock identities")
    if (validated["official_source_pdf_provenance"].get(
            "official_2025_senate_two_original_pdf_hashes_matched") is not True):
        raise ValueError("independent original Senate PDF provenance missing")

    indexed_rows = validated["boroughs"]
    reported_company_totals = validated["published_company_totals"]
    other_not_geocoded = validated["published_other_not_borough_assignable"]
    by_carrier: dict[str, list[dict]] = {}
    for edge in named["carrier_account_edges"]:
        carrier = edge["reported_carrier_label"]
        by_carrier.setdefault(carrier, []).append(edge)

    carriers = []
    for carrier in sorted(by_carrier):
        company_edges = sorted(by_carrier[carrier], key=lambda e: e["reported_corporate_account"])
        used_keys = [COMPANY_TO_STOCK[e["reported_corporate_account"]] for e in company_edges]
        if len(used_keys) != len(set(used_keys)):
            raise ValueError("duplicate company membership in carrier association list")
        observed_company_dwelling_total = sum(reported_company_totals[k] for k in used_keys)
        unassigned_total = sum(other_not_geocoded[k] for k in used_keys)
        boroughs = []
        for source_row in sorted(indexed_rows, key=lambda x: x["borough_name"]):
            components = {
                e["reported_corporate_account"]: source_row[
                    COMPANY_TO_STOCK[e["reported_corporate_account"]]
                ]
                for e in company_edges
            }
            boroughs.append({
                "borough": source_row["borough_name"],
                "published_corporate_dwelling_count_for_named_accounts": sum(components.values()),
                "per_company_published_corporate_dwelling_count": components,
                "number_of_carrier_insured_dwellings_observed": False,
            })
        assigned = sum(row["published_corporate_dwelling_count_for_named_accounts"] for row in boroughs)
        if assigned + unassigned_total != observed_company_dwelling_total:
            raise ValueError("published corporate stock disagrees with 12 boroughs and other category")
        carriers.append({
            "original_reported_carrier_label": carrier,
            "carrier_lei_verified": False,
            "named_corporate_accounts": [e["reported_corporate_account"] for e in company_edges],
            "source_reported_coinsurance_consortium_accounts": [
                e["reported_corporate_account"] for e in company_edges
                if e["member_of_insurer_consortium_explicitly_reported"]
            ],
            "public_stock_corporate_dwelling_total_including_unassigned": observed_company_dwelling_total,
            "public_stock_corporate_dwelling_total_in_12_berlin_boroughs": assigned,
            "public_stock_corporate_dwelling_total_unassigned_other": unassigned_total,
            "boroughs": boroughs,
            "full_corporate_dwelling_stock_insured_by_this_carrier_observed": False,
            "carrier_real_insured_location_count_observed": False,
            "carrier_real_insured_tiv_observed": False,
            "carrier_real_coinsurance_share_observed": False,
            "carrier_2026_policy_renewal_observed": False,
        })

    if len(carriers) != 5 or sum(len(x["named_corporate_accounts"]) for x in carriers) != 8:
        raise ValueError("carrier/account relation population changed")

    return {
        "schema_version": "PUBLIC_NAMED_INSURER_BERLIN_CORPORATE_STOCK_REFERENCE_V0",
        "report_status": "research_only_not_insured_exposure_not_admitted",
        "source_provenance": {
            "insurer_accounts_original_senate_pdf": insurer["source_official_url"],
            "independent_borough_stock_original_senate_pdf": stock["source_official_url"],
            "carrier_relation_as_of": "2025-04-01",
            "company_borough_dwelling_stock_as_of": "2025-06-30",
            "berlinovo_stock_as_of_but_not_a_named_carrier_account": "2025-09-30",
            "existing_independent_original_source_pdf_receipt_checked": True,
            "original_pdfs_redownloaded_by_this_export": False,
            "insurer_observation_sha256": insurer_sha256,
            "dwelling_stock_observation_sha256": stock_sha256,
        },
        "separate_carrier_name_count": 5,
        "named_company_count": 6,
        "named_carrier_company_association_count": 8,
        "carrier_views": carriers,
        "aggregation_restrictions": {
            "across_carriers_additive": False,
            "carrier_company_stock_equivalent_to_insured_dwellings": False,
            "housing_dwellings_equal_individual_buildings": False,
            "insured_sites_or_tiv_known": False,
            "co_insurance_shares_known": False,
            "cat_model_loss_calibration_available": False,
        },
        "research_limitations": [
            "Named building insurers from April 2025 are not verified 2026 active insurers.",
            "June 2025 landlord dwelling stock is not a verified schedule of buildings covered in April.",
            "Allianz and R+V both name degewo; ERGO and Generali both name Gewobag. These corporate dwelling counts overlap by carrier, so carrier totals must not be summed.",
            "An original source naming several carriers does not prove an equal participation, full corporate stock coverage or exclusive insurer contract.",
            "Observed corporate dwellings are not insured buildings, insured policies, replacement cost, sums insured, retained loss or an OEP/AEP distribution.",
            "Original insurer name strings have not been matched to unique LEIs or group perimeter.",
        ],
    }


def run(insurer_path: Path = INSURER, stock_path: Path = STOCK) -> dict:
    blobs = [p.read_bytes() for p in (insurer_path, stock_path)]
    if any(len(x) > MAX_BYTES for x in blobs):
        raise ValueError("source observation input too large")
    insurer, stock = [tomllib.loads(blob.decode("utf-8")) for blob in blobs]
    return build(
        stock, insurer,
        insurer_sha256=hashlib.sha256(blobs[0]).hexdigest(),
        stock_sha256=hashlib.sha256(blobs[1]).hexdigest(),
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--insurer", type=Path, default=INSURER)
    p.add_argument("--stock", type=Path, default=STOCK)
    args = p.parse_args(argv)
    try:
        print(json.dumps(run(args.insurer, args.stock), sort_keys=True,
                         ensure_ascii=False, indent=2))
    except (OSError, UnicodeError, ValueError, tomllib.TOMLDecodeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
