#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, fail-closed ISIMIP3a ER11 historical maximum-rain filelist check.

Checks only an independently obtained plain-text provider filelist. Never
performs HTTP requests, fetches NetCDF bytes, infers commercial data rights,
or approves the source for insurer CAT modelling.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

SOURCE_ID = "isimip3a.tc.er11-wind.historical.maxrain.1950-2021"
DATASET_ID = "f08ab32e-b3ad-4984-81d1-495235765b6c"
FILELIST_URL = f"https://data.isimip.org/api/v1/datasets/{DATASET_ID}/filelist/"
PROVIDER_PREFIX = (
    "/ISIMIP3a/InputData/climate/tropical_cyclones/obsclim/"
    "global/storm/historical/ER11-wind/"
)
FILE_NAME = re.compile(r"er11-wind_obsclim_historical_maxrain_([0-9]{4})\.nc\Z")
HEX_SHA256 = re.compile(r"[a-f0-9]{64}\Z")
EXPECTED_YEARS = tuple(range(1950, 2022))
MAX_FILELIST_BYTES = 32_768


class ISIMIPFilelistError(ValueError):
    """Invalid original-file metadata identity, contents or completeness."""


def inspect_filelist_bytes(blob: bytes, expected_sha256: str) -> dict:
    """Validate 72 year-specific URL *names*; no NetCDF files are accessed."""
    if not isinstance(expected_sha256, str) or not HEX_SHA256.fullmatch(expected_sha256):
        raise ISIMIPFilelistError("independently pinned expected SHA256 must be 64 lowercase hex digits")
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_FILELIST_BYTES:
        raise ISIMIPFilelistError("filelist must be nonempty and within 32 KiB")
    observed_sha256 = hashlib.sha256(blob).hexdigest()
    if observed_sha256 != expected_sha256:
        raise ISIMIPFilelistError("filelist SHA256 mismatch")
    try:
        text = blob.decode("ascii")
    except UnicodeError as exc:
        raise ISIMIPFilelistError("filelist must be ASCII") from exc
    if "\r" in text or "\x00" in text or "\t" in text:
        raise ISIMIPFilelistError("CR, NUL and tabs prohibited")
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()
    if len(lines) != len(EXPECTED_YEARS) or any(not line for line in lines):
        raise ISIMIPFilelistError("expected exactly 72 nonempty annual URLs")
    observed_years = []
    seen_urls = set()
    for line in lines:
        if line.strip() != line or any(ord(c) < 33 or ord(c) > 126 for c in line):
            raise ISIMIPFilelistError("unsafe characters in URL")
        try:
            url = urlsplit(line)
            port = url.port
        except ValueError as exc:
            raise ISIMIPFilelistError("malformed provider URL") from exc
        if (url.scheme != "https" or url.hostname != "files.isimip.org"
                or port is not None or url.username or url.password
                or url.query or url.fragment):
            raise ISIMIPFilelistError("wrong host/scheme, credentials, port, query or fragment")
        if not url.path.startswith(PROVIDER_PREFIX):
            raise ISIMIPFilelistError("wrong ISIMIP3a pathway or model family")
        match = FILE_NAME.fullmatch(url.path[len(PROVIDER_PREFIX):])
        if not match:
            raise ISIMIPFilelistError("unexpected ER11 maximum-rain filename")
        if line in seen_urls:
            raise ISIMIPFilelistError("duplicate URL")
        seen_urls.add(line)
        observed_years.append(int(match.group(1)))
    if tuple(observed_years) != EXPECTED_YEARS:
        raise ISIMIPFilelistError("missing, duplicate or out-of-order historical year")
    return {
        "profile": "isimip3a-er11-maxrain-annual-filelist-preflight-v0",
        "source_id": SOURCE_ID,
        "provider_dataset_id": DATASET_ID,
        "provider_filelist_url": FILELIST_URL,
        "filelist_sha256": observed_sha256,
        "filelist_byte_count": len(blob),
        "annual_file_count": len(observed_years),
        "first_year": observed_years[0],
        "last_year": observed_years[-1],
        "provider_file_url_names_checked": True,
        "underlying_ibtracs_and_era5_reanalysis": True,
        "derived_max_24h_rainfall_not_direct_observation": True,
        "this_is_not_a_tc_wind_footprint": True,
        "netcdf_bytes_downloaded": False,
        "netcdf_checksums_verified": False,
        "data_license_reviewed": False,
        "commercial_insurance_use_approved": False,
        "scientific_model_validation_approved": False,
        "admission_status": "not_admitted",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--filelist", required=True, type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.filelist.resolve() == args.out.resolve():
        parser.error("refusing to overwrite original provider filelist")
    try:
        if args.filelist.stat().st_size > MAX_FILELIST_BYTES:
            raise ISIMIPFilelistError("filelist exceeds 32 KiB")
        report = inspect_filelist_bytes(args.filelist.read_bytes(), args.expected_sha256)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except (ISIMIPFilelistError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
