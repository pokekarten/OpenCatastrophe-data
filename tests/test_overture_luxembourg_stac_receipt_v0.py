# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline mocked real STAC/S3 response-contract tests; no provider network."""
import json
import struct
import unittest

from research_runners.overture_luxembourg_stac_receipt_v0 import (
    EXPECTED_BYTES, EXPECTED_ROWS, EXPECTED_ROW_GROUPS_STAC,
    METADATA_PREFIX_BYTES, S3_URL, STAC_URL, ProbeError, main, probe,
)
from tests.test_overture_building_original_metadata_probe_v0 import field, vint, zig


def footer_header(rows=EXPECTED_ROWS):
    names = [
        "id", "sources", "record_id", "geometry", "bbox", "height", "num_floors",
        "xmin", "ymin", "xmax", "ymax", "names", "primary", "common",
        "is_underground", "roof_height"
    ] + [f"synthetic_nested_{i}" for i in range(46)]
    elements = [field("schema", children=24)]
    elements += [field(name, physical=6) for name in names]
    assert len(elements) == 63
    raw = bytearray([0x15])
    raw.extend(zig(2))
    raw.extend([0x19, 0xfc])
    raw.extend(vint(len(elements)))
    for element in elements:
        raw.extend(element)
    raw.append(0x16)
    raw.extend(zig(rows))
    raw.append(0)
    assert len(raw) <= METADATA_PREFIX_BYTES
    return bytes(raw).ljust(METADATA_PREFIX_BYTES, b"\0")


class Fake:
    def __init__(self):
        self.item = {
            "type": "Feature", "id": "00226", "stac_version": "1.1.0",
            "bbox": [3.8891329765319824, 48.707069396972656,
                     6.534274101257324, 50.80072784423828],
            "properties": {
                "datetime": "2026-10-21T00:00:00Z",
                "num_rows": EXPECTED_ROWS,
                "num_row_groups": EXPECTED_ROW_GROUPS_STAC
            },
            "assets": {"aws": {"href": S3_URL, "file:size": EXPECTED_BYTES}}
        }
        self.bad_stac_json = None
        self.status = 206
        self.footer_length = 1461640
        self.parquet_rows = EXPECTED_ROWS
        self.bad_first = False
        self.bad_last = False
        self.inconsistent_etag = False
        self.bad_content_range = False
        self.calls = []

    def __call__(self, request, limit):
        url = request.full_url
        if url == STAC_URL:
            body = (self.bad_stac_json if self.bad_stac_json is not None else
                    json.dumps(self.item).encode())
            if len(body) > limit:
                raise AssertionError("oversized fixture")
            return 200, {"content-length": str(len(body))}, body
        if url != S3_URL:
            raise AssertionError("unexpected remote source")
        range_value = request.get_header("Range")
        if range_value is None:
            raise AssertionError("original S3 read must be a byte range")
        self.calls.append(range_value)
        if range_value == "bytes=0-3":
            start, end = 0, 3
            body = b"NOPE" if self.bad_first else b"PAR1"
        elif range_value == f"bytes={EXPECTED_BYTES-8}-{EXPECTED_BYTES-1}":
            start, end = EXPECTED_BYTES - 8, EXPECTED_BYTES - 1
            body = struct.pack("<I", self.footer_length) + (
                b"NOPE" if self.bad_last else b"PAR1"
            )
        else:
            start = EXPECTED_BYTES - self.footer_length - 8
            end = start + METADATA_PREFIX_BYTES - 1
            if range_value != f"bytes={start}-{end}":
                raise AssertionError("unbounded/unknown range")
            body = footer_header(self.parquet_rows)
        if len(body) > limit:
            raise AssertionError("range exceeded budget")
        etag = '"' + ("b" if self.inconsistent_etag and len(self.calls) > 1 else "a") * 32 + '-8"'
        headers = {
            "content-range": f"bytes {start}-{end + int(self.bad_content_range)}/{EXPECTED_BYTES}",
            "content-length": str(len(body)), "etag": etag
        }
        return self.status, headers, body


