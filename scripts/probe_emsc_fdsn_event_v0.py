# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One-event, no-persistence EMSC FDSN JSON connectivity probe.

Only the exact reviewed source-access contract's latest_event_json operation
is executable. No arbitrary target, query, date range, HTTP headers, token,
event export or model ingestion is provided.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import ssl
import sys
from typing import Any, Callable
from urllib import error, request

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.validate_source_access import validate_path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "access" / "emsc.seismicportal.fdsn-event.json"
PROBE_URL = (
    "https://www.seismicportal.eu/fdsnws/event/1/query"
    "?format=json&limit=1&orderby=time&nodata=204"
    "&includeallorigins=false&includearrivals=false"
)
MAX_RESPONSE_BYTES = 1_048_576
TIMEOUT_SECONDS = 30
PROFILE = "oc-emsc-fdsn-latest-event-connectivity-v0"


class EMSCProbeError(ValueError):
    """A source contract, network or bounded response gate failed."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EMSCProbeError("duplicate JSON property in provider response")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise EMSCProbeError("non-finite JSON number in provider response")


def verify_frozen_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    contract = validate_path(path)
    if (
        contract["access_id"] != "emsc.seismicportal.fdsn-event"
        or contract["source_ids"] != ["emsc.seismicportal.fdsn-event"]
        or contract["service_root"] != "https://www.seismicportal.eu"
        or contract["interface_type"] != "fdsn"
        or contract["status"] != "probe_ready"
        or contract["authentication"]["mode"] != "none"
        or contract["probe_contract"]["operation"] != "latest_event_json"
        or contract["probe_contract"]["mode"] != "catalogue_query"
        or contract["probe_contract"]["requires_credentials"] is not False
        or contract["request_contract"]["allowed_operations"] != ["latest_event_json"]
        or contract["request_contract"]["path_templates"] != ["/fdsnws/event/1/query"]
        or contract["rights_and_policy"]["dataset_rights_status"] != "verified"
        or contract["rights_and_policy"]["api_terms_status"] != "separate_reviewed"
        or contract["rights_and_policy"]["commercial_automation_status"] != "allowed"
        or contract["operational_constraints"]["max_probe_bytes"] != MAX_RESPONSE_BYTES
    ):
        raise EMSCProbeError("frozen EMSC probe contract is not approved for this operation")
    return contract


def inspect_json_bytes(raw: bytes) -> dict[str, Any]:
    """Validate provider GeoJSON shape without exporting event observations."""
    if type(raw) is not bytes or not (0 < len(raw) <= MAX_RESPONSE_BYTES):
        raise EMSCProbeError("provider payload is empty or outside the one-MiB limit")
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EMSCProbeError("provider response is not valid strict UTF-8 JSON") from exc
    if type(payload) is not dict or payload.get("type") != "FeatureCollection":
        raise EMSCProbeError("FDSN JSON must be a GeoJSON FeatureCollection")
    features = payload.get("features")
    if type(features) is not list or len(features) != 1:
        raise EMSCProbeError("probe must return exactly one event feature")
    feature = features[0]
    if type(feature) is not dict or feature.get("type") != "Feature":
        raise EMSCProbeError("provider event is not a GeoJSON Feature")
    geometry = feature.get("geometry")
    if type(geometry) is not dict or geometry.get("type") != "Point":
        raise EMSCProbeError("one-event geometry must be a Point")
    coords = geometry.get("coordinates")
    if type(coords) is not list or len(coords) not in (2, 3):
        raise EMSCProbeError("event coordinates must be a 2D or 3D position")
    if any(type(x) not in (int, float) or not math.isfinite(x) for x in coords):
        raise EMSCProbeError("event coordinates must be finite numbers, not booleans")
    if not (-180 <= coords[0] <= 180 and -90 <= coords[1] <= 90):
        raise EMSCProbeError("event coordinates outside WGS84 bounds")
    properties = feature.get("properties")
    if type(properties) is not dict or type(properties.get("source_id")) is not str or not properties["source_id"].strip():
        raise EMSCProbeError("event must have a non-empty provider source_id")
    return {"event_count": 1, "format": "geojson_feature_collection", "geometry": "Point"}


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise EMSCProbeError("redirect outside frozen EMSC source identity is forbidden")


def _open(request_obj: request.Request, timeout: int):
    opener = request.build_opener(
        request.ProxyHandler({}),
        NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    )
    return opener.open(request_obj, timeout=timeout)


def probe(
    *,
    open_request: Callable[[request.Request, int], Any] = _open,
    utc_clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    contract_path: Path = CONTRACT_PATH,
) -> dict[str, Any]:
    verify_frozen_contract(contract_path)
    req = request.Request(PROBE_URL, headers={"Accept": "application/json"}, method="GET")
    try:
        with open_request(req, TIMEOUT_SECONDS) as response:
            if response.geturl() != PROBE_URL:
                raise EMSCProbeError("unexpected response URL/redirect")
            status = response.status
            if type(status) is not int or status != 200:
                raise EMSCProbeError("source did not provide HTTP 200 one-event response")
            media_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media_type != "application/json":
                raise EMSCProbeError("unexpected EMSC response media type")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except EMSCProbeError:
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        raise EMSCProbeError("bounded EMSC provider request failed") from exc

    if len(raw) > MAX_RESPONSE_BYTES:
        raise EMSCProbeError("source returned more bytes than permitted")
    shape = inspect_json_bytes(raw)
    checked_at = utc_clock()
    if checked_at.tzinfo is None or checked_at.utcoffset() is None:
        raise EMSCProbeError("UTC receipt timestamp must be timezone-aware")
    return {
        "profile": PROFILE,
        "source_id": "emsc.seismicportal.fdsn-event",
        "source_access_contract": "access/emsc.seismicportal.fdsn-event.json",
        "retrieved_at_utc": checked_at.astimezone(timezone.utc).isoformat(),
        "request_url": PROBE_URL,
        "http_status": 200,
        "media_type": "application/json",
        "response_bytes": len(raw),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        **shape,
        "external_bytes_persisted": False,
        "model_input_admitted": False,
        "live_response_replayable_without_frozen_bytes": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="execute the exact one-event anonymous provider request")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("no network request by default; specify --live to run the frozen one-event probe")
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False, indent=2))
    except (EMSCProbeError, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
