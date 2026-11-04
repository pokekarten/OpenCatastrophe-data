#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One fixed ACT BD-Adresses original CSV: full-byte proof and aggregate QA.

This is a bounded, opt-in source-science diagnostic; it neither publishes
addresses nor creates insured objects, admitted source assets, or database rows.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import statistics
import tempfile
from urllib.error import URLError
from urllib.request import Request, build_opener

from scripts.probe_lu_bd_adresses_metadata_v0 import ASSETS, NoRedirect

SOURCE = ASSETS[1]
RESOURCE_ID, FILENAME, VINTAGE, PUBLISHER_MD5, _LOW, _HIGH = SOURCE
URL = f"https://download.data.public.lu/resources/adresses-georeferencees-bd-adresses/{VINTAGE}/{FILENAME}"
# Sourced from the exact publisher resource record, read 2026-11-04.
EXPECTED_SIZE = 28_209_815
MAX_BYTES = 32_000_000
MAX_ROWS = 1_000_000
CHUNK = 65536
HEADER = (
    "rue", "numero", "localite", "code_postal", "id_caclr_rue", "id_caclr_bat",
    "lat_wgs84", "lon_wgs84", "coord_est_luref", "coord_nord_luref",
    "id_geoportail", "commune", "lau2",
)


class OriginalAddressError(ValueError):
    """Hard source-version or original CSV structure failure, no row content."""


def _valid_number(value: str, lo: float, hi: float) -> float | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        number = float(value)
    except ValueError as exc:
        raise OriginalAddressError("Original coordinate is not numeric") from exc
    if not math.isfinite(number) or not lo <= number <= hi:
        raise OriginalAddressError("Original coordinate outside reviewed bounds")
    return number


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r1, a1, r2, a2 = map(math.radians, (lat1, lon1, lat2, lon2))
    h = math.sin((r2-r1)/2)**2 + math.cos(r1)*math.cos(r2)*math.sin((a2-a1)/2)**2
    return 2*6371008.8*math.asin(math.sqrt(max(0.0, min(1.0, h))))


def _percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    vals = sorted(values)
    pos = (len(vals)-1)*pct
    lo = math.floor(pos); hi = math.ceil(pos)
    return vals[lo] + (vals[hi]-vals[lo])*(pos-lo)


def inspect_csv(original_file, *, transformer=None) -> dict:
    """Parse a verified original CSV; emit only aggregates and fingerprints.

    Optional transformer follows pyproj always_xy: x/y EPSG:2169 to lon/lat
    EPSG:4326. The input is never emitted. Header is authoritative exact shape.
    """
    original_file.seek(0)
    with io.TextIOWrapper(original_file, encoding="utf-8-sig", newline="") as decoded:
        reader = csv.reader(decoded, delimiter=";", strict=True)
        try:
            header = next(reader)
        except (StopIteration, UnicodeError, csv.Error) as exc:
            raise OriginalAddressError("Original CSV header unreadable") from exc
        if tuple(header) != HEADER:
            raise OriginalAddressError("Original CSV header changed from pinned 13-column version")
        rows = 0
        missing_wgs = 0
        missing_luref = 0
        missing_ids = 0
        duplicate_coordinate_rows = 0
        repeated_address_id_rows = 0
        seen_coords: set[tuple[str, str]] = set()
        seen_address_ids: set[str] = set()
        differences: list[float] = []
        for row in reader:
            rows += 1
            if rows > MAX_ROWS:
                raise OriginalAddressError("Original CSV exceeds reviewed row budget")
            if len(row) != len(HEADER):
                raise OriginalAddressError("Original CSV row width mismatch")
            # Avoid holding street/address content or returning any individual ID.
            lat = _valid_number(row[6], 49.0, 51.0)
            lon = _valid_number(row[7], 5.0, 8.0)
            east = _valid_number(row[8], 25_000, 130_000)
            north = _valid_number(row[9], 25_000, 160_000)
            if (lat is None) != (lon is None) or (east is None) != (north is None):
                raise OriginalAddressError("Partial original coordinate pair")
            if lat is None:
                missing_wgs += 1
            else:
                key = (row[6], row[7])
                if key in seen_coords:
                    duplicate_coordinate_rows += 1
                else:
                    seen_coords.add(key)
            if east is None:
                missing_luref += 1
            if transformer is not None and None not in (lat, lon, east, north):
                projected_lon, projected_lat = transformer.transform(east, north)
                if not math.isfinite(projected_lon) or not math.isfinite(projected_lat):
                    raise OriginalAddressError("LUREF transform returned non-finite coordinates")
                differences.append(_haversine_m(lat, lon, projected_lat, projected_lon))
            address_id = row[5].strip()
            if not address_id:
                missing_ids += 1
            elif address_id in seen_address_ids:
                repeated_address_id_rows += 1
            else:
                seen_address_ids.add(address_id)
        if rows == 0:
            raise OriginalAddressError("Original CSV has no records")
        return {
            "row_count": rows,
            "schema_column_count": len(HEADER),
            "schema_header_sha256": hashlib.sha256(";".join(HEADER).encode("utf-8")).hexdigest(),
            "missing_wgs84_pairs": missing_wgs,
            "missing_luref_pairs": missing_luref,
            "duplicate_exact_coordinate_rows": duplicate_coordinate_rows,
            "distinct_exact_coordinate_pairs": len(seen_coords),
            "missing_caclr_building_ids": missing_ids,
            "repeated_caclr_building_id_rows": repeated_address_id_rows,
            "paired_crs_transform_evaluated": transformer is not None,
            "paired_crs_transform_observations": len(differences),
            "paired_crs_error_median_m": None if not differences else round(statistics.median(differences), 3),
            "paired_crs_error_p95_m": None if not differences else round(_percentile(differences, .95), 3),
            "paired_crs_error_max_m": None if not differences else round(max(differences), 3),
            "coordinate_source_independent": False,
            "building_identity_proven": False,
            "rights_admitted": False,
            "cat_model_input_admitted": False,
        }


