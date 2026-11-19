#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One fixed HydroATLAS v1 Figshare article METADATA request, no GIS downloads.

All seven provider-listed archive/document file identities are pinned.
Figshare-supplied MD5 values are original provider metadata assertions, not
independently computed hashes of any 11+ GiB archives. Per-column HydroATLAS
licences (CC BY or ODbL) remain outside this metadata-only capability.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import ssl
import sys
from typing import Any, Callable
from urllib import error, request
from urllib.parse import urlsplit

from scripts.validate_source_access import validate_path

ROOT = Path(__file__).resolve().parents[1]
ACCESS_ID = "hydrosheds.hydroatlas.v1"
CONTRACT_PATH = ROOT / "access" / (ACCESS_ID + ".json")
ARTICLE_ID = 9890531
URL = "https://api.figshare.com/v2/articles/9890531"
MAX_BYTES = 131_072
TIMEOUT = 30
EXPECTED_SIZE = 12_027_317_200
REVIEWED_FILES = {
    20082110: ("HydroATLAS_TechDoc_v10.pdf", 1024082, "a1b20a273d3e04c55c9d673c7b18fac1"),
    20082113: ("BasinATLAS_Catalog_v10.pdf", 60341549, "2431a6fd7b381b0435133edcc23efecf"),
    20082122: ("RiverATLAS_Catalog_v10.pdf", 68738715, "a3eba9288783053eaaecd12ecaccb519"),
    20082137: ("BasinATLAS_Data_v10.gdb.zip", 2695658577, "69af94baee68da5a3f80f09e7b85bd04"),
    20087237: ("BasinATLAS_Data_v10_shp.zip", 4276492333, "ce5013294bdcb6f884ff6cdf1a1acae0"),
    20087321: ("RiverATLAS_Data_v10.gdb.zip", 2506480742, "f6f1cbf80b422710b78947137f7fd4e8"),
    20087486: ("RiverATLAS_Data_v10_shp.zip", 2418581202, "7a6d74226ce8fe6e7e0eb20e2abe71ee"),
}


