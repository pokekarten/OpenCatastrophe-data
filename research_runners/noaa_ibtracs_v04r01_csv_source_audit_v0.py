# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Read-only source-pinned QA for the historical original NOAA IBTrACS ALL CSV.

This does not download anything. Identity/aggregate expectations are sourced
from docs/research/executed-source-findings-20261103.md (acquired 2026-11-02).
The approved access/noaa.ncei.ibtracs.v04r01.json describes a DIFFERENT NetCDF
distribution: it cannot authorize this CSV acquisition or commercial model use.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re

SOURCE_ID = "noaa.ncei.ibtracs.v04r01"
ORIGINAL_CSV = "ibtracs.ALL.list.v04r01.csv"
ORIGINAL_URL = (
    "https://www.ncei.noaa.gov/data/"
    "international-best-track-archive-for-climate-stewardship-ibtracs/"
    "v04r01/access/csv/ibtracs.ALL.list.v04r01.csv"
)
PINNED_BYTES = 333_183_438
PINNED_SHA256 = "7a11978ceba2953754b75bcc99bf1cfc8f00046aa5054054573edc904240d820"
PINNED_DATA_ROWS = 730_416
PINNED_STORM_IDS = 13_631
PINNED_LON_GT_180 = 10_658
PINNED_COLUMNS = 174
MAX_RECORDS = 1_000_000
REQUIRED = ("SID", "SEASON", "BASIN", "ISO_TIME", "LAT", "LON", "WMO_WIND", "USA_WIND", "TRACK_TYPE")
ISO_TIME = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")


class IBTrACSAuditError(ValueError):
    """Original identity or native science-shape gate is blocked."""


def audit_rows(reader: object, *, expected_columns: int = PINNED_COLUMNS,
               max_records: int = MAX_RECORDS) -> dict[str, int]:
    """Parse a local CSV stream, returning only safe aggregate diagnostics."""
    rows = csv.reader(reader, strict=True)
    try:
        header = next(rows)
        units = next(rows)
    except (StopIteration, csv.Error) as exc:
        raise IBTrACSAuditError("missing complete two-line CSV header/units") from exc
    if len(header) != expected_columns or len(set(header)) != len(header):
        raise IBTrACSAuditError("wrong number of columns or duplicate headers")
    if any(name not in header for name in REQUIRED):
        raise IBTrACSAuditError("required original NOAA columns missing")
    if len(units) != expected_columns or units[0].strip():
        raise IBTrACSAuditError("original column-units row missing or malformed")
    index = {key: header.index(key) for key in REQUIRED}
    if not units[index["LAT"]].strip() or not units[index["LON"]].strip():
        raise IBTrACSAuditError("native coordinate units missing")
    storm_ids: set[str] = set()
    count = over_180 = 0
    for row in rows:
        count += 1
        if count > max_records:
            raise IBTrACSAuditError("bounded CSV record limit exceeded")
        if len(row) != expected_columns:
            raise IBTrACSAuditError("ragged original CSV observation")
        sid = row[index["SID"]].strip()
        if not sid or not ISO_TIME.fullmatch(row[index["ISO_TIME"]].strip()):
            raise IBTrACSAuditError("missing SID or malformed ISO_TIME")
        storm_ids.add(sid)
        try:
            lat, lon = float(row[index["LAT"]]), float(row[index["LON"]])
        except ValueError as exc:
            raise IBTrACSAuditError("missing or nonnumeric native coordinates") from exc
        if not all(map(math.isfinite, (lat, lon))) or not (-90 <= lat <= 90) or not (-180 <= lon <= 360):
            raise IBTrACSAuditError("out-of-domain original coordinate")
        if lon > 180:
            over_180 += 1
    if not count:
        raise IBTrACSAuditError("no source observation rows")
    return {"data_rows": count, "distinct_storm_ids": len(storm_ids),
            "longitude_gt_180_rows": over_180, "column_count": len(header)}


def audit_original_file(path: Path, *, expected_bytes: int = PINNED_BYTES,
                        expected_sha256: str = PINNED_SHA256,
                        expected_metrics: tuple[int, int, int] = (
                            PINNED_DATA_ROWS, PINNED_STORM_IDS, PINNED_LON_GT_180),
                        expected_columns: int = PINNED_COLUMNS) -> dict[str, object]:
    """Compare original bytes to independent SHA before parsing, no network."""
    try:
        before = path.stat()
        if not path.is_file() or before.st_size != expected_bytes:
            raise IBTrACSAuditError("original CSV byte count does not match receipt")
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1 << 20), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected_sha256:
            raise IBTrACSAuditError("original CSV SHA-256 does not match receipt")
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            metrics = audit_rows(source, expected_columns=expected_columns)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise IBTrACSAuditError("source changed during read-only audit")
    except (OSError, UnicodeError, csv.Error) as exc:
        raise IBTrACSAuditError("cannot read complete original CSV") from exc
    observed = (metrics["data_rows"], metrics["distinct_storm_ids"],
                metrics["longitude_gt_180_rows"])
    if observed != expected_metrics:
        raise IBTrACSAuditError("source aggregate metrics do not match pinned receipt")
    return {
        "source_id": SOURCE_ID, "source_distribution": ORIGINAL_CSV,
        "original_url": ORIGINAL_URL, "original_bytes": before.st_size,
        "original_sha256": digest.hexdigest(), **metrics,
        "rights_approved_for_commercial_model": False,
        "source_admitted": False, "model_input_approved": False,
        "native_longitude_gt_180_is_not_invalid": True,
        "agency_wind_averaging_harmonized": False,
        "track_type_provisional_and_spur_review_pending": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-csv", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = audit_original_file(args.original_csv)
    except IBTrACSAuditError as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
