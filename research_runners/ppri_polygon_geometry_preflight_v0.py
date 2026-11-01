# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed, offline original ArcGIS PPRI GeoJSON topology receipt.

No network or database writes. Bring independently acquired original bytes
from the exact public feature-query URL; do not commit provider geometry.
This is a research geometry check, NOT licence or flood-event admission.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from shapely.geometry import shape
from shapely.validation import explain_validity

HOST = "sig.seinegrandslacs.fr"
LAYER = "/arcgis/rest/services/Gestion_Eaux_Inondations_GP/MapServer/17/query"


def audit(raw: bytes, query_url: str, objectid: int) -> dict:
    parsed = urlsplit(query_url)
    opts = parse_qs(parsed.query)
    if parsed.scheme != "https" or parsed.hostname != HOST or parsed.path != LAYER:
        raise ValueError("source URL must be the exact approved ArcGIS layer")
    if opts.get("f", [""])[0].lower() != "geojson":
        raise ValueError("GeoJSON response format required")
    if opts.get("returnGeometry", [""])[0].lower() != "true" or opts.get("outSR", [""])[0] != "4326":
        raise ValueError("must request geometry in WGS84")
    if opts.get("where", [""])[0].replace(" ", "").lower() != f"objectid={objectid}":
        raise ValueError("query must select exactly the declared objectid")
    if not raw:
        raise ValueError("empty provider response")
    try:
        obj = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("invalid JSON/UTF-8 provider bytes") from exc
    if obj.get("type") != "FeatureCollection" or len(obj.get("features", [])) != 1:
        raise ValueError("require exactly one feature, no more and no fewer")
    feature = obj["features"][0]
    if feature.get("type") != "Feature" or feature.get("id") != objectid:
        raise ValueError("wrong feature identity")
    properties = feature.get("properties")
    if not isinstance(properties, dict) or properties.get("objectid") != objectid:
        raise ValueError("source objectid property mismatch")
    geometry = feature.get("geometry")
    if not isinstance(geometry, dict) or geometry.get("type") not in ("Polygon", "MultiPolygon"):
        raise ValueError("polygon/multipolygon required")
    geom = shape(geometry)
    if geom.is_empty:
        raise ValueError("empty polygon")
    bounds = list(map(float, geom.bounds))
    if not all(math.isfinite(v) for v in bounds):
        raise ValueError("non-finite coordinates")
    # These bounds cover only a small Paris-area research pilot. Do not use
    # this restriction as a global PPRI validator.
    if not (1 <= bounds[0] <= bounds[2] <= 4 and 47 <= bounds[1] <= bounds[3] <= 50):
        raise ValueError("unexpected geographic bounds")
    simplified = ("maxAllowableOffset" in opts
                  or "geometryPrecision" in opts
                  or "quantizationParameters" in opts)
    valid = bool(geom.is_valid)
    return {
        "contract": "OC-PPRI-POLYGON-TOPOLOGY-PREFLIGHT-0.1",
        "source_objectid": objectid,
        "source_zone_code": properties.get("code_zone"),
        "source_response_sha256": hashlib.sha256(raw).hexdigest(),
        "source_response_bytes": len(raw),
        "geometry_type": geom.geom_type,
        "bounding_box_wgs84": bounds,
        "topology_valid": valid,
        "topology_validation_reason": explain_validity(geom),
        "geometry_request_simplified_or_rounded": simplified,
        "unsimplified_requested_geometry_topology_valid": valid and not simplified,
        "safe_for_precise_spatial_overlay": valid and not simplified,
        "licence_reviewed": False,
        "historical_2016_flood_footprint": False,
        "insured_loss_observed": False,
        "cat_model_admitted": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-file", required=True, type=Path)
    parser.add_argument("--query-url", required=True)
    parser.add_argument("--objectid", type=int, required=True)
    args = parser.parse_args()
    try:
        report = audit(args.source_file.read_bytes(), args.query_url, args.objectid)
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc), "topology_valid": False,
                          "safe_for_precise_spatial_overlay": False,
                          "cat_model_admitted": False}, sort_keys=True))
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["safe_for_precise_spatial_overlay"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
