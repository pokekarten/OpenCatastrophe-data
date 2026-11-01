#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independent official FES proof for source-derived second Berlin SRGK pilot.

Exactly two fixed official GetFeature requests. The published source polygon
must still derive the same frozen second pilot and the independent filtered
polygon must positively intersect it. No flood-depth/risk/model admission.
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
from urllib import error, parse, request

from shapely.geometry import box

from research_runners.berlin_srgk_model_area_pilot_coverage_v0 import (
    CONTROL_URL, MAX_BYTES, PARAMS, ROOT, TIMEOUT,
    CoverageBlocked, NoRedirect, parse_features,
)
from research_runners.berlin_srgk_second_model_area_candidate_v0 import (
    choose_candidate,
)

PROFILE = "berlin-srgk-second-pilot-official-fes-independent-proof-v0"
SOURCE_ANCHOR_RUN = 41363179064
SOURCE_ANCHOR_SHA256 = "62d6c31ef5dd17227aad35afd740031eff9f7343f50bff99d941a0c822ff95d5"
SECOND_BBOX = (391860, 5816840, 392060, 5817040)
FILTER = (
    '<fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0" '
    'xmlns:gml="http://www.opengis.net/gml/3.2">'
    '<fes:Intersects><fes:ValueReference>geom</fes:ValueReference>'
    '<gml:Envelope srsName="EPSG:25833">'
    '<gml:lowerCorner>391860 5816840</gml:lowerCorner>'
    '<gml:upperCorner>392060 5817040</gml:upperCorner>'
    '</gml:Envelope></fes:Intersects></fes:Filter>'
)
FILTER_URL = ROOT + "?" + parse.urlencode(PARAMS + [("filter", FILTER)])


def _opener(req: request.Request, timeout: int):
    return request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    ).open(req, timeout=timeout)


def _fetch(url: str, opener) -> bytes:
    if url not in (CONTROL_URL, FILTER_URL):
        raise CoverageBlocked("unreviewed model-area request URL")
    req = request.Request(url, method="GET", headers={
        "Accept": "application/json", "Accept-Encoding": "identity"})
    try:
        with opener(req, TIMEOUT) as resp:
            if resp.status != 200 or resp.geturl() != url:
                raise CoverageBlocked("original WFS URL/status changed")
            if resp.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise CoverageBlocked("unreviewed source HTTP compression")
            media = resp.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media not in ("application/json", "application/geo+json",
                             "application/vnd.geo+json"):
                raise CoverageBlocked("original WFS not valid GeoJSON media")
            return resp.read(MAX_BYTES+1)
    except CoverageBlocked:
        raise
    except (error.URLError, OSError, TimeoutError) as exc:
        raise CoverageBlocked("original detailed source WFS unavailable") from exc


def evaluate(control_raw: bytes, filter_raw: bytes) -> dict:
    prior = choose_candidate(control_raw)
    if tuple(prior["second_pilot_bbox_epsg25833"]) != SECOND_BBOX:
        raise CoverageBlocked("source model geometry no longer anchors frozen second pilot")
    parsed = parse_features(filter_raw, require_one=False)
    if not parsed["feature_count"]:
        status = "FES_EMPTY_SECOND_PILOT_COVERAGE_UNRESOLVED"
        local_area = None
    else:
        area = float(parsed["geometry"].intersection(box(*SECOND_BBOX)).area)
        if not math.isfinite(area) or area < 10 or area > 40_000.001:
            raise CoverageBlocked("filtered model-area geometry fails exact positive intersection")
        status = "TWO_INDEPENDENT_SOURCE_QUERIES_VERIFY_MODEL_AREA_OVERLAP"
        local_area = round(area, 1)
    return {
        "profile": PROFILE,
        "second_fixed_pilot_epsg25833": list(SECOND_BBOX),
        "source_derived_candidate_intersection_m2": prior[
            "positive_original_source_polygon_overlap_area_m2"],
        "official_filtered_geometry_intersection_m2": local_area,
        "source_sampled_feature_count_control": 1,
        "source_sampled_feature_count_fes": int(parsed["feature_count"]),
        "provider_filter_acceptance_status": status,
        "previous_source_anchor_run": SOURCE_ANCHOR_RUN,
        "previous_source_anchor_sha256": SOURCE_ANCHOR_SHA256,
        "provider_spatial_filter_independently_confirmed": bool(parsed["feature_count"]),
        "source_water_depth_raster_available_for_this_pilot_verified": False,
        "water_depth_units_or_pixels_verified": False,
        "insured_property_ids_or_loss_estimated": False,
        "cat_model_input_approved": False,
        "raw_source_feature_geometry_or_properties_persisted": False,
    }


def probe(*, opener=_opener,
          clock=lambda: datetime.now(timezone.utc)) -> dict:
    control = _fetch(CONTROL_URL, opener)
    filtered = _fetch(FILTER_URL, opener)
    try:
        outcome = evaluate(control, filtered)
    except (CoverageBlocked, ImportError) as exc:
        print(json.dumps({
            "profile": PROFILE,
            "status": "BLOCKED_UNVERIFIED_SECOND_PILOT_SOURCE_FILTER",
            "block_reason": str(exc),
            "original_control_sha256": sha256(control).hexdigest(),
            "original_filtered_sha256": sha256(filtered).hexdigest(),
            "original_control_bytes": len(control),
            "original_filtered_bytes": len(filtered),
            "raw_source_geometry_persisted": False,
            "cat_model_input_approved": False,
        }, sort_keys=True), file=sys.stderr)
        raise
    stamp = clock()
    if not isinstance(stamp, datetime) or stamp.utcoffset() is None:
        raise CoverageBlocked("original source timestamp requires UTC offset")
    return {
        **outcome,
        "source_request_count": 2,
        "original_control_response_sha256": sha256(control).hexdigest(),
        "original_fes_response_sha256": sha256(filtered).hexdigest(),
        "original_control_response_bytes": len(control),
        "original_fes_response_bytes": len(filtered),
        "observed_utc": stamp.astimezone(timezone.utc).isoformat(),
        "source_script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", action="store_true")
    args = p.parse_args(argv)
    if not args.live:
        p.error("explicit --live required for two fixed reviewed official WFS requests")
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
    except (CoverageBlocked, ImportError, ValueError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
