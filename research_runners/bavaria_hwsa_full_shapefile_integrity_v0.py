#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline fail-closed LfU flood-defence shapefile archive structural proof.

Reads user-provided original Bavaria LfU source ZIP(s) from outside Git.
Does NOT fetch over the network, copy private provider geometry to Git, emit
location points, assign protected buildings, modify WRI hazard depth, or admit
a CAT insurance model. ZIP metadata alone is insufficient: this verifier
decompresses each actual member with ZIP CRC checking, parses every SHP
polyline record, crosschecks its SHX offsets and DBF row counts, and verifies
both declared coordinate systems and multi-format DBF identities.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import zipfile

PROVIDER = "Bayerisches Landesamt für Umwelt"
SOURCE_ATOM = "https://www.lfu.bayern.de/gdi/dls/hwsa.xml"
SOURCE_ARCHIVES = {
    4258: "https://www.lfu.bayern.de/gdi/dls/daten/hwsa/hwsa_epsg4258_shp.zip",
    25832: "https://www.lfu.bayern.de/gdi/dls/daten/hwsa/hwsa_epsg25832_shp.zip",
}
EXPECTED_COUNTS = {"deich": 2171, "hwschutzwand": 801, "hwschutzsystem": 891}
FIELD_NAMES = ("WWO_KNZ", "GEW_KNZ", "OBJ_ART", "WWA", "LINK")
EXTENSIONS = ("dbf", "prj", "shp", "shx")
MAX_ARCHIVE = 12_000_000
MAX_MEMBER = 4_000_000
MAX_TOTAL_DECOMPRESSED = 12_000_000
MAX_POINTS_PER_RECORD = 200_000
PROFILE = "bavaria-lfu-hwsa-full-member-geometry-integrity-offline-v0"


class GeometryGateError(ValueError):
    """Bad or incomplete provider source, or inconsistent Shapefile geometry."""


def _shape_header(data: bytes, label: str) -> dict:
    if len(data) < 100:
        raise GeometryGateError(label + ": truncated Shapefile header")
    if (struct.unpack_from(">I", data, 0)[0] != 9994
            or struct.unpack_from("<I", data, 28)[0] != 1000
            or struct.unpack_from("<I", data, 32)[0] != 3):
        raise GeometryGateError(label + ": not an ESRI v1000 polyline layer")
    total_words = struct.unpack_from(">I", data, 24)[0]
    if total_words * 2 != len(data):
        raise GeometryGateError(label + ": declared file length differs from extracted bytes")
    bbox = struct.unpack_from("<4d", data, 36)
    if (not all(math.isfinite(v) for v in bbox)
            or bbox[0] > bbox[2] or bbox[1] > bbox[3]):
        raise GeometryGateError(label + ": invalid XY bounds")
    return {"bounds": bbox, "source_file_bytes": len(data)}


def _inspect_dbf(data: bytes) -> dict:
    if len(data) < 34:
        raise GeometryGateError("truncated DBF")
    records = struct.unpack_from("<I", data, 4)[0]
    header_bytes, record_bytes = struct.unpack_from("<HH", data, 8)
    if (header_bytes < 33 or (header_bytes - 33) % 32
            or record_bytes < 2 or header_bytes > len(data)):
        raise GeometryGateError("invalid DBF row width or header")
    number_fields = (header_bytes - 33) // 32
    if number_fields != len(FIELD_NAMES) or data[header_bytes - 1] != 0x0D:
        raise GeometryGateError("unexpected LfU DBF field descriptor structure")
    if len(data) not in (header_bytes + records * record_bytes,
                         header_bytes + records * record_bytes + 1):
        raise GeometryGateError("DBF byte count cannot be reconciled to row count")
    if len(data) == header_bytes + records * record_bytes + 1 and data[-1] != 0x1A:
        raise GeometryGateError("invalid DBF EOF marker")
    fields = []
    widths = 0
    for i in range(number_fields):
        p = 32 + 32 * i
        name = data[p:p+11].split(b"\x00", 1)[0].decode("ascii")
        kind = chr(data[p + 11])
        width = data[p + 16]
        if kind != "C" or not 0 < width <= 254:
            raise GeometryGateError("LfU DBF unexpected column type or size")
        fields.append(name)
        widths += width
    if tuple(fields) != FIELD_NAMES or record_bytes != widths + 1:
        raise GeometryGateError("LfU source DBF schema changed")
    deleted_count = 0
    for i in range(records):
        flag = data[header_bytes + i * record_bytes]
        if flag == 0x2A:
            deleted_count += 1
        elif flag != 0x20:
            raise GeometryGateError("unrecognised DBF record/deletion flag")
    return {
        "records_in_source_dbf": records,
        "deleted_row_flags": deleted_count,
        "fixed_field_names": list(fields),
        "header_bytes": header_bytes,
        "record_bytes": record_bytes,
        "source_member_sha256": hashlib.sha256(data).hexdigest(),
    }


