# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict offline C3S EWS annual NUTS storm-indicator CSV parser.

This is a regional *hazard validation* product, NOT an event catalogue,
location exposure, insurer loss series, storm-footprint or CAT simulation.
Actual NUTS vintage is unverified until checked against provider metadata.
"""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
import math
from pathlib import Path
import re

FIELDS = (
    "year", "region", "threshold", "storm_number", "mean_wind_gust",
    "ssi", "normalised_ssi", "area_ratio", "wind_gust_ratio", "algorithm",
)
THRESHOLDS = (Decimal("0"), Decimal("15.6"), Decimal("20"), Decimal("25"))
REGION_CODE = re.compile(r"[A-Z]{2}[A-Z0-9]{0,2}\Z")
SHA256 = re.compile(r"[a-f0-9]{64}\Z")


class AnnualSummaryError(ValueError):
    """CSV format/scientific contract is unsupported or ambiguous."""


def _decimal(raw: str, label: str, optional: bool = False) -> Decimal | None:
    value = raw.strip()
    if optional and value in ("", "NA", "NaN"):
        return None
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise AnnualSummaryError(f"{label}: nonnumeric value") from exc
    if not number.is_finite() or number < 0:
        raise AnnualSummaryError(f"{label}: nonfinite or negative")
    converted = float(number)
    if not math.isfinite(converted) or (number != 0 and converted == 0):
        raise AnnualSummaryError(f"{label}: outside supported finite float precision")
    return number


def _float_or_none(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def parse_annual_csv(blob: bytes) -> dict:
    """Validate the original CSV bytes; never collapse thresholds, algorithms or NUTS levels."""
    if not isinstance(blob, bytes) or not blob or len(blob) > 250_000_000:
        raise AnnualSummaryError("CSV must be nonempty and no larger than 250 MB")
    try:
        text = blob.decode("utf-8-sig")
    except UnicodeError as exc:
        raise AnnualSummaryError("invalid UTF-8 input") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""), dialect="excel", strict=True)
    if reader.fieldnames is None or set(reader.fieldnames) != set(FIELDS) or len(reader.fieldnames) != len(FIELDS):
        raise AnnualSummaryError("unexpected or duplicate CSV headers; 10 official C3S fields required")
    rows = []
    seen = set()
    storms_by_threshold: dict[tuple[str, str, str], dict[Decimal, int]] = {}
    for index, row in enumerate(reader, start=2):
        if None in row or any(v is None for v in row.values()):
            raise AnnualSummaryError(f"line {index}: invalid CSV field count")
        year_s = row["year"].strip()
        if not re.fullmatch(r"\d{4}", year_s) or not 1940 <= int(year_s) <= 2026:
            raise AnnualSummaryError(f"line {index}: year outside pinned historical 1940-2026 coverage")
        region = row["region"].strip()
        if not REGION_CODE.fullmatch(region):
            raise AnnualSummaryError(f"line {index}: invalid NUTS0/1/2 region code")
        threshold = _decimal(row["threshold"], "threshold")
        if threshold not in THRESHOLDS:
            raise AnnualSummaryError(f"line {index}: unsupported C3S gust threshold")
        algorithm = row["algorithm"].strip()
        if not algorithm:
            raise AnnualSummaryError(f"line {index}: blank tracking algorithm")
        storm_count_s = row["storm_number"].strip()
        if not re.fullmatch(r"\d+", storm_count_s):
            raise AnnualSummaryError(f"line {index}: storm_number must be nonnegative integer")
        storm_count = int(storm_count_s)
        if storm_count > 100000:
            raise AnnualSummaryError(f"line {index}: implausible storm_number")
        metrics = {field: _decimal(row[field], field, optional=True)
                   for field in ("mean_wind_gust", "ssi", "normalised_ssi", "area_ratio", "wind_gust_ratio")}
        if metrics["area_ratio"] is not None and metrics["area_ratio"] > 1:
            raise AnnualSummaryError(f"line {index}: area_ratio must be <= 1")
        key = (year_s, region, threshold, algorithm)
        if key in seen:
            raise AnnualSummaryError(f"line {index}: duplicate year/region/threshold/algorithm")
        seen.add(key)
        group = storms_by_threshold.setdefault((year_s, region, algorithm), {})
        group[threshold] = storm_count
        rows.append({
            "year": int(year_s), "region": region, "nuts_level": len(region)-2,
            "threshold_mps": str(threshold), "algorithm": algorithm,
            "storm_number": storm_count,
            **{key: _float_or_none(v) for key, v in metrics.items()},
            "missing_hazard_metric_fields": sorted(key for key,v in metrics.items() if v is None),
        })
    if not rows:
        raise AnnualSummaryError("CSV has no indicator rows")
    for (year, region, algorithm), groups in storms_by_threshold.items():
        sequence = sorted(groups.items())
        for (lower_t, lower), (upper_t, upper) in zip(sequence, sequence[1:]):
            if lower < upper:
                raise AnnualSummaryError(
                    f"nested threshold count contradiction in {year}/{region}/{algorithm}: "
                    f"count({lower_t})={lower} < count({upper_t})={upper}")
    rows.sort(key=lambda r: (r["year"],r["region"],r["algorithm"],Decimal(r["threshold_mps"])))
    return {
        "evidence_class": "C3S_ANNUAL_REGIONAL_HAZARD_ONLY_NO_EVENT_OR_INSURANCE_LOSS",
        "official_dataset": "sis-european-wind-storm-reanalysis",
        "official_doi": "10.24381/bf1f06a9",
        "source_csv_sha256": hashlib.sha256(blob).hexdigest(),
        "observed_row_count": len(rows),
        "observed_years": sorted({r["year"] for r in rows}),
        "observed_nuts_levels": sorted({r["nuts_level"] for r in rows}),
        "observed_tracking_algorithm_labels": sorted({r["algorithm"] for r in rows}),
        "nuts_vintage": "unverified_from_csv",
        "automatic_nuts_join_permitted": False,
        "records_are_individual_cat_events": False,
        "rows": rows,
        "insured_losses_calculated": False,
        "threshold_counts_must_not_be_summed": True,
        "different_tracking_algorithms_must_not_be_summed": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path, help="Exact, locally downloaded C3S CSV")
    parser.add_argument("--expected-source-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    blob = args.csv_file.read_bytes()
    if not SHA256.fullmatch(args.expected_source_sha256) or hashlib.sha256(blob).hexdigest() != args.expected_source_sha256:
        raise AnnualSummaryError("CSV raw bytes differ from approved SHA256")
    output = parse_annual_csv(blob)
    if args.csv_file.resolve() == args.out.resolve():
        raise AnnualSummaryError("refusing to overwrite original C3S CSV")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, sort_keys=True, indent=2, allow_nan=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
