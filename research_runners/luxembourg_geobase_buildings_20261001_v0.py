#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Research-only exact-source receipt for Luxembourg ACT GeoBase Buildings 2026-10-01.

Fixed official CC0 Buildings-theme ZIP only; read-only layer/schema counts,
not provider feature geometries or per-building IDs. MD5 is catalogue supplied,
not a signed/authenticating digest. A fresh SHA-256 is reproducibility evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import stat
import sys
import tempfile
import zipfile

RESOURCE_ID = "e93c27f8-1908-442b-9dc4-d10a117cf315"
RESOURCE_URL = ("https://download.data.public.lu/resources/bd-l-geobase/"
                "20261001-010523/buildings-20261001.zip")
ORIGINAL_MD5 = "f414154f993128a63f539aae2644c75a"
MAX_ZIP_BYTES = 80 * 1024 * 1024
MAX_EXPANDED_BYTES = 1500 * 1024 * 1024
MAX_MEMBERS = 80
MAX_FILES = 8
MAX_RATIO = 500
HEX_MD5 = re.compile(r"[a-f0-9]{32}\Z")


class GeoBaseError(ValueError):
    """Unexpected, unsafe or unverified source file; never admit model data."""


def _fingerprints(file: Path) -> tuple[str, str]:
    h1, h2 = hashlib.md5(), hashlib.sha256()
    with file.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h1.update(block)
            h2.update(block)
    return h1.hexdigest(), h2.hexdigest()


def _safe(info: zipfile.ZipInfo) -> None:
    name = info.filename
    mode = (info.external_attr >> 16) & 0o170000
    if (not name or name.startswith("/") or "\\" in name or ":" in name
            or "\x00" in name or any(p in {"", ".", ".."} for p in name.rstrip("/").split("/"))
            or info.flag_bits & 1 or mode == stat.S_IFLNK):
        raise GeoBaseError("Unsafe or encrypted original ZIP member")


