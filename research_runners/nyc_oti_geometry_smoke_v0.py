# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Read-only 30-feature NYC OTI GeoJSON structural/vintage research smoke.

Research ONLY: no raw original building coordinates, BINs, PLUTO keys, model
exposures, insurer IDs or money values are written or printed. Spherical
areas are approximate diagnostics, NOT surveyed area, TIV or loss estimates.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import json
import math
import re
import statistics
import sys
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

HOST = "data.cityofnewyork.us"
LL84_VIEW = "5zyy-y8am"
FOOTPRINT_VIEW = "5zhs-2jue"
N = 30
CHUNK = 5
BATCH_LIMIT = 100
SINGLE_LIMIT = 20
MAX_RESPONSE_BYTES = 240_000
MAX_VERTICES_PER_FEATURE = 20_000
MAX_VERTICES_COHORT = 70_000
RADIUS_M = 6_371_008.8
BBL = re.compile(r"[1-5][0-9]{9}\Z")
BIN = re.compile(r"[1-5][0-9]{6}\Z")
NUMERIC_ID = re.compile(r"[0-9]+\Z")
LL84_FIELDS = ("property_id", "report_year", "nyc_borough_block_and_lot",
               "nyc_building_identification", "parent_property_id", "number_of_buildings")
FOOTPRINT_FIELDS = ("bin", "doitt_id", "base_bbl", "mappluto_bbl",
                    "feature_code", "the_geom", "geom_source",
                    "construction_year", "last_edited_date")


class GeometryProbeError(ValueError):
    pass


