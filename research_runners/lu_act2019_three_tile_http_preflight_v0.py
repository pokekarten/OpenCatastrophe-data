#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Three ACT 2019 LiDAR tile archives: bounded remote HEAD and 4-byte Range probes.

The caller supplies the exact hash-pinned official GeoJSON index. Never download
a tile archive, upload original point data, or print tile URLs/identifiers.
Reports only site-level ordered metadata, not full source integrity or CAT admission.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener

from research_runners.lu_act2019_original_lidar_tile_index_v0 import (
    SITES, WINDOW_HALF_M, OBSERVED_STUDY_TILE_COUNTS,
    _unique_pairs, _reject_constant, _validate_asset_url, profile_index,
    verify_original, OriginalIndexError,
)

MAX_REMOTE_BYTES = 1_500_000_000
EXPECTED_TOTAL_SITES = sum(OBSERVED_STUDY_TILE_COUNTS.values())
RANGE_RX = re.compile(r"bytes 0-3/([1-9][0-9]{0,11})\Z")
TIMEOUT_SECONDS = 15


class TileProbeError(ValueError):
    """Hand-authored source or geometry error, no original source text."""


class RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise TileProbeError("Unreviewed provider redirect")


def build_site_windows():
    """Two fixed public 100m squares with the same geometry as the index audit."""
    try:
        from pyproj import Transformer
        from shapely.geometry import Polygon
    except ImportError as exc:
        raise TileProbeError("Pinned GIS runtime required") from exc
    forward = Transformer.from_crs(4326, 3035, always_xy=True)
    backward = Transformer.from_crs(3035, 4326, always_xy=True)
    windows = {}
    for site, (lon,lat) in SITES.items():
        x,y = forward.transform(lon,lat)
        points = [backward.transform(a,b) for a,b in (
            (x-WINDOW_HALF_M, y-WINDOW_HALF_M),
            (x+WINDOW_HALF_M, y-WINDOW_HALF_M),
            (x+WINDOW_HALF_M, y+WINDOW_HALF_M),
            (x-WINDOW_HALF_M, y+WINDOW_HALF_M),
        )]
        if not all(math.isfinite(z) for v in points for z in v):
            raise TileProbeError("Invalid fixed study area")
        square=Polygon(points)
        if square.is_empty or not square.is_valid or square.area <= 0:
            raise TileProbeError("Invalid fixed study polygon")
        windows[site] = square
    return windows


def select_site_urls(original_index: dict, windows: dict) -> dict[str,list[str]]:
    """Original-source selection; exact geometry intersection and URL safety."""
    polygons=profile_index(original_index)
    if set(windows) != set(SITES):
        raise TileProbeError("Missing or unexpected predeclared study site")
    try:
        from shapely.geometry import shape
    except ImportError as exc:
        raise TileProbeError("Pinned Shapely runtime required") from exc
    selected={s:[] for s in SITES}
    for feature, geom in zip(original_index["features"],polygons,strict=True):
        polygon=shape(geom)
        if polygon.is_empty or not polygon.is_valid or polygon.area <= 0:
            raise TileProbeError("Invalid original tile polygon")
        for site,window in windows.items():
            if polygon.intersects(window) and polygon.intersection(window).area > 0:
                selected[site].append(_validate_asset_url(feature["properties"]["url"]))
    if any(len(selected[s]) != OBSERVED_STUDY_TILE_COUNTS[s] for s in SITES):
        raise TileProbeError("Original fixed-site tile count drifted")
    all_urls=[u for group in selected.values() for u in group]
    if len(all_urls) != EXPECTED_TOTAL_SITES or len(set(all_urls)) != EXPECTED_TOTAL_SITES:
        raise TileProbeError("Overlapping or duplicate site tile identities")
    return selected


def validate_response_origin(response, expected_url: str):
    """Reject any unexpected response origin even if HTTP tools followed a redirect."""
    url=response.geturl()
    if url != expected_url or urlsplit(url).scheme != "https":
        raise TileProbeError("Remote source origin changed")


