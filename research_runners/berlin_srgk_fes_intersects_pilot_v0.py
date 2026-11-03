#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original Berlin WFS FES 2.0 Intersects countercheck for frozen BLD4 pilot.

Use a fixed public EPSG:25833 bbox envelope and the exact original source
schema-approved 'geom' field. No dynamic URLs, geometries, IDs, model-depth
values, insurer exposures, CAT losses or original source bytes persisted.
A positive *verified polygon intersection* only proves sampled model-area
coverage, NOT source flood raster/depth availability or risk.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import math
import ssl
import sys
from urllib import error, parse, request

from research_runners.berlin_srgk_model_area_pilot_coverage_v0 import (
    ALLOWED_CRS, BBOX, LAYER, SOURCE_SRS, CoverageBlocked, parse_features,
)
from research_runners.berlin_srgk_wfs_schema_hits_v0 import (
    BASE, SCHEMA_URL, inspect_schema,
)

# Original provider 2026-11-01 XSD SHA observed via independently
# reviewed metadata-only main run #41355919644.
SCHEMA_SHA256 = "8112bf8db14b7f3f1cb516717e128e0a450b643e645c29b1955e6c69bd57b87f"
SCHEMA_MAX_BYTES = 512 * 1024
FEATURE_MAX_BYTES = 786_432
FILTER = (
    '<fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0" '
    'xmlns:gml="http://www.opengis.net/gml/3.2">'
    '<fes:Intersects><fes:ValueReference>geom</fes:ValueReference>'
    '<gml:Envelope srsName="EPSG:25833">'
    '<gml:lowerCorner>391700 5819950</gml:lowerCorner>'
    '<gml:upperCorner>391900 5820150</gml:upperCorner>'
    '</gml:Envelope></fes:Intersects></fes:Filter>'
)
PARAMS = (
    ("service", "WFS"),
    ("version", "2.0.0"),
    ("request", "GetFeature"),
    ("typeNames", LAYER),
    ("count", "1"),
    ("srsName", SOURCE_SRS),
    ("outputFormat", "application/json"),
    ("filter", FILTER),
)
FEATURE_URL = BASE + "?" + parse.urlencode(PARAMS)
PROFILE = "berlin-srgk-fixed-pilot-fes-intersects-original-v0"


class FesBlocked(ValueError):
    """Original service response cannot establish reviewed source intersection."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise FesBlocked("original WFS redirected")


def _opener(req):
    return request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context())
    ).open(req, timeout=35)


def _fetch(url, *, opener=_opener):
    if url not in (SCHEMA_URL, FEATURE_URL):
        raise FesBlocked("WFS URL not explicitly approved")
    max_bytes = SCHEMA_MAX_BYTES if url == SCHEMA_URL else FEATURE_MAX_BYTES
    req = request.Request(url, method="GET", headers={
        "Accept": "application/xml,application/json", "Accept-Encoding": "identity"})
    try:
        with opener(req) as resp:
            if resp.status != 200 or resp.geturl() != url:
                raise FesBlocked("unreviewed WFS status or redirect")
            if resp.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise FesBlocked("unreviewed source content encoding")
            kind = resp.headers.get("Content-Type", "").split(";", 1)[0].lower().strip()
            expected = (("text/xml", "application/xml", "application/xsd+xml")
                        if url == SCHEMA_URL else
                        ("application/json", "application/geo+json",
                         "application/vnd.geo+json"))
            if kind not in expected:
                raise FesBlocked("WFS source media type mismatch")
            length = resp.headers.get("Content-Length")
            if length is not None and (not length.isdecimal()
                                      or int(length) > max_bytes):
                raise FesBlocked("WFS response Content-Length exceeds bound")
            body = resp.read(max_bytes+1)
            if not body or len(body) > max_bytes or (
                length is not None and len(body) != int(length)
            ):
                raise FesBlocked("empty/incomplete/oversized WFS source response")
            return body
    except (error.URLError, OSError, TimeoutError) as exc:
        raise FesBlocked("original Berlin WFS unavailable") from exc


def validate_original_schema(raw: bytes):
    if sha256(raw).hexdigest() != SCHEMA_SHA256:
        raise FesBlocked("original Berlin model-area geometry schema SHA changed")
    try:
        described = inspect_schema(raw)
    except ValueError as exc:
        raise FesBlocked("original source schema could not be verified") from exc
    if described["geometry_property_name_candidates"] != ["geom"]:
        raise FesBlocked("single official 'geom' source property not established")
    return described


def assess_feature(raw: bytes) -> dict:
    """Reject geometry outside fixed pilot; report intersection area only."""
    from shapely.geometry import box

    try:
        parsed = parse_features(raw, require_one=False)
    except (ValueError, ImportError) as exc:
        raise FesBlocked("FES original source feature/CRS/geometry unverified") from exc
    if not parsed["feature_count"]:
        # This *cannot* prove absence of model area: original WFS BBOX was
        # observed to return an unrelated source polygon in a prior run.
        return {
            "model_area_result": "EMPTY_FES_RESPONSE_COVERAGE_UNRESOLVED",
            "source_pilot_model_intersection_m2": None,
            "returned_features": 0,
            "any_noncoverage_or_dryness_proven": False,
            "hazard_depth_or_insurer_loss_admitted": False,
        }
    original_polygon = parsed["geometry"]
    pilot = box(*BBOX)
    clipped = original_polygon.intersection(pilot)
    if clipped.is_empty or clipped.area <= 0 or not math.isfinite(clipped.area):
        raise FesBlocked("FES selected polygon does not intersect fixed BLD4 pilot")
    if not clipped.is_valid or clipped.area > 40_000.00001:
        raise FesBlocked("unreviewed polygon intersection or area")
    return {
        "model_area_result": "EXACT_SAMPLED_MODEL_AREA_INTERSECTION_PROVEN",
        "source_pilot_model_intersection_m2": round(float(clipped.area), 3),
        "returned_features": 1,
        "any_noncoverage_or_dryness_proven": False,
        "hazard_depth_or_insurer_loss_admitted": False,
    }


def probe(*, opener=_opener, clock=lambda: datetime.now(timezone.utc)):
    schema = _fetch(SCHEMA_URL, opener=opener)
    checked = validate_original_schema(schema)
    original = _fetch(FEATURE_URL, opener=opener)
    finding = assess_feature(original)
    date = clock()
    if not isinstance(date, datetime) or date.utcoffset() is None:
        raise FesBlocked("original evidence timestamp is not timezone aware")
    return {
        "profile": PROFILE,
        "original_source": BASE,
        "original_feature_type": LAYER,
        "original_geometry_field": "geom",
        "source_model_area_schema_full_sha256": SCHEMA_SHA256,
        "actual_source_filtered_geojson_full_sha256": sha256(original).hexdigest(),
        "actual_source_filtered_geojson_response_bytes": len(original),
        "retrieved_utc": date.astimezone(timezone.utc).isoformat(),
        **finding,
        "one_fixed_schema_then_one_fixed_fes_request": True,
        "original_feature_ids_geometries_or_attributes_exported": False,
        "detail_pluvial_flood_raster_cells_verified": False,
        "original_BKG_KOSTRA_source_equivalence_proven": False,
        "annual_flood_event_model_or_CAT_loss_admitted": False,
    }


def main():
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
    except (FesBlocked, ValueError, OSError, ImportError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
