# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline, metadata-only Blue Heart index and timestamp/QA preflight.

Source contract: Zenodo 20699635 README.md, 6995 original-byte intermediary
receipt SHA-256 ff9b0259b579cae0a36d5f8388928f3e251cfece348be6edcd25b607f19112c7.
This tool does not fetch provider data or grant licence/model-use admission.
Only aggregate counts are returned; source coordinates/identifiers are not printed.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Mapping


class BlueHeartPreflightError(ValueError):
    """Fail closed when Blue Heart metadata cannot be safely interpreted."""


GAUGE_TYPES = frozenset({"Borehole", "Fluvial", "Sewer", "Highway gully", "Rain"})
OPTIONAL_NUMERIC_BY_GAUGE = {
    "floodThreshold_mm": "Highway gully",
    "bedLevelEstimate_mAOD": "Fluvial",
    "bankLevelEstimate_mAOD": "Fluvial",
}
REQUIRED_COLUMNS = frozenset(
    {
        "locationLatitude",
        "locationLongitude",
        "gaugeType",
        "dataPath",
        "dataQualityFlagsPath",
        "gaugeParameters",
        "parameterUnits",
        "gaugeOwner",
        *OPTIONAL_NUMERIC_BY_GAUGE,
    }
)
QUALITY_CATEGORIES = {"1": "good", "2": "suspect", "3": "bad"}
QUALITY_RE = re.compile(r"^([123])([A-E]*)$")
OFFSET_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


def parse_quality_label(label: str) -> tuple[str, tuple[str, ...]]:
    """Parse README codes without treating missing or suspect values as good."""

    if not isinstance(label, str) or not label.strip():
        raise BlueHeartPreflightError("missing quality label must not be inferred as good")
    match = QUALITY_RE.fullmatch(label.strip())
    if match is None:
        raise BlueHeartPreflightError("quality label must be 1/2/3 with optional A-E reasons")
    digit, reasons = match.groups()
    if len(set(reasons)) != len(reasons):
        raise BlueHeartPreflightError("duplicate quality reason")
    if digit == "1" and reasons:
        raise BlueHeartPreflightError("a good observation cannot carry failure reason labels")
    return QUALITY_CATEGORIES[digit], tuple(reasons)


def explicit_utc_timestamp(value: str) -> str:
    """Convert only offset-bearing instants, never assume a gully device timezone."""

    if not isinstance(value, str) or not OFFSET_TIMESTAMP_RE.fullmatch(value.strip()):
        raise BlueHeartPreflightError(
            "timestamp requires an explicit UTC offset; source highway-gully raw times are ambiguous"
        )
    try:
        instant = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise BlueHeartPreflightError("invalid offset-bearing timestamp") from exc
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise BlueHeartPreflightError("missing timezone")
    return instant.astimezone(timezone.utc).isoformat()


