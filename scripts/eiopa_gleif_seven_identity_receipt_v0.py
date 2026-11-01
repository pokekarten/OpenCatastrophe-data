#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read-only EIOPA -> GLEIF LEI check; strictly identity evidence, never CAT exposure.

Only seven exact LEIs observed in CAT-Neon research are examined. The EIOPA
observations are *not* proof that original regulator CSV bytes were pinned.
Live GLEIF reads require --live; output contains no full provider responses.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from urllib.request import Request, urlopen

from scripts.gleif_level1_insurer_identity_pilot import valid_lei

API = "https://api.gleif.org/api/v1/lei-records/"
TERMS = "https://www.gleif.org/en/meta/lei-data-terms-of-use"
MAX_BYTES = 120000

# EIOPA research *observations* read from insurance-risk-core/main on 2026-11-01.
# No new legal entity or EIOPA original-byte assertion is created from this map.
EI0PA_LEI_CASES = {
    "259400VDTC20UW6M5D80": ("LV", '"Baltijas Apdrošināšanas Nams" apdrošināšanas akciju sabiedrība', "049"),
    "63670018BQ5R7IKA8T76": ("DK", '"danmark" Erhverv, Skadesforsikringsaktieselskab', "53118"),
    "213800AEQ6JQDLCWQN31": ("ES", "A.M.A., AGRUPACIÓN MUTUAL ASEGURADORA, MUTUA DE SEGUROS A PRIMA FIJA", "M0328"),
    "213800LXNGNQ5O1XBW47": ("MT", "AAK INSURANCE MALTA LIMITED", "C 51071"),
    "529900SURJXJXSY5O039": ("LT", "AB Lietuvos draudimas", "110051834"),
    "95980020140005024486": ("ES", "MUTUALITAT DELS ENGINYERS MUTUALITAT DE PREVISIO SOCIAL", "P3159"),
    "7437008CXP8UX8KITQ76": ("FI", "Ålands Ömsesidiga Försäkringsbolag", "01450820"),
}


class IdentityReceiptError(ValueError):
    """External identity data did not meet a fixed read-only check."""


def unique_pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise IdentityReceiptError("duplicate GLEIF JSON key")
        obj[key] = value
    return obj


def reject_constant(value):
    raise IdentityReceiptError("non-finite GLEIF JSON value")


def inspect_gleif_bytes(blob: bytes, lei: str) -> dict:
    if lei not in EI0PA_LEI_CASES or not valid_lei(lei):
        raise IdentityReceiptError("unexpected EIOPA LEI")
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_BYTES:
        raise IdentityReceiptError("GLEIF bytes empty, wrong type or too large")
    try:
        payload = json.loads(blob.decode("utf-8-sig"),
                             object_pairs_hook=unique_pairs,
                             parse_constant=reject_constant)
    except (UnicodeError, json.JSONDecodeError, TypeError) as exc:
        raise IdentityReceiptError("invalid original GLEIF JSON") from exc
    if type(payload) is not dict or type(payload.get("data")) is not dict:
        raise IdentityReceiptError("invalid GLEIF JSON:API envelope")
    data = payload["data"]
    attr = data.get("attributes")
    if data.get("id") != lei or data.get("type") != "lei-records" or type(attr) is not dict or attr.get("lei") != lei:
        raise IdentityReceiptError("GLEIF response LEI or record type mismatch")
    entity, reg = attr.get("entity"), attr.get("registration")
    if type(entity) is not dict or type(reg) is not dict:
        raise IdentityReceiptError("missing GLEIF legal entity fields")
    expected_country, expected_name, expected_local = EI0PA_LEI_CASES[lei]
    address = entity.get("legalAddress")
    legal_name = entity.get("legalName")
    if type(address) is not dict or type(legal_name) is not dict:
        raise IdentityReceiptError("missing legal address/name")
    if entity.get("jurisdiction") != expected_country or address.get("country") != expected_country:
        raise IdentityReceiptError("GLEIF jurisdiction does not match EIOPA observation")
    if entity.get("status") != "ACTIVE" or reg.get("status") != "ISSUED":
        raise IdentityReceiptError("inactive GLEIF legal entity or unissued LEI")
    name = legal_name.get("name")
    registered_as = entity.get("registeredAs")
    if type(name) is not str or not name.strip() or len(name) > 500:
        raise IdentityReceiptError("invalid GLEIF legal name")
    if registered_as is not None and (type(registered_as) is not str or len(registered_as) > 100):
        raise IdentityReceiptError("invalid GLEIF registeredAs")
    raw_trans = entity.get("transliteratedOtherNames") or []
    if type(raw_trans) is not list:
        raise IdentityReceiptError("invalid other-name structure")
    aliases = [o.get("name") for o in raw_trans if type(o) is dict and type(o.get("name")) is str]
    name_relation = (
        "exact" if name == expected_name
        else "gleif_ascii_transliteration_exact" if expected_name in aliases
        else "manual_legal_name_variant"
    )
    registration_relation = "exact" if registered_as == expected_local else "manual_local_register_id_review"
    return {
        "source": "GLEIF Level-1 individual LEI record",
        "lei": lei,
        "jurisdiction": expected_country,
        "gleif_legal_entity_status": "ACTIVE",
        "gleif_lei_registration_status": "ISSUED",
        "eiopa_to_gleif_name_relation": name_relation,
        "eiopa_to_gleif_local_registration_relation": registration_relation,
        "gleif_source_url": API + lei,
        "gleif_original_byte_sha256": hashlib.sha256(blob).hexdigest(),
        "gleif_source_terms": TERMS,
        "gleif_source_license": "CC0-1.0",
        "eiopa_original_csv_verified": False,
        "eiopa_registration_currently_verified": False,
        "neon_updated": False,
        "new_legal_entity_created": False,
        "insured_exposure_observed": False,
        "model_input_approved": False,
    }


