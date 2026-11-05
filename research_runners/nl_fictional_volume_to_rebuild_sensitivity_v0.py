# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Research-only fictional 3D building-rebuild sensitivity, never TIV.

Demonstrates how an *independently licensed and correctly dated* construction
replacement-cost unit rate COULD interact with building-envelope m3 and a
single dimensionless temporal escalation factor.

Only COMPLETELY INVENTED site volumes/rates are accepted. Real BAG, 3DBAG,
insurer, policy, address, coordinate or provider source data are forbidden.
The min/max of three LoD volumes is a geometry sensitivity envelope, NOT a
confidence interval. No production exposure, CAT or treaty input.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import argparse
import json
import tomllib
from pathlib import Path
import re
import sys

MAX_BYTES = 250_000
MAX_BUILDINGS = 100
ID = re.compile(r"SYNTH-BLDG-(?:[0-9]{3})\Z")
ALLOWED_LODS = ("lod12", "lod13", "lod22")
CENT = Decimal("0.01")


class FictionalRebuildError(ValueError):
    """Unjustified cost assumptions, unsafe source data or broken units."""


def read_fixture(path):
    p = Path(path)
    if p.stat().st_size > MAX_BYTES:
        raise FictionalRebuildError("research input over budget")
    # TOML is the repository's established scenario format. The standard
    # library parser rejects duplicate keys; _number rejects nonfinite inputs.
    return tomllib.loads(p.read_text(encoding="utf-8"))


def _keys(value, required, name):
    if not isinstance(value, dict) or set(value) != set(required):
        raise FictionalRebuildError(name + ": wrong fields or unapproved source data")
    return value


def _number(value, name, *, lower, upper):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise FictionalRebuildError(name + ": requires numeric decimal")
    if isinstance(value, str) and not re.fullmatch(r"(?:0|[1-9][0-9]*)(?:\.[0-9]{1,6})?", value):
        raise FictionalRebuildError(name + ": require a plain positive decimal string")
    try:
        n = Decimal(str(value))
    except InvalidOperation as exc:
        raise FictionalRebuildError(name + ": not decimal") from exc
    if not n.is_finite() or n < lower or n > upper:
        raise FictionalRebuildError(name + ": outside fictional research bounds")
    return n


