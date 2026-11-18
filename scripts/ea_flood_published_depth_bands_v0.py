# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict, offline interpretation of official EA *published caption text* only.

This is NOT an adapter for actual WFS/OGC feature depth_band values. No raw
feature values have been admitted; lexical identity and interval boundary
semantics require provider asset/product documentation before any such join.
"""

from __future__ import annotations

import argparse
import json

# Exact prose captions from the EA's 2026 present-day and climate-change
# 3.3% AEP defended *dataset descriptions*. These are not observed WFS values.
CAPTION_BOUNDS_MM: dict[str, tuple[int | None, int | None]] = {
    "Up to 150mm": (None, 150),
    "150 – 300mm": (150, 300),
    "300 – 600mm": (300, 600),
    "600 – 900mm": (600, 900),
    "900 – 1200mm": (900, 1200),
    "1200 – 2300mm": (1200, 2300),
    "Over 2300mm": (2300, None),
}
MISSING_CAPTION = "Unavailable"


class DepthCaptionBlocked(ValueError):
    """Caption could not be interpreted without guessing."""


def inspect_published_caption(caption: str) -> dict[str, object]:
    """Describe publisher's caption conservatively; do not calculate a depth."""
    if type(caption) is not str:
        raise DepthCaptionBlocked("caption must be an exact published string")
    if caption == MISSING_CAPTION:
        status = "published_unavailable_marker"
        bounds: tuple[int | None, int | None] = (None, None)
    elif caption in CAPTION_BOUNDS_MM:
        status = "published_depth_interval_caption"
        bounds = CAPTION_BOUNDS_MM[caption]
    else:
        raise DepthCaptionBlocked("unknown caption or unverified actual feature label")
    return {
        "source": "Environment Agency 2026 river/sea defended 3.3% AEP published summary",
        "status": status,
        "published_caption": caption,
        "nominal_lower_boundary_mm": bounds[0],
        "nominal_upper_boundary_mm": bounds[1],
        "boundary_inclusivity_verified": False,
        "unbounded_side_does_not_mean_zero_depth": True,
        "unavailable_means_missing_not_zero": status == "published_unavailable_marker",
        "observed_actual_feature_label_verified": False,
        "safe_for_direct_feature_value_join": False,
        "representative_depth_mm": None,
        "building_depth_mm": None,
        "estimated_damage_ratio": None,
        "source_asset_rights_reviewed": False,
        "model_data_admitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--published-caption", required=True)
    args = parser.parse_args()
    try:
        result = inspect_published_caption(args.published_caption)
    except DepthCaptionBlocked as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
