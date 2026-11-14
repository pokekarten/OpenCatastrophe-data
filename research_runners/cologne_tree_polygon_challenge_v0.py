# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Research-only Cologne tree point-in-official-Stadtteil polygon challenge.

Read five pinned sorted Baumkataster WFS point samples and independently
ask the municipal KGG ArcGIS REST *Stadtteil polygon layer* whether each
ETRS89/UTM32 -> WGS84 point intersects exactly one official city polygon.
An outside-Cologne negative control must return no polygon. Compare the
published tree Stadtteil string only when present: blanks are not silently
imputed; contradictions fail closed. Provider rows/positions/names never
leave process memory or appear in stdout/Git; original source bytes never
persist. This challenges plausibility, not spatial accuracy or admission.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import unicodedata
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

import cologne_tree_crs_challenge_v0 as tree

KGG_BASE = (
    "https://geoportal.stadt-koeln.de/arcgis/rest/services/basiskarten/"
    "kgg/MapServer/3/query"
)
KGG_STADTTEIL_BOUNDS = (6.77146787, 50.82547445, 7.16351331, 51.09018683)
NEGATIVE_POINT = (13.405, 52.52)  # Fixed public Berlin control.
MAX_RESPONSE_BYTES = 16_384


class PolygonChallengeError(ValueError):
    """The independent KGG polygon/label result fails source challenge."""


class DenyRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def query_url(lon: float, lat: float) -> str:
    """Only accept candidate Cologne point positions or one fixed negative."""
    if not (isinstance(lon, (int, float)) and isinstance(lat, (int, float))
            and math.isfinite(lon) and math.isfinite(lat)):
        raise PolygonChallengeError("non-finite or invalid query position")
    west, south, east, north = KGG_STADTTEIL_BOUNDS
    if not ((west <= lon <= east and south <= lat <= north)
            or (lon, lat) == NEGATIVE_POINT):
        raise PolygonChallengeError("unapproved KGG point location")
    # OGC-style geographic x/y: lon, lat with explicit inSR=4326.
    return (
        KGG_BASE + "?where=1%3D1&geometry=" + format(lon, ".8f") +
        "," + format(lat, ".8f") +
        "&geometryType=esriGeometryPoint&inSR=4326"
        "&spatialRel=esriSpatialRelIntersects"
        "&returnGeometry=false&outFields=name,nummer&f=json"
    )