def verify_original_stream(source, *, expected_size: int = EXPECTED_SIZE,
                           expected_md5: str = PUBLISHER_MD5, transformer=None) -> dict:
    """Single pass full source-byte MD5/SHA256 check; bounded spooled disk."""
    size = 0
    md5 = hashlib.md5()  # nosec B324: publisher's metadata checksum, not for security
    sha = hashlib.sha256()
    with tempfile.TemporaryFile(mode="w+b") as spool:
        while True:
            chunk = source.read(CHUNK)
            if not chunk:
                break
            if type(chunk) is not bytes:
                raise OriginalAddressError("Provider source not a byte stream")
            size += len(chunk)
            if size > MAX_BYTES or size > expected_size:
                raise OriginalAddressError("Source exceeds fixed original byte budget")
            spool.write(chunk)
            md5.update(chunk); sha.update(chunk)
        if size != expected_size or md5.hexdigest().lower() != expected_md5:
            raise OriginalAddressError("Original byte count/MD5 did not match fixed provider receipt")
        report = inspect_csv(spool, transformer=transformer)
    return {
        "profile": "lu-bd-adresses-original-csv-v0",
        "original_source_url": URL,
        "official_resource_id": RESOURCE_ID,
        "source_vintage": "2026-11-02",
        "original_size_bytes": size,
        "publisher_md5_matched": True,
        "original_sha256_computed": sha.hexdigest(),
        "source_rows_ever_logged": False,
        "original_bytes_stored_in_git": False,
        **report,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Opt in to one full 28.2 MB official-original GET")
    parser.add_argument("--transform", action="store_true", help="Use independent pyproj EPSG2169-to-4326 numerical check")
    args = parser.parse_args(argv)
    if not args.live:
        print("Offline default: original source not downloaded; --live is explicit")
        return 0
    try:
        transformer = None
        if args.transform:
            from pyproj import Transformer
            transformer = Transformer.from_crs("EPSG:2169", "EPSG:4326", always_xy=True)
        request = Request(URL, method="GET", headers={"Accept": "text/csv", "Accept-Encoding": "identity",
                    "User-Agent": "OpenCatastrophe-original-source-quality/0"})
        with build_opener(NoRedirect()).open(request, timeout=45) as response:
            if response.getcode() != 200:
                raise OriginalAddressError("Original provider returned unexpected HTTP status")
            report = verify_original_stream(response, transformer=transformer)
    except (OSError, URLError, ValueError, ImportError, UnicodeError, csv.Error):
        # Never echo a provider CSV line, address, raw input URL or runtime data.
        print("BLOCKED: original source could not be safely validated")
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
