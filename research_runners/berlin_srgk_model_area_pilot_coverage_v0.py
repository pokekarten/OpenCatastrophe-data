#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Berlin SRGK exact BLD4 pilot model-area coverage, never a flood-depth claim.

Read-only: at most two bounded official WFS GetFeature requests, one source
existence control and one 200-m frozen pilot. Original geometry stays memory
only; output is aggregate/decision metadata. PR tests use synthetic GeoJSON.
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
from typing import Callable
from urllib import error, parse, request

ROOT = "https://gdi.berlin.de/services/wfs/ua_srgk"
CATALOGUE = "https://daten.berlin.de/datensaetze/starkregengefahrenkarte-wfs-1aa4f1ef"
LAYER = "ua_srgk:a_modellgebiete"
SOURCE_SRS = "EPSG:25833"
BBOX = (391700, 5819950, 391900, 5820150)
TIMEOUT = 40
MAX_BYTES = 786_432
PROFILE = "berlin-srgk-model-area-fixed-bld4-bbox-wfs-v0"
ALLOWED_CRS = {"EPSG:25833", "urn:ogc:def:crs:EPSG::25833", "urn:ogc:def:crs:EPSG:6.9:25833"}
PARAMS = [
    ("service", "WFS"),
    ("version", "2.0.0"),
    ("request", "GetFeature"),
    ("typeNames", LAYER),
    ("count", "1"),
    ("srsName", SOURCE_SRS),
    ("outputFormat", "application/json"),
]
CONTROL_URL = ROOT + "?" + parse.urlencode(PARAMS)
PILOT_URL = ROOT + "?" + parse.urlencode(PARAMS + [
    ("bbox", ",".join(str(x) for x in BBOX) + "," + SOURCE_SRS)
])


class CoverageBlocked(ValueError):
    """Provider response is not a verified bounded scientific statement."""


def _reject_object_duplicates(pairs):
    item = {}
    for key, value in pairs:
        if key in item:
            raise CoverageBlocked("duplicate WFS GeoJSON property")
        item[key] = value
    return item


def _reject_constant(value):
    raise CoverageBlocked("nonfinite WFS JSON number")


def parse_features(raw: bytes, *, require_one: bool):
    """Read feature geometry in memory, then emit no source geometry to caller."""
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise CoverageBlocked("empty or oversized official model-area response")
    try:
        obj = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_object_duplicates,
                         parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CoverageBlocked("invalid original WFS GeoJSON") from exc
    if type(obj) is not dict or obj.get("type") != "FeatureCollection":
        raise CoverageBlocked("original response is not GeoJSON FeatureCollection")
    features = obj.get("features")
    if type(features) is not list or len(features) > 1:
        raise CoverageBlocked("WFS count=1 violated")
    if require_one and len(features) != 1:
        raise CoverageBlocked("positive-control WFS contains no source model area")
    returned = obj.get("numberReturned")
    if returned is not None and (type(returned) is not int or returned != len(features)):
        raise CoverageBlocked("provider WFS numberReturned contradicts features")
    matched = obj.get("numberMatched")
    if matched is not None and matched != "unknown":
        if type(matched) is int and matched >= 0:
            pass
        elif type(matched) is str and matched.isascii() and matched.isdecimal():
            matched = int(matched)
        else:
            raise CoverageBlocked("invalid WFS numberMatched")
        if matched < len(features) or (matched == 0 and features):
            raise CoverageBlocked("provider matched count contradicts features")
    if not features:
        # An empty BBOX response, even with a zero count, cannot independently
        # establish complete no-coverage without provider spatial truth.
        return {"feature_count": 0, "geometry": None, "crs_validated": False}
    crs = obj.get("crs")
    if type(crs) is not dict or crs.get("type") != "name" or type(crs.get("properties")) is not dict:
        raise CoverageBlocked("missing original polygon CRS declaration")
    if crs["properties"].get("name") not in ALLOWED_CRS:
        raise CoverageBlocked("model-area polygon is not EPSG:25833")
    feature = features[0]
    if type(feature) is not dict or feature.get("type") != "Feature":
        raise CoverageBlocked("unrecognized source feature")
    geometry = feature.get("geometry")
    if type(geometry) is not dict or geometry.get("type") not in ("Polygon", "MultiPolygon"):
        raise CoverageBlocked("model area not polygonal")
    try:
        from shapely.geometry import shape
        g = shape(geometry)
    except (ValueError, TypeError, IndexError, ImportError) as exc:
        raise CoverageBlocked("source model area has invalid geometry") from exc
    if (not g.is_valid or g.is_empty or not 0 < g.area < 10_000_000_000
            or not all(math.isfinite(c) for c in g.bounds)):
        raise CoverageBlocked("source model area invalid or unbounded")
    return {"feature_count": 1, "geometry": g, "crs_validated": True}


