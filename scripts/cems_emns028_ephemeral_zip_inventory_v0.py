# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded one-shot EMSN028 archive acquisition for metadata-only receipt.

Original ZIP is never uploaded, committed, extracted or retained. Access
does not grant restricted/third-party rights or CAT model admission.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import tempfile
import urllib.error
import urllib.request
import zipfile
from scripts.cems_emns028_zip_head_receipt_v0 import (
    SOURCE_URL, OfficialRedirectOnly, assert_expected_destination,
)

EXPECTED_SIZE = 155_898_548  # live HTTP Content-Range, 2026-11-01
MAX_ARCHIVE_BYTES = 180_000_000
MAX_MEMBER_COUNT = 100_000
MAX_UNCOMPRESSED_BYTES = 20_000_000_000


def inspect_local(path: Path) -> dict:
    if not zipfile.is_zipfile(path):
        raise ValueError("not a ZIP central-directory archive")
    total_bytes = path.stat().st_size
    with path.open("rb") as src:
        digest = hashlib.file_digest(src, "sha256").hexdigest()
    with zipfile.ZipFile(path) as zf:
        members = zf.infolist()
        if not members or len(members) > MAX_MEMBER_COUNT:
            raise ValueError("unexpected archive member count")
        names = [item.filename for item in members]
        for name in names:
            pp = PurePosixPath(name)
            if not name or pp.is_absolute() or ".." in pp.parts or "\\" in name:
                raise ValueError("unsafe ZIP member path")
        total_uncompressed = sum(i.file_size for i in members)
        if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
            raise ValueError("declared uncompressed size over safety cap")
        exts = Counter(PurePosixPath(item.filename).suffix.lower()
                       for item in members if not item.is_dir())
        gdb_dirs = {part for item in names for part in PurePosixPath(item).parts
                    if part.lower().endswith(".gdb")}
        return {
            "receipt_kind": "CEMS_EMSN028_ZIP_COMPLETE_METADATA_V0",
            "source_url": SOURCE_URL,
            "archive_byte_size": total_bytes,
            "archive_sha256_from_this_download": digest,
            "archive_member_count": len(members),
            "declared_uncompressed_bytes": total_uncompressed,
            "gdb_directory_count": len(gdb_dirs),
            "member_extension_counts": dict(sorted(exts.items())),
            "aoi04_filename_hint_count": sum(
                "04" in name.lower() or "ponthierry" in name.lower()
                for name in names),
            "archive_structure_read_from_zip_central_directory": True,
            "member_payloads_decompressed": False,
            "archive_extracted": False,
            "aoi04_observed_extent_layer_verified": False,
            "historical_2016_buildings_verified": False,
            "activation_specific_reuse_rights_cleared": False,
            "insurer_tiv_or_loss_observed": False,
            "cat_model_admitted": False,
        }


def acquire_and_inspect() -> dict:
    opener = urllib.request.build_opener(OfficialRedirectOnly())
    req = urllib.request.Request(SOURCE_URL, method="GET", headers={
        "User-Agent": "OpenCatastrophe-Metadata-Research/0.1 (bounded archive, no redistribution)"})
    path = None
    try:
        with opener.open(req, timeout=90) as response:
            assert_expected_destination(response.geturl())
            if response.status != 200:
                raise ValueError("GET source returned non-200 response")
            header = response.headers.get("Content-Length")
            if header is not None and (
                not header.isdecimal() or int(header) > MAX_ARCHIVE_BYTES
            ):
                raise ValueError("refused unknown/oversized archive length")
            with tempfile.NamedTemporaryFile(
                prefix="cems-emns028-", suffix=".zip", delete=False
            ) as temp:
                path = Path(temp.name)
                total = 0
                while True:
                    piece = response.read(
                        min(1024 * 1024, MAX_ARCHIVE_BYTES + 1 - total))
                    if not piece:
                        break
                    total += len(piece)
                    if total > MAX_ARCHIVE_BYTES:
                        raise ValueError("archive exceeded strict byte limit")
                    temp.write(piece)
        if total != EXPECTED_SIZE:
            raise ValueError("archive version changed; review and explicitly repin")
        return inspect_local(path)
    finally:
        if path is not None:
            path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live", action="store_true",
        help="explicitly acquire <=180 MB to temporary runner storage")
    parser.add_argument("--local", type=Path,
                        help="inspect separately authorised local ZIP")
    args = parser.parse_args()
    if args.live == bool(args.local):
        parser.error("choose exactly one of --live / --local")
    try:
        result = acquire_and_inspect() if args.live else inspect_local(args.local)
    except (ValueError, OSError, urllib.error.HTTPError, urllib.error.URLError,
            zipfile.BadZipFile) as exc:
        # No presigned URL or provider byte leakage in error messages.
        print(json.dumps({
            "receipt_kind": "CEMS_EMSN028_ZIP_COMPLETE_METADATA_V0",
            "successful": False, "error_type": type(exc).__name__,
            "cat_model_admitted": False}, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