def decode_total_length(value):
    if not isinstance(value,str) or not value.isdecimal():
        return None
    n=int(value)
    return n if 4 <= n <= MAX_REMOTE_BYTES else None


def probe_one(url: str, *, opener=None) -> dict:
    """At most HEAD + 4 bytes of ZIP data; never trust server size as byte proof."""
    _validate_asset_url(url)
    if opener is None:
        opener=build_opener(RejectRedirects())
    outcome={
        "head_http": None, "head_content_length_bytes": None,
        "range_http": None, "range_206_supported": False,
        "first_four_bytes_zip_local_header": False,
        "range_full_size_matches_head": False,
        "original_archive_full_sha256_verified": False,
        "full_zip_download_attempted": False,
        "original_laz_points_inspected": False,
    }
    try:
        req=Request(url, method="HEAD",headers={"Accept-Encoding":"identity"})
        with opener.open(req,timeout=TIMEOUT_SECONDS) as response:
            validate_response_origin(response,url)
            outcome["head_http"] = response.status
            if response.status != 200:
                return outcome
            outcome["head_content_length_bytes"] = decode_total_length(
                response.headers.get("Content-Length"))
    except (HTTPError, URLError, TimeoutError, OSError, TileProbeError):
        return outcome
    # Failure/missing size is a meaningful unverified result, not permission
    # to download unknown original data.
    if outcome["head_content_length_bytes"] is None:
        return outcome
    try:
        req=Request(url,method="GET",headers={
            "Range":"bytes=0-3","Accept-Encoding":"identity"})
        with opener.open(req,timeout=TIMEOUT_SECONDS) as response:
            validate_response_origin(response,url)
            outcome["range_http"]=response.status
            if response.status != 206:
                return outcome
            outcome["range_206_supported"]=True
            match=RANGE_RX.fullmatch(response.headers.get("Content-Range","").strip())
            outcome["range_full_size_matches_head"]=bool(
                match and int(match.group(1)) == outcome["head_content_length_bytes"])
            # A 4-byte read cannot validate the whole archive. Never call
            # response.read() without an explicit max size.
            outcome["first_four_bytes_zip_local_header"]=response.read(4)==b"PK\x03\x04"
    except (HTTPError, URLError, TimeoutError, OSError, TileProbeError):
        pass
    return outcome


def run(path: Path, *, opener=None) -> dict:
    receipt=verify_original(path)  # full immutable source hashes / site counts
    try:
        original=json.loads(path.read_text(encoding="utf-8"),
                            object_pairs_hook=_unique_pairs,
                            parse_constant=_reject_constant)
    except (UnicodeError, ValueError) as exc:
        raise TileProbeError("Original source JSON could not be reloaded") from exc
    urls=select_site_urls(original,build_site_windows())
    if len(urls) != 2:
        raise TileProbeError("Source sites not conserved")
    sites={}
    for site,chosen in urls.items():
        sites[site]={
            "index_tile_footprints":len(chosen),
            "ordered_original_tile_http_metadata":[probe_one(u,opener=opener) for u in chosen],
        }
    return {
        "profile":"lu-act2019-three-original-tile-head-range-preflight-v0",
        "source_index_sha256":receipt["original_index_sha256"],
        "source_index_original_tile_polygons":receipt["original_index_tile_polygons"],
        "sites":sites,
        "unique_remote_zip_assets_probed":EXPECTED_TOTAL_SITES,
        "http_header_size_is_original_byte_integrity_proof":False,
        "source_catalogue_rights_individually_reviewed":False,
        "point_cloud_zip_bytes_acquired":False,
        "independent_2019_building_truth_validated":False,
        "cat_exposure_model_input_admitted":False,
        "original_tile_urls_logged":False,
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-index",required=True,type=Path)
    args=p.parse_args(argv)
    try:
        result=run(args.original_index)
    except (OriginalIndexError,TileProbeError,OSError,ValueError,TypeError):
        # Do not dump provider URLs, original tile filenames or coordinates.
        print("BLOCKED: original LiDAR2019 tile HTTP preflight source/area contract")
        return 2
    print(json.dumps(result,indent=2,sort_keys=True,allow_nan=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
