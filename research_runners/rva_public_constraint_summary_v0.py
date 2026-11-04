# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Public R+V *accounting* and group event context only; no actual CAT portfolio."""

import argparse
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HISTORY = ROOT / "research/observations/rva_solo_hgb_property_2019_2025_v0.toml"
DEFAULT_SIGNALS = ROOT / "research/observations/rva_public_event_tariff_distribution_signals_v0.toml"

def q(value, digits=2):
    quant = Decimal(1).scaleb(-digits)
    return format(value.quantize(quant, rounding=ROUND_HALF_UP), f".{digits}f")

def public_receipt(history, signals):
    if history.get("entity") != "R+V Allgemeine Versicherung AG" or signals.get("target_legal_entity") != history["entity"]:
        raise ValueError("Refuse mismatched legal entity")
    if any(signals.get(k) is not False for k in (
        "company_insured_address_observed", "company_regional_portfolio_shares_observed",
        "company_peril_specific_solo_loss_observed", "production_calibration_authorized")):
        raise ValueError("Public signals cannot assert actual insurer CAT portfolio")
    contracts = history["building_contract_observations"]
    if contracts.get("unit") != "contracts" or contracts.get("company_natcat_covered_building_count_observed") is not False:
        raise ValueError("Contracts do not identify actual covered buildings")
    policy_rows = contracts["years"]
    if [r["year"] for r in policy_rows] != [2023, 2024, 2025]:
        raise ValueError("Issuer policy years incorrect")
    claims = history["building_gross_claims_observations"]
    if claims.get("observed_peril_split") is not False or claims.get("observed_event_split") is not False:
        raise ValueError("Original HGB claims cannot be treated as NatCat")
    claim_by_year = {r["year"]: Decimal(r["gross_claims_eur"]) for r in claims["years"]}
    premium_by_year = {r["year"]: Decimal(r["connected_buildings_self_written"]) * Decimal(1000) for r in history["years"]}
    rows = []
    for r in policy_rows:
        year, count = r["year"], r["contracts"]
        premium = premium_by_year[year]
        if count <= 0 or premium <= 0:
            raise ValueError("Invalid HGB scale")
        out = {
            "year": year,
            "observed_year_end_connected_building_contracts": count,
            "observed_hgb_self_written_connected_building_gwp_eur": q(premium,0),
            "derived_booked_gwp_over_year_end_contract_eur": q(premium / Decimal(count)),
            "derived_ratio_not_tariff_rate": True,
            "regional_policy_share_observed": False,
            "insurance_tiv_observed": False,
            "cat_peril_gross_loss_observed": False,
            "merger_scope_break": r["perimeter_break"]
        }
        if year in claim_by_year:
            value = claim_by_year[year]
            out.update({
                "observed_hgb_gross_all_cause_claim_expense_eur": q(value),
                "derived_all_cause_claim_expense_over_booked_gwp_percent": q(value/premium*100),
                "claims_not_event_peril_or_net": True
            })
        rows.append(out)
    es = signals["evidence"]
    if len({r["id"] for r in es}) != len(es) or any(
        x["solo_catastrophe_loss_calibration_admitted"] is not False
        or x["solo_geographic_exposure_admitted"] is not False for x in es
    ):
        raise ValueError("Uncontrolled source evidence")
    bernd = next(x for x in es if x["id"] == "ruv_bernd_flood_claims_report_20220707")
    if (bernd["scope"] != "group_customer_population_mixed_entities"
        or bernd["flood_coverage_population"] != "affected_R+V_customers_in_flood_areas_2021"):
        raise ValueError("Do not generalize selected 2021 group flood sample")
    group_2021_count = Decimal(bernd["claims"])
    group_2021_large = Decimal(bernd["large_claims"])
    group_2021_total = Decimal(bernd["amount"])
    group_2021_large_eur = Decimal(bernd["large_claims_amount"])
    if group_2021_count < group_2021_large or group_2021_total < group_2021_large_eur:
        raise ValueError("Large loss counts/amounts must fit approximate whole event")
    hail_2024 = next(x for x in es if x["id"] == "ruv_hail_2024_followup_20250521")
    if (hail_2024["scope"] != "group_customer_population_mixed_entities"
        or hail_2024.get("motor_included") is not True):
        raise ValueError("Hail cannot be presented as solo property")
    total_hail, motor_hail = Decimal(hail_2024["amount"]), Decimal(hail_2024["motor_amount"])
    if total_hail < motor_hail:
        raise ValueError("Motor portion exceeds annual group total")
    return {
        "schema_version": "RVA_PUBLIC_CONSTRAINT_SUMMARY_V0",
        "target_legal_entity": history["entity"],
        "company_aggregate_hgb_connected_buildings": rows,
        "group_public_claims_context": {
            "bernd_2021_reported_large_claim_share_percent_approx": q(group_2021_large/group_2021_count*100),
            "bernd_2021_reported_large_claim_amount_share_percent_approx": q(group_2021_large_eur/group_2021_total*100),
            "bernd_2021_flood_area_cover_fraction_conditional": bernd["flood_coverage_fraction"],
            "hail_2024_reported_group_non_motor_residual_eur_million_approx": q(total_hail-motor_hail,0),
            "group_report_not_solo_company_loss": True,
            "2024_nonmotor_hail_not_equivalent_to_building_hail": True
        },
        "admission": {
            "model_input_approved": False,
            "company_geocoded_location_ready": False,
            "company_tiv_observed": False,
            "company_natural_perils_covered_risks_observed": False,
            "actual_company_event_cat_gul_or_net_observed": False,
            "oasis_calibrated": False
        },
        "interpretation": "Observational insurer contract+finance benchmark and separate cross-entity group claim context. GWP/year-end contracts is not a tariff, and HGB all-cause claims are not CAT claims."
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY)
    parser.add_argument("--signals", type=Path, default=DEFAULT_SIGNALS)
    args = parser.parse_args()
    a, b = args.history.read_bytes(), args.signals.read_bytes()
    h, s = tomllib.loads(a.decode("utf-8")), tomllib.loads(b.decode("utf-8"))
    receipt = public_receipt(h, s)
    receipt["input_sha256"] = {"issuer_history_toml": hashlib.sha256(a).hexdigest(),
                                 "group_signals_toml": hashlib.sha256(b).hexdigest()}
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2))

if __name__ == "__main__":
    main()
