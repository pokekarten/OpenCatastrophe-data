# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bind frozen DWD station-00003 metadata bytes to fail-closed temporal evidence.

This first-stage helper deliberately does not guess DWD metadata table columns,
encoding, or validity-date semantics. It reuses the repository ZIP inspector,
requires the frozen metadata identity/station/families, hashes the exact required
member contents, and reports temporal coverage as unverified until an
authoritative member-format contract is available.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import stat
import sys
import zipfile
from pathlib import Path, PurePosixPath

try:
    from scripts.inspect_dwd_metadata_zip import InspectionError, inspect_zip
except ModuleNotFoundError:  # direct execution via `python scripts/...`
    from inspect_dwd_metadata_zip import InspectionError, inspect_zip

EXPECTED_METADATA_SHA256 = "1703b0a7b464da98f83a9fe60ca8ad4725fa8fa9b53685c04491e1a2cfcbd657"
EXPECTED_STATION_ID = "00003"
MEASUREMENT_SHA256 = "8b4cf7e26efc8ddde431ca2cfc5251ef7588c9566b41e5490fa372ffa42689a4"
MEASUREMENT_WINDOW = {"start": "2010-01-01", "end": "2011-03-31"}
FAMILY_PREFIXES = {
    "geography": "metadaten_geographie",
    "equipment": "metadaten_geraete",
    "parameter": "metadaten_parameter",
}


class TemporalEvidenceError(ValueError):
    """Raised when frozen-evidence intake cannot be proven safely."""


def _family_for_member(name: str) -> str | None:
    basename = PurePosixPath(name).name.casefold()
    matches = []
    for family, prefix in FAMILY_PREFIXES.items():
        if basename.startswith(prefix):
            suffix = basename[len(prefix):]
            if not suffix or suffix[0] in "_.-":
                matches.append(family)
    if len(matches) > 1:
        raise TemporalEvidenceError(f"ambiguous provider metadata family: {name}")
    return matches[0] if matches else None


def _member_sha256(archive: zipfile.ZipFile, name: str) -> str:
    digest = hashlib.sha256()
    with archive.open(name, "r") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_bounded_regular_snapshot(path: Path, expected_byte_size: int) -> bytes:
    if type(expected_byte_size) is not int or expected_byte_size < 0:
        raise TemporalEvidenceError("inspected metadata byte size is invalid")
    if not hasattr(os, "O_NOFOLLOW"):
        raise TemporalEvidenceError("platform cannot enforce no-follow metadata ZIP reopen")

    flags = os.O_RDONLY | os.O_NOFOLLOW
    if hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY

    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise TemporalEvidenceError("metadata ZIP could not be reopened as a no-follow regular file") from exc

    try:
        reopened = os.fstat(fd)
        if not stat.S_ISREG(reopened.st_mode):
            raise TemporalEvidenceError("metadata ZIP reopened object is not a regular file")
        if reopened.st_size != expected_byte_size:
            raise TemporalEvidenceError("metadata byte size changed after ZIP inspection")

        chunks: list[bytes] = []
        remaining = expected_byte_size + 1
        while remaining:
            try:
                chunk = os.read(fd, min(1024 * 1024, remaining))
            except OSError as exc:
                raise TemporalEvidenceError("metadata ZIP bounded read failed") from exc
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        snapshot = b"".join(chunks)
        if len(snapshot) != expected_byte_size:
            raise TemporalEvidenceError("metadata byte size changed after ZIP inspection")
        return snapshot
    finally:
        os.close(fd)


def _collect(path: Path, expected_sha256: str, expected_station_id: str) -> dict[str, object]:
    try:
        inspection = inspect_zip(path)
    except InspectionError as exc:
        raise TemporalEvidenceError(str(exc)) from exc

    input_info = inspection["input"]
    observed = inspection["observed"]
    if input_info["sha256"] != expected_sha256:
        raise TemporalEvidenceError("metadata SHA-256 does not match the frozen asset")
    if observed["station_ids"] != [expected_station_id]:
        raise TemporalEvidenceError("ZIP station identity does not match frozen station 00003")

    required = set(FAMILY_PREFIXES)
    observed_required = required.intersection(observed["metadata_families"])
    if observed_required != required:
        missing = ", ".join(sorted(required - observed_required))
        raise TemporalEvidenceError(f"required provider metadata families missing: {missing}")

    snapshot = _read_bounded_regular_snapshot(path, input_info["byte_size"])
    snapshot_sha256 = hashlib.sha256(snapshot).hexdigest()
    if snapshot_sha256 != expected_sha256 or snapshot_sha256 != input_info["sha256"]:
        raise TemporalEvidenceError("metadata bytes changed after ZIP inspection")

    members_by_family: dict[str, list[dict[str, object]]] = {family: [] for family in sorted(required)}
    try:
        with zipfile.ZipFile(io.BytesIO(snapshot)) as archive:
            for member in inspection["zip"]["members"]:
                name = str(member["path"])
                family = _family_for_member(name)
                if family is None:
                    continue
                members_by_family[family].append({
                    "path": name,
                    "uncompressed_bytes": member["uncompressed_bytes"],
                    "crc32": member["crc32"],
                    "sha256": _member_sha256(archive, name),
                })
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        raise TemporalEvidenceError(str(exc)) from exc

    for family, members in members_by_family.items():
        if not members:
            raise TemporalEvidenceError(f"no provider-native member matched required family: {family}")
        members.sort(key=lambda item: str(item["path"]))

    return {
        "profile": "opencatastrophe-dwd-metadata-temporal-evidence-v1",
        "metadata_asset": {
            "filename": input_info["local_filename"],
            "byte_size": input_info["byte_size"],
            "sha256": input_info["sha256"],
            "station_id": expected_station_id,
        },
        "measurement_asset": {
            "sha256": MEASUREMENT_SHA256,
            "window": MEASUREMENT_WINDOW,
        },
        "required_family_members": members_by_family,
        "format_status": "blocked_member_format_spec_required",
        "temporal_coverage_status": "unverified",
        "blocker": (
            "Frozen member contents are byte-bound, but no authoritative contract currently defines "
            "their table columns, encoding, or validity-date semantics. Do not infer intervals."
        ),
        "claims": {
            "station_homogeneity_proven": False,
            "calibration_quality_proven": False,
            "hazard_fitness_proven": False,
            "model_validity_proven": False,
            "publication_authorized": False,
            "external_bytes_persisted": False,
        },
    }


def collect_temporal_evidence(path: Path) -> dict[str, object]:
    return _collect(path, EXPECTED_METADATA_SHA256, EXPECTED_STATION_ID)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_path", type=Path)
    args = parser.parse_args(argv)
    try:
        result = collect_temporal_evidence(args.zip_path)
    except TemporalEvidenceError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