def parse_point_reply(payload: bytes) -> str | None:
    """Accept at most one polygon label, never return source geometry/rows."""
    if not payload or len(payload) > MAX_RESPONSE_BYTES:
        raise PolygonChallengeError("empty or oversized KGG response")
    try:
        doc = json.loads(payload.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise PolygonChallengeError("invalid KGG JSON") from exc
    if not isinstance(doc, dict) or "error" in doc:
        raise PolygonChallengeError("provider returned KGG error")
    features = doc.get("features")
    if not isinstance(features, list) or len(features) > 1:
        raise PolygonChallengeError("unexpected KGG feature count")
    if not features:
        return None
    feature = features[0]
    if not isinstance(feature, dict) or "geometry" in feature:
        raise PolygonChallengeError("unexpected polygon geometry in reply")
    attr = feature.get("attributes")
    if not isinstance(attr, dict) or set(attr) != {"name", "nummer"}:
        raise PolygonChallengeError("unexpected city-area attribute contract")
    name, number = attr.get("name"), attr.get("nummer")
    if not isinstance(name, str) or not name.strip() or len(name) > 80:
        raise PolygonChallengeError("missing official Stadtteil label")
    if not isinstance(number, str) or not number.isdigit() or len(number) != 3:
        raise PolygonChallengeError("missing official numeric Stadtteil identity")
    return name.strip()


def fetch_official_stadtteil(lon: float, lat: float) -> str | None:
    """One fixed-origin provider-side polygon intersection, no raw polygons."""
    url = query_url(lon, lat)
    req = Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "OpenCatastrophe-data-Cologne-polygon-science/1",
    }, method="GET")
    try:
        with build_opener(DenyRedirects).open(req, timeout=20) as response:
            if response.status != 200 or response.geturl() != url:
                raise PolygonChallengeError("KGG HTTP status or redirect refused")
            if response.headers.get_content_type().lower() != "application/json":
                raise PolygonChallengeError("KGG response not JSON")
            length = response.headers.get("Content-Length")
            if length is not None and int(length) > MAX_RESPONSE_BYTES:
                raise PolygonChallengeError("KGG response advertises excess size")
            payload = response.read(MAX_RESPONSE_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        raise PolygonChallengeError("KGG fixed network gate failed") from exc
    return parse_point_reply(payload)


def _canonical_label(value: str) -> str:
    return unicodedata.normalize("NFC", value).casefold().strip()


def review_samples(samples: list[dict[str, object]], transform, lookup) -> dict[str, object]:
    """Fail on wrong polygon membership, mismatched source Stadtteil or control.

    The injected transform/lookup make regression tests synthetic and offline.
    """
    try:
        envelope = tree.assess_crs_hypothesis(samples, transform)
    except tree.ChallengeError as exc:
        raise PolygonChallengeError("upstream CRS/envelope challenge failed") from exc

    corroborated = 0
    missing_source = 0
    kgg_labels = []
    for sample in samples:
        lon, lat = transform(*sample["coords_internal"])
        if not (math.isfinite(lon) and math.isfinite(lat)):
            raise PolygonChallengeError("non-finite transformed position")
        official = lookup(lon, lat)
        if not isinstance(official, str) or not official.strip():
            raise PolygonChallengeError("tree point not inside exactly one official Stadtteil polygon")
        source = sample.get("source_stadtteil_internal", "")
        if not isinstance(source, str) or len(source) > 80:
            raise PolygonChallengeError("invalid private source Stadtteil label")
        if source.strip():
            if _canonical_label(source) != _canonical_label(official):
                raise PolygonChallengeError("tree Stadtteil contradicts independent KGG polygon")
            corroborated += 1
        else:
            missing_source += 1
        kgg_labels.append(official)

    # An outside-Cologne point must not be accepted by the server-side filter.
    if lookup(*NEGATIVE_POINT) is not None:
        raise PolygonChallengeError("negative outside-city polygon control failed")
    if corroborated < 3:
        raise PolygonChallengeError("too few independent source-label agreements")
    if len(set(_canonical_label(label) for label in kgg_labels)) < 3:
        raise PolygonChallengeError("insufficient distinct official Stadtteil polygons")

    return {
        "source": "Stadt Koeln public Baumkataster WFS",
        "independent_official_polygon_provider": "Stadt Koeln KGG Stadtteil ArcGIS REST",
        "candidate_source_crs": "EPSG:25832",
        "candidate_target_crs": "EPSG:4326",
        "fixed_sorted_offsets": list(tree.OFFSETS),
        "sample_count": len(samples),
        "independent_polygon_hits": len(samples),
        "source_stadtteil_labels_corroborated": corroborated,
        "source_stadtteil_labels_missing": missing_source,
        "independent_distinct_stadtteil_count": len(set(kgg_labels)),
        "outside_city_negative_control_returns_zero": True,
        "provider_response_sha256": envelope["source_response_sha256"],
        "raw_tree_ids_or_coordinates_exposed": False,
        "external_data_bytes_persisted": False,
        "provider_snapshot_pinned": False,
        "independent_positional_accuracy_verified": False,
        "scientific_validation_complete": False,
        "model_admitted": False,
    }


def run_live() -> dict[str, object]:
    try:
        from pyproj import Transformer
    except ImportError as exc:
        raise PolygonChallengeError(
            "optional spatial profile missing: install requirements-eu-flood-spatial.txt"
        ) from exc
    samples = [tree.acquire_one(offset) for offset in tree.OFFSETS]
    replay = tree.acquire_one(tree.OFFSETS[0])
    if (replay["tree_id_sha256"] != samples[0]["tree_id_sha256"]
            or replay["coords_internal"] != samples[0]["coords_internal"]):
        raise PolygonChallengeError("tree register drift between sorted requests")
    transform = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True)
    result = review_samples(samples, transform.transform, fetch_official_stadtteil)
    result["first_sample_replay_stable"] = True
    result["observed_utc"] = datetime.now(timezone.utc).isoformat()
    result["verified_live"] = True
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live", action="store_true",
        help="explicit 6 tree WFS + 5 official polygon + 1 negative-control requests",
    )
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("offline by default; pass --live for source-bound verification")
    try:
        print(json.dumps(run_live(), sort_keys=True))
        return 0
    except (PolygonChallengeError, tree.ChallengeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