def calculate(data):
    _keys(data, {
        "schema", "provenance", "scenario", "buildings",
    }, "fixture")
    if data["schema"] != "fictional-dutch-rebuild-cost-sensitivity-v0":
        raise FictionalRebuildError("unsupported version")
    prov = _keys(data["provenance"], {
        "source_kind", "real_provider_rows", "licensed_cost_baseline",
        "real_insurer_identity", "source_admitted", "model_input_approved",
    }, "provenance")
    if not (
        prov["source_kind"] == "invented_fixture_only"
        and type(prov["real_provider_rows"]) is int and prov["real_provider_rows"] == 0
        and prov["licensed_cost_baseline"] is False
        and prov["real_insurer_identity"] is False
        and prov["source_admitted"] is False
        and prov["model_input_approved"] is False
    ):
        raise FictionalRebuildError("not strictly invented proof-of-math input")
    scenario = _keys(data["scenario"], {
        "currency", "rate_unit", "cost_rate_baseline_period", "target_period",
        "rate_was_already_indexed_to_target",
        "fictional_low_rate_eur_per_m3",
        "fictional_high_rate_eur_per_m3",
        "fictional_base_period_index", "fictional_target_period_index",
        "fictional_index_style",
    }, "scenario")
    if (scenario["currency"] != "EUR" or scenario["rate_unit"] != "EUR_per_m3"
            or scenario["fictional_index_style"] != "independent_CBS_style_synthetic_numbers"):
        raise FictionalRebuildError("not a permitted fictional EUR/m3 scenario")
    baseline = scenario["cost_rate_baseline_period"]
    target = scenario["target_period"]
    if not all(isinstance(t, str) and re.fullmatch(r"20[0-9]{2}-(?:0[1-9]|1[0-2])", t)
               for t in (baseline, target)):
        raise FictionalRebuildError("periods must be YYYY-MM")
    indexed = scenario["rate_was_already_indexed_to_target"]
    if type(indexed) is not bool:
        raise FictionalRebuildError("rate indexing provenance must be boolean")
    low = _number(scenario["fictional_low_rate_eur_per_m3"], "fictional low cost rate",
                  lower=Decimal("0.01"), upper=Decimal("10000"))
    high = _number(scenario["fictional_high_rate_eur_per_m3"], "fictional high cost rate",
                   lower=low, upper=Decimal("10000"))
    base_i = _number(scenario["fictional_base_period_index"], "fictional base index",
                     lower=Decimal("1"), upper=Decimal("10000"))
    target_i = _number(scenario["fictional_target_period_index"], "fictional target index",
                       lower=Decimal("1"), upper=Decimal("10000"))
    factor = target_i / base_i
    if (indexed or baseline == target) and factor != 1:
        raise FictionalRebuildError("double-escalation: rate already at target or same period")
    if baseline > target:
        raise FictionalRebuildError("cannot back-date fictional reference rate without methodology")
    if factor > Decimal("4") or factor < Decimal("0.25"):
        raise FictionalRebuildError("unreasonable single synthetic index escalation")

    buildings = data["buildings"]
    if (not isinstance(buildings, list) or not 1 <= len(buildings) <= MAX_BUILDINGS):
        raise FictionalRebuildError("invalid synthetic building count")
    ids = set()
    sums = {lod: Decimal(0) for lod in ALLOWED_LODS}
    per_build_low, per_build_high = Decimal(0), Decimal(0)
    chosen_lod = "lod13"
    chosen_sum = Decimal(0)
    for row in buildings:
        r = _keys(row, {"id", "usage_class", "volumes_m3"}, "synthetic building")
        ident = r["id"]
        if not isinstance(ident, str) or not ID.fullmatch(ident) or ident in ids:
            raise FictionalRebuildError("duplicate or non-fictional building identifier")
        ids.add(ident)
        if r["usage_class"] != "synthetic_standard_residential":
            raise FictionalRebuildError("not validated for non-residential/monumental typologies")
        v = _keys(r["volumes_m3"], ALLOWED_LODS, "fictional LoD volumes")
        values = {
            lod: _number(v[lod], lod+" volume m3", lower=Decimal("1"),
                         upper=Decimal("1000000"))
            for lod in ALLOWED_LODS
        }
        for lod, value in values.items():
            sums[lod] += value
        lo_vol = min(values.values())
        hi_vol = max(values.values())
        # Bounds are sensitivity intervals, not physical volume truth or
        # confidence limits. Never multiply all three LoD variants together.
        per_build_low += lo_vol * low * factor
        per_build_high += hi_vol * high * factor
        chosen_sum += values[chosen_lod] * (low + high) / 2 * factor
    lower = per_build_low.quantize(CENT, rounding=ROUND_HALF_UP)
    upper = per_build_high.quantize(CENT, rounding=ROUND_HALF_UP)
    center = chosen_sum.quantize(CENT, rounding=ROUND_HALF_UP)
    if not (lower <= center <= upper):
        raise FictionalRebuildError("valuation arithmetic/sensitivity ordering broken")

    return {
        "schema": "fictional-rebuilding-value-math-receipt-v0",
        "currency": "EUR",
        "scenario_only": True,
        "fictional_building_count": len(buildings),
        "input_volume_unit": "modelled_envelope_m3_invented",
        "rate_unit": "fictional_EUR_per_m3",
        "fictional_lod_volume_sums_m3": {
            lod: str(sums[lod]) for lod in ALLOWED_LODS
        },
        "fictional_index_ratio_target_over_base": str(factor),
        "fictional_rebuild_lower_eur": str(lower),
        "fictional_rebuild_mid_eur": str(center),
        "fictional_rebuild_upper_eur": str(upper),
        "sensitivity_interval_not_confidence_band": True,
        "cost_rate_rights_reviewed": False,
        "original_3dbag_release_pinned": False,
        "3dbag_original_feature_bytes_used": False,
        "real_buildings_or_insurer_inferred": False,
        "premium_or_coverage_inferred": False,
        "actual_insured_tiv": None,
        "cat_model_input_approved": False,
        "building_peril_or_treaty_model_calibrated": False,
        "gross_net_oep_aep_ip_curves_computed": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True,
                        help="fully invented source-free scenario JSON")
    args = parser.parse_args(argv)
    try:
        result = calculate(read_fixture(args.fixture))
    except (ValueError, OSError, UnicodeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
