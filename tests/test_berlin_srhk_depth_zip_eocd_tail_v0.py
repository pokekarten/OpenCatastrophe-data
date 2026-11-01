# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only ZIP EOCD and exact HTTPS Range negative tests."""
from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
import struct
import unittest
from zipfile import ZipFile, ZIP_DEFLATED

from research_runners.berlin_srhk_depth_zip_eocd_tail_v0 import (
    TAIL_BYTES, OBJECTS, ROOT, LAST_MODIFIED, TIMEOUT, EocdSourceError,
    inspect_tail, inspect_directory, validate_range, probe,
)


def make_tail(scenario="extreme", names=("first.tif", "second.TIFF", "README.txt"),
              *, zip_comment=b""):
    blob = BytesIO()
    with ZipFile(blob, "w", compression=ZIP_DEFLATED) as z:
        for name in names:
            z.writestr(name, b"FAKE-TEST-DATA-NOT-A-REAL-TIFF")
        z.comment = zip_comment
    original = blob.getvalue()
    # Fake a large, exactly HEAD-sized source ZIP with only the synthetic
    # directory/EOCD near EOF. Patch ZIP's 32-bit directory absolute offset
    # to agree with the artificial source size, as a real archive would.
    offset_of_eocd = len(original) - 22 - len(zip_comment)
    cd_offset = struct.unpack_from("<I", original, offset_of_eocd + 16)[0]
    shift = OBJECTS[scenario][1] - len(original)
    modified = bytearray(original)
    struct.pack_into("<I", modified, offset_of_eocd + 16, cd_offset + shift)
    tail = bytes(modified[-TAIL_BYTES:])
    return tail.rjust(TAIL_BYTES, b"\0")


def headers(scenario="extreme"):
    total = OBJECTS[scenario][1]
    return {"Content-Range": f"bytes {total-TAIL_BYTES}-{total-1}/{total}",
            "Content-Length": str(TAIL_BYTES),
            "Content-Type": "application/zip",
            "Last-Modified": LAST_MODIFIED[scenario]}


class FakeResponse(BytesIO):
    status = 206

    def __init__(self, scenario, body=None, response_url=None, head=None):
        super().__init__(make_tail(scenario) if body is None else body)
        self.url = response_url or ROOT + OBJECTS[scenario][0]
        self.headers = headers(scenario) if head is None else head
        self.read_calls = 0

    def geturl(self):
        return self.url

    def read(self, size=-1):
        self.read_calls += 1
        return super().read(size)


