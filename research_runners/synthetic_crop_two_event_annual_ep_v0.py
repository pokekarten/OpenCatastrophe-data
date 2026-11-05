#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""10,000 fictional crop impact years with EXACT two-event OEP/AEP reference.

Synthetic direct-value impairment arithmetic only. NOT insurance GUL/IL,
actual frequencies, insurer AAL, calibrated CAT, stochastic hazard, or OEP/AEP
for any real portfolio. Occurrences and independence are entirely invented.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from hashlib import sha256
from itertools import product
import json

from shapely.geometry import box, mapping
if __package__:
    from .synthetic_crop_value_impact_v0 import hypothetical_impact
else:
    from synthetic_crop_value_impact_v0 import hypothetical_impact

YEARS = 10000
SEED = 20261105
EVENTS = (("SYNTH-EVENT-001", "flood", 26), ("SYNTH-EVENT-002", "hail", 13))
THRESHOLDS_EUR = (0, 2250, 4900, 5000, 7150, 11900, 14000)


class AnnualCurveError(ValueError):
    """Invented fixture, event probability, or loss accounting drift."""


def _money(cents: int) -> str:
    if type(cents) is not int or cents < 0:
        raise AnnualCurveError("invalid integer-cent value")
    return str(Decimal(cents) / 100)


def _cents(value: str) -> int:
    number = Decimal(value)
    if not number.is_finite() or number < 0 or number != number.quantize(Decimal("0.01")):
        raise AnnualCurveError("invalid fractional-cent source impact")
    return int(number * 100)


def _fields() -> dict:
    return {
        "schema": "synthetic-crop-parcels-v0", "crs": "EPSG:3035",
        "synthetic_only": True, "external_source_rows_used": 0,
        "parcels": [
            {"parcel_id": "SYNTH-CROP-001", "crop_class": "SYNTH-WHEAT",
             "geometry": mapping(box(0, 0, 100, 100))},
            {"parcel_id": "SYNTH-CROP-002", "crop_class": "SYNTH-MAIZE",
             "geometry": mapping(box(100, 0, 200, 100))},
        ],
    }


def _hazard(event_id: str, peril: str) -> dict:
    result = {
        "schema": "synthetic-crop-hazard-v0", "crs": "EPSG:3035",
        "synthetic_only": True, "external_source_rows_used": 0,
        "event_id": event_id, "peril": peril, "unit": "m" if peril == "flood" else "mm",
    }
    if (event_id, peril) == ("SYNTH-EVENT-001", "flood"):
        zones = (
            ("SYNTH-ZONE-001", 1, False, box(0, 0, 150, 100)),
            ("SYNTH-ZONE-002", 2, False, box(50, 0, 100, 100)),
            ("SYNTH-ZONE-003", None, True, box(150, 0, 200, 100)),
        )
    elif (event_id, peril) == ("SYNTH-EVENT-002", "hail"):
        zones = (
            ("SYNTH-ZONE-001", 40, False, box(0, 0, 50, 100)),
            ("SYNTH-ZONE-002", 20, False, box(50, 0, 100, 100)),
            ("SYNTH-ZONE-003", 0, False, box(100, 0, 200, 100)),
        )
    else:
        raise AnnualCurveError("unexpected invented event identity/peril")
    result["zones"] = [
        {"zone_id": ident, "intensity": intensity, "nodata": missing,
         "geometry": mapping(geom)}
        for ident, intensity, missing, geom in zones
    ]
    return result


def build_events() -> list[dict]:
    fields = _fields()
    result = []
    for event_id, peril, byte_threshold in EVENTS:
        impact = hypothetical_impact(fields, _hazard(event_id, peril))
        if (impact["event_id"] != event_id or impact["peril"] != peril or
                impact["source_observed_crop_or_hazard_rows_used"] != 0 or
                impact["underwriting_or_insured_tiv"] is not False or
                impact["admitted_cat_model_input"] is not False):
            raise AnnualCurveError("source identity/admission condition drift")
        lower = _cents(impact["fictional_total_direct_impact_lower_eur"])
        upper = _cents(impact["fictional_total_direct_impact_upper_eur"])
        if not 0 <= lower <= upper:
            raise AnnualCurveError("event uncertainty bounds violated")
        result.append({
            "event_id": event_id, "peril": peril,
            "annual_presence_p": Fraction(byte_threshold, 256),
            "byte_threshold": byte_threshold,
            "lower_cents": lower, "upper_cents": upper,
        })
    if ([e["lower_cents"] for e in result] != [490000, 225000] or
            [e["upper_cents"] for e in result] != [1190000, 225000]):
        raise AnnualCurveError("toy spatial value-impact pipeline drift")
    return result


def enumerate_year_worlds(events: list[dict]) -> list[dict]:
    if len(events) != 2:
        raise AnnualCurveError("exactly two invented event types supported")
    worlds = []
    for present in product((False, True), repeat=2):
        probability = Fraction(1)
        lower = []
        upper = []
        for event, included in zip(events, present):
            p = event["annual_presence_p"]
            if not isinstance(p, Fraction) or not Fraction(0) <= p <= Fraction(1):
                raise AnnualCurveError("invalid annual Bernoulli probability")
            probability *= p if included else 1 - p
            if included:
                lower.append(event["lower_cents"])
                upper.append(event["upper_cents"])
        worlds.append({
            "presence": present, "weight": probability,
            "oep_lower": max(lower, default=0),
            "oep_upper": max(upper, default=0),
            "aep_lower": sum(lower),
            "aep_upper": sum(upper),
        })
    if sum((w["weight"] for w in worlds), Fraction()) != 1:
        raise AnnualCurveError("event probabilities do not total one")
    return worlds


