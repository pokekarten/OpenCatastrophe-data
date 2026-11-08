# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fixed, bounded original NRW LoD2 CityJSON building sample: aggregate QA only.

The provider body is transient; output excludes original geometry, object IDs,
addresses, exact coordinates and source attributes. Not insurance CAT admission.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

SOURCE_ID = "de.nrw.geobasis-lod2-ogc-features.2026"
SAMPLE_URL = (
    "https://ogc-api.nrw.de/3dg/v1/collections/building/items?"
    "f=cityjson&limit=5&bbox=6.9500,50.9300,6.9520,50.9320"
)
BBOX = (6.9500, 50.9300, 6.9520, 50.9320)  # synthetic study AOI; not a policy location
CRS = "http://www.opengis.net/def/crs/OGC/0/CRS84h"
MAX_BYTES = 65536
MAX_ROOTS = 5
MAX_CITY_OBJECTS = 100
MAX_VERTICES = 30000
ROOF_FIELDS = ("roofType", "measuredHeight", "storeysAboveGround", "function")


class SampleError(ValueError):
    """Source shape, CRS, spatial-filter or boundedness gate failed."""


class _NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise SampleError("redirect rejected: exact source URL required")


def _strict_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, val in pairs:
        if key in out:
            raise SampleError("duplicate JSON key")
        out[key] = val
    return out


def _reject_nonfinite(value: str) -> None:
    raise SampleError("non-finite JSON numeric literal")


def _finite_number(value: Any) -> bool:
    return type(value) in (float, int) and math.isfinite(value)


def _iter_indices(value: Any):
    if type(value) is int:
        yield value
    elif isinstance(value, list):
        for child in value:
            yield from _iter_indices(child)
    else:
        raise SampleError("invalid CityJSON geometry boundary index type")


def _intersects(minx: float, miny: float, maxx: float, maxy: float) -> bool:
    west, south, east, north = BBOX
    return minx <= east and maxx >= west and miny <= north and maxy >= south


