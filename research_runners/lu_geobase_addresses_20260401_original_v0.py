#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original April-2026 ACT GeoBase Addresses GPKG: structure and key QA only.

Publisher source-version pinned; read-only original bytes; no address values,
source identifiers, points, household records or crosswalks are emitted.
The publisher MD5 is a version receipt, not a signed authenticity proof.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import zipfile

from research_runners.luxembourg_geobase_buildings_20261001_v0 import _safe

URL = ("https://download.data.public.lu/resources/bd-l-geobase/"
       "20260401-011010/addresses-20260401.zip")
RESOURCE_ID = "d76d095a-94a0-4426-af15-45f70881c63f"
PUBLISHER_MD5 = "5157355db4b81736ad2e1d2d399a1bed"
# Independently observed complete original source bytes in GitHub run 41885861174.
EXPECTED_ZIP_SHA256 = "edaf17ed2c802c155fd75caecfe44cbd23581a4b0a59f25935fa2d71a5e0b2eb"
EXPECTED_GPKG_SHA256 = "b357e7aa76a61ecabee45df28d68f3cdbce4ecdebf6f396d4d83ad2ba648fc12"
MAX_ZIP_BYTES = 24 * 1024 * 1024
MAX_EXPANDED_BYTES = 400 * 1024 * 1024
MAX_MEMBERS = 50
MAX_LAYER_ROWS = 400000
VALID_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,127}$")


class GeoBaseAddressError(ValueError):
    """Reject unsafe, drifted or unsupported original address source."""


def _hash_file(path: Path) -> tuple[int, str, str]:
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= MAX_ZIP_BYTES:
        raise GeoBaseAddressError("original source ZIP is not regular or within fixed size budget")
    md5 = hashlib.md5()  # nosec B324: compare against publisher's MD5 receipt only
    sha = hashlib.sha256()
    size = 0
    with path.open("rb") as src:
        while data := src.read(1024 * 1024):
            size += len(data)
            md5.update(data)
            sha.update(data)
    return size, md5.hexdigest(), sha.hexdigest()


def _text_id(value: object, name: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, int) and type(value) is not bool:
        value = str(value)
    if not isinstance(value, str) or len(value) > 256:
        raise GeoBaseAddressError(f"{name}: invalid identifier type or length")
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise GeoBaseAddressError(f"{name}: control character in identifier")
    return value if value.strip() else None


def _id_summary(values, role: str, *, max_rows: int = MAX_LAYER_ROWS) -> dict:
    counts: Counter[str] = Counter()
    rows = missing = padded = 0
    for value in values:
        rows += 1
        if rows > max_rows:
            raise GeoBaseAddressError(f"{role}: row budget exceeded")
        key = _text_id(value, role)
        if key is None:
            missing += 1
        else:
            counts[key] += 1
            if key.strip() != key:
                padded += 1
    return {
        "rows": rows,
        "nonblank_rows": rows - missing,
        "blank_rows": missing,
        "distinct_nonblank_ids": len(counts),
        "duplicate_excess_nonblank_rows": sum(v - 1 for v in counts.values()),
        "max_rows_per_id": max(counts.values(), default=0),
        "whitespace_padded_rows": padded,
    }


def _quote(value: str) -> str:
    if not VALID_NAME.fullmatch(value):
        raise GeoBaseAddressError("unreviewed original table or column name")
    return '"' + value + '"'


def _gpkg_profile(gpkg: Path) -> dict:
    with closing(sqlite3.connect(gpkg.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)) as db:
        db.execute("PRAGMA query_only=ON")
        if db.execute("PRAGMA application_id").fetchone()[0] not in (
            0x47504B47, 0x47503130, 0x47503131,
        ):
            raise GeoBaseAddressError("original source is not a GeoPackage")
        present = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"gpkg_contents", "gpkg_geometry_columns", "gpkg_spatial_ref_sys"}.issubset(present):
            raise GeoBaseAddressError("mandatory original GeoPackage metadata missing")
        original_layers = list(db.execute(
            "SELECT c.table_name,c.srs_id,g.geometry_type_name,g.column_name,g.srs_id "
            "FROM gpkg_contents c JOIN gpkg_geometry_columns g "
            "ON c.table_name=g.table_name "
            "WHERE c.data_type='features' ORDER BY c.table_name"
        ))
        if not 1 <= len(original_layers) <= 12:
            raise GeoBaseAddressError("unreviewed original address layer count")
        outputs = []
        for table, epsg, geom_type, geom_col, geom_epsg in original_layers:
            if epsg != 2169 or geom_epsg != 2169 or str(geom_type).upper() not in (
                "POINT", "MULTIPOINT", "GEOMETRY",
            ):
                raise GeoBaseAddressError("original address layer EPSG or geometry drift")
            name = _quote(table)
            cols = [r[1] for r in db.execute(f"PRAGMA table_info({name})")]
            if (not 2 <= len(cols) <= 80 or geom_col not in cols
                    or any(not VALID_NAME.fullmatch(c) for c in cols)):
                raise GeoBaseAddressError("original address column schema unreviewed")
            count = db.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
            if type(count) is not int or not 0 < count <= MAX_LAYER_ROWS:
                raise GeoBaseAddressError("original address population out of budget")
            ids = {}
            for field in ("AD_AddressID", "AlternativeIdentifier"):
                if field in cols:
                    q = _quote(field)
                    data = (r[0] for r in db.execute(f"SELECT {q} FROM {name}"))
                    ids[field] = _id_summary(data, field)
                    if ids[field]["rows"] != count:
                        raise GeoBaseAddressError("original ID source row count mismatch")
            outputs.append({
                "source_layer_name": table,
                "geometry_type_declared": geom_type,
                "declared_epsg": epsg,
                "original_feature_rows": count,
                "column_names_only": cols,
                "expected_address_keys_present": {
                    "AD_AddressID": "AD_AddressID" in cols,
                    "AlternativeIdentifier": "AlternativeIdentifier" in cols,
                },
                "aggregate_id_quality": ids,
            })
    return {"gpkg_original_address_layers": outputs}


