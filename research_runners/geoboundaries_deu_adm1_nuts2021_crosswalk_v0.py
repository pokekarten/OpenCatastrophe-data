#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exact-source, area-based geoBoundaries DEU ADM1 <-> Eurostat NUTS1 2021 audit.

NUTS geometries are simplified 1:20M statistical cartographic shapes, not
building-level address/parcel truth. Source matched by independent polygons,
never by names or an unsupported change of NUTS vintage. The SQLite crosswalk
is local research staging, not a production/insurance-data admission.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
from typing import Any

from research_runners.geoboundaries_deu_adm1_cat_sqlite_v0 import (
    ROOT, _check_destination, open_cat_index, lookup_admin1,
)
from research_runners.geoboundaries_deu_adm1_original_geojson_v0 import (
    BOUNDARY_ID, EXPECTED_FEATURES, SOURCE_LFS_OID_SHA256, SOURCE_LFS_SIZE,
    SOURCE_GIT_COMMIT, inspect_geojson_bytes,
)

EUROSTAT_COMMIT = "8186be451525164ea24b43560cb943fda7c5520c"
EUROSTAT_URL = (
    "https://raw.githubusercontent.com/eurostat/Nuts2json/"
    + EUROSTAT_COMMIT + "/pub/v2/2021/4326/20M/nutsrg_1.json"
)
EUROSTAT_SIZE = 194_955
EUROSTAT_SHA256 = "1cacacf29694f518f6446ec286b5f251f3fea109d84874eb317c50b7300419b1"
EUROSTAT_BLOB_SHA1 = "0d0ce3881456017f3013cc07fe350646b69f216d"
EUROSTAT_TOTAL_NUTS1 = 123
CROSSWALK_SCHEMA = "deu_adm1_2021_to_eurostat_nuts1_2021_simplified20M_v0"
CROSSWALK_APP_ID = 0x43415432  # CAT2, deliberately NOT the existing CAT1 spatial DB
EXPECTED_NUTS = frozenset(
    ["DE1", "DE2", "DE3", "DE4", "DE5", "DE6", "DE7", "DE8",
     "DE9", "DEA", "DEB", "DEC", "DED", "DEE", "DEF", "DEG"]
)
MIN_BIDIRECTIONAL_OVERLAP = 0.75
MAX_SOURCE_BYTES = 300_000


