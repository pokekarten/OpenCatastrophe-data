# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Conservative visible-alpha envelope count-only FEMA queries.

A source block may contain visible pixels in an irregular mask. Its enclosing
WGS84 rectangle is an *upper-bound geography* for positive-alpha pixels.
If an independent FEMA source point query returns zero in that rectangle,
there are no potential NOAA-visible point samples in the source block.
A positive reply does not prove a point lies on a nontransparent pixel.
No original image bytes or FEMA feature rows are exported.
"""

from __future__ import annotations

from typing import Any

from research_runners.noaa_fema_envelope_overlap_v0 import (
    COHORT_WHERE, FEMA_LAYER, EnvelopeOverlapError, _count,
    _polygon_from_bbox,
)
from research_runners.noaa_michael_exact_alpha_live_v0 import (
    SourceAlphaProbeError, measure_alpha, SOURCE_ID,
)
from research_runners.noaa_michael_tiff_header_v0 import (
    TIFFHeaderError, _table, _vals, preflight as header_preflight,
)


class AlphaPolygonError(ValueError):
    """Invalid source image identity, pixel mask or scoped provider count."""


def original_alpha_enclosing_polygon_query(
    stac_item: Any, original_header: Any, block_index: Any, original_deflate: Any,
) -> dict[str, Any]:
    """Return source-pixel-inclusive *bounding polygon* and strict count query."""
    if type(original_header) is not bytes or len(original_header) != 4096:
        raise AlphaPolygonError("original TIFF 4KiB metadata absent")
    try:
        tiff = header_preflight(original_header, stac_item)
    except (TIFFHeaderError, TypeError, ValueError, KeyError) as exc:
        raise AlphaPolygonError("original TIFF or STAC identity failed") from exc
    if tiff["tile_id_from_stac_only"] != SOURCE_ID:
        raise AlphaPolygonError("unreviewed source asset or STAC item")
    if type(block_index) is not int or block_index not in (324, 344):
        raise AlphaPolygonError("block outside two selected unresolved pilot scopes")
    tags = _table(original_header)
    if _vals(original_header, tags, 317, 3) != (2,) or _vals(original_header, tags, 338, 3) != (2,):
        raise AlphaPolygonError("TIFF predictor or alpha band changed")
    lengths = _vals(original_header, tags, 325, 4)
    if type(original_deflate) is not bytes or len(original_deflate) != lengths[block_index]:
        raise AlphaPolygonError("original byte count does not match TIFF IFD")
    row, col = divmod(block_index, 19)
    valid_width = min(512, tiff["raster_width_pixels"] - col * 512)
    valid_height = min(512, tiff["raster_height_pixels"] - row * 512)
    try:
        decoded = measure_alpha(original_deflate, valid_width=valid_width, valid_height=valid_height)
    except SourceAlphaProbeError as exc:
        raise AlphaPolygonError("original Deflate/Adler32 and alpha decoding blocked") from exc
    bbox = decoded["nonzero_alpha_pixel_extent_xy_in_block"]
    if bbox is None:
        raise AlphaPolygonError("no alpha-positive pixels; whole block is excluded")
    x0, y0, x1, y1 = bbox
    sx, sy, sz = _vals(original_header, tags, 33550, 12)
    px, py, pz, geo_x, geo_y, gz = _vals(original_header, tags, 33922, 12)
    west = geo_x + (col * 512 + x0) * sx
    east = geo_x + (col * 512 + x1 + 1) * sx
    north = geo_y - (row * 512 + y0) * sy
    south = geo_y - (row * 512 + y1 + 1) * sy
    try:
        ring = _polygon_from_bbox([west, south, east, north])
    except EnvelopeOverlapError as exc:
        raise AlphaPolygonError("source-image alpha enclosing polygon invalid") from exc
    query = {
        "where": COHORT_WHERE,
        "geometry": ring,
        "geometryType": "esriGeometryPolygon",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "returnCountOnly": "true",
        "returnGeometry": "false",
        "f": "json",
    }
    return {
        "profile": "noaa_michael_visible_alpha_enclosing_fema_polygon_v0",
        "source_tile_id": SOURCE_ID,
        "source_block_index": block_index,
        "source_alpha_positive_pixels": decoded["alpha_nonzero_pixels"],
        "source_alpha_zero_pixels": decoded["alpha_zero_pixels"],
        "source_alpha_pixel_bbox": bbox,
        "fema_query_endpoint": FEMA_LAYER,
        "fema_count_query": query,
        "polygon_encloses_all_visible_pixels_not_exact_mask": True,
        "positive_count_proves_pixel_visible": False,
        "fema_point_coordinates_retrieved": False,
        "source_original_bytes_authenticated_outside_caller": False,
        "model_input_admitted": False,
    }


def reconcile_counts(block_reply: Any, visible_bbox_reply: Any) -> dict[str, Any]:
    """Document an aggregate exclusion when candidate visible-area bbox count is zero."""
    try:
        block = _count(block_reply)
        candidate = _count(visible_bbox_reply)
    except EnvelopeOverlapError as exc:
        raise AlphaPolygonError("invalid provider-style count reply") from exc
    if block > 23_682 or candidate > block:
        raise AlphaPolygonError("visible alpha bbox cannot exceed scoped parent count")
    return {
        "source_block_fema_polygon_count": block,
        "conservative_alpha_bbox_fema_polygon_count": candidate,
        "counts_outside_alpha_enclosing_bbox": block - candidate,
        "candidate_count_does_not_establish_pixel_visible": True,
        "original_source_fema_label_independence_proven": False,
        "per_feature_coordinates_retrieved": False,
        "model_input_admitted": False,
    }
