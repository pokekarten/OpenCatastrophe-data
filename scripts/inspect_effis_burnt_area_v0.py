#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Metadata-only EFFIS observed burned-area REST/GeoJSON research preflight.

NO perimeter coordinates or provider rows are saved in the result. Source
is the live mutable EFFIS current endpoint; event ID alone does NOT provide
an immutable snapshot or model-admission evidence.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

BASE_URL = "https://api.effis.emergency.copernicus.eu/rest/2/burntareas/current/"
MAX_BYTES = 2_000_000
MAX_VERTICES = 200_000
MAX_POLYGONS = 1000


class EFFISSourceError(ValueError):
    """Missing or inconsistent source event geometry, identity or access."""


def retrieve_event(event_id: int) -> bytes:
    if type(event_id) is not int or not 1 <= event_id <= 999_999_999:
        raise EFFISSourceError("expected bounded positive event ID")
    url = BASE_URL + "?id=" + str(event_id)
    request = Request(url, headers={"Accept": "application/json",
                                   "User-Agent": "OpenCatastrophe-Research-EFFIS/1.0"})
    with urlopen(request, timeout=45) as response:
        target = urlsplit(response.geturl())
        if target.scheme != "https" or target.hostname != "api.effis.emergency.copernicus.eu":
            raise EFFISSourceError("untrusted API redirect")
        data = response.read(MAX_BYTES + 1)
    if not 0 < len(data) <= MAX_BYTES:
        raise EFFISSourceError("EFFIS JSON source has invalid or unbounded size")
    return data


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EFFISSourceError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _finite_point(point):
    if not isinstance(point, list) or len(point) < 2:
        raise EFFISSourceError("invalid geometry coordinate shape")
    lon, lat = point[:2]
    if type(lon) not in (float, int) or type(lat) not in (float, int):
        raise EFFISSourceError("invalid coordinate number")
    if not (math.isfinite(lon) and math.isfinite(lat) and -180 <= lon <= 180 and -90 <= lat <= 90):
        raise EFFISSourceError("out-of-range coordinate")
    return float(lon), float(lat)


def inspect_event_json(data: bytes, event_id: int) -> dict:
    if type(data) is not bytes or not 0 < len(data) <= MAX_BYTES:
        raise EFFISSourceError("invalid raw JSON bytes")
    try:
        payload = json.loads(data.decode("utf-8-sig"), object_pairs_hook=_strict_object,
                             parse_constant=lambda _: (_ for _ in ()).throw(EFFISSourceError("non-finite JSON")))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise EFFISSourceError("invalid UTF-8 JSON") from exc
    if not isinstance(payload, dict) or payload.get("count") != 1:
        raise EFFISSourceError("expected one uniquely filtered event")
    records = payload.get("results")
    if not isinstance(records, list) or len(records) != 1:
        raise EFFISSourceError("unexpected pagination or event count")
    event = records[0]
    if not isinstance(event, dict) or type(event.get("id")) is not int or event["id"] != event_id:
        raise EFFISSourceError("event ID does not match exact API query")
    country = event.get("country")
    if not isinstance(country, str) or len(country) != 2 or not country.isupper():
        raise EFFISSourceError("unsupported country identity")
    fired = event.get("firedate")
    try:
        occurred = datetime.fromisoformat(fired)
        if occurred.utcoffset() is None:
            raise EFFISSourceError("firedate timezone offset missing")
    except (ValueError, TypeError) as exc:
        raise EFFISSourceError("invalid firedate") from exc
    try:
        area = Decimal(str(event["area_ha"]))
    except (InvalidOperation, KeyError, TypeError) as exc:
        raise EFFISSourceError("invalid reported area_ha") from exc
    if not area.is_finite() or area <= 0:
        raise EFFISSourceError("reported burnt area must be positive")
    geom = event.get("shape")
    if not isinstance(geom, dict) or geom.get("type") != "MultiPolygon":
        raise EFFISSourceError("expected explicit GeoJSON MultiPolygon")
    polygons = geom.get("coordinates")
    if not isinstance(polygons, list) or not 0 < len(polygons) <= MAX_POLYGONS:
        raise EFFISSourceError("empty or excessive polygon collection")
    n_rings, n_vertices = 0, 0
    for polygon in polygons:
        if not isinstance(polygon, list) or not polygon:
            raise EFFISSourceError("polygon rings missing")
        for ring in polygon:
            if not isinstance(ring, list) or len(ring) < 4:
                raise EFFISSourceError("invalid polygon ring")
            first = _finite_point(ring[0])
            for point in ring:
                _finite_point(point)
                n_vertices += 1
                if n_vertices > MAX_VERTICES:
                    raise EFFISSourceError("geometries exceed research size budget")
            if _finite_point(ring[-1]) != first:
                raise EFFISSourceError("polygon ring is not closed")
            n_rings += 1
    centroid = event.get("centroid")
    if centroid is not None:
        if not isinstance(centroid, dict) or centroid.get("type") != "Point":
            raise EFFISSourceError("invalid reported centroid")
        _finite_point(centroid.get("coordinates"))
    bbox = event.get("bbox")
    if bbox is not None:
        if not isinstance(bbox, list) or len(bbox) != 4:
            raise EFFISSourceError("invalid bbox")
        xmin, ymin = _finite_point(bbox[:2])
        xmax, ymax = _finite_point(bbox[2:])
        if not xmin <= xmax or not ymin <= ymax:
            raise EFFISSourceError("inverted bbox")
    return {
        "source": "European Forest Fire Information System EFFIS REST v2/current",
        "source_url": BASE_URL + "?id=" + str(event_id),
        "source_bytes_sha256": hashlib.sha256(data).hexdigest(),
        "observation_stage": "burnt_area_not_building_loss",
        "event_id": event_id,
        "country_code": country,
        "event_firedate": occurred.isoformat(),
        "reported_area_ha": str(area),
        "polygon_count": len(polygons),
        "ring_count": n_rings,
        "vertex_count": n_vertices,
        "geometry_type": "MultiPolygon",
        "coordinate_order": "longitude_latitude",
        "result_includes_raw_geometry": False,
        "snapshot_immutable": False,
        "model_admission": False,
        "insured_loss_computed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-id", required=True, type=int)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fetch", action="store_true")
    mode.add_argument("--file", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    raw = retrieve_event(args.event_id) if args.fetch else args.file.read_bytes()
    report = inspect_event_json(raw, args.event_id)
    rendered = json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if args.out:
        if args.file and args.out.resolve() == args.file.resolve():
            raise EFFISSourceError("refusing to overwrite original source")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
