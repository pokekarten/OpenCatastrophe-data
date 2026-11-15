# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed, source-dated legal-entity resolution for named insurer accounts.

No GLEIF/provider HTTP requests, no property sites, no insurance renewals and
no database writes. A verified regulator LEI identity is distinct from the
Senate's observation of a historical company insurance relationship.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.gleif_level1_insurer_identity_pilot import valid_lei  # noqa: E402
from public_named_corporate_insurer_report_v0 import (  # noqa: E402
    SOURCE as SENATE,
    project as project_named_accounts,
)

PREFLIGHT = ROOT / "research/observations/berlin_named_carrier_lei_temporal_preflight_20261105_v0.toml"
SENATE_URL = "https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr/S19-22033.pdf"
RVA_REGULATOR = "https://acpr.banque-france.fr/fr/fiche-detaillee/rv-allgemeine-versicherung-aktiengesellschaft-0"
PROVINZIAL_MERGER = "https://www.fma.gv.at/bestanduebertragung-von-der-westfaelische-provinzial-versicherung-aktiengesellschaft-auf-die-provinzial-versicherung-ag-ehemals-provinzial-rheinland-versicherung-ag/"
BRANCH_SOURCE = "https://lei.bloomberg.com/leis/view/815600FA8F92119B8D12"
ALLOWED = {
    "R+V Allgemeine Versicherung AG": "regulator_identity_correspondence",
    "Allianz AG": "unresolved_issuer_short_name",
    "ERGO": "unresolved_brand_label",
    "Generali": "unresolved_brand_label",
    "Westfälische Provinzial Versicherung AG": "historical_merged_entity_label",
}
RVA = "R+V Allgemeine Versicherung AG"
WPV = "Westfälische Provinzial Versicherung AG"
FORBIDDEN_TRUE_FLAGS = (
    "contracts_in_2026_independently_verified",
    "real_insured_buildings_observed",
    "co_insurance_fraction_verified",
)
MAX_INPUT = 128_000


def reject(message: str) -> None:
    raise ValueError(message)