def fetch_live(lei: str) -> bytes:
    if lei not in EI0PA_LEI_CASES:
        raise IdentityReceiptError("only pinned public EIOPA LEIs may be fetched")
    url = API + lei
    time.sleep(0.3)
    request = Request(url, headers={
        "Accept": "application/vnd.api+json",
        "User-Agent": "OpenCatastrophe-data-research/0.1 (+https://github.com/pokekarten/OpenCatastrophe-data)",
    })
    with urlopen(request, timeout=20) as response:
        if response.status != 200 or response.geturl() != url:
            raise IdentityReceiptError("unexpected GLEIF HTTP status or redirect")
        result = response.read(MAX_BYTES + 1)
    if len(result) > MAX_BYTES:
        raise IdentityReceiptError("oversized GLEIF response")
    return result


def audit(read_bytes) -> dict:
    receipts = []
    for lei in sorted(EI0PA_LEI_CASES):
        receipts.append(inspect_gleif_bytes(read_bytes(lei), lei))
    if len(receipts) != 7 or len({r["lei"] for r in receipts}) != 7:
        raise IdentityReceiptError("incomplete fixed GLEIF identity batch")
    return {
        "schema": "oc-eiopa-gleif-seven-identity-receipt-v0",
        "source_lei_count": 7,
        "status_active_issued_count": len(receipts),
        "name_exact_count": sum(r["eiopa_to_gleif_name_relation"] == "exact" for r in receipts),
        "name_transliteration_exact_count": sum(r["eiopa_to_gleif_name_relation"] == "gleif_ascii_transliteration_exact" for r in receipts),
        "name_manual_review_count": sum(r["eiopa_to_gleif_name_relation"] == "manual_legal_name_variant" for r in receipts),
        "local_register_exact_count": sum(r["eiopa_to_gleif_local_registration_relation"] == "exact" for r in receipts),
        "source_receipts": receipts,
        "neon_updated": False,
        "model_input_approved": False,
        "evidence_only": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="explicitly allow 7 bounded direct GLEIF HTTPS GETs")
    args = parser.parse_args()
    if not args.live:
        raise IdentityReceiptError("no network by default: pass --live explicitly")
    print(json.dumps(audit(fetch_live), sort_keys=True, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (IdentityReceiptError, OSError, ValueError) as exc:
        raise SystemExit(f"BLOCKED: {exc}") from exc
