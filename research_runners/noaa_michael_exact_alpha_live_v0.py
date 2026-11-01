# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Optional bounded original NOAA TIFF alpha probe: two exact source blocks.

Never run from offline tests or import side effects. No original image bytes
are written to disk, Git or output; only derived numbers and hash receipts.
The live CLI is deliberately opt-in and its failure is NOT source admission.
"""

from __future__ import annotations

import hashlib
import json
import re
import urllib.request
import zlib
from typing import Any, Callable

from research_runners.noaa_michael_tiff_header_v0 import (
    _table, _vals, preflight as header_preflight,
)

SOURCE_ID = "20181011aC0853300w302100n"
ROOT = "https://coastalimagery.blob.core.windows.net/digitalcoast/HurricaneMichael_2018_8883/"
STAC_URL = ROOT + "stac/" + SOURCE_ID + ".json"
TIFF_URL = ROOT + SOURCE_ID + ".tif"
TARGETS = (324, 344)
BYTES_CAP = 1024 * 1024
CANONICAL_WIDTH = 9340
CANONICAL_HEIGHT = 9340
PATTERN = re.compile(r"^bytes (\d+)-(\d+)/(\d+)$")


class SourceAlphaProbeError(ValueError):
    """Original source bytes cannot support the proposed limited conclusion."""


def measure_alpha(
    encoded: bytes, *, valid_width: int = 512, valid_height: int = 512,
) -> dict[str, Any]:
    """Decode Deflate with Adler32 verification and TIFF Predictor=2 alpha.

    The four 8-bit channels are pixel-interleaved; predictor differences are
    reversed independently for each sample, at each row boundary. The alpha
    band is the fourth sample, as independently established from TIFF tags.
    """
    if (type(encoded) is not bytes or not 1 <= len(encoded) <= BYTES_CAP
        or type(valid_width) is not int or not 1 <= valid_width <= 512
        or type(valid_height) is not int or not 1 <= valid_height <= 512):
        raise SourceAlphaProbeError("invalid bounded original block bytes or valid pixel dimensions")
    try:
        decompressor = zlib.decompressobj()
        raw = decompressor.decompress(encoded, 512 * 512 * 4 + 1)
    except zlib.error as exc:
        raise SourceAlphaProbeError("original Deflate/Adler32 decode failed") from exc
    if (len(raw) != 512 * 512 * 4 or not decompressor.eof
        or decompressor.unused_data or decompressor.unconsumed_tail):
        raise SourceAlphaProbeError("original decoded raster is truncated, oversize, or has trailing bytes")
    zero = positive = opaque = 0
    min_col, max_col, min_row, max_row = 512, -1, 512, -1
    for row in range(valid_height):
        last_alpha = 0
        row_start = row * 512 * 4
        for col in range(512):
            last_alpha = (last_alpha + raw[row_start + col * 4 + 3]) & 255
            if col >= valid_width:
                continue
            if last_alpha == 0:
                zero += 1
            else:
                positive += 1
                opaque += last_alpha == 255
                min_col, max_col = min(min_col, col), max(max_col, col)
                min_row, max_row = min(min_row, row), max(max_row, row)
    if zero + positive != valid_width * valid_height:
        raise SourceAlphaProbeError("alpha pixel census inconsistent")
    return {
        "valid_pixels": valid_width * valid_height,
        "alpha_zero_pixels": zero,
        "alpha_nonzero_pixels": positive,
        "alpha_opaque_pixels": opaque,
        "nonzero_alpha_pixel_extent_xy_in_block": (
            [min_col, min_row, max_col, max_row] if positive else None
        ),
        "full_image_alpha_mask_verified": False,
        "source_damage_annotation_proven_independent": False,
        "fema_point_on_visible_pixel_proven": False,
        "model_input_admitted": False,
    }


def fetch_range(
    start: int, size: int, *, if_match: str | None = None,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> tuple[bytes, str | None, int]:
    """HTTP206 only, one original tile URL and exact byte limits.

    Detects a drifting ETag when supplied and refuses mismatched response
    Content-Range or byte lengths. A successful partial range is NOT a full
    file checksum. Opener injection allows fully offline synthetic tests.
    """
    if (type(start) is not int or type(size) is not int or not 0 <= start
        or not 1 <= size <= BYTES_CAP or start + size > 1_000_000_000):
        raise SourceAlphaProbeError("source request outside strict bounded byte range")
    headers = {
        "User-Agent": "OpenCatastropheData-SourceResearch/0.1 (metadata-only)",
        "Range": f"bytes={start}-{start + size - 1}",
        "Accept-Encoding": "identity",
    }
    if if_match is not None:
        # The original Azure CDN sometimes returns an opaque ASCII ETag
        # token without quotes. Preserve exact origin bytes; reject controls,
        # spaces, delimiters and any possibility of HTTP-header injection.
        if (type(if_match) is not str or not
            re.fullmatch(r'[A-Za-z0-9_./:"-]{1,200}', if_match)):
            raise SourceAlphaProbeError("untrusted source ETag")
        headers["If-Match"] = if_match
    request = urllib.request.Request(TIFF_URL, headers=headers, method="GET")
    try:
        with opener(request, timeout=20) as response:
            if response.getcode() != 206 or response.geturl() != TIFF_URL:
                raise SourceAlphaProbeError("source HTTP206/origin mismatch")
            match = PATTERN.fullmatch(response.headers.get("Content-Range", ""))
            if not match:
                raise SourceAlphaProbeError("original source Content-Range absent or malformed")
            from_byte, to_byte, total = map(int, match.groups())
            if (from_byte, to_byte) != (start, start + size - 1) or total < start + size:
                raise SourceAlphaProbeError("source byte scope or total length contradicts response")
            etag = response.headers.get("ETag")
            if if_match is not None and etag != if_match:
                raise SourceAlphaProbeError("source ETag changed between range requests")
            chunk = response.read(size + 1)
            if len(chunk) != size:
                raise SourceAlphaProbeError("original HTTP response byte size mismatch")
            return chunk, etag, total
    except SourceAlphaProbeError:
        raise
    except Exception as exc:
        raise SourceAlphaProbeError("NOAA original remote range inaccessible") from exc


def run_bounded_original_probe() -> dict[str, Any]:
    """Opt-in online original source audit; never called in test discovery."""
    request = urllib.request.Request(
        STAC_URL, headers={"User-Agent": "OpenCatastropheData-SourceResearch/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as resp:
            if resp.geturl() != STAC_URL or resp.getcode() != 200:
                raise SourceAlphaProbeError("STAC source URI or status drift")
            raw = resp.read(200_001)
    except Exception as exc:
        raise SourceAlphaProbeError("original NOAA STAC item inaccessible") from exc
    if len(raw) > 200_000:
        raise SourceAlphaProbeError("unbounded source STAC JSON")
    try:
        item = json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise SourceAlphaProbeError("source STAC JSON not parseable") from exc
    header, etag, total = fetch_range(0, 4096)
    identity = header_preflight(header, item)
    if identity["tile_id_from_stac_only"] != SOURCE_ID:
        raise SourceAlphaProbeError("original source TIFF id drift")
    tags = _table(header)
    if _vals(header, tags, 317, 3) != (2,) or _vals(header, tags, 338, 3) != (2,):
        raise SourceAlphaProbeError("TIFF predictor/straight-alpha sample profile drift")
    if [identity["raster_height_pixels"], identity["raster_width_pixels"]] != [
        CANONICAL_HEIGHT, CANONICAL_WIDTH,
    ]:
        raise SourceAlphaProbeError("original source tile shape drift")
    offsets, lengths = _vals(header, tags, 324, 4), _vals(header, tags, 325, 4)
    if total < identity["minimum_original_file_bytes_from_main_ifd"]:
        raise SourceAlphaProbeError("server total file length contradicts original TIFF IFD")
    reports = []
    for index in TARGETS:
        payload, next_etag, next_total = fetch_range(
            offsets[index], lengths[index], if_match=etag,
        )
        if next_total != total or (etag and next_etag != etag):
            raise SourceAlphaProbeError("original object size or ETag changed")
        row, col = divmod(index, 19)
        vw = min(512, CANONICAL_WIDTH - col * 512)
        vh = min(512, CANONICAL_HEIGHT - row * 512)
        report = measure_alpha(payload, valid_width=vw, valid_height=vh)
        reports.append({
            "original_tiff_block_index": index,
            "source_compressed_block_sha256": hashlib.sha256(payload).hexdigest(),
            "source_compressed_byte_count": lengths[index],
            "source_byte_range": [offsets[index], offsets[index] + lengths[index] - 1],
            **report,
        })
    return {
        "profile": "noaa_michael_live_two_source_block_alpha_v0",
        "original_source_id": SOURCE_ID,
        "original_first_ifd_sha256": hashlib.sha256(header).hexdigest(),
        "http206_reported_total_file_length": total,
        "source_etag_present": bool(etag),
        "full_original_asset_sha256_verified": False,
        "fema_point_alpha_pixel_intersection_verified": False,
        "original_asset_rights_admitted": False,
        "block_reports": reports,
        "model_input_admitted": False,
    }


def main() -> int:
    # JSON summary contains NO original source bytes or point coordinates.
    try:
        result = run_bounded_original_probe()
    except SourceAlphaProbeError as exc:
        print("NOAA_ORIGINAL_ALPHA_PROBE_BLOCKED: " + str(exc))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
