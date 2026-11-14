# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline shape/CRS plausibility screen for one Dutch NBPW WFS geometry.

This is NOT a WFS downloader, GeoJSON-to-EPSG conversion, original-provider
receipt, flood-defence performance measurement, or CAT model admission.
Source: nl.ihw.nbpw.primary-flood-defence-trajectories.2026.
"""

from __future__ import annotations

import json
import math
from typing import Any

SOURCE_ID = "nl.ihw.nbpw.primary-flood-defence-trajectories.2026"
MAX_RESPONSE_BYTES = 131072
MAX_LINES = 256
MAX_VERTICES = 3000


class NbpwGeometryError(ValueError):
    """Reject a structurally or semantically ambiguous one-feature sample."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise NbpwGeometryError("duplicate JSON key")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise NbpwGeometryError("non-finite JSON constant")


def screen_nbpw_projected_multiline(original: bytes, *, declared_crs: str) -> dict[str, Any]:
    """Screen only one MultiLineString in declared RD New coordinates.

    Require explicit externally reviewed CRS. Range checks alone are NOT
    provenance or CRS verification. No input geometry is returned or stored.
    """
    if declared_crs != "EPSG:28992":
        raise NbpwGeometryError("source CRS must be independently declared EPSG:28992")
    if not isinstance(original, bytes) or not original or len(original) > MAX_RESPONSE_BYTES:
        raise NbpwGeometryError("original response missing or exceeds bounded byte ceiling")
    try:
        payload = json.loads(
            original.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise NbpwGeometryError("original response is not strict UTF-8 JSON") from exc
    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
        raise NbpwGeometryError("expected GeoJSON FeatureCollection object")
    features = payload.get("features")
    if not isinstance(features, list) or len(features) != 1:
        raise NbpwGeometryError("expected exactly one bounded feature")
    feature = features[0]
    if not isinstance(feature, dict) or feature.get("type") != "Feature":
        raise NbpwGeometryError("expected one GeoJSON Feature")
    if not isinstance(feature.get("properties"), dict):
        raise NbpwGeometryError("feature properties must be an object")
    geometry = feature.get("geometry")
    if not isinstance(geometry, dict) or geometry.get("type") != "MultiLineString":
        raise NbpwGeometryError("expected non-null MultiLineString geometry")
    lines = geometry.get("coordinates")
    if not isinstance(lines, list) or not 1 <= len(lines) <= MAX_LINES:
        raise NbpwGeometryError("invalid or unbounded line count")

    min_x = min_y = math.inf
    max_x = max_y = -math.inf
    vertices = 0
    for line in lines:
        if not isinstance(line, list) or len(line) < 2:
            raise NbpwGeometryError("each line must have at least two vertices")
        for point in line:
            if not isinstance(point, list) or len(point) != 2:
                raise NbpwGeometryError("only 2D coordinates supported")
            x, y = point
            if (
                type(x) not in (int, float)
                or type(y) not in (int, float)
                or not math.isfinite(x)
                or not math.isfinite(y)
            ):
                raise NbpwGeometryError("coordinate is nonnumeric, boolean or nonfinite")
            if not (0 <= x <= 300000 and 280000 <= y <= 650000):
                raise NbpwGeometryError("coordinate outside generous Netherlands RD New screening bounds")
            min_x, max_x = min(min_x, x), max(max_x, x)
            min_y, max_y = min(min_y, y), max(max_y, y)
            vertices += 1
            if vertices > MAX_VERTICES:
                raise NbpwGeometryError("too many vertices for bounded metadata-only screen")

    return {
        "source_id": SOURCE_ID,
        "declared_crs": declared_crs,
        "crs_verification": "range_plausibility_only",
        "lines": len(lines),
        "vertices": vertices,
        "bbox_rdnew": [min_x, min_y, max_x, max_y],
        "original_bytes": len(original),
        "rights_approved": False,
        "scientifically_validated": False,
        "model_admission": False,
    }
