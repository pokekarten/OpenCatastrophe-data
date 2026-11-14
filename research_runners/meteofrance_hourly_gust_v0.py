# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded, original-data Météo-France hourly three-second gust preflight.

Only public catalogue metadata and a fixed department/period are reachable in
--live mode. This is source evidence and a station sample, NOT source admission,
3-second-gust comparability proof or a calibrated windstorm CAT model.
Original rows never enter repository files or console output.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

CATALOGUE_URL = "https://www.data.gouv.fr/api/1/datasets/donnees-climatologiques-de-base-horaires/"
DOCUMENT_URL = "https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/BASE/HOR/H_descriptif_champs.csv"
RESOURCE_TITLE = "HOR_departement_75_periode_2020-2024"
RESOURCE_FILENAME = "H_75_2020-2024.csv.gz"
ALLOWED_HOSTS = frozenset(("www.data.gouv.fr", "meteofrance.s3.sbg.io.cloud.ovh.net"))
MAX_CATALOGUE_BYTES = 12 * 1024 * 1024
MAX_DOCUMENT_BYTES = 64 * 1024
MAX_GZIP_BYTES = 32 * 1024 * 1024
MAX_CSV_BYTES = 160 * 1024 * 1024
MAX_ROWS = 1_000_000
MAX_STATIONS = 1000
FIELDS = ("NUM_POSTE", "AAAAMMJJHH", "FF", "FXI", "FXI3S", "STATUS_FXI3S")
QUALITY_OK = frozenset(("0", "1"))


