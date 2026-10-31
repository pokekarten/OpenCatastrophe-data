#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Re-fetch official Eurostat NUTS 2024 attribute codes and original HANZE events.

Only aggregate NUTS identity coverage of verified DFO/HANZE candidate pairs
is emitted. No admin boundaries, originals, linked rows or insured losses
are redistributed. This is source research, not a CAT-model input approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
from urllib.parse import urlsplit

if __package__:
    from .dfo_hanze_original_provider_overlap_receipt_v0 import (
        COUNTRY_CROSSWALK, fetch_hanze_pinned, fetch_publisher_bytes,
    )
    from .dfo_original_provider_byte_receipt_v0 import PINNED_ORIGINAL_SHA256, verify_source_bytes
    from .historical_cat_csv_provider_receipt_v0 import SOURCE_RECEIPT
    from .flood_event_link_candidates_v0 import link_candidates
    from .hanze_gisco_nuts2024_attribute_audit_v0 import (
        GISCO_URL, MAX_BYTES, audit_hanze_candidate_region_codes,
    )
else:
    from dfo_hanze_original_provider_overlap_receipt_v0 import (
        COUNTRY_CROSSWALK, fetch_hanze_pinned, fetch_publisher_bytes,
    )
    from dfo_original_provider_byte_receipt_v0 import PINNED_ORIGINAL_SHA256, verify_source_bytes
    from historical_cat_csv_provider_receipt_v0 import SOURCE_RECEIPT
    from flood_event_link_candidates_v0 import link_candidates
    from hanze_gisco_nuts2024_attribute_audit_v0 import (
        GISCO_URL, MAX_BYTES, audit_hanze_candidate_region_codes,
    )


def fetch_official_nuts2024_attributes() -> bytes:
    request = urllib.request.Request(
        GISCO_URL, headers={"User-Agent": "OpenCatastropheNUTS2024SourceProof/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        final = urlsplit(response.geturl())
        if final.scheme != "https" or final.hostname != "gisco-services.ec.europa.eu":
            raise ValueError("GISCO download redirected outside official publisher")
        data = response.read(MAX_BYTES + 1)
    if not 0 < len(data) <= MAX_BYTES:
        raise ValueError("original GISCO attribute file is missing or oversized")
    return data


def make_gisco_hanze_receipt(dfo: bytes, hanze: bytes, gisco: bytes,
                            expected_gisco_sha256: str | None = None) -> dict:
    verified_dfo = verify_source_bytes(
        dfo, expected_sha256=PINNED_ORIGINAL_SHA256,
    )
    if verified_dfo["reported_event_count"] != 5503:
        raise ValueError("DFO source profile changed unexpectedly")
    han = SOURCE_RECEIPT["sources"]["hanze_v3_0_2_beta"]
    crosswalk = json.dumps(COUNTRY_CROSSWALK, sort_keys=True,
                           separators=(",", ":")).encode("utf-8")
    candidates = link_candidates(
        dfo, PINNED_ORIGINAL_SHA256, hanze, han["observed_sha256"],
        crosswalk, hashlib.sha256(crosswalk).hexdigest(),
    )
    result = audit_hanze_candidate_region_codes(
        hanze, han["observed_sha256"], candidates, gisco,
        expected_gisco_sha256=expected_gisco_sha256,
    )
    if result["candidate_pair_count"] != 9:
        raise ValueError("verified original DFO/HANZE candidate count drift")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-gisco-sha256", help="external independently pinned GISCO original digest")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = make_gisco_hanze_receipt(
        fetch_publisher_bytes(), fetch_hanze_pinned(),
        fetch_official_nuts2024_attributes(),
        expected_gisco_sha256=args.expected_gisco_sha256,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