class TransportFailure(GeometryProbeError):
    """Only this failure permits narrower queries; never count it as nonmatch."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise GeometryProbeError("NYC provider redirect requires review")


def _url(view: str, params: dict[str, str]) -> str:
    if view not in (LL84_VIEW, FOOTPRINT_VIEW):
        raise GeometryProbeError("unexpected NYC dataset")
    return f"https://{HOST}/resource/{view}.json?{urlencode(params)}"


def ll84_url() -> str:
    return _url(LL84_VIEW, {
        "$select": ",".join(LL84_FIELDS),
        "$where": "report_year = 2024 AND nyc_borough_block_and_lot like '1000%'",
        "$order": "property_id ASC",
        "$limit": str(N),
    })


def footprint_url(bins: tuple[str, ...]) -> str:
    if type(bins) is not tuple or not 1 <= len(bins) <= CHUNK:
        raise GeometryProbeError("one to five original BINs required")
    if len(set(bins)) != len(bins) or any(type(b) is not str or not BIN.fullmatch(b) for b in bins):
        raise GeometryProbeError("invalid or duplicated original BIN")
    if any(b[1:] == "000000" for b in bins):
        raise GeometryProbeError("unassigned million BIN cannot be an identity")
    return _url(FOOTPRINT_VIEW, {
        "$select": ",".join(FOOTPRINT_FIELDS),
        "$where": "bin in (" + ",".join(bins) + ")",
        "$limit": str(SINGLE_LIMIT if len(bins) == 1 else BATCH_LIMIT),
    })


def _fetch(url: str) -> bytes:
    parts = urlsplit(url)
    if (parts.scheme, parts.hostname, parts.username, parts.password) != ("https", HOST, None, None):
        raise GeometryProbeError("only original NYC HTTPS provider allowed")
    if parts.path not in (f"/resource/{LL84_VIEW}.json", f"/resource/{FOOTPRINT_VIEW}.json"):
        raise GeometryProbeError("unexpected provider resource")
    request = Request(url, headers={"Accept": "application/json",
                        "User-Agent": "OpenCatastrophe-OTI-geometry-30row-research/0"})
    try:
        with build_opener(_NoRedirect()).open(request, timeout=20) as response:
            if response.status != 200 or response.headers.get_content_type() != "application/json":
                raise GeometryProbeError("non-200 or non-JSON original provider response")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (OSError, TimeoutError) as exc:
        raise TransportFailure("original-source transport unavailable; never infer missing feature") from exc
    if len(raw) > MAX_RESPONSE_BYTES:
        raise GeometryProbeError("oversized source response; do not silently truncate")
    return raw


def _parse(raw: bytes, limit: int) -> list[dict]:
    if type(raw) is not bytes or len(raw) > MAX_RESPONSE_BYTES:
        raise GeometryProbeError("invalid source response budget")
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise GeometryProbeError("invalid source JSON") from exc
    if type(data) is not list or len(data) >= limit or any(type(row) is not dict for row in data):
        raise GeometryProbeError("malformed or cardinality-truncated source response")
    return data


def geometry_screen(geometry: object) -> tuple[int, float, int, int]:
    """Check GeoJSON ring framing and bounds; return (vertices, approx m², parts, holes).

    Uses the spherical lon/sin(latitude) trapezoid formula, not a verified
    equal-area CRS, a geodesic/surveyed area, or polygon topology validation.
    Never use returned area as insured/TIV or as production footprint area.
    """
    if type(geometry) is not dict or set(geometry) != {"type", "coordinates"}:
        raise GeometryProbeError("unexpected GeoJSON geometry fields")
    if geometry["type"] != "MultiPolygon":
        raise GeometryProbeError("expected original MultiPolygon")
    polygons = geometry["coordinates"]
    if type(polygons) is not list or not polygons:
        raise GeometryProbeError("empty/malformed MultiPolygon")
    if len(polygons) > 100:
        raise GeometryProbeError("too many polygon parts")
    vertex_count = 0
    hole_count = 0
    total_area = 0.0
    for polygon in polygons:
        if type(polygon) is not list or not polygon or len(polygon) > 100:
            raise GeometryProbeError("invalid ring collection")
        hole_count += len(polygon) - 1
        for ring_index, ring in enumerate(polygon):
            if type(ring) is not list or not 4 <= len(ring) <= MAX_VERTICES_PER_FEATURE:
                raise GeometryProbeError("invalid ring vertex count")
            vertex_count += len(ring)
            if vertex_count > MAX_VERTICES_PER_FEATURE:
                raise GeometryProbeError("feature exceeds coordinate budget")
            first = ring[0]
            last = ring[-1]
            if type(first) is not list or first != last:
                raise GeometryProbeError("unclosed ring")
            seen_x, seen_y = [], []
            for pair in ring:
                if type(pair) is not list or len(pair) != 2 or any(type(v) not in (int, float) or not math.isfinite(v) for v in pair):
                    raise GeometryProbeError("invalid WGS84 coordinate")
                lon, lat = pair
                if not (-75.0 < lon < -73.0 and 40.0 < lat < 42.0):
                    raise GeometryProbeError("coordinate outside broad NYC guardrails")
                seen_x.append(lon)
                seen_y.append(lat)
            if max(seen_x) - min(seen_x) < 1e-8 or max(seen_y) - min(seen_y) < 1e-8:
                raise GeometryProbeError("degenerate ring bbox")
            subtotal = 0.0
            for a, b in zip(ring, ring[1:]):
                dlon = math.radians(b[0] - a[0])
                subtotal += dlon * (math.sin(math.radians(a[1])) + math.sin(math.radians(b[1]))) / 2
            ring_area = abs(subtotal) * RADIUS_M * RADIUS_M
            if ring_area < 1.0:
                raise GeometryProbeError("zero or tiny spherical screen ring")
            total_area += ring_area if ring_index == 0 else -ring_area
    if not (1 < total_area < 1e8):
        raise GeometryProbeError("invalid net spherical area diagnostic")
    return vertex_count, total_area, len(polygons), hole_count


def summarize(ll84: list[dict], footprints: list[dict]) -> dict:
    if type(ll84) is not list or len(ll84) != N or any(type(x) is not dict for x in ll84):
        raise GeometryProbeError("LL84 cohort must contain exactly 30 rows")
    expected: dict[str, str] = {}
    seen_properties = set()
    for row in ll84:
        if set(row) - set(LL84_FIELDS):
            raise GeometryProbeError("unexpected LL84 field")
        pid, bbl, bin_value = (row.get("property_id"), row.get("nyc_borough_block_and_lot"),
                               row.get("nyc_building_identification"))
        if type(pid) is not str or not NUMERIC_ID.fullmatch(pid) or pid in seen_properties:
            raise GeometryProbeError("bad or duplicate LL84 property")
        seen_properties.add(pid)
        if row.get("report_year") != "2024" or type(bbl) is not str or not BBL.fullmatch(bbl):
            raise GeometryProbeError("wrong LL84 year/BBL")
        if type(bin_value) is not str or not BIN.fullmatch(bin_value) or bin_value[1:] == "000000":
            raise GeometryProbeError("multi/invalid/million BIN unsupported in 30-row smoke")
        if bin_value in expected:
            raise GeometryProbeError("shared LL84 BIN in convenience cohort")
        if row.get("parent_property_id") != "Not Applicable: Standalone Property" or row.get("number_of_buildings") != "1":
            raise GeometryProbeError("parent campus or multi-building LL84 row")
        expected[bin_value] = bbl

    if type(footprints) is not list or len(footprints) != N or any(type(x) is not dict for x in footprints):
        raise GeometryProbeError("footprint record count not exactly 30")
    seen_doitt = set()
    seen_bins = set()
    geom_sources = Counter()
    base_bbl_relation = Counter()
    edited_after_2024 = 0
    missing_construction_year = 0
    constructed_after_2024 = 0
    vertex_total = 0
    part_multiple = 0
    with_holes = 0
    vertex_counts = []
    spherical_areas = []
    for row in footprints:
        if set(row) - set(FOOTPRINT_FIELDS):
            raise GeometryProbeError("unexpected geometry/source field")
        b = row.get("bin")
        doitt = row.get("doitt_id")
        if type(b) is not str or b not in expected or b in seen_bins:
            raise GeometryProbeError("missing/repeated/out-of-cohort footprint BIN")
        if type(doitt) is not str or not NUMERIC_ID.fullmatch(doitt) or doitt in seen_doitt:
            raise GeometryProbeError("missing/repeated DOITT feature identifier")
        seen_bins.add(b)
        seen_doitt.add(doitt)
        if row.get("feature_code") != "2100":
            raise GeometryProbeError("not a standard building outline")
        base = row.get("base_bbl")
        mappluto = row.get("mappluto_bbl")
        if type(base) is not str or not BBL.fullmatch(base) or mappluto != expected[b]:
            raise GeometryProbeError("physical-vs-billing BBL namespace not resolved")
        base_bbl_relation["equal" if base == expected[b] else "different"] += 1

        source = row.get("geom_source", "missing")
        if source not in ("Photogrammetric", "Other (Manual)", "missing"):
            raise GeometryProbeError("unknown geometry acquisition method")
        geom_sources[source] += 1
        year = row.get("construction_year")
        if year is None or year == "0":
            missing_construction_year += 1
        elif type(year) is not str or not re.fullmatch(r"[12][0-9]{3}", year):
            raise GeometryProbeError("invalid construction year")
        elif int(year) > 2024:
            constructed_after_2024 += 1
        edited = row.get("last_edited_date")
        if edited is not None:
            if type(edited) is not str:
                raise GeometryProbeError("invalid edit timestamp")
            try:
                year_edited = datetime.fromisoformat(edited.replace("Z", "+00:00")).year
            except ValueError as exc:
                raise GeometryProbeError("invalid edit timestamp") from exc
            if year_edited > 2024:
                edited_after_2024 += 1
        vertices, area_m2, parts, holes = geometry_screen(row.get("the_geom"))
        vertex_total += vertices
        if vertex_total > MAX_VERTICES_COHORT:
            raise GeometryProbeError("total vertices exceed pilot budget")
        vertex_counts.append(vertices)
        spherical_areas.append(area_m2)
        if parts > 1:
            part_multiple += 1
        if holes:
            with_holes += 1

    return {
        "profile": "nyc-oti-30-footprint-geometry-research-v0",
        "sample_rule": "LL84 2024 BBL prefix 1000%, 30 ascending property IDs",
        "footprints": N,
        "geometry_type": "MultiPolygon",
        "ring_structure_and_bbox_passed": N,
        "not_a_polygon_topology_validity_proof": True,
        "geometry_source_counts": dict(sorted(geom_sources.items())),
        "physical_base_bbl_vs_billing_mappluto_bbl": dict(sorted(base_bbl_relation.items())),
        "vertices": {"total": vertex_total, "min": min(vertex_counts), "max": max(vertex_counts)},
        "multipart_features": part_multiple,
        "features_with_inner_rings": with_holes,
        "construction_year_missing_or_zero": missing_construction_year,
        "construction_year_after_2024": constructed_after_2024,
        "last_edit_year_after_2024": edited_after_2024,
        "spherical_approx_area_m2": {
            "min_rounded": round(min(spherical_areas)),
            "median_rounded": round(statistics.median(spherical_areas)),
            "max_rounded": round(max(spherical_areas)),
            "sum_rounded": round(sum(spherical_areas)),
            "not_for_tiv_or_loss": True,
        },
        "historical_2024_presence_proven": False,
        "topology_survey_or_equal_area_crs_proven": False,
        "source_rights_or_model_admission_approved": False,
        "insurance_tiv_or_loss_calculated": False,
        "raw_property_ids_bin_bbl_or_geometry_exported": False,
    }


def run_live(fetch=_fetch) -> dict:
    ll84 = _parse(fetch(ll84_url()), N + 1)
    if len(ll84) != N:
        raise GeometryProbeError("incomplete original LL84 cohort")
    bins = []
    for row in ll84:
        value = row.get("nyc_building_identification")
        if type(value) is not str or not BIN.fullmatch(value) or value[1:] == "000000":
            raise GeometryProbeError("unsupported non-single BIN")
        bins.append(value)
    if len(set(bins)) != N:
        raise GeometryProbeError("duplicate original LL84 BIN")
    all_rows = []
    for i in range(0, N, CHUNK):
        batch = tuple(bins[i:i + CHUNK])
        try:
            all_rows.extend(_parse(fetch(footprint_url(batch)), BATCH_LIMIT))
        except TransportFailure:
            for b in batch:
                all_rows.extend(_parse(fetch(footprint_url((b,))), SINGLE_LIMIT))
    return summarize(ll84, all_rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Run a bounded original-source geometry probe")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("explicit --live required; no network by default")
    try:
        print(json.dumps(run_live(), sort_keys=True, separators=(",", ":")))
        return 0
    except GeometryProbeError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
