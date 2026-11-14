# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline, byte-bounded header preflight for Natural Earth 110m Admin-0 Countries v5.1.1.

This is neither a downloader nor a complete GIS/scientific validation. It never
persists provider bytes and cannot authorize admission or CAT model use.
"""

from __future__ import annotations

from io import BytesIO
import hashlib
import stat
import struct
from zipfile import BadZipFile, ZipFile

SOURCE_ID = "naturalearth.public-domain.admin-geography"
PRODUCT_VERSION = "5.1.1"
BASENAME = "ne_110m_admin_0_countries"
REQUIRED = frozenset({"shp", "shx", "dbf", "prj"})
OPTIONAL = frozenset({"cpg", "version.txt", "readme.html"})
MAX_ZIP_BYTES = 1024 * 1024
MAX_MEMBER_BYTES = 5 * 1024 * 1024
MAX_TOTAL_UNPACKED = 10 * 1024 * 1024
MAX_RECORDS = 5000


class ArchiveBlocked(ValueError):
    """A provider archive failed the deliberately narrow offline preflight."""


def _shapefile_header(raw: bytes, extension: str) -> tuple[int, tuple[float, ...]]:
    if len(raw) < 100 or struct.unpack_from(">I", raw, 0)[0] != 9994:
        raise ArchiveBlocked(f"{extension}: invalid Shapefile magic/header")
    if struct.unpack_from("<I", raw, 28)[0] != 1000:
        raise ArchiveBlocked(f"{extension}: unsupported Shapefile header version")
    if struct.unpack_from("<I", raw, 32)[0] != 5:
        raise ArchiveBlocked(f"{extension}: expected Polygon shape type")
    if struct.unpack_from(">I", raw, 24)[0] * 2 != len(raw):
        raise ArchiveBlocked(f"{extension}: declared file length mismatch")
    bbox = struct.unpack_from("<4d", raw, 36)
    xmin, ymin, xmax, ymax = bbox
    if not (-180 <= xmin <= xmax <= 180 and -90 <= ymin <= ymax <= 90):
        raise ArchiveBlocked(f"{extension}: invalid lon/lat bounding box")
    return len(raw), bbox


def inspect_original_zip(raw: bytes) -> dict[str, object]:
    """Check archive framing and high-level SHP/SHX/DBF/PRJ identity; hash ORIGINAL ZIP.

    No geometric record parsing, feature validity, authority of country codes,
    political-border policy, or scientific-model quality is established here.
    """
    if type(raw) is not bytes or not 100 <= len(raw) <= MAX_ZIP_BYTES:
        raise ArchiveBlocked("ZIP input must be nonempty bounded original bytes")
    if not raw.startswith(b"PK\x03\x04"):
        raise ArchiveBlocked("invalid ZIP local header")
    try:
        with ZipFile(BytesIO(raw)) as archive:
            members = archive.infolist()
            if not 4 <= len(members) <= 7:
                raise ArchiveBlocked("unexpected archive member count")
            found: dict[str, object] = {}
            total = 0
            for item in members:
                name = item.filename
                if (item.is_dir() or "/" in name or "\\" in name or name.startswith(".")
                        or not name.startswith(BASENAME + ".")):
                    raise ArchiveBlocked("unexpected member name/path")
                extension = name[len(BASENAME) + 1:].lower()
                if extension not in REQUIRED | OPTIONAL or extension in found:
                    raise ArchiveBlocked("unknown or duplicate Shapefile component")
                if item.flag_bits & 1 or (item.create_system == 3 and stat.S_IFMT(item.external_attr >> 16) == stat.S_IFLNK):
                    raise ArchiveBlocked("encrypted or symlink member")
                if item.file_size > MAX_MEMBER_BYTES or item.compress_size == 0 and item.file_size > 0:
                    raise ArchiveBlocked("oversized or invalid member")
                if item.compress_size and item.file_size > 100 * item.compress_size:
                    raise ArchiveBlocked("excessive compression ratio")
                total += item.file_size
                if total > MAX_TOTAL_UNPACKED:
                    raise ArchiveBlocked("uncompressed archive budget exceeded")
                found[extension] = item
            if not REQUIRED.issubset(found):
                raise ArchiveBlocked("required SHP/SHX/DBF/PRJ missing")
            parts = {key: archive.read(found[key]) for key in REQUIRED}
    except (BadZipFile, EOFError, OSError, RuntimeError, ValueError) as exc:
        if isinstance(exc, ArchiveBlocked):
            raise
        raise ArchiveBlocked("corrupted or unparseable ZIP") from exc

    shp_bytes, shp_bbox = _shapefile_header(parts["shp"], "shp")
    shx_bytes, shx_bbox = _shapefile_header(parts["shx"], "shx")
    if shx_bytes < 108 or (shx_bytes - 100) % 8:
        raise ArchiveBlocked("shx: malformed index length")
    count = (shx_bytes - 100) // 8
    if count > MAX_RECORDS or any(abs(a - b) > 1e-9 for a, b in zip(shp_bbox, shx_bbox)):
        raise ArchiveBlocked("shx: unreasonable count or inconsistent bounding box")
    dbf = parts["dbf"]
    if len(dbf) < 33 or dbf[0] not in {0x03, 0x83}:
        raise ArchiveBlocked("dbf: invalid dBASE header")
    dbf_count = struct.unpack_from("<I", dbf, 4)[0]
    header_length, record_length = struct.unpack_from("<HH", dbf, 8)
    if (dbf_count != count or not 0 < dbf_count <= MAX_RECORDS
            or header_length < 33 or record_length < 1
            or header_length + dbf_count * record_length > len(dbf)):
        raise ArchiveBlocked("dbf: record count or declared length mismatch")
    try:
        prj = parts["prj"].decode("ascii").upper()
    except UnicodeDecodeError as exc:
        raise ArchiveBlocked("prj: unsupported encoding") from exc
    if not ("GEOGCS" in prj and ("WGS_1984" in prj or "WGS 84" in prj)):
        raise ArchiveBlocked("prj: WGS84 geographic coordinate system not identified")
    return {
        "source_id": SOURCE_ID,
        "product_version": PRODUCT_VERSION,
        "original_sha256": hashlib.sha256(raw).hexdigest(),
        "original_bytes": len(raw),
        "shp_bytes": shp_bytes,
        "shx_record_count": count,
        "dbf_record_count": dbf_count,
        "bbox_lonlat": list(shp_bbox),
        "verification_scope": "offline_shapefile_header_only_not_scientific_admission",
        "stored_original_bytes": False,
    }
