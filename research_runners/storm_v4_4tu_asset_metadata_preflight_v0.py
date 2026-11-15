#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, fail-closed reconciliation of exact 4TU STORM v4 article + file-list metadata.

Research-only: a provider-published file inventory is NOT original track-byte
verification, an API access approval, a vulnerability function or model admission.
No network requests or provider bytes are written by this tool.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

SOURCE_ID = "storm.ibtracs.present-climate.v4"
DOI = "10.4121/12706085.v4"
# Candidate article UUID from the provider's versioned /datasets/<uuid>/4 link.
# It must independently agree with the actual v2 API article response.
ARTICLE_UUID = "01b2ebc7-7903-42ef-b46b-f43b9175dbf4"
MAX_ARTICLE_BYTES = 262_144
MAX_LIST_BYTES = 1_048_576
PROFILE = "storm-v4-4tu-original-asset-metadata-preflight-v0"
UUID = re.compile(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
MD5 = re.compile(r"[0-9a-f]{32}\Z")
EXPECTED = {
    "README.txt": (2322, "bcffee2371f9f2dacc16905b91f22202"),
    "Basins of STORM IBTrACS dataset.kml": (2612, "e45ddb50b5d9b7007564b77cfe21a34c"),
    "STORMV4.zip": (543251824, "d3e5647fa9c01b1ed33c33c0c930eb30"),
}


class Blocked(ValueError):
    """Unproven original release, corrupt metadata or competing asset identity."""


def _object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    record: dict[str, object] = {}
    for k, v in pairs:
        if k in record:
            raise Blocked("duplicate provider JSON key")
        record[k] = v
    return record


def _nonfinite(_: str) -> None:
    raise Blocked("non-finite JSON value")


def _finite(value: str) -> float:
    f = float(value)
    if not math.isfinite(f):
        raise Blocked("non-finite JSON float")
    return f


def _read(raw: bytes, sha: str, limit: int) -> object:
    if type(raw) is not bytes or not 0 < len(raw) <= limit:
        raise Blocked("missing or oversized original metadata bytes")
    if type(sha) is not str or not SHA.fullmatch(sha):
        raise Blocked("independently supplied SHA-256 must be lowercase hex")
    if hashlib.sha256(raw).hexdigest() != sha:
        raise Blocked("independent source response SHA-256 mismatch")
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_object,
                          parse_constant=_nonfinite, parse_float=_finite)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise Blocked("invalid UTF-8/JSON provider metadata") from exc


def _file_id(row: dict) -> str:
    ident = row.get("uuid", row.get("id"))
    if type(ident) is not str or not UUID.fullmatch(ident):
        raise Blocked("provider file UUID absent or invalid")
    # 4TU v2 file-list examples legitimately contain id=null alongside uuid.
    if row.get("id") is not None and row["id"] != ident:
        raise Blocked("conflicting file UUID aliases")
    return ident


def _download_link_safe(row: dict, ident: str) -> None:
    # Links remain documentary evidence and are NEVER fetched. Any unexpected
    # URL shape requires review rather than trusting an unreviewed CDN/redirect.
    url = row.get("download_url")
    if url is None:
        return
    if type(url) is not str:
        raise Blocked("malformed provider file URL")
    try:
        parts = urlsplit(url)
    except ValueError as exc:
        raise Blocked("invalid provider download URL") from exc
    expected_path = "/file/" + ARTICLE_UUID + "/" + ident
    if (parts.scheme != "https" or parts.netloc != "data.4tu.nl"
        or parts.path != expected_path or parts.query or parts.fragment
        or parts.username is not None or parts.password is not None):
        raise Blocked("unreviewed provider download URL shape")


