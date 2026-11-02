#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed, one-shot full original GHCN-Daily station file research preflight.

One fixed provider object. A complete original byte SHA-256 and synthetic-safe
summary are returned, never raw weather observations or a CAT dataset.
--live is required for *one* public HTTPS GET; no URL/station/size controls.
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

CONTRACT = Path(__file__).resolve().parents[1] / "access" / "noaa.nodd.ghcnd-central-park-complete.json"
URL = "https://noaa-ghcn-pds.s3.amazonaws.com/csv/by_station/USW00094728.csv"
STATION = "USW00094728"
MAX_BYTES = 25_165_824
MIN_BYTES = 1_048_576
MIN_ROWS = 10_000
MAX_ROWS = 800_000
TIMEOUT = 60
PROFILE = "oc-ghcnd-single-full-station-original-receipt-v0"
HEADER = ["ID", "DATE", "ELEMENT", "DATA_VALUE", "M_FLAG", "Q_FLAG", "S_FLAG", "OBS_TIME"]
MEDIA_TYPES = {"binary/octet-stream", "application/octet-stream", "text/csv", "text/plain"}
ELEMENT = re.compile(r"^[A-Z0-9]{4}$")
VALUE = re.compile(r"^-?[0-9]{1,8}$")
FLAG = re.compile(r"^[A-Za-z0-9]?$")
CLOCK = re.compile(r"^(?:[01][0-9]|2[0-3])[0-5][0-9]$")
ETAG = re.compile(r'^"([0-9a-fA-F]{32})(?:-[0-9]+)?"$')


class StationFullProbeError(ValueError):
    """An unexpected provider response or scientific source shape."""


def verify_contract(path: Path = CONTRACT) -> dict[str, Any]:
    payload = validate_path(path)
    if (
        payload["access_id"] != "noaa.nodd.ghcnd-central-park-complete"
        or payload["source_ids"] != ["noaa.ncei.ghcn-daily"]
        or payload["status"] != "probe_ready"
        or payload["interface_type"] != "http_file"
        or payload["service_root"] != "https://noaa-ghcn-pds.s3.amazonaws.com"
        or payload["request_contract"]["allowed_operations"] != ["read_one_full_station_for_hash_and_schema"]
        or payload["request_contract"]["path_templates"] != ["/csv/by_station/USW00094728.csv"]
        or payload["authentication"]["mode"] != "none"
        or payload["probe_contract"]["mode"] != "provider_specific"
        or payload["probe_contract"]["operation"] != "read_one_full_station_for_hash_and_schema"
        or payload["probe_contract"]["requires_credentials"] is not False
        or payload["rights_and_policy"]["dataset_rights_status"] != "verified"
        or payload["rights_and_policy"]["api_terms_status"] != "same_as_dataset"
        or payload["rights_and_policy"]["commercial_automation_status"] != "allowed"
        or payload["operational_constraints"]["max_probe_bytes"] != 5 * 1024 * 1024
        or payload["operational_constraints"]["max_sample_bytes"] != MAX_BYTES
        or payload["operational_constraints"]["timeout_seconds"] != TIMEOUT
    ):
        raise StationFullProbeError("frozen whole-station NOAA source contract differs from code")
    return payload


