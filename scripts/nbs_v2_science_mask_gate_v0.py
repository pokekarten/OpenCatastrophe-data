# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed, offline NCEI Blended Sea Winds v2 cell provenance screen.

Only for the Science Quality *daily* stream, not NRT or six-hourly data.
The original provider mask must accompany wind fields. Mask code 6 is model
filling, not a satellite observation; all other presently unmapped codes stay
unresolved rather than becoming false observed-source labels.

Does not retrieve bytes, approve automation, clear data/API rights, or admit
scientific/model inputs. Use only after independent source/asset identity checks.
"""
from __future__ import annotations

import math
from typing import Any

FILL = -9999.0
DATASET_ID = "noaacwBlendedWindsDaily"


class NBSMaskGateError(ValueError):
    """Unsupported source identity or unsafe wind/mask semantics."""


def _number(value: Any, field: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise NBSMaskGateError(f"{field} must be finite numeric")
    return float(value)


def screen_science_daily_cell(record: Any) -> dict[str, Any]:
    """Classify one paired windspeed/mask cell without inventing observation truth.

    The input fields are already parsed/decoded synthetic or reviewed provider
    values. Does not parse netCDF, CRS or time axes; those need separate gates.
    """
    if type(record) is not dict:
        raise NBSMaskGateError("expected one cell record object")
    required = {
        "dataset_id": DATASET_ID,
        "product_version": "2.0",
        "stream": "science_quality",
        "cadence": "daily",
        "units": "m s-1",
    }
    for field, expected in required.items():
        if record.get(field) != expected:
            raise NBSMaskGateError(f"wrong or missing {field}")
    if "mask" not in record or "windspeed" not in record:
        raise NBSMaskGateError("wind field and provider mask must both be supplied")
    mask = _number(record["mask"], "mask")
    wind = _number(record["windspeed"], "windspeed")
    if mask != FILL and (not mask.is_integer() or mask < 0):
        raise NBSMaskGateError("unexpected nonintegral or negative mask code")
    if wind != FILL and wind < 0:
        raise NBSMaskGateError("negative non-fill windspeed")
    if wind == FILL or mask == FILL:
        category = "missing_fill_value"
        usable = False
    elif mask == 6:
        category = "model_filled"
        usable = True
    else:
        category = "mask_code_not_independently_reviewed"
        usable = True
    return {
        "dataset_id": DATASET_ID,
        "product_version": "2.0",
        "stream": "science_quality",
        "mask_code": int(mask) if mask != FILL else None,
        "wind_speed_m_s": wind if usable else None,
        "cell_provenance": category,
        "numeric_value_present": usable,
        "independent_observation_verified": False,
        "model_input_approved": False,
    }
