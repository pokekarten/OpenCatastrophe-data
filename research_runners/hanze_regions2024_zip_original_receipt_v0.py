#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fetch HANZE v3.0.2-beta region ZIP original and emit metadata-only receipt."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import urllib.request
from urllib.parse import urlsplit

if __package__:
    from .hanze_regions2024_geometry_zip_audit_v0 import (
        SOURCE_URL, PUBLISHER_BYTES, inspect_hanze_region_geometry_zip,
    )
else:
    from hanze_regions2024_geometry_zip_audit_v0 import (
        SOURCE_URL, PUBLISHER_BYTES, inspect_hanze_region_geometry_zip,
    )


def fetch_zip_publisher() -> bytes:
    req = urllib.request.Request(SOURCE_URL, headers={
        "User-Agent": "OpenCatastropheHANZEOriginalGeometryAudit/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        url = urlsplit(response.geturl())
        if url.scheme != "https" or url.hostname != "zenodo.org":
            raise ValueError("region ZIP redirected outside source publisher")
        blob = response.read(PUBLISHER_BYTES + 1)
    if len(blob) != PUBLISHER_BYTES:
        raise ValueError("original regional ZIP size drift")
    return blob


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--expected-source-sha256", default=None)
    args = p.parse_args()
    result = inspect_hanze_region_geometry_zip(fetch_zip_publisher(),
                                               expected_sha256=args.expected_source_sha256)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True,
                                   allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
