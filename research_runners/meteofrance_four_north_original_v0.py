# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded, independent original Météo-France northern hourly gust preflight.

Data and station IDs are not published. Original source digests are observation
receipts, NOT proof of physical equivalence, loss calibration or rights admission.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import datetime
import gzip
import io
import json
import re
import sys

from research_runners.meteofrance_hourly_gust_v0 import (
    Blocked, _read_url, sha256, verify_dictionary, DOCUMENT_URL, MAX_DOCUMENT_BYTES,
    CATALOGUE_URL, MAX_CATALOGUE_BYTES,
)
from research_runners.meteofrance_north_hourly_catalogue_v0 import audit_catalogue, BASE

# ID, compressed byte count, initial original SHA-256 (not yet observed).
# SHA-256 must be set from actual first CI proof before further use.
ASSETS = {
    "02": ("3ae65545-9ce4-4227-a184-111bad9d0185", 19_437_733, None),
    "62": ("fb9e6687-3ae8-4ed9-b106-be22db8d1fa1", 25_053_359, None),
    "76": ("31c4683e-5538-4832-96ef-1f2568051019", 26_582_693, None),
    "80": ("1a936a45-b6ad-4c2b-84cf-cb4c853938b7", 21_177_200, None),
}
MAX_COMPRESSED = 32 * 1024 * 1024
MAX_INFLATED = 384 * 1024 * 1024
MAX_ROWS = 1_600_000
MAX_STATIONS = 2500
FIELDS = ("NUM_POSTE", "AAAAMMJJHH", "FF", "FXI", "FXI3S", "QFXI3S", "STATUS_FXI3S")


def asset_url(dep: str) -> str:
    if dep not in ASSETS:
        raise Blocked("unknown fixed department identity")
    return BASE + "H_" + dep + "_previous-2020-2024.csv.gz"


def check_identity(catalogue: dict, dep: str) -> dict:
    if dep not in ASSETS:
        raise Blocked("not a selected original department")
    entries = [r for r in catalogue.get("sources", []) if r.get("department") == dep]
    if len(entries) != 1:
        raise Blocked("catalogue resource identity is not unique")
    entry = entries[0]
    ident, size, _ = ASSETS[dep]
    if (entry.get("resource_id") != ident
            or entry.get("declared_compressed_bytes") != size
            or entry.get("original_url") != asset_url(dep)
            or entry.get("source_admitted") is not False
            or entry.get("original_bytes_fetched") is not False):
        raise Blocked("catalogue UUID, source path, byte length or admission flag changed")
    return entry


class LimitedInflation(io.RawIOBase):
    """Count source uncompressed bytes without materializing the CSV."""
    def __init__(self, gzip_file: gzip.GzipFile, byte_cap: int):
        super().__init__()
        self.gz = gzip_file
        self.byte_cap = byte_cap
        self.bytes_read = 0

    def readable(self) -> bool:
        return True

    def readinto(self, buf) -> int:
        n = self.gz.readinto(buf)
        if n is None:
            n = 0
        self.bytes_read += n
        if self.bytes_read > self.byte_cap:
            raise Blocked("inflated original exceeds byte cap")
        return n


