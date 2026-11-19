# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline 10,000-year synthetic GUL parity through the curve semantics bridge.

This module replays the deliberately invented hash worlds described by draft
research PR #1081 without reading its unmerged code, any database, or provider
payload. A toy 0-5 index / ratio curve replaces the algebraic multiplier, so
matching receipts establish arithmetic equivalence, NOT physical calibration.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from decimal import Decimal

from research_runners.synthetic_ci_curve_catxl_bridge_v0 import (
    fictional_event_loss_cells,
)

WORLD_COUNT = 10_000
SOURCE_LABEL = "OC_NEON_10K_SYNTH_GUL_V0"
ASSETS = tuple((f"SYNTH-{i:02d}", 100_000 + 25_000 * i) for i in range(1, 13))
# The sorted peril ordering is part of the exact string-receipt contract.
PERILS = tuple(sorted((("windstorm", 26), ("flood", 13))))
TOY_HAZARD_UNIT = "synthetic_dimensionless_hazard_index"


def _hash_bytes(text: str) -> bytes:
    # MD5 is for exact replay of the SQL toy's byte recipe, not authentication.
    return hashlib.md5(text.encode("ascii")).digest()


def synthetic_curve_for_factor(factor: int) -> tuple[tuple[int, Decimal], ...]:
    """Invented linear damage ratio y=(factor*x)/100, for index x in [0,5]."""
    if type(factor) is not int or factor not in (1, 2, 3):
        raise ValueError("only the three declared synthetic susceptibility factors are allowed")
    return ((0, Decimal("0")), (5, Decimal(factor) / Decimal(20)))


def _percentile_disc(values: list[int], numerator: int, denominator: int) -> int:
    """PostgreSQL percentile_disc rank = ceil(n*p), counting from one."""
    if not values or type(numerator) is not int or type(denominator) is not int:
        raise ValueError("nonempty exact integer quantile inputs required")
    if not 0 < numerator <= denominator:
        raise ValueError("quantile must be in (0,1]")
    ranked = sorted(values)
    position = (len(ranked) * numerator + denominator - 1) // denominator - 1
    return ranked[position]


def replay_synthetic_curve_10k() -> dict:
    """Reproduce a **different implementation** of the fixed fictional GUL.

    The publication-facing receipts are computed from the curve route rather
    than imported from the SQL or independent Python implementation in #1081.
    No treaty allocation is included; previous CAT-XL two-event toy is separate.
    """
    positions = dict(ASSETS)
    annual_rows: list[str] = []
    event_rows: list[str] = []
    event_asset_rows: list[str] = []
    event_intensity_rows: list[str] = []
    annual_losses: list[int] = []
    annual_maxima: list[int] = []
    peril_counts: Counter[str] = Counter()
    peril_totals: Counter[str] = Counter()
    years_with_two_perils = 0

    for year in range(WORLD_COUNT):
        gross_year = 0
        max_event = 0
        events_in_year = 0
        for peril, threshold in PERILS:
            raw = _hash_bytes(f"{SOURCE_LABEL}|{year}|{peril}")
            if raw[0] >= threshold:
                continue

            # 1..5 is an invented categorical score, NOT mm, PGA or m/s.
            score = 1 + raw[1] % 5
            grouped: dict[int, dict[str, int]] = {1: {}, 2: {}, 3: {}}
            for asset_id, _ in ASSETS:
                local = _hash_bytes(
                    f"{SOURCE_LABEL}|local|{year}|{peril}|{asset_id}"
                )
                factor = 1 + local[2] % 3
                grouped[factor][asset_id] = score

            # Critically, individual local factors change a *fictional
            # susceptibility curve*, not the hazard's global index.
            cell_map: dict[str, int] = {}
            for factor, subset in grouped.items():
                if subset:
                    cells = fictional_event_loss_cells(
                        positions_eur=positions,
                        intensities=subset,
                        curve_points=synthetic_curve_for_factor(factor),
                        source_curve_id=f"SYNTH-NEON-GUL-FACTOR-{factor}",
                        asset_class="SYNTH-GENERIC-PROPERTY",
                        curve_unit=TOY_HAZARD_UNIT,
                        event_unit=TOY_HAZARD_UNIT,
                        output_metric="fractional_damage_ratio",
                    )
                    cell_map.update(cells)
            if set(cell_map) != set(positions):
                raise AssertionError("toy event must retain all twelve exact assets")
            event_sum = 0
            for asset_id, value in ASSETS:
                amount = cell_map[asset_id]
                if not 0 <= amount <= value:
                    raise AssertionError("loss outside fictional asset-value bound")
                event_asset_rows.append(f"{year}:{peril}:{asset_id}:{amount}")
                event_sum += amount

            event_rows.append(f"{year}:{peril}:{event_sum}")
            event_intensity_rows.append(f"{year}:{peril}:{score}")
            events_in_year += 1
            peril_counts[peril] += 1
            peril_totals[peril] += event_sum
            gross_year += event_sum
            max_event = max(max_event, event_sum)

        years_with_two_perils += events_in_year == 2
        annual_rows.append(f"{year}:{gross_year}:{max_event}:{events_in_year}")
        annual_losses.append(gross_year)
        annual_maxima.append(max_event)

    def receipt(rows: list[str]) -> str:
        return hashlib.md5("|".join(rows).encode("ascii")).hexdigest()

    total = sum(annual_losses)
    return {
        "classification": "INDEPENDENTLY_SYNTHETIC_CURVE_TO_GUL_10K_PARITY_ONLY",
        "model_input_approved": False,
        "real_insurer": False,
        "real_hazard_or_vulnerability": False,
        "external_source_rows_used": 0,
        "neon_query_executed": False,
        "treaty_or_retro_executed": False,
        "curve_unit": TOY_HAZARD_UNIT,
        "worlds": len(annual_losses),
        "assets": len(ASSETS),
        "invented_exposure_value_eur": sum(positions.values()),
        "events": sum(peril_counts.values()),
        "zero_event_years": annual_losses.count(0),
        "years_with_both_perils": years_with_two_perils,
        "gross_loss_total_eur": total,
        "aal_eur": str(Decimal(total) / Decimal(WORLD_COUNT)),
        "aep99_eur": _percentile_disc(annual_losses, 99, 100),
        "aep995_eur": _percentile_disc(annual_losses, 995, 1000),
        "oep99_eur": _percentile_disc(annual_maxima, 99, 100),
        "oep995_eur": _percentile_disc(annual_maxima, 995, 1000),
        "max_annual_eur": max(annual_losses),
        "peril_event_counts": dict(sorted(peril_counts.items())),
        "peril_loss_totals_eur": dict(sorted(peril_totals.items())),
        "receipts_md5": {
            "annual": receipt(annual_rows),
            "event": receipt(event_rows),
            "event_asset": receipt(event_asset_rows),
            "event_intensity": receipt(event_intensity_rows),
        },
    }


if __name__ == "__main__":
    import json
    print(json.dumps(replay_synthetic_curve_10k(), indent=2, sort_keys=True))
