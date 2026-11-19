#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Derive one new, source-anchored Berlin SRGK study box from one original WFS area.

No dynamic source URL, provider geometry upload, insured building or hazard
claim. The output is one public derived pilot candidate for later independent
spatial-query confirmation, not a verified Berlin detailed depth model.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import ssl
import sys
from urllib import error, request

from shapely.geometry import box

from research_runners.berlin_srgk_model_area_pilot_coverage_v0 import (
    BBOX as OLD_BLD4_BBOX,
    CONTROL_URL,
    MAX_BYTES,
    TIMEOUT,
    CoverageBlocked,
    NoRedirect,
    parse_features,
)

PROFILE = "berlin-srgk-one-model-area-derived-second-pilot-v0"
# Conservative Berlin projected vicinity; this is a sanity bound, not a
# claim that every detail model is within this rectangular envelope.
BERLIN_ENVELOPE = box(340_000, 5_770_000, 465_000, 5_875_000)
HALF_WIDTH_M = 100
CENTER_GRID_M = 20
MIN_POSITIVE_INTERSECTION_M2 = 10.0


def choose_candidate(original_response: bytes) -> dict:
    parsed = parse_features(original_response, require_one=True)
    if not parsed["crs_validated"] or parsed["feature_count"] != 1:
        raise CoverageBlocked("no CRS-verified single official model-area feature")
    geom = parsed["geometry"]
    # Original source polygon can be multipart, never assume one part or
    # derive a candidate from an envelope centroid outside a polygon.
    if not geom.within(BERLIN_ENVELOPE) or geom.area < MIN_POSITIVE_INTERSECTION_M2:
        raise CoverageBlocked("model polygon outside Berlin research sanity envelope")
    point = geom.representative_point()
    if not geom.contains(point) or not point.within(BERLIN_ENVELOPE):
        raise CoverageBlocked("no source-interior representative point")
    # Snap *derived public research coordinates* deterministically. Do not
    # copy original vertices, building polygons, IDs, or provider attributes.
    east = int(math.floor(point.x / CENTER_GRID_M + 0.5) * CENTER_GRID_M)
    north = int(math.floor(point.y / CENTER_GRID_M + 0.5) * CENTER_GRID_M)
    second = box(east-HALF_WIDTH_M, north-HALF_WIDTH_M,
                 east+HALF_WIDTH_M, north+HALF_WIDTH_M)
    if not second.within(BERLIN_ENVELOPE) or second.intersects(box(*OLD_BLD4_BBOX)):
        raise CoverageBlocked("new pilot overlaps old BLD4 or leaves Berlin research bounds")
    intersection = geom.intersection(second)
    if (intersection.is_empty or not intersection.is_valid or
        not math.isfinite(intersection.area) or
        intersection.area < MIN_POSITIVE_INTERSECTION_M2 or
        intersection.area > 40_000.001):
        raise CoverageBlocked("new pilot lacks positive-area original polygon overlap")
    # Re-derive with exact decimal finite precision only; no original feature
    # geometry or address in the output. This is a *candidate*, not a proof
    # the provider supports an equivalent FES filter on later requests.
    return {
        "profile": PROFILE,
        "second_pilot_bbox_epsg25833": [int(v) for v in second.bounds],
        "second_pilot_size_m": [200, 200],
        "candidate_derived_from_one_original_source_polygon": True,
        "positive_original_source_polygon_overlap_area_m2": round(float(intersection.area), 1),
        "sampled_model_area_count": 1,
        "other_model_areas_not_sampled": True,
        "original_bld4_pilot_is_separate": True,
        "candidate_has_verified_geometry_in_same_source_response": True,
        "provider_fes_filter_for_second_pilot_verified": False,
        "detailed_depth_tiff_pixels_or_units_verified": False,
        "per_building_depth_or_insurer_loss_computed": False,
        "cat_model_input_approved": False,
        "original_source_features_ids_or_geometry_persisted": False,
    }


def _opener(req: request.Request, timeout: int):
    return request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    ).open(req, timeout=timeout)


def probe(*, opener=_opener, clock=lambda: datetime.now(timezone.utc)) -> dict:
    req = request.Request(CONTROL_URL, method="GET",
                          headers={"Accept": "application/json", "Accept-Encoding": "identity"})
    try:
        with opener(req, TIMEOUT) as resp:
            if resp.status != 200 or resp.geturl() != CONTROL_URL:
                raise CoverageBlocked("official Berlin WFS source URL or status drift")
            media = resp.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media not in ("application/json", "application/geo+json",
                             "application/vnd.geo+json"):
                raise CoverageBlocked("original WFS response not allowed GeoJSON")
            if resp.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise CoverageBlocked("unexpected original WFS compression")
            original = resp.read(MAX_BYTES+1)
    except CoverageBlocked:
        raise
    except (error.URLError, OSError, TimeoutError) as exc:
        raise CoverageBlocked("original source unavailable") from exc
    candidate = choose_candidate(original)
    stamp = clock()
    if not isinstance(stamp, datetime) or stamp.utcoffset() is None:
        raise CoverageBlocked("source retrieval clock not timezone aware")
    return {
        "original_wfs_getfeature_exact_url": CONTROL_URL,
        "original_source_response_sha256": sha256(original).hexdigest(),
        "original_source_response_bytes": len(original),
        "observed_utc": stamp.astimezone(timezone.utc).isoformat(),
        "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "one_exact_original_source_get": True,
        **candidate,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("explicit --live required for one reviewed official WFS request")
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
    except (CoverageBlocked, ValueError, OSError, ImportError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
