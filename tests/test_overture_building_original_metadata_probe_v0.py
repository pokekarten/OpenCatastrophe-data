# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests for original Overture building Parquet metadata access."""
import struct
import unittest
from urllib.parse import urlsplit
from xml.sax.saxutils import escape
from research_runners.overture_building_original_metadata_probe_v0 import (
    BUCKET, PREFIX, ProbeError, SCHEMA, _metadata_header, main, probe,
)

KEYS = [
    PREFIX + "part-00000-85375c54-5dfb-57c7-b21d-8b5e5245ad06-c000.zstd.parquet",
    PREFIX + "part-00001-25a868c6-9ddc-5e1c-8e0e-8286ae2005d9-c000.zstd.parquet",
]
SIZES = [533137080, 533341551]
FOOTERS = [668264, 703774]
ROWS = [5002132, 5001978]
ETAG = '"' + 'a' * 32 + '-8"'


def vint(n):
    out = bytearray()
    while n >= 128:
        out.append((n & 127) | 128)
        n >>= 7
    out.append(n)
    return bytes(out)


def zig(n):
    return vint((n << 1) ^ (n >> 63))


def field(name, children=None, physical=None):
    b = bytearray()
    last = 0
    if physical is not None:
        b.append(0x15)
        b.extend(zig(physical))
        last = 1
    b.append(((4-last) << 4) | 8)
    b.extend(vint(len(name)))
    b.extend(name.encode())
    if children is not None:
        b.append(0x15)
        b.extend(zig(children))
    b.append(0)
    return b


def metadata(rows=5002132, remove=None, wrong_geom=False):
    names = ("id", "sources", "record_id", "geometry", "bbox", "height", "num_floors",
             "xmin", "ymin", "xmax", "ymax", "names", "primary", "common",
             "is_underground", "roof_height")
    if remove:
        names = tuple(x for x in names if x != remove) + ("other_" + remove,)
    elements = [field("schema", children=24)]
    elements += [field(n, physical=5 if n == "geometry" and wrong_geom else 6) for n in names]
    out = bytearray([0x15])
    out.extend(zig(2))
    out.append(0x19)
    out.append(0xfc)
    out.extend(vint(len(elements)))
    for element in elements:
        out.extend(element)
    out.append(0x16)
    out.extend(zig(rows))
    out.append(0)
    return bytes(out)


class Fixture:
    def __init__(self):
        self.keys = KEYS.copy()
        self.sizes = SIZES.copy()
        self.footers = FOOTERS.copy()
        self.rows = ROWS.copy()
        self.list_status = 200
        self.range_status = 206
        self.list_prefix = PREFIX
        self.list_bucket = BUCKET
        self.truncated = "true"
        self.range_etag = ETAG
        self.length_extra = 0
        self.range_header_bad = False
        self.bad_start = False
        self.bad_end = False
        self.bad_geometry = False
        self.missing_field = None
        self.bad_rows = False
        self.calls = []

    def xml(self):
        items = ''.join(
            '<Contents><Key>' + escape(key) + '</Key><Size>' + str(size) + '</Size>'
            '<ETag>' + escape(ETAG) + '</ETag><LastModified>2026-10-21T17:38:24.000Z</LastModified></Contents>'
            for key, size in zip(self.keys, self.sizes)
        )
        return ('<?xml version="1.0" encoding="UTF-8"?>'
                '<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">'
                '<Name>' + self.list_bucket + '</Name><Prefix>' + self.list_prefix + '</Prefix>'
                '<MaxKeys>2</MaxKeys><IsTruncated>' + self.truncated + '</IsTruncated>'
                + items + '</ListBucketResult>').encode()

    def __call__(self, req, limit):
        url = urlsplit(req.full_url)
        if url.query:
            return self.list_status, {}, self.xml()
        key = url.path.lstrip("/")
        idx = self.keys.index(key)
        size = self.sizes[idx]
        raw_range = req.get_header("Range")
        self.calls.append(raw_range)
        if req.get_header("If-match") != ETAG:
            raise AssertionError("source ETag not pinned")
        if raw_range == "bytes=0-3":
            start, end = 0, 3
            body = b"WRNG" if self.bad_start else b"PAR1"
        elif raw_range == f"bytes={size-8}-{size-1}":
            start, end = size - 8, size - 1
            body = struct.pack("<I", self.footers[idx]) + (b"WRNG" if self.bad_end else b"PAR1")
        else:
            start = size - self.footers[idx] - 8
            end = start + 8192 - 1
            if raw_range != f"bytes={start}-{end}":
                raise AssertionError("unexpected metadata range")
            body = metadata(-1 if self.bad_rows else self.rows[idx], remove=self.missing_field,
                            wrong_geom=self.bad_geometry).ljust(8192, b"\0")
        if len(body) > limit:
            raise AssertionError("response unbounded")
        headers = {"content-range": f"bytes {start}-{end if not self.range_header_bad else end+1}/{size}",
                   "content-length": str(len(body) + self.length_extra), "etag": self.range_etag}
        return self.range_status, headers, body


