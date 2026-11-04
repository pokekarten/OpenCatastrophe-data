#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Only classify reviewed DDT Loiret 2021 reconstructed flood-depth legend.

An atlas colour class is an interval-censored, smoothed provider estimate;
it is not an observed exact parcel water depth or a calibrated loss input.
No original geospatial bytes, point locations, or source rights are assumed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


class AtlasClassBlocked(ValueError):
    """Provider edition or semantics were not proven."""


_VERSION = "DDT45_LOING_AVAL_AZI_2021"
_EVENT = "LOING_MAY_JUNE_2016"
# Four final DDT-2021 map classes, NOT the DRIEE-2017 raw 50-cm steps.
_CLASS_BOUNDS = {
    "0-0.5": ("0.00", "0.50"),
    "0.5-1": ("0.50", "1.00"),
    "1-2": ("1.00", "2.00"),
    ">2": ("2.00", None),
}


def review_azi_class(metadata):
    if not isinstance(metadata, dict) or set(metadata) != {
        "atlas_version", "event_id", "depth_class"
    }:
        raise AtlasClassBlocked("required edition, event and depth class only")
    if metadata["atlas_version"] != _VERSION:
        raise AtlasClassBlocked("edition not independently reviewed")
    if metadata["event_id"] != _EVENT:
        raise AtlasClassBlocked("wrong historical event identity")
    depth_class = metadata["depth_class"]
    if not isinstance(depth_class, str) or depth_class not in _CLASS_BOUNDS:
        raise AtlasClassBlocked("unknown or malformed 2021 depth class")
    lo, hi = _CLASS_BOUNDS[depth_class]
    return {
        "profile": "oc-ddt45-loing-2021-classified-depth-research-v0",
        "edition": _VERSION,
        "event": _EVENT,
        "published_class": depth_class,
        "lower_depth_class_boundary_m": lo,
        "upper_depth_class_boundary_m": hi,
        "open_ended_upper_class": hi is None,
        "class_edge_inclusion_from_legend_verified": False,
        "exact_observed_depth_m": None,
        "exact_reconstructed_depth_m": None,
        "meaning": "reconstructed_smoothed_and_vectorized_water_depth_class",
        "source_polygon_min_area_m2": 500,
        "source_original_GIS_bytes_attested": False,
        "asset_footprint_covered_by_source_established": False,
        "unmapped_location_proves_dry": False,
        "provider_reuse_rights_cleared": False,
        "valid_independent_2016_holdout": False,
        "model_input_admitted": False,
        "insured_loss_estimate_permitted": False,
    }


def _strict_keys(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise AtlasClassBlocked("duplicate JSON key")
        result[k] = v
    return result


def _reject_nonfinite(_):
    raise AtlasClassBlocked("nonfinite JSON number")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-json", required=True, type=Path)
    args = parser.parse_args()
    try:
        if not args.metadata_json.is_file() or args.metadata_json.stat().st_size > 4096:
            raise AtlasClassBlocked("bounded local metadata file required")
        metadata = json.loads(args.metadata_json.read_text(encoding="utf-8"),
                              object_pairs_hook=_strict_keys, parse_constant=_reject_nonfinite)
        result = review_azi_class(metadata)
    except (AtlasClassBlocked, OSError, UnicodeError, json.JSONDecodeError) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
