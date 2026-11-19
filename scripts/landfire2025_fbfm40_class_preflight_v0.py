# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline LF 2025 CONUS FBFM40 categorical pixel-value science preflight.

Use only on a separately authorized, preselected *sample* already extracted
outside the repository. This tool does not read TIFF/ZIP, acquire provider
bytes, establish source provenance, clear rights or admit an insurance model.
Source: https://www.landfire.gov/sites/default/files/DataDictionary/LF2025/LF2025_FBFM40ADD.pdf
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

SOURCE_ID = "us.landfire.fuel-vegetation.2025"
PRODUCT = "LF2025_FBFM40_CONUS"
MAX_SAMPLES = 16_384
MAX_JSON_BYTES = 524_288
NODATA = -9999
NONBURNABLE = {91: "NB1_urban_developed", 92: "NB2_snow_ice", 93: "NB3_agriculture",
               98: "NB8_open_water", 99: "NB9_barren"}
FUEL_FAMILIES = {
    "GR_grass": frozenset(range(101, 110)),
    "GS_grass_shrub": frozenset(range(121, 125)),
    "SH_shrub": frozenset(range(141, 150)),
    "TU_timber_understory": frozenset(range(161, 166)),
    "TL_timber_litter": frozenset(range(181, 190)),
    "SB_slash_blowdown": frozenset(range(201, 205)),
}
BURNABLE = frozenset().union(*FUEL_FAMILIES.values())
ALLOWED = BURNABLE | NONBURNABLE.keys() | {NODATA}
assert len(BURNABLE) == 40 and len(ALLOWED) == 46


class LandfireClassError(ValueError):
    """Not an unambiguous, bounded LF2025 nonseasonal FBFM40 class sample."""


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in pairs:
        if k in out:
            raise LandfireClassError("duplicate JSON evidence key")
        out[k] = v
    return out


def _reject_nonfinite(_: str) -> None:
    raise LandfireClassError("nonfinite raster class value")


def screen_lf2025_fbfm40_sample(dataset: str, values: Any) -> dict[str, Any]:
    """Validate the categorical domain; never treat class codes as fire risk.

    The input must be an externally sourced, scientifically preselected vector.
    These checks do not prove any pixel has genuine LANDFIRE provenance.
    """
    if not isinstance(dataset, str) or dataset != PRODUCT:
        raise LandfireClassError("expected exact nonseasonal LF2025 FBFM40 CONUS product")
    if not isinstance(values, list) or not 1 <= len(values) <= MAX_SAMPLES:
        raise LandfireClassError("expected a bounded nonempty class sample array")
    histogram: Counter[int] = Counter()
    for v in values:
        if isinstance(v, bool) or not isinstance(v, int) or v not in ALLOWED:
            raise LandfireClassError("unexpected, non-integer or unclassified FBFM40 value")
        histogram[v] += 1
    fuel_count = sum(histogram[k] for k in BURNABLE)
    nonburnable_count = sum(histogram[k] for k in NONBURNABLE)
    nodata_count = histogram[NODATA]
    valid_count = fuel_count + nonburnable_count
    if valid_count == 0:
        raise LandfireClassError("all-NODATA sample has no scientific fuel information")
    if fuel_count + nonburnable_count + nodata_count != len(values):
        raise LandfireClassError("class counts do not conserve sampled pixels")
    return {
        "source_id": SOURCE_ID,
        "declared_nonseasonal_product": PRODUCT,
        "total_sampled_pixel_values": len(values),
        "valid_class_pixels": valid_count,
        "burnable_fuel_model_pixels": fuel_count,
        "nonburnable_class_pixels": nonburnable_count,
        "nodata_pixels": nodata_count,
        "nonburnable_by_class": {str(k): histogram[k] for k in sorted(NONBURNABLE)},
        "burnable_by_family": {family: sum(histogram[k] for k in codes)
                               for family, codes in FUEL_FAMILIES.items()},
        "observed_class_counts": {str(k): histogram[k] for k in sorted(histogram)},
        "supported_fuel_model_code_count": 40,
        "supported_nonburnable_code_count": 5,
        "fuel_model_is_nominal_categorical_not_continuous": True,
        "no_data_cannot_be_treated_as_nonburnable": True,
        "sample_is_not_a_complete_raster": True,
        "raster_crs_resolution_and_georeferencing_verified": False,
        "original_archive_md5_and_sha256_verified": False,
        "sample_original_provider_provenance_verified": False,
        "sampling_representativeness_verified": False,
        "ignition_probability_or_event_frequency_derived": False,
        "commercial_data_rights_verified": False,
        "model_source_admitted": False,
        "neon_storage": "not_performed",
    }


def screen_sample_json(raw: bytes) -> dict[str, Any]:
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_JSON_BYTES:
        raise LandfireClassError("sample JSON must be bounded nonempty bytes")
    try:
        doc = json.loads(raw.decode("utf-8", errors="strict"),
                         object_pairs_hook=_unique, parse_constant=_reject_nonfinite)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise LandfireClassError("invalid sample JSON syntax") from exc
    if not isinstance(doc, dict) or set(doc) != {"dataset", "values"}:
        raise LandfireClassError("expected only dataset and values keys")
    return screen_lf2025_fbfm40_sample(doc["dataset"], doc["values"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-json", type=Path, required=True,
                        help="independently authorized local categorical values; no remote URL")
    args = parser.parse_args()
    with args.sample_json.open("rb") as reader:
        raw = reader.read(MAX_JSON_BYTES + 1)
    print(json.dumps(screen_sample_json(raw), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
