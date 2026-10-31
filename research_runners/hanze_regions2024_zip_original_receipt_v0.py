#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fetch HANZE v3.0.2-beta region ZIP original and emit metadata-only receipt."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import urllib.request
from urllib.parse import urlsplit

if __package__:
    from .hanze_regions2024_geometry_zip_audit_v0 import (
        SOURCE_URL, PUBLISHER_BYTES, inspect_hanze_region_geometry_zip,
    )
    from .hanze_regions2024_geometry_code_coverage_v0 import (
        compare_hanze_geometry_native_glossary, survey_verified_event_region_geometry_coverage,
    )
    from .hanze_native_regions2024_original_receipt_v0 import (
        fetch_versioned_hanze_regions, PINNED_S2_SHA256,
    )
    from .dfo_hanze_original_provider_overlap_receipt_v0 import (
        COUNTRY_CROSSWALK, fetch_hanze_pinned, fetch_publisher_bytes,
    )
    from .dfo_original_provider_byte_receipt_v0 import PINNED_ORIGINAL_SHA256
    from .historical_cat_csv_provider_receipt_v0 import SOURCE_RECEIPT
    from .flood_event_link_candidates_v0 import link_candidates
else:
    from hanze_regions2024_geometry_zip_audit_v0 import (
        SOURCE_URL, PUBLISHER_BYTES, inspect_hanze_region_geometry_zip,
    )
    from hanze_regions2024_geometry_code_coverage_v0 import (
        compare_hanze_geometry_native_glossary, survey_verified_event_region_geometry_coverage,
    )
    from hanze_native_regions2024_original_receipt_v0 import (
        fetch_versioned_hanze_regions, PINNED_S2_SHA256,
    )
    from dfo_hanze_original_provider_overlap_receipt_v0 import (
        COUNTRY_CROSSWALK, fetch_hanze_pinned, fetch_publisher_bytes,
    )
    from dfo_original_provider_byte_receipt_v0 import PINNED_ORIGINAL_SHA256
    from historical_cat_csv_provider_receipt_v0 import SOURCE_RECEIPT
    from flood_event_link_candidates_v0 import link_candidates


PINNED_ZIP_SHA256 = "4e8a4afe47940fbe38600fa7090faf84da389e7bb65bc72c1b65244c837b1ff8"


def fetch_zip_publisher() -> bytes:
    req = urllib.request.Request(SOURCE_URL, headers={
        "User-Agent": "OpenCatastropheHANZEOriginalGeometryAudit/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        url = urlsplit(response.geturl())
        if url.scheme != "https" or url.hostname != "zenodo.org":
            raise ValueError("region ZIP redirected outside source publisher")
        blob = response.read(PUBLISHER_BYTES + 1)
    if len(blob) != PUBLISHER_BYTES:
        raise ValueError("original regional ZIP size drift")
    return blob


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--expected-source-sha256", default=None)
    args = p.parse_args()
    if args.expected_source_sha256 is not None and args.expected_source_sha256 != PINNED_ZIP_SHA256:
        raise ValueError("original HANZE 2024 region geometry archive SHA cannot be overridden")
    zip_bytes = fetch_zip_publisher()
    result = inspect_hanze_region_geometry_zip(zip_bytes, expected_sha256=PINNED_ZIP_SHA256)
    s2 = fetch_versioned_hanze_regions()
    dfo = fetch_publisher_bytes()
    hanze = fetch_hanze_pinned()
    crosswalk = json.dumps(COUNTRY_CROSSWALK, sort_keys=True, separators=(",", ":")).encode("utf-8")
    hanze_sha = SOURCE_RECEIPT["sources"]["hanze_v3_0_2_beta"]["observed_sha256"]
    overlaps = link_candidates(dfo, PINNED_ORIGINAL_SHA256, hanze, hanze_sha,
                               crosswalk, __import__("hashlib").sha256(crosswalk).hexdigest())
    result["native_glossary_geometry_id_comparison"] = compare_hanze_geometry_native_glossary(
        zip_bytes, s2, expected_zip_sha256=PINNED_ZIP_SHA256,
        expected_glossary_sha256=PINNED_S2_SHA256)
    result["candidate_region_geometry_id_coverage"] = survey_verified_event_region_geometry_coverage(
        zip_bytes, s2, hanze, hanze_sha, overlaps, expected_zip_sha256=PINNED_ZIP_SHA256,
        expected_glossary_sha256=PINNED_S2_SHA256)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True,
                                   allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