def inspect_full_csv(raw: bytes) -> dict[str, Any]:
    """Validate *every* provider row, preserving original units and flag semantics."""
    if type(raw) is not bytes or not MIN_BYTES <= len(raw) <= MAX_BYTES:
        raise StationFullProbeError("complete original station bytes outside reviewed bounds")
    if b"\x00" in raw or not raw.endswith(b"\n"):
        raise StationFullProbeError("original station CSV is binary or lacks last complete record")
    try:
        text = raw.decode("utf-8", errors="strict")
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        if next(reader, None) != HEADER:
            raise StationFullProbeError("original eight-field GHCN CSV header not present")
        counts: dict[str, int] = {}
        flagged_quality: dict[str, int] = {}
        count = 0
        missing_values = 0
        q_count = 0
        m_count = 0
        s_count = 0
        earliest: str | None = None
        latest: str | None = None
        unique: set[tuple[str, str]] = set()
        for row in reader:
            if len(row) != 8:
                raise StationFullProbeError("unexpected original row column count")
            station, date, element, value, mflag, qflag, sflag, observation_time = row
            if station != STATION:
                raise StationFullProbeError("the original object contains another station")
            if not re.fullmatch(r"\d{8}", date):
                raise StationFullProbeError("nonstandard station date")
            try:
                day = datetime.strptime(date, "%Y%m%d")
            except ValueError as exc:
                raise StationFullProbeError("invalid calendar day") from exc
            if not 1700 <= day.year <= 2026:
                raise StationFullProbeError("original station date outside reviewed historical window")
            if ELEMENT.fullmatch(element) is None or VALUE.fullmatch(value) is None:
                raise StationFullProbeError("original element or integer observation malformed")
            if not all(FLAG.fullmatch(flag) is not None for flag in (mflag, qflag, sflag)):
                raise StationFullProbeError("invalid original measurement/quality/source flags")
            if observation_time and CLOCK.fullmatch(observation_time) is None:
                raise StationFullProbeError("invalid original observation time")
            identity = (date, element)
            if identity in unique:
                raise StationFullProbeError("duplicate original day-element station observation")
            unique.add(identity)
            count += 1
            if count > MAX_ROWS:
                raise StationFullProbeError("whole-station row limit exceeded")
            earliest = min(earliest, date) if earliest else date
            latest = max(latest, date) if latest else date
            counts[element] = counts.get(element, 0) + 1
            q_count += bool(qflag)
            m_count += bool(mflag)
            s_count += bool(sflag)
            missing_values += value == "-9999"
            if qflag:
                flagged_quality[element] = flagged_quality.get(element, 0) + 1
    except (UnicodeError, csv.Error) as exc:
        raise StationFullProbeError("invalid original UTF-8 CSV payload") from exc
    if not MIN_ROWS <= count <= MAX_ROWS:
        raise StationFullProbeError("unexpected whole-station observation count")
    return {
        "station_id": STATION,
        "complete_original_rows_checked": count,
        "first_observation_day": earliest,
        "last_observation_day": latest,
        "rows_by_element": dict(sorted(counts.items())),
        "nonblank_quality_flags_by_element": dict(sorted(flagged_quality.items())),
        "nonblank_measurement_flag_rows": m_count,
        "nonblank_quality_flag_rows": q_count,
        "nonblank_source_flag_rows": s_count,
        "original_missing_sentinel_rows": missing_values,
        "all_original_rows_validated": True,
        "units_converted": False,
        "scientific_quality_admitted": False,
        "full_provider_object_bytes_hashed": True,
    }


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise StationFullProbeError("provider redirected to an unreviewed object")


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
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    contract_path: Path = CONTRACT,
) -> dict[str, Any]:
    verify_contract(contract_path)
    req = request.Request(URL, method="GET", headers={
        "Accept": "text/csv", "Accept-Encoding": "identity",
    })
    try:
        with open_request(req, TIMEOUT) as response:
            if response.geturl() != URL or type(response.status) is not int or response.status != 200:
                raise StationFullProbeError("expected exact provider HTTP 200 with no redirect")
            if response.headers.get("Content-Range") is not None:
                raise StationFullProbeError("unexpected partial provider file")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise StationFullProbeError("provider silently compressed original bytes")
            media = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media not in MEDIA_TYPES:
                raise StationFullProbeError("unreviewed original object MIME type")
            length_text = response.headers.get("Content-Length", "")
            if not length_text.isdecimal():
                raise StationFullProbeError("exact full provider Content-Length required")
            length = int(length_text)
            if not MIN_BYTES <= length <= MAX_BYTES:
                raise StationFullProbeError("provider file size outside reviewed 1-24 MiB limit")
            raw = response.read(MAX_BYTES + 1)
            if len(raw) != length:
                raise StationFullProbeError("original provider body does not match Content-Length")
            etag = response.headers.get("ETag", "")
            last_modified = response.headers.get("Last-Modified", "")
    except StationFullProbeError:
        raise
    except (error.URLError, error.HTTPError, OSError, TimeoutError) as exc:
        raise StationFullProbeError("full-station provider GET failed closed") from exc

    shape = inspect_full_csv(raw)
    checked = now()
    if checked.tzinfo is None or checked.utcoffset() is None:
        raise StationFullProbeError("receipt needs timezone-aware UTC")
    return {
        "profile": PROFILE,
        "source_access_contract": "access/noaa.nodd.ghcnd-central-park-complete.json",
        "retrieved_at_utc": checked.astimezone(timezone.utc).isoformat(),
        "provider_url": URL,
        "http_status": 200,
        "mime_type": media,
        "original_body_bytes": length,
        "original_body_sha256": hashlib.sha256(raw).hexdigest(),
        "provider_etag": etag if ETAG.fullmatch(etag) else None,
        "provider_last_modified": last_modified if len(last_modified) <= 128 else None,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        **shape,
        "rolling_release_not_atomically_bound": True,
        "original_observations_persisted": False,
        "neon_artifact_inserted": False,
        "model_input_admitted": False,
        "insured_exposure_inferred": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="one fixed original-station full GET")
    options = parser.parse_args(argv)
    if not options.live:
        parser.error("network disabled by default; --live required for exact provider GET")
    try:
        print(json.dumps(probe(), indent=2, sort_keys=True, allow_nan=False))
    except (StationFullProbeError, OSError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