def _metadata(original: Path) -> dict:
    db = sqlite3.connect(original.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    try:
        db.execute("PRAGMA query_only=ON")
        if db.execute("PRAGMA application_id").fetchone()[0] not in (0x47504B47, 0x47503130, 0x47503131):
            raise GeoBaseError("Expected a real GeoPackage SQLite application ID")
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        required = {"gpkg_contents", "gpkg_geometry_columns", "gpkg_spatial_ref_sys"}
        if not required.issubset(tables):
            raise GeoBaseError("Missing mandatory GeoPackage metadata tables")
        rows = list(db.execute(
            "SELECT c.table_name,c.srs_id,g.column_name,g.geometry_type_name,g.srs_id "
            "FROM gpkg_contents c JOIN gpkg_geometry_columns g ON c.table_name=g.table_name "
            "WHERE c.data_type='features' ORDER BY c.table_name"))
        if not 1 <= len(rows) <= 24:
            raise GeoBaseError("Unexpected original feature-layer count")
        result = []
        for table, source_srs, geom_col, geom_type, declared_srs in rows:
            if source_srs != declared_srs or source_srs != 2169:
                raise GeoBaseError("Source geometry does not declare EPSG:2169")
            if not isinstance(geom_type, str) or geom_type.upper() not in ("POLYGON", "MULTIPOLYGON", "GEOMETRY"):
                raise GeoBaseError("Unexpected nonpolygon geometry declaration")
            if not isinstance(table, str) or not table or len(table) > 128 or "\x00" in table:
                raise GeoBaseError("Unsafe layer name")
            quoted = '"' + table.replace('"', '""') + '"'
            cols = list(db.execute("PRAGMA table_info(" + quoted + ")"))
            if len(cols) > 80 or geom_col not in [x[1] for x in cols]:
                raise GeoBaseError("Invalid or excessive original layer columns")
            count = db.execute("SELECT count(*) FROM " + quoted).fetchone()[0]
            if not isinstance(count, int) or not 1 <= count <= 20000000:
                raise GeoBaseError("Invalid original layer record count")
            result.append({
                "layer": table, "geometry_column": geom_col,
                "geometry_type_declared": geom_type, "epsg_declared": source_srs,
                "feature_rows": count, "field_names_only": [x[1] for x in cols],
            })
        return {"gpkg_layer_metadata": result}
    except sqlite3.DatabaseError as exc:
        raise GeoBaseError("Unreadable original GeoPackage metadata") from exc
    finally:
        db.close()


def inspect(source: Path, *, expected_md5: str = ORIGINAL_MD5) -> dict:
    source = Path(source)
    if not isinstance(expected_md5, str) or not HEX_MD5.fullmatch(expected_md5):
        raise GeoBaseError("Malformed predeclared publisher MD5")
    if not source.is_file() or source.is_symlink() or not 0 < source.stat().st_size <= MAX_ZIP_BYTES:
        raise GeoBaseError("Missing, symlink or oversized original source ZIP")
    md5, sha256 = _fingerprints(source)
    if md5 != expected_md5:
        raise GeoBaseError("Original source MD5 differs from exact publisher resource")
    gpkg_results = []
    total = 0
    with tempfile.TemporaryDirectory(prefix="oc-lu-geobase-buildings-") as working:
        try:
            with zipfile.ZipFile(source) as archive:
                members = archive.infolist()
                if not 1 <= len(members) <= MAX_MEMBERS:
                    raise GeoBaseError("Unexpected ZIP member count")
                names = set()
                for member in members:
                    _safe(member)
                    if member.filename in names:
                        raise GeoBaseError("Duplicate original ZIP member")
                    names.add(member.filename)
                    if member.is_dir():
                        continue
                    if (member.file_size <= 0 or member.compress_size <= 0 or
                            member.file_size > member.compress_size * MAX_RATIO):
                        raise GeoBaseError("Invalid or excessively compressed original member")
                    total += member.file_size
                    if total > MAX_EXPANDED_BYTES:
                        raise GeoBaseError("Original ZIP exceeds expanded size budget")
                    if member.filename.lower().endswith(".gpkg"):
                        if len(gpkg_results) >= MAX_FILES:
                            raise GeoBaseError("Too many original GeoPackage files")
                        local = Path(working) / ("file-" + str(len(gpkg_results)) + ".gpkg")
                        h = hashlib.sha256()
                        written = 0
                        with archive.open(member) as inp, local.open("xb") as out:
                            while data := inp.read(1024 * 1024):
                                written += len(data)
                                if written > member.file_size:
                                    raise GeoBaseError("ZIP decompression size exceeded")
                                h.update(data)
                                out.write(data)
                        if written != member.file_size:
                            raise GeoBaseError("ZIP inner GeoPackage declared size mismatch")
                        details = _metadata(local)
                        gpkg_results.append({"gpkg_sha256": h.hexdigest(), "gpkg_bytes": written, **details})
                    else:
                        # CRC-test ancillary archive members too, without retaining bytes.
                        with archive.open(member) as inp:
                            for _ in iter(lambda: inp.read(1024 * 1024), b""):
                                pass
                if not gpkg_results:
                    raise GeoBaseError("No original GeoPackage member")
        except (zipfile.BadZipFile, zipfile.LargeZipFile, RuntimeError, OSError, EOFError, NotImplementedError) as exc:
            raise GeoBaseError("Original ZIP integrity/CRC/read failed") from exc
    return {
        "profile": "lu-act-geobase-buildings-20261001-source-metadata-v0",
        "resource_id": RESOURCE_ID, "publisher_md5_match": True,
        "original_zip_md5": md5, "original_zip_sha256": sha256,
        "original_zip_bytes": source.stat().st_size,
        "archive_total_expanded_bytes": total,
        "original_gpkg_files": gpkg_results,
        "original_geometry_rows_exported": False,
        "source_rights_and_scientific_admission_approved": False,
        "same_provider_act2023v2_independence_verified": False,
        "model_input_admitted": False,
        "source_data_persisted": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(inspect(args.source_zip), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False))
    except (OSError, GeoBaseError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