class ProbeTests(unittest.TestCase):
    def test_original_metadata_contract(self):
        f = Fixture()
        result = probe(fetch=f)
        self.assertEqual(result["rows_reported_in_sampled_files"], 10004110)
        self.assertEqual([x["rows_reported"] for x in result["original_object_evidence"]], ROWS)
        self.assertEqual(result["sampled_files"], 2)
        self.assertEqual(len(f.calls), 6)
        self.assertTrue(result["listing_truncated"])
        self.assertEqual(result["schema"], SCHEMA)
        for key in ("model_input_approved", "global_building_count_verified",
                    "original_geometries_read", "independent_source_licensing_reviewed",
                    "insured_tiv_estimated", "neon_production_modified"):
            self.assertIs(result[key], False)

    def test_wrong_prefix(self):
        f = Fixture();f.list_prefix = PREFIX.replace("type=building", "type=building_part")
        with self.assertRaises(ProbeError):probe(fetch=f)

    def test_wrong_bucket(self):
        f = Fixture();f.list_bucket = "other"
        with self.assertRaises(ProbeError):probe(fetch=f)

    def test_wrong_object_key(self):
        f = Fixture();f.keys[1] = PREFIX + "evil.parquet"
        with self.assertRaises(ProbeError):probe(fetch=f)

    def test_duplicate_object_key(self):
        f = Fixture();f.keys[1] = f.keys[0]
        with self.assertRaises(ProbeError):probe(fetch=f)

    def test_empty_listing(self):
        f = Fixture();f.keys = [];f.sizes = []
        with self.assertRaises(ProbeError):probe(fetch=f)

    def test_bad_truncation_marker(self):
        f = Fixture();f.truncated = "no"
        with self.assertRaises(ProbeError):probe(fetch=f)

    def test_bad_parquet_header(self):
        f = Fixture();f.bad_start = True
        with self.assertRaises(ProbeError):probe(fetch=f)

    def test_bad_parquet_tail(self):
        f = Fixture();f.bad_end = True
        with self.assertRaises(ProbeError):probe(fetch=f)

    def test_bad_range_status(self):
        f = Fixture();f.range_status = 200
        with self.assertRaises(ProbeError):probe(fetch=f)

    def test_bad_content_range(self):
        f = Fixture();f.range_header_bad = True
        with self.assertRaises(ProbeError):probe(fetch=f)

    def test_bad_etag(self):
        f = Fixture();f.range_etag = '"' + 'f' * 32 + '-8"'
        with self.assertRaises(ProbeError):probe(fetch=f)

    def test_bad_content_length(self):
        f = Fixture();f.length_extra = 1
        with self.assertRaises(ProbeError):probe(fetch=f)

    def test_large_footer(self):
        f = Fixture();f.footers[0] = 3_000_000
        with self.assertRaises(ProbeError):probe(fetch=f)

    def test_missing_critical_column(self):
        f = Fixture();f.missing_field = "geometry"
        with self.assertRaises(ProbeError):probe(fetch=f)

    def test_wrong_geometry_type(self):
        f = Fixture();f.bad_geometry = True
        with self.assertRaises(ProbeError):probe(fetch=f)

    def test_negative_row_count(self):
        f = Fixture();f.bad_rows = True
        with self.assertRaises(ProbeError):probe(fetch=f)

    def test_truncated_thrift(self):
        self.assertEqual(_metadata_header(metadata())["rows_reported"], 5002132)
        with self.assertRaises(ProbeError):_metadata_header(b"junk")

    def test_offline_by_default(self):
        self.assertEqual(main([]), 2)


if __name__ == "__main__":
    unittest.main()
