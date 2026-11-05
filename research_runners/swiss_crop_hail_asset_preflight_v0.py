# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, fail-closed local original-asset identity check for Swiss crop hail v1.

This never downloads, redistributes, decodes HDF5 model fields, or admits data.
Published Zenodo MD5 values are source-stated; independent SHA-256 is calculated
on operator-held files and reported only after exact MD5 and format checks pass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile


class Blocked(ValueError):
    """The local file cannot be identified as the exact expected source asset."""


# Publisher record IDs / v1 displayed file MD5 values (checked 2026-11-05).
# These identify files, not insurer exposures, independently cleared data
# rights, or an annual event model. Source pages: https://zenodo.org/records/{id}
ASSETS = {
    "exposure_zip": (11064756, "7db8df4c81ba5d1c1c7b8371cee53e15", "zip", 40_000_000),
    "exposure_metadata": (11064756, "05faf6e57f0b37130b3fc1c16190ed6c", "csv", 20_000),
    "damage_zip": (11064767, "c17119f9cd35f57ad49662a6f8ba1166", "zip", 8_000_000),
    "damage_metadata": (11064767, "0260ae2047e3fc02aa7ad88cf7911dda", "csv", 20_000),
    "radar_meshs_h5": (11064781, "f18b4e27342a374b08ca4c0ec8f90b5c", "hdf5", 9_000_000),
    "radar_poh_h5": (11064781, "3eee87725577ee3b74e0c33601dbfffa", "hdf5", 12_000_000),
    "radar_metadata": (11064781, "c4d4090b272eb9969a9045f93b2ce2c2", "csv", 20_000),
    "code_zip": (12784190, "96f72406c1464824434e66c54998be0e", "zip", 5_000_000),
}

EVENT_DATES = (
    "2017-06-27", "2017-07-08", "2017-08-01", "2019-06-15",
    "2019-06-30", "2019-07-01", "2021-06-20", "2021-06-21",
    "2021-06-28", "2021-07-12", "2021-07-13", "2021-07-24",
)


def _inspect_zip(path: Path) -> int:
    """Reject suspicious archive structure; do not unpack supplier content."""
    count, expanded_bytes, seen = 0, 0, set()
    try:
        with zipfile.ZipFile(path) as archive:
            for entry in archive.infolist():
                name = entry.filename.replace("\\", "/")
                p = PurePosixPath(name)
                if (not name or name.startswith("/") or ".." in p.parts or
                        any(part == "" for part in name.rstrip("/").split("/")) or
                        ":" in p.parts[0] or name in seen):
                    raise Blocked("unsafe or duplicate ZIP member")
                seen.add(name)
                mode = entry.external_attr >> 16
                if stat.S_ISLNK(mode) or entry.flag_bits & 1:
                    raise Blocked("symlink or encrypted ZIP member")
                expanded_bytes += entry.file_size
                if (expanded_bytes > 256_000_000 or
                        entry.file_size > 80_000_000 or
                        entry.file_size > 200 * max(entry.compress_size, 1)):
                    raise Blocked("ZIP decompression bound exceeded")
                count += 1
                if count > 5000:
                    raise Blocked("ZIP member count limit exceeded")
    except (OSError, zipfile.BadZipFile, EOFError) as exc:
        raise Blocked("invalid ZIP container") from exc
    if count == 0:
        raise Blocked("empty ZIP container")
    return count


def inspect_local(asset: str, path: Path) -> dict[str, object]:
    """Verify one operator-held file, without making a network request."""
    if asset not in ASSETS:
        raise Blocked("unrecognized source asset")
    record, published_md5, kind, maximum = ASSETS[asset]
    if path.is_symlink() or not path.is_file():
        raise Blocked("source asset must be a regular non-symlink file")
    initial = path.stat()
    if not (0 < initial.st_size <= maximum):
        raise Blocked("source asset exceeds fixed size bound or is empty")
    md5 = hashlib.md5(usedforsecurity=False)
    sha256 = hashlib.sha256()
    try:
        with path.open("rb") as source:
            signature = source.read(8)
            source.seek(0)
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                md5.update(chunk)
                sha256.update(chunk)
    except OSError as exc:
        raise Blocked("source asset unreadable") from exc
    final = path.stat()
    if ((initial.st_size, initial.st_mtime_ns, initial.st_ino) !=
            (final.st_size, final.st_mtime_ns, final.st_ino)):
        raise Blocked("source asset changed during preflight")
    if md5.hexdigest() != published_md5:
        raise Blocked("source asset differs from source-published MD5")
    if kind == "hdf5" and signature != b"\x89HDF\r\n\x1a\n":
        raise Blocked("expected HDF5 file signature absent")
    if kind == "csv" and (b"\x00" in signature or b"," not in path.read_bytes()[:8192]):
        raise Blocked("expected CSV metadata header absent")
    zip_members = _inspect_zip(path) if kind == "zip" else None
    return {
        "asset": asset, "record_id": record, "record_version": "v1" if record != 12784190 else "1.0",
        "file_size": initial.st_size, "publisher_md5_verified": True,
        "sha256": sha256.hexdigest(), "format": kind, "zip_member_count": zip_members,
        "event_count_context_only": len(EVENT_DATES),
        "source_bytes_committed": False, "admitted_for_cat_model": False,
        "insurer_losses_validated": False, "annual_event_frequency_validated": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", required=True, choices=sorted(ASSETS))
    parser.add_argument("--file", required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(inspect_local(args.asset, args.file), sort_keys=True))
    except (Blocked, OSError) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
