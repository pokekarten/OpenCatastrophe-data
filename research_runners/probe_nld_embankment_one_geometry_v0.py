# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Research-only, one-feature original USACE NLD Embankments Z-coverage canary.

An explicit --live opt-in reads exactly one public layer-11 feature with 3D
polyline geometry from a fixed provider URL. Only counts, blockers and the
transient HTTP entity SHA-256 are emitted. No coordinates, identifiers, source
geometry/Z ordinates or provider response bytes are persisted or printed.
This does not certify crest heights, units, protection or model admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import urllib.error
import urllib.request

SOURCE_ID = "us.usace.nld.public-embankments.2026"
QUERY_URL = (
    "https://geospatial.sec.usace.army.mil/dls/rest/services/"
    "NLD/Public/FeatureServer/11/query"
    "?where=1%3D1&outFields=OBJECTID%2CEMBANK_ID"
    "&returnGeometry=true&returnZ=true&returnM=false"
    "&resultRecordCount=1&orderByFields=OBJECTID&outSR=4269&f=json"
)
MAX_BYTES = 32768
MAX_VERTICES = 4096
MAX_PATHS = 64
TIMEOUT_SECONDS = 15
# JSON doubles cannot preserve consecutive integer identifiers above 2**53-1.
MAX_EXACT_JSON_INTEGER_ID = (1 << 53) - 1


