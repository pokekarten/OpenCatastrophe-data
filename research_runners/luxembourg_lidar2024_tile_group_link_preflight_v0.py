#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Pinned Luxembourg LiDAR2024 original index: tile-group URLs and HEAD preflight.

Fixed public-city 250m research window; source rows are private to the process.
No LAZ downloads, original tile URLs/names, geometries or identities exported.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
import sqlite3
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

from research_runners.luxembourg_lidar2024_fixed_tile_candidates_v0 import (
    SOURCE_SHA256, HALF_WIDTH_M, DEFAULT_LON, DEFAULT_LAT, MAX_TILE_CANDIDATES,
    select_original_tiles, LidarTileSelectionError,
)

CATALOGUE_RESOURCE = re.compile(r"^/(?:en|fr|de)/datasets/r/[0-9a-fA-F-]{36}/?$")
DIRECT_ZIP = re.compile(
    r"^/resources/bd-l-lidar2024-releve-3d-du-territoire-luxembourgeois/"
    r"[0-9]{8}-[0-9]{6}/lidar2024-c[0-9]{3}-r[0-9]{3}\.zip$",
    flags=re.IGNORECASE,
)


class LidarLinkError(ValueError):
    """No provider-host-safe tile-group link or invalid source receipt."""


def classify_link(value: str) -> str:
    """Only fixed provider HTTPS resource URLs can be queried (HEAD only)."""
    if not isinstance(value, str) or len(value) > 2048 or not value:
        return "missing_or_invalid"
    try:
        p = urlsplit(value)
        if (p.scheme != "https" or p.username is not None or p.password is not None
                or p.port not in (None, 443) or p.query or p.fragment
                or "\\" in p.path or "%" in p.path):
            return "not_allowlisted"
        host = p.hostname
    except ValueError:
        return "not_allowlisted"
    if host == "data.public.lu" and CATALOGUE_RESOURCE.fullmatch(p.path):
        return "provider_catalogue_resource"
    if host == "download.data.public.lu" and DIRECT_ZIP.fullmatch(p.path):
        return "provider_direct_tile_group_zip"
    return "not_allowlisted"


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def head_source(url: str, *, timeout: int = 12) -> dict:
    if classify_link(url) not in (
        "provider_catalogue_resource", "provider_direct_tile_group_zip"
    ):
        raise LidarLinkError("Refuse unallowlisted original tile-group endpoint")
    req = Request(url, method="HEAD", headers={"User-Agent": "OpenCatastrophe-data-source-research/0"})
    opener = build_opener(_NoRedirect())
    try:
        with opener.open(req, timeout=timeout) as response:
            status = response.status
            headers = response.headers
    except HTTPError as exc:
        status, headers = exc.code, exc.headers
    except (URLError, TimeoutError, OSError) as exc:
        return {"head_request_reachable": False, "http_status": None,
                "declared_content_length_bytes": None, "destination_host_class": None}
    length = headers.get("Content-Length")
    try:
        nbytes = int(length) if length is not None and length.isdecimal() else None
    except (TypeError, ValueError):
        nbytes = None
    if nbytes is not None and nbytes < 0:
        nbytes = None
    target = headers.get("Location")
    redirect_class = classify_link(target) if target else None
    # URLs, queries, host paths and response-body bytes are never emitted.
    return {
        "head_request_reachable": True,
        "http_status": status,
        "declared_content_length_bytes": nbytes,
        "destination_host_class": redirect_class,
        "potential_future_download_below_100_mib": (
            nbytes is not None and 0 < nbytes <= 100 * 1024 * 1024 and
            status == 200
        ),
    }


