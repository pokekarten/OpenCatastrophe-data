#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Berlin SRGK exact 200m model-area FES Intersects proof, not hazard pixels.

Official WFS XSD independently verified `geom` as MultiSurfacePropertyType.
One fixed positive-control WFS GetFeature + one fixed FES spatial filter;
no provider geometry, raster, address, risk or CAT model evidence persisted.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import ssl
import sys
from urllib import error, parse, request

from research_runners.berlin_srgk_model_area_pilot_coverage_v0 import (
    BBOX, CONTROL_URL, MAX_BYTES, PARAMS, ROOT, TIMEOUT,
    CoverageBlocked, NoRedirect, classify,
)

SCHEMA_XSD_SHA256 = "8112bf8db14b7f3f1cb516717e128e0a450b643e645c29b1955e6c69bd57b87f"
SCHEMA_SOURCE_RUN = 41355903211
PROFILE = "berlin-srgk-fes2-exact-geom-intersects-bld4-pilot-v0"
FILTER = (
    '<fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0" '
    'xmlns:gml="http://www.opengis.net/gml/3.2">'
    '<fes:Intersects><fes:ValueReference>geom</fes:ValueReference>'
    '<gml:Envelope srsName="EPSG:25833">'
    '<gml:lowerCorner>391700 5819950</gml:lowerCorner>'
    '<gml:upperCorner>391900 5820150</gml:upperCorner>'
    '</gml:Envelope></fes:Intersects></fes:Filter>'
)
FILTER_URL = ROOT + "?" + parse.urlencode(PARAMS + [("filter", FILTER)])


def _get(req, timeout):
    return request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    ).open(req, timeout=timeout)


def _bounded_source_get(url: str, opener) -> bytes:
    if url not in (CONTROL_URL, FILTER_URL):
        raise CoverageBlocked("source request not exact and source-locked")
    req = request.Request(url, method="GET", headers={"Accept": "application/json"})
    try:
        with opener(req, TIMEOUT) as resp:
            if resp.status != 200 or resp.geturl() != url:
                raise CoverageBlocked("unexpected WFS status or source redirect")
            media = resp.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media not in ("application/json", "application/geo+json", "application/vnd.geo+json"):
                raise CoverageBlocked("source did not return GeoJSON in fixed FES query")
            return resp.read(MAX_BYTES + 1)
    except CoverageBlocked:
        raise
    except (error.URLError, TimeoutError, OSError) as exc:
        raise CoverageBlocked("reviewed exact official FES request failed") from exc


def probe(*, opener=_get, clock=lambda: datetime.now(timezone.utc)):
    control = _bounded_source_get(CONTROL_URL, opener)
    candidate = _bounded_source_get(FILTER_URL, opener)
    safe = {
        "profile": PROFILE,
        "reviewed_official_xsd_sha256": SCHEMA_XSD_SHA256,
        "reviewed_original_xsd_workflow_id": SCHEMA_SOURCE_RUN,
        "fes_geometry_property": "geom",
        "original_control_sha256": sha256(control).hexdigest(),
        "original_fes_pilot_sha256": sha256(candidate).hexdigest(),
        "original_control_bytes": len(control),
        "original_fes_pilot_bytes": len(candidate),
        "original_control_and_fes_bodies_identical": control == candidate,
        "exact_reviewed_public_wfs_requests": 2,
        "raw_source_features_or_geometry_persisted": False,
        "physical_water_depth_units_verified": False,
        "insured_cat_model_admitted": False,
    }
    try:
        result = classify(control, candidate)
    except (CoverageBlocked, ImportError) as exc:
        # Even if provider does not support the FES operation, preserve enough
        # identity to investigate without publishing any source coordinates.
        print(json.dumps({
            **safe,
            "fes_source_coverage_status": "BLOCKED_UNVERIFIED_FILTER_RESULT",
            "block_reason": str(exc),
            "insured_cat_model_admitted": False,
        }, sort_keys=True), file=sys.stderr)
        raise
    now = clock()
    if not isinstance(now, datetime) or now.utcoffset() is None:
        raise CoverageBlocked("original source timestamp must have timezone")
    return {
        **safe,
        "fes_exact_intersects_filter_requested": True,
        "fes_bld4_pilot_query_crs": "EPSG:25833",
        "fes_bld4_original_bbox_m": list(BBOX),
        "checked_utc": now.astimezone(timezone.utc).isoformat(),
        "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        **result,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("explicit --live required to query one fixed FES filter and control")
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
    except (CoverageBlocked, ImportError, ValueError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
