# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline, byte-pinned NHSL v1.0 XLSX + Nunavut regional GeoPackage preflight.

Read-only analysis of ORIGINAL release assets already obtained separately under
their licence; NEVER download, commit, admit, or export provider data here.
A successful preflight is not a model-use or insurance portfolio approval.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import posixpath
import re
import sqlite3
import stat
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any

RELEASE_URL = "https://github.com/OpenDRR/national-human-settlement/releases/tag/v1.0"
PINNED = {
    "dictionary": {
        "name": "nhsl_physical_exposure_attributes_en.xlsx",
        "bytes": 17888,
        "sha256": "e191efb7662c1442c8da7379f54a86e710d6f7c63ff76b2bad89550c9ac55ca8",
    },
    "polygon": {
        "name": "nhsl_physical_exposure_indicators_s_nu.zip",
        "bytes": 73663,
        "sha256": "8da41815457b3a163de09be24691ffaf972c4b34ced69dfacabc00723275032b",
        "member": "nhsl_physical_exposure_indicators_s_nu.gpkg",
        "gpkg_bytes": 233472,
        "gpkg_crc32": "187affd2",
        "geometry_family": {"POLYGON", "MULTIPOLYGON"},
        "required_columns": {
            "Sauid", "Et_BldgNum", "Et_BldgArea", "Et_BldgValue",
            "Et_StrValue", "Et_NStrValue", "Et_ContValue", "Et_AssetValue",
        },
    },
    "archetype": {
        "name": "nhsl_physical_exposure_indicators_b_nu.zip",
        "bytes": 113156,
        "sha256": "c5b3e15bf1050712aba4d6b627f1a40bf616d4cfde8cf28f77967c9973ea0bdb",
        "member": "nhsl_physical_exposure_indicators_b_nu.gpkg",
        "gpkg_bytes": 876544,
        "gpkg_crc32": "c641a5fc",
        "geometry_family": {"POINT", "MULTIPOINT"},
        "required_columns": {
            "Sauid", "BldgID", "E_BldgNum", "E_BldgValue",
            "E_StrValue", "E_NStrValue", "E_ContValue", "E_AssetValue",
        },
    },
}
MAX_RAW_ASSET_BYTES = 1_000_000
MAX_DECOMPRESSED_MEMBER_BYTES = 2_000_000
MAX_DICTIONARY_XML_BYTES = 2_000_000
NS = {
    "ss": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}

class NHSLBinaryError(ValueError):
    """Original package identity, binary structure, or schema is not validated."""


def _bytes(path: Path, expected: dict[str, Any]) -> bytes:
    if not path.is_file() or not 0 < path.stat().st_size <= MAX_RAW_ASSET_BYTES:
        raise NHSLBinaryError("missing or unbounded NHSL original file")
    data = path.read_bytes()
    if len(data) != expected["bytes"]:
        raise NHSLBinaryError(f"original provider asset size drift: {expected['name']}")
    if hashlib.sha256(data).hexdigest() != expected["sha256"]:
        raise NHSLBinaryError(f"original provider asset SHA-256 drift: {expected['name']}")
    return data


def _zip_members(raw: bytes, max_member_bytes: int) -> zipfile.ZipFile:
    try:
        zf = zipfile.ZipFile(io.BytesIO(raw), "r")
        files = zf.infolist()
        if len(files) > 100 or len({f.filename for f in files}) != len(files):
            raise NHSLBinaryError("duplicate or too many ZIP members")
        if any(
            not f.filename or f.filename.startswith("/")
            or ".." in f.filename.split("/") or "\\" in f.filename
            or f.flag_bits & 1 or stat.S_ISLNK(f.external_attr >> 16)
            or f.file_size > max_member_bytes
            or f.compress_type not in (zipfile.ZIP_DEFLATED, zipfile.ZIP_STORED)
            for f in files
        ):
            raise NHSLBinaryError("unsafe or oversized ZIP member")
        if sum(f.file_size for f in files) > 5_000_000:
            raise NHSLBinaryError("ZIP uncompressed budget exceeded")
        return zf
    except (zipfile.BadZipFile, OSError) as exc:
        raise NHSLBinaryError("invalid ZIP structure") from exc


