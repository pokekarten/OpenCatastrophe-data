#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fixed five-building official Berlin ALKIS WFS-to-CAT1/CAT2 research sample.

The official source is a mutable monthly-updated WFS. This is a bounded
independent geometry/provenance connectivity test, not a historical 2021
buildings snapshot, personal-address dataset, or insured-value estimator.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import ssl
import sys
from typing import Any, Callable
from urllib import parse, request, error

from research_runners.geoboundaries_deu_adm1_nuts2021_crosswalk_v0 import (
    resolve_nuts1_for_point,
)

ROOT = "https://gdi.berlin.de/services/wfs/alkis_gebaeude"
LAYER = "alkis_gebaeude:gebaeude"
SOURCE_SRS = "EPSG:25833"
# A deliberately small immutable site around central Berlin. All WFS
# parameters are constructed by code; no arbitrary user bbox, service, query,
# COUNT, outputFormat, feature type or further source reads permitted.
BBOX = (391700, 5819950, 391900, 5820150)
MAX_COUNT = 5
MAX_BYTES = 524_288
TIMEOUT = 35
PROFILE = "oc-berlin-alkis-fixed-bbox-five-buildings-de3-v0"
PARAMS = [
    ("service", "WFS"),
    ("version", "2.0.0"),
    ("request", "GetFeature"),
    ("typeNames", LAYER),
    ("count", str(MAX_COUNT)),
    ("srsName", SOURCE_SRS),
    ("bbox", ",".join(map(str, BBOX)) + "," + SOURCE_SRS),
    ("outputFormat", "application/json"),
]
URL = ROOT + "?" + parse.urlencode(PARAMS)
ALLOWED_CRS = {
    "EPSG:25833", "urn:ogc:def:crs:EPSG::25833",
    "urn:ogc:def:crs:EPSG:6.9:25833",
}


class BerlinBuildingSampleError(ValueError):
    """Source features, bytes, geometry or CAT regional linkage not verified."""


def _reject_constant(_value: str):
    raise BerlinBuildingSampleError("nonfinite original building GeoJSON number")