class HydroATLASBlocked(ValueError):
    """Original provider source identity, policy or metadata changed."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise HydroATLASBlocked("Figshare redirect outside frozen reviewed route")


def verify_reviewed_contract(path: Path = CONTRACT_PATH) -> None:
    c = validate_path(path)
    r = c["rights_and_policy"]
    p = urlsplit(URL)
    if (c["access_id"] != ACCESS_ID or c["source_ids"] != [ACCESS_ID]
            or c["interface_type"] != "rest" or c["status"] != "probe_ready"
            or c["service_root"] != "https://api.figshare.com"
            or c["api_version"] != "v2"
            or c["access_scope"] != ["metadata"]
            or c["request_contract"]["allowed_operations"] != ["basin_river_v10_archive_metadata"]
            or c["request_contract"]["path_templates"] != ["/v2/articles/9890531"]
            or c["authentication"]["mode"] != "none"
            or c["probe_contract"]["mode"] != "metadata_get"
            or c["probe_contract"]["operation"] != "basin_river_v10_archive_metadata"
            or c["probe_contract"]["requires_credentials"] is not False
            or r["dataset_rights_status"] != "verified"
            or r["api_terms_status"] != "separate_reviewed"
            or r["commercial_automation_status"] != "allowed"
            or r["terms_url"] != "https://info.figshare.com/user-guide/figshare-policies/"
            or c["operational_constraints"]["max_probe_bytes"] != MAX_BYTES
            or c["operational_constraints"]["timeout_seconds"] != TIMEOUT
            or c["operational_constraints"]["retry_policy"] != "none"
            or p.scheme != "https" or p.netloc != "api.figshare.com"
            or p.path != "/v2/articles/9890531" or p.query or p.fragment
            or p.username or p.password):
        raise HydroATLASBlocked("HydroATLAS public metadata access contract changed")


def _strict_mapping(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in pairs:
        if k in out:
            raise HydroATLASBlocked("duplicate original Figshare JSON key")
        out[k] = v
    return out


def _reject_constant(value: str) -> None:
    raise HydroATLASBlocked("non-finite article metadata value")


def inspect_metadata(raw: bytes) -> dict[str, Any]:
    if not raw or len(raw) > MAX_BYTES:
        raise HydroATLASBlocked("original article metadata exceeds byte bound")
    try:
        item = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_strict_mapping,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HydroATLASBlocked("invalid original Figshare JSON metadata") from exc
    if type(item) is not dict:
        raise HydroATLASBlocked("expected single Figshare article object")
    doi = item.get("doi")
    if (type(item.get("id")) is not int or item["id"] != ARTICLE_ID
            or item.get("title") != "HydroATLAS version 1.0"
            or type(item.get("version")) is not int or item["version"] != 1
            or item.get("is_public") is not True
            or item.get("status") != "public"
            or type(doi) is not str
            or re.fullmatch(r"10\.6084/m9\.figshare\.9890531(?:\.v1)?", doi) is None):
        raise HydroATLASBlocked("HydroATLAS article/version public DOI identity drift")
    licence = item.get("license")
    if (type(licence) is not dict
            or licence.get("name") != "CC BY 4.0"
            or licence.get("url") != "https://creativecommons.org/licenses/by/4.0/"):
        raise HydroATLASBlocked("original Figshare article rights label changed")
    original_files = item.get("files")
    if type(original_files) is not list or len(original_files) != 7:
        raise HydroATLASBlocked("HydroATLAS source file inventory changed")
    observed = {}
    for f in original_files:
        if type(f) is not dict or type(f.get("id")) is not int:
            raise HydroATLASBlocked("missing original provider file identity")
        fid = f["id"]
        if fid not in REVIEWED_FILES or fid in observed:
            raise HydroATLASBlocked("unknown or duplicate HydroATLAS source file")
        name, size, expected_md5 = REVIEWED_FILES[fid]
        if (f.get("name") != name
                or type(f.get("size")) is not int or f["size"] != size
                or f.get("is_link_only") is not False
                or f.get("supplied_md5") != expected_md5
                or f.get("computed_md5") != expected_md5
                or f.get("download_url") != f"https://ndownloader.figshare.com/files/{fid}"):
            raise HydroATLASBlocked("provider published HydroATLAS file metadata drift")
        observed[fid] = size
    if (set(observed) != set(REVIEWED_FILES)
            or sum(observed.values()) != EXPECTED_SIZE
            or type(item.get("size")) is not int
            or item["size"] != EXPECTED_SIZE):
        raise HydroATLASBlocked("original HydroATLAS archive sizes changed")
    return {
        "article_id_verified": ARTICLE_ID,
        "article_version_verified": 1,
        "publication_license_label": "CC BY 4.0",
        "original_provider_file_metadata_verified": 7,
        "provider_declared_gis_zip_count": 4,
        "provider_declared_technical_pdf_count": 3,
        "provider_declared_total_asset_bytes": EXPECTED_SIZE,
        "original_file_md5_independently_recomputed": False,
        "original_asset_sha256_independently_verified": False,
        "per_attribute_ccby_odbl_licenses_scoped": False,
        "gis_archive_files_downloaded": 0,
        "pdf_files_downloaded": 0,
    }


def _open(req: request.Request, timeout: int):
    return request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    ).open(req, timeout=timeout)


def probe(*, open_request: Callable = _open,
          clock: Callable = lambda: datetime.now(timezone.utc)) -> dict[str, Any]:
    verify_reviewed_contract()
    req = request.Request(URL, method="GET", headers={
        "Accept": "application/json",
        "Accept-Encoding": "identity",
        "User-Agent": "OpenCatastrophe-data/0.1 (+https://github.com/pokekarten/OpenCatastrophe-data)",
    })
    try:
        with open_request(req, TIMEOUT) as response:
            if response.status != 200 or response.geturl() != URL:
                raise HydroATLASBlocked("Figshare original response identity/status failed")
            media = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media != "application/json":
                raise HydroATLASBlocked("Figshare original metadata MIME type changed")
            if response.headers.get("Content-Encoding", "identity").strip().lower() != "identity":
                raise HydroATLASBlocked("unreviewed provider content encoding")
            declared = response.headers.get("Content-Length")
            if declared is not None:
                if not declared.isascii() or not declared.isdecimal() or int(declared) > MAX_BYTES:
                    raise HydroATLASBlocked("invalid original provider response size")
            raw = response.read(MAX_BYTES + 1)
            if declared is not None and int(declared) != len(raw):
                raise HydroATLASBlocked("provider Content-Length mismatch")
    except HydroATLASBlocked:
        raise
    except (error.HTTPError, error.URLError, TimeoutError, OSError) as exc:
        raise HydroATLASBlocked("exact reviewed Figshare metadata request unavailable") from exc
    shape = inspect_metadata(raw)
    at = clock()
    if at.tzinfo is None or at.utcoffset() is None:
        raise HydroATLASBlocked("UTC-aware receipt time required")
    return {
        "profile": "oc-hydroatlas-figshare-v1-fixed-article-metadata-v0",
        "access_id": ACCESS_ID,
        "retrieval_utc": at.astimezone(timezone.utc).isoformat(),
        "request_sha256": hashlib.sha256(("GET " + URL).encode("ascii")).hexdigest(),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "response_bytes": len(raw),
        "access_contract_sha256": hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest(),
        "probe_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        **shape,
        "original_provider_payload_persisted": False,
        "scientific_hydroatlas_sample_admitted": False,
        "cat_model_input_approved": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="one original HydroATLAS Figshare metadata GET")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("network disabled by default; explicitly specify --live")
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
    except (HydroATLASBlocked, ValueError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
