# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-pinned official TED WBM 2026 competition/award procedure lineage.

BT-04 (root cbc:ContractFolderID) identifies *procurement procedure*, whereas
BT-701 (root cbc:ID) identifies *notice*. Similar titles / internal buyer IDs
and contract company matches are NEVER enough to assert same procedure.
OPP-090 previous-publication refs are recorded independently from BT-04.
No insurer building allocation, policy share or CAT exposure is admitted.
"""
from __future__ import annotations

import json
import re
import sys
import uuid
import xml.etree.ElementTree as ET

from . import ted_wbm_2026_competition_original_preflight_v0 as competition
from . import ted_wbm_eforms_winner_role_v0 as award
from . import ted_berlin_insurance_original_xml_preflight_v0 as original
from . import ted_wbm_original_award_graph_receipt_v0 as award_receipt

CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
CAC = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
NS = {"cbc": CBC, "cac": CAC}
MAX_NODES = 40000
MAX_REF_COUNT = 40
COMPETITION_NOTICE = "286307-2026"
AWARD_NOTICE = "668506-2026"
PUBLICATION_NUMBER = re.compile(r"[0-9]{1,8}-20[0-9]{2}\Z")


def _one_text(root: ET.Element, path: str, *, required: bool, label: str) -> str | None:
    elems = root.findall(path, NS)
    if len(elems) > 1 or (required and len(elems) != 1):
        raise ValueError("TED_WBM_LINEAGE_INVALID_" + label + "_CARDINALITY")
    if not elems:
        return None
    node = elems[0]
    value = (node.text or "").strip()
    if len(node) or not value or len(value) > 200 or any(ord(c) < 32 for c in value):
        raise ValueError("TED_WBM_LINEAGE_BAD_" + label)
    return value


def _uuid4(value: str, label: str) -> str:
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise ValueError("TED_WBM_LINEAGE_" + label + "_NOT_UUID") from exc
    if parsed.version != 4 or str(parsed) != value.lower():
        raise ValueError("TED_WBM_LINEAGE_" + label + "_NOT_UUID4")
    return str(parsed)


def extract_metadata(data: bytes, *, role: str) -> dict:
    """Structure-only extraction; NOT source authenticated. Use verify() for proof."""
    if role not in ("competition", "award"):
        raise ValueError("TED_WBM_LINEAGE_ROLE_NOT_ALLOWLISTED")
    if type(data) is not bytes or not 100 <= len(data) <= 2_000_000:
        raise ValueError("TED_WBM_LINEAGE_BAD_SOURCE_SIZE")
    if re.search(rb"<!\s*(?:DOCTYPE|ENTITY)\b", data, flags=re.I):
        raise ValueError("TED_WBM_LINEAGE_XML_DTD_FORBIDDEN")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError("TED_WBM_LINEAGE_INVALID_XML") from exc
    expected = (
        "{urn:oasis:names:specification:ubl:schema:xsd:ContractNotice-2}ContractNotice"
        if role == "competition" else
        "{urn:oasis:names:specification:ubl:schema:xsd:ContractAwardNotice-2}ContractAwardNotice"
    )
    if root.tag != expected:
        raise ValueError("TED_WBM_LINEAGE_WRONG_UBL_NOTICE_ROOT")
    if sum(1 for _ in root.iter()) > MAX_NODES:
        raise ValueError("TED_WBM_LINEAGE_TOO_MANY_XML_NODES")

    # SDK BT-04 versus BT-701. BT-04 is a procedure UUID, NOT a notice UUID.
    procedure_id = _uuid4(
        _one_text(root, "cbc:ContractFolderID", required=True, label="PROCEDURE") or "",
        "PROCEDURE",
    )
    ids = root.findall("cbc:ID", NS)
    if len(ids) != 1 or ids[0].attrib.get("schemeName") != "notice-id":
        raise ValueError("TED_WBM_LINEAGE_MISSING_EXACT_NOTICE_ID_SCHEME")
    notice_id = _uuid4(
        _one_text(root, "cbc:ID", required=True, label="NOTICE") or "",
        "NOTICE",
    )
    internal = root.findall("cac:ProcurementProject/cbc:ID", NS)
    if len(internal) > 1:
        raise ValueError("TED_WBM_LINEAGE_MULTIPLE_INTERNAL_IDS")
    internal_id = None
    if internal:
        if internal[0].attrib.get("schemeName") != "InternalID":
            raise ValueError("TED_WBM_LINEAGE_NON_INTERNAL_PROCEDURE_ID")
        internal_id = _one_text(
            root, "cac:ProcurementProject/cbc:ID", required=True, label="INTERNAL"
        )

    previous_refs: list[str] = []
    for ref in root.findall("cac:NoticeDocumentReference/cbc:ID", NS):
        if ref.attrib.get("schemeName") != "ojs-notice-id":
            # Other typed references may exist. Never reinterpret a UUID or
            # unknown scheme as an OJ S publication reference.
            continue
        val = (ref.text or "").strip()
        if not PUBLICATION_NUMBER.fullmatch(val):
            raise ValueError("TED_WBM_LINEAGE_INVALID_PREVIOUS_OJS_NUMBER")
        previous_refs.append(val)
    if len(previous_refs) > MAX_REF_COUNT or len(set(previous_refs)) != len(previous_refs):
        raise ValueError("TED_WBM_LINEAGE_DUPLICATE_OR_TOO_MANY_PREVIOUS_REFS")

    return {
        "role": role,
        "root_notice_id_BT701": notice_id,
        "root_procedure_id_BT04": procedure_id,
        "buyer_defined_internal_procedure_id_BT22": internal_id,
        "previous_published_notice_ids_OPP090": sorted(previous_refs),
        "metadata_extraction_alone_authenticates_official_source": False,
    }


def compare(early: dict, late: dict) -> dict:
    if early.get("role") != "competition" or late.get("role") != "award":
        raise ValueError("TED_WBM_LINEAGE_WRONG_ROLE_PAIR")
    for item in (early, late):
        if item.get("metadata_extraction_alone_authenticates_official_source") is not False:
            raise ValueError("TED_WBM_LINEAGE_SOURCE_AUTHENTICITY_CLAIM_FORBIDDEN")
        for key in ("root_notice_id_BT701", "root_procedure_id_BT04"):
            _uuid4(item.get(key, ""), key)
    if early["root_notice_id_BT701"] == late["root_notice_id_BT701"]:
        raise ValueError("TED_WBM_LINEAGE_SAME_BT701_NOTICE_IN_TWO_DISTINCT_PUBLICATIONS")
    same_procedure = (
        early["root_procedure_id_BT04"] == late["root_procedure_id_BT04"]
    )
    earlier_pub_ref = COMPETITION_NOTICE in late["previous_published_notice_ids_OPP090"]
    internal_id_equal = bool(
        early.get("buyer_defined_internal_procedure_id_BT22")
        and early.get("buyer_defined_internal_procedure_id_BT22")
            == late.get("buyer_defined_internal_procedure_id_BT22")
    )
    if same_procedure:
        classification = "SAME_PROCEDURE_CONFIRMED_BY_BT04"
    elif earlier_pub_ref:
        classification = "DIFFERENT_BT04_BUT_EXPLICIT_EARLIER_PUBLICATION_REFERENCE_REVIEW"
    else:
        classification = "DIFFERENT_BT04_NO_DIRECT_SAME_PROCEDURE_PROOF"
    return {
        "schema_version": "TED_WBM_2026_ORIGINAL_BT04_NOTICE_LINEAGE_V0",
        "competition_publication_number": COMPETITION_NOTICE,
        "award_publication_number": AWARD_NOTICE,
        "competition_notice_uuid_BT701": early["root_notice_id_BT701"],
        "award_notice_uuid_BT701": late["root_notice_id_BT701"],
        "competition_procedure_uuid_BT04": early["root_procedure_id_BT04"],
        "award_procedure_uuid_BT04": late["root_procedure_id_BT04"],
        "procedure_ids_identical": same_procedure,
        "buyer_internal_procedure_ids_identical": internal_id_equal,
        "award_explicitly_references_competition_publication": earlier_pub_ref,
        "competition_previous_published_references": early["previous_published_notice_ids_OPP090"],
        "award_previous_published_references": late["previous_published_notice_ids_OPP090"],
        "classification": classification,
        "same_title_or_internal_id_alone_establishes_same_procedure": False,
        "different_procedure_uuid_silently_treated_as_same": False,
        "insured_buildings_or_current_coinsurance_shares_proved": False,
        "company_specific_CAT_exposure_admitted": False,
    }


def verify(*, competition_raw: bytes, award_raw: bytes) -> dict:
    # Source authentication remains enforced by independent reviewers.
    c = competition.inspect(competition_raw)
    a = original.inspect(AWARD_NOTICE, award_raw)
    if not (
        c["original_xml_retrieval_independently_rechecked_against_reviewed_sha"]
        and a["original_sha256_immutable_pin_verified"]
        and a["original_byte_count_immutable_pin_verified"]
    ):
        raise ValueError("TED_WBM_LINEAGE_ORIGINAL_SOURCE_NOT_PINNED")
    result = award.parse_award_roles(award_raw)
    award_receipt.validate(result)
    report = compare(
        extract_metadata(competition_raw, role="competition"),
        extract_metadata(award_raw, role="award"),
    )
    report["competition_original_xml_sha256"] = c["original_source_sha256"]
    report["competition_original_xml_byte_count"] = c["original_source_bytes"]
    report["award_original_xml_sha256"] = a["original_source_sha256"]
    report["award_original_xml_byte_count"] = a["original_source_bytes"]
    report["exact_pinned_original_sources_replayed_this_execution"] = True
    report["actual_award_company_contract_graph_verified_this_execution"] = True
    report["raw_original_xml_committed_or_printed"] = False
    return report


def main() -> int:
    try:
        early = competition.fetch()
        late = original.fetch(AWARD_NOTICE)
        print(json.dumps(
            verify(competition_raw=early, award_raw=late),
            ensure_ascii=False, sort_keys=True,
        ))
    except (ValueError, OSError, TypeError, KeyError) as exc:
        print("TED_WBM_BT04_LINEAGE_SOURCE_BLOCKED: " + str(exc)[:155],
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
