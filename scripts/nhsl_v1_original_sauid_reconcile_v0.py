# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Reconcile NHSL v1.0 Nunavut archetypes to settled areas using *original* GPKGs.

Requires exact, pinned source release ZIP bytes stored outside Git.
Never turns replacement cost into insured TIV or invents building coordinates.
Outputs counts, totals and numerical residuals ONLY, not source feature rows.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import sqlite3
import sys
import tempfile
import zipfile
from collections.abc import Iterable, Mapping
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Any

if __package__:
    from .nhsl_v1_original_binary_preflight_v0 import (
        PINNED, NHSLBinaryError, _bytes, check_archive,
    )
else:
    from nhsl_v1_original_binary_preflight_v0 import (
        PINNED, NHSLBinaryError, _bytes, check_archive,
    )

SOURCE_ID = "can.nrcan.nhsl.physical-exposure.2016-2020"
FIELDS = {
    "building_count": ("Et_BldgNum", "E_BldgNum"),
    "floor_area_sqft": ("Et_BldgArea", "E_BldgArea"),
    "structural_cad_2019": ("Et_StrValue", "E_StrValue"),
    "nonstructural_cad_2019": ("Et_NStrValue", "E_NStrValue"),
    "building_cost_cad_2019": ("Et_BldgValue", "E_BldgValue"),
    "contents_cad_2019": ("Et_ContValue", "E_ContValue"),
    "assets_cad_2019": ("Et_AssetValue", "E_AssetValue"),
}
TOLERANCES = {
    "building_count": Decimal("0.000001"),
    "floor_area_sqft": Decimal("0.000001"),
    "structural_cad_2019": Decimal("0.02"),
    "nonstructural_cad_2019": Decimal("0.02"),
    "building_cost_cad_2019": Decimal("0.02"),
    "contents_cad_2019": Decimal("0.02"),
    "assets_cad_2019": Decimal("0.02"),
}
# 0.02 CAD per SAUID is a *comparison tolerance*, not new data precision.
MAX_RECORDS = 100_000


class NHSLReconcileError(ValueError):
    """Untrustworthy/malformed original input or scientific conservation failure."""


def _numeric(value: Any, label: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (float, int, Decimal)):
        raise NHSLReconcileError(f"{label}: SQLite number required (not missing or text)")
    if isinstance(value, float) and not math.isfinite(value):
        raise NHSLReconcileError(f"{label}: nonfinite")
    try:
        x = Decimal(str(value))
    except InvalidOperation as exc:
        raise NHSLReconcileError(f"{label}: invalid Decimal") from exc
    if not x.is_finite() or x < 0 or x > Decimal("1000000000000000"):
        raise NHSLReconcileError(f"{label}: nonfinite/negative/unbounded")
    return x


def _source_id(value: Any) -> str:
    if not isinstance(value, str) or not value or len(value) > 70:
        raise NHSLReconcileError("missing/unbounded source SAUID")
    return value


