# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-pinned eForms *award role* extraction, not portfolio allocation.

Read the official 668506-2026 WBM ContractAwardNotice from the already
allowlisted TED original XML fetch. Trace only the SDK-described link:
LotResult[selec-w] -> SettledContract[CON] -> LotTender[TEN] ->
TenderingParty[TPA] -> Tenderer[ORG] -> Organization/Company.
Crucial: LotResult/LotTender can enumerate *received* tenders, not just winners. Do NOT promote mere name occurrences to winners.
This reports award group membership, never nine per-carrier insured buildings,
policy limits, premiums, coinsurance shares, or CAT insured sums.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET

from .ted_berlin_insurance_original_xml_preflight_v0 import (
    SOURCES, fetch as fetch_ted_xml, inspect as inspect_original,
)

NOTICE = "668506-2026"
NS = {
    "ubl": "urn:oasis:names:specification:ubl:schema:xsd:ContractAwardNotice-2",
    "ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "efext": "http://data.europa.eu/p27/eforms-ubl-extensions/1",
    "efac": "http://data.europa.eu/p27/eforms-ubl-extension-aggregate-components/1",
}
RESULTS = (
    "./ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/"
    "efext:EformsExtension/efac:NoticeResult"
)
REPORT_SCOPE = "PUBLIC_TED_WBM_2026_CONTRACT_AWARD_WINNER_ROLE_ONLY_V0"
MIRROR_LABELS = (
    "HDI Global SE", "Helvetia Schweizerische Versicherungsgesellschaft AG",
    "R+V Allgemeine Versicherung AG",
)
MAX_XML_NODES = 40000
LIMIT_GROUPS = 60
ID = re.compile(r"(?:LOT|TEN|TPA|ORG|RES|CON)-[0-9A-Z]{4,24}\Z")


def error(reason: str) -> None:
    raise ValueError("TED_EFORMS_" + reason)


def required_id(elem: ET.Element | None, *, expected_prefix: str) -> str:
    if elem is None or elem.text is None or not ID.fullmatch(elem.text.strip()):
        error("MISSING_OR_INVALID_TECHNICAL_REFERENCE")
    value = elem.text.strip()
    if not value.startswith(expected_prefix + "-"):
        error("WRONG_TECHNICAL_REFERENCE_TYPE")
    return value


def _get_id(node: ET.Element, prefix: str) -> str:
    return required_id(node.find("cbc:ID", NS), expected_prefix=prefix)


def one(nodes: list[ET.Element], label: str) -> ET.Element:
    if len(nodes) != 1:
        error("EXPECTED_ONE_" + label)
    return nodes[0]


def index_nodes(
    parent: ET.Element, path: str, prefix: str, label: str,
) -> dict[str, ET.Element]:
    found = parent.findall(path, NS)
    if not 0 < len(found) <= LIMIT_GROUPS:
        error("UNEXPECTED_" + label + "_COUNT")
    result = {}
    for node in found:
        key = _get_id(node, prefix)
        if key in result:
            error("DUPLICATE_" + label + "_ID")
        result[key] = node
    return result


def _single_child_reference(node: ET.Element, path: str, prefix: str) -> str:
    refs = node.findall(path, NS)
    return _get_id(one(refs, prefix + "_REFERENCE"), prefix)


