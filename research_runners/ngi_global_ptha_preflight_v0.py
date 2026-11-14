# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, bounded, no-raw-output preflight of NGI/GA globalPTHA.txt (Zenodo 16964551).

The output is a quality report, NOT a model admission, event set or loss file.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

PUBLISHER_MD5 = "d8dd8ad55fe89bd56b455e392387a99e"
MAX_BYTES = 12_000_000
MAX_ROWS = 200_000
RATE_THRESHOLDS_CM = (5, 10, 25, 50, 100, 300, 500, 1000, 2000)
RETURN_PERIODS_Y = (10, 50, 100, 200, 500, 1000, 2500)
RATES = tuple(f"rate_{n}" for n in RATE_THRESHOLDS_CM)
HEIGHTS = tuple(f"ari{n}" for n in RETURN_PERIODS_Y)
OTHER = ("ari500P", "ari500M", "ari500LL")
REQUIRED = ("FID", *RATES, *HEIGHTS, *OTHER, "POINT_X", "POINT_Y")


class InvalidOriginal(ValueError):
    """Missing/altered data, unsafe size, or invalid numerical structure."""


def audit(path: Path, *, expected_md5: str = PUBLISHER_MD5) -> dict:
    size = path.stat().st_size
    if not 0 < size <= MAX_BYTES:
        raise InvalidOriginal("file_size_out_of_bounds")
    raw = path.read_bytes()
    if hashlib.md5(raw).hexdigest() != expected_md5:
        raise InvalidOriginal("publisher_md5_mismatch")
    sha256 = hashlib.sha256(raw).hexdigest()
    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InvalidOriginal("text_encoding_invalid") from exc
    reader = csv.DictReader(io.StringIO(content), delimiter=";", strict=True)
    if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise InvalidOriginal("header_missing_or_duplicate")
    header = set(reader.fieldnames)
    if not set(REQUIRED).issubset(header):
        raise InvalidOriginal("required_columns_missing")
    aliases = ("ari500LZ", "ari500ZL")
    if sum(col in header for col in aliases) != 1:
        raise InvalidOriginal("ambiguous_ari500_zero_sigma_column")
    if header != (set(REQUIRED) | (set(aliases) & header)):
        raise InvalidOriginal("unexpected_columns")
    counts = {name: 0 for name in (
        "nonmonotonic_exceedance_rates", "nonmonotonic_return_heights",
        "uncertainty_interval_inverted", "point_outside_95pct_bounds",
        "left_censored_0p1m", "right_censored_20m",
        "longitudes_using_0_to_360", "rows",
    )}
    seen = set()
    for row in reader:
        if counts["rows"] >= MAX_ROWS:
            raise InvalidOriginal("too_many_rows")
        if None in row or any(v is None or not v.strip() for v in row.values()):
            raise InvalidOriginal("row_fields_missing")
        try:
            fid = int(row["FID"])
            fields = {k: float(row[k]) for k in (*RATES, *HEIGHTS, *OTHER, *(set(aliases) & header), "POINT_X", "POINT_Y")}
        except (ValueError, TypeError, OverflowError) as exc:
            raise InvalidOriginal("non_numeric_original_field") from exc
        if fid in seen:
            raise InvalidOriginal("duplicate_fid")
        seen.add(fid)
        if any(not math.isfinite(v) for v in fields.values()):
            raise InvalidOriginal("non_finite_original_field")
        x, y = fields["POINT_X"], fields["POINT_Y"]
        if not (-180 <= x <= 360 and -90 <= y <= 90):
            raise InvalidOriginal("coordinate_out_of_bounds")
        if x > 180:
            counts["longitudes_using_0_to_360"] += 1
        rates = [fields[k] for k in RATES]
        heights = [fields[k] for k in HEIGHTS]
        extra_heights = [fields[k] for k in (*OTHER, *(set(aliases) & header))]
        if any(v < 0 for v in rates) or any(not 0.1 <= v <= 20 for v in (*heights, *extra_heights)):
            raise InvalidOriginal("rate_or_height_out_of_domain")
        if any(b > a + 1e-12 for a, b in zip(rates, rates[1:])):
            counts["nonmonotonic_exceedance_rates"] += 1
        if any(b + 1e-12 < a for a, b in zip(heights, heights[1:])):
            counts["nonmonotonic_return_heights"] += 1
        lower, median, upper = fields["ari500M"], fields["ari500"], fields["ari500P"]
        if lower > upper:
            counts["uncertainty_interval_inverted"] += 1
        if median < lower or median > upper:
            counts["point_outside_95pct_bounds"] += 1
        counts["left_censored_0p1m"] += sum(v == 0.1 for v in heights)
        counts["right_censored_20m"] += sum(v == 20.0 for v in heights)
        counts["rows"] += 1
    if not counts["rows"]:
        raise InvalidOriginal("no_rows")
    return {
        "status": "quality_anomalies" if any(counts[k] for k in (
            "nonmonotonic_exceedance_rates", "nonmonotonic_return_heights",
            "uncertainty_interval_inverted", "point_outside_95pct_bounds")) else "parsed_with_no_flagged_anomalies",
        "source": "zenodo:16964551/globalPTHA.txt",
        "size_bytes": size, "md5": expected_md5, "sha256": sha256,
        "zero_sigma_column": next(c for c in aliases if c in header),
        "semantics": "annual_mean_exceedance_rates_not_event_frequency_or_event_set",
        "admission": "none", "checks": counts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="External original file; never commit source bytes")
    args = parser.parse_args()
    try:
        result = audit(args.file)
    except (InvalidOriginal, OSError, csv.Error) as exc:
        print(json.dumps({"status": "invalid_original", "error": str(exc), "admission": "none"}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 1 if result["status"] == "quality_anomalies" else 0


if __name__ == "__main__":
    raise SystemExit(main())