def compare_aggregate_rows(
    polygons: Iterable[Mapping[str, Any]],
    archetypes: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Pure in-memory function; accepts invented rows for offline regression tests."""
    with localcontext() as ctx:
        ctx.prec = 50
        grouped: dict[str, dict[str, Any]] = {}
        archetype_rows = 0
        for row in archetypes:
            archetype_rows += 1
            if archetype_rows > MAX_RECORDS:
                raise NHSLReconcileError("unbounded archetype row count")
            id_ = _source_id(row["Sauid"])
            bucket = grouped.setdefault(id_, {"rows": 0, **{k: Decimal(0) for k in FIELDS}})
            bucket["rows"] += 1
            for metric, (_, a_field) in FIELDS.items():
                bucket[metric] += _numeric(row[a_field], a_field)

        seen: set[str] = set()
        missing_archetypes = 0
        areas = 0
        polygon_total = {k: Decimal(0) for k in FIELDS}
        archetype_total = {k: Decimal(0) for k in FIELDS}
        per_field = {
            k: {
                "max_abs_diff": Decimal(0),
                "mismatch_count": 0,
                "delta_sum": Decimal(0),
            }
            for k in FIELDS
        }
        for row in polygons:
            areas += 1
            if areas > MAX_RECORDS:
                raise NHSLReconcileError("unbounded polygon row count")
            id_ = _source_id(row["Sauid"])
            if id_ in seen:
                raise NHSLReconcileError("duplicate polygon SAUID")
            seen.add(id_)
            bucket = grouped.get(id_)
            if bucket is None:
                missing_archetypes += 1
            for metric, (p_field, _) in FIELDS.items():
                polygon_value = _numeric(row[p_field], p_field)
                polygon_total[metric] += polygon_value
                if bucket is not None:
                    gap = bucket[metric] - polygon_value
                    per_field[metric]["max_abs_diff"] = max(
                        per_field[metric]["max_abs_diff"], abs(gap)
                    )
                    per_field[metric]["delta_sum"] += gap
                    if abs(gap) > TOLERANCES[metric]:
                        per_field[metric]["mismatch_count"] += 1

        for bucket in grouped.values():
            for metric in FIELDS:
                archetype_total[metric] += bucket[metric]

        orphan_archetypes = len(grouped.keys() - seen)
        if not areas or not archetype_rows:
            raise NHSLReconcileError("empty polygon or archetype GPKG")

        mismatches = sum(v["mismatch_count"] for v in per_field.values())
        passed = not (missing_archetypes or orphan_archetypes or mismatches)
        return {
            "region": "Nunavut",
            "source_candidate_id": SOURCE_ID,
            "source_role": "original_release_v1.0_polygon_archetype_sauid_conservation",
            "settled_areas": areas,
            "archetype_records": archetype_rows,
            "unique_archetype_sauids": len(grouped),
            "matched_sauids": areas - missing_archetypes,
            "unmatched_polygon_sauids": missing_archetypes,
            "unmatched_archetype_sauids": orphan_archetypes,
            "metrics": {
                metric: {
                    "polygon_total": str(polygon_total[metric]),
                    "archetype_total": str(archetype_total[metric]),
                    "max_abs_delta_per_sauid": str(info["max_abs_diff"]),
                    "delta_sum": str(info["delta_sum"]),
                    "sauids_exceeding_tolerance": info["mismatch_count"],
                    "tolerance": str(TOLERANCES[metric]),
                }
                for metric, info in per_field.items()
            },
            "numeric_conservation_passed": passed,
            "raw_location_ids_or_geometry_emitted": False,
            "archetype_is_individual_rooftop": False,
            "observed_insured_values": False,
            "oed_insured_locations_exportable": False,
            "source_rights_for_model_use_reviewed": False,
            "scientific_fitness_reviewed": False,
            "model_input_approved": False,
            "admission_status": "not_admitted",
        }


def _read_rows(extracted_gpkg: Path, role: str) -> list[dict[str, Any]]:
    table = PINNED[role]["member"].removesuffix(".gpkg")
    quoted = '"' + table.replace('"', '""') + '"'
    cols = ["Sauid"] + [
        pair[0] if role == "polygon" else pair[1] for pair in FIELDS.values()
    ]
    projection = ", ".join('"' + col + '"' for col in cols)
    query = f"SELECT {projection} FROM {quoted}"
    con = sqlite3.connect(extracted_gpkg.as_uri() + "?mode=ro&immutable=1", uri=True)
    try:
        con.execute("PRAGMA query_only=ON")
        con.execute("PRAGMA trusted_schema=OFF")
        rows = con.execute(query).fetchall()
    except sqlite3.DatabaseError as exc:
        raise NHSLReconcileError(f"{role}: original GPKG SQL query failed") from exc
    finally:
        con.close()
    if len(rows) > MAX_RECORDS:
        raise NHSLReconcileError(f"{role}: too many rows")
    return [dict(zip(cols, values)) for values in rows]


def audit_original_archives(polygon_zip: Path, archetype_zip: Path) -> dict[str, Any]:
    """Verify provider SHA/CRC and SQLite integrity before original data comparison."""
    raw = {}
    for role, path in (("polygon", polygon_zip), ("archetype", archetype_zip)):
        raw[role] = _bytes(path, PINNED[role])
        check_archive(raw[role], role, PINNED[role])
    with tempfile.TemporaryDirectory(prefix="nhsl-sauid-reconcile-") as tmp:
        original_rows = {}
        for role in ("polygon", "archetype"):
            with zipfile.ZipFile(io.BytesIO(raw[role])) as zf:
                data = zf.read(PINNED[role]["member"])
            target = Path(tmp) / (role + ".gpkg")
            target.write_bytes(data)
            original_rows[role] = _read_rows(target, role)
        receipt = compare_aggregate_rows(original_rows["polygon"], original_rows["archetype"])
        receipt["original_source_file_hashes_verified"] = {
            role: PINNED[role]["sha256"] for role in ("polygon", "archetype")
        }
        receipt["original_sqlite_integrity_checked"] = True
        return receipt


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polygon-zip", type=Path, required=True)
    p.add_argument("--archetype-zip", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        result = audit_original_archives(args.polygon_zip, args.archetype_zip)
    except (NHSLReconcileError, NHSLBinaryError, KeyError, OSError, zipfile.BadZipFile) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["numeric_conservation_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
