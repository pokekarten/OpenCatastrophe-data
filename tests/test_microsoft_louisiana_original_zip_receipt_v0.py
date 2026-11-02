# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original provider metadata mocked; zero original data or buildings fetched."""
from __future__ import annotations

import struct
import unittest

from research_runners.microsoft_louisiana_original_zip_receipt_v0 import (
    OriginalArchiveError, EXPECTED_MEMBER, MAX_TAIL_BYTES, probe,
)

N = 150_000_000
ETAG='"source-opaque-etag"'
CD_N=46+len(EXPECTED_MEMBER.encode("utf-8"))
CD_START=N-22-CD_N


def synthetic_central(*, name=EXPECTED_MEMBER, packed=70_000_000,
                      unpacked=629_850_000, flags=0):
    b=name.encode("utf-8")
    return struct.pack(
        "<IHHHHHHIIIHHHHHII",0x02014b50,20,20,flags,8,0,0,0,
        packed,unpacked,len(b),0,0,0,0,0,0,
    ) + b


def fake_fetch(*, name=EXPECTED_MEMBER, etag=ETAG,
               corrupted_end=False, wrong_compressed=False,
               reject_range=False, wrong_original_size=False,
               flags=0):
    central=synthetic_central(
        name=name, packed=0 if wrong_compressed else 70_000_000,
        flags=flags)
    cd_start=N-22-len(central)
    ending=struct.pack(
        "<IHHHHIIH",0x06054b50,0,0,1,1,len(central),cd_start,0,
    )
    if corrupted_end:
        ending=b"BAD!" + ending[4:]
    tail=(b"\x00"*(MAX_TAIL_BYTES-len(central)-len(ending))
          +central+ending)

    def fetch(req,limit):
        if req.full_url != (
                "https://minedbuildings.z5.web.core.windows.net/"
                "legacy/usbuildings-v2/Louisiana.geojson.zip"):
            raise AssertionError("unreviewed source host")
        if req.get_method()=="HEAD":
            return 200, {"content-length":str(N-1 if wrong_original_size else N),
                         "etag":etag, "accept-ranges":"bytes"},b""
        if reject_range:
            return 200,{"content-length":"1"},b"\0"
        requested=req.get_header("Range")
        start,end=map(int,requested.removeprefix("bytes=").split("-"))
        if start==N-MAX_TAIL_BYTES and end==N-1:
            body=tail
        elif start==cd_start and end==cd_start+len(central)-1:
            body=central
        else:
            raise AssertionError(f"unexpected original range {requested}")
        return 206, {
            "content-length":str(len(body)),
            "content-range":f"bytes {start}-{end}/{N}",
            "etag":etag,
        },body
    return fetch


class MicrosoftLouisianaOriginalZipReceiptTests(unittest.TestCase):
    def test_fixed_official_archive_structure_not_building_admission(self):
        out=probe(fetch=fake_fetch())
        self.assertEqual(out["source_zip_entries"],1)
        self.assertEqual(out["source_member_name"],EXPECTED_MEMBER)
        self.assertEqual(out["source_member_uncompressed_bytes"],629_850_000)
        self.assertFalse(out["geojson_original_records_read"])
        self.assertFalse(out["georeferenced_parish_crosswalk_executed"])
        self.assertFalse(out["cat_model_input_admitted"])

    def test_source_authority_does_not_prove_2173567_features(self):
        out=probe(fetch=fake_fetch())
        self.assertFalse(out["reported_2173567_buildings_verified"])
        self.assertFalse(out["full_archive_sha256_verified"])
        self.assertFalse(out["source_ODbL_reuse_rights_approved"])

    def test_zip_eocd_corruption_rejected(self):
        with self.assertRaises(OriginalArchiveError):
            probe(fetch=fake_fetch(corrupted_end=True))

    def test_duplicate_or_wrong_original_geojson_member_rejected(self):
        with self.assertRaises(OriginalArchiveError):
            probe(fetch=fake_fetch(name="../secret.json"))

    def test_original_zero_length_compressed_payload_rejected(self):
        with self.assertRaises(OriginalArchiveError):
            probe(fetch=fake_fetch(wrong_compressed=True))

    def test_encrypted_source_file_rejected(self):
        with self.assertRaises(OriginalArchiveError):
            probe(fetch=fake_fetch(flags=1))

    def test_wrong_http_length_must_fail_without_downgrade(self):
        with self.assertRaises(OriginalArchiveError):
            probe(fetch=fake_fetch(wrong_original_size=True))

    def test_ignored_range_request_refused(self):
        with self.assertRaises(OriginalArchiveError):
            probe(fetch=fake_fetch(reject_range=True))

    def test_missing_or_untrusted_etag_refused(self):
        for tag in ("", "bad-etag", "W/"+ETAG):
            with self.subTest(tag=tag), self.assertRaises(OriginalArchiveError):
                probe(fetch=fake_fetch(etag=tag))


if __name__=="__main__":
    unittest.main()