def classify(control_raw: bytes, pilot_raw: bytes) -> dict:
    from shapely.geometry import box

    control = parse_features(control_raw, require_one=True)
    pilot = parse_features(pilot_raw, require_one=False)
    area = None
    if pilot["feature_count"]:
        clipped = pilot["geometry"].intersection(box(*BBOX))
        if clipped.is_empty or clipped.area <= 0 or not math.isfinite(clipped.area):
            raise CoverageBlocked("returned BBOX feature has no positive pilot intersection")
        if clipped.area > 40_000.01:
            raise CoverageBlocked("source model area exceeds 200m pilot")
        area = round(clipped.area, 1)
        verdict = "PILOT_INTERSECTS_ONE_OFFICIAL_MODEL_AREA"
    else:
        verdict = "PILOT_COVERAGE_UNRESOLVED_EMPTY_SOURCE_RESPONSE"
    return {
        "profile": PROFILE,
        "official_source_layer": LAYER,
        "pilot_source_crs": SOURCE_SRS,
        "control_at_least_one_model_area_verified": True,
        "pilot_model_area_feature_returned": bool(pilot["feature_count"]),
        "pilot_positive_intersection_area_m2_rounded": area,
        "pilot_model_area_coverage_status": verdict,
        "pilot_200m_bbox_fixed_and_not_user_supplied": True,
        "source_model_coverage_is_not_water_depth_coverage": True,
        "complete_city_coverage_not_inferred_from_sample": True,
        "original_model_area_geometry_or_ids_persisted": False,
        "no_pilot_features_not_interpreted_as_proven_dry": True,
        "original_water_depth_values_or_flood_losses_retrieved": False,
        "real_cat_model_input_approved": False,
    }


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CoverageBlocked("exact official WFS redirected")


def _get(req: request.Request, timeout: int):
    return request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    ).open(req, timeout=timeout)


def _fetch(url: str, opener: Callable) -> bytes:
    if url not in (CONTROL_URL, PILOT_URL):
        raise CoverageBlocked("unapproved official source request")
    req = request.Request(url, method="GET", headers={"Accept": "application/json"})
    try:
        with opener(req, TIMEOUT) as resp:
            if resp.status != 200 or resp.geturl() != url:
                raise CoverageBlocked("WFS original source URL or status mismatch")
            media = resp.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media not in ("application/json", "application/geo+json", "application/vnd.geo+json"):
                raise CoverageBlocked("official WFS source returned unreviewed media type")
            return resp.read(MAX_BYTES + 1)
    except CoverageBlocked:
        raise
    except (error.URLError, TimeoutError, OSError) as exc:
        raise CoverageBlocked("official fixed WFS model-area source request failed") from exc


def probe(*, opener: Callable = _get,
          clock: Callable = lambda: datetime.now(timezone.utc)) -> dict:
    control = _fetch(CONTROL_URL, opener)
    pilot = _fetch(PILOT_URL, opener)
    outcome = classify(control, pilot)
    now = clock()
    if not isinstance(now, datetime) or now.utcoffset() is None:
        raise CoverageBlocked("receipt clock must have a timezone")
    return {
        "retrieved_utc": now.astimezone(timezone.utc).isoformat(),
        "published_catalogue": CATALOGUE,
        "catalogue_licence_label": "CC-BY-4.0",
        "source_control_full_response_sha256": sha256(control).hexdigest(),
        "source_pilot_full_response_sha256": sha256(pilot).hexdigest(),
        "source_control_bytes": len(control),
        "source_pilot_bytes": len(pilot),
        "source_script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "exact_fixed_source_requests": 2,
        "source_raw_xml_geojson_persisted": False,
        **outcome,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("explicit --live required to query two fixed official WFS endpoints")
    try:
        print(json.dumps(probe(), ensure_ascii=False, allow_nan=False, sort_keys=True))
    except (CoverageBlocked, ImportError, ValueError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
