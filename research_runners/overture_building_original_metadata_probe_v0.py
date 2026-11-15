# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded, read-only original provider metadata check for Overture global buildings.

Never downloads rows, geometries or full Parquet files; output is not model input.
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

SCHEMA = "opencatastrophe-overture-building-original-metadata-probe-v0"
HOST = "overturemaps-us-west-2.s3.us-west-2.amazonaws.com"
BUCKET = "overturemaps-us-west-2"
RELEASE = "2026-10-21.0"
PREFIX = f"release/{RELEASE}/theme=buildings/type=building/"
S3_NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"
PART = re.compile(r"part-\d{5}-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}-c\d{3}\.zstd\.parquet\Z")
MAX_LIST_BYTES = 32768
MAX_METADATA_PREFIX = 8192
MAX_FOOTER_BYTES = 2_000_000
MAX_OBJECT_BYTES = 2_000_000_000
MAX_RESULTS = 2


class ProbeError(ValueError):
    """Original metadata cannot be safely verified."""


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _default_fetch(request, limit):
    opener = build_opener(ProxyHandler({}), HTTPSHandler(), NoRedirects())
    with opener.open(request, timeout=15) as response:
        headers = {k.lower(): v for k, v in response.headers.items()}
        if headers.get("content-length") and int(headers["content-length"]) > limit:
            raise ProbeError("HTTP response exceeds byte cap")
        body = response.read(limit + 1)
        if len(body) > limit:
            raise ProbeError("HTTP response stream exceeds byte cap")
        return response.status, headers, body


def _request(url, *, range_header=None, etag=None):
    headers = {"Accept-Encoding": "identity", "User-Agent": "OpenCatastrophe-public-metadata-probe/0"}
    if range_header:
        headers["Range"] = range_header
    if etag:
        headers["If-Match"] = etag
    return Request(url, headers=headers, method="GET")


def _field(root, name):
    child = root.find(S3_NS + name)
    if child is None or child.text is None:
        raise ProbeError(f"missing S3 {name}")
    return child.text


