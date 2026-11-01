#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Official Berlin Umweltatlas building heights WFS bounded access receipt.

Only one GetCapabilities source request, never GetFeature or building
height/roof values. The independent 2022/2023 LoD2-derived source is
not identical to mutable Berlin ALKIS or a 2021 building vintage.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
import sys
from typing import Callable, Any
from urllib import request, error

from research_runners.berlin_alkis_gebaeude_wfs_capabilities_v0 import (
    BerlinWfsError, inspect_capabilities,
)

BASE = "https://gdi.berlin.de/services/wfs/ua_gebaeudehoehen"
URL = BASE + "?request=GetCapabilities&service=WFS"
CATALOG = "https://daten.berlin.de/datensaetze/gebaudehohen-umweltatlas-wfs-d918088d"
TECHNICAL_FIELDS = (
    "https://gdi.berlin.de/data/ua_gebaeudehoehen/docs/"
    "Datenformatbeschreibung_06_10_1gebhoehen2022.pdf"
)
MAX_BYTES = 4_194_304
TIMEOUT = 35
PROFILE = "oc-berlin-umweltatlas-loD2-height-wfs-capabilities-v0"


class BerlinHeightWfsError(ValueError):
    """Unexpected separate height provider metadata; do not infer sources."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise BerlinHeightWfsError("reviewed official building-height WFS redirected")


def _fetch(req: request.Request, timeout: int):
    return request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    ).open(req, timeout=timeout)


def inspect_height_service(raw: bytes) -> dict[str, Any]:
    try:
        metadata = inspect_capabilities(raw)
    except BerlinWfsError as exc:
        raise BerlinHeightWfsError("official independent building-height WFS invalid") from exc
    if metadata["wfs_version"] != "2.0.0":
        raise BerlinHeightWfsError("unexpected 2022 height service WFS version")
    # Separate user-facing semantics are not established from the names
    # alone; only public provider layer metadata are returned.
    return {
        "wfs_version": metadata["wfs_version"],
        "advertised_feature_type_count": metadata["advertised_feature_type_count"],
        "height_candidate_feature_types": metadata["candidate_building_feature_types"],
        "height_candidate_feature_type_count": metadata["building_feature_type_count"],
        "provider_original_height_values_obtained": False,
        "official_source_identifier_mapped_to_ALKIS": False,
        "original_roof_or_building_geometries_obtained": False,
        "object_building_vs_part_mapping_verified": False,
    }


def probe(
    *, opener: Callable[[request.Request, int], Any] = _fetch,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> dict[str, Any]:
    req = request.Request(URL, method="GET", headers={
        "Accept": "application/xml, text/xml;q=0.9",
    })
    try:
        with opener(req, TIMEOUT) as response:
            if response.status != 200 or response.geturl() != URL:
                raise BerlinHeightWfsError("wrong fixed official height source response")
            media = response.headers.get("Content-Type", "").split(";", 1)[0].lower().strip()
            if media not in ("application/xml", "text/xml", "application/vnd.ogc.wfs_xml"):
                raise BerlinHeightWfsError("wrong official height WFS metadata type")
            raw = response.read(MAX_BYTES + 1)
    except BerlinHeightWfsError:
        raise
    except (error.URLError, OSError, TimeoutError) as exc:
        raise BerlinHeightWfsError("official building-height WFS not accessible") from exc
    verified = inspect_height_service(raw)
    utc = clock()
    if utc.tzinfo is None or utc.utcoffset() is None:
        raise BerlinHeightWfsError("UTC clock must be timezone aware")
    return {
        "profile": PROFILE,
        "source": "Berlin Umweltatlas Gebäudehöhen (LoD2-derived) WFS",
        "separate_source_catalogue_url": CATALOG,
        "separate_source_schema_documentation": TECHNICAL_FIELDS,
        "catalogue_license_label": "dl-de-zero-2.0",
        "catalogue_updated_on": "2023-08-23",
        "source_url": URL,
        "retrieved_at_utc": utc.astimezone(timezone.utc).isoformat(),
        "original_response_bytes": len(raw),
        "original_response_sha256": hashlib.sha256(raw).hexdigest(),
        "reviewed_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "original_provider_bytes_saved": False,
        "CAT_database_modified": False,
        "height_or_age_inferred_to_insured_buildings": False,
        "source_model_admitted": False,
        **verified,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", action="store_true")
    args = p.parse_args(argv)
    if not args.live:
        p.error("offline by default; --live requests one official bounded WFS metadata response")
    try:
        print(json.dumps(probe(), indent=2, sort_keys=True, allow_nan=False))
    except (BerlinHeightWfsError, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