def parse_original_dictionary(raw: bytes) -> dict[str, Any]:
    """Read source XLSX sheet names and literal field tokens via stdlib OOXML."""
    with _zip_members(raw, MAX_DICTIONARY_XML_BYTES) as zf:
        names = set(zf.namelist())
        if "xl/workbook.xml" not in names or "xl/_rels/workbook.xml.rels" not in names:
            raise NHSLBinaryError("not an XLSX workbook")
        wb = ET.fromstring(zf.read("xl/workbook.xml"))
        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        by_id = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            shared = [
                "".join(part.text or "" for part in si.findall(".//ss:t", NS))
                for si in root.findall(".//ss:si", NS)
            ]
        found: dict[str, set[str]] = {}
        for sheet in wb.findall(".//ss:sheet", NS):
            sheet_name = sheet.attrib.get("name")
            if sheet_name not in {"polygons", "buildings"}:
                continue
            sheet_id = sheet.attrib.get("{" + NS["r"] + "}id")
            target = by_id.get(sheet_id)
            if not target or ".." in target.split("/"):
                raise NHSLBinaryError("XLSX worksheet relationship missing or unsafe")
            path = (
                target.lstrip("/") if target.startswith("/xl/")
                else posixpath.normpath(posixpath.join("xl", target))
            )
            if path not in names:
                raise NHSLBinaryError(f"XLSX missing sheet XML: {sheet_name}")
            root = ET.fromstring(zf.read(path))
            tokens: set[str] = set()
            for c in root.findall(".//ss:sheetData/ss:row/ss:c", NS):
                value = c.find("ss:v", NS)
                inline = c.find("ss:is", NS)
                if c.attrib.get("t") == "s" and value is not None:
                    try:
                        cell_value = shared[int(value.text or "-1")]
                    except (IndexError, ValueError) as exc:
                        raise NHSLBinaryError("broken XLSX shared string index") from exc
                elif inline is not None:
                    cell_value = "".join(x.text or "" for x in inline.findall(".//ss:t", NS))
                elif c.attrib.get("t") == "str" and value is not None:
                    cell_value = value.text or ""
                else:
                    continue
                if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,70}", cell_value):
                    tokens.add(cell_value)
            found[sheet_name] = tokens
        if set(found) != {"polygons", "buildings"}:
            raise NHSLBinaryError("required original XLSX sheets not found")
        required_polygon = {
            "Sauid", "E_SauidLat", "E_SauidLon", "Et_BldgNum", "Et_BldgArea",
            "Et_BldgValue", "Et_StrValue", "Et_NStrValue", "Et_ContValue",
            "Et_AssetValue", "Et_ResHD", "fasuid",
        }
        required_building = {
            "Sauid", "BldgID", "BldgLat", "BldgLon", "E_BldgNum",
            "E_BldgValue", "E_StrValue", "E_NStrValue", "E_ContValue",
            "E_AssetValue", "E_BlgEpoch", "E_SSCZone", "fasuid",
        }
        if required_polygon - found["polygons"] or required_building - found["buildings"]:
            raise NHSLBinaryError("original XLSX critical field identities missing")
        return {
            "source_sheets": sorted(found),
            "required_polygon_attributes_seen": len(required_polygon),
            "required_archetype_attributes_seen": len(required_building),
            "original_dictionary_polygon_field_count_expected": 62,
            "original_dictionary_archetype_field_count_expected": 38,
            "literal_difference_to_live_service": {
                "polygon": ["Et_ResHD != Et_Res", "fasuid != fsauid"],
                "archetype": ["E_BlgEpoch != E_BldgEpoch", "E_SSCZone != SSC_Zone", "fasuid != fsauid"],
            },
        }


