# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Live, bounded and ephemeral FileGDB layer-schema inventory for EMSN028.

No raw Copernicus bytes are committed, uploaded or retained. Only layer
metadata (names/schema/CRS/count/bounds), not individual source features,
are printed. A layer-name hint is NOT AOI04 observed-flood admission.
Source-specific reuse rights and historical building vintages stay pending.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import zipfile

from scripts.cems_emns028_ephemeral_zip_inventory_v0 import (
    EXPECTED_SIZE, MAX_ARCHIVE_BYTES, acquire_and_inspect,
)
from scripts.cems_emns028_zip_head_receipt_v0 import SOURCE_URL

PINNED_ARCHIVE_SHA256 = "7ef43d0637447abae705728723c06d2f05415a21667fdee1f10e8fc25b5bf3c2"
MAX_GDB_UNCOMPRESSED_BYTES = 400_000_000
MAX_MEMBERS = 1000


def gdb_members(zf: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    info = zf.infolist()
    if not info or len(info) > MAX_MEMBERS:
        raise ValueError("unexpected ZIP member count")
    for item in info:
        pp = PurePosixPath(item.filename)
        if pp.is_absolute() or ".." in pp.parts or "\\" in item.filename:
            raise ValueError("unsafe archive member path")
        unix_mode = item.external_attr >> 16
        if stat.S_IFMT(unix_mode) == stat.S_IFLNK:
            raise ValueError("archive contains symlink")
    members = [
        item for item in info if any(
            part.lower().endswith(".gdb") for part in PurePosixPath(item.filename).parts
        )
    ]
    if not members:
        raise ValueError("ZIP has no FileGDB members")
    if sum(item.file_size for item in members) > MAX_GDB_UNCOMPRESSED_BYTES:
        raise ValueError("FileGDB uncompressed size exceeds bound")
    gdbs = {
        str(PurePosixPath(*PurePosixPath(item.filename).parts[:i+1]))
        for item in members
        for i, part in enumerate(PurePosixPath(item.filename).parts)
        if part.lower().endswith(".gdb")
    }
    if len(gdbs) != 1:
        raise ValueError("expected exactly one GDB root")
    return members


def extract_gdb_only(zf: zipfile.ZipFile, base: Path) -> Path:
    infos = gdb_members(zf)
    root = next(
        str(PurePosixPath(*PurePosixPath(item.filename).parts[:i+1]))
        for item in infos for i, part in enumerate(PurePosixPath(item.filename).parts)
        if part.lower().endswith(".gdb")
    )
    for item in infos:
        destination = base.joinpath(*PurePosixPath(item.filename).parts)
        if item.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(item, "r") as src, destination.open("wb") as dst:
            copied = 0
            while True:
                chunk = src.read(1024 * 1024)
                if not chunk:
                    break
                copied += len(chunk)
                if copied > item.file_size:
                    raise ValueError("FileGDB member exceeds declared byte size")
                dst.write(chunk)
            if copied != item.file_size:
                raise ValueError("FileGDB member has unexpected byte length")
    gdb_path = base.joinpath(*PurePosixPath(root).parts)
    if not gdb_path.is_dir():
        raise ValueError("extracted FileGDB directory missing")
    return gdb_path


def classify_name(name: str, schema_fields: list[str]) -> dict:
    """Lexical hints only. Unknown means source semantics NOT verified."""
    lowered = name.lower()
    fields = " ".join(schema_fields).lower()
    aoi_hint = any(s in lowered for s in (
        "ponthierry", "fargeau", "aoi04", "aoi_04", "_04",
    ))
    observed_hint = any(s in lowered for s in (
        "obsflood", "observed", "floodextent", "flood_extent",
    ))
    modeled_hint = any(s in lowered for s in (
        "maxflood", "maximum", "depth", "modeled", "modelled",
    ))
    return {
        "aoi04_name_hint": aoi_hint,
        "observed_extent_name_hint": observed_hint and not modeled_hint,
        "modeled_or_depth_name_hint": modeled_hint,
        "has_aoi_discriminator_field_hint": any(
            word in fields for word in ("aoi", "areaofinterest", "area_name")
        ),
        "observed_aoi04_layer_proven": False,
    }


def inspect_gdb(gdb_path: Path) -> dict:
    import fiona  # optional exact-pinned spatial dependency, not in core CI
    if not gdb_path.is_dir():
        raise ValueError("not a FileGDB directory")
    names = fiona.listlayers(str(gdb_path))
    if not names or len(names) > 150:
        raise ValueError("unexpected FileGDB layer count")
    metadata = []
    for name in names:
        if len(name) > 255:
            raise ValueError("unreasonably long FileGDB layer name")
        entry: dict = {"layer_name": name, "opened": False}
        try:
            with fiona.open(str(gdb_path), layer=name, mode="r") as collection:
                props = list(collection.schema.get("properties", {}).keys())
                entry.update({
                    "opened": True,
                    "feature_count": len(collection),
                    "geometry_schema_type": collection.schema.get("geometry"),
                    "crs_wkt_present": bool(collection.crs_wkt),
                    "crs_epsg": collection.crs.to_epsg() if collection.crs else None,
                    "schema_field_names": props[:70],
                    "bbox_native_crs": [
                        round(float(v), 4) for v in collection.bounds
                    ] if collection.bounds else None,
                })
                entry.update(classify_name(name, props))
        except (ValueError, RuntimeError) as exc:
            entry["error_type"] = type(exc).__name__
        metadata.append(entry)
    return {
        "total_layers_listed": len(names),
        "layers_opened": sum(x["opened"] for x in metadata),
        "aoi04_lexical_candidates": sum(x.get("aoi04_name_hint", False) for x in metadata),
        "observed_lexical_candidates": sum(
            x.get("observed_extent_name_hint", False) for x in metadata
        ),
        "layers": metadata,
    }


def run() -> dict:
    # Reuse the original fail-closed approved downloader, SHA, size and
    # central-directory check; it deletes the download in its finally block.
    # For FileGDB reading, acquire in our own temp directory so it remains
    # in-scope until the read-only schema inventory completes.
    import hashlib
    import urllib.request
    from scripts.cems_emns028_zip_head_receipt_v0 import (
        OfficialRedirectOnly, assert_expected_destination,
    )
    opener = urllib.request.build_opener(OfficialRedirectOnly())
    with tempfile.TemporaryDirectory(prefix="cems-emns028-gdb-") as td:
        base = Path(td)
        archive = base / "source.zip"
        request = urllib.request.Request(SOURCE_URL, method="GET", headers={
            "User-Agent": "OpenCatastrophe-CEMS-FileGDB-Research/0.1 (one-shot temporary)"
        })
        sha = hashlib.sha256()
        total = 0
        with opener.open(request, timeout=90) as response:
            assert_expected_destination(response.geturl())
            if response.status != 200:
                raise ValueError("unexpected HTTP status")
            length = response.headers.get("Content-Length")
            if length and (not length.isdecimal() or int(length) != EXPECTED_SIZE):
                raise ValueError("source Content-Length version drift")
            with archive.open("wb") as sink:
                while True:
                    chunk = response.read(min(1024 * 1024, MAX_ARCHIVE_BYTES + 1 - total))
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_ARCHIVE_BYTES:
                        raise ValueError("source archive exceeds byte cap")
                    sha.update(chunk)
                    sink.write(chunk)
        if total != EXPECTED_SIZE or sha.hexdigest() != PINNED_ARCHIVE_SHA256:
            raise ValueError("source ZIP length or SHA-256 does not match pinned archive")
        with zipfile.ZipFile(archive) as zf:
            gdb = extract_gdb_only(zf, base / "extracted")
        receipt = inspect_gdb(gdb)
        return {
            "receipt_kind": "CEMS_EMSN028_FILEGDB_LAYER_SCHEMA_V0",
            "source_url": SOURCE_URL,
            "archive_sha256_verified_against_research_pin": True,
            "archive_sha256": PINNED_ARCHIVE_SHA256,
            "archive_original_bytes": total,
            **receipt,
            "all_original_bytes_temporary_and_deleted": True,
            "source_layer_names_and_crs_only_not_feature_bytes": True,
            "aoi04_observed_extent_geometries_verified": False,
            "source_specific_commercial_rights_cleared": False,
            "physical_event_model_admitted": False,
            "insured_portfolio_admitted": False,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="one explicit temporary full download")
    args = parser.parse_args()
    if not args.live:
        parser.error("--live required; will make zero network calls otherwise")
    try:
        result = run()
    except Exception as exc:
        # Avoid printing potentially signed source URL credentials or raw content.
        result = {
            "receipt_kind": "CEMS_EMSN028_FILEGDB_LAYER_SCHEMA_V0",
            "success": False,
            "error_type": type(exc).__name__,
            "all_original_bytes_temporary_and_deleted": True,
            "aoi04_observed_extent_geometries_verified": False,
            "physical_event_model_admitted": False,
        }
        print(json.dumps(result, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