def assess(raw: bytes, *, media_type: str = "application/city+json") -> dict[str, Any]:
    """Validate a tiny original CityJSON sample and emit aggregate-only evidence."""
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_BYTES:
        raise SampleError("empty, non-bytes or oversized provider response")
    if media_type.split(";", 1)[0].strip().lower() != "application/city+json":
        raise SampleError("unexpected content type: require CityJSON")
    try:
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_pairs, parse_constant=_reject_nonfinite)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SampleError("invalid original UTF-8 CityJSON") from exc
    if not isinstance(payload, dict) or payload.get("type") != "CityJSON":
        raise SampleError("not a CityJSON document")
    if payload.get("version") != "1.1":
        raise SampleError("unexpected CityJSON version")
    meta = payload.get("metadata")
    if not isinstance(meta, dict) or meta.get("referenceSystem") != CRS:
        raise SampleError("unknown output CRS; never assume EPSG:5555 or WGS84")
    transform = payload.get("transform")
    if not isinstance(transform, dict):
        raise SampleError("CityJSON transform missing")
    scale, translate = transform.get("scale"), transform.get("translate")
    if not (isinstance(scale, list) and isinstance(translate, list)
            and len(scale) == len(translate) == 3
            and all(_finite_number(x) and x > 0 for x in scale)
            and all(_finite_number(x) for x in translate)):
        raise SampleError("invalid 3D coordinate transform")
    vertices = payload.get("vertices")
    if not isinstance(vertices, list) or not 0 < len(vertices) <= MAX_VERTICES:
        raise SampleError("invalid or unbounded vertex count")
    coordinates: list[tuple[float, float, float]] = []
    for v in vertices:
        if not (isinstance(v, list) and len(v) == 3 and all(type(x) is int for x in v)):
            raise SampleError("vertices must have quantized 3D integer coordinates")
        c = tuple(v[i] * scale[i] + translate[i] for i in range(3))
        if not all(math.isfinite(n) for n in c) or not (-180 <= c[0] <= 180 and -90 <= c[1] <= 90):
            raise SampleError("invalid transformed geographic coordinates")
        coordinates.append(c)
    objs = payload.get("CityObjects")
    if not isinstance(objs, dict) or not 0 < len(objs) <= MAX_CITY_OBJECTS:
        raise SampleError("invalid or excessive CityObjects")
    roots = {key: item for key, item in objs.items()
             if isinstance(item, dict) and item.get("type") == "Building"}
    parts = {key: item for key, item in objs.items()
             if isinstance(item, dict) and item.get("type") == "BuildingPart"}
    if not 0 < len(roots) <= MAX_ROOTS or len(roots) + len(parts) != len(objs):
        raise SampleError("unexpected city object types/count")
    for item in objs.values():
        if not isinstance(item, dict):
            raise SampleError("invalid city object")
    # The OGC bbox criterion means INTERSECTION, not full containment.
    # Use root and associated BuildingPart geometry, not unrelated global vertices.
    attached: dict[str, set[int]] = {key: set() for key in roots}
    geometry_kinds: Counter[str] = Counter()
    for key, item in objs.items():
        indices: set[int] = set()
        geom = item.get("geometry", [])
        if not isinstance(geom, list):
            raise SampleError("invalid geometry collection")
        for g in geom:
            if not isinstance(g, dict) or g.get("type") not in {"Solid", "MultiSolid", "MultiSurface"}:
                raise SampleError("unknown 3D geometry type")
            geometry_kinds[g["type"]] += 1
            indices.update(_iter_indices(g.get("boundaries")))
        if any(i < 0 or i >= len(vertices) for i in indices):
            raise SampleError("geometry references out-of-range vertex")
        if key in roots:
            attached[key].update(indices)
        else:
            parent_ids = item.get("parents")
            if not isinstance(parent_ids, list) or not parent_ids or not all(p in roots for p in parent_ids):
                raise SampleError("BuildingPart without declared Building parent")
            for parent in parent_ids:
                attached[parent].update(indices)
    if not geometry_kinds:
        raise SampleError("no source geometry")
    for indexes in attached.values():
        if not indexes:
            raise SampleError("building has no geometry or attached BuildingPart geometry")
        xs = [coordinates[i][0] for i in indexes]
        ys = [coordinates[i][1] for i in indexes]
        if not _intersects(min(xs), min(ys), max(xs), max(ys)):
            raise SampleError("a returned Building is outside the requested bbox")
    extent = meta.get("geographicalExtent")
    if not (isinstance(extent, list) and len(extent) == 6
            and all(_finite_number(v) for v in extent)
            and extent[0] <= extent[3] and extent[1] <= extent[4]
            and _intersects(extent[0], extent[1], extent[3], extent[4])):
        raise SampleError("invalid or out-of-AOI provider geographical extent")
    root_attributes = {}
    part_attributes = {}
    for field in ROOF_FIELDS:
        root_attributes[field] = sum(
            1 for o in roots.values()
            if isinstance(o.get("attributes"), dict)
            and o["attributes"].get(field) not in (None, "", [])
        )
        part_attributes[field] = sum(
            1 for o in parts.values()
            if isinstance(o.get("attributes"), dict)
            and o["attributes"].get(field) not in (None, "", [])
        )
    return {
        "profile": "oc-nrw-lod2-bounded-cityjson-sample-v0",
        "source_id": SOURCE_ID,
        "fixed_request_url": SAMPLE_URL,
        "crs": CRS,
        "content_type": "application/city+json",
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "source_bytes": len(raw),
        "buildings": len(roots),
        "building_parts": len(parts),
        "vertices": len(vertices),
        "geometry_types": dict(sorted(geometry_kinds.items())),
        "root_attribute_present": root_attributes,
        "part_attribute_present": part_attributes,
        "all_roots_intersect_request_bbox": True,
        "original_ids_or_addresses_emitted": False,
        "raw_geometry_emitted": False,
        "source_fitness_admitted": False,
        "insurer_locations_validated": False,
        "model_ready": False,
    }


def acquire() -> tuple[bytes, str]:
    request = Request(SAMPLE_URL, headers={
        "Accept": "application/city+json",
        "Accept-Encoding": "identity",
        "User-Agent": "OpenCatastrophe-source-bounded-qa/0",
    }, method="GET")
    try:
        with build_opener(_NoRedirects()).open(request, timeout=15) as response:
            if response.status != 200 or response.geturl() != SAMPLE_URL:
                raise SampleError("unexpected status/effective URL")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise SampleError("compressed sample rejected")
            reported = response.headers.get("Content-Length")
            if reported is not None:
                try:
                    size = int(reported)
                except ValueError as exc:
                    raise SampleError("invalid Content-Length") from exc
                if not 0 < size <= MAX_BYTES:
                    raise SampleError("Content-Length exceeds sample budget")
            return response.read(MAX_BYTES + 1), response.headers.get("Content-Type", "")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise SampleError(f"original sample HTTP failed: {type(exc).__name__}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--live", action="store_true", help="Single fixed five-building source GET")
    g.add_argument("--offline-json", type=Path, help="Synthetic local fixture; never use private data")
    args = parser.parse_args(argv)
    try:
        if args.live:
            raw, mime = acquire()
        else:
            if args.offline_json.stat().st_size > MAX_BYTES:
                raise SampleError("offline fixture exceeds maximum sample size")
            raw, mime = args.offline_json.read_bytes(), "application/city+json"
        receipt = assess(raw, media_type=mime)
        receipt["live_http_verified"] = bool(args.live)
        receipt["observed_utc"] = datetime.now(timezone.utc).isoformat()
    except (OSError, SampleError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
