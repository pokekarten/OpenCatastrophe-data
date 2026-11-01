# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Geometry-free, read-only FEMA × NOAA Michael STAC envelope count gate.

No feature-level FEMA rows, geometry, image pixels or user/policy data.
Provider API replies are *caller supplied*, not independently authenticated.
This only tests candidate spatial coincidence; neither observed pixels,
same property identity nor scientific independence is established.
"""

from __future__ import annotations

import math
from typing import Any

from research_runners.noaa_michael_stac_preflight_v0 import preflight as stac_preflight
from research_runners.noaa_michael_alpha_tile_probe_v0 import (
    AlphaTileProofError, probe_zero_block,
)
from research_runners.noaa_michael_tiff_header_v0 import _table, _vals

SERVICE_ITEM = "e56e3d16fa144684bd532edbf298042c"
FEMA_LAYER = (
    "https://services.arcgis.com/XG15cJAlne2vxtgt/arcgis/rest/services/"
    "FEMA_Historical_Geospatial_Damage_Assessment_Database/FeatureServer/0/query"
)
COHORT_WHERE = "DIS_NUMBER = 'DR-4399' AND ASMT_TYPE = 'RS' AND DMG_TYPE = 'WI'"
EVENT_WHERE = "DIS_NUMBER = 'DR-4399'"
LEVELS = frozenset(("UNK", "DES", "MAJ", "MIN", "AFF", "NOD"))
MAX_ROWS = 6


class EnvelopeOverlapError(ValueError):
    """Provider counts, query scope or STAC source metadata are inconsistent."""


def build_queries(item: Any) -> dict[str, Any]:
    """Return exact query parameters; NEVER fetch or export feature geometry."""
    try:
        report = stac_preflight(item)
    except (ValueError, TypeError, KeyError) as exc:
        raise EnvelopeOverlapError("source STAC metadata must pass first") from exc
    bbox = item["bbox"]
    if not (type(bbox) is list and len(bbox) == 4 and all(
        type(x) in (float, int) and math.isfinite(x) for x in bbox
    )):
        raise EnvelopeOverlapError("invalid source tile bbox")
    geom = ",".join(str(x) for x in bbox)
    base = {
        "geometry": geom,
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "returnGeometry": "false",
        "f": "json",
    }
    return {
        "endpoint": FEMA_LAYER,
        "source_tile_id": report["tile_id"],
        "cohort_census": dict(base, where=COHORT_WHERE, returnCountOnly="true"),
        "damage_level_groups": dict(
            base, where=COHORT_WHERE, groupByFieldsForStatistics="DMG_LEVEL",
            outStatistics=(
                '[{"statisticType":"count","onStatisticField":"OBJECTID",'
                '"outStatisticFieldName":"n"}]'
            ),
        ),
        "disaster_census": dict(base, where=EVENT_WHERE, returnCountOnly="true"),
    }


def build_proven_transparent_block_query(
    item: Any, original_header: bytes, block_index: Any, compressed: bytes,
) -> dict[str, Any]:
    """Construct an exact geometry-free point census for a proven zero-alpha block.

    Pixels/georeference are from the original TIFF header, not a guessed STAC
    rectangle. No HTTP requests, individual source points or raster bytes
    are included in the returned plan.
    """
    try:
        proof = probe_zero_block(original_header, item, block_index, compressed)
    except (AlphaTileProofError, ValueError, TypeError, KeyError) as exc:
        raise EnvelopeOverlapError("original NOAA compressed raster block did not pass proof") from exc
    if not proof["block_all_alpha_pixels_transparent_proven"]:
        raise EnvelopeOverlapError("original raster block is not proven transparent")
    try:
        tags = _table(original_header)
        scale = _vals(original_header, tags, 33550, 12)
        tie = _vals(original_header, tags, 33922, 12)
    except (ValueError, TypeError, KeyError) as exc:
        raise EnvelopeOverlapError("original georeference could not be recovered") from exc
    row, col = proof["block_row"], proof["block_column"]
    width, height = item["assets"][item["id"]]["proj:shape"][1], item["assets"][item["id"]]["proj:shape"][0]
    px0, py0 = col * 512, row * 512
    px1, py1 = min(px0 + 512, width), min(py0 + 512, height)
    west = tie[3] + px0 * scale[0]
    east = tie[3] + px1 * scale[0]
    north = tie[4] - py0 * scale[1]
    south = tie[4] - py1 * scale[1]
    if not (-180 < west < east < 180 and -90 < south < north < 90):
        raise EnvelopeOverlapError("computed block envelope outside valid geographic coordinates")
    query = dict(build_queries(item)["cohort_census"])
    query["geometry"] = ",".join(format(v, ".17g") for v in (west, south, east, north))
    return {
        "profile": "noaa_fema_verified_zero_alpha_block_query_v0",
        "endpoint": FEMA_LAYER,
        "query": query,
        "original_raster_block_index": block_index,
        "original_deflate_block_sha256": proof["original_compressed_block_sha256"],
        "block_fully_transparent_proven": True,
        "no_source_image_or_fema_feature_bytes_returned": True,
        "independent_fema_label_source_proven": False,
        "model_input_admitted": False,
    }


def _count(reply: Any) -> int:
    if type(reply) is not dict or set(reply) != {"count"}:
        raise EnvelopeOverlapError("only geometry-free provider count response accepted")
    value = reply["count"]
    if type(value) is not int or not 0 <= value <= 2_000_000_000:
        raise EnvelopeOverlapError("provider count must be a bounded nonnegative integer")
    return value


def reconcile(item: Any, cohort_count: Any, damage_level_groups: Any,
              disaster_count: Any) -> dict[str, Any]:
    """Reconcile exact scoped 3-query responses with no feature details."""
    plan = build_queries(item)
    subset = _count(cohort_count)
    all_disaster = _count(disaster_count)
    if subset > all_disaster:
        raise EnvelopeOverlapError("cohort is larger than parent disaster count")
    if type(damage_level_groups) is not list or len(damage_level_groups) > MAX_ROWS:
        raise EnvelopeOverlapError("damage groups are missing or unbounded")
    levels = {}
    for row in damage_level_groups:
        if type(row) is not dict or set(row) != {"DMG_LEVEL", "n"}:
            raise EnvelopeOverlapError("unexpected group fields or individual data present")
        label = row["DMG_LEVEL"]
        n = row["n"]
        if label not in LEVELS or label in levels or type(n) is not int or not 0 < n <= 2_000_000_000:
            raise EnvelopeOverlapError("unknown, repeated or invalid damage-level group")
        levels[label] = n
    if sum(levels.values()) != subset:
        raise EnvelopeOverlapError("grouped source counts disagree with cohort census")
    # No per-structure data or source bbox is echoed; counts cannot identify
    # any overlap with alpha-covered pixels or assign a unique building.
    return {
        "profile": "noaa_fema_michael_envelope_overlap_v0",
        "noaa_stac_tile_id": plan["source_tile_id"],
        "fema_public_layer_service_item_id": SERVICE_ITEM,
        "exact_disaster_number": "DR-4399",
        "assessment_type": "RS",
        "damage_type": "WI",
        "damage_points_in_tile_envelope": subset,
        "all_disaster_points_in_tile_envelope": all_disaster,
        "damage_level_counts": {k: levels.get(k, 0) for k in ("NOD", "AFF", "MIN", "MAJ", "DES", "UNK")},
        "candidate_envelope_contains_assessment_point": subset > 0,
        "source_api_replies_authenticated": False,
        "original_raster_alpha_coverage_verified": False,
        "same_building_identity_proven": False,
        "source_image_fema_label_independence_proven": False,
        "per_feature_geometry_retrieved": False,
        "model_input_admitted": False,
    }
