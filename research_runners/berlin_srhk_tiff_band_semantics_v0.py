#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Inspect bounded TIFF header band/NoData/units *declarations* only.

Pure offline library. Caller must separately authenticate original provider
bytes and ZIP/TIFF prefix. Reading GDAL_NO_DATA or GDAL_METADATA from IFD
does not read raster pixels, verify a mask, prove water-depth units or admit
source data into an insurer/CAT model.
"""
from __future__ import annotations

import math
import struct
from xml.etree import ElementTree as ET

MAX_PREFIX = 1_048_576
MAX_ENTRIES = 512
MAX_GDAL_XML = 32_768
REVIEWED_UNIT_LABELS = {
    "m": "m", "metre": "m", "meter": "m", "meters": "m", "metres": "m",
    "cm": "cm", "mm": "mm",
}


class TiffBandError(ValueError):
    """Bad/ambiguous/unsafe TIFF-band metadata."""


def _read_value(data: bytes, order: str, tag: int, row: tuple[int, int, bytes]):
    kind, count, packed = row
    if (tag == 42113 and kind != 2 or tag == 42112 and kind != 2
            or count < 1 or count > (128 if tag == 42113 else MAX_GDAL_XML)):
        raise TiffBandError("unreviewed GDAL tag type or length")
    if count <= 4:
        return packed[:count]
    off = struct.unpack(order + "I", packed)[0]
    if off < 8:
        raise TiffBandError("unsafe GDAL tag pointer")
    if off + count > len(data):
        return None
    return data[off:off+count]


def _text(raw: bytes, maximum: int):
    if not raw or len(raw) > maximum or not raw.endswith(b"\0"):
        raise TiffBandError("GDAL ASCII tag not safely NUL-terminated")
    if b"\0" in raw[:-1]:
        raise TiffBandError("embedded NUL in GDAL ASCII tag")
    try:
        value = raw[:-1].decode("ascii")
    except UnicodeError as exc:
        raise TiffBandError("non-ASCII GDAL tag outside reviewed contract") from exc
    if any(ord(c) < 32 and c not in "\t\n\r" for c in value):
        raise TiffBandError("control character in GDAL tag")
    return value.strip()


def _number(s: str):
    if not s or len(s) > 48:
        raise TiffBandError("unreviewed numeric GDAL value")
    if s.lower() in ("nan", "+nan", "-nan"):
        return {"type": "nan_sentinel", "value": None}
    try:
        val = float(s)
    except ValueError as exc:
        raise TiffBandError("invalid numeric GDAL metadata") from exc
    if not math.isfinite(val):
        raise TiffBandError("nonfinite non-NaN GDAL numeric value")
    return {"type": "finite_number", "value": val}


def _read_xml(raw: bytes):
    if b"<!doctype" in raw.lower() or b"<!entity" in raw.lower():
        raise TiffBandError("GDAL XML entity and DTD disallowed")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise TiffBandError("invalid GDAL metadata XML") from exc
    if root.tag != "GDALMetadata":
        raise TiffBandError("unreviewed GDAL metadata XML root")
    if len(root) > 128:
        raise TiffBandError("unbounded GDAL metadata Item count")
    fields = {}
    for e in root:
        if e.tag != "Item":
            raise TiffBandError("non-Item GDAL XML element")
        key = e.get("name")
        if key not in ("UNITTYPE", "SCALE", "OFFSET"):
            continue
        sample = e.get("sample")
        role = e.get("role")
        domain = e.get("domain")
        if sample not in (None, "0") or role not in (None, "") or domain not in (None, ""):
            continue
        if len(e) or key in fields or e.text is None or len(e.text) > 80:
            raise TiffBandError("ambiguous or oversized GDAL band metadata")
        fields[key] = e.text.strip()
    return fields


def inspect_tiff_band_declarations(prefix: bytes) -> dict:
    """Parse TIFF IFD metadata with explicit UNKNOWN for absent/out-of-range tags."""
    if type(prefix) is not bytes or not 8 <= len(prefix) <= MAX_PREFIX:
        raise TiffBandError("not a bounded source TIFF prefix")
    if prefix[:4] == b"II*\0":
        order = "<"
    elif prefix[:4] == b"MM\0*":
        order = ">"
    else:
        raise TiffBandError("expected classic TIFF first IFD")
    ifd = struct.unpack_from(order + "I", prefix, 4)[0]
    result = {
        "band_metadata_ifd_accessible": False,
        "bits_per_sample": None,
        "sample_format_code": None,
        "samples_per_pixel": None,
        "tiff_compression_code": None,
        "gdal_nodata_tag_present": None,
        "gdal_nodata_declared": None,
        "gdal_band_unit_label_declared": None,
        "gdal_band_unit_label_reviewed": False,
        "gdal_band_scale_claim": None,
        "gdal_band_offset_claim": None,
        "gdal_metadata_tag_present": None,
        "missing_gdal_metadata_does_not_imply_meters_or_no_nodata": True,
        "nodata_mask_or_pixels_validated": False,
        "water_depth_units_or_scale_scientifically_validated": False,
        "building_hazard_or_cat_loss_admitted": False,
        "original_tiff_pixels_accessed": False,
    }
    if ifd < 8:
        raise TiffBandError("invalid classic TIFF IFD position")
    if ifd + 2 > len(prefix):
        return result
    count = struct.unpack_from(order + "H", prefix, ifd)[0]
    if count > MAX_ENTRIES:
        raise TiffBandError("unbounded TIFF IFD entries")
    end = ifd + 2 + count*12 + 4
    if end > len(prefix):
        return result
    data = {}
    target = {258, 259, 277, 339, 42112, 42113}
    for n in range(count):
        at = ifd + 2 + n*12
        tag, kind, length = struct.unpack_from(order + "HHI", prefix, at)
        packed = prefix[at+8:at+12]
        if tag in target:
            if tag in data:
                raise TiffBandError("duplicate source band TIFF tag")
            data[tag] = (kind, length, packed)
    result["band_metadata_ifd_accessible"] = True
    for tag, field in ((258, "bits_per_sample"), (259, "tiff_compression_code"),
                       (277, "samples_per_pixel"), (339, "sample_format_code")):
        if tag not in data:
            continue
        kind, count, packed = data[tag]
        if kind != 3 or count != 1:
            raise TiffBandError("unsupported multiple-sample or non-SHORT TIFF band tag")
        value = struct.unpack(order + "H", packed[:2])[0]
        if not 1 <= value <= 65535:
            raise TiffBandError("zero-valued source TIFF band tag")
        result[field] = value
    if 42113 in data:
        raw = _read_value(prefix, order, 42113, data[42113])
        if raw is not None:
            result["gdal_nodata_tag_present"] = True
            result["gdal_nodata_declared"] = _number(_text(raw, 128))
    else:
        result["gdal_nodata_tag_present"] = False
    if 42112 in data:
        raw = _read_value(prefix, order, 42112, data[42112])
        if raw is not None:
            result["gdal_metadata_tag_present"] = True
            fields = _read_xml(_text(raw, MAX_GDAL_XML).encode("utf-8"))
            unit = fields.get("UNITTYPE")
            if unit is not None:
                result["gdal_band_unit_label_declared"] = (
                    REVIEWED_UNIT_LABELS.get(unit.strip().lower())
                )
                result["gdal_band_unit_label_reviewed"] = (
                    result["gdal_band_unit_label_declared"] is not None
                )
            for name, field in (("SCALE", "gdal_band_scale_claim"),
                                ("OFFSET", "gdal_band_offset_claim")):
                if name in fields:
                    v = _number(fields[name])
                    if v["type"] != "finite_number":
                        raise TiffBandError("nonfinite source band scale or offset")
                    result[field] = v["value"]
    else:
        result["gdal_metadata_tag_present"] = False
    return result