def inspect(file: Path, *, probe_head: bool = False) -> dict:
    base = select_original_tiles(file)
    try:
        from pyproj import Transformer
        to3035 = Transformer.from_crs(4326, 3035, always_xy=True)
        to2169 = Transformer.from_crs(3035, 2169, always_xy=True)
        cx, cy = to3035.transform(DEFAULT_LON, DEFAULT_LAT)
        points = [to2169.transform(x, y) for x,y in (
            (cx-HALF_WIDTH_M,cy-HALF_WIDTH_M),
            (cx+HALF_WIDTH_M,cy-HALF_WIDTH_M),
            (cx+HALF_WIDTH_M,cy+HALF_WIDTH_M),
            (cx-HALF_WIDTH_M,cy+HALF_WIDTH_M))]
        coords = [p for row in points for p in row]
        if not all(math.isfinite(x) for x in coords):
            raise LidarLinkError("invalid fixed spatial coordinates")
        xlo,xhi = min(x for x,_ in points),max(x for x,_ in points)
        ylo,yhi = min(y for _,y in points),max(y for _,y in points)
        with sqlite3.connect(Path(file).resolve().as_uri()+"?mode=ro&immutable=1",uri=True) as db:
            db.execute("PRAGMA query_only=ON")
            rows = db.execute(
                'SELECT t."Fichier",t."Dossier",t."DownloadLink" '
                'FROM "TableauAssemblage" t JOIN "rtree_TableauAssemblage_geom" r '
                'ON t."fid"=r.id WHERE r.maxx>=? AND r.minx<=? '
                'AND r.maxy>=? AND r.miny<=? ORDER BY t."fid" LIMIT ?',
                (xlo,xhi,ylo,yhi,MAX_TILE_CANDIDATES+1),
            ).fetchall()
    except (sqlite3.DatabaseError, LidarTileSelectionError, ImportError) as exc:
        raise LidarLinkError("Unable to inspect the validated original tile candidates") from exc
    if len(rows) != base["rtree_bbox_candidate_tiles"]:
        raise LidarLinkError("Original index candidate count drift")
    url_class_counts = Counter()
    missing = Counter()
    url_set = set()
    for file_name, folder, url in rows:
        if not isinstance(file_name, str) or not file_name.strip():
            missing["Fichier"] += 1
        if not isinstance(folder, str) or not folder.strip():
            missing["Dossier"] += 1
        kind = classify_link(url)
        url_class_counts[kind] += 1
        if kind in ("provider_catalogue_resource", "provider_direct_tile_group_zip"):
            url_set.add(url)
        else:
            raise LidarLinkError("Original index includes unallowlisted tile DownloadLink")
    # The fixed provider-index group URLs are checked in memory, not output.
    checks = [head_source(url) for url in sorted(url_set)] if probe_head else []
    return {
        "profile": "lu-lidar2024-tile-group-link-preflight-v0",
        "source_index_sha256": SOURCE_SHA256,
        "fixed_research_window_side_metres": 250,
        "rtree_candidate_tile_rows": len(rows),
        "provider_resource_link_type_counts": dict(sorted(url_class_counts.items())),
        "source_metadata_field_missing_counts": dict(sorted(missing.items())),
        "distinct_allowlisted_group_urls": len(url_set),
        "one_link_can_serve_multiple_tiles": len(url_set) < len(rows),
        "head_probe_per_group_without_original_url": checks,
        "head_checks_executed": probe_head,
        "actual_tile_polygon_intersection_verified": False,
        "original_laz_or_zip_bytes_downloaded": False,
        "classified_point_or_height_values_read": False,
        "coordinate_order_ground_control_verified": False,
        "building_heights_verified": False,
        "model_input_admitted": False,
        "raw_resource_links_tile_names_or_original_rows_exported": False,
    }


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-gpkg",type=Path,required=True)
    p.add_argument("--probe-head",action="store_true",
                   help="HEAD only against allowlisted official URLs; no redirects followed")
    args=p.parse_args(argv)
    try:
        result=inspect(args.original_gpkg,probe_head=args.probe_head)
    except (OSError,LidarLinkError,LidarTileSelectionError) as exc:
        print("BLOCKED: "+str(exc),file=sys.stderr)
        return 2
    print(json.dumps(result,sort_keys=True,indent=2,allow_nan=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
