# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded, original-host-only acquisition of eight version-specific Zenodo source files.

Only externally held temporary files are processed. No model admission or
raw-source byte persistence is implied by a successful receipt.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
from urllib.parse import urlsplit, quote
from urllib.request import Request, HTTPRedirectHandler, build_opener
from urllib.error import HTTPError, URLError

from research_runners.swiss_crop_hail_asset_preflight_v0 import (
    ASSETS, Blocked, inspect_local,
)

SOURCE_FILES = {
    "exposure_metadata": "metadata.csv",
    "damage_metadata": "metadata.csv",
    "exposure_zip": "data-files.zip",
    "damage_zip": "data-files.zip",
    "code_zip": "raphael-portmann/202403_crop_hail_damage_footprint-1.0.zip",
    "radar_metadata": "metadata.csv",
    "radar_meshs_h5": "hail_MESHS_CH_12_events_2017_2021.h5",
    "radar_poh_h5": "hail_POH_CH_12_events_2017_2021.h5",
}
MAX_TOTAL = 80_000_000
HOST = "zenodo.org"


def require_original_host(url: str) -> None:
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.hostname != HOST or
            parts.port not in (None, 443) or parts.username or parts.password):
        raise Blocked("redirect or source is not original zenodo.org HTTPS")


class OriginalOnlyRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        result = super().redirect_request(request, fp, code, msg, headers, newurl)
        if result is None:
            raise Blocked("unsupported HTTP redirect")
        require_original_host(result.full_url)
        return result


def source_url(asset: str) -> str:
    if asset not in SOURCE_FILES:
        raise Blocked("asset not explicitly allowlisted")
    record_id = ASSETS[asset][0]
    if asset == "code_zip":
        return f"https://{HOST}/api/records/12784190/files/raphael-portmann/202403_crop_hail_damage_footprint-1.0.zip/content"
    return f"https://{HOST}/records/{record_id}/files/{quote(SOURCE_FILES[asset])}?download=1"


def acquire_one(asset: str, target: Path, opener) -> int:
    if asset not in SOURCE_FILES:
        raise Blocked("asset not explicitly allowlisted")
    url = source_url(asset)
    require_original_host(url)
    maximum = ASSETS[asset][3]
    request = Request(
        url, headers={"Accept": "*/*",
                      "Accept-Encoding": "identity",
                      "User-Agent": "OpenCatastrophe-data-source-research/0.1"})
    try:
        with opener.open(request, timeout=30) as response:
            require_original_host(response.geturl())
            if getattr(response, "status", 200) != 200:
                raise Blocked("source response is not HTTP 200")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise Blocked("compressed HTTP transfer is not supported")
            header = response.headers.get("Content-Length")
            expected = None
            if header is not None:
                try:
                    expected = int(header)
                except (ValueError, TypeError) as exc:
                    raise Blocked("invalid Content-Length") from exc
                if not 0 < expected <= maximum:
                    raise Blocked("declared file size outside limit")
            total = 0
            with target.open("xb") as handle:
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > maximum:
                        raise Blocked("stream exceeded fixed byte limit")
                    handle.write(chunk)
            if total == 0 or (expected is not None and total != expected):
                raise Blocked("empty or truncated source file")
            return total
    except HTTPError as exc:
        raise Blocked(f"{asset}: original publisher returned HTTP {exc.code}") from exc
    except (URLError, OSError, TimeoutError) as exc:
        raise Blocked(f"{asset}: original publisher transport failed ({type(exc).__name__})") from exc


def verify(assets: tuple[str, ...], opener=None) -> dict[str, object]:
    if not assets or len(assets) != len(set(assets)) or any(a not in SOURCE_FILES for a in assets):
        raise Blocked("unknown or duplicate source selection")
    if sum(ASSETS[a][3] for a in assets) > MAX_TOTAL:
        raise Blocked("aggregate size ceiling exceeded")
    opener = opener or build_opener(OriginalOnlyRedirect())
    receipts = []
    with tempfile.TemporaryDirectory(prefix="swiss-hail-zenodo-original-") as tmp:
        for i, asset in enumerate(assets):
            target = Path(tmp) / f"original-{i}.bin"
            acquire_one(asset, target, opener)
            receipts.append(inspect_local(asset, target))
    return {
        "schema_version": "swiss-hail-zenodo-original-receipts-v0",
        "source_replay": "publisher-original-md5-verified",
        "receipts": receipts,
        "source_bytes_committed": False,
        "source_bytes_retained": False,
        "scientific_admission": False,
        "annual_event_frequency_validated": False,
        "insurer_loss_estimation_validated": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-radar", action="store_true")
    parser.add_argument("--include-archives", action="store_true", help="also verify original two crop data ZIPs")
    parser.add_argument("--include-code", action="store_true", help="verify original Zenodo software archive (never execute)")
    parser.add_argument("--code-only", action="store_true", help="diagnose exact software archive independently without other downloads")
    args = parser.parse_args()
    assets = ("exposure_metadata", "damage_metadata", "radar_metadata")
    if args.include_radar:
        assets += ("radar_meshs_h5", "radar_poh_h5")
    if args.include_archives:
        assets += ("exposure_zip", "damage_zip")
    if args.include_code:
        assets += ("code_zip",)
    if args.code_only:
        if args.include_code or args.include_radar or args.include_archives:
            parser.error("--code-only cannot be combined with other selections")
        assets = ("code_zip",)
    try:
        print(json.dumps(verify(assets), sort_keys=True))
    except Blocked as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
