#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded offline original ZIP/GeoPackage metadata receipt for Luxembourg ACT2023v2.

Never fetch sources, export individual building records, or admit model inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
import zipfile

PRODUCT_RESOURCE_ID = "d62942ec-0dc8-40e2-9fa4-27841e6e1ac1"
SOURCE_URL = (
    "https://download.data.public.lu/resources/"
    "base-de-donnees-nationale-des-batiments-3d-2023/20260317-160936/"
    "act2023v2-buildings3d-footprints.gpkg.zip"
)
MAX_ZIP_BYTES = 110 * 1024 * 1024
MAX_GPKG_BYTES = 1500 * 1024 * 1024
EXPECTED_SRS = 2169
APPLICATION_ID = 0x47504B47


class OriginalPreflightError(ValueError):
    """Pinned provider archive or metadata does not meet the research contract."""


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def _safe_member(info: zipfile.ZipInfo) -> None:
    name = info.filename
    if (not name or name.startswith("/") or "\\" in name or ":" in name
            or any(p in {"", ".", ".."} for p in name.rstrip("/").split("/"))
            or (info.external_attr >> 16) & 0o170000 == 0o120000
            or info.flag_bits & 1):
        raise OriginalPreflightError("unsafe, linked or encrypted ZIP member")
    if info.file_size > MAX_GPKG_BYTES:
        raise OriginalPreflightError("ZIP member oversized")
    if info.compress_size and info.file_size > 1000 * info.compress_size:
        raise OriginalPreflightError("ZIP excessive expansion ratio")


def _ident(s: str) -> str:
    if not isinstance(s, str) or not s or len(s) > 128 or "\x00" in s:
        raise OriginalPreflightError("invalid SQL identifier")
    return '"' + s.replace('"', '""') + '"'


def _read_gpkg(path: Path) -> dict:
    with path.open("rb") as f:
        if f.read(16) != b"SQLite format 3\x00":
            raise OriginalPreflightError("not SQLite")
    db = sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True)
    try:
        if db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID:
            raise OriginalPreflightError("not a GeoPackage application ID")
        mandatory = {"gpkg_contents", "gpkg_geometry_columns", "gpkg_spatial_ref_sys"}
        found = {r[0] for r in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN "
            "('gpkg_contents', 'gpkg_geometry_columns', 'gpkg_spatial_ref_sys')")}
        if found != mandatory:
            raise OriginalPreflightError("incomplete GeoPackage metadata")
        if not db.execute("SELECT 1 FROM gpkg_spatial_ref_sys WHERE srs_id=?",
                          (EXPECTED_SRS,)).fetchone():
            raise OriginalPreflightError("source EPSG:2169 not declared")
        layers = list(db.execute(
            "SELECT c.table_name,c.data_type,c.srs_id,g.column_name,"
            "g.geometry_type_name,g.srs_id,g.z,g.m,"
            "c.min_x,c.min_y,c.max_x,c.max_y "
            "FROM gpkg_contents c JOIN gpkg_geometry_columns g "
            "ON c.table_name=g.table_name WHERE c.data_type='features' "
            "ORDER BY c.table_name"))
        if not 1 <= len(layers) <= 8:
            raise OriginalPreflightError("unexpected feature-layer count")
        result = []
        for row in layers:
            name, kind, c_srs, col, geom, g_srs, z, m, *bounds = row
            if (kind != "features" or c_srs != EXPECTED_SRS or
                    g_srs != EXPECTED_SRS or not isinstance(geom, str) or
                    geom.upper() not in ("POLYGON", "MULTIPOLYGON") or
                    z not in (0, 2) or m not in (0, 2)):
                raise OriginalPreflightError("invalid footprint geometry/CRS declaration")
            count = db.execute("SELECT count(*) FROM " + _ident(name)).fetchone()[0]
            if not isinstance(count, int) or not 1 <= count <= 20_000_000:
                raise OriginalPreflightError("invalid feature count")
            cols = [r[1] for r in db.execute(
                "PRAGMA table_info(" + _ident(name) + ")")]
            if col not in cols:
                raise OriginalPreflightError("missing declared geometry column")
            result.append({
                "table_name": name, "geometry_column": col,
                "declared_geometry_type": geom, "declared_epsg": EXPECTED_SRS,
                "provider_feature_rows": count, "column_names_only": cols,
                "provider_extent_present": all(v is not None for v in bounds),
            })
        return {"sqlite_application_id": "GPKG", "layers": result}
    except sqlite3.DatabaseError as exc:
        raise OriginalPreflightError("SQLite GeoPackage metadata error") from exc
    finally:
        db.close()


def preflight(path: Path, expected_sha256: str | None = None) -> dict:
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise OriginalPreflightError("original must be a regular non-symlink file")
    size = path.stat().st_size
    if not 0 < size <= MAX_ZIP_BYTES:
        raise OriginalPreflightError("ZIP outside bounded original size")
    zip_sha = _hash(path)
    if expected_sha256 is not None and (
        len(expected_sha256) != 64 or
        any(c not in "0123456789abcdef" for c in expected_sha256) or
        expected_sha256 != zip_sha
    ):
        raise OriginalPreflightError("ZIP SHA-256 mismatch")
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if not 1 <= len(members) <= 12:
                raise OriginalPreflightError("unexpected ZIP member count")
            for item in members:
                _safe_member(item)
            gpkg = [item for item in members if item.filename.lower().endswith(".gpkg")]
            if len(gpkg) != 1:
                raise OriginalPreflightError("exactly one .gpkg member required")
            info = gpkg[0]
            with TemporaryDirectory(prefix="oc-gpkg-") as d:
                local = Path(d) / "original.gpkg"
                gpkg_hash = hashlib.sha256()
                written = 0
                with archive.open(info) as inp, local.open("wb") as out:
                    while buf := inp.read(1024 * 1024):
                        written += len(buf)
                        if written > MAX_GPKG_BYTES:
                            raise OriginalPreflightError("expanded GPKG too large")
                        gpkg_hash.update(buf)
                        out.write(buf)
                if written != info.file_size:
                    raise OriginalPreflightError("ZIP member size disagreement")
                metadata = _read_gpkg(local)
                member_sha = gpkg_hash.hexdigest()
    except (zipfile.BadZipFile, zipfile.LargeZipFile, RuntimeError, EOFError) as exc:
        raise OriginalPreflightError("unsafe or corrupt source ZIP") from exc
    return {
        "profile": "luxembourg-act2023v2-footprint-original-gpkg-receipt-v0",
        "provider_resource_id": PRODUCT_RESOURCE_ID,
        "provider_url": SOURCE_URL,
        "zip_bytes": size, "zip_sha256": zip_sha,
        "verified_against_independent_prior_sha256": expected_sha256 is not None,
        "original_gpkg_bytes": written, "original_gpkg_sha256": member_sha,
        "gpkg_metadata": metadata,
        "raw_building_records_exported": False,
        "source_bytes_persisted_by_script": False,
        "axis_order_and_geometry_validity_verified": False,
        "license_and_scientific_admission_verified": False,
        "model_input_admitted": False,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-zip", type=Path, required=True)
    p.add_argument("--sha256", help="Independent pre-existing SHA-256 if available")
    a = p.parse_args(argv)
    try:
        report = preflight(a.source_zip, expected_sha256=a.sha256)
    except (OSError, OriginalPreflightError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
