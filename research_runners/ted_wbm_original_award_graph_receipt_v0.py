# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Verify exact WBM 2026 original eForms graph against saved research receipt.

A successful SHA-pinned original publisher XML replay + RES->CON->TEN->TPA->ORG
graph match conserves the legal award relationships. It does NOT validate a
signed policy schedule, carrier shares, insured properties or an exposure TIV.
"""
from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

from . import ted_wbm_eforms_winner_role_v0 as role
from .ted_berlin_insurance_original_xml_preflight_v0 import (
    SOURCES, fetch as fetch_original_xml,
)

REGISTER = (
    Path(__file__).resolve().parents[1] / "research" / "observations" /
    "ted_wbm_2026_original_eforms_award_graph_receipt_v0.toml"
)
SCHEMA = "TED_WBM_2026_OFFICIAL_EFORMS_AWARDED_CONTRACT_GRAPH_RECEIPT_V0"
FIELDS = (
    "lot_result_id", "lot_id", "settled_contract_id", "winning_tender_id",
    "winning_party_id",
)


def validate(report: dict, *, register: dict | None = None) -> dict:
    if register is None:
        register = tomllib.loads(REGISTER.read_text(encoding="utf-8"))
    spec = SOURCES[role.NOTICE]
    if (
        register.get("schema_version") != SCHEMA
        or register.get("notice_publication_number") != role.NOTICE
        or register.get("official_original_xml_url")
            != "https://ted.europa.eu/en/notice/668506-2026/xml"
        or register.get("source_original_xml_sha256")
            != spec["original_xml_sha256_pinned"]
        or register.get("source_original_xml_bytes")
            != spec["original_xml_bytes_pinned"]
        or register.get("source_ci_workflow_run_id") != 42091432185
        or register.get("source_notice_type") != "ContractAwardNotice"
        or register.get("buyer_xml_organization_id") != "ORG-0001"
        or register.get("buyer_source_name")
            != "WBM Wohnungsbaugesellschaft Berlin-Mitte mbH"
        or register.get("all_awards_share_technical_lot_id") != "LOT-0000"
        or register.get("verified_contract_result_tender_role_edges_count") != 3
        or register.get("verified_distinct_settled_contracts_count") != 3
        or register.get("verified_distinct_winning_party_organizations_count") != 3
    ):
        raise ValueError("TED_WBM_ORIGINAL_GRAPH_SOURCE_RECEIPT_MISMATCH")
    for key in (
        "source_is_official_original_xml_immutable_sha_and_length_replayed",
        "winner_links_proved_from_settled_contract_not_search_index",
        "search_index_winner_name_only_is_insufficient_to_verify_a_winner",
    ):
        if register.get(key) is not True:
            raise ValueError("TED_WBM_ORIGINAL_GRAPH_PROVENANCE_FLAG_CHANGED")
    for key in (
        "original_xml_bytes_committed_or_redistributed",
        "real_insured_building_identifiers_or_coordinates_observed",
        "per_company_coinsurance_percentage_observed",
        "premium_policy_limit_deductible_or_reinstatement_tiv_observed",
        "current_signed_policy_coverage_and_effective_dates_verified",
        "real_carrier_location_CAT_exposure_admitted",
    ):
        if register.get(key) is not False:
            raise ValueError("TED_WBM_ORIGINAL_GRAPH_MODEL_ADMISSION_FORBIDDEN")
    if (
        not isinstance(report, dict)
        or report.get("schema_version") != role.REPORT_SCOPE
        or report.get("notice") != role.NOTICE
        or report.get("official_xml_sha256")
            != register["source_original_xml_sha256"]
        or report.get("official_original_xml_url")
            != register["official_original_xml_url"]
        or report.get("exact_original_xml_sha256_and_bytes_pin_matched_this_execution") is not True
        or report.get("actual_award_buyer_original_organization_name")
            != register["buyer_source_name"]
        or report.get("winner_lot_result_count") != 3
        or report.get("settled_contracts_linked_to_winning_results") != 3
        or report.get("winning_result_contract_tender_links") != 3
        or report.get("won_tenders_selected_by_settled_contract_not_received_tender_list") is not True
        or report.get("source_winner_names_exactly_match_secondary_mirror_names") is not True
    ):
        raise ValueError("TED_WBM_OFFICIAL_ORIGINAL_LIVE_GRAPH_NOT_VERIFIED")
    for key in (
        "claimed_carrier_insured_buildings",
        "known_insurance_contract_coin_shares",
        "known_peril_sublimits_deductibles_or_tiv",
        "actual_carrier_by_location_CAT_exposures_admitted",
    ):
        if report.get(key) is not False:
            raise ValueError("TED_WBM_REAL_EXPOSURE_CLAIM_FORBIDDEN")
    expected = register.get("contract_awards")
    observed = report.get("award_role_paths")
    if (
        not isinstance(expected, list) or len(expected) != 3
        or not isinstance(observed, list) or len(observed) != 3
    ):
        raise ValueError("TED_WBM_GRAPH_EXPECTED_THREE_EXACT_CONTRACTS")
    expected_index = {}
    for record in expected:
        if not isinstance(record, dict) or any(not isinstance(record.get(k), str)
                                               for k in (*FIELDS, "winning_organization_id",
                                                         "winning_organization_source_name")):
            raise ValueError("TED_WBM_BAD_REGISTERED_CONTRACT")
        contract = record["settled_contract_id"]
        if contract in expected_index:
            raise ValueError("TED_WBM_DUPLICATE_REGISTERED_CONTRACT")
        expected_index[contract] = record
    actual_index = {}
    for record in observed:
        if not isinstance(record, dict):
            raise ValueError("TED_WBM_INVALID_ACTUAL_GRAPH_ROW")
        contract = record.get("settled_contract_id")
        if not isinstance(contract, str) or contract in actual_index:
            raise ValueError("TED_WBM_DUPLICATE_ACTUAL_CONTRACT")
        actual_index[contract] = record
        if record.get("this_group_documents_insured_object_allocations") is not False:
            raise ValueError("TED_WBM_MODEL_SCOPE_CHANGED")
        if record.get("this_group_documents_coinsurance_percentages") is not False:
            raise ValueError("TED_WBM_MODEL_SCOPE_CHANGED")
        if record.get("this_group_documents_reinsurance_or_net_retention") is not False:
            raise ValueError("TED_WBM_MODEL_SCOPE_CHANGED")
        if record.get("contract_signatories_are_automatically_winning_underwriters") is not False:
            raise ValueError("TED_WBM_SIGNATORY_IS_NOT_UNDERWRITER_PROOF")
    if set(expected_index) != set(actual_index):
        raise ValueError("TED_WBM_CONTRACT_SET_DRIFT")
    all_orgs = set()
    for contract_id, recorded in expected_index.items():
        observed_row = actual_index[contract_id]
        if any(observed_row.get(k) != recorded[k] for k in FIELDS):
            raise ValueError("TED_WBM_CONTRACT_TO_RESULT_TENDER_LOT_DRIFT")
        members = observed_row.get("winning_party_member_organizations")
        if not isinstance(members, list) or len(members) != 1:
            raise ValueError("TED_WBM_WINNING_PARTY_MEMBERSHIP_DRIFT")
        m = members[0]
        if (m.get("xml_organization_id") != recorded["winning_organization_id"]
                or m.get("source_company_name")
                    != recorded["winning_organization_source_name"]):
            raise ValueError("TED_WBM_WINNER_TO_CONTRACT_EDGE_DRIFT")
        all_orgs.add(m["xml_organization_id"])
    if len(all_orgs) != 3:
        raise ValueError("TED_WBM_DISTINCT_COMPANY_COUNT_DRIFT")
    return {
        "schema_version": SCHEMA,
        "original_ted_sha256_and_bytes_rechecked": True,
        "verified_settled_contract_to_tender_to_source_company_edges": 3,
        "technical_lot_id": "LOT-0000",
        "named_awardees_are_official_original_eforms_contract_linked": True,
        "company_insurance_participation_share_verified": False,
        "source_verified_insured_risk_locations_or_tiv": False,
        "admitted_to_CAT_model": False,
    }


def main() -> int:
    try:
        original = fetch_original_xml(role.NOTICE)
        result = validate(role.parse_award_roles(original))
        print(json.dumps(result, sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("TED_WBM_ORIGINAL_AWARD_GRAPH_RECEIPT_BLOCKED: " +
              str(exc)[:155], file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
