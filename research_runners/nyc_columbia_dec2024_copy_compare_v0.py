# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Read-only identity and bbox comparison of a *third-party* NYC December 2024 copy.

The ArcGIS copy was uploaded on 2024-12-07 by a Columbia account, NOT
authenticated as a City OTI archival release. Its editing timestamp is an
ArcGIS service metadata value, not a certified original City capture date.
No raw property IDs, polygons, geometry coordinates or source rows exported.
This tool does not admit year-2024 city stock or any insurer exposures.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
import re
import sys
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

CITY = "data.cityofnewyork.us"
ARCGIS = "services2.arcgis.com"
ARCGIS_CATALOG = "www.arcgis.com"
LL84 = "5zyy-y8am"
CURRENT_OTI = "5zhs-2jue"
ITEM_ID = "66e3c725ad9843569da25ce1059a3807"
ITEM_OWNER = "rm4068_columbia"
ARCGIS_PATH = (
    "/ArcGIS/rest/services/NYC_Building_Footprint/FeatureServer/0"
)
EXPECTED_COPY_FEATURES = 1082964
EXPECTED_ITEM_CREATED_DAY = "2024-12-07"
MAX_RESPONSE_BYTES = 450_000
MAX_FEATURE_VERTICES = 15_000
MAX_COHORT_VERTICES = 60_000
N = 30
GROUP = 5
BIN = re.compile(r"[1-5][0-9]{6}\Z")
BBL = re.compile(r"[1-5][0-9]{9}\Z")
DEC = re.compile(r"[0-9]+\Z")
LL_FIELDS = (
    "property_id", "nyc_borough_block_and_lot",
    "nyc_building_identification", "parent_property_id",
    "number_of_buildings", "report_year",
)
OLD_FIELDS = (
    "BIN", "DOITT_ID", "BASE_BBL", "MPLUTO_BBL", "FEAT_CODE",
    "CNSTRCT_YR", "LSTMODDATE",
)
CURRENT_FIELDS = (
    "bin", "doitt_id", "base_bbl", "mappluto_bbl", "feature_code",
    "the_geom",
)


class CopyProbeError(ValueError):
    pass


