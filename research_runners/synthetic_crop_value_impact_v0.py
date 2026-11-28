#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Invented crop-value direct-impact arithmetic on the synthetic-only area overlay.

No original agricultural sources, insured exposure values, claims, real hazard
intensity, calibrated vulnerability, or CAT event frequencies. This module is
NOT an insured gross/net loss, ELT, AEP, OEP, risk premium or catastrophe model.
All values and damage ratios are intentionally hypothetical fixed examples.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import json
from pathlib import Path

if __package__:
    from .synthetic_crop_hazard_area_overlay_v0 import (
        OverlayError, _read_json, overlay,
    )
else:
    from synthetic_crop_hazard_area_overlay_v0 import (
        OverlayError, _read_json, overlay,
    )

HECTARE_M2 = Decimal("10000")
CENT = Decimal("0.01")
# Invented for arithmetic tests only. EUR per hectare is not insured TIV.
FICTIONAL_VALUE_PER_HA = {
    "SYNTH-WHEAT": Decimal("10000"),
    "SYNTH-BARLEY": Decimal("8000"),
    "SYNTH-MAIZE": Decimal("14000"),
}
# Invented illustrative fraction of crop value impaired at each intensity.
# No interpolation/extrapolation, agricultural season, soil, fragility or cover.
TOY_DAMAGE_RATIOS = {
    "flood": {
        Decimal("0"): Decimal("0"),
        Decimal("1"): Decimal("0.20"),
        Decimal("2"): Decimal("0.50"),
        Decimal("3"): Decimal("0.75"),
    },
    "hail": {
        Decimal("0"): Decimal("0"),
        Decimal("20"): Decimal("0.10"),
        Decimal("40"): Decimal("0.35"),
        Decimal("60"): Decimal("0.65"),
    },
}


class ImpactError(ValueError):
    """Toy impact blocked: source or scenario assumptions were not met."""


def _decimal(value: object, label: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise ImpactError(label + " must be decimal")
    try:
        d = Decimal(str(value))
    except InvalidOperation as exc:
        raise ImpactError(label + " is malformed") from exc
    if not d.is_finite() or d < 0:
        raise ImpactError(label + " must be finite and nonnegative")
    return d


def _money(value: Decimal) -> str:
    if not value.is_finite() or value < 0:
        raise ImpactError("unbounded value amount")
    return str(value.quantize(CENT, rounding=ROUND_HALF_UP))


def hypothetical_impact(parcels: dict, hazard: dict) -> dict:
    """Re-execute exact fictional polygon overlay; only then map loss fractions."""
    try:
        support = overlay(parcels, hazard)
    except OverlayError as exc:
        raise ImpactError("synthetic support gate: " + str(exc)) from exc
    peril = support["peril"]
    ratios = TOY_DAMAGE_RATIOS[peril]
    parcel_rows = []
    known_total = Decimal(0)
    unobserved_upper_total = Decimal(0)
    asset_value_total = Decimal(0)
    for field in support["synthetic_parcels"]:
        cls = field["crop_class"]
        if cls not in FICTIONAL_VALUE_PER_HA:
            raise ImpactError("unsupported fictional crop class")
        euro_per_ha = FICTIONAL_VALUE_PER_HA[cls]
        value = _decimal(field["total_area_m2"], "area") / HECTARE_M2 * euro_per_ha
        asset_value_total += value

        known_impact = Decimal(0)
        for bin in field["intensity_bands"]:
            intensity = _decimal(bin["intensity"], "intensity")
            if intensity not in ratios:
                raise ImpactError("intensity not in explicitly invented toy ratio table")
            area = _decimal(bin["area_m2"], "covered band area")
            known_impact += area / HECTARE_M2 * euro_per_ha * ratios[intensity]
        unobserved_area = (
            _decimal(field["explicit_nodata_area_m2"], "nodata")
            + _decimal(field["outside_support_unknown_area_m2"], "unknown")
        )
        upper_unknown = unobserved_area / HECTARE_M2 * euro_per_ha
        if known_impact + upper_unknown > value + Decimal("0.01"):
            raise ImpactError("hypothetical impact exceeds entire parcel value")
        known_total += known_impact
        unobserved_upper_total += upper_unknown
        parcel_rows.append({
            "fictional_parcel_id": field["parcel_id"],
            "fictional_crop_class": cls,
            "fictional_asset_value_eur": _money(value),
            "known_support_direct_impact_eur": _money(known_impact),
            "unknown_support_increment_min_eur": "0.00",
            "unknown_support_increment_max_eur": _money(upper_unknown),
            "illustrative_event_direct_impact_lower_eur": _money(known_impact),
            "illustrative_event_direct_impact_upper_eur": _money(
                known_impact + upper_unknown
            ),
        })
    upper_total = known_total + unobserved_upper_total
    if upper_total > asset_value_total + CENT:
        raise ImpactError("portfolio impact upper bound exceeds its invented value")
    return {
        "profile": "synthetic-crop-direct-value-impact-v0",
        "event_id": support["event_id"],
        "peril": peril,
        "hypothetical_crop_value_per_hectare_eur": {
            key: _money(val) for key, val in sorted(FICTIONAL_VALUE_PER_HA.items())
        },
        "hypothetical_intensity_to_fraction_impaired": {
            str(k): str(v) for k, v in sorted(ratios.items())
        },
        "parcel_count": support["parcel_count"],
        "fictional_total_asset_value_eur": _money(asset_value_total),
        "fictional_known_support_direct_impact_eur": _money(known_total),
        "fictional_unobserved_support_impact_increment_min_eur": "0.00",
        "fictional_unobserved_support_impact_increment_max_eur": _money(
            unobserved_upper_total
        ),
        "fictional_total_direct_impact_lower_eur": _money(known_total),
        "fictional_total_direct_impact_upper_eur": _money(upper_total),
        "per_fictional_parcel": parcel_rows,
        "unknown_hazard_support_not_assumed_dry": True,
        "all_values_damage_ratios_and_locations_invented": True,
        "source_observed_crop_or_hazard_rows_used": 0,
        "underwriting_or_insured_tiv": False,
        "insured_gross_or_net_loss_calculated": False,
        "event_frequency_calibrated": False,
        "elt_or_aep_oep_calculated": False,
        "admitted_cat_model_input": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("synthetic_parcels_json", type=Path)
    parser.add_argument("synthetic_hazard_json", type=Path)
    parser.add_argument("--parcels-sha256", required=True)
    parser.add_argument("--hazard-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        result = hypothetical_impact(
            _read_json(args.synthetic_parcels_json, args.parcels_sha256),
            _read_json(args.synthetic_hazard_json, args.hazard_sha256),
        )
    except (ImpactError, OverlayError, OSError, OverflowError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
