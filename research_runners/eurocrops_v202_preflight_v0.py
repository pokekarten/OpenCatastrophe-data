#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, bounded EuroCropsV2.02 original GeoParquet preflight.

No network, no source rows in output, no model admission.
Requires optional pyarrow and shapely for original Parquet inspection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

JRC_BASE = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DRLL/EuroCropsV2/gpqtv202/"
NUTS = frozenset("at be2 be3 bg cz de4 dea dk ee es fi fr ie iti1 nl pt si sk".split())
NAME = re.compile(r"([a-z][a-z0-9]*)_(20\d\d)\.parquet\Z")
REQUIRED = ("cropfield", "original_code", "area_ha", "geom")
MAX_FILE_BYTES = 2_500_000_000

class Blocked(ValueError):
    """Fail closed if source or schema evidence is absent."""


def asset_identity(path: Path) -> tuple[str, int, str]:
    match = NAME.fullmatch(path.name)
    if match is None or match[1] not in NUTS or not (2008 <= int(match[2]) <= 2023):
        raise Blocked("expected a listed gpqtv202 NUTS/year parquet, not stack/arbitrary file")
    if path.is_symlink() or not path.is_file():
        raise Blocked("original input absent or symlink")
    size = path.stat().st_size
    if size <= 8 or size > MAX_FILE_BYTES:
        raise Blocked("original input empty or over explicit size cap")
    with path.open("rb") as f:
        if f.read(4) != b"PAR1":
            raise Blocked("Parquet header missing")
        f.seek(-4, 2)
        if f.read(4) != b"PAR1":
            raise Blocked("Parquet footer missing")
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return match[1], int(match[2]), digest.hexdigest()


def geo_metadata(metadata: dict | None, names: list[str]) -> dict:
    if any(col not in names for col in REQUIRED):
        raise Blocked("required original fields missing")
    if not metadata or b"geo" not in metadata:
        raise Blocked("GeoParquet metadata missing, cannot assume EPSG")
    try:
        geo = json.loads(metadata[b"geo"].decode("utf-8"))
        primary = geo["primary_column"]
        if primary != "geom":
            raise Blocked("wrong geometry column")
        crs = geo["columns"][primary]["crs"]
        if isinstance(crs, str):
            is_3035 = crs.upper() == "EPSG:3035"
        elif isinstance(crs, dict):
            identity = crs.get("id", {})
            is_3035 = (str(identity.get("authority", "")).upper() == "EPSG"
                       and str(identity.get("code", "")) == "3035")
        else:
            is_3035 = False
    except (KeyError, TypeError, AttributeError, ValueError, UnicodeError) as exc:
        raise Blocked("invalid GeoParquet metadata") from exc
    if not is_3035:
        raise Blocked("not independently evidenced as EPSG:3035")
    return {"primary_geometry_column": "geom", "crs": "EPSG:3035"}


def audit_rows(rows: list[dict]) -> dict:
    try:
        from shapely import wkb
        from shapely.errors import GEOSException
    except ImportError as exc:
        raise Blocked("shapely required") from exc
    stats = {"sampled": 0, "missing_crop_code": 0, "duplicate_cropfield_in_sample": 0,
             "invalid_area_ha": 0, "invalid_or_empty_geometry": 0,
             "non_polygon_geometry": 0, "area_disagreement_over_5pct": 0}
    seen: set[str] = set()
    for row in rows:
        stats["sampled"] += 1
        field = row.get("cropfield")
        if field is None or str(field) in seen:
            stats["duplicate_cropfield_in_sample"] += 1
        else:
            seen.add(str(field))
        code = row.get("original_code")
        if code is None or not str(code).strip():
            stats["missing_crop_code"] += 1
        area = row.get("area_ha")
        valid_area = (not isinstance(area, bool) and isinstance(area, (int, float))
                      and math.isfinite(area) and area > 0)
        if not valid_area:
            stats["invalid_area_ha"] += 1
        try:
            binary = row.get("geom")
            geom = wkb.loads(bytes(binary)) if isinstance(binary, (bytes, bytearray, memoryview)) else None
            if geom is None or geom.is_empty or not geom.is_valid:
                stats["invalid_or_empty_geometry"] += 1
                continue
            if geom.geom_type not in ("Polygon", "MultiPolygon"):
                stats["non_polygon_geometry"] += 1
                continue
            if valid_area and abs(geom.area / 10000 - float(area)) / float(area) > 0.05:
                stats["area_disagreement_over_5pct"] += 1
        except (ValueError, TypeError, OverflowError, GEOSException):
            stats["invalid_or_empty_geometry"] += 1
    return stats


def inspect_local(path: Path, expected_sha256: str, max_rows: int = 512) -> dict:
    if max_rows < 1 or max_rows > 5000:
        raise Blocked("sample size must be 1..5000")
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise Blocked("explicit expected original SHA256 required")
    region, year, actual = asset_identity(path)
    if actual != expected_sha256:
        raise Blocked("original source SHA256 mismatch")
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise Blocked("install optional pyarrow to inspect original file") from exc
    parquet = pq.ParquetFile(path)
    geo = geo_metadata(parquet.schema_arrow.metadata, parquet.schema_arrow.names)
    rows: list[dict] = []
    for batch in parquet.iter_batches(batch_size=min(512, max_rows), columns=list(REQUIRED)):
        take = min(max_rows - len(rows), batch.num_rows)
        rows.extend(batch.slice(0, take).to_pylist())
        if len(rows) == max_rows:
            break
    if not rows:
        raise Blocked("source contains no readable rows")
    stats = audit_rows(rows)
    return {
        "profile": "eurocrops-v202-local-source-qc-v0",
        "source_candidate_id": "eu.jrc.eurocropsv2.gsa-parcels",
        "source_url": JRC_BASE + path.name,
        "source_filename": path.name,
        "source_region": region, "source_year": year,
        "source_sha256": actual, "sha256_matched_operator_pin": True,
        "file_bytes": path.stat().st_size,
        "parquet_total_rows_from_footer": parquet.metadata.num_rows,
        "parquet_row_groups": parquet.metadata.num_row_groups,
        "schema_fields": list(parquet.schema_arrow.names),
        "geo": geo, "pyarrow_version": pa.__version__,
        "sample": stats,
        "sample_is_full_dataset": stats["sampled"] == parquet.metadata.num_rows,
        "research_qc_only": True,
        "rights_and_scientific_admission": "NOT_REVIEWED_NOT_ADMITTED",
        "loss_or_insurer_exposure_model_ready": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--sample-rows", type=int, default=512)
    args = parser.parse_args(argv)
    try:
        result = inspect_local(args.input, args.expected_sha256, args.sample_rows)
    except (Blocked, OSError, RuntimeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