def _feature_geometry_wkb_base_type(
    raw: bytes | memoryview | None,
    source_srs_id: int,
) -> int:
    """Verify GeoPackage header/SRS and identify the actual ISO WKB geometry family.

    This is a type-level inspection, NOT full coordinate/topology validation.
    GeoPackage geometry_columns may lawfully declare the generic GEOMETRY
    supertype even when all actual WKB values are Polygon/MultiPolygon/Point.
    """
    if not isinstance(raw, (bytes, memoryview)):
        raise NHSLBinaryError("GeoPackage feature geometry missing or not a BLOB")
    blob = bytes(raw)
    if len(blob) < 13 or blob[:2] != b"GP" or blob[2] != 0:
        raise NHSLBinaryError("invalid or unsupported GeoPackage binary geometry header")
    flags = blob[3]
    if flags & 0xF0:
        raise NHSLBinaryError("empty/reserved GeoPackage geometry flags")
    order = "little" if (flags & 1) else "big"
    envelope = (flags >> 1) & 7
    envelope_bytes = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}.get(envelope)
    if envelope_bytes is None:
        raise NHSLBinaryError("reserved GeoPackage geometry envelope code")
    header_srs = int.from_bytes(blob[4:8], order, signed=True)
    if header_srs != source_srs_id:
        raise NHSLBinaryError("GeoPackage per-feature SRS does not match metadata")
    start = 8 + envelope_bytes
    if start + 5 > len(blob):
        raise NHSLBinaryError("truncated WKB geometry after GeoPackage envelope")
    wkb_order = blob[start]
    if wkb_order not in (0, 1):
        raise NHSLBinaryError("invalid WKB endian indicator")
    raw_type = int.from_bytes(
        blob[start + 1:start + 5], "little" if wkb_order else "big"
    )
    # ISO WKB can add 1000/2000/3000 to the basic type for Z/M/ZM.
    if raw_type >= 4000 or raw_type < 1:
        raise NHSLBinaryError("unsupported or extended WKB feature type")
    return raw_type % 1000


