# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read exact official TED XML notices into *ephemeral* original-byte receipts.

Publisher XML is NEVER committed, dumped into CI logs or admitted as CAT
exposure. This is a source authenticity preflight: a first unpinned SHA-256
observation is not an immutable independently reverified source receipt.
Use a later reviewed explicit SHA pin before making that stronger claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BASE = "https://ted.europa.eu/en/notice/"
MAX_BYTES = 2_000_000
MAX_TEXT = 450_000
SOURCES = {
    "558592-2024": {
        "role": "gewobag_2024_insurance_competition_not_an_award",
        "expected_terms": (r"Gewobag", r"Gebäudeversicherung"),
        "original_xml_sha256_pinned": "51698e01c01caa9a0c58d41baf161d73a585d3b30f3b3dba12d95a3859b56b2f",
        "original_xml_bytes_pinned": 39733,
        "insurer_winner_as_of_2026_verified": False,
    },
    "668506-2026": {
        "role": "wbm_2026_nine_pure_commercial_object_award",
        "expected_terms": (r"WBM", r"Industrielle\s+Sachversicherung",
                           r"neun\s+reine\s+Gewerbeobjekte"),
        "original_xml_sha256_pinned": "7650720183d0c26430e0433858bf2e8b854ea68bb93fbf679e96ee696ee8fc78",
        "original_xml_bytes_pinned": 21837,
        "per_carrier_property_allocation_verified": False,
    },
}


def official_url(notice: str) -> str:
    if notice not in SOURCES:
        raise ValueError("TED_NOTICE_ID_NOT_ALLOWLISTED")
    return BASE + notice + "/xml"


def fetch(notice: str, *, opener=urllib.request.urlopen) -> bytes:
    url = official_url(notice)
    request = urllib.request.Request(
        url, headers={
            "Accept": "application/xml, text/xml;q=0.9",
            "User-Agent": "OpenCatastrophe-public-source-provenance/1.0",
        }
    )
    with opener(request, timeout=35) as response:
        effective = urllib.parse.urlsplit(response.geturl())
        if (effective.scheme != "https" or effective.hostname != "ted.europa.eu"
                or effective.path != urllib.parse.urlsplit(url).path):
            raise ValueError("TED_NOTICE_REDIRECT_CHANGED_OR_NOT_OFFICIAL")
        status = getattr(response, "status", 200)
        if status != 200:
            raise ValueError(f"TED_HTTP_NON_200_STATUS_{status}")
        chunks = []
        length = 0
        while True:
            chunk = response.read(65536)
            if not chunk:
                break
            length += len(chunk)
            if length > MAX_BYTES:
                raise ValueError("TED_SOURCE_EXCEEDS_MAX_BYTES")
            chunks.append(chunk)
    data = b"".join(chunks)
    if not data or len(data) < 100:
        raise ValueError("TED_SOURCE_TRUNCATED")
    return data


def inspect(notice: str, body: bytes) -> dict:
    spec = SOURCES.get(notice)
    if spec is None:
        raise ValueError("TED_NOTICE_ID_NOT_ALLOWLISTED")
    if type(body) is not bytes or not 100 <= len(body) <= MAX_BYTES:
        raise ValueError("TED_INVALID_SOURCE_SIZE_OR_TYPE")
    # Disable DTD/entity-based substitutions; ElementTree does not resolve
    # external entities, but reject these constructs rather than trust them.
    if re.search(rb"<!\s*(?:DOCTYPE|ENTITY)\b", body, flags=re.IGNORECASE):
        raise ValueError("TED_DOCTYPE_OR_ENTITY_FORBIDDEN")
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        raise ValueError("TED_NOT_XML_OR_INVALID_DOCUMENT") from exc
    tag = root.tag.split("}")[-1] if isinstance(root.tag, str) else ""
    if not (tag.endswith("Notice") and tag not in ("HTMLNotice", "FakeNotice")):
        raise ValueError("TED_UNEXPECTED_XML_NOTICE_ROOT")
    source_text = " ".join(
        t.strip() for t in root.itertext()
        if t and t.strip()
    )
    if len(source_text) > MAX_TEXT:
        raise ValueError("TED_EXTRACTED_TEXT_OVERSIZE")
    normalized = re.sub(r"\s+", " ", source_text)
    for expression in spec["expected_terms"]:
        if not re.search(expression, normalized, flags=re.IGNORECASE):
            raise ValueError("TED_EXPECTED_BUYER_OR_PRODUCT_TEXT_MISSING")
    source_sha = hashlib.sha256(body).hexdigest()
    if spec["original_xml_sha256_pinned"] is not None and source_sha != spec["original_xml_sha256_pinned"]:
        raise ValueError("TED_PINNED_ORIGINAL_SHA256_MISMATCH")
    if spec["original_xml_bytes_pinned"] is not None and len(body) != spec["original_xml_bytes_pinned"]:
        raise ValueError("TED_PINNED_ORIGINAL_BYTE_COUNT_MISMATCH")
    return {
        "notice": notice,
        "official_original_xml_url": official_url(notice),
        "expected_notice_role": spec["role"],
        "xml_document_root": tag,
        "original_source_bytes": len(body),
        "original_source_sha256": source_sha,
        "original_sha256_immutable_pin_verified": spec["original_xml_sha256_pinned"] is not None,
        "original_byte_count_immutable_pin_verified": spec["original_xml_bytes_pinned"] is not None,
        "source_document_semantic_marker_count": len(spec["expected_terms"]),
        "buyer_and_notice_subject_markers_present": True,
        # Publication number may be held outside a body element; its absence
        # is never quietly substituted with a fake XML field.
        "publication_number_literal_present_in_xml": notice in body.decode("utf-8", errors="ignore"),
        "source_original_bytes_committed_or_printed": False,
        "awarded_insurer_shares_or_per_property_allocation_verified": False,
        "actual_real_insured_location_or_tiv_admitted": False,
        "current_2026_gewobag_carrier_contract_verified": False,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--notice", choices=sorted(SOURCES), action="append",
                   help="exact official TED publication number; default both")
    args = p.parse_args(argv)
    try:
        receipts = [
            inspect(n, fetch(n)) for n in (args.notice or sorted(SOURCES))
        ]
        print(json.dumps({
            "schema": "OFFICIAL_TED_TWO_BERLIN_INSURANCE_NOTICES_XML_PREFLIGHT_V0",
            "publisher": "TED Publications Office of the European Union",
            "observed_original_xml_not_admitted_to_insurer_exposure": True,
            "source_xml_bytes_written_to_repository_or_console": False,
            "all_original_hashes_fixed_in_reviewed_source_register": all(
                r["original_sha256_immutable_pin_verified"] for r in receipts
            ),
            "source_receipts": receipts,
            "actual_carrier_by_site_tiv_or_losses_observed": False,
        }, sort_keys=True, ensure_ascii=False))
    except (OSError, ValueError) as exc:
        print("TED_ORIGINAL_SOURCE_PREFLIGHT_BLOCKED: " + str(exc)[:140], file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
