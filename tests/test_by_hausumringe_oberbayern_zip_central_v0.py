# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic ZIP metadata only, no provider archive fragments or geodata."""
import struct
import unittest

from research_runners.by_hausumringe_oberbayern_zip_central_v0 import (
    CENTRAL_SIZE, CENTRAL_START, END, FROZEN, LIMIT, RANGE, START, TOTAL,
    CentralBlocked, URL, inspect_suffix,
)


def fake() -> bytes:
    raw = bytearray(LIMIT)
    pos = CENTRAL_START - START
    for name, (offset, compressed, inflated) in FROZEN.items():
        name_b = name.encode("ascii")
        assert len(name_b) == 15
        struct.pack_into(
            "<IHHHHHHIIIHHHHHII",
            raw, pos, 0x02014B50, 20, 20, 0, 8, 0, 0,
            0x12345678, compressed, inflated, 15, 36, 0, 0, 0, 0, offset,
        )
        raw[pos+46:pos+61] = name_b
        # A synthetic 36-byte extra field proves the position accounting,
        # NOT actual provider auxiliary-field contents.
        pos += 97
    assert pos == LIMIT - 22
    struct.pack_into(
        "<IHHHHIIH",
        raw, pos, 0x06054B50, 0, 0, 4, 4, CENTRAL_SIZE, CENTRAL_START, 0,
    )
    return bytes(raw)


def headers(**changes):
    h = {
        "Content-Range": f"bytes {START}-{END}/{TOTAL}",
        "Content-Type": "application/zip",
        "Content-Length": str(LIMIT),
        "Content-Encoding": "identity",
    }
    h.update(changes)
    return h


class SyntheticZIPCentralTests(unittest.TestCase):
    def test_four_original_member_layout_and_no_admission(self):
        r = inspect_suffix(fake(), status=206, response_url=URL, headers=headers())
        self.assertEqual(r["source_id"], "de.bayern.hausumringe")
        self.assertEqual(r["central_directory_bytes"], 388)
        self.assertEqual(
            {x["name"] for x in r["original_expected_members"]},
            {"hausumringe.dbf", "hausumringe.prj",
             "hausumringe.shp", "hausumringe.shx"},
        )
        self.assertEqual(r["response_bytes"], 4096)
        self.assertFalse(r["original_shp_geometries_retrieved"])
        self.assertFalse(r["original_prj_epsg_verified"])
        self.assertFalse(r["complete_archive_sha256_verified"])
        self.assertFalse(r["model_input_approved"])

    def test_truncated_or_overlong_cannot_pass(self):
        for r in (fake()[:-1], fake()+b"\0", b""):
            with self.subTest(n=len(r)), self.assertRaises(CentralBlocked):
                inspect_suffix(r, status=206, response_url=URL, headers=headers())

    def test_wrong_status_redirect_or_source_length_block(self):
        for status, url, meta in (
            (200, URL, headers()),
            (206, "https://other.example/file", headers()),
            (206, URL, headers(**{"Content-Range":f"bytes {START}-{END}/174299766"})),
            (206, URL, headers(**{"Content-Range":"bytes 0-4095/174299765"})),
        ):
            with self.subTest(status=status,url=url,meta=meta), self.assertRaises(CentralBlocked):
                inspect_suffix(fake(), status=status, response_url=url, headers=meta)

    def test_wrong_media_encoding_length_blocks(self):
        for meta in (
            {"Content-Type":"text/html"},
            {"Content-Encoding":"gzip"},
            {"Content-Length":"174299765"},
        ):
            with self.subTest(meta=meta), self.assertRaises(CentralBlocked):
                inspect_suffix(fake(), status=206, response_url=URL, headers=headers(**meta))

    def test_eocd_wrong_count_comment_or_directory_offset_blocks(self):
        for p, val in ((LIMIT-22+10,3),(LIMIT-22+20,1),
                       (LIMIT-22+16,0),(LIMIT-22+12,0)):
            raw = bytearray(fake())
            raw[p] = val
            with self.subTest(position=p), self.assertRaises(CentralBlocked):
                inspect_suffix(bytes(raw), status=206,response_url=URL,headers=headers())

    def test_member_drift_signature_extra_and_compression_block(self):
        origin = CENTRAL_START-START
        for p,v in ((origin,0),(origin+12,0),(origin+28,0),
                    (origin+30,0),(origin+46,ord("x")),
                    (origin+20,0),(origin+42,9)):
            raw=bytearray(fake())
            raw[p]=v
            with self.subTest(position=p), self.assertRaises(CentralBlocked):
                inspect_suffix(bytes(raw), status=206,response_url=URL,headers=headers())

    def test_central_directory_must_be_contiguous(self):
        # Member offsets must agree with their local 30+15 byte headers.
        raw=bytearray(fake())
        ptr=CENTRAL_START-START+97+42
        struct.pack_into("<I",raw,ptr,FROZEN["hausumringe.prj"][0]+1)
        with self.assertRaises(CentralBlocked):
            inspect_suffix(bytes(raw),status=206,response_url=URL,headers=headers())

    def test_last_directory_entry_and_eocd_must_match_exact_4k_window(self):
        self.assertEqual(TOTAL - LIMIT, START)
        self.assertEqual(END, TOTAL-1)
        self.assertEqual(RANGE, f"bytes={START}-{END}")
        self.assertEqual(CENTRAL_START + CENTRAL_SIZE, TOTAL-22)


if __name__=="__main__":
    unittest.main()
