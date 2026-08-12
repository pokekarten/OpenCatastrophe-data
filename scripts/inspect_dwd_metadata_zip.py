# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Inspect one externally supplied DWD metadata ZIP without admitting its bytes.

The tool is deliberately read-only and dependency-free. It records exact local
input byte identity and a deterministic inventory of safe ZIP members. It does
not download data, interpret scientific fitness, or change repository admission
state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import BinaryIO

MAX_MEMBERS = 10_000
MAX_MEMBER_BYTES = 256 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED_BYTES = 1024 * 1024 * 1024
STATION_ID_RE = re.compile(r"(?<!\d)(\d{5})(?!\d)")
WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:/")
METADATA_FAMILIES = (
    "equipment",
    "geography",
    "instrument",
    "measurement",
    "parameter",
    "station",
)
DWD_PROVIDER_METADATA_FAMILIES = (
    ("metadaten_geographie", "geography"),
    ("metadaten_geraete", "equipment"),
    ("metadaten_parameter", "parameter"),
)


class InspectionError(ValueError):
    """Raised when an input cannot be inspected safely and deterministically."""


def _sha256_stream(handle: BinaryIO) -> str:
    digest = hashlib.sha256()
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest()


def _safe_member_name(name: str) -> str:
    if not name or "\\" in name or "\x00" in name:
        raise InspectionError("ZIP member path must be a non-empty POSIX path")
    candidate = name[:-1] if name.endswith("/") else name
    if not candidate or name.startswith("/") or WINDOWS_DRIVE_RE.match(candidate):
        raise InspectionError(f"unsafe ZIP member path: {name}")
    if any(part in {"", ".", ".."} for part in candidate.split("/")):
        raise InspectionError(f"unsafe ZIP member path: {name}")
    return name


def _is_symlink(info: zipfile.ZipInfo) -> bool:
    unix_mode = (info.external_attr >> 16) & 0xFFFF
    return stat.S_ISLNK(unix_mode)


def _metadata_family(name: str) -> str | None:
    lowered = PurePosixPath(name).name.casefold()
    provider_matches = [
        (token, normalized)
        for token, normalized in DWD_PROVIDER_METADATA_FAMILIES
        if token in lowered
    ]
    if len(provider_matches) > 1:
        raise InspectionError(f"ambiguous DWD metadata family in ZIP member: {name}")
    if provider_matches:
        token, normalized = provider_matches[0]
        if lowered.startswith(token):
            suffix = lowered[len(token):]
            if not suffix or suffix[0] in "_.-":
                return normalized
        return "metadata"
    for family in METADATA_FAMILIES:
        if family in lowered:
            return family
    if "meta" in lowered:
        return "metadata"
    return None


def inspect_zip(path: Path) -> dict[str, object]:
    try:
        if path.is_symlink() or not path.is_file():
            raise InspectionError("input must be a regular file, not a symlink")

        with path.open("rb") as handle:
            handle.seek(0, 2)
            byte_size = handle.tell()
            handle.seek(0)
            digest = _sha256_stream(handle)
            handle.seek(0)

            with zipfile.ZipFile(handle) as archive:
                infos = archive.infolist()
                if len(infos) > MAX_MEMBERS:
                    raise InspectionError(f"ZIP contains more than {MAX_MEMBERS} members")

                seen: set[str] = set()
                members: list[dict[str, object]] = []
                total_uncompressed = 0
                station_ids: set[str] = set()
                metadata_families: set[str] = set()

                for info in infos:
                    name = _safe_member_name(info.filename)
                    if name in seen:
                        raise InspectionError(f"duplicate ZIP member path: {name}")
                    seen.add(name)
                    if _is_symlink(info):
                        raise InspectionError(f"ZIP symlink member is not allowed: {name}")
                    if info.file_size < 0 or info.file_size > MAX_MEMBER_BYTES:
                        raise InspectionError(f"ZIP member exceeds safe size bound: {name}")
                    total_uncompressed += info.file_size
                    if total_uncompressed > MAX_TOTAL_UNCOMPRESSED_BYTES:
                        raise InspectionError("ZIP exceeds total uncompressed size bound")

                    station_ids.update(STATION_ID_RE.findall(PurePosixPath(name).name))
                    family = _metadata_family(name)
                    if family is not None:
                        metadata_families.add(family)
                    members.append(
                        {
                            "path": name,
                            "compressed_bytes": info.compress_size,
                            "uncompressed_bytes": info.file_size,
                            "crc32": f"{info.CRC:08x}",
                        }
                    )

            handle.seek(0)
            if _sha256_stream(handle) != digest:
                raise InspectionError("input bytes changed during inspection")
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile, InspectionError) as exc:
        if isinstance(exc, InspectionError):
            raise
        raise InspectionError(str(exc)) from exc

    members.sort(key=lambda item: str(item["path"]))
    return {
        "profile": "opencatastrophe-dwd-metadata-zip-inspection-v1",
        "input": {
            "local_filename": path.name,
            "byte_size": byte_size,
            "sha256": digest,
        },
        "zip": {
            "member_count": len(members),
            "total_uncompressed_bytes": total_uncompressed,
            "members": members,
        },
        "observed": {
            "station_ids": sorted(station_ids),
            "metadata_families": sorted(metadata_families),
        },
        "claims": {
            "admission_changed": False,
            "scientific_fitness_assessed": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_path", type=Path)
    args = parser.parse_args(argv)
    try:
        result = inspect_zip(args.zip_path)
    except InspectionError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
