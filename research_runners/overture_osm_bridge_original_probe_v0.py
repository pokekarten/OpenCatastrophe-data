# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded, read-only original AWS S3 metadata and Parquet-boundary probe.

No parquet rows, full provider objects, personal data or insurer exposures are
downloaded, retained or committed. This is source-access evidence only.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import re
import struct
import sys
from urllib.parse import quote, urlencode
from urllib.request import HTTPRedirectHandler, HTTPSHandler, ProxyHandler, Request, build_opener
import xml.etree.ElementTree as ET

SCHEMA = "opencatastrophe-overture-osm-bridge-original-probe-v0"
BUCKET = "overturemaps-us-west-2"
HOST = "overturemaps-us-west-2.s3.us-west-2.amazonaws.com"
RELEASE = "2026-10-21.0"
PREFIX = f"bridgefiles/{RELEASE}/provider=osm/theme=buildings/type=building/"
S3_NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"
PART = re.compile(r"part-\d{5}-[0-9a-f-]{36}\.c\d{3}\.snappy\.parquet\Z")
MAX_LIST_BYTES = 32_768
MAX_PART_BYTES = 1_000_000_000
MAX_FOOTER_BYTES = 131_072
MAX_RESULTS = 2


class ProbeError(ValueError):
    """Fail closed when original-source access evidence is inconsistent."""


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _default_fetch(request, limit):
    # No proxies, redirects, credentials or caller-selected URLs.
    opener = build_opener(ProxyHandler({}), HTTPSHandler(), NoRedirects())
    with opener.open(request, timeout=12) as response:
        headers = {k.lower(): v for k, v in response.headers.items()}
        if headers.get("content-length") and int(headers["content-length"]) > limit:
            raise ProbeError("response exceeds bounded byte budget")
        body = response.read(limit + 1)
        if len(body) > limit:
            raise ProbeError("stream exceeds bounded byte budget")
        return response.status, headers, body


def _request(url, *, byte_range=None):
    headers = {"User-Agent": "OpenCatastrophe-readonly-original-probe/0",
               "Accept-Encoding": "identity"}
    if byte_range is not None:
        headers["Range"] = byte_range
    return Request(url, headers=headers, method="GET")


def _text(node, tag):
    child = node.find(S3_NS + tag)
    if child is None or not child.text:
        raise ProbeError(f"missing S3 {tag}")
    return child.text


def _list_objects(fetch):
    url = "https://" + HOST + "/?" + urlencode({
        "list-type": "2", "prefix": PREFIX, "max-keys": str(MAX_RESULTS)
    })
    status, _, body = fetch(_request(url), MAX_LIST_BYTES)
    if status != 200 or not body.startswith(b"<?xml"):
        raise ProbeError("missing exact S3 XML listing")
    if b"<!DOCTYPE" in body or b"<!ENTITY" in body:
        raise ProbeError("XML entity declarations forbidden")
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        raise ProbeError("invalid S3 listing XML") from exc
    if root.tag != S3_NS + "ListBucketResult":
        raise ProbeError("wrong S3 XML root")
    if _text(root, "Name") != BUCKET or _text(root, "Prefix") != PREFIX:
        raise ProbeError("wrong S3 bucket or partition prefix")
    if _text(root, "MaxKeys") != str(MAX_RESULTS):
        raise ProbeError("unexpected S3 max-keys")
    truncated = _text(root, "IsTruncated")
    if truncated not in ("true", "false"):
        raise ProbeError("missing S3 truncation marker")
    objects = root.findall(S3_NS + "Contents")
    if not 1 <= len(objects) <= MAX_RESULTS:
        raise ProbeError("missing or excessive S3 sample objects")
    output = []
    for record in objects:
        key = _text(record, "Key")
        if not key.startswith(PREFIX) or not PART.fullmatch(key[len(PREFIX):]):
            raise ProbeError("unexpected S3 object key")
        raw_size = _text(record, "Size")
        if not re.fullmatch(r"[1-9]\d*", raw_size):
            raise ProbeError("invalid object length")
        size = int(raw_size)
        if size <= 12 or size > MAX_PART_BYTES:
            raise ProbeError("object length outside probe limits")
        modified = _text(record, "LastModified")
        try:
            datetime.fromisoformat(modified.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ProbeError("invalid original modification date") from exc
        etag = _text(record, "ETag")
        if not re.fullmatch(r'"[0-9a-f]{32}(?:-\d+)?"', etag):
            raise ProbeError("unrecognized ETag format")
        output.append({"key": key, "size": size, "last_modified": modified,
                       "s3_etag": etag})
    if len({obj["key"] for obj in output}) != len(output):
        raise ProbeError("duplicate source-object key")
    return output, truncated == "true"


def _range(fetch, obj, start, end):
    expected = end - start + 1
    url = "https://" + HOST + "/" + quote(obj["key"], safe="/=")
    status, headers, body = fetch(_request(url, byte_range=f"bytes={start}-{end}"), expected)
    if status != 206 or len(body) != expected:
        raise ProbeError("original object range request was not bounded HTTP 206")
    if headers.get("content-range") != f"bytes {start}-{end}/{obj['size']}":
        raise ProbeError("source Content-Range does not match listing")
    if headers.get("content-length") != str(expected):
        raise ProbeError("source response length is not exact")
    if headers.get("etag") != obj["s3_etag"]:
        raise ProbeError("original S3 ETag differs between list and byte-range probe")
    return body


def probe(*, fetch=_default_fetch):
    objects, truncated = _list_objects(fetch)
    inspected = []
    for obj in objects:
        header = _range(fetch, obj, 0, 3)
        tail = _range(fetch, obj, obj["size"] - 8, obj["size"] - 1)
        if header != b"PAR1" or tail[4:] != b"PAR1":
            raise ProbeError("original object lacks Parquet boundary magic")
        metadata_length = struct.unpack("<I", tail[:4])[0]
        if not 1 <= metadata_length <= MAX_FOOTER_BYTES or metadata_length >= obj["size"] - 12:
            raise ProbeError("unreasonable original Parquet footer metadata size")
        inspected.append({**obj, "parquet_magic_prefix_verified": True,
                          "parquet_magic_suffix_verified": True,
                          "footer_metadata_length_bytes": metadata_length,
                          "boundary_bytes_read": 12,
                          "whole_object_sha256_verified": False,
                          "parquet_schema_decoded": False,
                          "original_rows_read": False})
    return {"schema": SCHEMA, "provider": "Overture Maps Foundation",
            "dataset": "OpenStreetMap building GERS bridge",
            "release": RELEASE, "bucket": BUCKET, "prefix": PREFIX,
            "sampled_object_count": len(inspected), "listing_truncated": truncated,
            "objects": inspected, "full_object_downloaded": False,
            "rights_review_approved": False, "scientific_model_input_approved": False,
            "neon_import_performed": False,
            "note": "S3 list and 12 bytes per file verify original format/access only; ETags with multipart suffix are NOT full SHA256 or MD5 receipts."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="Opt in to one exact 2-key public S3 list and <=12 bytes per object")
    args = parser.parse_args(argv)
    if not args.live:
        print("BLOCKED: no network without explicit --live", file=sys.stderr)
        return 2
    try:
        result = probe()
    except (ProbeError, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