class OriginalLuxembourgStacTests(unittest.TestCase):
    def test_exact_provider_contract_and_no_admission(self):
        fake = Fake()
        out = probe(fetch=fake)
        self.assertEqual(out["source_object_reported_rows_not_luxembourg_rows"], EXPECTED_ROWS)
        self.assertEqual(out["source_stac_reported_row_groups_not_parsed"], 256)
        self.assertEqual(out["parquet_footer_length_bytes"], 1461640)
        self.assertEqual(out["source_parquet_schema_elements"], 63)
        self.assertEqual(len(fake.calls), 3)
        self.assertEqual(sum(int(z.split("-")[-1])-int(z.split("-")[0].split("=")[-1])+1
                             for z in fake.calls), 8204)
        for k in ("original_feature_data_read", "file_sha256_verified",
                  "gers_identity_verified", "source_rights_approved",
                  "national_building_count_measured",
                  "insurer_exposure_approved", "cat_model_input_approved"):
            self.assertIs(out[k], False)

    def test_reject_wrong_stac_identity(self):
        f = Fake()
        f.item["id"] = "00225"
        with self.assertRaises(ProbeError):
            probe(fetch=f)

    def test_reject_stac_release_change(self):
        f = Fake()
        f.item["properties"]["datetime"] = "2026-11-01T00:00:00Z"
        with self.assertRaises(ProbeError):
            probe(fetch=f)

    def test_reject_stac_row_change(self):
        f = Fake()
        f.item["properties"]["num_rows"] -= 1
        with self.assertRaises(ProbeError):
            probe(fetch=f)

    def test_reject_stac_row_group_change(self):
        f = Fake()
        f.item["properties"]["num_row_groups"] = 255
        with self.assertRaises(ProbeError):
            probe(fetch=f)

    def test_reject_file_not_intersecting_city(self):
        f = Fake()
        f.item["bbox"] = [10., 50., 12., 52.]
        with self.assertRaises(ProbeError):
            probe(fetch=f)

    def test_reject_wrong_aws_object(self):
        f = Fake()
        f.item["assets"]["aws"]["href"] = "https://example.org/unreviewed"
        with self.assertRaises(ProbeError):
            probe(fetch=f)

    def test_reject_source_size_change(self):
        f = Fake()
        f.item["assets"]["aws"]["file:size"] += 1
        with self.assertRaises(ProbeError):
            probe(fetch=f)

    def test_reject_malformed_stac_json(self):
        f = Fake()
        f.bad_stac_json = b'{"id":"00226","id":"00226"}'
        with self.assertRaises(ProbeError):
            probe(fetch=f)

    def test_reject_full_content_response_instead_of_range(self):
        f = Fake()
        f.status = 200
        with self.assertRaises(ProbeError):
            probe(fetch=f)

    def test_reject_etag_change_between_ranges(self):
        f = Fake()
        f.inconsistent_etag = True
        with self.assertRaises(ProbeError):
            probe(fetch=f)

    def test_reject_original_parquet_start_magic(self):
        f = Fake()
        f.bad_first = True
        with self.assertRaises(ProbeError):
            probe(fetch=f)

    def test_reject_original_parquet_end_magic(self):
        f = Fake()
        f.bad_last = True
        with self.assertRaises(ProbeError):
            probe(fetch=f)

    def test_reject_inconsistent_file_row_count(self):
        f = Fake()
        f.parquet_rows = EXPECTED_ROWS - 1
        with self.assertRaises(ProbeError):
            probe(fetch=f)

    def test_reject_unreasonably_large_footer(self):
        f = Fake()
        f.footer_length = 3_000_000
        with self.assertRaises(ProbeError):
            probe(fetch=f)

    def test_reject_bad_source_content_range(self):
        f = Fake()
        f.bad_content_range = True
        with self.assertRaises(ProbeError):
            probe(fetch=f)

    def test_no_implicit_original_access(self):
        self.assertEqual(main([]), 2)


if __name__ == "__main__":
    unittest.main()
