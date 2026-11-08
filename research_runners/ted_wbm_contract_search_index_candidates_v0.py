# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Research-only TED Search index candidate labels for one WBM award notice.

Official Search API fields are a *flattened notice-level index*: winner-name
is linked by the EU field catalogue through received tender references in a
selected LotResult, not necessarily through SettledContract / BT-3202 tender
references. Do not equate index winner labels or contract-tender IDs with a
verified pair, coinsurance carrier, risk site, insurance premium or model TIV.
"""
from __future__ import annotations

import json
import re
import sys

from . import ted_berlin_insurance_search_api_preflight_v0 as api

NOTICE = "668506-2026"
MAX_VALUES_PER_FIELD = 24
MAX_FIELD_CHARS = 300
TECH_TENDER_ID = re.compile(r"TEN-[0-9A-Z]{4,24}\Z")
EXPECTED_RESEARCH_LABELS = frozenset((
    "HDI Global SE",
    "Helvetia Schweizerische Versicherungsgesellschaft AG",
    "R+V Allgemeine Versicherung AG",
))
FIELDS = (
    "winner-name", "winner-identifier", "winner-selection-status",
    "contract-identifier", "contract-tender-id", "contract-conclusion-date",
    "winner-decision-date",
)


def _leaves(value, *, depth=0):
    if depth > 4:
        raise ValueError("TED_AWARD_INDEX_EXCESSIVE_NESTING")
    if value is None:
        return []
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return []
        if len(v) > MAX_FIELD_CHARS or any(ord(c) < 32 for c in v):
            raise ValueError("TED_AWARD_INDEX_INVALID_TEXT_VALUE")
        return [v]
    if isinstance(value, list):
        if len(value) > MAX_VALUES_PER_FIELD:
            raise ValueError("TED_AWARD_INDEX_UNBOUNDED_FIELD_ARRAY")
        return [x for part in value for x in _leaves(part, depth=depth + 1)]
    if isinstance(value, dict):
        if len(value) > MAX_VALUES_PER_FIELD:
            raise ValueError("TED_AWARD_INDEX_UNBOUNDED_LANGUAGE_MAP")
        return [x for part in value.values()
                for x in _leaves(part, depth=depth + 1)]
    raise ValueError("TED_AWARD_INDEX_WRONG_FIELD_TYPE")


def _candidate_strings(row: dict, field: str) -> list[str]:
    if field not in FIELDS:
        raise ValueError("TED_AWARD_INDEX_UNAPPROVED_FIELD")
    found = sorted(set(_leaves(row.get(field))))
    if len(found) > MAX_VALUES_PER_FIELD:
        raise ValueError("TED_AWARD_INDEX_EXCESSIVE_UNIQUE_VALUES")
    return found


def inspect_wbm(raw: bytes) -> dict:
    # This preflight validates one official publisher response: exact notice,
    # WBM buyer, insurance subject, bounded bytes and strict JSON semantics.
    primary = api.parse(NOTICE, raw)
    try:
        body = json.loads(
            raw.decode("utf-8"), object_pairs_hook=api._no_duplicate_json,
            parse_constant=lambda x: (_ for _ in ()).throw(
                ValueError("TED_API_NONFINITE")),
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("TED_AWARD_INDEX_INVALID_JSON") from exc
    row = body["notices"][0]

    labels = _candidate_strings(row, "winner-name")
    status = _candidate_strings(row, "winner-selection-status")
    contract_identifiers = _candidate_strings(row, "contract-identifier")
    tender_refs = _candidate_strings(row, "contract-tender-id")
    winner_identifiers = _candidate_strings(row, "winner-identifier")
    conclusion_dates = _candidate_strings(row, "contract-conclusion-date")
    decision_dates = _candidate_strings(row, "winner-decision-date")
    if any(not TECH_TENDER_ID.fullmatch(x) for x in tender_refs):
        raise ValueError("TED_AWARD_INDEX_UNEXPECTED_CONTRACT_TENDER_ID_SHAPE")
    if any(x not in {"selec-w", "clos-nw", "open-nw"} for x in status):
        raise ValueError("TED_AWARD_INDEX_UNEXPECTED_LOT_STATUS")

    return {
        "schema_version": "WBM_TED_SEARCH_INDEX_CONTRACT_LABEL_CANDIDATES_V0",
        "publication_number": NOTICE,
        "official_metadata_json_sha256": primary["structured_publisher_data_sha256"],
        "official_metadata_json_bytes": primary["structured_publisher_data_bytes"],
        "primary_publisher_notice_buyer_title_verified": True,
        "extracted_field_names_exactly_from_eu_search_field_catalogue": True,
        "indexed_winner_candidate_labels": labels,
        "indexed_winner_labels_present": bool(labels),
        "indexed_winner_labels_exactly_match_known_secondary_labels": (
            bool(labels) and set(labels) == EXPECTED_RESEARCH_LABELS
        ),
        # The Search API flattens multilingual, multiple-lot arrays.
        # Do not pair each company label to any particular contract/tender ID.
        "indexed_contract_tender_references_unpaired": tender_refs,
        "indexed_contract_identifier_count": len(contract_identifiers),
        "indexed_winner_identifier_count": len(winner_identifiers),
        "indexed_lot_winner_status_codes_unpaired": status,
        "indexed_contract_conclusion_dates_unpaired": conclusion_dates,
        "indexed_winner_decision_dates_unpaired": decision_dates,
        "source_api_winner_label_may_contain_nonwinning_received_bidders": True,
        "source_api_index_fields_prove_contract_to_company_join": False,
        "original_ubl_eforms_settled_contract_edges_verified": False,
        "individual_insurer_policy_or_coverage_share_verified": False,
        "individual_insured_building_location_tiv_or_perils_verified": False,
        "admitted_to_company_specific_CAT_model_exposure": False,
        "source_api_response_raw_body_logged_or_committed": False,
    }


def main() -> int:
    try:
        raw = api.fetch(NOTICE, fields=api.WBM_AWARD_CANDIDATE_FIELDS)
        print(json.dumps(inspect_wbm(raw), ensure_ascii=False, sort_keys=True))
    except (OSError, ValueError, KeyError) as exc:
        print("TED_WBM_SEARCH_CANDIDATES_BLOCKED: " +
              str(exc)[:160], file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
