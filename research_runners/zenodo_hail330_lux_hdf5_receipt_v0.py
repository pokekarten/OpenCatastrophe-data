# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline exact-source byte identity gate for external Luxembourg HDF5s.

Verifies publisher MD5, computes SHA256 and checks HDF5 signature. Does not
parse events, frequencies, centroids or damage. No admission or rights claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_H5_BYTES = 20 * 1024 * 1024
MAGIC = b"\x89HDF\r\n\x1a\n"
LUX_FILES = {
    "REF": ("hail_LUX_ref.h5", "1d66d63e84d44565c35461c0b8457a57"),
    "PGW": ("hail_LUX_PGW.h5", "2f92c82a25f73e33f93e494abbc2a610"),
}


class AssetError(ValueError):
    """External original asset cannot be trusted as publisher source bytes."""


def audit_file(path: Path, *, filename: str, md5: str) -> dict[str, object]:
    if not path.is_absolute() or path.name != filename or path.is_symlink() or not path.is_file():
        raise AssetError("missing, wrong-named or symlinked original file")
    real = path.resolve(strict=True)
    if real == ROOT or ROOT in real.parents:
        raise AssetError("original source bytes inside Git checkout")
    size = real.stat().st_size
    if not (len(MAGIC) <= size <= MAX_H5_BYTES):
        raise AssetError("original file outside bounded Luxembourg HDF5 size")
    hasher_md5, hasher_sha = hashlib.md5(), hashlib.sha256()  # noqa: S324 - publisher MD5 receipt
    with real.open("rb") as handle:
        if handle.read(len(MAGIC)) != MAGIC:
            raise AssetError("invalid HDF5 file signature")
        handle.seek(0)
        count = 0
        while True:
            chunk = handle.read(128 * 1024)
            if not chunk:
                break
            count += len(chunk)
            if count > MAX_H5_BYTES:
                raise AssetError("HDF5 stream exceeded byte cap")
            hasher_md5.update(chunk)
            hasher_sha.update(chunk)
    if count != size or hasher_md5.hexdigest() != md5:
        raise AssetError("publisher MD5 or file byte count mismatch")
    return {
        "filename": filename,
        "bytes": count,
        "publisher_md5_verified": True,
        "sha256_local": hasher_sha.hexdigest(),
        "hdf5_signature_checked": True,
        "hdf5_datasets_and_units_checked": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", required=True, type=Path, help="original outside-Git hail_LUX_ref.h5")
    parser.add_argument("--pgw", required=True, type=Path, help="original outside-Git hail_LUX_PGW.h5")
    args = parser.parse_args(argv)
    try:
        audited = [
            audit_file(args.ref, filename=LUX_FILES["REF"][0], md5=LUX_FILES["REF"][1]),
            audit_file(args.pgw, filename=LUX_FILES["PGW"][0], md5=LUX_FILES["PGW"][1]),
        ]
    except (AssetError, OSError) as exc:
        print(f"NOT_ADMITTED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "evidence_class": "ZENODO_LUX_ORIGINAL_HDF5_BYTE_IDENTITY_NO_SCIENTIFIC_ADMISSION",
        "source_doi": "10.5281/zenodo.17860440",
        "source_rights_approved": False,
        "event_time_frequency_checked": False,
        "files": audited,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
