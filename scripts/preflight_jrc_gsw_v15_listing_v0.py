# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline preflight for one original JRC Global Surface Water v1.5 asset path.

This checks *catalogue listing identity only*. It neither downloads a GeoTIFF
nor grants scientific, licensing, or model-input admission. The exact original
listing must be acquired separately; no network activity is performed here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SOURCE_ID = "ec-jrc.global-surface-water.1984-2024"
ORIGINAL_LISTING_URL = "https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/"
PUBLISHER_PAGE = "https://global-surface-water.appspot.com/download"
SELECTED_ASSET = (
    "download2024/Aggregated/VER1-5/occurrence/"
    "occurrence_10E_50N_v1_5_2024.tif"
)
MAX_LISTING_BYTES = 8_000_000


class GSWListingError(ValueError):
    """Original provider listing is missing, ambiguous or not parseable."""


def inspect_original_listing(payload: bytes) -> dict[str, object]:
    """Return a provenance receipt; do not infer asset bytes or pixel correctness."""
    if not isinstance(payload, bytes) or not payload or len(payload) > MAX_LISTING_BYTES:
        raise GSWListingError("original catalogue bytes missing or exceed fixed 8 MB bound")
    try:
        listing = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GSWListingError("original catalogue must be UTF-8") from exc
    if "\x00" in listing:
        raise GSWListingError("NUL in listing")
    paths = [line.strip() for line in listing.splitlines() if line.strip()]
    # No URL synthesis, fuzzy matching, or falling back to deprecated v1.4.
    selected_count = sum(line == SELECTED_ASSET for line in paths)
    if selected_count != 1:
        raise GSWListingError(
            "fixed v1.5 occurrence source path must occur exactly once "
            f"(found {selected_count})"
        )
    if any(
        line.startswith(("http:", "https:", "<", "/", "\\"))
        or "../" in line or "\\" in line or any(c.isspace() for c in line)
        for line in paths
    ):
        raise GSWListingError("expected safe provider-relative paths, not HTML or arbitrary URLs")
    return {
        "schema": "jrc-gsw-v15-original-listing-preflight-v0",
        "source_id": SOURCE_ID,
        "source_product_version": "1.5 (1984-2024)",
        "original_listing_url": ORIGINAL_LISTING_URL,
        "original_listing_sha256": hashlib.sha256(payload).hexdigest(),
        "original_listing_bytes": len(payload),
        "selected_path": SELECTED_ASSET,
        "selected_path_occurrences": selected_count,
        "original_asset_sha256": None,
        "original_asset_bytes_verified": False,
        "raster_pixel_values_verified": False,
        "source_data_downloaded_by_preflight": False,
        "model_input_approved": False,
        "science_notice": (
            "2026-11-10 corrected occurrence >100 in v1.5; use current bytes; "
            "monthly recurrence has separate unresolved sparse-observation issue"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-listing-file", type=Path, required=True)
    args = parser.parse_args()
    try:
        stat = args.original_listing_file.stat()
        if stat.st_size > MAX_LISTING_BYTES:
            raise GSWListingError("original catalogue exceeds fixed 8 MB bound")
        result = inspect_original_listing(args.original_listing_file.read_bytes())
    except (OSError, GSWListingError) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