class GeometryCanaryError(ValueError):
    """Fail closed if original response violates the bounded geometry contract."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise GeometryCanaryError("redirect forbidden")


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise GeometryCanaryError("duplicate JSON member")
        result[key] = value
    return result


def _reject_constant(value):
    raise GeometryCanaryError("non-finite JSON number")


def _finite_number(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, ValueError):
        # Legal JSON integers can be bigger than Python's float range.
        return False


def _exact_double_join_id(value):
    # The ArcGIS schema stores EMBANK_ID as Double, but this is an identity
    # *join key*, not a physical measurement. A fraction or >53-bit integer
    # cannot be losslessly represented as a JSON double identifier.
    return (type(value) in (int, float)
            and 0 <= value <= MAX_EXACT_JSON_INTEGER_ID
            and _finite_number(value)
            and value == int(value))


def validate_geometry_response(raw: bytes) -> dict[str, object]:
    if not raw or len(raw) > MAX_BYTES:
        raise GeometryCanaryError("empty or oversized original response")
    if raw.lstrip().startswith(b"<"):
        raise GeometryCanaryError("HTML/XML instead of JSON")
    try:
        data = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_pairs,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise GeometryCanaryError("invalid JSON source response") from exc
    if not isinstance(data, dict) or "error" in data:
        raise GeometryCanaryError("unexpected ArcGIS response or error")
    if data.get("objectIdFieldName") != "OBJECTID":
        raise GeometryCanaryError("wrong feature identity")
    if data.get("geometryType") != "esriGeometryPolyline":
        raise GeometryCanaryError("wrong geometry type")
    sr = data.get("spatialReference")
    if not isinstance(sr, dict) or type(sr.get("wkid")) is not int or sr["wkid"] != 4269:
        raise GeometryCanaryError("wrong horizontal CRS")
    fields = data.get("fields")
    if (
        not isinstance(fields, list)
        or len(fields) != 2
        or any(not isinstance(x, dict) for x in fields)
        or [(x.get("name"), x.get("type")) for x in fields] != [
            ("OBJECTID", "esriFieldTypeOID"),
            ("EMBANK_ID", "esriFieldTypeDouble"),
        ]
    ):
        raise GeometryCanaryError("wrong selected fields or types")
    features = data.get("features")
    if not isinstance(features, list) or len(features) != 1 or not isinstance(features[0], dict):
        raise GeometryCanaryError("not exactly one feature")
    if "exceededTransferLimit" in data and type(data["exceededTransferLimit"]) is not bool:
        raise GeometryCanaryError("invalid transfer-limit marker")
    feature = features[0]
    if set(feature) != {"attributes", "geometry"}:
        raise GeometryCanaryError("unexpected feature keys")
    attributes = feature["attributes"]
    if not isinstance(attributes, dict) or set(attributes) != {"OBJECTID", "EMBANK_ID"}:
        raise GeometryCanaryError("unexpected source attributes")
    oid = attributes["OBJECTID"]
    if type(oid) is not int or not 0 <= oid <= MAX_EXACT_JSON_INTEGER_ID:
        raise GeometryCanaryError("invalid OBJECTID")
    embank_id = attributes["EMBANK_ID"]
    if not _exact_double_join_id(embank_id):
        raise GeometryCanaryError("invalid EMBANK_ID")
    geom = feature["geometry"]
    if not isinstance(geom, dict) or geom.get("hasZ") is not True:
        raise GeometryCanaryError("missing 3D geometry declaration")
    if geom.get("hasM", False) is not False or set(geom) - {"hasZ", "hasM", "paths"}:
        raise GeometryCanaryError("unexpected dimensionality or geometry content")
    paths = geom.get("paths")
    if not isinstance(paths, list) or not 1 <= len(paths) <= MAX_PATHS:
        raise GeometryCanaryError("missing or excessive paths")
    vertices = 0
    z_present = 0
    z_missing = 0
    for path in paths:
        if not isinstance(path, list) or len(path) < 2:
            raise GeometryCanaryError("degenerate path")
        vertices += len(path)
        if vertices > MAX_VERTICES:
            raise GeometryCanaryError("too many vertices")
        for vertex in path:
            if not isinstance(vertex, list) or len(vertex) != 3:
                raise GeometryCanaryError("expected x,y,z with no measures")
            x, y, z = vertex
            if not (_finite_number(x) and _finite_number(y) and -180 <= x <= 180 and -90 <= y <= 90):
                raise GeometryCanaryError("unexpected horizontal ordinate")
            if z is None:
                z_missing += 1
            elif _finite_number(z):
                z_present += 1
            else:
                raise GeometryCanaryError("invalid Z ordinate")
    return {
        "source_id": SOURCE_ID,
        "shape": "one_original_3d_polyline_research_only",
        "horizontal_crs": "EPSG:4269",
        "one_feature": True,
        "path_count": len(paths),
        "vertex_count": vertices,
        "finite_z_count": z_present,
        "null_z_count": z_missing,
        "z_observed_not_crest_certified": z_present > 0,
        "vertical_units_resolved": False,
        "historical_snapshot_supported": False,
        "hydraulic_protection_validated": False,
        "source_bytes_persisted": False,
        "model_admitted": False,
    }


def get_one_original_geometry(opener=None) -> dict[str, object]:
    if opener is None:
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), NoRedirect()
        )
    request = urllib.request.Request(
        QUERY_URL,
        headers={"Accept": "application/json", "User-Agent": "OpenCatastrophe-NLD-one-geometry/1.0"},
        method="GET",
    )
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            if response.status != 200 or response.geturl() != QUERY_URL:
                raise GeometryCanaryError("unexpected original HTTP status or URL")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise GeometryCanaryError("compressed response forbidden")
            ctype = response.headers.get("Content-Type", "").lower()
            if not (ctype.startswith("application/json") or ctype.startswith("text/plain")):
                raise GeometryCanaryError("unexpected content type")
            raw = response.read(MAX_BYTES + 1)
    except (OSError, urllib.error.URLError) as exc:
        raise GeometryCanaryError("original provider request failed") from exc
    summary = validate_geometry_response(raw)
    summary["original_response_sha256"] = hashlib.sha256(raw).hexdigest()
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Opt into exactly one fixed original geometry GET")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("offline by default; use --live for exactly one bounded public source GET")
    print(json.dumps(get_one_original_geometry(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