def _object(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise BerlinBuildingSampleError("duplicate feature JSON object property")
        result[key] = value
    return result


def inspect_building_geojson(raw: bytes) -> tuple[dict, list[tuple[float, float]]]:
    """Return aggregate-only data and *private in-memory* representative points."""
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise BerlinBuildingSampleError("no data or oversized building response")
    try:
        doc = json.loads(raw.decode("utf-8"), object_pairs_hook=_object,
                         parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BerlinBuildingSampleError("provider did not send valid UTF-8 GeoJSON") from exc
    if type(doc) is not dict or doc.get("type") != "FeatureCollection":
        raise BerlinBuildingSampleError("not a bounded GeoJSON FeatureCollection")
    crs = doc.get("crs")
    crs_name = None
    if crs is not None:
        if type(crs) is not dict or crs.get("type") != "name" or type(crs.get("properties")) is not dict:
            raise BerlinBuildingSampleError("unreviewed source CRS metadata")
        crs_name = crs["properties"].get("name")
        if crs_name not in ALLOWED_CRS:
            raise BerlinBuildingSampleError("building GeoJSON is not projected EPSG:25833")
    features = doc.get("features")
    if type(features) is not list or not 1 <= len(features) <= MAX_COUNT:
        raise BerlinBuildingSampleError("sample must contain 1 to 5 real building features")
    returned = doc.get("numberReturned")
    if returned is not None and (type(returned) is not int or returned != len(features)):
        raise BerlinBuildingSampleError("WFS numberReturned differs from feature count")
    try:
        from shapely.geometry import shape, box
        from pyproj import Transformer
    except ImportError as exc:
        raise BerlinBuildingSampleError("reviewed projected-spatial dependencies missing") from exc
    query_box = box(*BBOX)
    to_geographic = Transformer.from_crs("EPSG:25833", "EPSG:4326",
                                         always_xy=True, allow_ballpark=False,
                                         only_best=True)
    points = []
    total_polygon_area = 0.0
    for feature in features:
        if type(feature) is not dict or feature.get("type") != "Feature":
            raise BerlinBuildingSampleError("invalid source feature envelope")
        if type(feature.get("properties")) is not dict:
            raise BerlinBuildingSampleError("source properties missing")
        geometry = feature.get("geometry")
        if type(geometry) is not dict or geometry.get("type") not in ("Polygon", "MultiPolygon"):
            raise BerlinBuildingSampleError("source did not return a polygonal building")
        try:
            geom = shape(geometry)
        except (TypeError, ValueError, IndexError) as exc:
            raise BerlinBuildingSampleError("invalid source feature polygon") from exc
        if geom.is_empty or not geom.is_valid or not 0 < geom.area < 1_000_000:
            raise BerlinBuildingSampleError("invalid, zero or improbable building footprint area")
        if not geom.intersects(query_box):
            raise BerlinBuildingSampleError("building feature is unrelated to exact source query box")
        if not all(math.isfinite(v) for v in geom.bounds):
            raise BerlinBuildingSampleError("non-finite building coordinates")
        x, y = geom.representative_point().coords[0]
        if not (300_000 < x < 500_000 and 5_700_000 < y < 5_950_000):
            raise BerlinBuildingSampleError("source coordinate axis/CRS mismatch")
        lon, lat = to_geographic.transform(x, y)
        if not (13.0 < lon < 13.8 and 52.2 < lat < 52.8):
            raise BerlinBuildingSampleError("not a Berlin building in WGS84")
        points.append((lon, lat))
        total_polygon_area += float(geom.area)
    return ({
        "sampled_feature_count": len(points),
        "all_feature_geometries_valid": True,
        "source_feature_geometry_type": "Polygon or MultiPolygon",
        "source_crs_requested": SOURCE_SRS,
        "source_crs_explicitly_declared_in_response": crs_name is not None,
        "total_sample_polygon_area_m2_rounded": round(total_polygon_area, 1),
        "sample_size_not_total_buildings_in_box": True,
        "individual_original_feature_ids_logged": False,
        "individual_original_coordinates_logged": False,
        "provider_feature_bytes_persisted": False,
        "individual_building_address_data_exported": False,
    }, points)


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise BerlinBuildingSampleError("fixed provider request redirected")


def _get(req: request.Request, timeout: int):
    opener = request.build_opener(request.ProxyHandler({}),
                                  NoRedirect(),
                                  request.HTTPSHandler(context=ssl.create_default_context()))
    return opener.open(req, timeout=timeout)


def probe(
    *, opener: Callable[[request.Request, int], Any] = _get,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    cat1: Path | None = None,
    cat2: Path | None = None,
) -> dict:
    req = request.Request(URL, method="GET",
                          headers={"Accept": "application/json"})
    try:
        with opener(req, TIMEOUT) as resp:
            if resp.status != 200 or resp.geturl() != URL:
                raise BerlinBuildingSampleError("unexpected status or redirected WFS source")
            media = resp.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media not in ("application/json", "application/geo+json"):
                raise BerlinBuildingSampleError("WFS did not return requested GeoJSON media type")
            raw = resp.read(MAX_BYTES + 1)
    except BerlinBuildingSampleError:
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        raise BerlinBuildingSampleError("original Berlin building request failed") from exc
    checked = clock()
    if checked.utcoffset() is None:
        raise BerlinBuildingSampleError("receipt clock must be offset-aware")
    stats, points = inspect_building_geojson(raw)

    joined = None
    if cat1 is not None or cat2 is not None:
        if cat1 is None or cat2 is None:
            raise BerlinBuildingSampleError("both pinned CAT1 and CAT2 databases required")
        counts = Counter()
        for lon, lat in points:
            hit = resolve_nuts1_for_point(cat1, cat2, lon, lat)
            if hit is None or hit["nuts1_code"] != "DE3" or hit["nuts_version"] != 2021 or hit["nuts_cartographic_scale"] != "10M":
                raise BerlinBuildingSampleError("real building cannot be assigned to the verified Berlin DE3 2021 crosswalk")
            counts[hit["nuts1_code"]] += 1
        joined = dict(counts)

    return {
        "profile": PROFILE,
        "publisher": "Senatsverwaltung für Stadtentwicklung, Bauen und Wohnen Berlin",
        "data_rights_from_official_catalogue": "dl-de-zero-2.0",
        "source_feature_type": LAYER,
        "source_wfs_version": "2.0.0",
        "request_url": URL,
        "retrieved_at_utc": checked.astimezone(timezone.utc).isoformat(),
        "response_bytes": len(raw),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_monthly_mutable": True,
        "source_geometry_year_not_proven_to_be_2021": True,
        "geoboundaries_year_used_for_join": 2021 if joined is not None else None,
        "nuts2021_10m_join_region_counts": joined,
        "source_original_bytes_saved": False,
        "persistent_cat_db_updated": False,
        "building_assets_or_insured_values_inferred": False,
        "model_input_admitted": False,
        **stats,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", action="store_true")
    p.add_argument("--cat1", type=Path, required=True)
    p.add_argument("--cat2", type=Path, required=True)
    args = p.parse_args(argv)
    if not args.live:
        p.error("one live fixed source request must be explicitly selected")
    try:
        print(json.dumps(probe(cat1=args.cat1, cat2=args.cat2),
                         indent=2, sort_keys=True, allow_nan=False))
    except (BerlinBuildingSampleError, ValueError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
