# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline-only, strictly bounded GSW v1.5 occurrence TIFF-header preflight.

Never issues requests, decodes source tiles, claims provider identity from bytes,
or promotes source pixels to CAT model inputs. Input is separately obtained,
reviewed *prefix* bytes only. A TIFF header does NOT identify the post-
2026-11-10 corrected original asset or prove its full-file checksum.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

SOURCE_ID = "ec-jrc.global-surface-water.1984-2024"
SOURCE_URL = (
    "https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/"
    "download2024/Aggregated/VER1-5/occurrence/"
    "occurrence_10E_50N_v1_5_2024.tif"
)
PREFIX_BYTES = 4096
MAX_IFD_ENTRIES = 256
MAX_DECODED_PIXEL_COUNT = 65536

# Only trusted TIFF first-IFD *inline scalar* tags. A 4096-byte header sample
# may not contain the GeoKey or tile arrays and therefore cannot prove CRS,
# raster grid, nodata tag or physical pixel values.
SCALARS = {
    256: "width_if_inline",
    257: "height_if_inline",
    258: "bits_per_sample_if_inline",
    259: "compression_if_inline",
    262: "photometric_if_inline",
    277: "samples_per_pixel_if_inline",
    322: "tile_width_if_inline",
    323: "tile_height_if_inline",
    339: "sample_format_if_inline",
}
GEO_TAGS = {33550, 33922, 34264, 34735, 34736, 34737, 42113}

# TIFF 6.0 architectural fields have tag-specific types, not any scalar.
# A malformed LONG-valued BitsPerSample=8 or SamplesPerPixel=1 must NOT
# support a positive 8-bit, single-band claim. Width/height and tiles also
# accept BigTIFF LONG8 when the header is explicitly BigTIFF.
FIELD_DTYPES = {
    256: frozenset((3, 4, 16)),
    257: frozenset((3, 4, 16)),
    258: frozenset((3,)),
    259: frozenset((3,)),
    262: frozenset((3,)),
    277: frozenset((3,)),
    322: frozenset((3, 4, 16)),
    323: frozenset((3, 4, 16)),
    339: frozenset((3,)),
}


class JRCHeaderBlocked(ValueError):
    """Missing, malformed or scientifically unjustified original evidence."""


def _read_integer(raw: bytes, endian: str, pos: int, size: int) -> int:
    if pos < 0 or size <= 0 or pos + size > len(raw):
        raise JRCHeaderBlocked("TIFF value falls outside bounded prefix")
    return int.from_bytes(raw[pos:pos + size],
                          byteorder="little" if endian == "<" else "big")


