# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed offline WSM 2025 40-field CSV science screen; no source acquisition.

Authoritative field order and units: https://doi.org/10.48440/wsm.2025.001
Dataset DOI: https://doi.org/10.5880/WSM.2025.001
A passed screen is NOT permission to download or CAT-model admission.
"""

from __future__ import annotations

import csv
import hashlib
import io
import math
import re

MAX_ORIGINAL_BYTES = 65_536
MAX_ROWS = 100
# Exact field order from Table 2-1, WSM Technical Report 25-01.
FIELDS = tuple("""ID ISC_ID SITE LAT LON AZI TYPE DEPTH QUALITY REGIME LOCALITY
COUNTRY DATE TIME NUMBER SD TOT_LEN VENT TOP BOT ANISOTROPY METHOD
S1AZ S1PL S2AZ S2PL S3AZ S3PL MAG_TYPE EQ_MAG CRUST
REF1 REF2 REF3 REF4 REF5 REF6 COMMENT PLATE DIST""".split())
QUALITIES = frozenset({"A", "B", "C", "D", "E", "Xmi", "Xne", "Xru"})
REGIMES = frozenset({"NF", "NS", "SS", "TS", "TF", "U"})


class Wsm2025FormatError(ValueError):
    """Input cannot be trusted as a bounded original WSM 2025 CSV slice."""


def _bounded_number(raw: str, lower: float, upper: float, label: str) -> float:
    try:
        value = float(raw)
    except ValueError as exc:
        raise Wsm2025FormatError(f"invalid {label}") from exc
    if not math.isfinite(value) or not lower <= value <= upper:
        raise Wsm2025FormatError(f"{label} outside valid range")
    return value


def screen_wsm2025_csv_bytes(original: bytes) -> dict[str, object]:
    """Screen supplied bytes without storing/reformatting records or changing source rights.

    A bounded slice must include the real 40-field header. A real original-asset
    receipt still requires an independently authorized external acquisition.
    """
    if not isinstance(original, bytes) or not original or len(original) > MAX_ORIGINAL_BYTES:
        raise Wsm2025FormatError("empty, non-byte or oversized original input")
    try:
        decoded = original.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise Wsm2025FormatError("not UTF-8 original CSV") from exc
    if "\x00" in decoded or "\r" in decoded and "\r\n" not in decoded:
        raise Wsm2025FormatError("binary or unexpected newline framing")
    reader = csv.DictReader(io.StringIO(decoded, newline=""), strict=True)
    if reader.fieldnames != list(FIELDS):
        raise Wsm2025FormatError("WSM 2025 full 40-field header mismatch")
    seen: set[str] = set()
    count = good_orientation = missing_orientation = 0
    quality_counts = {q: 0 for q in sorted(QUALITIES)}
    try:
        for row in reader:
            count += 1
            if count > MAX_ROWS:
                raise Wsm2025FormatError("row cap exceeded")
            if None in row or any(value is None for value in row.values()):
                raise Wsm2025FormatError("incomplete or excess CSV columns")
            source_id = row["ID"].strip()
            if not re.fullmatch(r"wsm[0-9]+", source_id, flags=re.IGNORECASE):
                raise Wsm2025FormatError("invalid WSM record identifier")
            if source_id in seen:
                raise Wsm2025FormatError("duplicate WSM record identifier")
            seen.add(source_id)
            _bounded_number(row["LAT"], -90, 90, "LAT degrees")
            _bounded_number(row["LON"], -180, 180, "LON degrees")
            angle = _bounded_number(row["AZI"], 0, 999, "AZI degrees")
            quality = row["QUALITY"].strip()
            if quality not in QUALITIES or row["REGIME"].strip() not in REGIMES:
                raise Wsm2025FormatError("unknown quality or stress-regime code")
            if angle == 999:
                if quality not in {"E", "Xmi"}:
                    raise Wsm2025FormatError("no-orientation sentinel with incompatible quality")
                missing_orientation += 1
            elif angle > 180:
                raise Wsm2025FormatError("AZI exceeds horizontal axial domain")
            else:
                good_orientation += 1
            quality_counts[quality] += 1
    except csv.Error as exc:
        raise Wsm2025FormatError("malformed quoted CSV") from exc
    if not count:
        raise Wsm2025FormatError("empty data slice")
    return {
        "source_id": "gfz.world-stress-map.2025",
        "product": "World Stress Map Database Release 2025",
        "original_sha256": hashlib.sha256(original).hexdigest(),
        "original_bytes": len(original),
        "rows_screened": count,
        "valid_orientation_rows": good_orientation,
        "missing_orientation_rows": missing_orientation,
        "quality_counts": quality_counts,
        "dataset_scope": "bounded_csv_screen_only",
        "licence_and_automation_authorization": "not_established_by_this_screen",
        "cat_model_admission": "not_admitted",
        "neon_storage": "storage_not_verified",
    }