class Blocked(ValueError):
    """Source identity, API transport or physical-unit ambiguity."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _check_url(url: str, *, document: bool = False) -> None:
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or parts.hostname not in ALLOWED_HOSTS:
        raise Blocked("source URL must use HTTPS and the fixed official host set")
    if parts.username or parts.password or parts.fragment or parts.query:
        raise Blocked("source URL cannot have credentials, fragments or query parameters")
    if document and url != DOCUMENT_URL:
        raise Blocked("dictionary URL must equal the frozen official file")


def _read_url(url: str, limit: int) -> bytes:
    _check_url(url)
    request = urllib.request.Request(url, headers={"User-Agent": "OpenCatastrophe-data-original-preflight/1.0", "Accept": "application/json, text/plain, */*"})
    with urllib.request.urlopen(request, timeout=30) as response:
        _check_url(response.geturl())
        size = response.headers.get("Content-Length")
        if size and size.isdecimal() and int(size) > limit:
            raise Blocked("declared asset exceeds byte cap")
        payload = response.read(limit + 1)
    if len(payload) > limit:
        raise Blocked("download exceeds byte cap")
    return payload


def resolve_resource(catalogue: bytes) -> dict[str, str | int | None]:
    try:
        payload = json.loads(catalogue.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise Blocked("catalogue is not valid UTF-8 JSON") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("resources"), list):
        raise Blocked("catalogue resources array missing")
    resources = payload["resources"]
    matches = [r for r in resources if isinstance(r, dict) and r.get("title") == RESOURCE_TITLE]
    if len(matches) != 1:
        raise Blocked(f"expected exactly one official {RESOURCE_TITLE} resource; got {len(matches)}")
    item = matches[0]
    url = item.get("url")
    if not isinstance(url, str):
        raise Blocked("resource lacks HTTPS download URL")
    _check_url(url)
    if not url.endswith("/" + RESOURCE_FILENAME) and not re.fullmatch(r"https://www\.data\.gouv\.fr/api/1/datasets/r/[0-9a-fA-F-]+/?", url):
        raise Blocked("resource URL/filename does not match frozen source identity")
    size = item.get("filesize")
    if size is not None and (type(size) is not int or size < 0 or size > MAX_GZIP_BYTES):
        raise Blocked("resource declared byte size out of allowed bounds")
    return {"resource_id": str(item.get("id", "")), "title": RESOURCE_TITLE, "url": url, "declared_bytes": size, "catalogue_sha256": sha256(catalogue)}


def verify_dictionary(content: bytes) -> str:
    if len(content) > MAX_DOCUMENT_BYTES:
        raise Blocked("dictionary byte cap exceeded")
    text = content.decode("utf-8-sig", errors="strict")
    # Exact provider scientific terms: 10-minute mean, hourly maximum instantaneous
    # and 3-second averaged maximum are three DIFFERENT physical wind variables.
    rules = {"FF": "10 mn", "FXI": "instantan", "FXI3S": "3 secondes", "STATUS_FXI3S": "fonction de transfert"}
    for key, marker in rules.items():
        match = re.search(r"(?m)^\s*" + re.escape(key) + r"\s*:\s*([^\r\n]+)", text)
        if not match or marker.casefold() not in match.group(1).casefold():
            raise Blocked(f"official field dictionary missing semantics: {key}")
    return sha256(content)


def audit_gzip(source: bytes, *, expected_sha256: str | None = None) -> dict[str, object]:
    if len(source) > MAX_GZIP_BYTES or len(source) < 18 or not source.startswith(b"\x1f\x8b"):
        raise Blocked("invalid or oversized gzip original")
    digest = sha256(source)
    if expected_sha256 is not None and expected_sha256 != digest:
        raise Blocked("original gzip byte SHA-256 mismatch")
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(source)) as archive:
            data = archive.read(MAX_CSV_BYTES + 1)
    except (EOFError, OSError) as exc:
        raise Blocked("invalid gzip payload") from exc
    if len(data) > MAX_CSV_BYTES:
        raise Blocked("inflated original CSV exceeds cap")
    try:
        stream = io.StringIO(data.decode("utf-8-sig"), newline="")
    except UnicodeError as exc:
        raise Blocked("original CSV is not valid UTF-8") from exc
    try:
        reader = csv.DictReader(stream, delimiter=";")
        if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise Blocked("original CSV header absent or duplicate")
        if any(k not in reader.fieldnames for k in FIELDS):
            raise Blocked("original CSV lacks required station, timestamp, or wind fields")
        if len(reader.fieldnames) < len(FIELDS) + 1:
            raise Blocked("implausibly short original CSV header")
        count = 0
        station_ids: set[str] = set()
        valid_3s = 0
        derived_3s = 0
        not_computed_3s = 0
        quality_counts: Counter[str] = Counter()
        wind_populated = Counter()
        for row in reader:
            count += 1
            if count > MAX_ROWS:
                raise Blocked("original station row cap exceeded")
            if None in row:
                raise Blocked("malformed CSV row with excess fields")
            station = row["NUM_POSTE"].strip()
            stamp = row["AAAAMMJJHH"].strip()
            if not re.fullmatch(r"\d{8}", station) or not re.fullmatch(r"202[0-4]\d{6}", stamp):
                raise Blocked("station ID or hourly timestamp violates fixed France-2020-2024 profile")
            station_ids.add(station)
            if len(station_ids) > MAX_STATIONS:
                raise Blocked("too many stations for single department")
            for name in ("FF", "FXI", "FXI3S"):
                v = row[name].strip()
                if v:
                    try:
                        n = float(v)
                    except ValueError as exc:
                        raise Blocked("invalid numeric wind variable") from exc
                    if not 0 <= n <= 120 or n != n:
                        raise Blocked("negative, nonfinite or physically implausible wind")
                    wind_populated[name] += 1
            gust = row["FXI3S"].strip()
            status = row["STATUS_FXI3S"].strip()
            quality = row.get("QFXI3S", "").strip()
            quality_counts[quality or "missing"] += 1
            if gust and quality in QUALITY_OK:
                valid_3s += 1
                if status == "1":
                    derived_3s += 1
                elif status == "0":
                    not_computed_3s += 1
                elif status:
                    raise Blocked("unsupported 3-second-gust calculation status")
        if not count:
            raise Blocked("original CSV contains no rows")
    except (csv.Error, TypeError, AttributeError) as exc:
        raise Blocked("malformed original CSV") from exc
    return {
        "original_gzip_sha256": digest,
        "original_gzip_bytes": len(source),
        "original_csv_bytes": len(data),
        "rows": count,
        "stations": len(station_ids),
        "nonmissing_wind_columns": dict(sorted(wind_populated.items())),
        "quality_checked_three_second_gusts": valid_3s,
        "status_calculated_three_second_gusts": derived_3s,
        "status_not_calculated_three_second_gusts": not_computed_3s,
        "quality_codes_three_second_gusts": dict(sorted(quality_counts.items())),
        "annual_ep_authorized": False,
        "source_admitted": False,
        "insured_loss_calibration_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--live", action="store_true", help="fetch one fixed public France 2020-2024 original")
    mode.add_argument("--original-gz", type=Path, help="offline original source gzip")
    parser.add_argument("--expected-sha256", help="require this full original gzip byte hash")
    args = parser.parse_args(argv)
    try:
        if args.live:
            dictionary_sha = verify_dictionary(_read_url(DOCUMENT_URL, MAX_DOCUMENT_BYTES))
            metadata = resolve_resource(_read_url(CATALOGUE_URL, MAX_CATALOGUE_BYTES))
            source = _read_url(str(metadata["url"]), MAX_GZIP_BYTES)
            result = audit_gzip(source)
            result.update({"dictionary_sha256": dictionary_sha, **metadata})
        else:
            result = audit_gzip(args.original_gz.read_bytes(), expected_sha256=args.expected_sha256)
        print(json.dumps(result, sort_keys=True, indent=2))
        return 0
    except (Blocked, OSError, UnicodeError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