def _occurs(year: int, event: dict) -> bool:
    # SHA256 is used only to make toy yearly draws reproducible.
    # A deterministic byte draw does NOT validate actual peril independence.
    payload = f"synthetic-crop-ep-v0|{SEED}|{year}|{event['event_id']}".encode("ascii")
    return sha256(payload).digest()[0] < event["byte_threshold"]


def exceedance_probability(worlds: list[dict], key: str, cents: int) -> Fraction:
    if key not in ("oep_lower", "oep_upper", "aep_lower", "aep_upper"):
        raise AnnualCurveError("unsupported annual loss metric")
    return sum((w["weight"] for w in worlds if w[key] > cents), Fraction())


def compute() -> dict:
    events = build_events()
    worlds = enumerate_year_worlds(events)
    annual: dict[str, list[int]] = {key: [] for key in
                                   ("oep_lower", "oep_upper", "aep_lower", "aep_upper")}
    event_counts = {e["event_id"]: 0 for e in events}
    simultaneous = 0
    ledger_digest = sha256()
    for year in range(YEARS):
        included = [event for event in events if _occurs(year, event)]
        simultaneous += len(included) == 2
        for event in included:
            event_counts[event["event_id"]] += 1
        sample = {
            "oep_lower": max((e["lower_cents"] for e in included), default=0),
            "oep_upper": max((e["upper_cents"] for e in included), default=0),
            "aep_lower": sum(e["lower_cents"] for e in included),
            "aep_upper": sum(e["upper_cents"] for e in included),
        }
        if not (sample["oep_lower"] <= sample["oep_upper"] <= sample["aep_upper"] and
                sample["oep_lower"] <= sample["aep_lower"] <= sample["aep_upper"]):
            raise AnnualCurveError("OEP/AEP/bounds ordering failed")
        for key, value in sample.items():
            annual[key].append(value)
        ledger_digest.update((json.dumps(
            [year, [e["event_id"] for e in included], sample],
            sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"))
    curves = []
    for threshold_eur in THRESHOLDS_EUR:
        threshold_cents = threshold_eur * 100
        entry = {"threshold_eur_strictly_exceeded": str(threshold_eur)}
        for metric, sampled in annual.items():
            exact = exceedance_probability(worlds, metric, threshold_cents)
            count = sum(amount > threshold_cents for amount in sampled)
            entry[metric] = {
                "analytic_probability_fraction": f"{exact.numerator}/{exact.denominator}",
                "analytic_probability": round(float(exact), 9),
                "sample_count_exceeding_in_10000_years": count,
                "sample_probability": round(count / YEARS, 9),
            }
        for side in ("lower", "upper"):
            if (entry["oep_" + side]["analytic_probability"] >
                    entry["aep_" + side]["analytic_probability"]):
                raise AnnualCurveError("AEP must be at least OEP at fixed threshold")
        for family in ("oep", "aep"):
            if (entry[family + "_lower"]["analytic_probability"] >
                    entry[family + "_upper"]["analytic_probability"]):
                raise AnnualCurveError("lower/upper exceedance bounds reversed")
        curves.append(entry)

    def expected_loss(key: str) -> str:
        cents = sum((world["weight"] * world[key] for world in worlds), Fraction())
        result = Decimal(cents.numerator) / Decimal(cents.denominator) / 100
        return str(result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    return {
        "profile": "synthetic-crop-two-event-10k-annual-ep-math-v0",
        "sample_years": YEARS, "toy_deterministic_seed": SEED,
        "invented_annual_occurrence_convention":
            "two_independent_Bernoulli_types_max_one_each_per_year",
        "analytic_worlds": 4,
        "analytic_world_probability_sum": "1/1",
        "fictional_event_types": [
            {"id": e["event_id"], "peril": e["peril"],
             "invented_annual_presence_probability":
                 f"{e['annual_presence_p'].numerator}/{e['annual_presence_p'].denominator}",
             "direct_value_impact_lower_eur": _money(e["lower_cents"]),
             "direct_value_impact_upper_eur": _money(e["upper_cents"])}
            for e in events
        ],
        "invented_exact_expected_annual_direct_impact_lower_eur":
            expected_loss("aep_lower"),
        "invented_exact_expected_annual_direct_impact_upper_eur":
            expected_loss("aep_upper"),
        "yearly_event_counts": event_counts,
        "years_with_both_event_types": simultaneous,
        "annual_receipt_sha256_not_source_authentication": ledger_digest.hexdigest(),
        "strict_annual_exceedance_curves": curves,
        "oep_is_maximum_of_event_direct_impacts": True,
        "aep_is_sum_of_event_direct_impacts": True,
        "source_crop_or_hazard_rows_used": 0,
        "all_loss_values_and_probabilities_invented": True,
        "real_insured_aal_oep_aep_or_gross_net": False,
        "real_event_frequency_dependence_or_cat_model_calibrated": False,
        "original_dataset_admitted": False,
    }


def main() -> int:
    print(json.dumps(compute(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
