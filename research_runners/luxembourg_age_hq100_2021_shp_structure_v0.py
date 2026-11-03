# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Count original AGE HQ100 SHP *structure* without reading any point coordinates.

Reader position: immediately after the 100-byte ESRI SHP main header.
For every record read header, polygon/part/point counts, and part offsets,
but skip (without decoding) all coordinate bytes. This is not geodetic
validation or proof of actual polygon validity.
"""
from __future__ import annotations

import struct

MAX_SHAPE_RECORDS = 1000000
MAX_POINTS = 5000000
MAX_PARTS = 500000


class HQ100ShapeStructureError(ValueError):
    pass


def inspect_polygon_structure(stream, *, declared_shp_bytes: int,
                              declared_shape_type: int) -> dict:
    if (declared_shape_type != 5 or not isinstance(declared_shp_bytes, int)
            or not 100 <= declared_shp_bytes <= 1024 * 1024 * 1024):
        raise HQ100ShapeStructureError("Expected original Polygon SHP header")
    offset = 100
    records = points = parts = 0
    max_parts = max_points = 0
    while offset < declared_shp_bytes:
        if records >= MAX_SHAPE_RECORDS:
            raise HQ100ShapeStructureError("Unbounded SHP record count")
        raw = stream.read(8)
        if len(raw) != 8:
            raise HQ100ShapeStructureError("Truncated SHP record header")
        ordinal, words = struct.unpack(">II", raw)
        contents_bytes = words * 2
        if (ordinal != records + 1 or contents_bytes < 44
                or offset + 8 + contents_bytes > declared_shp_bytes):
            raise HQ100ShapeStructureError("Invalid SHP record numbering or byte length")
        descriptor = stream.read(44)
        if len(descriptor) != 44:
            raise HQ100ShapeStructureError("Truncated SHP polygon record descriptor")
        shape_type = struct.unpack_from("<I", descriptor, 0)[0]
        n_parts, n_points = struct.unpack_from("<II", descriptor, 36)
        if (shape_type != 5 or n_parts < 1 or n_points < 4 * n_parts
                or parts + n_parts > MAX_PARTS or points + n_points > MAX_POINTS
                or contents_bytes != 44 + 4 * n_parts + 16 * n_points):
            raise HQ100ShapeStructureError("Unsupported polygon/ring/point record geometry layout")
        offsets = stream.read(4 * n_parts)
        if len(offsets) != 4 * n_parts:
            raise HQ100ShapeStructureError("Truncated original SHP part offsets")
        previous = -1
        for (index,) in struct.iter_unpack("<I", offsets):
            if index <= previous or index >= n_points:
                raise HQ100ShapeStructureError("Invalid or unsorted SHP part index")
            previous = index
        if struct.unpack_from("<I", offsets, 0)[0] != 0:
            raise HQ100ShapeStructureError("First source ring offset must start at point zero")
        # Drain raw location bytes in bounded chunks. Never decode point values.
        remaining = 16 * n_points
        while remaining:
            block = stream.read(min(1024 * 1024, remaining))
            if not block:
                raise HQ100ShapeStructureError("Truncated original SHP point byte block")
            remaining -= len(block)
        records += 1
        parts += n_parts
        points += n_points
        max_parts = max(max_parts, n_parts)
        max_points = max(max_points, n_points)
        offset += 8 + contents_bytes
    if offset != declared_shp_bytes or records < 1:
        raise HQ100ShapeStructureError("Original SHP records do not conserve declared bytes")
    return {
        "shp_polygon_record_count": records,
        "shp_total_polygon_ring_parts": parts,
        "shp_total_coordinate_pairs_skipped_without_decoding": points,
        "shp_largest_record_ring_parts": max_parts,
        "shp_largest_record_coordinate_pairs_skipped": max_points,
        "individual_coordinate_values_observed_or_exported": False,
        "polygon_topology_or_positive_area_verified": False,
    }
