#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Compare one complete NCEI original GHCN gzip US station with pinned NODD original.

Exactly one source GET, strict single gzip member and bounded inflated bytes.
Returns hashes and aggregate provider data only, never raw station values.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import ssl
import sys
from typing import Any, Callable
from urllib import error, request
import zlib

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.validate_source_access import validate_path
from scripts.probe_ghcnd_full_station_original_v0 import HEADER, STATION, inspect_full_csv

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "access" / "noaa.ncei.ghcnd-central-park-gzip.json"
URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/USW00094728.csv.gz"
MAX_COMPRESSED = 12 * 1024 * 1024
MAX_CSV = 24 * 1024 * 1024
TIMEOUT = 60
CHUNK = 65536
MEDIA = {"application/gzip", "application/x-gzip", "application/octet-stream", "binary/octet-stream"}
PROFILE = "oc-noaa-ncei-one-original-gzip-us-station-v0"
# Verified by the NODD one-full-original workflow on 2026-11-02;
# this is a baseline receipt, NOT a live NODD version/absolute freshness claim.
NODD_SHA256 = "7e75c1ba40312d0d04cc4fd41fa88bc14bc6ef21dde740735365896209ff3a0f"
NODD_ROWS = 458003
NODD_LAST_OBS = "20250205"
ETAG = re.compile(r'^"([0-9a-fA-F]{32})(?:-[0-9]+)?"$')


class NCEIStationError(ValueError):
    """NCEI original, bounds or semantic validation failure."""


def verify_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    c = validate_path(path)
    if (
        c["access_id"] != "noaa.ncei.ghcnd-central-park-gzip"
        or c["source_ids"] != ["noaa.ncei.ghcn-daily"]
        or c["status"] != "probe_ready"
        or c["interface_type"] != "http_file"
        or c["service_root"] != "https://www.ncei.noaa.gov"
        or c["request_contract"]["allowed_operations"] != [
            "one_fixed_us_station_gzip_integrity_and_freshness_probe"]
        or c["request_contract"]["path_templates"] != [
            "/pub/data/ghcn/daily/by_station/USW00094728.csv.gz"]
        or c["authentication"]["mode"] != "none"
        or c["probe_contract"]["mode"] != "provider_specific"
        or c["probe_contract"]["operation"] != "one_fixed_us_station_gzip_integrity_and_freshness_probe"
        or c["probe_contract"]["requires_credentials"] is not False
        or c["rights_and_policy"]["dataset_rights_status"] != "verified"
        or c["rights_and_policy"]["commercial_automation_status"] != "allowed"
        or c["operational_constraints"]["timeout_seconds"] != TIMEOUT
        or c["operational_constraints"]["max_probe_bytes"] != 5 * 1024 * 1024
        or c["operational_constraints"]["max_sample_bytes"] != MAX_COMPRESSED
    ):
        raise NCEIStationError("fixed NCEI original source contract changed")
    return c


def inflate_validated_gzip_members(
    raw: bytes, *, max_csv: int = MAX_CSV, max_members: int = 256
) -> tuple[bytes, int]:
    """RFC-1952 gzip permits concatenated members; validate every CRC and boundary.

    Reject any non-gzip trailing bytes, incomplete member, excessive member
    count or expanded data over the reviewed 24-MiB total, including across
    member boundaries. No member is trusted solely from a gzip header.
    """
    if type(raw) is not bytes or not 128 <= len(raw) <= MAX_COMPRESSED:
        raise NCEIStationError("gzip original empty or beyond fixed compressed size")
    pending = raw
    members = 0
    size = 0
    parts: list[bytes] = []
    while pending:
        members += 1
        if members > max_members:
            raise NCEIStationError("too many original gzip members")
        if not pending.startswith(b"\x1f\x8b\x08"):
            raise NCEIStationError("trailing bytes are not a complete gzip member")
        decoder = zlib.decompressobj(wbits=16 + zlib.MAX_WBITS)
        consumed_to = 0
        try:
            for start in range(0, len(pending), CHUNK):
                chunk = pending[start:start + CHUNK]
                expanded = decoder.decompress(chunk, max_csv - size + 1)
                size += len(expanded)
                if size > max_csv or decoder.unconsumed_tail:
                    raise NCEIStationError("inflated original exceeds bounded size")
                parts.append(expanded)
                if decoder.eof:
                    consumed_to = start + CHUNK
                    break
            if not decoder.eof:
                raise NCEIStationError("incomplete gzip member or invalid CRC")
            extra = decoder.flush(max_csv - size + 1)
            size += len(extra)
            if size > max_csv:
                raise NCEIStationError("inflated gzip trailer exceeds cap")
            if extra:
                parts.append(extra)
        except zlib.error as exc:
            raise NCEIStationError("gzip deflate/CRC original invalid") from exc
        pending = decoder.unused_data + pending[consumed_to:]
    return b"".join(parts), members


