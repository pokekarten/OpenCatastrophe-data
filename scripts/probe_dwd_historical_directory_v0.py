#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Inspect only the reviewed DWD CDC historical extreme-wind directory.

One fixed anonymous HTTPS GET, at most 1 MiB, no archive download. Bind an
exact source-index receipt and count DWD-native station/date archive identities;
never turn index entries into admitted weather/model data or publisher rights.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import ssl
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, Request, build_opener

from scripts.acquire_dwd_extreme_wind_receipt import (
    AcquisitionError,
    FILENAME as FROZEN_EXISTING_ARCHIVE,
    FrozenHTTPSHandler,
)
from scripts.probe_fixed_public_sources_v0 import NoRedirect, _bad_number, _unique_object

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "dwd.cdc.extreme-wind.http-file"
OPERATION = "inspect_historical_directory"
URL = (
    "https://opendata.dwd.de/climate_environment/CDC/observations_germany/"
    "climate/10_minutes/extreme_wind/historical/"
)
FILENAME_RE = re.compile(
    r"10minutenwerte_extrema_wind_([0-9]{5})_([0-9]{8})_([0-9]{8})_hist[.]zip\Z"
)
MAX_ARCHIVE_LINKS = 6000


class DirectoryBlocked(ValueError):
    """Fail closed on unreviewed provider URL, scope, response or index shape."""


def reviewed_contract(root: Path = ROOT) -> tuple[int, int, str]:
    path = root / "access" / (SOURCE + ".json")
    try:
        raw = path.read_bytes()
        contract = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                              parse_constant=_bad_number)
    except (OSError, UnicodeError, ValueError) as exc:
        raise DirectoryBlocked("reviewed DWD source contract not readable") from exc
    parsed = urlsplit(URL)
    base = urlsplit(contract.get("service_root", ""))
    if (
        contract.get("access_id") != SOURCE
        or contract.get("status") != "probe_ready"
        or contract.get("interface_type") != "http_file"
        or contract.get("authentication", {}).get("mode") != "none"
        or contract.get("probe_contract", {}).get("requires_credentials") is not False
        or contract.get("probe_contract", {}).get("operation") != OPERATION
        or OPERATION not in contract.get("request_contract", {}).get("allowed_operations", [])
        or "/historical/" not in contract.get("request_contract", {}).get("path_templates", [])
        or contract.get("rights_and_policy", {}).get("commercial_automation_status") != "allowed"
        or base.scheme != "https" or parsed.scheme != "https"
        or base.netloc != "opendata.dwd.de" or parsed.netloc != base.netloc
        or parsed.path != base.path.rstrip("/") + "/historical/"
        or any((parsed.query, parsed.fragment, base.query, base.fragment,
                parsed.username, parsed.password, base.username, base.password))
    ):
        raise DirectoryBlocked("DWD fixed directory diverges from reviewed source scope")
    bounds = contract.get("operational_constraints", {})
    max_bytes = bounds.get("max_probe_bytes")
    timeout = bounds.get("timeout_seconds")
    if (type(max_bytes) is not int or not 0 < max_bytes <= 1_048_576
            or type(timeout) is not int or not 0 < timeout <= 60):
        raise DirectoryBlocked("invalid DWD reviewed request bounds")
    return max_bytes, timeout, hashlib.sha256(raw).hexdigest()


class DirectoryLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.files: dict[str, tuple[str, date, date]] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        hrefs = [v for k, v in attrs if k.lower() == "href"]
        if len(hrefs) != 1 or not isinstance(hrefs[0], str):
            return
        name = hrefs[0]
        if not name.startswith("10minutenwerte_extrema_wind_"):
            return
        match = FILENAME_RE.fullmatch(name)
        if match is None:
            raise DirectoryBlocked("provider archive link has unexpected identity/URL syntax")
        try:
            begin = date.fromisoformat(
                match.group(2)[:4] + "-" + match.group(2)[4:6] + "-" + match.group(2)[6:]
            )
            end = date.fromisoformat(
                match.group(3)[:4] + "-" + match.group(3)[4:6] + "-" + match.group(3)[6:]
            )
        except ValueError as exc:
            raise DirectoryBlocked("provider archive contains invalid calendar date") from exc
        if begin > end or name in self.files:
            raise DirectoryBlocked("provider archive link dates or identity duplicated")
        self.files[name] = (match.group(1), begin, end)
        if len(self.files) > MAX_ARCHIVE_LINKS:
            raise DirectoryBlocked("provider historical archive list exceeds reviewed cap")