def inspect_tiff_prefix(raw: bytes) -> dict[str, object]:
    """Inspect exactly 4 KiB and preserve the distinction prefix vs whole TIFF."""
    if type(raw) is not bytes or len(raw) != PREFIX_BYTES:
        raise JRCHeaderBlocked("exactly 4096 externally supplied TIFF-prefix bytes required")
    if raw[:2] not in (b"II", b"MM"):
        raise JRCHeaderBlocked("invalid TIFF byte order")
    endian = "<" if raw[:2] == b"II" else ">"
    if raw[2:4] == (b"*\x00" if endian == "<" else b"\x00*"):
        big = False
        first_ifd = _read_integer(raw, endian, 4, 4)
        minimum_offset, count_bytes, entry_bytes, value_bytes = 8, 2, 12, 4
    elif raw[2:4] == (b"+\x00" if endian == "<" else b"\x00+"):
        big = True
        if _read_integer(raw, endian, 4, 2) != 8 or _read_integer(raw, endian, 6, 2) != 0:
            raise JRCHeaderBlocked("invalid BigTIFF word size or reserved field")
        first_ifd = _read_integer(raw, endian, 8, 8)
        minimum_offset, count_bytes, entry_bytes, value_bytes = 16, 8, 20, 8
    else:
        raise JRCHeaderBlocked("not TIFF/BigTIFF")
    # Classic TIFF requires word alignment; BigTIFF requires 8-byte
    # alignment for directory/value offsets (libtiff BigTIFF design).
    if first_ifd < minimum_offset or first_ifd % (8 if big else 2):
        raise JRCHeaderBlocked("invalid or unaligned first TIFF IFD pointer")

    # A first IFD outside a bounded prefix is inconclusive, not source proof.
    seen_tags: set[int] = set()
    shape: dict[str, int] = {}
    if first_ifd + count_bytes > len(raw):
        count: int | None = None
        directory_visible = False
    else:
        count = _read_integer(raw, endian, first_ifd, count_bytes)
        if count > MAX_IFD_ENTRIES:
            raise JRCHeaderBlocked("implausibly large first TIFF IFD entry count")
        # A complete TIFF IFD also contains its terminal next-IFD pointer
        # (4 bytes classic / 8 bytes BigTIFF). Without it, only entry
        # records may be visible, so the directory remains inconclusive.
        next_ifd_bytes = 8 if big else 4
        directory_visible = (
            first_ifd + count_bytes + count * entry_bytes + next_ifd_bytes
            <= len(raw)
        )
        if directory_visible:
            for n in range(count):
                off = first_ifd + count_bytes + n * entry_bytes
                tag = _read_integer(raw, endian, off, 2)
                dtype = _read_integer(raw, endian, off + 2, 2)
                items = _read_integer(raw, endian, off + 4, 8 if big else 4)
                if tag in seen_tags:
                    raise JRCHeaderBlocked("duplicate TIFF first IFD tag")
                seen_tags.add(tag)
                if tag not in SCALARS or items != 1:
                    continue
                if dtype not in FIELD_DTYPES[tag] or (dtype == 16 and not big):
                    continue  # Invalid tag-specific TIFF type: no shape claim.
                scalar_size = {3: 2, 4: 4, 16: 8 if big else 0}.get(dtype, 0)
                if scalar_size == 0 or scalar_size > value_bytes:
                    continue  # Not an inline scalar of a supported type.
                value = _read_integer(
                    raw, endian, off + (12 if big else 8), scalar_size
                )
                if tag in (256, 257, 258, 277, 322, 323) and value == 0:
                    raise JRCHeaderBlocked("invalid zero-valued TIFF dimension/band tag")
                if tag in (256, 257) and value > 200_000:
                    raise JRCHeaderBlocked("implausible TIFF dimension")
                shape[SCALARS[tag]] = value
    # Header dimensions alone are not an authenticated geographical tile,
    # nor do they prove compressed raster values or corrected publication.
    return {
        "profile": "jrc-gsw-v15-occurrence-offline-tiff-prefix-v0",
        "source_id": SOURCE_ID,
        "fixed_candidate_original_url": SOURCE_URL,
        "original_prefix_bytes": len(raw),
        "external_prefix_sha256": hashlib.sha256(raw).hexdigest(),
        "tiff_flavour": "BigTIFF" if big else "TIFF",
        "byte_order": "little" if endian == "<" else "big",
        "first_ifd_offset": first_ifd,
        "first_ifd_entry_count_if_visible": count,
        "first_ifd_fully_within_prefix": directory_visible,
        "geotiff_tag_ids_if_visible": sorted(seen_tags & GEO_TAGS),
        **{name: shape.get(name) for name in SCALARS.values()},
        "expected_10_degree_tile_40000x40000_if_inline": (
            shape.get("width_if_inline") == 40000
            and shape.get("height_if_inline") == 40000
        ),
        "single_8bit_band_if_inline": (
            shape.get("bits_per_sample_if_inline") == 8
            and shape.get("samples_per_pixel_if_inline") == 1
        ),
        "original_provider_source_identity_verified": False,
        "whole_original_tiff_sha256_verified": False,
        "post_2026_11_10_correction_verified": False,
        "geospatial_crs_and_affine_verified": False,
        "decoded_original_pixels_verified": False,
        "source_downloaded_by_preflight": False,
        "external_source_bytes_persisted_by_preflight": False,
        "model_input_approved": False,
    }


def validate_decoded_occurrence_values(values: bytes) -> dict[str, object]:
    """Check a separately decoded bounded byte raster window, *not* a TIFF blob.

    0..100 encode percentages (0: observed not water), 255 marks no data
    in the JRC/FAO Occurrence metadata. 101..254 are invalid for this layer.
    Do not call this on compressed TIFF bytes or other JRC product types.
    """
    if (type(values) is not bytes or not values
            or len(values) > MAX_DECODED_PIXEL_COUNT):
        raise JRCHeaderBlocked("decoded occurrence window must contain 1..65536 uint8 values")
    invalid = sorted(set(v for v in values if 100 < v < 255))
    if invalid:
        raise JRCHeaderBlocked("occurrence window has out-of-range non-NoData percentage values")
    measured = [v for v in values if v != 255]
    return {
        "profile": "jrc-gsw-occurrence-offline-decoded-value-gate-v0",
        "decoded_pixel_count": len(values),
        "nodata_255_count": len(values) - len(measured),
        "observed_zero_not_water_count": measured.count(0),
        "observed_percent_min": min(measured) if measured else None,
        "observed_percent_max": max(measured) if measured else None,
        "original_provider_source_identity_verified": False,
        "post_2026_11_10_correction_verified": False,
        "model_input_approved": False,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--offline-tiff-prefix-file", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        if args.offline_tiff_prefix_file.stat().st_size != PREFIX_BYTES:
            raise JRCHeaderBlocked("only exact 4096-byte TIFF prefix file permitted")
        result = inspect_tiff_prefix(args.offline_tiff_prefix_file.read_bytes())
    except (OSError, JRCHeaderBlocked) as exc:
        p.exit(2, f"BLOCKED: {exc}\n")
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