def _listing(fetch):
    url = "https://" + HOST + "/?" + urlencode({
        "list-type": "2", "prefix": PREFIX, "max-keys": str(MAX_RESULTS)
    })
    status, _, body = fetch(_request(url), MAX_LIST_BYTES)
    if status != 200 or not body.startswith(b"<?xml") or len(body) > MAX_LIST_BYTES:
        raise ProbeError("invalid or oversized original listing")
    if b"<!DOCTYPE" in body or b"<!ENTITY" in body:
        raise ProbeError("unsafe XML entity")
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        raise ProbeError("malformed provider XML") from exc
    if root.tag != S3_NS + "ListBucketResult":
        raise ProbeError("wrong XML root")
    if _field(root, "Name") != BUCKET or _field(root, "Prefix") != PREFIX:
        raise ProbeError("unexpected bucket/prefix")
    if _field(root, "MaxKeys") != str(MAX_RESULTS):
        raise ProbeError("wrong listing max keys")
    truncated = _field(root, "IsTruncated")
    if truncated not in ("true", "false"):
        raise ProbeError("invalid listing truncation")
    objects = root.findall(S3_NS + "Contents")
    if not 1 <= len(objects) <= MAX_RESULTS:
        raise ProbeError("no bounded original source objects")
    found = []
    for item in objects:
        key = _field(item, "Key")
        if not key.startswith(PREFIX) or not PART.fullmatch(key[len(PREFIX):]):
            raise ProbeError("unexpected provider object key")
        size = _field(item, "Size")
        if not re.fullmatch(r"[1-9]\d*", size) or not 16 < int(size) <= MAX_OBJECT_BYTES:
            raise ProbeError("invalid original size")
        etag = _field(item, "ETag")
        if not re.fullmatch(r'"[a-f0-9]{32}(?:-\d+)?"', etag):
            raise ProbeError("invalid original object ETag")
        modified = _field(item, "LastModified")
        try:
            parsed = datetime.fromisoformat(modified.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ProbeError("invalid object last-modified timestamp") from exc
        if parsed.utcoffset() is None:
            raise ProbeError("non-timezone provider timestamp")
        found.append({"key": key, "size": int(size), "s3_etag": etag, "last_modified": modified})
    if len({obj["key"] for obj in found}) != len(found):
        raise ProbeError("duplicate source object")
    return found, truncated == "true"


def _range(fetch, obj, start, end):
    length = end - start + 1
    if start < 0 or length <= 0 or length > MAX_METADATA_PREFIX or end >= obj["size"]:
        raise ProbeError("out-of-bounds original byte request")
    url = "https://" + HOST + "/" + quote(obj["key"], safe="/=")
    status, h, body = fetch(
        _request(url, range_header=f"bytes={start}-{end}", etag=obj["s3_etag"]), length
    )
    if status != 206 or len(body) != length:
        raise ProbeError("provider did not honor exact bounded range")
    if h.get("content-range") != f"bytes {start}-{end}/{obj['size']}":
        raise ProbeError("invalid Content-Range")
    if h.get("content-length") != str(length):
        raise ProbeError("invalid Content-Length")
    if h.get("etag") != obj["s3_etag"]:
        raise ProbeError("provider ETag differs between listing and range")
    return body


class _Compact:
    """Small bounded Thrift CompactProtocol reader for Parquet FileMetaData header."""

    def __init__(self, data):
        self.data = data
        self.pos = 0

    def byte(self):
        if self.pos >= len(self.data):
            raise ProbeError("truncated Thrift metadata header")
        n = self.data[self.pos]
        self.pos += 1
        return n

    def varint(self):
        n = 0
        for i in range(10):
            b = self.byte()
            n |= (b & 127) << (7 * i)
            if b < 128:
                return n
        raise ProbeError("invalid Thrift varint")

    def zig(self):
        n = self.varint()
        return (n >> 1) ^ -(n & 1)

    def binary(self):
        n = self.varint()
        if n > 4096 or self.pos + n > len(self.data):
            raise ProbeError("invalid Thrift binary length")
        b = self.data[self.pos:self.pos + n]
        self.pos += n
        try:
            return b.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise ProbeError("non-UTF8 metadata field") from exc

    def value(self, kind, depth=0):
        if depth > 32:
            raise ProbeError("metadata nesting too deep")
        if kind in (1, 2):
            return kind == 1
        if kind == 3:
            return self.byte()
        if kind in (4, 5, 6):
            return self.zig()
        if kind == 7:
            return struct.unpack("<d", bytes(self.byte() for _ in range(8)))[0]
        if kind == 8:
            return self.binary()
        if kind in (9, 10):
            h = self.byte()
            count, child = h >> 4, h & 15
            if count == 15:
                count = self.varint()
            if count > 512:
                raise ProbeError("metadata collection too long")
            return [self.value(child, depth + 1) for _ in range(count)]
        if kind == 11:
            count = self.varint()
            if count > 512:
                raise ProbeError("metadata map too long")
            if count == 0:
                return []
            types = self.byte()
            return [(self.value(types >> 4, depth + 1),
                     self.value(types & 15, depth + 1)) for _ in range(count)]
        if kind == 12:
            return self.fields(depth + 1)
        raise ProbeError("unsupported Thrift field type")

    def fields(self, depth=0, *, stop_at=None):
        last = 0
        out = {}
        for _ in range(512):
            h = self.byte()
            if h == 0:
                return out
            delta, kind = h >> 4, h & 15
            key = last + delta if delta else self.zig()
            if key <= 0 or key in out:
                raise ProbeError("invalid or duplicate Thrift field")
            out[key] = self.value(kind, depth + 1)
            last = key
            if stop_at is not None and key == stop_at:
                return out
        raise ProbeError("too many Thrift metadata fields")


def _metadata_header(data):
    root = _Compact(data).fields(stop_at=3)
    if root.get(1) != 2 or type(root.get(3)) is not int or not 1 <= root[3] <= 10_000_000:
        raise ProbeError("unexpected original Parquet version or row count")
    entries = root.get(2)
    if type(entries) is not list or not 16 <= len(entries) <= 160:
        raise ProbeError("unexpected original building schema size")
    if entries[0].get(4) != "schema" or entries[0].get(5) != 24:
        raise ProbeError("unexpected Overture root schema")
    names = [e.get(4) for e in entries]
    if any(type(n) is not str or not n for n in names):
        raise ProbeError("invalid source schema field names")
    for required in ("id", "sources", "record_id", "geometry", "bbox", "height",
                     "num_floors", "xmin", "ymin", "xmax", "ymax"):
        if required not in names:
            raise ProbeError(f"missing source schema field: {required}")
    geometry = next(e for e in entries if e[4] == "geometry")
    if geometry.get(1) != 6:
        raise ProbeError("geometry not encoded as expected Parquet BYTE_ARRAY")
    return {"parquet_version": root[1], "rows_reported": root[3],
            "schema_field_count": len(entries), "nested_schema_field_names": names,
            "schema_types_verified": True}


def probe(*, fetch=_default_fetch):
    objects, truncated = _listing(fetch)
    evidence = []
    for obj in objects:
        first = _range(fetch, obj, 0, 3)
        suffix = _range(fetch, obj, obj["size"] - 8, obj["size"] - 1)
        if first != b"PAR1" or suffix[4:] != b"PAR1":
            raise ProbeError("invalid Parquet boundary magic")
        footer_len = struct.unpack("<I", suffix[:4])[0]
        if not 1 <= footer_len <= MAX_FOOTER_BYTES or footer_len >= obj["size"] - 12:
            raise ProbeError("unsafe original footer size")
        start = obj["size"] - footer_len - 8
        available = min(footer_len, MAX_METADATA_PREFIX)
        header = _range(fetch, obj, start, start + available - 1)
        meta = _metadata_header(header)
        evidence.append({**obj, "footer_length_bytes": footer_len,
                         "metadata_prefix_read_bytes": available,
                         **meta, "source_rows_decoded": False,
                         "whole_file_sha256_verified": False})
    return {"schema": SCHEMA, "dataset": "Overture Buildings",
            "release": RELEASE, "source_bucket": BUCKET, "source_prefix": PREFIX,
            "sampled_files": len(evidence), "listing_truncated": truncated,
            "rows_reported_in_sampled_files": sum(v["rows_reported"] for v in evidence),
            "original_object_evidence": evidence, "global_building_count_verified": False,
            "original_geometries_read": False, "independent_source_licensing_reviewed": False,
            "model_input_approved": False, "insured_tiv_estimated": False,
            "neon_production_modified": False,
            "note": "Only pinned release metadata was read; no deduplicated world building count or insured model input."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="Explicitly opt in to bounded public S3 original metadata requests")
    args = parser.parse_args(argv)
    if not args.live:
        print("BLOCKED: use explicit --live for original provider requests", file=sys.stderr)
        return 2
    try:
        result = probe()
    except (ProbeError, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
