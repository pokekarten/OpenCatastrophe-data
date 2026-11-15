# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict synthetic-only OPERA DSWx-S1 v1 water-class cross-layer preflight.

NASA/JPL D-108761 Rev A (2024-08-16), Table 4-1. Caller-supplied
small pixel windows only: no Earthdata requests, image files or source
admission. Count classifications without returning pixel values.
"""
from __future__ import annotations

from collections import Counter

PRODUCT = "OPERA_L3_DSWX-S1_V1"
PRODUCT_VERSION = "1.0"
MAX_PIXELS = 4096
MAX_SIDE = 128
WTR_TO_BWTR = {0: 0, 1: 1, 3: 1, 250: 250, 251: 251, 255: 255}
CLASS_NAMES = {
    0: "valid_not_water_not_dry_ground_proof",
    1: "open_water",
    3: "inundated_vegetation",
    250: "hand_masked_unsupported",
    251: "layover_shadow_masked_unsupported",
    255: "nodata_unsupported",
}


class DswxV1PreflightBlocked(ValueError):
    """The declared version or synthetic pixel sample cannot be trusted."""


def summarize_wtr_bwtr_v1(
    *, product: str, product_version: str, width: int, height: int,
    wtr: list[int], bwtr: list[int],
) -> dict[str, object]:
    """Validate exact v1 code pairs, never infer physical depth or event cause.

    The upstream producer must separately authenticate its original granule,
    georeferencing, sensing UTC, version and rights. This function cannot do so.
    """
    if product != PRODUCT or product_version != PRODUCT_VERSION:
        raise DswxV1PreflightBlocked("wrong OPERA product or version; never reuse old class encodings")
    if (type(width) is not int or type(height) is not int
            or not 1 <= width <= MAX_SIDE or not 1 <= height <= MAX_SIDE
            or width * height > MAX_PIXELS):
        raise DswxV1PreflightBlocked("invalid bounded caller-supplied pixel window")
    expected = width * height
    if (type(wtr) is not list or type(bwtr) is not list
            or len(wtr) != expected or len(bwtr) != expected):
        raise DswxV1PreflightBlocked("WTR/BWTR dimensions or input types inconsistent")
    counts: Counter[int] = Counter()
    for a, b in zip(wtr, bwtr):
        if (type(a) is not int or type(b) is not int or a not in WTR_TO_BWTR
                or b != WTR_TO_BWTR[a]):
            raise DswxV1PreflightBlocked(
                "unknown v1 class or inconsistent WTR-to-BWTR mapping"
            )
        counts[a] += 1
    if sum(counts.values()) != expected:
        raise DswxV1PreflightBlocked("classification count not conserved")
    by_class = {CLASS_NAMES[k]: counts[k] for k in WTR_TO_BWTR}
    valid_water = counts[1] + counts[3]
    valid_nonwater = counts[0]
    masked = counts[250] + counts[251] + counts[255]
    if valid_water + valid_nonwater + masked != expected:
        raise DswxV1PreflightBlocked("unsupported classes silently counted as valid observations")
    return {
        "schema_version": "nasa-opera-dswx-s1-v1-synthetic-class-preflight-v0",
        "declared_product_not_originally_attested": PRODUCT,
        "declared_product_version_not_originally_attested": PRODUCT_VERSION,
        "sample_pixel_count": expected,
        "water_classified_cells": valid_water,
        "not_water_classified_cells_not_dry_ground_proof": valid_nonwater,
        "masked_or_nodata_cells_excluded": masked,
        "valid_classified_cells": valid_water + valid_nonwater,
        "wtr_classes": by_class,
        "all_cell_counts_conserved": True,
        "source_granule_bytes_or_metadata_authenticated": False,
        "source_observation_time_verified": False,
        "source_geolocation_or_ancillary_masks_verified": False,
        "source_rights_or_commercial_use_approved": False,
        "baseline_water_change_or_flood_cause_inferred": False,
        "water_depth_or_return_period_inferred": False,
        "cat_model_input_admitted": False,
        "insurer_loss_or_property_exposure_inferred": False,
    }