def parse_award_roles(original: bytes, *, notice: str = NOTICE) -> dict:
    if notice != NOTICE:
        error("AWARD_NOTICE_NOT_ALLOWLISTED")
    receipt = inspect_original(notice, original)
    if receipt["xml_document_root"] != "ContractAwardNotice":
        error("NOT_CONTRACT_AWARD_NOTICE")
    if not (receipt["original_sha256_immutable_pin_verified"]
            and receipt["original_byte_count_immutable_pin_verified"]):
        error("ORIGINAL_BYTES_NOT_RECHECKED_AGAINST_PIN")
    try:
        root = ET.fromstring(original)
    except ET.ParseError as exc:
        raise ValueError("TED_EFORMS_INVALID_XML") from exc
    if root.tag != "{" + NS["ubl"] + "}ContractAwardNotice":
        error("UNSUPPORTED_EFORMS_UBL_NAMESPACE")
    if sum(1 for _ in root.iter()) > MAX_XML_NODES:
        error("UNBOUNDED_XML_TREE")

    result = one(root.findall(RESULTS, NS), "NOTICE_RESULT")
    # Organization ids live at Company/PartyIdentification, not the
    # Organization wrapper. Never infer from cbc:ID on the wrapper.
    company_rows = root.findall(
        "./ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/"
        "efext:EformsExtension/efac:Organizations/efac:Organization/efac:Company", NS,
    )
    if not 1 <= len(company_rows) <= 120:
        error("UNEXPECTED_COMPANY_COUNT")
    companies: dict[str, str] = {}
    for company in company_rows:
        org_id = required_id(company.find("cac:PartyIdentification/cbc:ID", NS),
                             expected_prefix="ORG")
        names = company.findall("cac:PartyName/cbc:Name", NS)
        if len(names) != 1 or not (names[0].text or "").strip():
            error("ORGANIZATION_HAS_NO_SINGLE_NAME")
        name = names[0].text.strip()
        if org_id in companies or len(name) > 400:
            error("DUPLICATE_OR_INVALID_COMPANY")
        companies[org_id] = name

    buyer_refs = root.findall(
        "./cac:ContractingParty/cac:Party/cac:PartyIdentification/cbc:ID", NS
    )
    buyer_id = required_id(one(buyer_refs, "BUYER_REFERENCE"),
                           expected_prefix="ORG")
    buyer_name = companies.get(buyer_id)
    if not buyer_name or "WBM" not in buyer_name.upper():
        error("AWARD_BUYER_ROLE_NOT_WBM")

    tenders = index_nodes(result, "efac:LotTender", "TEN", "LOT_TENDER")
    parties = index_nodes(result, "efac:TenderingParty", "TPA", "TENDERING_PARTY")
    lot_results = index_nodes(result, "efac:LotResult", "RES", "LOT_RESULT")
    settled = index_nodes(result, "efac:SettledContract", "CON", "SETTLED_CONTRACT")
    winners = []
    used_contracts: set[str] = set()
    used_contract_tender_links: set[tuple[str, str, str]] = set()
    for result_id in sorted(lot_results):
        row = lot_results[result_id]
        status = row.findall("cbc:TenderResultCode", NS)
        if len(status) != 1 or not (status[0].text or "").strip():
            error("RESULT_WINNER_STATUS_MISSING")
        if status[0].text.strip() != "selec-w":
            continue

        lot_id = _single_child_reference(row, "efac:TenderLot", "LOT")
        received_tender_nodes = row.findall("efac:LotTender", NS)
        # Official SDK: these are the *received* tenders. Never interpret
        # them as winner-only, even if the LotResult says "selec-w".
        received_ids = [_get_id(ref, "TEN") for ref in received_tender_nodes]
        if len(received_ids) != len(set(received_ids)):
            error("DUPLICATE_RECEIVED_TENDER_REFERENCE")
        if any(ref not in tenders for ref in received_ids):
            error("RECEIVED_TENDER_ID_NOT_FOUND")
        for ref in received_ids:
            if _single_child_reference(tenders[ref], "efac:TenderLot", "LOT") != lot_id:
                error("RECEIVED_TENDER_WRONG_LOT")

        # The actual winning tender(s) are identified by each settled
        # contract's tender links, and by a contract reference from this
        # selected result. This is a graph join, NOT a name match.
        con_nodes = row.findall("efac:SettledContract", NS)
        if not con_nodes:
            error("SELECTED_RESULT_WITHOUT_SETTLED_CONTRACT")
        contract_ids = [_get_id(ref, "CON") for ref in con_nodes]
        if len(contract_ids) != len(set(contract_ids)):
            error("DUPLICATE_CONTRACT_REFERENCE_IN_RESULT")
        for con_id in sorted(contract_ids):
            contract = settled.get(con_id)
            if contract is None:
                error("SETTLED_CONTRACT_NOT_FOUND")
            used_contracts.add(con_id)

            referenced_tenders = contract.findall("efac:LotTender", NS)
            if not referenced_tenders:
                error("SETTLED_CONTRACT_WITHOUT_TENDER_REFERENCES")
            contract_tender_ids = [_get_id(ref, "TEN") for ref in referenced_tenders]
            if len(contract_tender_ids) != len(set(contract_tender_ids)):
                error("DUPLICATE_CONTRACT_TENDER_REFERENCE")

            signatory_elems = contract.findall(
                "cac:SignatoryParty/cac:PartyIdentification/cbc:ID", NS
            )
            signatory_ids = [
                required_id(n, expected_prefix="ORG") for n in signatory_elems
            ]
            if len(signatory_ids) != len(set(signatory_ids)):
                error("DUPLICATE_CONTRACT_SIGNATORY")
            if any(n not in companies for n in signatory_ids):
                error("CONTRACT_SIGNATORY_NOT_REGISTERED")
            signatories = [
                {"xml_organization_id": org, "source_company_name": companies[org]}
                for org in sorted(signatory_ids)
            ]
            applicable_tenders = 0
            for ten_id in sorted(contract_tender_ids):
                tender = tenders.get(ten_id)
                if tender is None:
                    error("CONTRACT_TENDER_NOT_FOUND")
                linked_lot = _single_child_reference(tender, "efac:TenderLot", "LOT")
                if linked_lot != lot_id:
                    # A single contract can involve multiple lots. Only the
                    # current winning LotResult's own lot is admitted.
                    continue
                applicable_tenders += 1
                if received_ids and ten_id not in received_ids:
                    error("SETTLED_WINNER_NOT_AMONG_RECEIVED_TENDERS")
                edge_id = (result_id, con_id, ten_id)
                if edge_id in used_contract_tender_links:
                    error("DUPLICATE_RESULT_CONTRACT_TENDER_EDGE")
                used_contract_tender_links.add(edge_id)

                party_id = _single_child_reference(
                    tender, "efac:TenderingParty", "TPA"
                )
                party = parties.get(party_id)
                if party is None:
                    error("WINNING_TENDERING_PARTY_NOT_FOUND")
                ref_nodes = party.findall("efac:Tenderer/cbc:ID", NS)
                if not ref_nodes:
                    error("WINNING_TENDERING_PARTY_WITHOUT_ORGANIZATIONS")
                member_ids = [
                    required_id(n, expected_prefix="ORG") for n in ref_nodes
                ]
                if len(member_ids) != len(set(member_ids)) or buyer_id in member_ids:
                    error("DUPLICATE_OR_BUYER_IN_WINNER_GROUP")
                if any(n not in companies for n in member_ids):
                    error("WINNER_ORGANIZATION_ID_NOT_FOUND")
                winners.append({
                    "lot_result_id": result_id,
                    "lot_id": lot_id,
                    "settled_contract_id": con_id,
                    "winning_tender_id": ten_id,
                    "winning_party_id": party_id,
                    "winning_party_member_organizations": [
                        {"xml_organization_id": n, "source_company_name": companies[n]}
                        for n in sorted(member_ids)
                    ],
                    "contract_signatories_separate_from_winning_tenderers": signatories,
                    "contract_signatories_are_automatically_winning_underwriters": False,
                    "this_group_documents_insured_object_allocations": False,
                    "this_group_documents_coinsurance_percentages": False,
                    "this_group_documents_reinsurance_or_net_retention": False,
                })
            if applicable_tenders == 0:
                error("CONTRACT_HAS_NO_TENDER_FOR_SELECTED_LOT")

    if not winners:
        error("NO_EXPLICIT_WINNER_RESULT")
    winner_ids = [(x["lot_result_id"], x["settled_contract_id"], x["winning_tender_id"]) for x in winners]
    if len(set(winner_ids)) != len(winner_ids):
        error("DUPLICATE_RESULT_CONTRACT_TENDER_EDGE")
    observed_names = sorted({
        m["source_company_name"] for win in winners
        for m in win["winning_party_member_organizations"]
    })
    return {
        "schema_version": REPORT_SCOPE,
        "notice": NOTICE,
        "official_xml_sha256": receipt["original_source_sha256"],
        "exact_original_xml_sha256_and_bytes_pin_matched_this_execution": True,
        "official_original_xml_url": receipt["official_original_xml_url"],
        "actual_award_buyer_original_organization_name": buyer_name,
        "winner_lot_result_count": len({x["lot_result_id"] for x in winners}),
        "winning_result_contract_tender_links": len(winners),
        "settled_contracts_linked_to_winning_results": len(used_contracts),
        "won_tenders_selected_by_settled_contract_not_received_tender_list": True,
        "source_organization_names_in_winning_tendering_parties": observed_names,
        "source_winner_names_exactly_match_secondary_mirror_names": (
            observed_names == sorted(MIRROR_LABELS)
        ),
        "award_role_paths": winners,
        "claimed_carrier_insured_buildings": False,
        "known_insurance_contract_coin_shares": False,
        "known_peril_sublimits_deductibles_or_tiv": False,
        "actual_carrier_by_location_CAT_exposures_admitted": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notice", default=NOTICE, choices=[NOTICE])
    args = parser.parse_args(argv)
    try:
        print(json.dumps(parse_award_roles(fetch_ted_xml(args.notice)),
                         ensure_ascii=False, sort_keys=True))
    except (OSError, ValueError) as exc:
        print("TED_WBM_WINNER_ROLE_RESEARCH_BLOCKED: " + str(exc)[:130],
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
