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
import os
import sqlite3
import tempfile
from pathlib import Path
import ssl
import sys
from typing import Any, Callable
from urllib import parse, request, error

from research_runners.geoboundaries_deu_adm1_nuts2021_crosswalk_v0 import (
    resolve_nuts1_for_point,
)
from research_runners.geoboundaries_deu_adm1_cat_sqlite_v0 import (
    _check_destination,
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
CAT4_APP_ID = 0x424C4434  # BLD4, separate from CAT1 / CAT2 / CAT3
CAT4_SCHEMA_VERSION = 1
CAT4_SCHEMA = "berlin_alkis_five_derived_footprints_cat4_staging_v0"
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
    # WFS GetFeature count is a feature *limit*, not a guarantee of distinct
    # physical buildings. Reject repeated source IDs and spatially identical
    # geometries before reporting the sampled building count or CAT join.
    # Five fixed features make topological equality checks safely bounded.
    feature_ids: set[str | int] = set()
    distinct_geometries = []
    total_polygon_area = 0.0
    for feature in features:
        if type(feature) is not dict or feature.get("type") != "Feature":
            raise BerlinBuildingSampleError("invalid source feature envelope")
        if type(feature.get("properties")) is not dict:
            raise BerlinBuildingSampleError("source properties missing")
        feature_id = feature.get("id")
        if feature_id is not None:
            if ((type(feature_id) is not str or not feature_id.strip())
                    and type(feature_id) is not int):
                raise BerlinBuildingSampleError("invalid WFS building feature ID")
            # A number 1 and a string "1" are distinct GeoJSON identities.
            identity = (type(feature_id).__name__, feature_id)
            if identity in feature_ids:
                raise BerlinBuildingSampleError("duplicate WFS building feature ID")
            feature_ids.add(identity)
        geometry = feature.get("geometry")
        if type(geometry) is not dict or geometry.get("type") not in ("Polygon", "MultiPolygon"):
            raise BerlinBuildingSampleError("source did not return a polygonal building")
        try:
            geom = shape(geometry)
        except (TypeError, ValueError, IndexError) as exc:
            raise BerlinBuildingSampleError("invalid source feature polygon") from exc
        if geom.is_empty or not geom.is_valid or not 0 < geom.area < 1_000_000:
            raise BerlinBuildingSampleError("invalid, zero or improbable building footprint area")
        if any(geom.equals(existing) for existing in distinct_geometries):
            raise BerlinBuildingSampleError("duplicate physical building footprint in WFS sample")
        distinct_geometries.append(geom)
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
        "sampled_distinct_polygon_count": len(distinct_geometries),
        "sampled_duplicate_ids_or_geometries_rejected": True,
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


def stage_derived_footprints(
    raw: bytes, region_codes: list[str], output: Path, *,
    receipt_utc: str,
) -> dict:
    """Create NEW local CAT4 file containing derived geometry, no private fields.

    Caller already passed exact WFS source validation and independently
    source-pinned CAT1/CAT2 point joins. Revalidate the exact same bytes here,
    never issue a second provider request. Only local polygon WKB/areas and
    verified administrative NUTS code are staged. No source feature IDs,
    names, addresses, tags, or monetary attributes survive into the DB.
    """
    stats, _ = inspect_building_geojson(raw)
    if len(region_codes) != stats["sampled_feature_count"] or any(
        code != "DE3" for code in region_codes
    ):
        raise BerlinBuildingSampleError("all sample polygons require independent DE3 attribution")
    target = _check_destination(output)
    from shapely.geometry import shape

    # Source body is bounded and validated; intentionally drop all properties,
    # addresses, and original feature identifiers at the parsing boundary.
    features = json.loads(raw.decode("utf-8"))["features"]
    fd, temp_name = tempfile.mkstemp(
        prefix=".berlin-alkis-cat4-", suffix=".sqlite", dir=target.parent,
    )
    os.close(fd)
    try:
        with closing(sqlite3.connect(temp_name)) as db:
            db.execute(f"PRAGMA application_id={CAT4_APP_ID}")
            db.execute(f"PRAGMA user_version={CAT4_SCHEMA_VERSION}")
            db.executescript("""
                CREATE TABLE provenance (
                    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                    schema_id TEXT NOT NULL,
                    source_service TEXT NOT NULL,
                    source_feature_type TEXT NOT NULL,
                    source_response_sha256 TEXT NOT NULL,
                    retrieved_at_utc TEXT NOT NULL,
                    source_rights TEXT NOT NULL,
                    building_vintage TEXT NOT NULL CHECK(building_vintage='current_mutable_unknown_feature_date'),
                    boundary_vintage INTEGER NOT NULL CHECK(boundary_vintage=2021),
                    region_source TEXT NOT NULL,
                    model_admitted INTEGER NOT NULL CHECK(model_admitted=0)
                );
                CREATE TABLE building_sample (
                    ordinal INTEGER PRIMARY KEY,
                    projected_epsg25833_geometry_wkb BLOB NOT NULL,
                    footprint_area_m2 REAL NOT NULL CHECK(footprint_area_m2>0),
                    nuts1_region TEXT NOT NULL CHECK(nuts1_region='DE3')
                );
            """)
            with db:
                db.execute(
                    "INSERT INTO provenance VALUES (1, ?, ?, ?, ?, ?, 'dl-de-zero-2.0', "
                    "'current_mutable_unknown_feature_date', 2021, "
                    "'geoBoundaries 2021 + Eurostat NUTS2021 10M independently verified', 0)",
                    (CAT4_SCHEMA, ROOT, LAYER, hashlib.sha256(raw).hexdigest(),
                     receipt_utc),
                )
                for idx, (feature, code) in enumerate(zip(features, region_codes), 1):
                    g = shape(feature["geometry"])
                    db.execute(
                        "INSERT INTO building_sample VALUES (?, ?, ?, ?)",
                        (idx, g.wkb, float(g.area), code),
                    )
            if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise BerlinBuildingSampleError("CAT4 integrity check failed")
            if db.execute("SELECT count(*) FROM building_sample").fetchone()[0] != len(features):
                raise BerlinBuildingSampleError("CAT4 building sample row count mismatch")
        # Atomic no-overwrite commit. A pre-existing user SQLite remains intact.
        os.link(temp_name, target)
    except (sqlite3.Error, OSError, ValueError) as exc:
        raise BerlinBuildingSampleError("bounded CAT4 geometry staging failed") from exc
    finally:
        Path(temp_name).unlink(missing_ok=True)
    return {
        "schema": CAT4_SCHEMA, "app_id": CAT4_APP_ID,
        "derived_geometry_local_staging_created": True,
        "geometry_rows": len(features),
        "all_rows_region": "DE3",
        "original_provider_properties_and_ids_saved": False,
        "source_original_response_bytes_saved": False,
        "model_input_admitted": False,
    }


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
    cat4_output: Path | None = None,
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
    joined_per_feature: list[str] = []
    if cat4_output is not None and (cat1 is None or cat2 is None):
        raise BerlinBuildingSampleError('CAT4 requires both source-pinned CAT1 and CAT2')
    if cat1 is not None or cat2 is not None:
        if cat1 is None or cat2 is None:
            raise BerlinBuildingSampleError("both pinned CAT1 and CAT2 databases required")
        counts = Counter()
        for lon, lat in points:
            hit = resolve_nuts1_for_point(cat1, cat2, lon, lat)
            if hit is None or hit["nuts1_code"] != "DE3" or hit["nuts_version"] != 2021 or hit["nuts_cartographic_scale"] != "10M":
                raise BerlinBuildingSampleError("real building cannot be assigned to the verified Berlin DE3 2021 crosswalk")
            counts[hit["nuts1_code"]] += 1
            joined_per_feature.append(hit["nuts1_code"])
        joined = dict(counts)

    derived_stage = None
    if cat4_output is not None:
        derived_stage = stage_derived_footprints(
            raw, joined_per_feature, cat4_output,
            receipt_utc=checked.astimezone(timezone.utc).isoformat(),
        )

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
        "cat4_derived_geometry_stage": derived_stage,
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
    p.add_argument("--cat4-output", type=Path, required=False,
                   help="new absolute *.cat.sqlite file, outside repository")
    args = p.parse_args(argv)
    if not args.live:
        p.error("one live fixed source request must be explicitly selected")
    try:
        print(json.dumps(probe(cat1=args.cat1, cat2=args.cat2,
                               cat4_output=args.cat4_output),
                         indent=2, sort_keys=True, allow_nan=False))
    except (BerlinBuildingSampleError, ValueError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
