# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Inspect official Hokota GitHub sample ZIP without putting provider bytes in Git.

The expected source blob SHA-1 is pinned from GitHub's immutable repository
tree, not from the archive filename. ZIP bytes are acquired externally by
a separately controlled workflow; this script makes no network request.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
import zipfile
from pathlib import Path

if __package__:
    from .plateau_citygml_original_zip_inventory_v0 import (
        MAX_ZIP_BYTES, ZipPreflightError, inspect_zip_file,
    )
    from .plateau_citygml_sample_structure_v0 import (
        MAX_GML_BYTES, CityGMLPreflightError, inspect_gml_bytes,
    )
else:
    from plateau_citygml_original_zip_inventory_v0 import (
        MAX_ZIP_BYTES, ZipPreflightError, inspect_zip_file,
    )
    from plateau_citygml_sample_structure_v0 import (
        MAX_GML_BYTES, CityGMLPreflightError, inspect_gml_bytes,
    )

PINNED_GIT_BLOB_SHA1 = "27be2d62ae68e3bae552c00f7635bbe47e871ea2"
PINNED_ZIP_BYTE_COUNT = 40347627
MAX_GML_SAMPLES = 3
READ_BLOCK = 1024 * 1024


class OfficialSampleError(ValueError):
    """An archive is not the pinned official Hokota test asset."""


def _pin_git_blob(path: Path) -> None:
    """Check the exact Git blob identity and stable regular-file metadata."""
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise OfficialSampleError("local sample file cannot be safely opened") from exc
    try:
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size != PINNED_ZIP_BYTE_COUNT:
                raise OfficialSampleError("sample does not match official pinned byte count")
            digest = hashlib.sha1()  # Git blob identity, NOT security signature.
            digest.update(f"blob {before.st_size}\0".encode("ascii"))
            total = 0
            while block := stream.read(READ_BLOCK):
                digest.update(block)
                total += len(block)
                if total > MAX_ZIP_BYTES:
                    raise OfficialSampleError("pinned sample exceeded local read ceiling")
            after = os.fstat(stream.fileno())
            identity = lambda x: (
                x.st_dev, x.st_ino, x.st_size, x.st_mtime_ns, x.st_ctime_ns
            )
            if total != before.st_size or identity(before) != identity(after):
                raise OfficialSampleError("sample changed during identity verification")
            if digest.hexdigest() != PINNED_GIT_BLOB_SHA1:
                raise OfficialSampleError("sample bytes do not match pinned Git blob identity")
    except OSError as exc:
        raise OfficialSampleError("local pinned sample read failed") from exc


def profile(path: Path) -> dict[str, object]:
    """Analyze one exact official GitHub asset, no source or sample bytes exposed."""
    _pin_git_blob(path)
    inventory = inspect_zip_file(path, expected_byte_count=PINNED_ZIP_BYTE_COUNT)
    sampled: list[dict[str, object]] = []
    candidates = 0
    # Only files previously accepted by the archive's global structural gate
    # are considered. ZIP member reads verify the selected member's CRC.
    try:
        with zipfile.ZipFile(path, "r") as archive:
            chosen = []
            for info in archive.infolist():
                nameparts = info.filename.lower().split("/")
                if not info.is_dir() and len(nameparts) >= 3 and (
                    any(nameparts[i:i + 2] == ["udx", "bldg"]
                        for i in range(len(nameparts) - 2))
                    and info.filename.lower().endswith(".gml")
                ):
                    candidates += 1
                    if 0 < info.file_size <= MAX_GML_BYTES:
                        chosen.append(info)
            for info in sorted(chosen, key=lambda x: (x.file_size, x.filename))[:MAX_GML_SAMPLES]:
                # zipfile.open verifies CRC at end of member read.
                with archive.open(info, "r") as handle:
                    raw = handle.read(MAX_GML_BYTES + 1)
                if len(raw) != info.file_size:
                    raise OfficialSampleError("selected CityGML member changed size")
                try:
                    receipt = inspect_gml_bytes(raw)
                    sampled.append({
                        "byte_count": len(raw),
                        "sha256": hashlib.sha256(raw).hexdigest(),
                        "structure_screen": "pass",
                        "building_count": receipt["building_element_count"],
                        "measured_height_count": receipt["measured_height_m_count"],
                        "lod0_ground_ring_screened_count": receipt.get(
                            "lod0_footprint_inline_ring_screened_count", 0
                        ),
                        "lod0_unresolved_count": receipt.get(
                            "lod0_geometry_unresolved_property_count", 0
                        ),
                        "provider_origin_beyond_git_blob": False,
                        "model_input_admitted": False,
                    })
                except CityGMLPreflightError:
                    sampled.append({
                        "byte_count": len(raw),
                        "sha256": hashlib.sha256(raw).hexdigest(),
                        "structure_screen": "blocked",
                        "building_count": None,
                        "model_input_admitted": False,
                    })
    except (OSError, RuntimeError, zipfile.BadZipFile, EOFError) as exc:
        raise OfficialSampleError("bounded member CRC inspection failed") from exc

    return {
        "upstream_repo": "Project-PLATEAU/SkylinesPLATEAU",
        "sample_subject": "Hokota 2020 (not Shinjuku 2024)",
        "git_blob_sha1": PINNED_GIT_BLOB_SHA1,
        "original_zip_sha256": inventory["local_zip_sha256"],
        "original_zip_byte_count": inventory["local_zip_byte_count"],
        "zip_total_member_count": inventory["zip_member_count"],
        "building_gml_member_count": inventory["building_citygml_file_count"],
        "building_member_candidates_count": candidates,
        "building_members_under_4mib_count": len(chosen),
        "sampled_gml_members_count": len(sampled),
        "samples": sampled,
        "sample_member_crc_checked_only": bool(sampled),
        "all_archive_member_crcs_checked": False,
        "all_building_geometries_checked": False,
        "archive_city_release_independently_proven": False,
        "municipality_and_year_in_archive_verified": False,
        "per_asset_license_review_completed": False,
        "cat_model_input_admitted": False,
        "no_source_bytes_committed": True,
        "provider_network_access_by_this_script": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        receipt = profile(args.input)
    except (ZipPreflightError, OfficialSampleError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
