# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed original BKG VG250 31.12.2025 GPKG ZIP .md5 sidecar preflight.

One immutable-looking ORIGINAL sidecar *response* is scientific metadata only:
the official /aktuell/ path is mutable and the published MD5 does not establish
the full ZIP SHA-256, release identity inside ZIP, projection, topological
quality, insured-site geolocation, nor CAT model-input approval.

This module has no network code, writes no provider source, and never exports
a full data ZIP or its contents. Call only with an exact authorized provider
sidecar obtained separately and protect complete original response bytes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

SOURCE_ID = "de.bkg.vg250.3112.2025"
SOURCE_VERSION = "VG250 Ebenen 31.12.2025, UTM32s GPKG ZIP"
PROVIDER = "Bundesamt fuer Kartographie und Geodaesie (BKG)"
PRODUCT_URL = (
    "https://gdz.bkg.bund.de/index.php/default/"
    "verwaltungsgebiete-1-250-000-stand-31-12-vg250-31-12.html"
)
SIDE_CAR_URL = (
    "https://daten.gdz.bkg.bund.de/produkte/vg/vg250_ebenen_1231/"
    "aktuell/vg250_12-31.utm32s.gpkg.ebenen.zip.md5"
)
ARCHIVE_URL = SIDE_CAR_URL[:-4]
ARCHIVE_NAME = "vg250_12-31.utm32s.gpkg.ebenen.zip"
# Observed on the official /aktuell/ directory, dated 08-Jun-2026; source
# listing metadata and vintage do not make the *full ZIP* immutable.
OFFICIAL_PUBLISHED_MD5 = "e6b4cf28d4b83557b4d6e3236713dec0"
MAX_SIDECAR_BYTES = 128

# GNU md5sum prints two spaces before the file name; a text-mode one-space
# sidecar or CRLF is tolerated, but never extra lines, paths, or arbitrary
# target ZIPs. No externally supplied filename or URL can change this gate.
SIDECAR_RE = re.compile(
    rb"([0-9a-f]{32})[ ]{1,2}(?:\*)?"
    rb"(vg250_12-31\.utm32s\.gpkg\.ebenen\.zip)(?:\r?\n)?\Z"
)


class BkgVg250SidecarBlocked(ValueError):
    """External source metadata or product identity failed closed."""


def inspect_original_sidecar(raw: bytes) -> dict[str, Any]:
    """Validate original publisher sidecar bytes, not the unseen ZIP payload."""
    if type(raw) is not bytes or not 1 <= len(raw) <= MAX_SIDECAR_BYTES:
        raise BkgVg250SidecarBlocked("sidecar missing, oversized or non-bytes")
    match = SIDECAR_RE.fullmatch(raw)
    if not match:
        raise BkgVg250SidecarBlocked("sidecar invalid MD5 record or ZIP identity")
    archive_md5 = match.group(1).decode("ascii")
    filename = match.group(2).decode("ascii")
    if archive_md5 != OFFICIAL_PUBLISHED_MD5 or filename != ARCHIVE_NAME:
        raise BkgVg250SidecarBlocked("source product sidecar MD5 changed")
    return {
        "source_id": SOURCE_ID,
        "product_version_from_official_page": SOURCE_VERSION,
        "provider": PROVIDER,
        "source_product_url": PRODUCT_URL,
        "original_provider_sidecar_url": SIDE_CAR_URL,
        "archive_url_not_downloaded": ARCHIVE_URL,
        "original_provider_sidecar_bytes": len(raw),
        "original_provider_sidecar_sha256": hashlib.sha256(raw).hexdigest(),
        "publisher_zip_md5_claim_from_original_sidecar": archive_md5,
        "expected_zip_basename": ARCHIVE_NAME,
        "full_zip_original_sha256_verified": False,
        "full_zip_original_bytes_acquired": False,
        "actual_zip_vintage_and_GPKG_layers_verified": False,
        "BKG_rights_and_attribution": "DL-DE-BY-2.0; BKG/year/data-sources",
        "coastal_GF2_vs_GF4_land_semantics_verified_for_2025": False,
        "model_input_approved": False,
        "risk_geolocation_approved": False,
        "sidecar_bytes_or_original_zip_persisted": False,
        "scope": "original_69ish_byte_md5_sidecar_only_not_full_zip_or_geom",
    }


def inspect_local_file(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise BkgVg250SidecarBlocked("expected regular non-symlink sidecar file")
    if not 1 <= path.stat().st_size <= MAX_SIDECAR_BYTES:
        raise BkgVg250SidecarBlocked("unexpected sidecar byte size")
    with path.open("rb") as handle:
        return inspect_original_sidecar(handle.read(MAX_SIDECAR_BYTES + 1))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-sidecar", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        summary = inspect_local_file(args.original_sidecar)
    except (BkgVg250SidecarBlocked, OSError, OverflowError, UnicodeError):
        print("BLOCKED: original BKG VG250 2025 sidecar not verified", file=sys.stderr)
        return 2
    summary["verified_by_tool_utc"] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
