# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed, fixed-target NLD Embankments metadata and height-unit canary.

No feature values, geometry, elevations, identifiers, credentials or provider
source bytes are retained. This is not a source admission or a height conversion.
Manual: python -m research_runners.probe_nld_embankment_vertical_metadata_v0 --live
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import urllib.error
import urllib.request

SOURCE_ID = "us.usace.nld.public-embankments.2026"
METADATA_URL = (
    "https://geospatial.sec.usace.army.mil/dls/rest/services/"
    "NLD/Public/FeatureServer/11?f=pjson"
)
SPEC_URL = "https://levees.sec.usace.army.mil/data-services/dictionary/"
# Reviewed official dictionary 2026-11-15. A dictionary version change requires
# human reconciliation; this literal is not a dynamic assertion of source bytes.
DICTIONARY_REFERENCE_UNIT = "international-foot"
MAX_BYTES = 65536
TIMEOUT_SECONDS = 15


class PreflightError(ValueError):
    """Reject ambiguous original layer metadata without inferring model fitness."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise PreflightError("redirect not permitted")


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise PreflightError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value):
    raise PreflightError("non-finite JSON number")


def _finite_json_float(token: str) -> float:
    # json.loads accepts e.g. 1e999 as float('inf') unless explicitly checked.
    value = float(token)
    if not math.isfinite(value):
        raise PreflightError("non-finite JSON number")
    return value


def validate_metadata(raw: bytes) -> dict[str, str | bool]:
    if not raw or len(raw) > MAX_BYTES:
        raise PreflightError("empty or oversized original metadata")
    if raw.lstrip().startswith(b"<"):
        raise PreflightError("HTML or XML is not ArcGIS JSON")
    try:
        data = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_pairs,
            parse_constant=_reject_constant,
            parse_float=_finite_json_float,
        )
    except PreflightError:
        raise
    except (UnicodeError, ValueError) as exc:
        raise PreflightError("invalid JSON metadata") from exc
    if not isinstance(data, dict) or "error" in data:
        raise PreflightError("ArcGIS error or non-object metadata")
    required = {
        "id": 11,
        "name": "Embankments",
        "type": "Feature Layer",
        "geometryType": "esriGeometryPolyline",
        "hasZ": True,
        "hasM": False,
        "objectIdField": "OBJECTID",
        "isDataVersioned": True,
        "isDataArchived": False,
    }
    for key, expected in required.items():
        if type(data.get(key)) is not type(expected) or data[key] != expected:
            raise PreflightError("unexpected source identity or versioning: " + key)
    archive = data.get("archivingInfo")
    if not isinstance(archive, dict) or archive.get("supportsQueryWithHistoricMoment") is not False:
        raise PreflightError("historical query support changed or unknown")
    source_sr = data.get("sourceSpatialReference")
    if (not isinstance(source_sr, dict)
            or type(source_sr.get("wkid")) is not int
            or source_sr["wkid"] != 4269):
        raise PreflightError("unexpected horizontal CRS")
    height = data.get("heightModelInfo")
    source_height = data.get("sourceHeightModelInfo")
    expected_height = {
        "heightModel": "gravity_related_height",
        "vertCRS": "NAVD88_height_(ftUS)",
        "heightUnit": "us-foot",
    }
    for field_name, entry in (("heightModelInfo", height), ("sourceHeightModelInfo", source_height)):
        if not isinstance(entry, dict):
            raise PreflightError(field_name + " missing")
        for key, expected in expected_height.items():
            if entry.get(key) != expected:
                raise PreflightError(field_name + " unexpected " + key)
    fields = data.get("fields")
    if not isinstance(fields, list) or not fields or any(not isinstance(x, dict) for x in fields):
        raise PreflightError("invalid layer field schema")
    field_names = [x.get("name") for x in fields]
    if any(not isinstance(name, str) for name in field_names) or len(set(field_names)) != len(field_names):
        raise PreflightError("duplicate or invalid field identities")
    typed = {x["name"]: x.get("type") for x in fields}
    for name, kind in {
        "OBJECTID": "esriFieldTypeOID",
        "EMBANK_ID": "esriFieldTypeDouble",
        "SEGMENT_ID": "esriFieldTypeDouble",
        "SYSTEM_ID": "esriFieldTypeDouble",
        "SURVEY_DATE": "esriFieldTypeDate",
    }.items():
        if typed.get(name) != kind:
            raise PreflightError("required source field schema changed: " + name)
    if expected_height["heightUnit"] == DICTIONARY_REFERENCE_UNIT:
        raise PreflightError("dictionary and service discrepancy unexpectedly absent; re-review exact version")
    return {
        "source_id": SOURCE_ID,
        "shape": "metadata_only_no_feature_or_geometry",
        "horizontal_crs": "EPSG:4269",
        "vertical_crs": expected_height["vertCRS"],
        "service_height_unit": expected_height["heightUnit"],
        "current_dictionary_reference_unit": DICTIONARY_REFERENCE_UNIT,
        "unit_conflict_unresolved": True,
        "service_is_data_versioned": True,
        "historic_snapshot_supported": False,
        "elevation_values_examined": False,
        "data_persisted": False,
        "model_admitted": False,
    }


def get_original_metadata(opener=None) -> dict[str, str | bool]:
    if opener is None:
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), NoRedirect()
        )
    request = urllib.request.Request(
        METADATA_URL,
        headers={"Accept": "application/json", "User-Agent": "OpenCatastrophe-NLD-metadata-canary/1.0"},
        method="GET",
    )
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            if response.status != 200 or response.geturl() != METADATA_URL:
                raise PreflightError("original source URL or status changed")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise PreflightError("unexpected compressed metadata")
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if content_type not in ("application/json", "text/plain"):
                raise PreflightError("unexpected response content type")
            declared = response.headers.get("Content-Length")
            if declared is not None and (
                type(declared) is not str or not declared.isascii()
                or not declared.isdecimal() or len(declared) > len(str(MAX_BYTES))
                or int(declared) > MAX_BYTES
            ):
                raise PreflightError("invalid original metadata Content-Length")
            raw = response.read(MAX_BYTES + 1)
            if declared is not None and len(raw) != int(declared):
                raise PreflightError("original metadata Content-Length mismatch")
    except (OSError, urllib.error.URLError) as exc:
        raise PreflightError("original metadata transport failure") from exc
    summary = validate_metadata(raw)
    summary["original_response_sha256"] = hashlib.sha256(raw).hexdigest()
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Run one fixed provider metadata GET")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("offline by default; opt in to the single original metadata GET with --live")
    print(json.dumps(get_original_metadata(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
