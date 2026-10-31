#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Reproduce publisher-byte exact HANZE native S2 2024 region-code evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

if __package__:
    from .hanze_native_regions2024_source_audit_v0 import (
        FILE_URL, PUBLISHER_BYTES, audit_hanze_s2_candidate_codes,
    )
    from .dfo_hanze_original_provider_overlap_receipt_v0 import (
        COUNTRY_CROSSWALK, fetch_hanze_pinned, fetch_publisher_bytes,
    )
    from .dfo_original_provider_byte_receipt_v0 import PINNED_ORIGINAL_SHA256, verify_source_bytes
    from .historical_cat_csv_provider_receipt_v0 import SOURCE_RECEIPT
    from .flood_event_link_candidates_v0 import link_candidates
else:
    from hanze_native_regions2024_source_audit_v0 import (
        FILE_URL, PUBLISHER_BYTES, audit_hanze_s2_candidate_codes,
    )
    from dfo_hanze_original_provider_overlap_receipt_v0 import (
        COUNTRY_CROSSWALK, fetch_hanze_pinned, fetch_publisher_bytes,
    )
    from dfo_original_provider_byte_receipt_v0 import PINNED_ORIGINAL_SHA256, verify_source_bytes
    from historical_cat_csv_provider_receipt_v0 import SOURCE_RECEIPT
    from flood_event_link_candidates_v0 import link_candidates


PINNED_S2_SHA256 = "4d5f26a28b742debf86598f1cfd99887930de1d0e45ca72a6c3cd2ea90d57edc"
PINNED_S2_REGION_COUNT = 1442
PINNED_S2_COUNTRY_COUNT = 42
PINNED_MULTI_REGION_PAIRS = 9
PINNED_REGION_LIST_TOKENS = 150


def fetch_versioned_hanze_regions() -> bytes:
    request = urllib.request.Request(FILE_URL, headers={"User-Agent": "OpenCatastropheHANZENativeRegions/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        if not response.geturl().startswith("https://zenodo.org/"):
            raise ValueError("HANZE regional glossary redirected outside publisher")
        original = response.read(PUBLISHER_BYTES + 1)
    if len(original) != PUBLISHER_BYTES:
        raise ValueError("publisher HANZE S2 original size drift")
    return original


def reproduce_s2_receipt(dfo: bytes, hanze: bytes, s2: bytes,
                         expected_s2_sha256: str | None = None) -> dict:
    dfo_receipt = verify_source_bytes(dfo, expected_sha256=PINNED_ORIGINAL_SHA256)
    if dfo_receipt["reported_event_count"] != 5503:
        raise ValueError("DFO original profile drift")
    han = SOURCE_RECEIPT["sources"]["hanze_v3_0_2_beta"]
    crosswalk = json.dumps(COUNTRY_CROSSWALK, sort_keys=True, separators=(",", ":")).encode("utf-8")
    candidate = link_candidates(
        dfo, PINNED_ORIGINAL_SHA256, hanze, han["observed_sha256"],
        crosswalk, hashlib.sha256(crosswalk).hexdigest(),
    )
    out = audit_hanze_s2_candidate_codes(
        hanze, han["observed_sha256"], candidate, s2, expected_s2_sha256=expected_s2_sha256,
    )
    if out["candidate_pair_count"] != 9:
        raise ValueError("unexpected real DFO/HANZE candidate count")
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--expected-s2-sha256")
    args = parser.parse_args()
    result = reproduce_s2_receipt(
        fetch_publisher_bytes(), fetch_hanze_pinned(), fetch_versioned_hanze_regions(),
        expected_s2_sha256=PINNED_S2_SHA256,
    )
    if args.expected_s2_sha256 is not None and args.expected_s2_sha256 != PINNED_S2_SHA256:
        raise ValueError("HANZE S2 independently pinned checksum cannot be overridden")
    if (result["original_glossary"]["distinct_region_codes"] != PINNED_S2_REGION_COUNT
            or result["original_glossary"]["distinct_region_country_prefixes"] != PINNED_S2_COUNTRY_COUNT
            or result["status_counts"]["exact_multi_region_glossary_matched"] != PINNED_MULTI_REGION_PAIRS
            or result["region_tokens_from_accepted_lists"] != PINNED_REGION_LIST_TOKENS):
        raise ValueError("HANZE S2 original regional glossary or candidate profile drift")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