def inspect_index(raw: bytes) -> dict:
    try:
        index = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DirectoryBlocked("directory is not strict UTF-8 HTML") from exc
    parser = DirectoryLinks()
    parser.feed(index)
    parser.close()
    if FROZEN_EXISTING_ARCHIVE not in parser.files:
        raise DirectoryBlocked("previously pinned DWD station-00003 archive absent")
    if not parser.files:
        raise DirectoryBlocked("provider historical directory contains no valid archive links")
    spans = list(parser.files.values())
    return {
        "historical_archive_link_count": len(spans),
        "unique_station_ids": len({x[0] for x in spans}),
        "earliest_filename_coverage_start": min(x[1] for x in spans).isoformat(),
        "latest_filename_coverage_end": max(x[2] for x in spans).isoformat(),
        "existing_station_00003_archive_found": True,
        "existing_archive_filename": FROZEN_EXISTING_ARCHIVE,
    }


def run_probe(root: Path = ROOT, *, opener=None) -> dict:
    limit, timeout, contract_hash = reviewed_contract(root)
    request = Request(URL, method="GET", headers={
        "Accept": "text/html,text/plain",
        "Accept-Encoding": "identity",
        "User-Agent": "OpenCatastrophe-DWD-index-receipt/0.1",
    })
    client = opener if opener is not None else build_opener(
        ProxyHandler({}), NoRedirect(), FrozenHTTPSHandler(context=ssl.create_default_context())
    )
    try:
        with client.open(request, timeout=timeout) as response:
            if response.status != 200 or response.geturl() != URL:
                raise DirectoryBlocked("unexpected DWD HTTP status or redirect")
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if content_type not in {"text/html", "text/plain"}:
                raise DirectoryBlocked("unexpected DWD directory content type")
            content_encoding = response.headers.get("Content-Encoding", "identity").strip().lower()
            if content_encoding not in {"", "identity"}:
                raise DirectoryBlocked("compressed directory response not reviewed")
            declared = response.headers.get("Content-Length")
            if declared is not None:
                try:
                    size = int(declared)
                except ValueError as exc:
                    raise DirectoryBlocked("invalid DWD Content-Length") from exc
                if size < 0 or size > limit:
                    raise DirectoryBlocked("DWD directory exceeds reviewed byte limit")
            raw = response.read(limit + 1)
            if not raw or len(raw) > limit:
                raise DirectoryBlocked("DWD directory empty or over byte cap")
            if declared is not None and len(raw) != size:
                raise DirectoryBlocked("DWD directory Content-Length mismatch")
    except (HTTPError, URLError, TimeoutError, OSError, AcquisitionError) as exc:
        raise DirectoryBlocked("DWD read-only directory request failed") from exc
    return {
        "profile": "opencatastrophe-dwd-historical-directory-receipt-v0",
        "source_id": SOURCE,
        "operation": OPERATION,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "directory_request_sha256": hashlib.sha256(URL.encode("ascii")).hexdigest(),
        "directory_response_sha256": hashlib.sha256(raw).hexdigest(),
        "directory_response_bytes": len(raw),
        "access_contract_sha256": contract_hash,
        "probe_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        **inspect_index(raw),
        "original_archives_downloaded": 0,
        "external_bytes_persisted": False,
        "model_input_approved": False,
    }


def main(argv=None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    try:
        result = run_probe()
    except DirectoryBlocked as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "model_input_approved": False}), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
