# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Manual-only, bounded original ArcGIS flood-defence one-record canary.

Only source-provided OBJECTID is read (without geometry), never stored or
printed. This script does not authorize source admission, CAT input or Neon writes.
Run: python -m research_runners.probe_aims_nld_flood_defences_v0 --live\nRun one: python -m research_runners.probe_aims_nld_flood_defences_v0 --live --source uk.ea.aims.spatial-flood-defences.2026
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.request
from dataclasses import dataclass

MAX_BYTES = 8192
TIMEOUT_SECONDS = 15


@dataclass(frozen=True)
class Target:
    source_id: str
    url: str
    oid: str
    wkid: int


TARGETS = (
    Target(
        "uk.ea.aims.spatial-flood-defences.2026",
        "https://environment.data.gov.uk/arcgis/rest/services/EA/"
        "SpatialFloodDefencesIncStandardisedAttributes/FeatureServer/0/query"
        "?where=1%3D1&outFields=objectid&returnGeometry=false&resultRecordCount=1&f=json",
        "objectid",
        27700,
    ),
    Target(
        "us.usace.nld.public-floodwalls.2026",
        "https://geospatial.sec.usace.army.mil/dls/rest/services/"
        "NLD/Public/FeatureServer/12/query"
        "?where=1%3D1&outFields=OBJECTID&returnGeometry=false&resultRecordCount=1&f=json",
        "OBJECTID",
        4269,
    ),
)


class ProbeFailure(ValueError):
    """Fail closed on transport, shape, identity or boundedness problems."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProbeFailure("redirect forbidden")


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProbeFailure("duplicate JSON member")
        result[key] = value
    return result


def _reject_constant(value):
    raise ProbeFailure("non-finite JSON number")


def validate_payload(raw: bytes, target: Target) -> dict[str, str | int]:
    if not raw or len(raw) > MAX_BYTES:
        raise ProbeFailure("empty or oversized provider response")
    if raw.lstrip().startswith((b"<", b"<!")):
        raise ProbeFailure("HTML/XML is not ArcGIS JSON")
    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_pairs, parse_constant=_reject_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ProbeFailure("not valid UTF-8 JSON") from exc
    if not isinstance(data, dict) or "error" in data:
        raise ProbeFailure("ArcGIS error or non-object response")
    if data.get("objectIdFieldName") != target.oid or data.get("geometryType") != "esriGeometryPolyline":
        raise ProbeFailure("unexpected layer identity or geometry type")
    spatial_ref = data.get("spatialReference")
    if not isinstance(spatial_ref, dict) or spatial_ref.get("wkid") != target.wkid:
        raise ProbeFailure("unexpected source CRS")
    fields = data.get("fields")
    if not isinstance(fields, list) or len(fields) != 1 or not isinstance(fields[0], dict):
        raise ProbeFailure("unexpected fields selection")
    if fields[0].get("name") != target.oid or fields[0].get("type") != "esriFieldTypeOID":
        raise ProbeFailure("unexpected OID column")
    features = data.get("features")
    if not isinstance(features, list) or len(features) != 1 or not isinstance(features[0], dict):
        raise ProbeFailure("exactly one record required")
    if "geometry" in features[0]:
        raise ProbeFailure("geometry returned despite no-geometry contract")
    attrs = features[0].get("attributes")
    if not isinstance(attrs, dict) or set(attrs) != {target.oid}:
        raise ProbeFailure("unexpected record attributes")
    if type(attrs[target.oid]) is not int or attrs[target.oid] < 0:
        raise ProbeFailure("invalid OBJECTID")
    if "exceededTransferLimit" in data and type(data["exceededTransferLimit"]) is not bool:
        raise ProbeFailure("invalid transfer-limit marker")
    return {"source_id": target.source_id, "shape": "one_oid_no_geometry", "wkid": target.wkid}


def get_one(target: Target, opener=None) -> dict[str, str | int]:
    if opener is None:
        # Do not use environment proxies, redirects, credentials or retries.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    request = urllib.request.Request(
        target.url, headers={"Accept": "application/json", "User-Agent": "OpenCatastrophe-research-canary/1.0"},
        method="GET",
    )
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            if response.status != 200 or response.geturl() != target.url:
                raise ProbeFailure("unexpected HTTP status or response URL")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise ProbeFailure("compressed responses forbidden")
            content_type = response.headers.get("Content-Type", "").lower()
            if not (content_type.startswith("application/json") or content_type.startswith("text/plain")):
                raise ProbeFailure("unexpected content type")
            body = response.read(MAX_BYTES + 1)
    except (OSError, urllib.error.URLError) as exc:
        raise ProbeFailure("network read failed") from exc
    summary = validate_payload(body, target)
    # SHA refers only to this exact transient original HTTP entity; no raw response is persisted.
    summary["original_response_sha256"] = hashlib.sha256(body).hexdigest()
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Opt in to original bounded provider reads")
    parser.add_argument(
        "--source", choices=tuple(target.source_id for target in TARGETS),
        help="Select exactly one of the two compile-time fixed provider contracts",
    )
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("offline by default; use --live for fixed bounded source GETs")
    selected = tuple(target for target in TARGETS if args.source in (None, target.source_id))
    for target in selected:
        result = get_one(target)
        print(json.dumps({**result, "data_persisted": False, "model_admitted": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
