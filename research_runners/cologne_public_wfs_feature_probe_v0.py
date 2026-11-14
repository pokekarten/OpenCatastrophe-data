# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""One-feature Cologne WFS GeoJSON preflight: schema/CRS receipts, no data storage.

The source GeoJSON bytes are never printed or persisted. The tree WFS has
been observed returning projected, unlabelled coordinates in a GeoJSON body:
this probe must not mistake it for WGS84 or admit it into a CAT model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

SOURCES = {
    "tree": {
        "candidate_id": "de.koeln.city-tree-register.2026",
        "url": (
            "https://geoportal.stadt-koeln.de/wss/service/baumkataster_extern_wfs/guest"
            "?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature"
            "&TYPENAMES=ms:baumkataster&COUNT=1&SORTBY=Baumnummer"
            "&OUTPUTFORMAT=application%2Fjson%3B%20subtype%3Dgeojson"
        ),
        "geometry_type": "Point",
    },
    "kgg": {
        "candidate_id": "de.koeln.statistik.rbs-geopackage.2026",
        "url": (
            "https://geoportal.stadt-koeln.de/arcgis/services/basiskarten/kgg"
            "/MapServer/WFSServer?SERVICE=WFS&VERSION=2.0.0"
            "&REQUEST=GetFeature&TYPENAMES=Basiskarten_kgg:Stadtviertel"
            "&COUNT=1&OUTPUTFORMAT=GEOJSON"
        ),
        "geometry_type": "MultiPolygon",
    },
}
MAX_RESPONSE_BYTES = 160_000


class WfsSampleError(ValueError):
    """Unsafe, malformed or unsupported one-feature source response."""


class DenyRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise WfsSampleError("duplicate GeoJSON key")
        result[key] = value
    return result


def _reject_number(value: str) -> None:
    raise WfsSampleError("non-finite numeric value is invalid")


def _positions(coordinates: object):
    if isinstance(coordinates, list):
        if len(coordinates) >= 2 and all(isinstance(v, (float, int)) and
                                         not isinstance(v, bool) and math.isfinite(v)
                                         for v in coordinates[:2]):
            yield float(coordinates[0]), float(coordinates[1])
        else:
            for child in coordinates:
                yield from _positions(child)


def inspect_geojson(payload: bytes, source: str) -> dict[str, object]:
    """Return only safe shape, size, CRS and source byte-identity evidence."""
    if source not in SOURCES:
        raise WfsSampleError("unsupported source")
    if not payload or len(payload) > MAX_RESPONSE_BYTES:
        raise WfsSampleError("empty or oversized GeoJSON")
    try:
        doc = json.loads(payload.decode("utf-8"),
                         object_pairs_hook=_unique_object,
                         parse_constant=_reject_number)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise WfsSampleError("invalid UTF-8 JSON") from exc
    if not isinstance(doc, dict) or doc.get("type") != "FeatureCollection":
        raise WfsSampleError("not a GeoJSON FeatureCollection")
    features = doc.get("features")
    if not isinstance(features, list) or len(features) != 1:
        raise WfsSampleError("exactly one feature is required")
    feature = features[0]
    if not isinstance(feature, dict) or feature.get("type") != "Feature":
        raise WfsSampleError("not a GeoJSON Feature")
    geom = feature.get("geometry")
    if not isinstance(geom, dict) or geom.get("type") != SOURCES[source]["geometry_type"]:
        raise WfsSampleError("unexpected geometry type")
    properties = feature.get("properties")
    if not isinstance(properties, dict) or not properties:
        raise WfsSampleError("missing property schema")
    positions = tuple(_positions(geom.get("coordinates")))
    if not positions or len(positions) > 60_000:
        raise WfsSampleError("missing or excessive coordinates")
    crs = doc.get("crs")
    declared = (crs.get("properties", {}).get("name")
                if isinstance(crs, dict) and isinstance(crs.get("properties"), dict)
                else None)
    if source == "kgg":
        if declared != "EPSG:4326" or not all(-180 <= lon <= 180 and
                                              -90 <= lat <= 90 for lon, lat in positions):
            raise WfsSampleError("KGG sample missing/invalid source-declared EPSG:4326")
        coordinate_status = "declared_wgs84_position_range_checked"
    else:
        # Stadt Koeln's tree WFS advertises EPSG:25832 as default. Original
        # GeoJSON has been observed with *no* CRS and metre-like coordinates,
        # even when a client explicitly requests EPSG:4326. Require a plausible
        # projected envelope while keeping every result non-admitted.
        if not all(250_000 <= x <= 500_000 and 5_550_000 <= y <= 5_750_000
                   for x, y in positions):
            raise WfsSampleError("tree coordinates do not fit NRW UTM32 hypothesis")
        number = properties.get("Baumnummer")
        if not isinstance(number, str) or not number.strip() or len(number) > 256:
            raise WfsSampleError("missing or invalid provider tree identifier")
        if declared not in (None, "EPSG:25832", "urn:ogc:def:crs:EPSG::25832"):
            raise WfsSampleError("tree GeoJSON CRS conflicts with metre coordinates")
        coordinate_status = "projected_epsg25832_hypothesis_only_not_model_approved"

    keys = sorted(properties)
    return {
        "candidate_id": SOURCES[source]["candidate_id"],
        "source": source,
        "response_size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "feature_count": 1,
        "geometry_type": geom["type"],
        "geometry_position_count": len(positions),
        "property_field_count": len(keys),
        "property_keys_sha256": hashlib.sha256(
            json.dumps(keys, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "tree_identifier_sha256": (
            hashlib.sha256(properties["Baumnummer"].encode("utf-8")).hexdigest()
            if source == "tree" else None
        ),
        "source_order": "Baumnummer_ascending" if source == "tree" else "unfixed",
        "source_crs_declaration": declared or "not_declared",
        "coordinate_status": coordinate_status,
        "model_admitted": False,
        "independent_science_verified": False,
        "external_bytes_persisted": False,
        "verified_live": False,
    }


def probe_live(source: str) -> dict[str, object]:
    if source not in SOURCES:
        raise WfsSampleError("unsupported source")
    url = str(SOURCES[source]["url"])
    request = Request(url, headers={
        "Accept": "application/json,application/geo+json",
        "User-Agent": "OpenCatastrophe-data-WFS-one-feature-preflight/1",
    }, method="GET")
    try:
        with build_opener(DenyRedirects).open(request, timeout=20) as response:
            if response.status != 200 or response.geturl() != url:
                raise WfsSampleError("HTTP status/redirect refused")
            if response.headers.get_content_type().lower() not in {
                "application/json", "application/geo+json"
            }:
                raise WfsSampleError("unrecognized GeoJSON media type")
            announced = response.headers.get("Content-Length")
            if announced is not None and int(announced) > MAX_RESPONSE_BYTES:
                raise WfsSampleError("source response too large")
            payload = response.read(MAX_RESPONSE_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        raise WfsSampleError("fixed network/data-size boundary failed") from exc
    receipt = inspect_geojson(payload, source)
    receipt.update({
        "provider_url": url,
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "verified_live": True,
    })
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=tuple(SOURCES), required=True)
    parser.add_argument("--live", action="store_true", help="explicit one-feature public source request")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("offline by default; use --live for one source feature")
    try:
        print(json.dumps(probe_live(args.source), sort_keys=True))
        return 0
    except WfsSampleError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