def _inspect_shx(shx: bytes, shp: bytes, crs: int) -> dict:
    ih = _shape_header(shx, "SHX")
    gh = _shape_header(shp, "SHP")
    if len(shx) < 100 or (len(shx) - 100) % 8:
        raise GeometryGateError("SHX index does not contain whole 8-byte entries")
    if any(abs(a - b) > 1e-7 for a, b in zip(ih["bounds"], gh["bounds"])):
        raise GeometryGateError("SHP vs SHX source world bounds mismatch")
    n = (len(shx) - 100) // 8
    if n > 100_000:
        raise GeometryGateError("source Shapefile unexpectedly huge")
    if crs == 4258:
        left, bottom, right, top = gh["bounds"]
        if not (5 < left <= right < 16 and 46 < bottom <= top < 52):
            raise GeometryGateError("EPSG:4258 source bounds not in Bavaria")
    elif crs == 25832:
        left, bottom, right, top = gh["bounds"]
        if not (100000 < left <= right < 1000000
                and 4_500_000 < bottom <= top < 6_000_000):
            raise GeometryGateError("EPSG:25832 source UTM32 bounds out of range")
    else:
        raise GeometryGateError("unknown original projected CRS")
    count_null = total_parts = total_points = 0
    previous_record_end = 100
    for i in range(n):
        ix_offset, ix_content_words = struct.unpack_from(">II", shx, 100 + 8*i)
        offset = ix_offset * 2
        content_bytes = ix_content_words * 2
        if (offset != previous_record_end
                or content_bytes < 4 or offset + 8 + content_bytes > len(shp)):
            raise GeometryGateError("SHX record does not align with sequential SHP record")
        record_id, record_content_words = struct.unpack_from(">II", shp, offset)
        if record_id != i + 1 or record_content_words != ix_content_words:
            raise GeometryGateError("SHP record number/length contradicts SHX")
        data_at = offset + 8
        shape_type = struct.unpack_from("<I", shp, data_at)[0]
        if shape_type == 0 and content_bytes == 4:
            count_null += 1
        elif shape_type == 3:
            if content_bytes < 48:
                raise GeometryGateError("short polyline record")
            record_box = struct.unpack_from("<4d", shp, data_at + 4)
            parts, points = struct.unpack_from("<II", shp, data_at + 36)
            if (not 0 < parts <= points <= MAX_POINTS_PER_RECORD
                    or 44 + 4*parts + 16*points != content_bytes
                    or not all(math.isfinite(v) for v in record_box)):
                raise GeometryGateError("polyline point/part geometry invalid")
            part_base = data_at + 44
            point_base = part_base + 4*parts
            last_part = -1
            for j in range(parts):
                part = struct.unpack_from("<I", shp, part_base + 4*j)[0]
                if not last_part < part < points:
                    raise GeometryGateError("polyline parts are not strictly increasing")
                last_part = part
            if struct.unpack_from("<I", shp, part_base)[0] != 0:
                raise GeometryGateError("polyline must start with first vertex")
            rx0, ry0, rx1, ry1 = record_box
            if (rx0 > rx1 or ry0 > ry1
                    or rx0 < gh["bounds"][0]-1e-7 or rx1 > gh["bounds"][2]+1e-7
                    or ry0 < gh["bounds"][1]-1e-7 or ry1 > gh["bounds"][3]+1e-7):
                raise GeometryGateError("record bounding box outside source SHP limits")
            for j in range(points):
                x, y = struct.unpack_from("<2d", shp, point_base + j*16)
                if (not math.isfinite(x) or not math.isfinite(y)
                        or x < rx0-1e-7 or x > rx1+1e-7
                        or y < ry0-1e-7 or y > ry1+1e-7):
                    raise GeometryGateError("non-finite or out-of-record-bbox vertex")
            total_parts += parts
            total_points += points
        else:
            raise GeometryGateError("unsupported or inconsistent polyline type")
        previous_record_end = offset + 8 + content_bytes
    if previous_record_end != len(shp):
        raise GeometryGateError("trailing unexplained SHP bytes or missing record")
    return {
        "source_polyline_records": n,
        "source_null_shape_records": count_null,
        "polyline_parts_checked": total_parts,
        "polyline_points_checked": total_points,
        "bounds_native_crs": list(gh["bounds"]),
        "all_shx_offsets_and_actual_shp_record_bytes_checked": True,
        "all_record_bboxes_and_vertices_checked": True,
        "shp_member_sha256": hashlib.sha256(shp).hexdigest(),
        "shx_member_sha256": hashlib.sha256(shx).hexdigest(),
    }


