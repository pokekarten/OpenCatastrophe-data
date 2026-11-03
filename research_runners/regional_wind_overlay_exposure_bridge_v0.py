# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exact-byte-pinned wind geometry -> NUTS2 sample exposure comparison.

No calibrated hazard, provider-byte admission, policy/insurer loss or event
frequency. Partial footprint support is UNKNOWN weather, never zero wind.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re

from research_runners.regional_wind_footprint_overlay_v0 import overlay
from research_runners.regional_exposure_hazard_join_v0 import join

MAX_INPUT_BYTES = 20_000_000
MAX_EXPOSURES = 20_000
SHA = re.compile(r"[0-9a-f]{64}\Z")


class BridgeError(ValueError):
    pass


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise BridgeError("duplicate JSON key in source")
        result[key] = value
    return result


def _nonfinite(value):
    raise BridgeError("nonfinite numeric JSON value")


def _strict_pinned(raw: bytes, expected: str, label: str) -> dict:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_INPUT_BYTES:
        raise BridgeError(f"{label} byte size out of bounds")
    if type(expected) is not str or SHA.fullmatch(expected) is None:
        raise BridgeError(f"{label} expected SHA-256 invalid")
    if sha256(raw).hexdigest() != expected:
        raise BridgeError(f"{label} bytes differ from expected SHA-256")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                           parse_constant=_nonfinite)
    except (ValueError, UnicodeError, TypeError) as exc:
        raise BridgeError(f"{label} input is not strict JSON") from exc
    if type(value) is not dict:
        raise BridgeError(f"{label} input root must be JSON object")
    return value


def run_bridge(regions_bytes: bytes, storm_bytes: bytes, exposures_bytes: bytes,
               *, regions_sha256: str, storm_sha256: str,
               exposures_sha256: str) -> dict:
    """Join one original physical storm's fully mapped NUTS2 cells only."""
    regions = _strict_pinned(regions_bytes, regions_sha256, "regions")
    storm = _strict_pinned(storm_bytes, storm_sha256, "storm")
    inp = _strict_pinned(exposures_bytes, exposures_sha256, "exposures")
    if set(inp) != {"exposures"} or type(inp["exposures"]) is not list:
        raise BridgeError("exposures document must contain only an exposures array")
    if len(inp["exposures"]) > MAX_EXPOSURES:
        raise BridgeError("exposure row count exceeds bound")

    # Validate ALL source exposure records even if the region weather
    # subsequently proves incomplete; avoid hiding malformed source rows.
    join({"exposures": inp["exposures"], "hazards": []})
    measured = overlay(regions, storm)
    coverage = {m["nuts2"]: m for m in measured["region_metrics"]}
    complete = {
        code for code, m in coverage.items()
        if (m["covered_area_fraction"] == 1.0
            and m["uncovered_area_weather_unknown"] is False
            and m["max_10m_gust_mps_in_covered_area"] is not None)
    }
    unknown_weather = sorted(set(coverage) - complete)

    eligible = []
    excluded = []
    for exposure in inp["exposures"]:
        if exposure["nuts_version"] != measured["nuts_version"]:
            reason = "NUTS_VINTAGE_NOT_SAME_AS_HAZARD_GEOMETRY"
        elif exposure["nuts2"] not in coverage:
            reason = "REGION_HAS_NO_BOUNDARY_IN_SOURCE"
        elif exposure["nuts2"] not in complete:
            reason = "WIND_FOOTPRINT_INCOMPLETE_NOT_ZERO_WIND"
        else:
            eligible.append(exposure)
            continue
        excluded.append({"exposure_record_id": exposure["record_id"],
                         "reason": reason})
    excluded.sort(key=lambda x: x["exposure_record_id"])

    hazards = [
        {"record_id": f"overlay:{measured['event_id']}:{code}",
         "dataset_id": measured["event_source_id"],
         "event_id": measured["event_id"],
         "event_date": measured["event_date"],
         "nuts_version": measured["nuts_version"],
         "nuts2": code, "peril": "extratropical_windstorm",
         "gust_mps": coverage[code]["max_10m_gust_mps_in_covered_area"],
         "aggregation": "max_of_footprint_grid_cells"}
        for code in sorted(complete)
    ]
    compared = join({"exposures": eligible, "hazards": hazards})
    return {
        "evidence_class": "WIND_FOOTPRINT_REGIONAL_EXPOSURE_COMPARISON_ONLY",
        "source_input_sha256": {
            "region_geometry_bytes": regions_sha256,
            "storm_grid_bytes": storm_sha256,
            "sample_exposure_bytes": exposures_sha256,
        },
        "source_provider_hash_claims_independently_authenticated": False,
        "source_rights_and_scientific_release_verified": False,
        "region_geometry_overlay_performed": True,
        "same_physical_event_id": measured["event_id"],
        "same_event_date": measured["event_date"],
        "nuts_version": measured["nuts_version"],
        "full_coverage_region_count": len(complete),
        "weather_incomplete_regions": unknown_weather,
        "weather_not_evaluated_exposures": excluded,
        "regionally_joined": compared["matched"],
        "full_coverage_hazard_without_exposure": compared["unmatched_hazards"],
        "eligible_but_unused_exposure_ids": compared["unused_exposure_ids"],
        "no_inference_for_incomplete_weather": True,
        "financial_amounts_are_original_sampled_sum_insured_only": True,
        "peril_intensity_is_maximum_10m_gust_mps_not_damage": True,
        "event_frequency_or_stochastic_worlds_calibrated": False,
        "economic_or_insured_losses_calculated": False,
        "vulnerability_model_calibrated": False,
        "real_insurer_market_allocation_inferred": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("regions", "storm", "exposures"):
        parser.add_argument(name, type=Path)
        parser.add_argument("--"+name+"-sha256", required=True)
    args = parser.parse_args()
    inputs = {}
    for name in ("regions", "storm", "exposures"):
        path = getattr(args, name)
        if not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
            parser.error(name+" original input size is not approved")
        inputs[name] = path.read_bytes()
    result = run_bridge(inputs["regions"], inputs["storm"], inputs["exposures"],
                        regions_sha256=args.regions_sha256,
                        storm_sha256=args.storm_sha256,
                        exposures_sha256=args.exposures_sha256)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