def inspect(article_raw: bytes, article_sha256: str,
            file_list_raw: bytes, file_list_sha256: str) -> dict:
    article = _read(article_raw, article_sha256, MAX_ARTICLE_BYTES)
    rows = _read(file_list_raw, file_list_sha256, MAX_LIST_BYTES)
    if type(article) is not dict or type(rows) is not list:
        raise Blocked("expected v2 single article and unpaginated file list")
    if article.get("uuid") != ARTICLE_UUID:
        raise Blocked("4TU article UUID does not match v4 provider permalink")
    if type(article.get("doi")) is not str or article["doi"].casefold() != DOI:
        raise Blocked("wrong exact STORM v4 DOI")
    version = article.get("version")
    if type(version) is int:
        if version != 4:
            raise Blocked("wrong 4TU original article version")
    elif type(version) is str:
        if version.strip() != "4":
            raise Blocked("wrong 4TU original article version")
    else:
        raise Blocked("4TU version missing")
    title = article.get("title")
    if (type(title) is not str or
        "storm ibtracs" not in title.casefold() or
        "synthetic tropical cyclone tracks" not in title.casefold()):
        raise Blocked("wrong STORM dataset title")
    if len(rows) != len(EXPECTED):
        raise Blocked("STORM v4 original file count drift")
    result = []
    seen_names: set[str] = set()
    seen_uuids: set[str] = set()
    for row in rows:
        if type(row) is not dict:
            raise Blocked("invalid file-list item")
        name = row.get("name")
        if type(name) is not str or name not in EXPECTED or name in seen_names:
            raise Blocked("unreviewed/duplicated STORM v4 original filename")
        # A provider-side link-only or incomplete upload is not the original
        # 4TU physical track artifact, even if the name matches the source page.
        for flag in ("is_link_only", "is_incomplete"):
            state = row.get(flag, False)
            if type(state) is not bool or state:
                raise Blocked("source file is linked/incomplete or has invalid upload flags")
        size = row.get("size")
        expected_size, expected_md5 = EXPECTED[name]
        if type(size) is not int or size != expected_size:
            raise Blocked("provider file size does not match published v4 inventory")
        digests = [row[k] for k in ("md5", "computed_md5", "supplied_md5")
                   if k in row and row[k] is not None]
        if not digests or any(type(v) is not str or not MD5.fullmatch(v)
                              or v != expected_md5 for v in digests):
            raise Blocked("missing/contradictory published file MD5")
        fid = _file_id(row)
        if fid in seen_uuids:
            raise Blocked("duplicate file UUID")
        _download_link_safe(row, fid)
        seen_names.add(name)
        seen_uuids.add(fid)
        result.append({
            "filename": name, "provider_file_uuid": fid,
            "provider_declared_bytes": expected_size,
            "provider_declared_md5": expected_md5,
            "verified_original_sha256": False,
        })
    if seen_names != set(EXPECTED):
        raise Blocked("incomplete STORM v4 original file inventory")
    return {
        "profile": PROFILE,
        "source_id": SOURCE_ID,
        "doi": DOI,
        "provider_article_uuid": ARTICLE_UUID,
        "version": 4,
        "article_metadata_bytes": len(article_raw),
        "article_metadata_sha256": article_sha256,
        "file_list_metadata_bytes": len(file_list_raw),
        "file_list_metadata_sha256": file_list_sha256,
        "files": sorted(result, key=lambda x: x["filename"]),
        "provider_asset_metadata_reconciled": True,
        "provider_declared_md5_is_not_independent_original_sha256": True,
        "original_asset_bytes_acquired": False,
        "original_asset_sha256_verified": False,
        "source_licensing_approved_for_acquisition": False,
        "asset_download_authorized": False,
        "track_fields_verified_from_v4_original": False,
        "source_admission_extended": False,
        "model_input_authorized": False,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--article-json", required=True, type=Path)
    p.add_argument("--article-sha256", required=True)
    p.add_argument("--file-list-json", required=True, type=Path)
    p.add_argument("--file-list-sha256", required=True)
    args = p.parse_args()
    try:
        if args.article_json.resolve() == args.file_list_json.resolve():
            raise Blocked("article and file-list must be distinct original responses")
        with args.article_json.open("rb") as stream:
            article_raw = stream.read(MAX_ARTICLE_BYTES + 1)
        with args.file_list_json.open("rb") as stream:
            file_list_raw = stream.read(MAX_LIST_BYTES + 1)
        result = inspect(article_raw, args.article_sha256, file_list_raw, args.file_list_sha256)
    except (OSError, Blocked) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
