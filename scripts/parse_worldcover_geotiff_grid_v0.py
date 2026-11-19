# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read only bounded GeoTIFF georeferencing metadata in a fixed 4 KiB prefix.

No filesystem, provider access, TIFF pixels, arbitrary dereferencing or
external byte persistence. A complete, internally consistent GeoKey and
pixel scale/tiepoint may establish a HEADER-ONLY declared spatial grid,
not full GeoTIFF/COG or science model admission.
"""
from __future__ import annotations

import math
import struct

SAMPLE_BYTES = 4096
MAX_FIRST_IFD_ENTRIES = 256
MAX_TAG_ITEMS = 256
MODEL_PIXEL_SCALE = 33550
MODEL_TIEPOINT = 33922
MODEL_TRANSFORM = 34264
GEO_KEY_DIRECTORY = 34735
SOURCE_TILE_BOUNDS = (9.0, 48.0, 12.0, 51.0)  # N48E009, lon-min, lat-min, lon-max, lat-max.


class GeoGridBlocked(ValueError):
    """Malformed, contradictory or unsafe geospatial header metadata."""


def _tag_data(
    raw: bytes, entry: tuple[int, int, int, int], *,
    value_width: int, endian: str,
) -> bytes | None:
    tag, dtype, count, offset = entry
    type_width = {3: 2, 12: 8}.get(dtype)
    if type_width is None or not 0 < count <= MAX_TAG_ITEMS:
        raise GeoGridBlocked("unsupported or excessive GeoTIFF tag type/count")
    length = count * type_width
    if length <= value_width:
        return raw[offset: offset + length]
    address = struct.unpack_from(endian + ("I" if value_width == 4 else "Q"), raw, offset)[0]
    if address < 8 or address > len(raw) or length > len(raw) - address:
        return None
    return raw[address:address + length]


def inspect_geotiff_grid(raw: bytes, *, width: int | None, height: int | None) -> dict:
    """Parse in-range TIFF geo tags; report only header-derived bounded facts."""
    if type(raw) is not bytes or len(raw) != SAMPLE_BYTES:
        raise GeoGridBlocked("requires exact reviewed 4096-byte original TIFF prefix")
    magic = raw[:4]
    if magic not in (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"):
        raise GeoGridBlocked("invalid TIFF magic")
    endian = "<" if magic[:2] == b"II" else ">"
    big = magic[2] == 43 if endian == "<" else magic[3] == 43
    if big:
        offset_size, reserved = struct.unpack_from(endian + "HH", raw, 4)
        if offset_size != 8 or reserved:
            raise GeoGridBlocked("malformed BigTIFF offset header")
        first_ifd = struct.unpack_from(endian + "Q", raw, 8)[0]
        count_width, entry_size, value_width, min_ifd = 8, 20, 8, 16
    else:
        first_ifd = struct.unpack_from(endian + "I", raw, 4)[0]
        count_width, entry_size, value_width, min_ifd = 2, 12, 4, 8

    empty = {
        "pixel_scale_degrees_if_complete": None,
        "tiepoint_raster_and_wgs84_if_complete": None,
        "geokey_model_type_if_complete": None,
        "geokey_raster_type_if_complete": None,
        "geokey_geographic_crs_if_complete": None,
        "header_tile_bounds_lonlat_if_verified": None,
        "geo_grid_verified_from_prefix_only": False,
    }
    if first_ifd < min_ifd:
        raise GeoGridBlocked("invalid first TIFF directory offset")
    if first_ifd + count_width > SAMPLE_BYTES:
        return empty
    count = struct.unpack_from(endian + ("Q" if big else "H"), raw, first_ifd)[0]
    if count > MAX_FIRST_IFD_ENTRIES:
        raise GeoGridBlocked("excessive TIFF directory entries")
    if first_ifd + count_width + count * entry_size > SAMPLE_BYTES:
        return empty

    tags = {}
    for i in range(count):
        at = first_ifd + count_width + i * entry_size
        tag, dtype = struct.unpack_from(endian + "HH", raw, at)
        if tag not in (MODEL_PIXEL_SCALE, MODEL_TIEPOINT, GEO_KEY_DIRECTORY, MODEL_TRANSFORM):
            continue
        if tag in tags:
            raise GeoGridBlocked("duplicate GeoTIFF tag")
        n = struct.unpack_from(endian + ("Q" if big else "I"), raw, at + 4)[0]
        field = at + (12 if big else 8)
        tags[tag] = (tag, dtype, n, field)

    if MODEL_TRANSFORM in tags and (MODEL_PIXEL_SCALE in tags or MODEL_TIEPOINT in tags):
        raise GeoGridBlocked("conflicting GeoTIFF model transform with scale/tiepoint")

    scale = tiepoint = None
    keys = {}
    if MODEL_PIXEL_SCALE in tags:
        entry = tags[MODEL_PIXEL_SCALE]
        if entry[1:3] != (12, 3):
            raise GeoGridBlocked("ModelPixelScaleTag must be three doubles")
        data = _tag_data(raw, entry, value_width=value_width, endian=endian)
        if data is not None:
            scale = struct.unpack(endian + "3d", data)
            if not all(math.isfinite(x) for x in scale) or not (scale[0] > 0 and scale[1] > 0):
                raise GeoGridBlocked("invalid GeoTIFF pixel scale")
    if MODEL_TIEPOINT in tags:
        entry = tags[MODEL_TIEPOINT]
        if entry[1:3] != (12, 6):
            raise GeoGridBlocked("ModelTiepointTag must be a single 6-double tiepoint")
        data = _tag_data(raw, entry, value_width=value_width, endian=endian)
        if data is not None:
            tiepoint = struct.unpack(endian + "6d", data)
            if not all(math.isfinite(x) for x in tiepoint):
                raise GeoGridBlocked("nonfinite GeoTIFF tiepoint")
    if GEO_KEY_DIRECTORY in tags:
        entry = tags[GEO_KEY_DIRECTORY]
        if entry[1] != 3 or not 4 <= entry[2] <= MAX_TAG_ITEMS or entry[2] % 4:
            raise GeoGridBlocked("invalid GeoKeyDirectoryTag type/count")
        data = _tag_data(raw, entry, value_width=value_width, endian=endian)
        if data is not None:
            values = struct.unpack(endian + str(entry[2]) + "H", data)
            version, revision, minor, declared_keys = values[:4]
            if version != 1 or revision > 2 or minor > 9 or declared_keys > 60 or (
                len(values) != 4 + 4 * declared_keys
            ):
                raise GeoGridBlocked("invalid GeoKeyDirectory header/count")
            for i in range(declared_keys):
                key, loc, n, val = values[4 + i * 4: 8 + i * 4]
                if key in keys:
                    raise GeoGridBlocked("duplicate GeoTIFF key")
                if key in (1024, 1025, 2048):
                    # Only the literal inline EPSG/model/raster scalar is trusted.
                    if (loc, n) != (0, 1):
                        raise GeoGridBlocked("GeoTIFF CRS/model key not directly encoded")
                    keys[key] = val

    details = {
        "pixel_scale_degrees_if_complete": list(scale[:2]) if scale else None,
        "tiepoint_raster_and_wgs84_if_complete": list(tiepoint) if tiepoint else None,
        "geokey_model_type_if_complete": keys.get(1024),
        "geokey_raster_type_if_complete": keys.get(1025),
        "geokey_geographic_crs_if_complete": keys.get(2048),
        "header_tile_bounds_lonlat_if_verified": None,
        "geo_grid_verified_from_prefix_only": False,
    }
    if width is None or height is None or not scale or not tiepoint:
        return details
    if (type(width) is not int or type(height) is not int or
        width != 36_000 or height != 36_000):
        return details
    if keys.get(1024) != 2 or keys.get(1025) != 1 or keys.get(2048) != 4326:
        return details

    i, j, k, x, y, z = tiepoint
    sx, sy, _ = scale
    xmin, xmax = x - i * sx, x + (width - i) * sx
    ymax, ymin = y + j * sy, y - (height - j) * sy
    bounds = (xmin, ymin, xmax, ymax)
    if all(math.isfinite(v) for v in bounds) and all(
        abs(observed - target) <= 1e-6
        for observed, target in zip(bounds, SOURCE_TILE_BOUNDS)
    ) and abs(k) <= 1e-9 and abs(z) <= 1e-9:
        details["header_tile_bounds_lonlat_if_verified"] = [round(v, 8) for v in bounds]
        details["geo_grid_verified_from_prefix_only"] = True
    return details
