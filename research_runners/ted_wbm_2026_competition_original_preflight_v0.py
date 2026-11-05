# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""First source provenance for earlier official WBM competition 286307-2026.

Do not compare its tender *eligibility minimums* with contract identifier
percentage labels as if this automatically verifies a current signed policy.
Emit hash, size and independently checked semantic markers; never source XML.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from .ted_berlin_insurance_original_xml_preflight_v0 import MAX_BYTES

NOTICE = "286307-2026"
URL = "https://ted.europa.eu/en/notice/286307-2026/xml"
PINNED_ORIGINAL_SHA256 = "54c0c84b379a9629f3e5774245ca763f66159e2cf45704ba985589202adcf9a1"
PINNED_ORIGINAL_BYTES = 41307
MAX_TRIES = 2
EXPECTED = {
    "buyer": r"\bWBM\b",
    "subject": r"Industrielle\s+Sachversicherung",
    "nine_commercial": r"neun\s+reine\s+Gewerbeobjekte",
    "lead_minimum_30": r"(?:Führungsangebot|Führung).*?30\s*%",
    "participating_minimum_15": r"(?:Beteiligungsangebot|Beteiligung).*?15\s*%",
    "storm": r"\bSturm\b",
    "flood": r"\bÜberschwemmung\b",
    "earthquake": r"\bErdbeben\b",
}


def fetch(*, opener=urllib.request.urlopen) -> bytes:
    request = urllib.request.Request(
        URL, headers={"Accept": "application/xml",
                      "User-Agent": "OpenCatastrophe-public-TED-WBM-competition/1.0"},
    )
    for i in range(MAX_TRIES):
        with opener(request, timeout=35) as response:
            target = urllib.parse.urlsplit(response.geturl())
            if (target.scheme != "https" or target.hostname != "ted.europa.eu"
                    or target.path != "/en/notice/286307-2026/xml"
                    or target.query or target.fragment):
                raise ValueError("TED_WBM_COMPETITION_NONOFFICIAL_REDIRECT")
            status = getattr(response, "status", 200)
            if status == 202:
                if i == MAX_TRIES - 1:
                    raise ValueError("TED_WBM_COMPETITION_HTTP_202_NO_ORIGINAL")
                continue
            if status != 200:
                raise ValueError("TED_WBM_COMPETITION_HTTP_NON200_" + str(status))
            chunks = []
            size = 0
            while True:
                part = response.read(65536)
                if not part:
                    break
                size += len(part)
                if size > MAX_BYTES:
                    raise ValueError("TED_WBM_COMPETITION_SOURCE_OVERSIZE")
                chunks.append(part)
            data = b"".join(chunks)
            if len(data) < 100:
                raise ValueError("TED_WBM_COMPETITION_SOURCE_TRUNCATED")
            return data
    raise ValueError("TED_WBM_COMPETITION_SOURCE_UNAVAILABLE")


def inspect(
    data: bytes, *,
    expected_sha256: str = PINNED_ORIGINAL_SHA256,
    expected_bytes: int = PINNED_ORIGINAL_BYTES,
) -> dict:
    if type(data) is not bytes or not 100 <= len(data) <= MAX_BYTES:
        raise ValueError("TED_WBM_COMPETITION_SOURCE_SIZE_INVALID")
    if re.search(rb"<!\s*(?:DOCTYPE|ENTITY)\b", data, re.I):
        raise ValueError("TED_WBM_COMPETITION_XML_DTD_FORBIDDEN")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError("TED_WBM_COMPETITION_INVALID_XML") from exc
    if not isinstance(root.tag, str) or root.tag.split("}")[-1] != "ContractNotice":
        raise ValueError("TED_WBM_COMPETITION_NOT_COMPETITION_NOTICE")
    if sum(1 for _ in root.iter()) > 40000:
        raise ValueError("TED_WBM_COMPETITION_XML_TREE_TOO_LARGE")
    if NOTICE not in data.decode("utf-8", "ignore"):
        raise ValueError("TED_WBM_COMPETITION_WRONG_PUBLICATION_ID")
    text = re.sub(r"\s+", " ", " ".join(
        t.strip() for t in root.itertext() if t and t.strip()))
    if len(text) > 450000:
        raise ValueError("TED_WBM_COMPETITION_XML_TEXT_OVERSIZE")
    # All semantic terms must come from one original publisher XML body; no
    # second-source mirror can fill a missing marker.
    for key, pattern in EXPECTED.items():
        if not re.search(pattern, text, re.I):
            raise ValueError("TED_WBM_COMPETITION_MISSING_SOURCE_MARKER_" + key)
    if hashlib.sha256(data).hexdigest() != expected_sha256 or len(data) != expected_bytes:
        raise ValueError("TED_WBM_COMPETITION_IMMUTABLE_ORIGINAL_PIN_MISMATCH")
    return {
        "schema_version": "TED_WBM_2026_COMPETITION_PINNED_ORIGINAL_REPLAY_V0",
        "notice": NOTICE,
        "official_url": URL,
        "xml_root": "ContractNotice",
        "original_source_bytes": len(data),
        "original_source_sha256": hashlib.sha256(data).hexdigest(),
        "lead_writing_minimum_30_percent_in_2026_tender_text": True,
        "follower_writing_minimum_15_percent_in_2026_tender_text": True,
        "commercial_object_count_described_not_geocoded": 9,
        "storm_flood_earthquake_in_requested_coverage": True,
        "original_xml_retrieval_independently_rechecked_against_reviewed_sha": True,
        "final_policy_coverage_quotas_or_rv_10_percent_verified": False,
        "insured_building_risk_coordinates_or_tiv_admitted": False,
        "raw_original_xml_committed_or_printed": False,
    }


def main() -> int:
    try:
        print(json.dumps(inspect(fetch()), sort_keys=True))
    except (OSError, ValueError) as exc:
        print("TED_WBM_COMPETITION_ORIGINAL_PREFLIGHT_BLOCKED: "
              + str(exc)[:150], file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
