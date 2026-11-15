# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline original-byte preflight for one pinned Natural Earth 110m Countries GeoJSON.

The publisher's GitHub repository stores this exact source blob at the pinned
commit, alongside ne_110m_admin_0_countries.VERSION.txt = 5.1.1.
A passing result is a structural CONTEXT screen, not CAT model admission.
No network requests, raw-data persistence or derived-data publication.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any

SOURCE_ID = "naturalearth.public-domain.admin-geography"
GITHUB_REPOSITORY = "nvkelso/natural-earth-vector"
GITHUB_COMMIT = "ca96624a56bd078437bca8184e78163e5039ad19"
GITHUB_PATH = "geojson/ne_110m_admin_0_countries.geojson"
PRODUCT_VERSION = "5.1.1"
ORIGINAL_SHA256 = "6866c877d39cba9c357620878839b336d569f8c662d3cfab4cb1dbe2d39c977f"
ORIGINAL_BYTES = 838726
EXPECTED_FEATURES = 177
EXPECTED_MISSING_ISO2 = 5
MAX_BYTES = 1024 * 1024
ADM0_ID_RE = re.compile(r"^[A-Z0-9]{3}$")


class GeojsonBlocked(ValueError):
    """Reject invalid identity, framing, attributes or polygon coordinate structure."""


def _reject_constant(value: str) -> None:
    raise GeojsonBlocked("non-finite JSON number is not allowed")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise GeojsonBlocked("duplicate JSON object key")
        obj[key] = value
    return obj


def _require_object(value: Any, name: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise GeojsonBlocked(f"{name}: expected JSON object")
    return value


def _screen_ring(ring: Any) -> int:
    if type(ring) is not list or len(ring) < 4:
        raise GeojsonBlocked("polygon ring must have at least four coordinates")
    for point in ring:
        if type(point) is not list or len(point) != 2:
            raise GeojsonBlocked("coordinate must be a two-component array")
        lon, lat = point
        if (type(lon) not in {int, float} or type(lat) not in {int, float}
                or not math.isfinite(lon) or not math.isfinite(lat)
                or not -180 <= lon <= 180 or not -90 <= lat <= 90):
            raise GeojsonBlocked("invalid lon/lat coordinate")
    if ring[0] != ring[-1]:
        raise GeojsonBlocked("polygon ring is not closed")
    return len(ring)


def _screen_polygon(polygon: Any) -> tuple[int, int]:
    if type(polygon) is not list or not polygon:
        raise GeojsonBlocked("polygon must contain at least one ring")
    return len(polygon), sum(_screen_ring(ring) for ring in polygon)


def inspect_original_geojson(raw: bytes, *, require_pinned_identity: bool = True) -> dict[str, object]:
    """Verify original bytes and minimal polygon/ID semantics without modifying them.

    Setting require_pinned_identity=False is only for independently synthetic
    fixtures; it never establishes the pinned provider-product identity.
    """
    if type(raw) is not bytes or not 2 <= len(raw) <= MAX_BYTES:
        raise GeojsonBlocked("invalid or oversized original-byte input")
    digest = hashlib.sha256(raw).hexdigest()
    if require_pinned_identity and (len(raw) != ORIGINAL_BYTES or digest != ORIGINAL_SHA256):
        raise GeojsonBlocked("unexpected original provider GeoJSON byte identity")
    try:
        decoded = raw.decode("utf-8")
        root = json.loads(decoded, object_pairs_hook=_reject_duplicate_keys, parse_constant=_reject_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise GeojsonBlocked("invalid original UTF-8 JSON") from exc
    root = _require_object(root, "root")
    if root.get("type") != "FeatureCollection" or type(root.get("features")) is not list:
        raise GeojsonBlocked("expected GeoJSON FeatureCollection")
    features = root["features"]
    if not features or len(features) > 1000:
        raise GeojsonBlocked("unreasonable feature count")
    seen_codes: set[str] = set()
    geometry_types: dict[str, int] = {}
    missing_iso2 = ring_count = coordinate_pairs = 0
    for feature in features:
        feature = _require_object(feature, "feature")
        if feature.get("type") != "Feature":
            raise GeojsonBlocked("unexpected GeoJSON feature type")
        props = _require_object(feature.get("properties"), "properties")
        code = props.get("ADM0_A3")
        if type(code) is not str or not ADM0_ID_RE.fullmatch(code):
            raise GeojsonBlocked("missing or invalid ADM0_A3 identifier")
        if code in seen_codes:
            raise GeojsonBlocked("duplicate ADM0_A3 identifier")
        seen_codes.add(code)
        iso2 = props.get("ISO_A2")
        if type(iso2) is not str:
            raise GeojsonBlocked("invalid ISO_A2 type; preserve source sentinel")
        if iso2 == "-99":
            missing_iso2 += 1
        elif not re.fullmatch(r"[A-Z]{2}", iso2):
            raise GeojsonBlocked("unexpected ISO_A2 value")
        geom = _require_object(feature.get("geometry"), "geometry")
        kind, coordinates = geom.get("type"), geom.get("coordinates")
        if kind == "Polygon":
            polygons = [coordinates]
        elif kind == "MultiPolygon":
            if type(coordinates) is not list or not coordinates:
                raise GeojsonBlocked("MultiPolygon must contain polygons")
            polygons = coordinates
        else:
            raise GeojsonBlocked("unsupported non-polygon feature")
        geometry_types[kind] = geometry_types.get(kind, 0) + 1
        for polygon in polygons:
            rings, pairs = _screen_polygon(polygon)
            ring_count += rings
            coordinate_pairs += pairs

    if require_pinned_identity and (len(features) != EXPECTED_FEATURES
                                    or missing_iso2 != EXPECTED_MISSING_ISO2
                                    or coordinate_pairs != 10654):
        raise GeojsonBlocked("pinned source scientific inventory drift")
    return {
        "source_id": SOURCE_ID,
        "product_version": PRODUCT_VERSION if require_pinned_identity else "synthetic_only",
        "provider_repository": GITHUB_REPOSITORY if require_pinned_identity else None,
        "provider_commit": GITHUB_COMMIT if require_pinned_identity else None,
        "provider_path": GITHUB_PATH if require_pinned_identity else None,
        "original_sha256": digest,
        "original_bytes": len(raw),
        "feature_count": len(features),
        "unique_adm0_a3": len(seen_codes),
        "missing_iso2_sentinel_count": missing_iso2,
        "polygon_ring_count": ring_count,
        "coordinate_pair_count": coordinate_pairs,
        "geometry_type_counts": geometry_types,
        "original_bytes_persisted": False,
        "model_input_admitted": False,
        "scope": "source_geometry_structure_only_not_topology_or_cat_validation",
    }
