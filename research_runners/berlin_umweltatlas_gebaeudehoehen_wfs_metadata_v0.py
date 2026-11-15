#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One exact, bounded original Berlin Umweltatlas roof-height WFS metadata probe.

No GetFeature, individual building, height values, address, owner data, or
original XML is written. 2022 LoD2 height source != current ALKIS WFS.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
import sys
from typing import Any, Callable
from urllib import request, error

from research_runners.berlin_alkis_gebaeude_wfs_capabilities_v0 import (
    BerlinWfsError, inspect_capabilities,
)

BASE = "https://gdi.berlin.de/services/wfs/ua_gebaeudehoehen"
URL = BASE + "?request=GetCapabilities&service=WFS"
CATALOGUE = "https://daten.berlin.de/datensaetze/gebaudehohen-umweltatlas-wfs-d918088d"
SOURCE_ID = "de.berlin.umweltatlas-gebaeudehoehen-2022.wfs"
PROFILE = "oc-berlin-umweltatlas-loD2-height-wfs-metadata-v0"
MAX_BYTES = 2_097_152
TIMEOUT = 35


class HeightWfsError(ValueError):
    """Exact source identity or metadata boundaries not independently verified."""


def inspect(raw: bytes) -> dict[str, Any]:
    """Parse only bounded feature-type names and CRS metadata, no source objects."""
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise HeightWfsError("empty or oversized height WFS metadata")
    try:
        metadata = inspect_capabilities(raw)
    except BerlinWfsError as exc:
        raise HeightWfsError("invalid official WFS capabilities") from exc
    if metadata["wfs_version"] != "2.0.0":
        raise HeightWfsError("unreviewed Umweltatlas WFS protocol version")
    height_layers = [
        row for row in metadata["candidate_building_feature_types"]
        if "hoehe" in row["name"].casefold() or "höhe" in row["name"].casefold()
    ]
    if not height_layers:
        raise HeightWfsError("historical building-height layer not advertised")
    if len(height_layers) > 8:
        raise HeightWfsError("unbounded building-height feature-type count")
    return {
        "wfs_version": metadata["wfs_version"],
        "advertised_feature_type_count": metadata["advertised_feature_type_count"],
        "height_feature_types": height_layers,
        "height_feature_type_count": len(height_layers),
        "other_feature_types_not_assumed_to_be_height_data": (
            metadata["advertised_feature_type_count"] - len(height_layers)
        ),
        "full_source_field_schema_verified": False,
        "building_heights_retrieved": False,
        "measured_heights_proven": False,
        "original_feature_bytes_saved": False,
        "model_input_admitted": False,
    }


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise HeightWfsError("fixed official height WFS redirected")


def _fetch(req: request.Request, timeout: int):
    return request.build_opener(
        request.ProxyHandler({}),
        NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    ).open(req, timeout=timeout)


def probe(
    *, opener: Callable[[request.Request, int], Any] = _fetch,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> dict[str, Any]:
    req = request.Request(
        URL, method="GET", headers={"Accept": "application/xml, text/xml;q=0.9"},
    )
    try:
        with opener(req, TIMEOUT) as response:
            if response.status != 200 or response.geturl() != URL:
                raise HeightWfsError("unexpected provider URL or response status")
            media = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media not in ("application/xml", "text/xml", "application/vnd.ogc.wfs_xml"):
                raise HeightWfsError("unexpected official WFS metadata content type")
            raw = response.read(MAX_BYTES + 1)
    except HeightWfsError:
        raise
    except (OSError, error.URLError, TimeoutError) as exc:
        raise HeightWfsError("official height WFS metadata request failed") from exc

    metadata = inspect(raw)
    dt = clock()
    if not isinstance(dt, datetime) or dt.tzinfo is None or dt.utcoffset() is None:
        raise HeightWfsError("UTC receipt clock must be timezone-aware")
    return {
        "profile": PROFILE,
        "candidate_id": SOURCE_ID,
        "catalogue_url": CATALOGUE,
        "request_url": URL,
        "retrieved_at_utc": dt.astimezone(timezone.utc).isoformat(),
        "response_bytes": len(raw),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_temporal_reference": "Umweltatlas 2022, ALKIS footprint reference 2022-04-07",
        "source_independent_from_current_alkis": False,
        "height_may_be_imputed_as_three_metres": True,
        "no_individual_buildings_or_roof_attributes_requested": True,
        "new_model_permission_granted": False,
        "source_raw_xml_persisted": False,
        **metadata,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("offline by default; explicit --live required")
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
    except (HeightWfsError, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