class CrosswalkError(ValueError):
    """Original digest, source-vintage, geometry or one-to-one proof failed."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise CrosswalkError("duplicate original JSON key")
        result[key] = value
    return result


def _invalid_constant(_: str):
    raise CrosswalkError("non-finite JSON constant")


def _parse_eurostat(
    raw: bytes, *, expected_sha256: str = EUROSTAT_SHA256,
    expected_size: int = EUROSTAT_SIZE,
) -> list[dict]:
    if type(raw) is not bytes or len(raw) != expected_size or len(raw) > MAX_SOURCE_BYTES:
        raise CrosswalkError("Eurostat exact original byte count mismatch")
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise CrosswalkError("Eurostat exact original SHA-256 mismatch")
    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_object,
                          parse_constant=_invalid_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CrosswalkError("not strict original Eurostat GeoJSON") from exc
    if type(data) is not dict or data.get("type") != "FeatureCollection":
        raise CrosswalkError("not Eurostat GeoJSON FeatureCollection")
    if "crs" in data and data["crs"] is not None:
        raise CrosswalkError("unexpected embedded CRS metadata")
    features = data.get("features")
    if type(features) is not list:
        raise CrosswalkError("missing original Eurostat features")
    if len(features) != EUROSTAT_TOTAL_NUTS1:
        raise CrosswalkError("unexpected original all-Europe NUTS1 feature count")
    german: dict[str, dict] = {}
    for feature in features:
        if type(feature) is not dict or feature.get("type") != "Feature":
            raise CrosswalkError("bad NUTS1 feature envelope")
        p = feature.get("properties")
        if type(p) is not dict:
            raise CrosswalkError("bad Eurostat NUTS1 properties")
        code = p.get("id")
        if type(code) is not str or not re.fullmatch(r"[A-Z0-9]{3,5}", code):
            raise CrosswalkError("unexpected Eurostat NUTS1 code")
        if code.startswith("DE"):
            if code not in EXPECTED_NUTS or code in german:
                raise CrosswalkError("unexpected or duplicate DE NUTS1 code")
            name = p.get("na")
            if type(name) is not str or not name.strip() or len(name) > 200:
                raise CrosswalkError("missing official NUTS region name")
            geo = feature.get("geometry")
            if type(geo) is not dict or geo.get("type") not in ("Polygon", "MultiPolygon"):
                raise CrosswalkError("invalid NUTS1 polygon kind")
            german[code] = geo
    if frozenset(german) != EXPECTED_NUTS:
        raise CrosswalkError("Germany NUTS1 has missing/extra official regions")
    return [dict(code=code, geometry=german[code]) for code in sorted(german)]


def audit_crosswalk(
    geo_raw: bytes, nuts_raw: bytes, *,
    geo_sha256: str = SOURCE_LFS_OID_SHA256,
    geo_size: int = SOURCE_LFS_SIZE,
    nuts_sha256: str = EUROSTAT_SHA256,
    nuts_size: int = EUROSTAT_SIZE,
    nuts_total: int = EUROSTAT_TOTAL_NUTS1,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Independent source projections; return local-only mapping and safe summary."""
    # The caller cannot pretend another NUTS dataset is the published real
    # vintage in the provenance: synthetic fixtures must still have 16 DE codes.
    inspect_geojson_bytes(geo_raw, expected_sha256=geo_sha256,
                          expected_size=geo_size)
    if nuts_total != EUROSTAT_TOTAL_NUTS1:
        raise CrosswalkError("only reviewed Eurostat all-region feature count permitted")
    nut_rows = _parse_eurostat(nuts_raw, expected_sha256=nuts_sha256,
                              expected_size=nuts_size)
    from shapely.geometry import shape
    from shapely.ops import transform
    from pyproj import Transformer

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True,
                                      allow_ballpark=False, only_best=True)

    raw_geo = json.loads(geo_raw.decode("utf-8"))["features"]
    shape_rows = []
    for feature in raw_geo:
        item = feature["properties"]
        sid = item["shapeID"]
        shape_rows.append((
            sid, transform(transformer.transform, shape(feature["geometry"]))
        ))
    target_rows = [
        (item["code"], transform(transformer.transform, shape(item["geometry"])))
        for item in nut_rows
    ]
    # A low-quality simplification or CRS issue cannot be silently accepted.
    if any(
        not p.is_valid or p.is_empty or not math.isfinite(p.area) or p.area <= 0
        for _, p in shape_rows + target_rows
    ):
        raise CrosswalkError("invalid or nonphysical projected source polygon")

    mapping = []
    for sid, geopol in shape_rows:
        intersections = []
        for code, nutspol in target_rows:
            area = float(geopol.intersection(nutspol).area)
            intersections.append((code, area, float(nutspol.area)))
        intersections.sort(key=lambda x: x[1], reverse=True)
        code, primary_area, target_area = intersections[0]
        runner_up = intersections[1][1]
        src_coverage = primary_area / float(geopol.area)
        ref_coverage = primary_area / target_area
        # One true polygon match must dominate every independent false
        # candidate, in both area directions. This is **not** a declaration
        # that the original boundaries are metrically equal.
        if (src_coverage < MIN_BIDIRECTIONAL_OVERLAP
            or ref_coverage < MIN_BIDIRECTIONAL_OVERLAP
            or runner_up >= primary_area * 0.10):
            raise CrosswalkError(
                "no unambiguous high-coverage NUTS1/ADM1 match; " +
                f"best_nuts1={code} geo_fraction={src_coverage:.6f} " +
                f"nuts_fraction={ref_coverage:.6f} " +
                f"runner_up_share_of_best={runner_up / primary_area if primary_area else 0.0:.6f}"
            )
        mapping.append({
            "shape_id": sid,
            "nuts1_code": code,
            "geo_area_3035_m2": float(geopol.area),
            "nuts_area_3035_m2": target_area,
            "intersection_area_3035_m2": primary_area,
            "geo_coverage_fraction": src_coverage,
            "nuts_coverage_fraction": ref_coverage,
        })
    codes = [x["nuts1_code"] for x in mapping]
    if len(mapping) != EXPECTED_FEATURES or set(codes) != EXPECTED_NUTS:
        raise CrosswalkError("non-bijective polygon crosswalk: duplicate/missing NUTS1 region")
    return mapping, {
        "profile": CROSSWALK_SCHEMA,
        "geo_boundaries_germany_source_sha256": geo_sha256,
        "eurostat_nuts2021_source_sha256": nuts_sha256,
        "source_region_count": len(mapping),
        "matched_distinct_nuts1_codes": len(set(codes)),
        "nuts_version": "2021",
        "nuts_cartographic_scale": "20M",
        "projected_area_crs": "EPSG:3035",
        "minimum_geo_polygon_coverage": round(min(x["geo_coverage_fraction"] for x in mapping), 6),
        "minimum_nuts_polygon_coverage": round(min(x["nuts_coverage_fraction"] for x in mapping), 6),
        "maximum_source_geometry_area_difference_is_not_zero": any(
            abs(x["geo_area_3035_m2"] - x["nuts_area_3035_m2"]) > 1.0
            for x in mapping
        ),
        "original_nuts_codes": sorted(set(codes)),
        "simplified_geography_not_building_accuracy": True,
        "crosswalk_is_observed_area_overlap_not_legal_region_equivalence": True,
        "nuts2016_eubucco_modified_geography_not_covered": True,
        "insurer_exposure_or_real_building_rows_imported": False,
    }