def check_sqlite_gpkg(gpkg: bytes, role: str, expected: dict[str, Any]) -> dict[str, Any]:
    """Run a read-only, temporary SQLite structural check; never persist original data."""
    if not gpkg.startswith(b"SQLite format 3\x00") or len(gpkg) > MAX_DECOMPRESSED_MEMBER_BYTES:
        raise NHSLBinaryError("decompressed member is not a bounded SQLite GeoPackage")
    with tempfile.TemporaryDirectory(prefix="nhsl-source-check-") as tmp:
        file = Path(tmp) / "original.gpkg"
        file.write_bytes(gpkg)
        try:
            con = sqlite3.connect(file.as_uri() + "?mode=ro&immutable=1", uri=True)
            try:
                con.execute("PRAGMA trusted_schema=OFF")
                table_names = {name for (name,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                required = {"gpkg_contents", "gpkg_geometry_columns", "gpkg_spatial_ref_sys"}
                if not required.issubset(table_names):
                    raise NHSLBinaryError(f"{role} missing GeoPackage metadata tables")
                geometry_rows = con.execute(
                    "SELECT table_name, column_name, geometry_type_name, srs_id FROM gpkg_geometry_columns"
                ).fetchall()
                if len(geometry_rows) != 1:
                    raise NHSLBinaryError(f"{role}: expected one geometry table")
                table, column, geom, epsg = geometry_rows[0]
                if (
                    not isinstance(table, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,110}", table)
                    or table not in table_names
                    or not isinstance(column, str)
                    or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,110}", column)
                    or not isinstance(geom, str)
                    or geom.upper() not in expected["geometry_family"] | {"GEOMETRY"}
                    or type(epsg) is not int
                ):
                    raise NHSLBinaryError(f"{role}: wrong feature table, column or geometry declaration")
                columns = {str(row[1]) for row in con.execute(f'PRAGMA table_info("{table}")')}
                missing = (expected["required_columns"] | {column}) - columns
                if missing:
                    raise NHSLBinaryError(f"{role}: missing exact GPKG columns: {sorted(missing)}")
                expected_wkb = {"polygon": {3, 6}, "archetype": {1, 4}}[role]
                observed_wkb: set[int] = set()
                checked_geometries = 0
                for (binary,) in con.execute(f'SELECT "{column}" FROM "{table}"'):
                    checked_geometries += 1
                    if checked_geometries > 5_000_000:
                        raise NHSLBinaryError(f"{role}: unbounded feature geometries")
                    base_type = _feature_geometry_wkb_base_type(binary, epsg)
                    if base_type not in expected_wkb:
                        raise NHSLBinaryError(
                            f"{role}: actual WKB geometry family conflicts with role"
                        )
                    observed_wkb.add(base_type)
                if not checked_geometries:
                    raise NHSLBinaryError(f"{role}: no original feature geometries")
                content = con.execute(
                    "SELECT data_type, srs_id FROM gpkg_contents WHERE table_name=?", (table,)
                ).fetchone()
                if not content or content[0] != "features" or content[1] != epsg:
                    raise NHSLBinaryError(f"{role}: invalid feature metadata or CRS")
                if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise NHSLBinaryError(f"{role}: SQLite integrity_check failed")
                count = con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                if type(count) is not int or count < 0 or count > 5_000_000:
                    raise NHSLBinaryError(f"{role}: impossible row count")
                return {
                    "geometry_family": geom.upper(),
                    "metadata_geometry_is_generic": geom.upper() == "GEOMETRY",
                    "observed_wkb_base_types": sorted(observed_wkb),
                    "wkb_feature_geometries_checked": checked_geometries,
                    "wkb_type_and_srs_check": "passed",
                    "wkb_topology_and_coordinate_bounds_checked": False,
                    "internal_gpkg_srs_id": epsg,
                    "feature_table_name": table,
                    "feature_count": count,
                    "required_columns_seen": len(expected["required_columns"]),
                    "sqlite_integrity_check": "ok",
                    "original_rows_or_coordinates_emitted": False,
                }
            finally:
                con.close()
        except sqlite3.DatabaseError as exc:
            raise NHSLBinaryError(f"{role}: invalid SQLite GeoPackage") from exc


def check_archive(raw: bytes, role: str, expected: dict[str, Any]) -> dict[str, Any]:
    with _zip_members(raw, MAX_DECOMPRESSED_MEMBER_BYTES) as zf:
        members = zf.infolist()
        if len(members) != 1 or members[0].filename != expected["member"]:
            raise NHSLBinaryError(f"{role}: wrong or extra archive member")
        info = members[0]
        if (
            info.compress_type != zipfile.ZIP_DEFLATED
            or info.file_size != expected["gpkg_bytes"]
            or f"{info.CRC:08x}" != expected["gpkg_crc32"]
        ):
            raise NHSLBinaryError(f"{role}: changed publisher ZIP member metadata")
        try:
            gpkg = zf.read(info)
        except (zipfile.BadZipFile, RuntimeError, EOFError) as exc:
            raise NHSLBinaryError(f"{role}: damaged ZIP member or CRC") from exc
        if len(gpkg) != expected["gpkg_bytes"]:
            raise NHSLBinaryError(f"{role}: member bytes mismatch")
        return check_sqlite_gpkg(gpkg, role, expected)


def inspect_assets(dictionary: Path, polygons: Path, archetypes: Path) -> dict[str, Any]:
    a = _bytes(dictionary, PINNED["dictionary"])
    b = _bytes(polygons, PINNED["polygon"])
    c = _bytes(archetypes, PINNED["archetype"])
    return {
        "source_candidate_id": "can.nrcan.nhsl.physical-exposure.2016-2020",
        "release_url": RELEASE_URL,
        "region": "Nunavut",
        "release_identity": "OpenDRR NHSL GitHub release v1.0",
        "original_file_hashes_verified": {
            key: {"name": data["name"], "bytes": data["bytes"], "sha256": data["sha256"]}
            for key, data in PINNED.items()
        },
        "dictionary": parse_original_dictionary(a),
        "polygons": check_archive(b, "polygon", PINNED["polygon"]),
        "building_archetypes": check_archive(c, "archetype", PINNED["archetype"]),
        "original_file_bytes_committed": False,
        "source_rights_for_model_use_reviewed": False,
        "scientific_fitness_reviewed": False,
        "polygon_to_archetype_value_conservation_proven": False,
        "source_admitted": False,
        "oed_insured_locations_exportable": False,
        "admission_status": "not_admitted",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dictionary-xlsx", type=Path, required=True)
    p.add_argument("--polygon-zip", type=Path, required=True)
    p.add_argument("--archetype-zip", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        result = inspect_assets(args.dictionary_xlsx, args.polygon_zip, args.archetype_zip)
    except (NHSLBinaryError, OSError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