def validation_view_for_original_csv(raw: bytes) -> tuple[bytes, bool]:
    """Preserve provider original bytes, add validation-only header if absent.

    NCEI source can be headerless while NODD-derived station CSV has a header.
    Accept exactly eight provider-native columns and the fixed station ID in
    the first real row; do not reinterpret a different CSV schema or modify
    the original body hash. All rows are then validated by the shared strict
    original-station inspector.
    """
    expected = (",".join(HEADER) + "\n").encode("ascii")
    if raw.startswith(expected):
        return raw, True
    first = raw.split(b"\n", 1)[0]
    try:
        columns = first.decode("ascii", errors="strict").split(",")
    except UnicodeError as exc:
        raise NCEIStationError("unreviewed first original CSV row") from exc
    if (
        len(columns) != len(HEADER)
        or columns[0] != STATION
        or not re.fullmatch(r"\d{8}", columns[1])
        or not re.fullmatch(r"[A-Z0-9]{4}", columns[2])
        or not re.fullmatch(r"-?[0-9]{1,8}", columns[3])
    ):
        raise NCEIStationError("missing exact GHCN header and no valid eight-column first row")
    return expected + raw, False


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise NCEIStationError("source redirected to unreviewed host/path")


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
    req = request.Request(URL, method="GET", headers={
        "Accept": "application/gzip", "Accept-Encoding": "identity",
    })
    try:
        with open_request(req, TIMEOUT) as res:
            if res.geturl() != URL or type(res.status) is not int or res.status != 200:
                raise NCEIStationError("expected exact provider HTTP 200 without redirect")
            if res.headers.get("Content-Range") is not None:
                raise NCEIStationError("partial range not accepted as whole original")
            if res.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise NCEIStationError("source is transparently HTTP-compressed")
            media = res.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media not in MEDIA:
                raise NCEIStationError("unreviewed provider gzip MIME")
            clen = res.headers.get("Content-Length", "")
            if clen and (not clen.isdecimal() or int(clen) > MAX_COMPRESSED):
                raise NCEIStationError("invalid or overlong provider content length")
            raw = res.read(MAX_COMPRESSED + 1)
            if len(raw) > MAX_COMPRESSED or (clen and len(raw) != int(clen)):
                raise NCEIStationError("truncated or oversized original compressed source")
            etag = res.headers.get("ETag", "")
            modified = res.headers.get("Last-Modified", "")
    except NCEIStationError:
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        raise NCEIStationError("fixed NCEI gzip request failed closed") from exc

    csv_raw, gzip_members = inflate_validated_gzip_members(raw)
    normalized_view, had_header = validation_view_for_original_csv(csv_raw)
    shape = inspect_full_csv(normalized_view)
    now = utc_clock()
    if now.tzinfo is None or now.utcoffset() is None:
        raise NCEIStationError("timezone-aware UTC required for research receipt")

    return {
        "profile": PROFILE,
        "source_access_contract": "access/noaa.ncei.ghcnd-central-park-gzip.json",
        "retrieved_at_utc": now.astimezone(timezone.utc).isoformat(),
        "provider_url": URL,
        "http_status": 200,
        "mime_type": media,
        "compressed_original_bytes": len(raw),
        "compressed_original_sha256": hashlib.sha256(raw).hexdigest(),
        "inflated_original_csv_bytes": len(csv_raw),
        "validated_gzip_members": gzip_members,
        "inflated_original_csv_sha256": hashlib.sha256(csv_raw).hexdigest(),
        "original_provider_csv_header_present": had_header,
        "transient_header_added_only_for_validation": not had_header,
        "comparison_csv_sha256_after_header_only_normalization": hashlib.sha256(normalized_view).hexdigest(),
        "same_observation_rows_as_pinned_nodd_after_header_normalization": hashlib.sha256(normalized_view).hexdigest() == NODD_SHA256,
        "provider_etag": etag if ETAG.fullmatch(etag) else None,
        "provider_last_modified": modified if len(modified) <= 128 else None,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        **shape,
        "nodd_pinned_baseline_observed_utc_date": "2026-11-02",
        "nodd_pinned_baseline_csv_sha256": NODD_SHA256,
        "nodd_pinned_baseline_rows": NODD_ROWS,
        "nodd_pinned_baseline_last_observation": NODD_LAST_OBS,
        "same_csv_bytes_as_pinned_nodd_20261102": hashlib.sha256(csv_raw).hexdigest() == NODD_SHA256,
        "ncei_last_day_later_than_pinned_nodd": shape["last_observation_day"] > NODD_LAST_OBS,
        "scientific_homogeneity_admitted": False,
        "commercial_global_ghcnd_rights_inferred": False,
        "raw_provider_bytes_persisted": False,
        "neon_artifact_inserted": False,
        "model_input_admitted": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="one fixed U.S. NCEI original gzip GET")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("network opt-in with --live for one fixed whole source")
    try:
        print(json.dumps(probe(), indent=2, sort_keys=True, allow_nan=False))
    except (NCEIStationError, ValueError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
