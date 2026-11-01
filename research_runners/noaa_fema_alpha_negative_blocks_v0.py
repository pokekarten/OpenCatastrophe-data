# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict NOAA alpha-negative x FEMA aggregate-only block evidence.

A FEMA point count in a proven all-transparent image block cannot validate
damage in that NOAA raster. This does NOT invalidate FEMA classifications,
identify a house, or establish coverage of neighbouring blocks. Caller-supplied
responses do not prove provider authenticity or boundary ownership.
"""

from __future__ import annotations

from typing import Any

from research_runners.noaa_michael_alpha_tile_probe_v0 import (
    AlphaTileProofError, probe_zero_block,
)
from research_runners.noaa_michael_tiff_header_v0 import (
    TIFFHeaderError, preflight as tiff_header_preflight,
)

REVIEWED_BLOCKS = tuple(row * 19 + col for row in (16, 17, 18) for col in range(4))
SOURCE_ITEM_ID = "20181011aC0853300w302100n"
MAX_COHORT = 23_682


class BlockCoverageEvidenceError(ValueError):
    """Fail closed on malformed counts, source identity or original bytes."""


def _count(reply: Any) -> int:
    if type(reply) is not dict or set(reply) != {"count"}:
        raise BlockCoverageEvidenceError("only source-style count-only responses are accepted")
    n = reply["count"]
    if type(n) is not int or not 0 <= n <= MAX_COHORT:
        raise BlockCoverageEvidenceError("FEMA aggregate count outside bounded cohort")
    return n


def reconcile_block_mask(
    item: Any, first_ifd_4096: bytes, parent_polygon_census: Any,
    block_polygon_censuses: Any, proven_original_deflate_blocks: Any,
) -> dict[str, Any]:
    """Reconcile exactly 12 block counts and optional audited original bytes.

    Each block census is only a {"count": integer} provider-style reply.
    Do not treat a nonzero decoded TIFF block as proven alpha-visible.
    """
    try:
        if type(first_ifd_4096) is not bytes:
            raise BlockCoverageEvidenceError("original source IFD must be bytes")
        metadata = tiff_header_preflight(first_ifd_4096, item)
    except (TIFFHeaderError, TypeError, ValueError, KeyError) as exc:
        raise BlockCoverageEvidenceError("source TIFF/STAC identity or shape invalid") from exc
    if metadata["tile_id_from_stac_only"] != SOURCE_ITEM_ID:
        raise BlockCoverageEvidenceError("source item differs from bounded Michael pilot")
    parent = _count(parent_polygon_census)
    if type(block_polygon_censuses) is not dict or set(block_polygon_censuses) != set(REVIEWED_BLOCKS):
        raise BlockCoverageEvidenceError("must supply exactly twelve scoped polygon count receipts")
    counts = {i: _count(block_polygon_censuses[i]) for i in REVIEWED_BLOCKS}
    if sum(counts.values()) != parent:
        raise BlockCoverageEvidenceError("12 source polygon counts disagree with parent census")
    if (type(proven_original_deflate_blocks) is not dict
        or not set(proven_original_deflate_blocks) <= set(REVIEWED_BLOCKS)):
        raise BlockCoverageEvidenceError("original compressed bytes outside audited block scope")
    verified_zero = []
    for i in REVIEWED_BLOCKS:
        if i not in proven_original_deflate_blocks:
            continue
        try:
            proof = probe_zero_block(
                first_ifd_4096, item, i, proven_original_deflate_blocks[i]
            )
        except AlphaTileProofError as exc:
            raise BlockCoverageEvidenceError("verified raster block bytes/IFD failed") from exc
        if proof["block_all_alpha_pixels_transparent_proven"]:
            verified_zero.append(i)
    negative = sum(counts[i] for i in verified_zero)
    return {
        "profile": "noaa_michael_fema_negative_alpha_polygon_block_v0",
        "source_tile_id": SOURCE_ITEM_ID,
        "fema_disaster_number": "DR-4399",
        "fema_assessment_method": "RS",
        "fema_damage_mechanism": "WI",
        "source_parent_polygon_aggregate_count": parent,
        "source_12_block_polygon_count_sum": sum(counts.values()),
        "source_pilot_block_count": len(REVIEWED_BLOCKS),
        "verified_fully_transparent_block_indices": verified_zero,
        "fema_aggregate_count_in_verified_transparent_blocks": negative,
        "fema_aggregate_count_in_not_proven_transparent_blocks": parent - negative,
        "transparent_blocks_excluded_from_noaa_image_damage_validation": True,
        "verified_nontransparent_alpha_under_any_fema_point": False,
        "feature_boundary_ownership_verified": False,
        "fema_count_responses_authenticated": False,
        "image_full_file_sha256_verified": False,
        "fema_source_label_independence_verified": False,
        "unique_building_identity_verified": False,
        "model_input_admitted": False,
    }
