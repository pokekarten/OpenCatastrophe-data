#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One fixed byte-range of original NOAA GHCN-Daily station CSV; no persistence.

This is an *observation format preflight*, not a validated full station dataset,
not a tropical-storm/flood event and not an admitted CAT input. Network is
opt-in with --live; cannot change station, URL, headers, query or byte limit.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import ssl
import sys
from typing import Any, Callable
from urllib import error, request

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.validate_source_access import validate_path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "access" / "noaa.nodd.ghcnd-central-park-range.json"
URL = "https://noaa-ghcn-pds.s3.amazonaws.com/csv/by_station/USW00094728.csv"
STATION_ID = "USW00094728"
BYTE_LIMIT = 65_536
TIMEOUT = 30
PROFILE = "oc-ghcnd-central-park-64k-original-prefix-v0"
HEADER = ["ID", "DATE", "ELEMENT", "DATA_VALUE", "M_FLAG", "Q_FLAG", "S_FLAG", "OBS_TIME"]
# NOAA NODD currently serves this exact CSV object as binary/octet-stream.
MEDIA = {"application/octet-stream", "binary/octet-stream", "text/plain", "text/csv", "application/vnd.ms-excel"}
CONTENT_RANGE = re.compile(r"^bytes 0-65535/([1-9][0-9]*)$")
ELEMENT = re.compile(r"^[A-Z0-9]{4}$")
SIGNED_INTEGER = re.compile(r"^-?[0-9]{1,8}$")
FLAG = re.compile(r"^[A-Za-z0-9]?$")
CLOCK = re.compile(r"^[0-2][0-9][0-5][0-9]$")


class GHCNDStationProbeError(ValueError):
    """Provider response or exact source identity is invalid."""


def verify_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    contract = validate_path(path)
    if (
        contract["access_id"] != "noaa.nodd.ghcnd-central-park-range"
        or contract["source_ids"] != ["noaa.ncei.ghcn-daily"]
        or contract["status"] != "probe_ready"
        or contract["interface_type"] != "http_file"
        or contract["service_root"] != "https://noaa-ghcn-pds.s3.amazonaws.com"
        or contract["request_contract"]["allowed_operations"] != ["probe_fixed_station_range"]
        or contract["request_contract"]["path_templates"] != ["/csv/by_station/USW00094728.csv"]
        or contract["probe_contract"]["mode"] != "provider_specific"
        or contract["probe_contract"]["operation"] != "probe_fixed_station_range"
        or contract["probe_contract"]["requires_credentials"] is not False
        or contract["authentication"]["mode"] != "none"
        or contract["rights_and_policy"]["dataset_rights_status"] != "verified"
        or contract["rights_and_policy"]["api_terms_status"] != "same_as_dataset"
        or contract["rights_and_policy"]["commercial_automation_status"] != "allowed"
        or contract["operational_constraints"]["max_probe_bytes"] != BYTE_LIMIT
        or contract["operational_constraints"]["timeout_seconds"] != TIMEOUT
        or "Range: bytes=0-65535" not in contract["request_contract"]["parameter_rules"]
    ):
        raise GHCNDStationProbeError("reviewed station sample contract does not match exact code")
    return contract


def _read_prefix_lines(raw: bytes) -> tuple[list[str], bool]:
    if type(raw) is not bytes or len(raw) != BYTE_LIMIT:
        raise GHCNDStationProbeError("expected exactly 65536 original prefix bytes")
    if b"\x00" in raw:
        raise GHCNDStationProbeError("binary NUL in text station sample")
    # UTF-8 must be valid for all COMPLETE lines; the final byte range can
    # bisect a Unicode sequence and is never parsed as a complete record.
    end = raw.rfind(b"\n")
    if end < 1:
        raise GHCNDStationProbeError("no complete CSV line in prefix")
    try:
        decoded = raw[:end + 1].decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise GHCNDStationProbeError("complete provider CSV lines must be UTF-8") from exc
    lines = decoded.splitlines()
    if not lines or any(not line.strip() for line in lines):
        raise GHCNDStationProbeError("blank or empty provider CSV line")
    return lines, (end + 1 < len(raw))