def inspect(source_zip: Path, *, expected_md5: str = PUBLISHER_MD5,
            expected_zip_sha256: str = EXPECTED_ZIP_SHA256,
            expected_gpkg_sha256: str = EXPECTED_GPKG_SHA256) -> dict:
    if not isinstance(expected_md5, str) or not re.fullmatch(r"[a-f0-9]{32}", expected_md5):
        raise GeoBaseAddressError("invalid publisher source MD5 pin")
    if any(not isinstance(d, str) or not re.fullmatch(r"[a-f0-9]{64}", d)
           for d in (expected_zip_sha256, expected_gpkg_sha256)):
        raise GeoBaseAddressError("invalid original SHA-256 pin")
    size, md5, zip_sha = _hash_file(source_zip)
    if md5 != expected_md5:
        raise GeoBaseAddressError("original publisher ZIP MD5 mismatch")
    if zip_sha != expected_zip_sha256:
        raise GeoBaseAddressError("original ZIP SHA-256 differs from independently observed baseline")
    with tempfile.TemporaryDirectory(prefix="oc-lu-geobase-address-") as temporary:
        target = Path(temporary) / "original.gpkg"
        with zipfile.ZipFile(source_zip) as arc:
            members = arc.infolist()
            if not 1 <= len(members) <= MAX_MEMBERS:
                raise GeoBaseAddressError("original archive member budget exceeded")
            names = set()
            gpkg = []
            total = 0
            for member in members:
                try:
                    _safe(member)
                except ValueError as exc:
                    raise GeoBaseAddressError("unsafe original ZIP member") from exc
                if member.filename in names:
                    raise GeoBaseAddressError("duplicate source ZIP path")
                names.add(member.filename)
                if member.is_dir():
                    continue
                total += member.file_size
                if total > MAX_EXPANDED_BYTES:
                    raise GeoBaseAddressError("expanded original ZIP size exceeds budget")
                if member.filename.lower().endswith(".gpkg"):
                    gpkg.append(member)
            if len(gpkg) != 1:
                raise GeoBaseAddressError("exactly one original GeoPackage is required")
            member = gpkg[0]
            sha = hashlib.sha256()
            written = 0
            with arc.open(member) as raw, target.open("xb") as dest:
                while chunk := raw.read(1024 * 1024):
                    written += len(chunk)
                    if written > member.file_size or written > MAX_EXPANDED_BYTES:
                        raise GeoBaseAddressError("original GeoPackage expansion drift")
                    sha.update(chunk)
                    dest.write(chunk)
            if written != member.file_size or written == 0:
                raise GeoBaseAddressError("original GeoPackage truncated")
            if sha.hexdigest() != expected_gpkg_sha256:
                raise GeoBaseAddressError("original GeoPackage SHA-256 differs from observed baseline")
        report = _gpkg_profile(target)
    return {
        "profile": "lu-geobase-addresses-20260401-original-schema-v0",
        "original_resource_url": URL,
        "official_resource_id": RESOURCE_ID,
        "source_vintage": "2026-04-01",
        "original_zip_bytes": size,
        "publisher_zip_md5_verified": md5,
        "observed_original_zip_sha256": zip_sha,
        "observed_original_gpkg_sha256": sha.hexdigest(),
        "only_aggregate_results": True,
        "all_original_bytes_ephemeral": True,
        "individual_addresses_ids_geometry_exported": False,
        "address_to_building_crosswalk_proven": False,
        "source_independence_proven": False,
        "commercial_rights_approved": False,
        "cat_model_input_admitted": False,
        **report,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-zip", required=True, type=Path)
    args = p.parse_args(argv)
    try:
        result = inspect(args.source_zip)
    except (OSError, ValueError, zipfile.BadZipFile, sqlite3.DatabaseError,
            EOFError, UnicodeError):
        print("BLOCKED: original GeoBase Addresses source integrity or schema drift",
              file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
