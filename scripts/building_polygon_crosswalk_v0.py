#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded, offline-only building footprint overlap diagnostics in EPSG:3035.

Operator-supplied local CSVs only. Output contains aggregate statistics and
source hashes, never building links, coordinates, values, or admitted inputs.
Requires optional Shapely 2.1.2 from requirements-eu-flood-spatial.txt.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import sys

import shapely
from shapely import STRtree
from shapely.errors import GEOSException, ShapelyError
from shapely.geometry.base import BaseGeometry

CRS = "EPSG:3035"
COLUMNS = ("building_id", "geometry_wkt", "upstream_family")
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_ROWS = 2000
MAX_PAIRS = 20000
DEFAULT_IOU_THRESHOLD = 0.6  # Diagnostic heuristic; not calibrated.


class FootprintAuditError(ValueError):
    """Invalid local input or scientifically unsafe candidate set."""


@dataclass(frozen=True)
class Record:
    identity: str
    geometry: BaseGeometry
    family: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _date_identity(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise FootprintAuditError("source vintage must be exact YYYY-MM-DD")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise FootprintAuditError("source vintage is not a calendar date") from exc
    return value


def _load(path: Path) -> list[Record]:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            raise FootprintAuditError("source sample exceeds 5 MiB input budget")
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != list(COLUMNS):
                raise FootprintAuditError("CSV header must be building_id,geometry_wkt,upstream_family")
            records: list[Record] = []
            ids: set[str] = set()
            for row_idx, row in enumerate(reader, 2):
                if len(records) >= MAX_ROWS:
                    raise FootprintAuditError("more than 2000 buildings per source")
                if None in row or any(not isinstance(row.get(c), str) for c in COLUMNS):
                    raise FootprintAuditError(f"malformed source CSV row {row_idx}")
                identity, wkt, family = (row[c].strip() for c in COLUMNS)
                if not identity or len(identity) > 256 or identity in ids:
                    raise FootprintAuditError(f"missing/duplicate building ID at row {row_idx}")
                if not family or len(family) > 128:
                    raise FootprintAuditError(f"missing/invalid source lineage at row {row_idx}")
                if not wkt or len(wkt) > 100000:
                    raise FootprintAuditError(f"missing/oversized WKT at row {row_idx}")
                try:
                    geom = shapely.from_wkt(wkt)
                except (GEOSException, ValueError, TypeError) as exc:
                    raise FootprintAuditError(f"malformed WKT at row {row_idx}") from exc
                if (geom is None or geom.geom_type not in ("Polygon", "MultiPolygon")
                        or geom.is_empty or not geom.is_valid or geom.area <= 0
                        or not math.isfinite(float(geom.area))
                        or not all(math.isfinite(float(v)) for pt in shapely.get_coordinates(geom)
                                   for v in pt)):
                    raise FootprintAuditError(f"invalid building polygon at row {row_idx}")
                ids.add(identity)
                records.append(Record(identity, geom, family))
        if not records:
            raise FootprintAuditError("empty building sample")
        return records
    except (OSError, UnicodeError, csv.Error) as exc:
        raise FootprintAuditError("cannot read bounded local UTF-8 CSV") from exc


def audit(left_path: Path, right_path: Path, *, left_source_id: str,
          right_source_id: str, left_vintage: str, right_vintage: str,
          left_crs: str, right_crs: str,
          iou_threshold: float = DEFAULT_IOU_THRESHOLD) -> dict:
    """Compute aggregate high-overlap hypotheses; never building equivalence."""
    if left_crs != CRS or right_crs != CRS:
        raise FootprintAuditError("both source samples must be declared in EPSG:3035")
    for sid in (left_source_id, right_source_id):
        if not isinstance(sid, str) or not sid or len(sid) > 256:
            raise FootprintAuditError("both public source identities are mandatory")
    if left_source_id == right_source_id:
        raise FootprintAuditError("expected two distinct source identities")
    _date_identity(left_vintage)
    _date_identity(right_vintage)
    if (isinstance(iou_threshold, bool) or not isinstance(iou_threshold, (int, float))
            or not math.isfinite(iou_threshold) or not 0 < iou_threshold <= 1):
        raise FootprintAuditError("IoU must be in (0,1]")

    left, right = _load(left_path), _load(right_path)
    tree = STRtree([record.geometry for record in right])
    left_links: list[set[int]] = [set() for _ in left]
    right_links: list[set[int]] = [set() for _ in right]
    iou_for_pair: dict[tuple[int, int], float] = {}
    positive_intersections = 0
    candidates_checked = 0
    try:
        for li, record in enumerate(left):
            for right_index in tree.query(record.geometry):
                candidates_checked += 1
                if candidates_checked > MAX_PAIRS:
                    raise FootprintAuditError("too many intersecting-box candidates for bounded pilot")
                ri = int(right_index)
                other = right[ri]
                intersection = float(record.geometry.intersection(other.geometry).area)
                if intersection <= 0:
                    continue
                positive_intersections += 1
                union = float(record.geometry.area + other.geometry.area - intersection)
                iou = intersection / union
                if not math.isfinite(iou) or not 0 <= iou <= 1 + 1e-10:
                    raise FootprintAuditError("non-finite or invalid geometry overlap")
                if iou >= iou_threshold:
                    left_links[li].add(ri)
                    right_links[ri].add(li)
                    iou_for_pair[(li, ri)] = min(1.0, iou)
    except (GEOSException, ShapelyError) as exc:
        raise FootprintAuditError("GEOS cannot calculate a valid polygon intersection") from exc

    unique_pairs = [(li, next(iter(links))) for li, links in enumerate(left_links)
                    if len(links) == 1 and len(right_links[next(iter(links))]) == 1]
    same_family = sum(left[li].family == right[ri].family for li, ri in unique_pairs)
    unknown_lineage = sum(left[li].family.lower() == "unknown"
                          or right[ri].family.lower() == "unknown" for li, ri in unique_pairs)
    return {
        "schema_version": "building-polygon-crosswalk-diagnostic-v0",
        "crs_declared_by_caller_not_verified": CRS,
        "left_source_id": left_source_id,
        "right_source_id": right_source_id,
        "left_vintage": left_vintage,
        "right_vintage": right_vintage,
        "source_vintages_equal": left_vintage == right_vintage,
        "left_sha256": _sha256(left_path),
        "right_sha256": _sha256(right_path),
        "iou_threshold_diagnostic_not_calibrated": iou_threshold,
        "counts": {
            "left_buildings": len(left),
            "right_buildings": len(right),
            "bbox_candidates_checked": candidates_checked,
            "positive_area_overlaps": positive_intersections,
            "high_iou_hypothesis_edges": len(iou_for_pair),
            "unique_high_iou_hypotheses_not_confirmed_matches": len(unique_pairs),
            "left_with_no_high_iou": sum(not x for x in left_links),
            "right_with_no_high_iou": sum(not x for x in right_links),
            "left_with_multiple_high_iou": sum(len(x) > 1 for x in left_links),
            "right_with_multiple_high_iou": sum(len(x) > 1 for x in right_links),
            "hypotheses_from_same_upstream_family": same_family,
            "hypotheses_with_unknown_lineage": unknown_lineage,
        },
        "unique_candidate_median_iou": (
            round(statistics.median(iou_for_pair[pair] for pair in unique_pairs), 6)
            if unique_pairs else None
        ),
        "source_rights_reviewed": False,
        "upstream_independence_established": False,
        "model_input_admitted": False,
        "source_bytes_persisted_by_tool": False,
        "individual_matches_exported": False,
        "warning": (
            "Diagnostic only: high overlap does not prove common building identity; "
            "EPSG:3035 and source vintages are caller claims, not coordinate verification; "
            "derived upstream geometries are not independent validation; "
            "split/merge, missing footprints and permit/renovation timing require human review. "
            "Do not fill attributes, calculate losses or admit source data from this report."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("left", "right"):
        parser.add_argument("--" + flag, required=True, type=Path)
        parser.add_argument("--" + flag + "-source-id", required=True)
        parser.add_argument("--" + flag + "-vintage", required=True)
        parser.add_argument("--" + flag + "-crs", required=True)
    parser.add_argument("--iou-threshold", type=float, default=DEFAULT_IOU_THRESHOLD)
    parser.add_argument("--out", type=Path, help="Optional aggregate-only JSON report")
    args = parser.parse_args(argv)
    try:
        result = audit(
            args.left, args.right,
            left_source_id=args.left_source_id, right_source_id=args.right_source_id,
            left_vintage=args.left_vintage, right_vintage=args.right_vintage,
            left_crs=args.left_crs, right_crs=args.right_crs,
            iou_threshold=args.iou_threshold,
        )
    except FootprintAuditError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    content = json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if args.out:
        try:
            args.out.write_text(content, encoding="utf-8")
        except OSError as exc:
            print(f"BLOCKED: cannot write aggregate report: {exc}", file=sys.stderr)
            return 2
    else:
        sys.stdout.write(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
