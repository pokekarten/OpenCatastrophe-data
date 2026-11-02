#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fixed NOAA CO-OPS water-level probe; metadata receipt only, no data export.

One station, one historical UTC day, one tidal datum, and a fixed query.
Run with --live explicitly. Neither the request nor a successful observation
is a hazard map, verified event intensity, insurer exposure or model admission.
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
CONTRACT_PATH = ROOT / "access" / "noaa.coops.water-levels.json"
PARAMETERS = (
    ("begin_date", "20260101"),
    ("end_date", "20260101"),
    ("station", "9414290"),
    ("product", "water_level"),
    ("datum", "MLLW"),
    ("time_zone", "gmt"),
    ("units", "metric"),
    ("application", "OpenCatastrophe"),
    ("format", "json"),
)
URL = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?" + "&".join(
    key + "=" + value for key, value in PARAMETERS
)
MAX_BYTES = 1_048_576
TIMEOUT_SECONDS = 30
PROFILE = "oc-noaa-coops-sf-20260101-water-level-v0"


class COOPSProbeError(ValueError):
    """An explicit preflight, contract or response invariant failed."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise COOPSProbeError("duplicate provider JSON property")
        obj[key] = value
    return obj


def _reject_nonfinite(value: str) -> None:
    raise COOPSProbeError("non-finite JSON value")


def verify_frozen_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    contract = validate_path(path)
    rights = contract["rights_and_policy"]
    probe_contract = contract["probe_contract"]
    if (
        contract["access_id"] != "noaa.coops.water-levels"
        or contract["source_ids"] != ["noaa.coops.water-levels"]
        or contract["interface_type"] != "rest"
        or contract["status"] != "probe_ready"
        or contract["service_root"] != "https://api.tidesandcurrents.noaa.gov"
        or contract["authentication"]["mode"] != "none"
        or contract["request_contract"]["allowed_operations"] != ["bounded_water_level_observations"]
        or contract["request_contract"]["path_templates"] != ["/api/prod/datagetter"]
        or probe_contract["mode"] != "provider_specific"
        or probe_contract["operation"] != "bounded_water_level_observations"
        or probe_contract["requires_credentials"] is not False
        or rights["dataset_rights_status"] != "verified"
        or rights["api_terms_status"] != "separate_reviewed"
        or rights["commercial_automation_status"] != "allowed"
        or contract["operational_constraints"]["max_probe_bytes"] != MAX_BYTES
        or contract["operational_constraints"]["timeout_seconds"] != TIMEOUT_SECONDS
        or any(
            key + "=" + value not in contract["request_contract"]["parameter_rules"]
            for key, value in PARAMETERS
        )
    ):
        raise COOPSProbeError("NOAA fixed probe is not permitted by the reviewed contract")
    return contract


def _finite(text: Any, *, field: str) -> float:
    if type(text) is not str or not text.strip():
        raise COOPSProbeError(field + " must be a numeric string")
    try:
        value = float(text)
    except ValueError as exc:
        raise COOPSProbeError(field + " must be numeric") from exc
    if not math.isfinite(value):
        raise COOPSProbeError(field + " must be finite")
    return value


def inspect_json_bytes(raw: bytes) -> dict[str, Any]:
    """Check station identity, UTC time, flags and measurement shape only."""
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise COOPSProbeError("empty or oversized provider response")
    try:
        data = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise COOPSProbeError("response is not strict UTF-8 JSON") from exc
    if type(data) is not dict or "error" in data:
        raise COOPSProbeError("provider returned an error or non-object")
    metadata = data.get("metadata")
    if type(metadata) is not dict or metadata.get("id") != "9414290":
        raise COOPSProbeError("unexpected station identity")
    if type(metadata.get("name")) is not str or not metadata["name"].strip():
        raise COOPSProbeError("station name missing")
    lat = _finite(metadata.get("lat"), field="station latitude")
    lon = _finite(metadata.get("lon"), field="station longitude")
    if not (30 <= lat <= 45 and -130 <= lon <= -115):
        raise COOPSProbeError("station location outside San Francisco region")
    observations = data.get("data")
    if type(observations) is not list or not 1 <= len(observations) <= 240:
        raise COOPSProbeError("expected at most one day of 6-minute observations")
    previous: datetime | None = None
    for item in observations:
        if type(item) is not dict:
            raise COOPSProbeError("observation must be an object")
        stamp = item.get("t")
        if type(stamp) is not str:
            raise COOPSProbeError("observation timestamp missing")
        try:
            instant = datetime.strptime(stamp, "%Y-%m-%d %H:%M")
        except ValueError as exc:
            raise COOPSProbeError("invalid observation timestamp") from exc
        if (instant.strftime("%Y-%m-%d") != "2026-01-01"
                or instant.minute % 6 != 0
                or (previous is not None and instant <= previous)):
            raise COOPSProbeError("observation outside frozen UTC day or time ordering")
        previous = instant
        _finite(item.get("v"), field="water-level height")
        if type(item.get("f")) is not str or not item["f"].strip():
            raise COOPSProbeError("provider data flags missing")
        if type(item.get("q")) is not str or not item["q"].strip():
            raise COOPSProbeError("provider quality flag missing")
    return {
        "station_id": "9414290",
        "utc_day": "2026-01-01",
        "datum": "MLLW",
        "unit": "m",
        "observation_rows": len(observations),
        "provider_quality_flags_present": True,
        "quality_scientifically_assessed": False,
    }


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise COOPSProbeError("provider redirect forbidden by fixed contract")


def _open(req: request.Request, timeout: int):
    opener = request.build_opener(
        request.ProxyHandler({}),
        NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    )
    return opener.open(req, timeout=timeout)


def probe(
    *,
    open_request: Callable[[request.Request, int], Any] = _open,
    utc_clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    contract_path: Path = CONTRACT_PATH,
) -> dict[str, Any]:
    verify_frozen_contract(contract_path)
    req = request.Request(URL, headers={"Accept": "application/json"}, method="GET")
    try:
        with open_request(req, TIMEOUT_SECONDS) as response:
            if response.geturl() != URL or type(response.status) is not int or response.status != 200:
                raise COOPSProbeError("unexpected HTTP status or redirect")
            media = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media != "application/json":
                raise COOPSProbeError("unexpected provider response media type")
            raw = response.read(MAX_BYTES + 1)
    except COOPSProbeError:
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        raise COOPSProbeError("bounded NOAA request failed") from exc
    summary = inspect_json_bytes(raw)
    now = utc_clock()
    if now.tzinfo is None or now.utcoffset() is None:
        raise COOPSProbeError("receipt clock must be timezone-aware")
    return {
        "profile": PROFILE,
        "source_access_contract": "access/noaa.coops.water-levels.json",
        "retrieved_at_utc": now.astimezone(timezone.utc).isoformat(),
        "request_url": URL,
        "http_status": 200,
        "media_type": "application/json",
        "response_bytes": len(raw),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        **summary,
        "original_bytes_persisted": False,
        "model_input_admitted": False,
        "insured_exposure_inferred": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="run exact one-day NOAA sample; no raw output")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("no network request by default; use --live")
    try:
        print(json.dumps(probe(), indent=2, sort_keys=True, allow_nan=False))
    except (COOPSProbeError, OSError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
