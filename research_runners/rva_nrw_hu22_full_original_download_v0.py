# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Explicit research-only full original Geobasis NRW HU 2022 ZIP acquisition.

Requires --live. Fetches exactly one 901,092,946-byte official ZIP into an
ephemeral local file; no third-party bytes are uploaded as a Github artifact.
Intended only for a bounded, reviewed one-shot CI job with sufficient runtime.
No personal insurer/customer information is requested or inferred.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from urllib.request import Request,urlopen

from rva_nrw_hu_full_zip_stratified_reservoir_v0 import (
    EXPECTED_ZIP_BYTES, EXPECTED_ORIGINAL_SHA256, SourceBlocked
)

ORIGINAL_URL=("https://www.opengeodata.nrw.de/produkte/geobasis/lk/hist/"
              "hist_hu_shp/2022_hu_EPSG4647_Shape.zip")
MAX_BYTES=EXPECTED_ZIP_BYTES
CHUNK=4*1024*1024


def download_original_once(path:Path,*,urlopen_=urlopen)->dict:
    # Path.exists() returns False for a dangling symlink. Reject it (and
    # symlinked directory ancestors) *before* the expensive provider GET.
    # Do not remove any pre-existing path when open("xb") fails.
    if (path.is_symlink() or path.exists() or not path.parent.is_dir()
            or any(ancestor.is_symlink() for ancestor in path.absolute().parents)):
        raise SourceBlocked("temporary original archive path must be new and not symlinked")
    created_here=False
    req=Request(ORIGINAL_URL,headers={
        "User-Agent":"OpenCatastrophe-official-NRW-source-integrity-research/0.1",
        "Accept":"application/zip,application/octet-stream"
    },method="GET")
    total=0
    digest=hashlib.sha256()
    try:
        with urlopen_(req,timeout=70) as response:
            if response.status!=200 or response.geturl()!=ORIGINAL_URL:
                raise SourceBlocked("official full-download HTTP status or origin changed")
            claimed=response.headers.get("Content-Length")
            if claimed!=str(MAX_BYTES):
                raise SourceBlocked("official original full archive Content-Length changed")
            with path.open("xb") as stream:
                created_here=True
                while True:
                    chunk=response.read(CHUNK)
                    if not chunk:
                        break
                    total+=len(chunk)
                    if total>MAX_BYTES:
                        raise SourceBlocked("original provider exceeded exact pinned byte budget")
                    digest.update(chunk)
                    stream.write(chunk)
        if total!=MAX_BYTES or path.stat().st_size!=MAX_BYTES:
            raise SourceBlocked("original provider archived 2022 ZIP truncated")
        if digest.hexdigest()!=EXPECTED_ORIGINAL_SHA256:
            raise SourceBlocked("original provider 2022 archive SHA256 identity drift")
        return {
            "schema":"NRW_HU_2022_SINGLE_FULL_ORIGINAL_PROVIDER_DOWNLOAD_V0",
            "provider_original_archive_url":ORIGINAL_URL,
            "official_source_sha256_computed_after_full_get":digest.hexdigest(),
            "official_archive_full_bytes":total,
            "original_archive_downloaded_into_ephemeral_location_only":True,
            "source_GFK_geometry_or_insurer_portfolio_verified_by_this_download":False,
            "source_derived_insured_locations":False,
            "native_cat_run":False,
        }
    except BaseException:
        # Interrupted 901 MB reads (including KeyboardInterrupt) must not
        # leave a partial provider archive behind. Only remove a file that
        # this exact invocation successfully created via exclusive open.
        if created_here:
            path.unlink(missing_ok=True)
        raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-original-zip",required=True,type=Path)
    p.add_argument("--live",action="store_true",
                   help="explicitly authorize up to 901MB one-shot provider original HTTPS GET")
    args=p.parse_args()
    if not args.live:
        p.exit(2,"BLOCKED: --live original full source download must be explicit\n")
    try:
        print(json.dumps(download_original_once(args.output_original_zip),sort_keys=True))
    except (OSError,SourceBlocked) as exc:
        p.exit(2,"NRW_2022_FULL_SOURCE_DOWNLOAD_BLOCKED: "+str(exc)+"\n")
    return 0


if __name__=="__main__":
    sys.exit(main())
