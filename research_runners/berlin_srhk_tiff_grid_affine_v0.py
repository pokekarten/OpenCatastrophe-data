# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline fail-closed TIFF header affine-grid evidence for Berlin SRHK depth.

Only an independently authenticated bounded TIFF *prefix* is accepted. This
parses uncompressed metadata, never TIFF pixel blocks or ZIP members. A
complete GeoTIFF scale/tiepoint, CRS, raster convention and dimensions may
establish header-only projected bounds, not genuine depth, NoData or losses.
"""
from __future__ import annotations

import math
import struct

MAX_PREFIX_BYTES = 1_048_576
MAX_IFD_ENTRIES = 512
MAX_RASTER_AXIS = 250_000
# Existing fixed 200 x 200 m Berlin ALKIS building sample bbox, EPSG:25833.
PILOT_BBOX = (391700.0, 5819950.0, 391900.0, 5820150.0)


class BerlinTiffGridError(ValueError):
    """Contradictory, unsupported, or unsafe TIFF spatial metadata."""


def _read_tag(raw: bytes, order: str, value: tuple[int, int, int, int], *, tag: int,
              expected_type: int, expected_count: int) -> bytes | None:
    dtype, count, value_field, field_value = value
    if dtype != expected_type or count != expected_count:
        raise BerlinTiffGridError(f"unsupported tag {tag} metadata encoding")
    nbytes = count * {3: 2, 4: 4, 12: 8}[dtype]
    if nbytes <= 4:
        return raw[value_field:value_field+nbytes]
    offset = field_value
    if offset < 8:
        raise BerlinTiffGridError(f"unsafe tag {tag} offset")
    if offset + nbytes > len(raw):
        return None  # Header-only research: absence is UNKNOWN, not false/zero.
    return raw[offset:offset+nbytes]


def inspect_berlin_tiff_header_grid(raw: bytes) -> dict:
    """Inspect metadata from a validated/decompressed source TIFF prefix only.

    Does not prove the prefix belongs to an original object; caller must bind
    to the exact provider range receipt and its TIFF member integrity gates.
    """
    if type(raw) is not bytes or not 8 <= len(raw) <= MAX_PREFIX_BYTES:
        raise BerlinTiffGridError("unreviewed TIFF prefix length or type")
    if raw[:4] not in (b"II*\x00", b"MM\x00*"):
        raise BerlinTiffGridError("only classic TIFF header accepted for affine audit")
    order = "<" if raw[:2] == b"II" else ">"
    ifd = struct.unpack_from(order + "I", raw, 4)[0]
    if ifd < 8:
        raise BerlinTiffGridError("invalid first IFD offset")
    out = {
        "header_only_georeferencing_verified": False,
        "header_declared_crs_epsg": None,
        "header_raster_width_pixels": None,
        "header_raster_height_pixels": None,
        "header_pixel_size_m": None,
        "header_projected_bbox_epsg25833_m": None,
        "pilot_bbox_intersects_header_raster_extent": None,
        "header_covers_entire_pilot_bbox": None,
        "original_tiff_pixels_sampled": False,
        "original_depth_units_or_nodata_verified": False,
        "raster_overlaps_real_source_footprints_verified": False,
        "actual_flood_exposure_admitted": False,
    }
    if ifd + 2 > len(raw):
        return out
    count = struct.unpack_from(order + "H", raw, ifd)[0]
    if count > MAX_IFD_ENTRIES:
        raise BerlinTiffGridError("excessive TIFF IFD count")
    if ifd + 2 + 12*count + 4 > len(raw):
        return out
    tags: dict[int, tuple[int, int, int, int]] = {}
    for i in range(count):
        where = ifd + 2 + 12*i
        tag, dtype, n, field_val = struct.unpack_from(order + "HHII", raw, where)
        if tag in (256, 257, 274, 33550, 33922, 34264, 34735):
            if tag in tags:
                raise BerlinTiffGridError("duplicate critical TIFF metadata tag")
            tags[tag] = (dtype, n, where+8, field_val)
    if 34264 in tags:
        raise BerlinTiffGridError("ModelTransformationTag requires separate rotated-grid review")

    def value(tag: int, dtype: int, num: int):
        entry = tags.get(tag)
        if entry is None:
            return None
        return _read_tag(raw, order, entry, tag=tag, expected_type=dtype,
                         expected_count=num)

    dims = []
    for tag in (256, 257):
        entry = tags.get(tag)
        if entry is None:
            dims.append(None)
            continue
        dtype = entry[0]
        if dtype not in (3, 4):
            raise BerlinTiffGridError("unreviewed TIFF image dimensions type")
        item = value(tag, dtype, 1)
        if item is None:
            dims.append(None)
            continue
        n = struct.unpack(order + ("H" if dtype == 3 else "I"), item)[0]
        if not 1 <= n <= MAX_RASTER_AXIS:
            raise BerlinTiffGridError("raster axis exceeds reviewed bounds")
        dims.append(n)
    width, height = dims
    out["header_raster_width_pixels"] = width
    out["header_raster_height_pixels"] = height
    if width and height and width * height > 10_000_000_000:
        raise BerlinTiffGridError("unreviewed raster pixel count")
    orientation = tags.get(274)
    if orientation:
        orient = value(274, 3, 1)
        if orient is not None and struct.unpack(order+"H", orient)[0] != 1:
            raise BerlinTiffGridError("nonstandard TIFF orientation needs review")

    keys: dict[int, int] = {}
    geo = tags.get(34735)
    if geo:
        if geo[0] != 3 or not 4 <= geo[1] <= 2048 or geo[1] % 4:
            raise BerlinTiffGridError("invalid GeoKeyDirectory encoding")
        nbytes = geo[1]*2
        if nbytes <= 4:
            raw_keys = raw[geo[2]:geo[2]+nbytes]
        elif geo[3] < 8:
            raise BerlinTiffGridError("invalid GeoKeyDirectory pointer")
        elif geo[3]+nbytes > len(raw):
            raw_keys = None
        else:
            raw_keys = raw[geo[3]:geo[3]+nbytes]
        if raw_keys is not None:
            vals = struct.unpack(order+str(geo[1])+"H", raw_keys)
            ver, revision, minor, nkeys = vals[:4]
            if (ver != 1 or revision > 10 or minor > 10 or nkeys > 500
                    or 4 + nkeys*4 != len(vals)):
                raise BerlinTiffGridError("invalid GeoKeyDirectory size or version")
            seen = set()
            for j in range(nkeys):
                key, tag_loc, kcount, kval = vals[4+4*j:8+4*j]
                if key in seen:
                    raise BerlinTiffGridError("duplicate GeoKey")
                seen.add(key)
                if key in (1024, 1025, 3072):
                    if tag_loc != 0 or kcount != 1:
                        raise BerlinTiffGridError("indirect critical GeoKey unsupported")
                    keys[key] = kval
    crs = keys.get(3072)
    out["header_declared_crs_epsg"] = crs
    if crs is not None and crs != 25833:
        raise BerlinTiffGridError("raster projected CRS not Berlin pilot EPSG:25833")
    if keys.get(1024) not in (None, 1):
        raise BerlinTiffGridError("GeoTIFF model is not projected")
    if keys.get(1025) not in (None, 1):
        raise BerlinTiffGridError("PixelIsPoint grid requires separate half-pixel review")

    scale_data = value(33550, 12, 3)
    tie_data = value(33922, 12, 6)
    if scale_data is None or tie_data is None:
        return out
    sx, sy, sz = struct.unpack(order+"3d", scale_data)
    i, j, k, x, y, z = struct.unpack(order+"6d", tie_data)
    if (not all(math.isfinite(v) for v in (sx, sy, sz, i, j, k, x, y, z))
            or not 0.01 <= sx <= 500 or not 0.01 <= sy <= 500 or abs(k) > 1e-8):
        raise BerlinTiffGridError("unsafe or non-finite affine pixel scale or tiepoint")
    out["header_pixel_size_m"] = [sx, sy]
    if not (width and height and keys.get(1024) == 1 and keys.get(1025) == 1 and crs == 25833):
        return out  # No silent default assumption of pixel registration or CRS.
    xmin, ymax = x-i*sx, y+j*sy
    xmax, ymin = xmin + width*sx, ymax - height*sy
    if not all(math.isfinite(v) for v in (xmin, ymin, xmax, ymax)):
        raise BerlinTiffGridError("invalid projected raster bounds")
    out["header_projected_bbox_epsg25833_m"] = [xmin, ymin, xmax, ymax]
    a,b,c,d = PILOT_BBOX
    out["pilot_bbox_intersects_header_raster_extent"] = (
        xmax > a and xmin < c and ymax > b and ymin < d
    )
    out["header_covers_entire_pilot_bbox"] = (
        xmin <= a and ymin <= b and xmax >= c and ymax >= d
    )
    out["header_only_georeferencing_verified"] = True
    return out
