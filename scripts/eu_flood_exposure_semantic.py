# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Deterministic synthetic flood/exposure accounting kernel for Issue #270 Phase A0."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Iterable, Mapping, Sequence

DEPTH_CLASSES = (
    ("depth_gt_0_le_1m", Decimal("0"), Decimal("1")),
    ("depth_gt_1_le_3m", Decimal("1"), Decimal("3")),
    ("depth_gt_3_le_10m", Decimal("3"), Decimal("10")),
    ("depth_gt_10m", Decimal("10"), None),
)
ALLOCATION_METHOD = "area_weighted_uniform_within_census_cell_v1"
CONFIG_ID = "eu_flood_exposure_a0_v1"
TOLERANCE = Decimal("0.000000001")


@dataclass(frozen=True)
class HazardSupport:
    support_id: str
    fraction: Decimal | str | int | float
    depth_m: Decimal | str | int | float | None = None
    nodata: bool = False
    permanent_water: bool = False
    spurious_depth: bool = False


@dataclass(frozen=True)
class CensusCell:
    cell_id: str
    population: Decimal | str | int | float
    aoi_fraction: Decimal | str | int | float
    supports: Sequence[HazardSupport]


class SemanticError(ValueError):
    """Raised when synthetic input cannot be accounted for unambiguously."""


def _decimal(value: Decimal | str | int | float, *, field: str) -> Decimal:
    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise SemanticError(f"{field} must be a finite decimal") from exc
    if not result.is_finite():
        raise SemanticError(f"{field} must be finite")
    return result


def classify_depth(depth_m: Decimal | str | int | float) -> str:
    depth = _decimal(depth_m, field="depth_m")
    if depth < 0:
        raise SemanticError("depth_m must be non-negative")
    if depth == 0:
        return "dry_unexposed"
    for name, lower, upper in DEPTH_CLASSES:
        if depth > lower and (upper is None or depth <= upper):
            return name
    raise AssertionError("unreachable depth classification")


def _serialize_decimal(value: Decimal) -> str:
    if value == 0:
        return "0"
    return format(value.normalize(), "f")


def _validate_support(support: HazardSupport) -> tuple[Decimal, str]:
    if not support.support_id:
        raise SemanticError("support_id must be non-empty")
    fraction = _decimal(support.fraction, field="support fraction")
    if fraction <= 0 or fraction > 1:
        raise SemanticError("support fraction must be in (0, 1]")

    flags = {
        "nodata": bool(support.nodata),
        "permanent_water": bool(support.permanent_water),
        "spurious_depth": bool(support.spurious_depth),
    }
    active_flags = [name for name, active in flags.items() if active]
    if len(active_flags) > 1:
        raise SemanticError(
            f"support {support.support_id} has conflicting quality flags: "
            f"{','.join(active_flags)}"
        )
    if active_flags:
        if support.depth_m is not None:
            depth = _decimal(support.depth_m, field="depth_m")
            if depth < 0:
                raise SemanticError("depth_m must be non-negative")
        return fraction, {
            "nodata": "nodata_unclassified",
            "permanent_water": "permanent_water_context",
            "spurious_depth": "spurious_depth_context",
        }[active_flags[0]]

    if support.depth_m is None:
        raise SemanticError(f"support {support.support_id} requires depth_m when unflagged")
    return fraction, classify_depth(support.depth_m)


def aggregate_cells(cells: Iterable[CensusCell]) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    seen_cells: set[str] = set()

    for cell in cells:
        if not cell.cell_id:
            raise SemanticError("cell_id must be non-empty")
        if cell.cell_id in seen_cells:
            raise SemanticError(f"duplicate census cell id: {cell.cell_id}")
        seen_cells.add(cell.cell_id)

        population = _decimal(cell.population, field="population")
        if population < 0:
            raise SemanticError("population must be non-negative")
        aoi_fraction = _decimal(cell.aoi_fraction, field="aoi_fraction")
        if aoi_fraction < 0 or aoi_fraction > 1:
            raise SemanticError("aoi_fraction must be in [0, 1]")

        support_ids: set[str] = set()
        support_fraction = Decimal("0")
        bucket_fractions: dict[str, Decimal] = {
            "dry_unexposed": Decimal("0"),
            "depth_gt_0_le_1m": Decimal("0"),
            "depth_gt_1_le_3m": Decimal("0"),
            "depth_gt_3_le_10m": Decimal("0"),
            "depth_gt_10m": Decimal("0"),
            "permanent_water_context": Decimal("0"),
            "spurious_depth_context": Decimal("0"),
            "nodata_unclassified": Decimal("0"),
            "hazard_support_missing": Decimal("0"),
        }

        for support in cell.supports:
            if support.support_id in support_ids:
                raise SemanticError(
                    f"duplicate hazard support in cell {cell.cell_id}: {support.support_id}"
                )
            support_ids.add(support.support_id)
            fraction, bucket = _validate_support(support)
            support_fraction += fraction
            if support_fraction - aoi_fraction > TOLERANCE:
                raise SemanticError(
                    f"hazard support overlaps/exceeds AOI in cell {cell.cell_id}"
                )
            bucket_fractions[bucket] += fraction

        uncovered_aoi_fraction = aoi_fraction - support_fraction
        if uncovered_aoi_fraction < 0 and abs(uncovered_aoi_fraction) <= TOLERANCE:
            uncovered_aoi_fraction = Decimal("0")
        if uncovered_aoi_fraction < 0:
            raise SemanticError(f"hazard support overlaps/exceeds AOI in cell {cell.cell_id}")
        bucket_fractions["hazard_support_missing"] += uncovered_aoi_fraction

        excluded_fraction = Decimal("1") - aoi_fraction
        populations = {
            name: population * fraction for name, fraction in bucket_fractions.items()
        }
        excluded_population = population * excluded_fraction
        accounted = sum(populations.values(), excluded_population)
        if abs(accounted - population) > TOLERANCE:
            raise SemanticError(f"population does not reconcile for cell {cell.cell_id}")

        row: dict[str, object] = {
            "cell_id": cell.cell_id,
            "source_population": _serialize_decimal(population),
            "aoi_population_considered": _serialize_decimal(population * aoi_fraction),
            "excluded_by_aoi": _serialize_decimal(excluded_population),
        }
        row.update({name: _serialize_decimal(value) for name, value in populations.items()})
        rows.append(row)

    rows.sort(key=lambda row: str(row["cell_id"]))
    total_fields = (
        "source_population",
        "aoi_population_considered",
        "excluded_by_aoi",
        "dry_unexposed",
        "depth_gt_0_le_1m",
        "depth_gt_1_le_3m",
        "depth_gt_3_le_10m",
        "depth_gt_10m",
        "permanent_water_context",
        "spurious_depth_context",
        "nodata_unclassified",
        "hazard_support_missing",
    )
    totals = {
        field: _serialize_decimal(
            sum((Decimal(str(row[field])) for row in rows), Decimal("0"))
        )
        for field in total_fields
    }

    return {
        "config_id": CONFIG_ID,
        "allocation_method": ALLOCATION_METHOD,
        "input_kind": "fixture",
        "scientific_role": "test_fixture",
        "depth_classes": [
            {
                "name": name,
                "lower_exclusive_m": _serialize_decimal(lower),
                "upper_inclusive_m": None if upper is None else _serialize_decimal(upper),
            }
            for name, lower, upper in DEPTH_CLASSES
        ],
        "cells": rows,
        "totals": totals,
    }


def canonical_json(result: Mapping[str, object]) -> str:
    return json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