def build_crosswalk_staging(
    mapping: list[dict], receipt: dict, output: Path,
) -> None:
    target = _check_destination(output)
    fd, filename = tempfile.mkstemp(prefix=".cat-nuts-crosswalk-",
                                    suffix=".sqlite", dir=target.parent)
    os.close(fd)
    try:
        with closing(sqlite3.connect(filename)) as conn:
            conn.execute(f"PRAGMA application_id={CROSSWALK_APP_ID}")
            conn.execute("PRAGMA user_version=1")
            conn.executescript("""
                CREATE TABLE provenance (
                    schema_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    source_sha256 TEXT NOT NULL,
                    nuts_source_id TEXT NOT NULL,
                    nuts_sha256 TEXT NOT NULL,
                    nuts_version INTEGER NOT NULL CHECK(nuts_version=2021),
                    geographic_scale TEXT NOT NULL,
                    model_input_approved INTEGER NOT NULL CHECK(model_input_approved=0)
                );
                CREATE TABLE region_mapping (
                    shape_id TEXT PRIMARY KEY,
                    nuts1_code TEXT NOT NULL UNIQUE,
                    geo_overlap_fraction REAL NOT NULL,
                    nuts_overlap_fraction REAL NOT NULL
                );
            """)
            with conn:
                conn.execute("INSERT INTO provenance VALUES (?, ?, ?, ?, ?, 2021, '20M', 0)",
                    (CROSSWALK_SCHEMA, BOUNDARY_ID,
                     receipt["geo_boundaries_germany_source_sha256"],
                     EUROSTAT_COMMIT, receipt["eurostat_nuts2021_source_sha256"]))
                for row in mapping:
                    conn.execute("INSERT INTO region_mapping VALUES (?, ?, ?, ?)",
                        (row["shape_id"], row["nuts1_code"],
                         row["geo_coverage_fraction"], row["nuts_coverage_fraction"]))
            if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise CrosswalkError("SQLite crosswalk integrity failure")
            if conn.execute("SELECT count(*) FROM region_mapping").fetchone()[0] != 16:
                raise CrosswalkError("crosswalk SQLite count mismatch")
        os.link(filename, target)  # do not overwrite even during concurrent run
    except (OSError, sqlite3.Error) as exc:
        raise CrosswalkError("isolated CAT crosswalk SQLite build failed") from exc
    finally:
        Path(filename).unlink(missing_ok=True)


def resolve_nuts1_for_point(cat_geo_db: Path, crosswalk_db: Path,
                            lon: float, lat: float) -> dict | None:
    """Fail closed on foreign/unknown CAT DB, missing mapping, duplicate boundary."""
    from urllib.parse import quote
    with closing(open_cat_index(cat_geo_db)) as geo:
        hit = lookup_admin1(geo, lon, lat)
    if hit is None:
        return None
    uri = "file:" + quote(str(crosswalk_db.resolve()), safe="/") + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as conn:
        if (
            conn.execute("PRAGMA application_id").fetchone()[0] != CROSSWALK_APP_ID
            or conn.execute("PRAGMA user_version").fetchone()[0] != 1
        ):
            raise CrosswalkError("foreign CAT crosswalk database")
        stored = conn.execute(
            "SELECT source_sha256, nuts_sha256, nuts_version FROM provenance"
        ).fetchone()
        if stored != (SOURCE_LFS_OID_SHA256, EUROSTAT_SHA256, 2021):
            raise CrosswalkError("unapproved source digest/vintage in crosswalk")
        row = conn.execute(
            "SELECT nuts1_code, geo_overlap_fraction, nuts_overlap_fraction "
            "FROM region_mapping WHERE shape_id=?", (hit["shape_id"],)
        ).fetchone()
    if row is None:
        raise CrosswalkError("point matched ADM1 but crosswalk row missing")
    return {
        "nuts1_code": row[0], "nuts_version": 2021,
        "geoboundaries_shape_id": hit["shape_id"],
        "geoboundaries_year_represented": hit["source_year"],
        "geo_overlap_fraction": row[1],
        "nuts_overlap_fraction": row[2],
        "official_nuts2016_eubucco_relation_verified": False,
        "insured_value_inferred": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geo-original", type=Path, required=True)
    parser.add_argument("--nuts2021-original", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True,
                        help="fresh absolute *.cat.sqlite file outside repo")
    args = parser.parse_args(argv)
    try:
        if (not args.geo_original.is_file() or args.geo_original.is_symlink()
            or args.geo_original.stat().st_size != SOURCE_LFS_SIZE
            or not args.nuts2021_original.is_file()
            or args.nuts2021_original.is_symlink()
            or args.nuts2021_original.stat().st_size != EUROSTAT_SIZE):
            raise CrosswalkError("exact original files required, no Git LFS pointer")
        geo = args.geo_original.read_bytes()
        nuts = args.nuts2021_original.read_bytes()
        mapping, receipt = audit_crosswalk(geo, nuts)
        build_crosswalk_staging(mapping, receipt, args.output)
        print(json.dumps({**receipt, "cat_crosswalk_sqlite_created": True,
                          "original_source_bytes_committed": False,
                          "production_db_modified": False}, indent=2, sort_keys=True))
        return 0
    except (CrosswalkError, ValueError, OSError, sqlite3.Error) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
