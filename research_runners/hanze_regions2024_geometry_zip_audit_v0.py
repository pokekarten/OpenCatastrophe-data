#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original HANZE v3.0.2-beta v2024 region-geometry ZIP byte and layout audit.

Read the original publisher ZIP in memory only, require original provider MD5
and byte length, reject unsafe ZIP members and malformed shapefile headers.
Return aggregate layout, SHP/SHX/DBF sizes and field names only. Not a spatial
intersection, hazard footprint, commercial-use approval, or insurer-loss model.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import io
import math
from pathlib import PurePosixPath
import re
import struct
import zipfile

SOURCE_RELEASE = "https://zenodo.org/records/23670886"
SOURCE_URL = ("https://zenodo.org/api/records/23670886/files/"
              "Regions_v2024_simplified.zip/content")
PUBLISHER_BYTES = 2430309
PUBLISHER_MD5 = "410542984fda7e8898ccae3727b71cd8"
MAX_SOURCE_BYTES = 4_000_000
MAX_UNCOMPRESSED_BYTES = 150_000_000
MAX_MEMBER_BYTES = 100_000_000
MAX_MEMBERS = 80
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
EXPECTED_TYPES = frozenset({".shp", ".shx", ".dbf", ".prj", ".cpg", ".xml", ".qix", ".qmd", ".sbn", ".sbx"})


class RegionArchiveError(ValueError):
    """A source-original archive cannot safely be interpreted."""


def _dbf_header(zf: zipfile.ZipFile, member: str, cap: int) -> dict:
    with zf.open(member) as source:
        hdr = source.read(32)
        if len(hdr) != 32:
            raise RegionArchiveError("short DBF header")
        nrows, hlen, rlen = struct.unpack_from("<IHH", hdr, 4)
        if not 33 <= hlen <= 8192 or not 1 <= rlen <= 4096 or nrows > 100_000:
            raise RegionArchiveError("invalid bounded DBF header")
        rest = source.read(hlen - 32)
    if len(rest) != hlen - 32 or rest[-1:] != b"\r":
        raise RegionArchiveError("malformed DBF descriptor terminator")
    if (hlen - 33) % 32:
        raise RegionArchiveError("invalid DBF field descriptor length")
    fields = []
    for offset in range(0, hlen - 33, 32):
        spec = rest[offset:offset+32]
        raw = spec[:11].split(b"\x00", 1)[0]
        try:
            name = raw.decode("ascii")
        except UnicodeError as exc:
            raise RegionArchiveError("DBF field name is nonascii") from exc
        if not name or not re.fullmatch("[A-Za-z0-9_]+", name):
            raise RegionArchiveError("invalid DBF field identifier")
        if name in fields:
            raise RegionArchiveError("duplicate DBF field name")
        fields.append(name)
    if cap < hlen + nrows * rlen:
        raise RegionArchiveError("DBF length too short for declared records")
    if not fields or len(fields) > 200:
        raise RegionArchiveError("unexpected DBF field count")
    return {"declared_record_count": nrows, "field_names": fields,
            "field_count": len(fields), "record_length": rlen}


def _shape_header(zf: zipfile.ZipFile, shp: str, shx: str) -> dict:
    with zf.open(shp) as source:
        raw = source.read(100)
    with zf.open(shx) as source:
        index_head = source.read(100)
    if len(raw) != 100 or len(index_head) != 100:
        raise RegionArchiveError("short SHP/SHX header")
    for b in (raw, index_head):
        if struct.unpack_from(">I", b, 0)[0] != 9994:
            raise RegionArchiveError("invalid ESRI shapefile magic")
        if struct.unpack_from("<I", b, 28)[0] != 1000:
            raise RegionArchiveError("unsupported shapefile version")
    shape_type = struct.unpack_from("<I", raw, 32)[0]
    if shape_type not in (5, 15, 25, 31):
        raise RegionArchiveError("region archive is not a polygon shapefile")
    if struct.unpack_from("<I", index_head, 32)[0] != shape_type:
        raise RegionArchiveError("SHP/SHX shapefile type mismatch")
    bbox = struct.unpack_from("<4d", raw, 36)
    if any(not math.isfinite(x) for x in bbox) or bbox[0] > bbox[2] or bbox[1] > bbox[3]:
        raise RegionArchiveError("invalid SHP spatial bounds")
    shp_declared = struct.unpack_from(">I", raw, 24)[0] * 2
    shx_declared = struct.unpack_from(">I", index_head, 24)[0] * 2
    shp_real = zf.getinfo(shp).file_size
    shx_real = zf.getinfo(shx).file_size
    if shp_declared != shp_real or shx_declared != shx_real or shx_real < 100 or (shx_real - 100) % 8:
        raise RegionArchiveError("SHP/SHX original lengths or index count disagree")
    return {"shape_type_code": shape_type, "shape_index_record_count": (shx_real-100)//8,
            "bbox_header_values_finite_and_ordered": True,
            "bbox_geodetic_coordinate_reference_verified": False}