def inspect_original_zip(path: Path, epsg: int) -> dict:
    if epsg not in SOURCE_ARCHIVES:
        raise GeometryGateError("unknown original source EPSG")
    if not path.is_file() or not 1 <= path.stat().st_size <= MAX_ARCHIVE:
        raise GeometryGateError("source original ZIP missing or exceeds bounded size")
    expected = {
        f"{kind}_epsg{epsg}.{ext}"
        for kind in EXPECTED_COUNTS for ext in EXTENSIONS
    }
    try:
        with zipfile.ZipFile(path, "r", allowZip64=False) as archive:
            entries = archive.infolist()
            if (len(entries) != 12 or len({p.filename for p in entries}) != 12
                    or {p.filename for p in entries} != expected):
                raise GeometryGateError("ZIP member manifest differs from fixed LfU source schema")
            if sum(p.file_size for p in entries) > MAX_TOTAL_DECOMPRESSED:
                raise GeometryGateError("ZIP total unpacked size too large")
            for item in entries:
                if (item.file_size > MAX_MEMBER or item.is_dir() or item.flag_bits & 1
                        or item.compress_type not in (zipfile.ZIP_DEFLATED, zipfile.ZIP_STORED)
                        or item.filename.startswith(("/", ".")) or "/" in item.filename):
                    raise GeometryGateError("unsafe, unexpected or encrypted ZIP file")
            members = {p.filename: archive.read(p) for p in entries}
    except (zipfile.BadZipFile, EOFError, OSError, RuntimeError, ValueError) as exc:
        if isinstance(exc, GeometryGateError):
            raise
        raise GeometryGateError("ZIP CRC, decompression or member validation failed") from exc

    details = {}
    for kind, expected_count in EXPECTED_COUNTS.items():
        prefix = f"{kind}_epsg{epsg}."
        dbf = _inspect_dbf(members[prefix+"dbf"])
        shape = _inspect_shx(members[prefix+"shx"], members[prefix+"shp"], epsg)
        if dbf["records_in_source_dbf"] != expected_count or (
                shape["source_polyline_records"] != expected_count):
            raise GeometryGateError("original DBF/SHX/SHP record counts disagree")
        raw_prj = members[prefix+"prj"].decode("ascii", errors="strict")
        if epsg == 4258 and not any(x in raw_prj.upper() for x in ("ETRS", "ETRF")):
            raise GeometryGateError("unexpected source geographic .prj CRS")
        if epsg == 25832 and not ("UTM" in raw_prj.upper() and "32" in raw_prj):
            raise GeometryGateError("unexpected source projected UTM .prj CRS")
        details[kind] = {
            "source_count": expected_count,
            "source_dbf": dbf, "source_line_geometry": shape,
            "native_epsg": epsg,
            "per_record_insured_protection_proven": False,
            "crest_elevation_or_design_standard_source_verified": False,
        }
    return {
        "original_source_url": SOURCE_ARCHIVES[epsg],
        "original_zip_bytes": path.stat().st_size,
        "original_zip_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "native_epsg": epsg,
        "archive_member_count": len(members),
        "classes": details,
        "total_source_records": sum(EXPECTED_COUNTS.values()),
        "no_source_asset_coordinates_exported": True,
        "cross_epsg_duplicate_classes_not_double_counted": True,
        "full_original_zip_crc_and_spatial_geometry_checked": True,
    }


def inspect_original_archives(archives: dict[int, Path]) -> dict:
    if not archives or any(k not in SOURCE_ARCHIVES for k in archives):
        raise GeometryGateError("source archives must be 25832 and/or 4258")
    if len({p.resolve() for p in archives.values()}) != len(archives):
        raise GeometryGateError("cannot use one file as both projected source archives")
    proofs = {epsg: inspect_original_zip(path, epsg) for epsg, path in sorted(archives.items())}
    if set(proofs) == set(SOURCE_ARCHIVES):
        for kind in EXPECTED_COUNTS:
            a = proofs[4258]["classes"][kind]["source_dbf"]["source_member_sha256"]
            b = proofs[25832]["classes"][kind]["source_dbf"]["source_member_sha256"]
            if a != b:
                raise GeometryGateError("DBF attributes changed between source CRS exports")
    return {
        "profile": PROFILE,
        "provider": PROVIDER,
        "source_atom": SOURCE_ATOM,
        "provider_declared_license": "CC-BY-SA-4.0",
        "source_archives_proved": proofs,
        "counted_unique_source_rows_not_both_projection_exports": sum(EXPECTED_COUNTS.values()),
        "original_geometry_presence_not_site_protection": True,
        "reprojecting_EPSG_to_WRI_4326_performed": False,
        "fixed_or_mobile_deployment_confirmed": False,
        "dike_height_or_conditional_failure_probabilities_verified": False,
        "source_version_and_commercial_usage_review_complete": False,
        "WRI_hazard_defence_depth_correction_computed": False,
        "site_inside_defended_area_identified": False,
        "vulnerability_or_insurer_losses_computed": False,
        "model_input_admitted": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epsg-4258", type=Path)
    parser.add_argument("--epsg-25832", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    sources = {}
    if args.epsg_4258:
        sources[4258] = args.epsg_4258
    if args.epsg_25832:
        sources[25832] = args.epsg_25832
    if not sources or args.out.resolve() in {p.resolve() for p in sources.values()}:
        parser.error("at least one original ZIP required; never overwrite originals")
    try:
        proof = inspect_original_archives(sources)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(proof, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    except (OSError, UnicodeError, GeometryGateError) as exc:
        print("BLOCKED: "+str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