def _relative_csv_path(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BlueHeartPreflightError(f"{field} is missing")
    normalized = value.strip().replace("\\", "/")
    parts = PurePosixPath(normalized).parts
    if (
        normalized.startswith("/")
        or not parts
        or any(part in ("..", ".") for part in normalized.split("/"))
        or ":" in parts[0]
        or not normalized.lower().endswith(".csv")
    ):
        raise BlueHeartPreflightError(f"{field} must be a relative CSV path without traversal")
    return normalized


def _coord(row: Mapping[str, str], field: str, low: float, high: float) -> None:
    try:
        numeric = float(row[field])
    except (ValueError, TypeError, KeyError) as exc:
        raise BlueHeartPreflightError(f"invalid {field} coordinate") from exc
    if not math.isfinite(numeric) or not low <= numeric <= high:
        raise BlueHeartPreflightError(f"out-of-range {field} coordinate")


def _param_units(row: Mapping[str, str]) -> None:
    params = [x.strip() for x in (row.get("gaugeParameters") or "").split(";")]
    units = [x.strip() for x in (row.get("parameterUnits") or "").split(";")]
    if not params or len(params) != len(units) or not all(params) or not all(units):
        raise BlueHeartPreflightError("gaugeParameters/parameterUnits must be one-to-one")

def _optional_numeric_fields(
    row: Mapping[str, str],
    gauge_type: str,
    populated: Counter[str],
) -> None:
    """Validate optional dimensions only where present; missing is never zero."""

    for field, allowed_type in OPTIONAL_NUMERIC_BY_GAUGE.items():
        original = row.get(field)
        if original is None:
            raise BlueHeartPreflightError(f"missing optional dimension column: {field}")
        value = original.strip()
        if not value:
            continue
        try:
            numeric = float(value)
        except ValueError as exc:
            raise BlueHeartPreflightError(f"non-numeric {field}") from exc
        if not math.isfinite(numeric):
            raise BlueHeartPreflightError(f"non-finite {field}")
        if gauge_type != allowed_type:
            raise BlueHeartPreflightError(f"{field} belongs to {allowed_type} gauges")
        populated[field] += 1


def inspect_index_csv(path: Path, *, expected_gauges: int | None = None) -> dict[str, object]:
    """Check one local, separately rights-cleared index; return no sensitive rows."""

    path = Path(path)
    counts: Counter[str] = Counter()
    optional_populated: Counter[str] = Counter()
    seen_data_paths: set[str] = set()
    seen_qc_paths: set[str] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as fileobj:
        reader = csv.DictReader(fileobj)
        if reader.fieldnames is None or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise BlueHeartPreflightError("missing or duplicated index headers")
        if not REQUIRED_COLUMNS.issubset(set(reader.fieldnames)):
            raise BlueHeartPreflightError("missing required README index columns")
        for index, row in enumerate(reader, start=1):
            if index > 10000:
                raise BlueHeartPreflightError("source index exceeds bounded 10000-row preflight")
            gauge_type = row.get("gaugeType")
            if gauge_type not in GAUGE_TYPES:
                raise BlueHeartPreflightError("unknown gaugeType")
            _coord(row, "locationLatitude", -90.0, 90.0)
            _coord(row, "locationLongitude", -180.0, 180.0)
            _param_units(row)
            _optional_numeric_fields(row, gauge_type, optional_populated)
            data_path = _relative_csv_path(row.get("dataPath"), field="dataPath")
            qc_path = _relative_csv_path(row.get("dataQualityFlagsPath"), field="dataQualityFlagsPath")
            if data_path == qc_path or data_path in seen_data_paths or qc_path in seen_qc_paths:
                raise BlueHeartPreflightError("ambiguous or repeated telemetry/QC path")
            seen_data_paths.add(data_path)
            seen_qc_paths.add(qc_path)
            counts[gauge_type] += 1

    total = sum(counts.values())
    if not total:
        raise BlueHeartPreflightError("empty index")
    if expected_gauges is not None and total != expected_gauges:
        raise BlueHeartPreflightError("index size differs from separately declared gauge count")
    return {
        "index_rows": total,
        "gauge_type_counts": {key: counts[key] for key in sorted(counts)},
        "optional_field_populated_counts": {
            field: optional_populated[field] for field in sorted(OPTIONAL_NUMERIC_BY_GAUGE)
        },
        "has_telemetry_and_qc_paths": total,
        "source_bytes_admitted": False,
        "timestamp_alignment_approved": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded Blue Heart index preflight (offline only)")
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--expected-gauges", type=int, default=None)
    args = parser.parse_args()
    if args.expected_gauges is not None and args.expected_gauges < 1:
        parser.error("--expected-gauges must be positive")
    try:
        summary = inspect_index_csv(args.index, expected_gauges=args.expected_gauges)
    except (BlueHeartPreflightError, OSError, UnicodeError, csv.Error) as exc:
        parser.error(str(exc))
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
