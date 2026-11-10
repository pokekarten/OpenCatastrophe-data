# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline-only Blue Heart measurement/QC timestamp alignment preflight.

This gate intentionally does not infer UTC for the offset-naive raw highway
gully times described by Zenodo 20699635 README. It reads bounded LOCAL files,
never fetches a provider, and prints only aggregate match statistics.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from research_runners.blue_heart_index_preflight_v0 import (
    BlueHeartPreflightError,
    explicit_utc_timestamp,
)


def _read_explicit_utc_instants(path: Path, *, max_rows: int) -> set[str]:
    """Read a bounded timestamp column; duplicate or naive times fail closed."""

    times: set[str] = set()
    with Path(path).open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        headers = reader.fieldnames
        if headers is None or headers.count("timestamp") != 1:
            raise BlueHeartPreflightError("timestamp column missing or duplicated")
        for index, row in enumerate(reader, start=1):
            if index > max_rows:
                raise BlueHeartPreflightError("timestamp preflight row limit exceeded")
            instant = explicit_utc_timestamp(row.get("timestamp"))
            if instant in times:
                raise BlueHeartPreflightError("repeated UTC instant in one measurement or QC file")
            times.add(instant)
    if not times:
        raise BlueHeartPreflightError("timestamp file contains no records")
    return times


def inspect_timestamp_pair(
    measurement_csv: Path,
    quality_csv: Path,
    *,
    max_rows: int = 50000,
) -> dict[str, object]:
    """Check time-index integrity without joining measurements to QC labels.

    This check is only relevant after file-level rights and physical clock
    provenance have been independently established. Equal instants are not a
    guarantee of matching parameter column semantics or valid measurements.
    """

    if max_rows < 1 or max_rows > 1_000_000:
        raise BlueHeartPreflightError("max_rows must be between 1 and 1000000")
    measurements = _read_explicit_utc_instants(measurement_csv, max_rows=max_rows)
    quality = _read_explicit_utc_instants(quality_csv, max_rows=max_rows)
    overlap = len(measurements & quality)
    unmatched_raw = len(measurements - quality)
    unmatched_qc = len(quality - measurements)
    exact = unmatched_raw == 0 and unmatched_qc == 0
    return {
        "raw_timestamp_count": len(measurements),
        "quality_timestamp_count": len(quality),
        "matched_timestamp_count": overlap,
        "raw_without_quality_count": unmatched_raw,
        "quality_without_raw_count": unmatched_qc,
        "timestamp_sets_identical": exact,
        "timestamp_alignment_approved": exact,
        "physical_clock_provenance_verified": False,
        "source_bytes_admitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare local measurement and QC timestamps (offline and aggregate only)"
    )
    parser.add_argument("--measurements", required=True, type=Path)
    parser.add_argument("--quality", required=True, type=Path)
    parser.add_argument("--max-rows", type=int, default=50000)
    args = parser.parse_args()
    try:
        result = inspect_timestamp_pair(
            args.measurements, args.quality, max_rows=args.max_rows
        )
    except (BlueHeartPreflightError, OSError, UnicodeError, csv.Error) as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
