# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline single original Deflate TIFF tile proof: all-zero alpha only.

Only one locally supplied compressed tile and the first 4096 bytes of its TIFF
may be used. This is NOT a full-image coverage analysis or FEMA property match.
A nonzero compressed tile is deliberately *not* treated as alpha-visible:
TIFF Predictor/ExtraSamples and imagery provenance require further review.
"""

from __future__ import annotations

import hashlib
import zlib
from typing import Any

from research_runners.noaa_michael_tiff_header_v0 import (
    TIFFHeaderError, _table, _vals, preflight as tiff_header_preflight,
)

MAX_BLOCK_BYTES = 1_000_000
DECODED_BLOCK_BYTES = 512 * 512 * 4
MAX_ORIGINAL_BYTES = 4096


class AlphaTileProofError(ValueError):
    """Unmatched or unsafe source tile byte range."""


def probe_zero_block(header: Any, item: Any, tile_index: Any,
                     compressed: Any) -> dict[str, Any]:
    """Verify a *single* source TIFF block is entirely zero, or stay unknown.

    Callers must retain the original HTTP Range and item URLs outside the
    output, and must not describe an internal transparent block as proof
    of zero FEMA points or full raster image coverage.
    """
    try:
        if type(header) is not bytes or len(header) != MAX_ORIGINAL_BYTES:
            raise AlphaTileProofError("exact 4 KiB original TIFF header required")
        metadata = tiff_header_preflight(header, item)
        tags = _table(header)
        offsets = _vals(header, tags, 324, 4)
        sizes = _vals(header, tags, 325, 4)
        if type(tile_index) is not int or not 0 <= tile_index < len(offsets):
            raise AlphaTileProofError("tile index out of range or not an integer")
        expected = sizes[tile_index]
        if not 1 <= expected <= MAX_BLOCK_BYTES:
            raise AlphaTileProofError("source tile compressed size exceeds bounded probe")
        if type(compressed) is not bytes or len(compressed) != expected:
            raise AlphaTileProofError("compressed bytes must match exact source TIFF IFD byte count")
        if offsets[tile_index] < 4096:
            raise AlphaTileProofError("tile offset overlaps original TIFF header")

        # TIFF tag 317 marks horizontal prediction; for entirely zero
        # decompressed bytes, the horizontal predictor preserves zero.
        # Do NOT infer actual positive alpha when byte values are nonzero.
        try:
            dec = zlib.decompressobj()
            decoded = dec.decompress(compressed, DECODED_BLOCK_BYTES + 1)
            # A completed zlib stream needs no unbounded flush. A stream
            # exceeding the cap must fail without expanding remaining bytes.
        except zlib.error as exc:
            raise AlphaTileProofError("malformed original Deflate raster tile") from exc
        if (len(decoded) != DECODED_BLOCK_BYTES or not dec.eof
            or dec.unused_data or dec.unconsumed_tail):
            raise AlphaTileProofError("compressed tile has truncated, excess or mis-sized raster content")
        fully_zero = not any(decoded)
        tile_width = (metadata["raster_width_pixels"] + 511) // 512
        row, col = divmod(tile_index, tile_width)
        valid_width = min(512, metadata["raster_width_pixels"] - col * 512)
        valid_height = min(512, metadata["raster_height_pixels"] - row * 512)
        if min(valid_width, valid_height) <= 0:
            raise AlphaTileProofError("index does not refer to actual image pixels")
        return {
            "profile": "noaa_michael_2018_single_alpha_zero_deflate_tile_v0",
            "source_tile_id": metadata["tile_id_from_stac_only"],
            "original_tiff_block_index": tile_index,
            "block_row": row,
            "block_column": col,
            "original_compressed_byte_offset": offsets[tile_index],
            "original_compressed_byte_count": expected,
            "original_compressed_block_sha256": hashlib.sha256(compressed).hexdigest(),
            "original_block_deflate_decoded": True,
            "decoded_block_all_channels_zero": fully_zero,
            "block_all_alpha_pixels_transparent_proven": fully_zero,
            "proven_transparent_pixels_in_this_block_only": (
                valid_width * valid_height if fully_zero else 0
            ),
            "original_full_file_hash_verified": False,
            "other_raster_blocks_covered": False,
            "whole_image_alpha_coverage_measured": False,
            "source_image_fema_label_independence_proven": False,
            "fema_point_pixel_intersection_proven": False,
            "model_input_admitted": False,
        }
    except TIFFHeaderError as exc:
        raise AlphaTileProofError("source TIFF header cannot be trusted") from exc
