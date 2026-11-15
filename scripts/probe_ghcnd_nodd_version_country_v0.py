#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Two-object, metadata-only NOAA NODD GHCN-Daily source preflight.

The public GHCN version and country-code metadata are not meteorological
observations and not CAT model inputs. Opt in with --live. The request paths,
protocol, size limit and provider are fixed; no user-supplied network inputs.
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

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.validate_source_access import validate_path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "access" / "noaa.nodd.ghcnd-version-country.json"
ROOT_URL = "https://noaa-ghcn-pds.s3.amazonaws.com"
OBJECTS = (
    ("version", ROOT_URL + "/ghcnd-version.txt"),
    ("countries", ROOT_URL + "/ghcnd-countries.txt"),
)
MAX_BYTES = 4096
TIMEOUT_SECONDS = 30
PROFILE = "oc-noaa-nodd-ghcnd-version-country-v0"
MEDIA_TYPES = {"application/octet-stream", "text/plain"}
UPDATE_RE = re.compile(r"\b(\d+\.\d+)-upd-(\d{10})\b")
REPROCESSED_RE = re.compile(r"\b(\d+\.\d+)-por-(\d{10})\b")
COUNTRY_RE = re.compile(r"^([A-Z]{2})\s+(.+?)\s*$")


class GHCNDProbeError(ValueError):
    """Provider identity, parsing or bounded access violation."""


def verify_frozen_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    contract = validate_path(path)
    if (
        contract["access_id"] != "noaa.nodd.ghcnd-version-country"
        or contract["source_ids"] != ["noaa.ncei.ghcn-daily"]
        or contract["service_root"] != ROOT_URL
        or contract["interface_type"] != "http_file"
        or contract["status"] != "probe_ready"
        or contract["authentication"]["mode"] != "none"
        or contract["request_contract"]["allowed_operations"] != ["probe_version_and_country_metadata"]
        or contract["request_contract"]["path_templates"] != [
            "/ghcnd-version.txt", "/ghcnd-countries.txt"
        ]
        or contract["probe_contract"]["mode"] != "metadata_get"
        or contract["probe_contract"]["operation"] != "probe_version_and_country_metadata"
        or contract["probe_contract"]["requires_credentials"] is not False
        or contract["rights_and_policy"]["dataset_rights_status"] != "verified"
        or contract["rights_and_policy"]["api_terms_status"] != "same_as_dataset"
        or contract["rights_and_policy"]["commercial_automation_status"] != "allowed"
        or contract["operational_constraints"]["max_probe_bytes"] != MAX_BYTES
        or contract["operational_constraints"]["timeout_seconds"] != TIMEOUT_SECONDS
    ):
        raise GHCNDProbeError("frozen GHCN NODD metadata contract changed")
    return contract


def _decode(raw: bytes) -> str:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise GHCNDProbeError("metadata object empty or beyond strict size limit")
    try:
        content = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise GHCNDProbeError("metadata file must be strict UTF-8") from exc
    if "\x00" in content or "\r" in content:
        raise GHCNDProbeError("metadata file has unexpected control characters")
    return content


def _valid_utc_id(timestamp: str) -> datetime:
    try:
        return datetime.strptime(timestamp, "%Y%m%d%H")
    except ValueError as exc:
        raise GHCNDProbeError("malformed GHCN provider version timestamp") from exc


def parse_version(raw: bytes) -> dict[str, str]:
    content = _decode(raw)
    updates = UPDATE_RE.findall(content)
    reprocessed = REPROCESSED_RE.findall(content)
    if (
        len(updates) != 1 or len(reprocessed) != 1
        or "The current version of GHCN Daily is " not in content
        or "last fully reprocessed version:" not in content
    ):
        raise GHCNDProbeError("missing or ambiguous update/reprocessing version")
    release, timestamp = updates[0]
    por_release, por_timestamp = reprocessed[0]
    if release != por_release or _valid_utc_id(timestamp) < _valid_utc_id(por_timestamp):
        raise GHCNDProbeError("inconsistent GHCN version timeline")
    return {
        "rolling_version": release + "-upd-" + timestamp,
        "last_reprocessed_version": por_release + "-por-" + por_timestamp,
    }


def parse_countries(raw: bytes) -> dict[str, Any]:
    content = _decode(raw)
    lines = [line for line in content.split("\n") if line.strip()]
    if not 100 <= len(lines) <= 400:
        raise GHCNDProbeError("unexpected GHCN-native country vocabulary size")
    codes: set[str] = set()
    for line in lines:
        match = COUNTRY_RE.fullmatch(line)
        if match is None or len(match.group(2)) > 160:
            raise GHCNDProbeError("invalid GHCN country-code mapping row")
        code = match.group(1)
        if code in codes:
            raise GHCNDProbeError("duplicate GHCN-native country code")
        codes.add(code)
    return {
        "ghcn_native_country_count": len(codes),
        "country_codes_are_iso3166": False,
        "country_crosswalk_admitted": False,
    }


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise GHCNDProbeError("provider redirect is forbidden")


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
    receipts: dict[str, Any] = {}
    shapes: dict[str, Any] = {}
    for label, url in OBJECTS:
        req = request.Request(url, headers={"Accept": "text/plain"}, method="GET")
        try:
            with open_request(req, TIMEOUT_SECONDS) as response:
                if response.geturl() != url or type(response.status) is not int or response.status != 200:
                    raise GHCNDProbeError("metadata GET did not return direct HTTP 200")
                media = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
                if media not in MEDIA_TYPES:
                    raise GHCNDProbeError("unexpected NOAA metadata media type")
                if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                    raise GHCNDProbeError("transparent content encoding is forbidden")
                raw = response.read(MAX_BYTES + 1)
        except GHCNDProbeError:
            raise
        except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
            raise GHCNDProbeError("bounded NOAA metadata request failed") from exc
        shape = parse_version(raw) if label == "version" else parse_countries(raw)
        shapes.update(shape)
        receipts[label] = {
            "url": url,
            "http_status": 200,
            "media_type": media,
            "response_bytes": len(raw),
            "response_sha256": hashlib.sha256(raw).hexdigest(),
        }
    checked = utc_clock()
    if checked.tzinfo is None or checked.utcoffset() is None:
        raise GHCNDProbeError("receipt timestamp must be timezone-aware")
    return {
        "profile": PROFILE,
        "source_access_contract": "access/noaa.nodd.ghcnd-version-country.json",
        "retrieved_at_utc": checked.astimezone(timezone.utc).isoformat(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "objects": receipts,
        **shapes,
        "raw_provider_bytes_persisted": False,
        "weather_observations_acquired": False,
        "model_input_admitted": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="two exact public metadata GETs, no raw output")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("network is opt-in; use --live for the two fixed objects")
    try:
        print(json.dumps(probe(), indent=2, sort_keys=True, allow_nan=False))
    except (GHCNDProbeError, OSError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