def inspect_hanze_region_geometry_zip(blob: bytes, expected_sha256: str | None = None) -> dict:
    if type(blob) is not bytes or len(blob) != PUBLISHER_BYTES or len(blob) > MAX_SOURCE_BYTES:
        raise RegionArchiveError("original archive provider-byte length mismatch")
    if hashlib.md5(blob, usedforsecurity=False).hexdigest() != PUBLISHER_MD5:
        raise RegionArchiveError("original publisher MD5 mismatch")
    sha = hashlib.sha256(blob).hexdigest()
    if expected_sha256 is not None and (
        type(expected_sha256) is not str or not SHA256.fullmatch(expected_sha256)
        or expected_sha256 != sha
    ):
        raise RegionArchiveError("original source SHA256 mismatch")
    try:
        archive = zipfile.ZipFile(io.BytesIO(blob), mode="r")
    except (OSError, zipfile.BadZipFile) as exc:
        raise RegionArchiveError("invalid region ZIP") from exc
    with archive:
        infos = archive.infolist()
        if not 3 <= len(infos) <= MAX_MEMBERS:
            raise RegionArchiveError("unexpected member count")
        groups = {}
        names = set()
        types = Counter()
        total = 0
        for member in infos:
            name = member.filename
            path = PurePosixPath(name)
            if (not name or name.startswith("/") or "\\" in name or
                ":" in name or any(part in ("..", ".") for part in path.parts)
                or name.endswith("/") or member.is_dir()):
                raise RegionArchiveError("archive member path not a regular relative file")
            if name in names:
                raise RegionArchiveError("duplicate original ZIP member path")
            names.add(name)
            if (member.flag_bits & 1 or member.compress_type not in
                    (zipfile.ZIP_DEFLATED, zipfile.ZIP_STORED)):
                raise RegionArchiveError("encrypted or unsupported ZIP compression")
            if (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise RegionArchiveError("ZIP symbolic link forbidden")
            if member.file_size > MAX_MEMBER_BYTES or member.file_size < 0:
                raise RegionArchiveError("member exceeds bounded source extraction")
            total += member.file_size
            if total > MAX_UNCOMPRESSED_BYTES:
                raise RegionArchiveError("archive expansion exceeds total bound")
            suffix = path.suffix.lower()
            if suffix not in EXPECTED_TYPES:
                raise RegionArchiveError("unreviewed archive file extension: " + repr(suffix) + "; file: " + repr(name))
            types[suffix] += 1
            key = str(path.with_suffix(""))
            group = groups.setdefault(key, {})
            if suffix in group:
                raise RegionArchiveError("duplicate basename and extension")
            group[suffix] = name
        shape_datasets = []
        for root, parts in sorted(groups.items()):
            if ".shp" not in parts:
                if ".shx" in parts or ".dbf" in parts:
                    raise RegionArchiveError("orphan shapefile data component")
                continue
            if not all(s in parts for s in (".shx", ".dbf")):
                raise RegionArchiveError("shapefile trio incomplete")
            shape = _shape_header(archive, parts[".shp"], parts[".shx"])
            dbf = _dbf_header(archive, parts[".dbf"], archive.getinfo(parts[".dbf"]).file_size)
            shape["dbf"] = dbf
            shape["index_and_dbf_records_equal"] = (
                shape["shape_index_record_count"] == dbf["declared_record_count"])
            if not shape["index_and_dbf_records_equal"]:
                raise RegionArchiveError("shapefile/DBF record counts differ")
            shape["has_projection_wkt"] = ".prj" in parts
            shape["has_codepage_file"] = ".cpg" in parts
            shape_datasets.append(shape)
        if not shape_datasets:
            raise RegionArchiveError("no supported shapefile source")
        return {
            "schema_version": "hanze-native-regions-2024-zip-layout-v0",
            "publisher_record": SOURCE_RELEASE,
            "publisher_archive_url": SOURCE_URL,
            "original_bytes": len(blob),
            "publisher_md5_matched": True,
            "observed_sha256": sha,
            "original_sha256_independently_pinned": expected_sha256 is not None,
            "archive_member_count": len(infos),
            "total_decompressed_member_bytes": total,
            "member_extensions_counts": {k: types[k] for k in sorted(types)},
            "shapefile_component_groups": shape_datasets,
            "original_geo_names_or_coordinate_arrays_exported": False,
            "geometry_topology_or_projection_validated": False,
            "admin_polygons_are_not_flood_hazard_footprints": True,
            "attached_insured_assets_or_claims": False,
            "source_rights_and_geography_sublicenses_reviewed": False,
            "model_input_admitted": False,
        }
