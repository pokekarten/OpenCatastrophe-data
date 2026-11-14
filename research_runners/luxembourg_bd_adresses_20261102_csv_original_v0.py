#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exact-resource, aggregate-only ACT BD-Adresses 2026-11-02 CSV preflight.

Source bytes are read only from a user-provided local temporary original CSV.
Never print values, individual rows, IDs, coordinates, or copied address data.
Original source usage is not CAT model admission or a building identity match.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys

ORIGINAL_URL = ("https://download.data.public.lu/resources/"
                "adresses-georeferencees-bd-adresses/20261102-033122/addresses.csv")
RESOURCE_ID = "5cadc5b8-6a7d-4283-87bc-f9e58dd771f7"
ORIGINAL_MD5 = "946114c1a24b49471b580bc225e4cb25"
ORIGINAL_BYTES = 28209815
MAX_BYTES = 32 * 1024 * 1024
MAX_ROWS = 600_000
MAX_COLUMNS = 80
MAX_FIELD_BYTES = 32768
HEX_MD5 = re.compile(r"^[a-f0-9]{32}$")
ALLOWED_DELIMITERS = ",;\t"


class AddressCsvError(ValueError):
    """Block unsafe or nonmatching exact source; never echo address values."""


def digests(path: Path) -> tuple[int, str, str]:
    if path.is_symlink() or not path.is_file():
        raise AddressCsvError("original file must be regular and not symlink")
    size = path.stat().st_size
    if not 0 < size <= MAX_BYTES:
        raise AddressCsvError("original CSV file exceeds byte cap or is empty")
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    with path.open("rb") as fh:
        while block := fh.read(1024 * 1024):
            md5.update(block)
            sha256.update(block)
    return size, md5.hexdigest(), sha256.hexdigest()


def _detect_dialect(sample: str):
    if not sample or "\x00" in sample:
        raise AddressCsvError("not a safe nonbinary CSV prefix")
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=ALLOWED_DELIMITERS)
    except csv.Error as exc:
        raise AddressCsvError("could not determine original CSV dialect") from exc
    if dialect.delimiter not in ALLOWED_DELIMITERS:
        raise AddressCsvError("unexpected original CSV delimiter")
    return dialect


def _coordinates(columns: list[str]) -> tuple[int, int] | None:
    norm = [re.sub(r"[^a-z0-9]+", "", x.casefold()) for x in columns]
    lat_names = {"lat", "latitude", "latitudewgs84", "wgs84lat", "wgs84latitude",
                 "latwgs84", "geomlat"}
    lon_names = {"lon", "long", "longitude", "longitudewgs84", "wgs84lon",
                 "wgs84longitude", "lonwgs84", "geomlon"}
    lat = [i for i, name in enumerate(norm) if name in lat_names]
    lon = [i for i, name in enumerate(norm) if name in lon_names]
    if len(lat) != 1 or len(lon) != 1 or lat[0] == lon[0]:
        return None
    return lat[0], lon[0]


def _numeric(raw: str, limit: float) -> float | None:
    value = raw.strip()
    if not value:
        return None
    # A semicolon-delimited source may use a decimal comma.
    if value.count(",") == 1 and "." not in value:
        value = value.replace(",", ".")
    try:
        num = float(value)
    except ValueError:
        return None
    if not math.isfinite(num) or abs(num) > limit:
        return None
    return num


def inspect(source: Path, *, expected_size: int = ORIGINAL_BYTES,
            expected_md5: str = ORIGINAL_MD5) -> dict:
    if type(expected_size) is not int or not 0 < expected_size <= MAX_BYTES:
        raise AddressCsvError("invalid exact-source size contract")
    if not isinstance(expected_md5, str) or not HEX_MD5.fullmatch(expected_md5):
        raise AddressCsvError("invalid original MD5 contract")
    size, md5, sha256 = digests(Path(source))
    if size != expected_size or md5 != expected_md5:
        raise AddressCsvError("original CSV does not match exact pinned provider bytes")

    old_limit = csv.field_size_limit()
    csv.field_size_limit(MAX_FIELD_BYTES)
    try:
        with Path(source).open("r", encoding="utf-8-sig", errors="strict", newline="") as stream:
            sample = stream.read(16384)
            dialect = _detect_dialect(sample)
            stream.seek(0)
            reader = csv.reader(stream, dialect)
            try:
                columns = next(reader)
            except StopIteration as exc:
                raise AddressCsvError("empty CSV") from exc
            if not 2 <= len(columns) <= MAX_COLUMNS:
                raise AddressCsvError("source column count out of bounded range")
            if any(not field or len(field) > 128 or "\x00" in field for field in columns):
                raise AddressCsvError("source field header invalid")
            if len({field.casefold() for field in columns}) != len(columns):
                raise AddressCsvError("source column names are not unique")
            coord_cols = _coordinates(columns)
            count = 0
            missing_pair = 0
            malformed_pair = 0
            valid_pair = 0
            duplicate_pair = 0
            seen: set[tuple[str, str]] = set()
            for row in reader:
                if len(row) != len(columns):
                    raise AddressCsvError("CSV row width mismatch")
                count += 1
                if count > MAX_ROWS:
                    raise AddressCsvError("original CSV rows exceed budget")
                if coord_cols is None:
                    continue
                lat_text, lon_text = row[coord_cols[0]].strip(), row[coord_cols[1]].strip()
                if not lat_text or not lon_text:
                    missing_pair += 1
                    continue
                lat, lon = _numeric(lat_text, 90), _numeric(lon_text, 180)
                if lat is None or lon is None:
                    malformed_pair += 1
                    continue
                valid_pair += 1
                # String-level duplicates are a strict lower bound only:
                # equivalent decimals may have different lexical forms.
                key = (lat_text, lon_text)
                if key in seen:
                    duplicate_pair += 1
                else:
                    seen.add(key)
    except (UnicodeError, csv.Error) as exc:
        raise AddressCsvError("original CSV encoding, quoting or field limit invalid") from exc
    finally:
        csv.field_size_limit(old_limit)
    if count == 0:
        raise AddressCsvError("original source CSV has no data rows")
    return {
        "source": "lu.act.bd-adresses.csv.2026-11-02",
        "resource_id": RESOURCE_ID,
        "publisher_original_md5_verified": md5,
        "observed_original_sha256": sha256,
        "observed_original_bytes": size,
        "column_count": len(columns),
        "column_names_only": columns,
        "csv_delimiter": dialect.delimiter,
        "observed_data_rows": count,
        "wgs84_coordinate_columns_identified": coord_cols is not None,
        "coordinate_quality": None if coord_cols is None else {
            "valid_wgs84_coordinate_pairs": valid_pair,
            "missing_coordinate_pairs": missing_pair,
            "malformed_or_out_of_range_pairs": malformed_pair,
            "duplicate_exact_coordinate_text_pairs_excess": duplicate_pair,
        },
        "raw_address_rows_exported": 0,
        "analysis_only": True,
        "rights_approved": False,
        "independent_building_identity_proven": False,
        "cat_model_input_admitted": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-csv", type=Path, required=True,
                        help="locally acquired exact 2026-11-02 original; not downloaded by this script")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(inspect(args.source_csv), sort_keys=True, indent=2))
        return 0
    except (OSError, ValueError, OverflowError):
        print("BLOCKED: original address CSV failed exact-source or aggregate-quality checks",
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
