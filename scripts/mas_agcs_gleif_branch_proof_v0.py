#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded GLEIF proof for ONE SG branch LEI and its DISTINCT DE parent.

Offline by default; --live fetches three precise GLEIF URLs. Retains only
source-body hashes and identities, never source JSON/Neon writes/CAT approvals.
Registration and relationship statuses are independent and must NOT be
interpreted as current branch licence authorisation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from urllib.request import Request, urlopen

BRANCH = "984500D1360HXAUAEF86"
PARENT = "F240A7PWJB2BLKELB442"
UEN = "T11FC0131K"
BASE = "https://api.gleif.org/api/v1/lei-records/"
URLS = {
    "branch": BASE + BRANCH,
    "parent": BASE + PARENT,
    "relationship": BASE + BRANCH + "/head-office-relationship",
}
MAX_BYTES = 100000


class GLEIFBranchReceiptError(ValueError):
    """Original GLEIF source record, scope or status diverged."""


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise GLEIFBranchReceiptError("duplicate JSON key")
        result[key] = value
    return result


def reject_nonfinite(value):
    raise GLEIFBranchReceiptError("non-finite JSON value")


def parse_original(blob: bytes, kind: str) -> dict:
    if kind not in URLS:
        raise GLEIFBranchReceiptError("unreviewed response role")
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_BYTES:
        raise GLEIFBranchReceiptError("source bytes unavailable or over limit")
    try:
        result = json.loads(blob.decode("utf-8-sig"), object_pairs_hook=no_duplicate_keys,
                            parse_constant=reject_nonfinite)
    except (UnicodeError, TypeError, json.JSONDecodeError) as exc:
        raise GLEIFBranchReceiptError("invalid GLEIF JSON body") from exc
    if type(result) is not dict or type(result.get("data")) is not dict:
        raise GLEIFBranchReceiptError("missing single GLEIF JSON:API record")
    record = result["data"]
    expected_type = "relationship-records" if kind == "relationship" else "lei-records"
    if record.get("type") != expected_type or type(record.get("attributes")) is not dict:
        raise GLEIFBranchReceiptError("wrong GLEIF record type")
    if kind in ("branch", "parent"):
        if record.get("id") != (BRANCH if kind == "branch" else PARENT):
            raise GLEIFBranchReceiptError("wrong GLEIF LEI")
    return record


def original_audit(source_bytes: dict[str, bytes]) -> dict:
    if set(source_bytes) != set(URLS):
        raise GLEIFBranchReceiptError("requires exactly three original GLEIF records")
    b = parse_original(source_bytes["branch"], "branch")["attributes"]
    p = parse_original(source_bytes["parent"], "parent")["attributes"]
    r = parse_original(source_bytes["relationship"], "relationship")["attributes"]
    b_entity, p_entity = b.get("entity"), p.get("entity")
    b_reg, p_reg = b.get("registration"), p.get("registration")
    link, link_reg = r.get("relationship"), r.get("registration")
    if not all(type(x) is dict for x in
               (b_entity, p_entity, b_reg, p_reg, link, link_reg)):
        raise GLEIFBranchReceiptError("missing GLEIF entity/registration/relationship fields")
    if (b_entity.get("category") != "BRANCH"
            or b_entity.get("legalName", {}).get("name") !=
            "ALLIANZ GLOBAL CORPORATE & SPECIALTY SE SINGAPORE BRANCH"
            or b_entity.get("jurisdiction") != "DE"
            or b_entity.get("legalAddress", {}).get("country") != "SG"
            or b_entity.get("registeredAs") != UEN
            or b_entity.get("registeredAt", {}).get("id") != "RA000523"
            or b_entity.get("status") != "ACTIVE"):
        raise GLEIFBranchReceiptError("branch original identifier/scope changed")
    if (p_entity.get("category") != "GENERAL"
            or p_entity.get("legalName", {}).get("name") != "Allianz Global Corporate & Specialty SE"
            or p_entity.get("jurisdiction") != "DE"
            or p_entity.get("legalAddress", {}).get("country") != "DE"
            or p_entity.get("registeredAs") != "HRB 208312"
            or p_entity.get("status") != "ACTIVE"):
        raise GLEIFBranchReceiptError("parent legal entity changed")
    if b_reg.get("status") != "LAPSED" or p_reg.get("status") != "ISSUED":
        raise GLEIFBranchReceiptError("branch/parent LEI status changed; re-review")
    if (link.get("type") != "IS_INTERNATIONAL_BRANCH_OF"
            or link.get("startNode") != {"id": BRANCH, "type": "LEI"}
            or link.get("endNode") != {"id": PARENT, "type": "LEI"}
            or link.get("status") != "ACTIVE"):
        raise GLEIFBranchReceiptError("GLEIF branch relationship changed")
    if link_reg.get("status") != "LAPSED":
        raise GLEIFBranchReceiptError("relationship registration status changed; re-review")
    return {
        "schema": "oc-gleif-agcs-sg-international-branch-receipt-v0",
        "branch_lei": BRANCH,
        "parent_lei": PARENT,
        "branch_acra_registration": UEN,
        "branch_lei_registration": "LAPSED",
        "parent_lei_registration": "ISSUED",
        "gleif_relationship_type": "IS_INTERNATIONAL_BRANCH_OF",
        "gleif_relationship_status": "ACTIVE",
        "gleif_relationship_registration": "LAPSED",
        "evidence_only": True,
        "source_sha256": {
            k: hashlib.sha256(source_bytes[k]).hexdigest() for k in URLS
        },
        "source_urls": dict(URLS),
        "independently_verified_mas_licence_current": False,
        "branch_parent_relationship_written_to_neon": False,
        "cat_exposure_verified": False,
        "model_input_approved": False,
    }


def download_one(kind: str) -> bytes:
    if kind not in URLS:
        raise GLEIFBranchReceiptError("unexpected original source")
    url = URLS[kind]
    time.sleep(0.2)
    req = Request(url, headers={
        "Accept": "application/vnd.api+json",
        "User-Agent": "OpenCatastrophe-data-research/0.1 (+https://github.com/pokekarten/OpenCatastrophe-data)"
    })
    with urlopen(req, timeout=20) as response:
        if response.status != 200 or response.geturl() != url:
            raise GLEIFBranchReceiptError("unreviewed HTTP source redirect/status")
        original = response.read(MAX_BYTES + 1)
    if len(original) > MAX_BYTES:
        raise GLEIFBranchReceiptError("original source body oversized")
    return original


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="opt in to exactly three fixed original GLEIF HTTPS reads")
    args = parser.parse_args()
    if not args.live:
        raise GLEIFBranchReceiptError("no live network without --live")
    receipt = original_audit({kind: download_one(kind) for kind in URLS})
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (GLEIFBranchReceiptError, OSError) as exc:
        raise SystemExit(f"BLOCKED: {exc}") from exc