def audit_original(dep: str, source: bytes, *, inflated_cap: int = MAX_INFLATED) -> dict:
    if dep not in ASSETS:
        raise Blocked("unsupported original department")
    rid, declared_size, expected_sha = ASSETS[dep]
    if type(source) is not bytes or len(source) != declared_size or len(source) > MAX_COMPRESSED:
        raise Blocked("original compressed size differs from official catalogue")
    if not source.startswith(b"\x1f\x8b"):
        raise Blocked("original not gzip")
    hash_value = sha256(source)
    if expected_sha is not None and hash_value != expected_sha:
        raise Blocked("original SHA-256 differs from verified exact-byte receipt")
    stations: set[str] = set()
    count = good = derived = not_derived = 0
    qc: Counter[str] = Counter()
    nonmissing: Counter[str] = Counter()
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(source)) as f:
            bounded = LimitedInflation(f, inflated_cap)
            with io.TextIOWrapper(io.BufferedReader(bounded), encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream, delimiter=";")
                if (reader.fieldnames is None
                        or len(reader.fieldnames) != len(set(reader.fieldnames))
                        or any(c not in reader.fieldnames for c in FIELDS)):
                    raise Blocked("original source missing hourly gust/QC columns")
                for row in reader:
                    count += 1
                    if count > MAX_ROWS:
                        raise Blocked("original exceeds row cap")
                    if None in row or any(v is None for v in row.values()):
                        raise Blocked("invalid source CSV row")
                    station, stamp = row["NUM_POSTE"].strip(), row["AAAAMMJJHH"].strip()
                    if (not re.fullmatch(r"\d{8}", station)
                            or not station.startswith(dep)
                            or not re.fullmatch(r"202[0-4]\d{6}", stamp)):
                        raise Blocked("source station or hourly identity outside fixed window")
                    try:
                        datetime.strptime(stamp, "%Y%m%d%H")
                    except ValueError as exc:
                        raise Blocked("invalid real UTC hour") from exc
                    stations.add(station)
                    if len(stations) > MAX_STATIONS:
                        raise Blocked("source station cap exceeded")
                    for field in ("FF", "FXI", "FXI3S"):
                        v = row[field].strip()
                        if v:
                            try:
                                n = float(v)
                            except ValueError as exc:
                                raise Blocked("source wind is not numeric") from exc
                            if not 0 <= n <= 120 or n != n:
                                raise Blocked("nonfinite or physically implausible wind")
                            nonmissing[field] += 1
                    q = row["QFXI3S"].strip() or "missing"
                    if q not in ("0", "1", "2", "9", "missing"):
                        raise Blocked("unknown original wind quality code")
                    qc[q] += 1
                    if row["FXI3S"].strip() and q in ("0", "1"):
                        good += 1
                        status = row["STATUS_FXI3S"].strip()
                        if status == "1":
                            derived += 1
                        elif status == "0":
                            not_derived += 1
                        elif status:
                            raise Blocked("unrecognized FXI3S transfer reconstruction flag")
                uncompressed_bytes = bounded.bytes_read
    except (OSError, EOFError, UnicodeError, csv.Error) as exc:
        raise Blocked("original gzip/CSV was unreadable or incomplete") from exc
    if not count or not good or good != derived + not_derived:
        raise Blocked("original had no complete quality-checked 3s gust lineage")
    return {
        "department": dep, "resource_id": rid, "original_url": asset_url(dep),
        "original_gzip_bytes": declared_size, "original_gzip_sha256": hash_value,
        "original_sha256_pinned": expected_sha is not None,
        "original_csv_bytes": uncompressed_bytes, "rows": count,
        "stations": len(stations), "nonmissing_wind_columns": dict(sorted(nonmissing.items())),
        "quality_codes_three_second_gusts": dict(sorted(qc.items())),
        "quality_checked_three_second_gusts": good,
        "status_calculated_three_second_gusts": derived,
        "status_not_calculated_three_second_gusts": not_derived,
        "original_provider_bytes_committed": False,
        "source_admitted": False, "annual_ep_authorized": False,
        "insured_loss_calibration_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--department", choices=sorted(ASSETS), required=True)
    p.add_argument("--live", action="store_true", required=True)
    args = p.parse_args(argv)
    try:
        metadata = audit_catalogue(_read_url(CATALOGUE_URL, MAX_CATALOGUE_BYTES))
        check_identity(metadata, args.department)
        dictionary_hash = verify_dictionary(_read_url(DOCUMENT_URL, MAX_DOCUMENT_BYTES))
        original = _read_url(asset_url(args.department), MAX_COMPRESSED)
        result = audit_original(args.department, original)
        result.update({"profile": "meteofrance-four-north-original-2020-2024-v0",
                       "catalogue_sha256": metadata["catalogue_sha256"],
                       "dictionary_sha256": dictionary_hash})
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (Blocked, OSError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
