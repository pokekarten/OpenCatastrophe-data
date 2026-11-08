# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Parse exact TED eForms *contract identifier text* (BT-150), not policy shares.

Evidence chain: official HTTP 200 original XML pinned by SHA + bytes; proven
RES -> CON -> TEN -> TPA -> ORG graph; then exactly one published contract
identifier BT-150 per linked CON. A "%" in that text is only an attributed
percentage *label*, not a validated co-insurance schedule or CAT allocation.
"""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET

from . import ted_wbm_eforms_winner_role_v0 as award
from . import ted_wbm_original_award_graph_receipt_v0 as register
from .ted_berlin_insurance_original_xml_preflight_v0 import fetch

CON = re.compile(r"CON-[0-9A-Z]{4,24}\Z")
NUMBER = re.compile(r"(?<![0-9])([0-9]{1,3})\s*%")
MAX_TEXT = 180
EXPECTED_CONTRACTS = ("CON-0001", "CON-0002", "CON-0003")


def _text(el: ET.Element | None, *, required: bool) -> str | None:
    if el is None:
        if required:
            raise ValueError("TED_CONTRACT_IDENTIFIER_MISSING")
        return None
    if len(el) or el.text is None:
        raise ValueError("TED_CONTRACT_IDENTIFIER_NOT_SIMPLE_TEXT")
    value = el.text.strip()
    if (not value or len(value) > MAX_TEXT or any(ord(c) < 32 for c in value)):
        raise ValueError("TED_CONTRACT_IDENTIFIER_INVALID_TEXT")
    return value


def extract_contract_identifiers(
    original: bytes, *,
    expected_tender_contracts: dict[str, str],
) -> dict[str, dict]:
    """Parse only SDK-defined SettledContract/ContractReference/cbc:ID (BT-150).

    This lower-level parser does not authenticate source bytes: callers must
    validate original XML provenance and contract-company graph separately.
    """
    if type(original) is not bytes or not 100 <= len(original) <= 2_000_000:
        raise ValueError("TED_CONTRACT_IDENTIFIER_INVALID_SOURCE_SIZE")
    if re.search(rb"<!\s*(?:DOCTYPE|ENTITY)\b", original, flags=re.I):
        raise ValueError("TED_CONTRACT_IDENTIFIER_DTD_FORBIDDEN")
    try:
        root = ET.fromstring(original)
    except ET.ParseError as exc:
        raise ValueError("TED_CONTRACT_IDENTIFIER_INVALID_XML") from exc
    if root.tag != "{" + award.NS["ubl"] + "}ContractAwardNotice":
        raise ValueError("TED_CONTRACT_IDENTIFIER_WRONG_NOTICE_ROOT")
    if sum(1 for _ in root.iter()) > award.MAX_XML_NODES:
        raise ValueError("TED_CONTRACT_IDENTIFIER_OVERSIZE_XML_TREE")
    results = root.findall(award.RESULTS, award.NS)
    if len(results) != 1:
        raise ValueError("TED_CONTRACT_IDENTIFIER_NOTICE_RESULT_NOT_UNIQUE")
    contract_nodes = results[0].findall("efac:SettledContract", award.NS)
    if len(contract_nodes) != 3 or set(expected_tender_contracts) != set(EXPECTED_CONTRACTS):
        raise ValueError("TED_CONTRACT_IDENTIFIER_EXPECTED_THREE_CONTRACTS")
    output: dict[str,dict] = {}
    business_identifiers: set[str] = set()
    for item in contract_nodes:
        cid = _text(item.find("cbc:ID", award.NS), required=True)
        if not CON.fullmatch(cid or "") or cid in output:
            raise ValueError("TED_CONTRACT_IDENTIFIER_BAD_OR_DUPLICATE_CON_ID")
        contract_ref = item.findall("efac:ContractReference/cbc:ID", award.NS)
        if len(contract_ref) != 1:
            raise ValueError("TED_CONTRACT_IDENTIFIER_MISSING_OR_REPEAT_BUSINESS_ID")
        business = _text(contract_ref[0], required=True)
        if business in business_identifiers:
            raise ValueError("TED_CONTRACT_IDENTIFIER_DUPLICATE_BUSINESS_ID")
        business_identifiers.add(business)
        tender_nodes = item.findall("efac:LotTender/cbc:ID", award.NS)
        tenders = [(_text(x, required=True)) for x in tender_nodes]
        if not tenders or len(set(tenders)) != len(tenders):
            raise ValueError("TED_CONTRACT_IDENTIFIER_INVALID_TENDER_REFS")
        expected_tender = expected_tender_contracts.get(cid)
        if expected_tender not in tenders:
            raise ValueError("TED_CONTRACT_IDENTIFIER_GRAPH_TENDER_MISMATCH")
        title_nodes = item.findall("cbc:Title", award.NS)
        if len(title_nodes) > 1:
            raise ValueError("TED_CONTRACT_IDENTIFIER_DUPLICATE_CONTRACT_TITLE")
        title = _text(title_nodes[0], required=False) if title_nodes else None
        percent_tokens = NUMBER.findall(business)
        # Reject more than one numerical percent. The source is the label,
        # not a proof of final insurance participation.
        if len(percent_tokens) > 1:
            raise ValueError("TED_CONTRACT_IDENTIFIER_MULTIPLE_PERCENT_LABELS")
        percent_label = int(percent_tokens[0]) if percent_tokens else None
        if percent_label is not None and not 0 < percent_label <= 100:
            raise ValueError("TED_CONTRACT_IDENTIFIER_PERCENT_LABEL_OUT_OF_RANGE")
        output[cid] = {
            "contract_technical_id": cid,
            "contract_tender_id": expected_tender,
            "original_business_identifier_BT_150": business,
            "original_contract_title_BT_721_optional": title,
            "percentage_string_in_business_identifier": percent_label,
            "percentage_is_contract_identifier_label_only": True,
            "actual_insurer_policy_share_proved": False,
            "insured_buildings_policy_schedule_or_tiv_proved": False,
        }
    if set(output) != set(EXPECTED_CONTRACTS):
        raise ValueError("TED_CONTRACT_IDENTIFIER_CONTRACT_IDS_DRIFT")
    return output


def verify_original(original: bytes) -> dict:
    # This parses and validates the original SHA/size, buyer, semantic markers,
    # resolved insurer/company contract graph and immutable saved receipt.
    graph = award.parse_award_roles(original)
    receipt = register.validate(graph)
    expected = {
        row["settled_contract_id"]: row["winning_tender_id"]
        for row in graph["award_role_paths"]
    }
    labels = extract_contract_identifiers(
        original, expected_tender_contracts=expected
    )
    members = {
        row["settled_contract_id"]: row["winning_party_member_organizations"][0]
        for row in graph["award_role_paths"]
    }
    rows = []
    for cid in EXPECTED_CONTRACTS:
        row = labels[cid].copy()
        row["winning_organization_id"] = members[cid]["xml_organization_id"]
        row["winning_organization_name"] = members[cid]["source_company_name"]
        rows.append(row)
    percents = [r["percentage_string_in_business_identifier"] for r in rows]
    return {
        "schema_version": "TED_WBM_ORIGINAL_AWARD_CONTRACT_IDENTIFIER_LABELS_V0",
        "notice": award.NOTICE,
        "source_original_XML_sha256": graph["official_xml_sha256"],
        "verified_source_receipt_contract_edges": receipt[
            "verified_settled_contract_to_tender_to_source_company_edges"
        ],
        "lot_id": receipt["technical_lot_id"],
        "contract_identifier_labels": rows,
        "all_three_contract_identifier_labels_contain_one_percentage": all(
            v is not None for v in percents),
        "sum_of_percentage_labels_when_all_present": (
            sum(percents) if all(v is not None for v in percents) else None
        ),
        "percentage_labels_establish_actual_insurance_shares": False,
        "contract_terms_confirmed_from_full_signed_policy": False,
        "source_verified_individual_insured_properties": False,
        "source_verified_tiv_premium_limits_or_deductibles": False,
        "confirmed_company_specific_CAT_exposure_admitted": False,
        "original_xml_bytes_retained_or_logged": False,
    }


def main() -> int:
    try:
        print(json.dumps(verify_original(fetch(award.NOTICE)),
                         ensure_ascii=False, sort_keys=True))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print("TED_WBM_CONTRACT_SHARE_LABEL_PREFLIGHT_BLOCKED: " +
              str(exc)[:155], file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