def inspect_station_prefix(raw: bytes) -> dict[str, Any]:
    """Validate a full 64-KiB prefix, output aggregate fields only."""
    lines, truncated_tail = _read_prefix_lines(raw)
    try:
        rows = list(csv.reader(io.StringIO("\n".join(lines), newline=""), strict=True))
    except csv.Error as exc:
        raise GHCNDStationProbeError("malformed original station CSV") from exc
    if rows and rows[0] == HEADER:
        rows.pop(0)
    if not 50 <= len(rows) <= 3000:
        raise GHCNDStationProbeError("unexpected number of original daily element rows")
    seen: set[tuple[str, str]] = set()
    elements: set[str] = set()
    quality_flagged = 0
    source_flagged = 0
    measurement_flagged = 0
    dates: list[str] = []
    for i, row in enumerate(rows):
        if len(row) != 8:
            raise GHCNDStationProbeError("original station row must have eight columns")
        sid, day, element, value, mflag, qflag, sflag, obs_time = row
        if sid != STATION_ID:
            raise GHCNDStationProbeError("provider returned a different station")
        try:
            parsed = datetime.strptime(day, "%Y%m%d")
        except ValueError as exc:
            raise GHCNDStationProbeError("invalid provider observation date") from exc
        if not 1700 <= parsed.year <= 2026:
            raise GHCNDStationProbeError("observation day outside supported historical scope")
        if ELEMENT.fullmatch(element) is None or SIGNED_INTEGER.fullmatch(value) is None:
            raise GHCNDStationProbeError("invalid provider element or integer measurement")
        if any(FLAG.fullmatch(flag) is None for flag in (mflag, qflag, sflag)):
            raise GHCNDStationProbeError("invalid original M/Q/S flag")
        if obs_time:
            if CLOCK.fullmatch(obs_time) is None or int(obs_time[:2]) > 23:
                raise GHCNDStationProbeError("invalid original observation time")
        key = (day, element)
        if key in seen:
            raise GHCNDStationProbeError("duplicate day-element for fixed station")
        seen.add(key)
        elements.add(element)
        dates.append(day)
        measurement_flagged += bool(mflag)
        quality_flagged += bool(qflag)
        source_flagged += bool(sflag)
    return {
        "station_id": STATION_ID,
        "complete_original_rows_checked": len(rows),
        "first_observation_day": min(dates),
        "last_observation_day": max(dates),
        "element_types_seen": sorted(elements),
        "nonblank_measurement_flags": measurement_flagged,
        "nonblank_quality_flags": quality_flagged,
        "nonblank_source_flags": source_flagged,
        "partial_final_line_discarded": truncated_tail,
        "provider_native_values_converted": False,
        "full_station_history_complete": False,
        "scientific_quality_admitted": False,
    }


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise GHCNDStationProbeError("redirect violates exact provider identity")


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
    verify_contract(contract_path)
    req = request.Request(
        URL, method="GET",
        headers={"Range": "bytes=0-65535", "Accept": "text/csv", "Accept-Encoding": "identity"},
    )
    try:
        with open_request(req, TIMEOUT) as response:
            if response.geturl() != URL or type(response.status) is not int or response.status != 206:
                raise GHCNDStationProbeError("expected exact HTTP 206 without redirect")
            media = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media not in MEDIA:
                raise GHCNDStationProbeError("unexpected CSV content type")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise GHCNDStationProbeError("compressed content unsupported for fixed byte identity")
            match = CONTENT_RANGE.fullmatch(response.headers.get("Content-Range", ""))
            if match is None or int(match.group(1)) <= BYTE_LIMIT:
                raise GHCNDStationProbeError("provider Content-Range incompatible with fixed prefix")
            total = int(match.group(1))
            raw = response.read(BYTE_LIMIT + 1)
    except GHCNDStationProbeError:
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        raise GHCNDStationProbeError("bounded original provider request failed") from exc
    shape = inspect_station_prefix(raw)
    checked = utc_clock()
    if checked.tzinfo is None or checked.utcoffset() is None:
        raise GHCNDStationProbeError("UTC timestamp required for source receipt")
    return {
        "profile": PROFILE,
        "source_access_contract": "access/noaa.nodd.ghcnd-central-park-range.json",
        "original_url": URL,
        "range_header": "bytes=0-65535",
        "original_file_total_bytes_observed": total,
        "sample_bytes": len(raw),
        "sample_sha256": hashlib.sha256(raw).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "retrieved_at_utc": checked.astimezone(timezone.utc).isoformat(),
        "http_status": 206,
        "media_type": media,
        **shape,
        "raw_observations_persisted": False,
        "model_input_admitted": False,
        "insurance_portfolio_inferred": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="one fixed 64 KiB source range GET")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("network is disabled by default; use --live for a single fixed sample")
    try:
        print(json.dumps(probe(), sort_keys=True, indent=2, allow_nan=False))
    except (GHCNDStationProbeError, OSError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