def validate(preflight: dict, senate: dict, *, senate_sha256: str, preflight_sha256: str) -> dict:
    if (preflight.get("schema_version") != "BERLIN_NAMED_CARRIER_LEI_TEMPORAL_PREFLIGHT_V0"
            or preflight.get("research_review_date") != "2026-11-05"
            or preflight.get("source_senate_document") != "Drucksache 19/22033"
            or preflight.get("source_senate_issuer_date") != "2025-04-01"
            or preflight.get("source_senate_original_url") != SENATE_URL
            or preflight.get("source_observation_path") != SENATE.relative_to(ROOT).as_posix()):
        reject("carrier legal identity research source/version changed")
    for flag in (
        "original_regulator_or_gleif_http_json_hashed_in_this_preflight",
        "current_2026_carrier_contracts_proven",
        "all_carrier_labels_resolution_complete",
        "real_insured_site_locations_admitted",
        "corporate_stock_equal_insured_assets",
        "carrier_group_consolidation_permitted",
    ):
        if preflight.get(flag) is not False:
            reject("attempt to convert legal-entity research into model or full carrier verification")

    named = project_named_accounts(senate, source_sha256=senate_sha256)
    actual_labels = set(named["reported_carrier_labels"])
    if actual_labels != set(ALLOWED):
        reject("named-insurer source labels changed")
    rows = preflight.get("source_carriers")
    if not isinstance(rows, list) or len(rows) != len(ALLOWED):
        reject("expected exactly five legal identity review labels")
    by_name: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict):
            reject("invalid legal identity research record")
        name = row.get("reported_label")
        if not isinstance(name, str) or name not in ALLOWED or name in by_name:
            reject("unknown, duplicate or missing original insurer name")
        if row.get("resolution") != ALLOWED[name]:
            reject("identity resolution status violates original-source evidence")
        for flag in FORBIDDEN_TRUE_FLAGS:
            if row.get(flag) is not False:
                reject("legal-entity match cannot assert insurance risk or policy renewal")
        for key in (
            "resolved_lei", "resolved_legal_name", "resolved_jurisdiction",
            "regulator_identity_source_url", "regulator_identity_evidence",
            "unassigned_similarly_named_lei", "unassigned_similarly_named_lei_source_url",
            "unassigned_similarly_named_lei_reason", "possible_successor_legal_name",
            "successor_source_url", "historical_change_effective_date",
        ):
            if not isinstance(row.get(key), str):
                reject("legal-entity research record has missing typed evidence field")
        for key in ("resolved_lei", "unassigned_similarly_named_lei"):
            lei = row[key]
            if lei and not valid_lei(lei):
                reject("invalid ISO 17442 LEI checksum")
        by_name[name] = row
    if set(by_name) != actual_labels:
        reject("source carrier names and legal entity research differ")

    direct = by_name[RVA]
    if (direct["resolved_lei"] != "5299009UN4CBXZ336M65"
            or direct["resolved_legal_name"] != "R+V Allgemeine Versicherung Aktiengesellschaft"
            or direct["resolved_jurisdiction"] != "DE"
            or direct["regulator_identity_source_url"] != RVA_REGULATOR
            or "225615" not in direct["regulator_identity_evidence"]
            or direct["unassigned_similarly_named_lei"] != "815600FA8F92119B8D12"
            or direct["unassigned_similarly_named_lei_source_url"] != BRANCH_SOURCE
            or "branch" not in direct["unassigned_similarly_named_lei_reason"].lower()):
        reject("R+V German head-office LEI / Italian branch LEI collision not controlled")

    allianz = by_name["Allianz AG"]
    generali = by_name["Generali"]
    if (allianz["unassigned_similarly_named_lei"] != "529900X5FHSYN4P5R285"
            or allianz["unassigned_similarly_named_lei_source_url"] !=
            "https://acpr.banque-france.fr/fr/fiche-detaillee/allianz-versicherungs-aktiengesellschaft"
            or generali["unassigned_similarly_named_lei"] != "5493007JO8UEQ68NG776"
            or generali["unassigned_similarly_named_lei_source_url"] !=
            "https://acpr.banque-france.fr/fr/fiche-detaillee/generali-deutschland-versicherung-ag-0"):
        reject("ambiguous carrier candidate identity evidence drift")
    wpv = by_name[WPV]
    if (wpv["possible_successor_legal_name"] != "Provinzial Versicherung AG"
            or wpv["successor_source_url"] != PROVINZIAL_MERGER
            or wpv["historical_change_effective_date"] != "2021-01-01"):
        reject("2021 merged Provinzial legacy label lost its historical gate")
    for name, row in by_name.items():
        if name != RVA and (
            row["resolved_lei"] or row["resolved_legal_name"] or row["resolved_jurisdiction"]
            or row["regulator_identity_source_url"]
        ):
            reject("ambiguous/merged insurer label given an unsupported exact LEI")
        if name != WPV and (
            row["possible_successor_legal_name"] or row["successor_source_url"]
            or row["historical_change_effective_date"]
        ):
            reject("invented corporate successor or merger date")
        if name == "ERGO" and (
            row["unassigned_similarly_named_lei"]
            or row["unassigned_similarly_named_lei_source_url"]
        ):
            reject("unverified ERGO brand was assigned a candidate legal entity")

    output_edges = []
    for edge in named["carrier_account_edges"]:
        carrier = edge["reported_carrier_label"]
        row = by_name[carrier]
        output_edges.append({
            "senate_reported_insurer": carrier,
            "senate_reported_corporate_account": edge["reported_corporate_account"],
            "historical_relationship_as_of": edge["relationship_date"],
            "relationship_evidence_class": edge["relationship_evidence_class"],
            "source_reported_coinsurance_consortium": edge[
                "member_of_insurer_consortium_explicitly_reported"],
            "entity_resolution_status": row["resolution"],
            "regulator_identified_legal_entity_lei": row["resolved_lei"] or None,
            "regulator_identified_legal_name": row["resolved_legal_name"] or None,
            "candidate_lei_not_joined": row["unassigned_similarly_named_lei"] or None,
            "source_documented_legal_successor_not_contract_verified": (
                row["possible_successor_legal_name"] or None
            ),
            "actual_covered_buildings_or_tiv_verified": False,
            "2026_contract_renewal_verified": False,
            "automatic_portfolio_or_group_aggregation_allowed": False,
        })
    output_edges.sort(key=lambda r: (
        r["senate_reported_insurer"], r["senate_reported_corporate_account"],
    ))
    if len(output_edges) != 8 or sum(
        x["regulator_identified_legal_entity_lei"] is not None for x in output_edges
    ) != 3:
        reject("unexpected company/carrier or resolved R+V evidence count")
    return {
        "schema_version": "PUBLIC_NAMED_CARRIER_ACCOUNT_LEGAL_IDENTITY_REPORT_V0",
        "report_status": "research_only_partial_identity_preflight_not_cat_admitted",
        "source_receipts": {
            "senate_toml_sha256": senate_sha256,
            "legal_identity_preflight_toml_sha256": preflight_sha256,
            "official_senate_pdf_url": SENATE_URL,
            "original_GLEIF_regulator_http_body_hashed_this_run": False,
        },
        "resolved_distinct_senate_carrier_names": 1,
        "unresolved_or_legacy_distinct_senate_carrier_names": 4,
        "distinct_senate_carrier_names": 5,
        "named_company_carrier_relationships": output_edges,
        "legal_identity_and_portfolio_safety": {
            "italian_RV_branch_is_independent_german_primary_insurer": False,
            "allianz_short_name_auto_resolved": False,
            "ergo_or_generali_brand_auto_resolved": False,
            "merged_wpv_treated_as_active_legal_entity_in_2025": False,
            "historical_merged_legal_entity_auto_substituted_as_insurer_in_2025": False,
            "company_relationship_proves_insured_buildings": False,
            "insurer_legal_identity_implies_company_CAT_TIV": False,
            "2026_cover_renewal_or_contract_ownership_verified": False,
        },
    }


def read_and_project(senate_path: Path = SENATE, preflight_path: Path = PREFLIGHT) -> dict:
    try:
        blobs = (senate_path.read_bytes(), preflight_path.read_bytes())
        if any(not 0 < len(raw) <= MAX_INPUT for raw in blobs):
            reject("unbounded or missing original research record")
        senate, preflight = (tomllib.loads(raw.decode("utf-8")) for raw in blobs)
        return validate(
            preflight, senate,
            senate_sha256=hashlib.sha256(blobs[0]).hexdigest(),
            preflight_sha256=hashlib.sha256(blobs[1]).hexdigest(),
        )
    except (OSError, ValueError, UnicodeError, tomllib.TOMLDecodeError):
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--senate", type=Path, default=SENATE)
    parser.add_argument("--identity-preflight", type=Path, default=PREFLIGHT)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(
            read_and_project(args.senate, args.identity_preflight),
            sort_keys=True, ensure_ascii=False, indent=2,
        ))
    except (OSError, ValueError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