class CopyTransportError(CopyProbeError):
    """Retry transport failure per BIN; never silently convert to absence."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CopyProbeError("provider URL redirected; source identity review required")


def _query(host: str, path: str, params: dict[str, str]) -> str:
    if (host, path) not in {
        (CITY, f"/resource/{LL84}.json"),
        (CITY, f"/resource/{CURRENT_OTI}.json"),
        (ARCGIS, ARCGIS_PATH),
        (ARCGIS, ARCGIS_PATH + "/query"),
        (ARCGIS_CATALOG, f"/sharing/rest/content/items/{ITEM_ID}"),
    }:
        raise CopyProbeError("unexpected source URL")
    return f"https://{host}{path}?{urlencode(params)}"


def ll84_url() -> str:
    return _query(CITY, f"/resource/{LL84}.json", {
        "$select": ",".join(LL_FIELDS),
        "$where": "report_year = 2024 AND nyc_borough_block_and_lot like '1000%'",
        "$order": "property_id ASC",
        "$limit": str(N),
    })


def item_url() -> str:
    return _query(ARCGIS_CATALOG, f"/sharing/rest/content/items/{ITEM_ID}", {"f": "json"})


def layer_url() -> str:
    return _query(ARCGIS, ARCGIS_PATH, {"f": "json"})


def count_url() -> str:
    return _query(ARCGIS, ARCGIS_PATH + "/query", {
        "where": "1=1", "returnCountOnly": "true", "f": "json",
    })


def feature_urls(bins: tuple[str, ...]) -> tuple[str, str]:
    if type(bins) is not tuple or not 1 <= len(bins) <= GROUP or len(set(bins)) != len(bins):
        raise CopyProbeError("require one to five unique original BINs")
    if any(type(b) is not str or not BIN.fullmatch(b) or b[1:] == "000000" for b in bins):
        raise CopyProbeError("invalid or unassigned original BIN")
    where = "BIN IN (" + ",".join(bins) + ")"
    old_url = _query(ARCGIS, ARCGIS_PATH + "/query", {
        "where": where, "outFields": ",".join(OLD_FIELDS),
        "returnGeometry": "true", "outSR": "4326", "f": "json",
    })
    current_url = _query(CITY, f"/resource/{CURRENT_OTI}.json", {
        "$select": ",".join(CURRENT_FIELDS),
        "$where": "bin in (" + ",".join(bins) + ")",
        "$limit": "100",
    })
    return old_url, current_url


def _fetch(url: str) -> bytes:
    parsed = urlsplit(url)
    if (parsed.scheme, parsed.username, parsed.password) != ("https", None, None):
        raise CopyProbeError("only original HTTPS source identities allowed")
    if (parsed.hostname, parsed.path) not in {
        (CITY, f"/resource/{LL84}.json"),
        (CITY, f"/resource/{CURRENT_OTI}.json"),
        (ARCGIS, ARCGIS_PATH),
        (ARCGIS, ARCGIS_PATH + "/query"),
        (ARCGIS_CATALOG, f"/sharing/rest/content/items/{ITEM_ID}"),
    }:
        raise CopyProbeError("provider host or path changed")
    req = Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "OpenCatastrophe-2024-thirdparty-building-copy-research/0",
    })
    try:
        with build_opener(_NoRedirect()).open(req, timeout=20) as response:
            if response.status != 200 or response.headers.get_content_type() != "application/json":
                raise CopyProbeError("provider did not return HTTP 200 application/json")
            payload = response.read(MAX_RESPONSE_BYTES + 1)
    except (OSError, TimeoutError) as exc:
        raise CopyTransportError("source unreachable; cannot infer zero rows") from exc
    if len(payload) > MAX_RESPONSE_BYTES:
        raise CopyProbeError("provider response exceeds bounded research payload")
    return payload


def _decode(raw: bytes):
    if type(raw) is not bytes or not 1 <= len(raw) <= MAX_RESPONSE_BYTES:
        raise CopyProbeError("bad original-source response size")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CopyProbeError("invalid source JSON") from exc
    if type(value) is dict and "error" in value:
        raise CopyProbeError("provider returned an error envelope")
    return value


def _day_from_millis(value) -> str:
    if type(value) is not int or not 0 < value < 2_000_000_000_000:
        raise CopyProbeError("unexpected provider date timestamp")
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).date().isoformat()


def validate_provider(item: dict, layer: dict, counts: dict) -> dict:
    if type(item) is not dict or type(layer) is not dict or type(counts) is not dict:
        raise CopyProbeError("missing provider metadata")
    if (item.get("id"), item.get("owner"), item.get("access")) != (
        ITEM_ID, ITEM_OWNER, "public"
    ):
        raise CopyProbeError("ArcGIS item id, owner or access drifted")
    created, modified = (_day_from_millis(item.get("created")),
                         _day_from_millis(item.get("modified")))
    if created != EXPECTED_ITEM_CREATED_DAY or modified != EXPECTED_ITEM_CREATED_DAY:
        raise CopyProbeError("2024 hosted copy is no longer version-stable")
    if layer.get("serviceItemId") != ITEM_ID or layer.get("name") != "building":
        raise CopyProbeError("ArcGIS layer points at unexpected item")
    info = layer.get("editingInfo")
    if type(info) is not dict:
        raise CopyProbeError("ArcGIS edit metadata not provided")
    for key in ("lastEditDate", "dataLastEditDate", "schemaLastEditDate"):
        if _day_from_millis(info.get(key)) != EXPECTED_ITEM_CREATED_DAY:
            raise CopyProbeError("hosted copy edit metadata no longer pinned to Dec 7")
    wkid = (layer.get("extent") or {}).get("spatialReference") or {}
    if wkid.get("latestWkid") != 2263:
        raise CopyProbeError("unexpected ArcGIS native State Plane CRS")
    field_names = {
        f.get("name") for f in layer.get("fields", [])
        if type(f) is dict
    }
    if not set(OLD_FIELDS).issubset(field_names):
        raise CopyProbeError("historical copy field schema changed")
    if type(counts.get("count")) is not int or counts["count"] != EXPECTED_COPY_FEATURES:
        raise CopyProbeError("hosted copy full layer count changed")
    return {
        "provider_copy_owner": ITEM_OWNER,
        "provider_copy_item_created_utc": created,
        "provider_copy_last_modified_utc": modified,
        "provider_copy_feature_count": counts["count"],
        "native_crs_epsg": 2263,
        "queried_polygon_crs_epsg": 4326,
        "official_nyc_oti_archive_release_attested": False,
    }


def parse_ll84(raw: object) -> tuple[tuple[str, ...], dict[str, str]]:
    if type(raw) is not list or len(raw) != N:
        raise CopyProbeError("LL84 must return exactly the fixed 30-row cohort")
    pids = set()
    result = {}
    ordered = []
    for r in raw:
        if type(r) is not dict or set(r) != set(LL_FIELDS):
            raise CopyProbeError("LL84 original source field schema changed")
        p, b, key = (r["property_id"], r["nyc_borough_block_and_lot"],
                     r["nyc_building_identification"])
        if (type(p) is not str or not DEC.fullmatch(p) or p in pids
            or type(b) is not str or not BBL.fullmatch(b) or not b.startswith("1000")
            or type(key) is not str or not BIN.fullmatch(key)
            or key[1:] == "000000" or key in result
            or r["report_year"] != "2024"
            or r["parent_property_id"] != "Not Applicable: Standalone Property"
            or r["number_of_buildings"] != "1"):
            raise CopyProbeError("ambiguous 2024 LL84 property/building grain")
        pids.add(p)
        result[key] = b
        ordered.append(key)
    return tuple(ordered), result


def _outline(rings: object, old: bool) -> tuple[int, tuple[float, float, float, float]]:
    if type(rings) is not list or not rings:
        raise CopyProbeError("missing geometry rings")
    # ArcGIS supplies a flat rings collection; GeoJSON current polygons are
    # nested Polygon -> LinearRing collections and flattened by the caller.
    n = 0
    xmin = ymin = float("inf")
    xmax = ymax = float("-inf")
    for ring in rings:
        if type(ring) is not list or not 4 <= len(ring) <= MAX_FEATURE_VERTICES:
            raise CopyProbeError("ring cardinality invalid")
        if ring[0] != ring[-1]:
            raise CopyProbeError("source ring not closed")
        n += len(ring)
        if n > MAX_FEATURE_VERTICES:
            raise CopyProbeError("individual polygon vertex budget exceeded")
        for point in ring:
            if (type(point) is not list or len(point) != 2
                or any(type(v) not in (int, float) or not math.isfinite(v) for v in point)):
                raise CopyProbeError("invalid geographic coordinate pair")
            lon, lat = point
            if not (-75 < lon < -73 and 40 < lat < 42):
                raise CopyProbeError("unexpected NYC geographic bounds")
            xmin, xmax = min(xmin, lon), max(xmax, lon)
            ymin, ymax = min(ymin, lat), max(ymax, lat)
    if xmax - xmin < 1e-8 or ymax - ymin < 1e-8:
        raise CopyProbeError("degenerate polygon bbox")
    return n, (xmin, xmax, ymin, ymax)


def _old_records(raw: object, permitted: set[str]) -> dict[str, dict]:
    if type(raw) is not dict or type(raw.get("features")) is not list:
        raise CopyProbeError("ArcGIS features missing")
    if raw.get("exceededTransferLimit"):
        raise CopyProbeError("ArcGIS feature query truncated")
    sr = raw.get("spatialReference") or {}
    if sr.get("latestWkid", sr.get("wkid")) != 4326:
        raise CopyProbeError("ArcGIS output WGS84 CRS not confirmed")
    entries = {}
    for row in raw["features"]:
        if type(row) is not dict or type(row.get("attributes")) is not dict:
            raise CopyProbeError("malformed ArcGIS feature")
        a = row["attributes"]
        b = a.get("BIN")
        if type(b) is not int or str(b) not in permitted or str(b) in entries:
            raise CopyProbeError("out-of-cohort or duplicate hosted BIN")
        if a.get("FEAT_CODE") != 2100:
            raise CopyProbeError("hosted source nonbuilding feature")
        for k in ("BASE_BBL", "MPLUTO_BBL"):
            if type(a.get(k)) is not str or not BBL.fullmatch(a[k]):
                raise CopyProbeError("missing physical or billing BBL")
        if type(a.get("DOITT_ID")) is not int or a["DOITT_ID"] <= 0:
            raise CopyProbeError("missing/invalid hosted DOITT identity")
        rings = (row.get("geometry") or {}).get("rings")
        entries[str(b)] = {**a, "_shape": _outline(rings, old=True)}
    return entries


def _city_records(raw: object, permitted: set[str]) -> dict[str, dict]:
    if type(raw) is not list or len(raw) >= 100:
        raise CopyProbeError("current OTI query malformed/truncated")
    entries = {}
    for row in raw:
        if type(row) is not dict:
            raise CopyProbeError("current OTI feature malformed")
        b = row.get("bin")
        if type(b) is not str or b not in permitted or b in entries:
            raise CopyProbeError("out-of-cohort or duplicate OTI BIN")
        if row.get("feature_code") != "2100":
            raise CopyProbeError("current OTI nonbuilding feature")
        for k in ("base_bbl", "mappluto_bbl"):
            if type(row.get(k)) is not str or not BBL.fullmatch(row[k]):
                raise CopyProbeError("invalid current OTI BBL")
        doitt = row.get("doitt_id")
        if type(doitt) is not str or not DEC.fullmatch(doitt) or doitt == "0":
            raise CopyProbeError("invalid current OTI DOITT")
        geom = row.get("the_geom")
        if type(geom) is not dict or geom.get("type") != "MultiPolygon":
            raise CopyProbeError("expected current OTI GeoJSON multipolygon")
        polys = geom.get("coordinates")
        if type(polys) is not list or not polys:
            raise CopyProbeError("malformed current OTI polygon collection")
        rings = []
        for polygon in polys:
            if type(polygon) is not list or not polygon:
                raise CopyProbeError("invalid OTI inner polygon")
            rings.extend(polygon)
        entries[b] = {**row, "_shape": _outline(rings, old=False)}
    return entries


def summarize(item: dict, layer: dict, count: dict, ll84: list[dict],
              old_groups: list[dict], current_groups: list[list[dict]]) -> dict:
    meta = validate_provider(item, layer, count)
    bins, expected = parse_ll84(ll84)
    if type(old_groups) is not list or type(current_groups) is not list:
        raise CopyProbeError("missing source groups")
    if len(old_groups) != N // GROUP or len(current_groups) != N // GROUP:
        raise CopyProbeError("expected six complete original source groups")
    old_rows, current_rows = {}, {}
    all_vertices = 0
    for i in range(0, N, GROUP):
        bset = set(bins[i:i+GROUP])
        hosted = _old_records(old_groups[i // GROUP], bset)
        city = _city_records(current_groups[i // GROUP], bset)
        if len(hosted) != GROUP or len(city) != GROUP or set(hosted) != bset or set(city) != bset:
            raise CopyProbeError("source transport or BIN cardinality incomplete")
        old_rows.update(hosted)
        current_rows.update(city)
        all_vertices += sum(x["_shape"][0] for x in hosted.values())
        all_vertices += sum(x["_shape"][0] for x in city.values())
        if all_vertices > MAX_COHORT_VERTICES:
            raise CopyProbeError("cohort geometry exceeded fixed budget")
    counts = Counter()
    max_delta = 0.0
    doitt_old = set()
    doitt_city = set()
    for b in bins:
        x = old_rows[b]
        y = current_rows[b]
        doitt_old.add(str(x["DOITT_ID"]))
        doitt_city.add(y["doitt_id"])
        counts["both_provider_buildings"] += 1
        counts["stable_doitt"] += str(x["DOITT_ID"]) == y["doitt_id"]
        counts["stable_base_bbl"] += x["BASE_BBL"] == y["base_bbl"]
        counts["stable_billing_bbl"] += x["MPLUTO_BBL"] == y["mappluto_bbl"]
        counts["old_billing_matches_ll84_bbl"] += x["MPLUTO_BBL"] == expected[b]
        counts["old_base_bbl_matches_ll84_bbl"] += x["BASE_BBL"] == expected[b]
        counts["both_standard_building_code_2100"] += 1
        a, abox = x["_shape"]
        c, cbox = y["_shape"]
        counts["same_number_of_ring_vertices"] += a == c
        delta = max(abs(u-v) for u, v in zip(abox, cbox))
        max_delta = max(max_delta, delta)
        counts["bbox_within_1e_9_degrees"] += delta <= 1e-9
        counts["bbox_within_1e_5_degrees"] += delta <= 1e-5
    if len(doitt_old) != N or len(doitt_city) != N:
        raise CopyProbeError("DOITT identifiers duplicated within 30-feature research cohort")
    return {
        "profile": "nyc_columbia_dec2024_copy_oti2026_30_geometry_comparison_v0",
        "sample_rule": "LL84 2024 BBL prefix 1000%, first 30 ascending property_id",
        "old_arcgis_source": "Columbia-hosted independent ArcGIS NYC Building Footprint",
        "current_oti_source": CURRENT_OTI,
        **meta,
        "cohort_size": N,
        "original_source_comparison": dict(sorted(counts.items())),
        "max_bbox_abs_delta_degrees": round(max_delta, 12),
        "bbox_diagnostics_are_not_geometric_equivalence": True,
        "original_source_2024_full_snapshot_sha256_known": False,
        "authenticated_original_nyc_asof_2024_stock": False,
        "external_replica_reuse_rights_approved": False,
        "worldwide_exposure_or_insured_tiv_calculated": False,
        "raw_external_source_rows_ids_or_geometries_exported": False,
    }


def run_live(fetch=_fetch) -> dict:
    item = _decode(fetch(item_url()))
    layer = _decode(fetch(layer_url()))
    count = _decode(fetch(count_url()))
    if type(item) is not dict or type(layer) is not dict or type(count) is not dict:
        raise CopyProbeError("malformed original source metadata")
    ll84 = _decode(fetch(ll84_url()))
    bins, _ = parse_ll84(ll84)
    old_groups, current_groups = [], []
    for i in range(0, N, GROUP):
        group = bins[i:i+GROUP]
        old, current = feature_urls(group)
        try:
            a = _decode(fetch(old))
        except CopyTransportError:
            singles = []
            for b in group:
                singles.extend(_old_records(_decode(fetch(feature_urls((b,))[0])), {b}).values())
            # These are the already validated per-BIN records. Preserve
            # schema to reuse the central original-feature validator below.
            raise CopyProbeError("ArcGIS batch timeout: retry only via explicit reviewed source runner")  # no inferred matches
        try:
            c = _decode(fetch(current))
        except CopyTransportError:
            raise CopyProbeError("NYC batch transport unavailable; no negative-match inference")
        old_groups.append(a)
        current_groups.append(c)
    return summarize(item, layer, count, ll84, old_groups, current_groups)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="bounded opt-in original-service research queries")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("no network without explicit --live")
    try:
        print(json.dumps(run_live(), sort_keys=True, separators=(",", ":")))
        return 0
    except CopyProbeError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