class BerlinEocdTailTests(unittest.TestCase):
    def test_synthetic_real_zip_members_and_source_total(self):
        for scenario in OBJECTS:
            with self.subTest(scenario=scenario):
                out = inspect_tail(make_tail(scenario), scenario=scenario)
                self.assertEqual(out["zip_member_count_declared"], 3)
                self.assertTrue(out["central_directory_fully_present_within_original_tail"])
                self.assertTrue(out["central_directory_members_independently_parsed"])
                self.assertFalse(out["central_directory_separate_range_needed"])
                self.assertEqual(out["tiff_named_member_count"], 2)
                self.assertEqual(out["other_named_member_count"], 1)
                self.assertFalse(out["full_zip_sha256_or_archive_integrity_proven"])
                self.assertFalse(out["true_tiff_crs_units_or_nodata_verified"])
                self.assertFalse(out["individual_member_names_emitted"])
                self.assertNotIn("first.tif", str(out))
                self.assertEqual(len(out["original_tail_sha256_only"]), 64)

    def test_bounded_http206_no_redirect_and_if_range_pinned(self):
        for scenario in OBJECTS:
            with self.subTest(scenario=scenario):
                calls = []
                response = FakeResponse(scenario)
                def opener(req, timeout):
                    calls.append((req.get_method(), req.full_url,
                                  req.headers.get("Range"),
                                  req.headers.get("If-range"), timeout))
                    return response
                out = probe(scenario, opener=opener,
                            clock=lambda: datetime(2026, 11, 1, tzinfo=timezone.utc))
                n = OBJECTS[scenario][1]
                self.assertEqual(calls, [("GET", ROOT + OBJECTS[scenario][0],
                    f"bytes={n-TAIL_BYTES}-{n-1}", LAST_MODIFIED[scenario], TIMEOUT)])
                self.assertEqual(response.read_calls, 1)
                self.assertEqual(out["original_tail_bytes_received"], TAIL_BYTES)
                self.assertTrue(out["http_range_status_206_verified"])
                self.assertTrue(out["no_original_source_bytes_persisted"])
                self.assertTrue(out["last_modified_same_as_prior_head_when_sent"])

    def test_refuse_http200_full_zip_before_reading_body(self):
        class Full(FakeResponse):
            status = 200
        res = Full("extreme")
        with self.assertRaisesRegex(EocdSourceError, "did not honor"):
            probe("extreme", opener=lambda req, timeout: res)
        self.assertEqual(res.read_calls, 0)

    def test_changed_size_content_range_headers_and_modified_refused(self):
        for change in (
            {"Content-Range": "bytes 0-65556/619211977"},
            {"Content-Range": "bytes 0-65556/619211978"},
            {"Content-Length": str(TAIL_BYTES+1)},
            {"Content-Type": "text/html"},
            {"Content-Encoding": "gzip"},
            {"Last-Modified": "Fri, 20 Feb 2026 00:00:00 GMT"},
        ):
            with self.subTest(change=change), self.assertRaises(EocdSourceError):
                validate_range({**headers(), **change}, scenario="extreme")

    def test_malformed_zip_tail_or_zip64_sentinel_refused(self):
        sample = make_tail()
        with self.assertRaisesRegex(EocdSourceError, "tail length"):
            inspect_tail(sample[:-1], scenario="extreme")
        with self.assertRaisesRegex(EocdSourceError, "end-of-central-directory"):
            inspect_tail(bytes(TAIL_BYTES), scenario="extreme")
        # EOCD is normally 22 bytes from EOF with no comment.
        for field_at, fmt, value in ((12, "<I", 0xFFFFFFFF), (10, "<H", 0xFFFF),
                                     (4, "<H", 1), (16, "<I", 0)):
            bad = bytearray(sample)
            struct.pack_into(fmt, bad, len(bad)-22+field_at, value)
            with self.subTest(field=field_at), self.assertRaises(EocdSourceError):
                inspect_tail(bytes(bad), scenario="extreme")

    def test_zip_comment_and_hidden_eocd_signature_in_comment(self):
        comment = b"an innocent note including PK\x05\x06 fake bytes"
        tail = make_tail(zip_comment=comment)
        row = inspect_tail(tail, scenario="extreme")
        self.assertEqual(row["zip_archive_comment_bytes"], len(comment))
        self.assertEqual(row["tiff_named_member_count"], 2)
        corrupt = bytearray(tail)
        corrupt[-1] = 255
        # Comment contents are not interpreted; the original EOCD remains valid.
        self.assertTrue(inspect_tail(bytes(corrupt), scenario="extreme")["single_disk_zip_classic_eocd"])

    def test_reject_traversal_duplicate_and_encrypted_members(self):
        for names in (("../secret.tif",), ("folder/../../secret.tif",),
                      ("same.tif", "same.tif")):
            with self.subTest(names=names), self.assertRaises(EocdSourceError):
                inspect_tail(make_tail(names=names), scenario="extreme")
        sample = bytearray(make_tail())
        # First central record is in the tail before EOCD; locate its header
        # and mark general-purpose flag 1 (encrypted).
        at = sample.index(b"PK\x01\x02")
        flags = struct.unpack_from("<H", sample, at+8)[0]
        struct.pack_into("<H", sample, at+8, flags | 1)
        with self.assertRaisesRegex(EocdSourceError, "unsafe"):
            inspect_tail(bytes(sample), scenario="extreme")

    def test_central_directory_too_large_for_tail_needs_separate_range(self):
        # More than 65KB of directory metadata is valid but explicitly
        # cannot be claimed as parsed from a 65KB tail.
        names = tuple(f"tiles/tile-{i:05d}-" + "x"*110 + ".tif" for i in range(450))
        sample = make_tail(names=names)
        out = inspect_tail(sample, scenario="extreme")
        self.assertGreater(out["central_directory_size_bytes"], TAIL_BYTES)
        self.assertFalse(out["central_directory_fully_present_within_original_tail"])
        self.assertTrue(out["central_directory_separate_range_needed"])
        self.assertFalse(out["central_directory_members_independently_parsed"])
        self.assertIsNone(out["tiff_named_member_count"])
        self.assertEqual(out["zip_member_count_declared"], 450)

    def test_naive_clock_and_unsupported_source_refused(self):
        with self.assertRaisesRegex(EocdSourceError, "timezone"):
            probe("extreme", opener=lambda req, timeout: FakeResponse("extreme"),
                  clock=lambda: datetime(2026,11,1))
        with self.assertRaisesRegex(EocdSourceError, "unknown"):
            probe("wildcard", opener=lambda req, timeout: FakeResponse("extreme"))


if __name__ == "__main__":
    unittest.main()
