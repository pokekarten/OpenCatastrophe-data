# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No-network ZIP directory tests with fictional tiny in-memory archives."""
from __future__ import annotations

import io
import struct
import unittest
import zipfile

from research_runners.lu_act2019_three_zip_directory_range_v0 import (
    DirectoryError, ORIGINAL_SIZE_BY_SITE, MAX_TAIL, locate_eocd,
    summarize_central, safe_range, inspect_one_zip,
)

SYNTHETIC_URL = (
    "https://download.data.public.lu/resources/"
    "lidar-2019-releve-3d-du-territoire-luxembourgeois/"
    "20200101-000000/synthetic-only-not-a-source.zip"
)


def fake_archive(*, comment=b""):
    output=io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("fake-points.laz",b"FICTION_ONLY")
        archive.writestr("readme.txt",b"NOT_REAL_LIDAR")
        archive.comment=comment
    return output.getvalue()


def parse_original_fixture(payload):
    tail=payload[-min(len(payload),MAX_TAIL):]
    info=locate_eocd(tail,tail_start=len(payload)-len(tail),total=len(payload))
    c=payload[info["offset"]:info["offset"]+info["size"]]
    return info,summarize_central(c,entries=info["entries"],
                               archive_size=len(payload),
                               directory_offset=info["offset"])


class FakeResponse:
    def __init__(self, url, status, headers, data=b""):
        self._url=url
        self.status=status
        self.headers=headers
        self.data=data
        self.calls=[]
    def geturl(self):
        return self._url
    def read(self, n):
        if not isinstance(n,int) or n>262145 or n<1:
            raise AssertionError("Unbounded or invalid response body request")
        self.calls.append(n)
        return self.data[:n]
    def __enter__(self):
        return self
    def __exit__(self,*args):
        return False


class FakeOpen:
    def __init__(self, responses):
        self.responses=list(responses)
        self.requests=[]
    def open(self, req, timeout):
        self.requests.append((req.get_method(),req.headers,timeout))
        if not self.responses:
            raise AssertionError("Unexpected network request")
        return self.responses.pop(0)


class ZIPCentralDirectoryTests(unittest.TestCase):
    def test_ordinary_zip_eocd_and_file_types(self):
        original=fake_archive()
        info,report=parse_original_fixture(original)
        self.assertEqual(info["entries"],2)
        self.assertEqual(report["member_extension_counts"]["laz"],1)
        self.assertEqual(report["member_extension_counts"]["txt"],1)
        self.assertEqual(report["member_extension_counts"]["other"],0)
        self.assertEqual(report["zip_method_code_counts"],{"0":2})
        self.assertFalse(report["original_zip_full_sha256_verified"])
        self.assertFalse(report["archive_members_extracted_or_read"])
        self.assertNotIn("fake-points.laz",str(report))

    def test_eocd_supports_comment_with_signature_like_bytes(self):
        archive=fake_archive(comment=b"prefixPK\x05\x06false-directory")
        info,report=parse_original_fixture(archive)
        self.assertEqual(info["eocd_comment_bytes"],len(b"prefixPK\x05\x06false-directory"))
        self.assertEqual(report["central_member_total"],2)

    def test_false_eocd_signature_does_not_pass(self):
        with self.assertRaises(DirectoryError):
            locate_eocd(b"PK\x05\x06"+b"\x00"*40,tail_start=0,total=44)

    def test_truncated_directory_rejected(self):
        archive=fake_archive()
        info,_=parse_original_fixture(archive)
        payload=archive[info["offset"]:info["offset"]+info["size"]-1]
        with self.assertRaises(DirectoryError):
            summarize_central(payload,entries=info["entries"],
                              archive_size=len(archive),directory_offset=info["offset"])

    def test_nonconserved_eocd_offset_rejected(self):
        archive=bytearray(fake_archive())
        archive[-8:-4]=struct.pack("<I",500)  # EOCD central directory offset changes
        with self.assertRaises(DirectoryError):
            parse_original_fixture(bytes(archive))

    def test_zip64_eocd_sentinel_rejected_not_implicitly_parsed(self):
        archive=bytearray(fake_archive())
        archive[-12:-8]=struct.pack("<I",0xffffffff)  # directory size
        with self.assertRaises(DirectoryError):
            parse_original_fixture(bytes(archive))

    def test_spanned_archive_eocd_fails(self):
        archive=bytearray(fake_archive())
        archive[-18:-16]=struct.pack("<H",1)
        with self.assertRaises(DirectoryError):
            parse_original_fixture(bytes(archive))

    def test_member_name_does_not_appear_and_path_escape_blocks(self):
        raw=bytearray(fake_archive())
        info,_=parse_original_fixture(bytes(raw))
        pos=info["offset"]+46
        raw[pos:pos+4]=b"../."
        central=bytes(raw[info["offset"]:info["offset"]+info["size"]])
        with self.assertRaises(DirectoryError):
            summarize_central(central,entries=info["entries"],
                              archive_size=len(raw),directory_offset=info["offset"])

    def test_unapproved_byte_range_budget_fails_before_network(self):
        class Unused:
            def open(self,*args,**kwargs):
                raise AssertionError("Should not attempt network")
        with self.assertRaises(DirectoryError):
            safe_range(SYNTHETIC_URL,start=0,length=262145,total=1000000,opener=Unused())
        with self.assertRaises(DirectoryError):
            safe_range(SYNTHETIC_URL,start=100,length=10,total=105,opener=Unused())

    def test_http_200_instead_of_206_is_rejected_without_body_read(self):
        res=FakeResponse(SYNTHETIC_URL,200,{"Content-Length":"999"},b"x"*10)
        fake=FakeOpen([res])
        with self.assertRaises(DirectoryError):
            safe_range(SYNTHETIC_URL,start=50,length=10,total=100,opener=fake)
        self.assertEqual(res.calls,[])

    def test_http_range_response_origin_change_rejected(self):
        res=FakeResponse("https://other.example/not-a-source",206,
                         {"Content-Range":"bytes 0-3/100","Content-Length":"4"},b"ZIP!")
        with self.assertRaises(DirectoryError):
            safe_range(SYNTHETIC_URL,start=0,length=4,total=100,opener=FakeOpen([res]))

    def test_short_malformed_or_reencoded_range_rejected(self):
        for headers in (
            {"Content-Range":"bytes 0-2/100","Content-Length":"4"},
            {"Content-Range":"bytes 0-3/100","Content-Length":"3"},
            {"Content-Range":"bytes 0-3/100","Content-Encoding":"gzip"},
        ):
            with self.subTest(headers=headers):
                res=FakeResponse(SYNTHETIC_URL,206,headers,b"ZIP!")
                with self.assertRaises(DirectoryError):
                    safe_range(SYNTHETIC_URL,start=0,length=4,total=100,opener=FakeOpen([res]))

    def test_response_exactly_bounded_returns_four_bytes(self):
        res=FakeResponse(SYNTHETIC_URL,206,
                         {"Content-Range":"bytes 0-3/100","Content-Length":"4"},b"ABCD")
        result=safe_range(SYNTHETIC_URL,start=0,length=4,total=100,opener=FakeOpen([res]))
        self.assertEqual(result,b"ABCD")
        self.assertEqual(res.calls,[5])

    def test_pinned_site_zip_lengths_not_claimed_full_integrity(self):
        self.assertEqual(ORIGINAL_SIZE_BY_SITE["luxembourg-city"],(449275061,))
        self.assertEqual(ORIGINAL_SIZE_BY_SITE["berdorf-village"],(410361626,374704804))

    def test_tiny_synthetic_archive_full_flow_read_bounds(self):
        archive=fake_archive()
        total=len(archive)
        head=FakeResponse(SYNTHETIC_URL,200,{"Content-Length":str(total)})
        prefix=FakeResponse(SYNTHETIC_URL,206,
                            {"Content-Range":f"bytes 0-3/{total}"},b"PK\x03\x04")
        tail=FakeResponse(SYNTHETIC_URL,206,
                          {"Content-Range":f"bytes 0-{total-1}/{total}",
                           "Content-Length":str(total)},archive)
        opener=FakeOpen([head,prefix,tail])
        result=inspect_one_zip(SYNTHETIC_URL,expected_size=total,opener=opener)
        self.assertEqual(result["member_extension_counts"]["laz"],1)
        self.assertEqual(result["member_extension_counts"]["txt"],1)
        self.assertEqual(result["central_member_total"],2)
        self.assertFalse(result["complete_original_zip_archive_downloaded"])
        self.assertEqual(len(opener.requests),3)
        self.assertEqual([x[0] for x in opener.requests],["HEAD","GET","GET"])
        self.assertNotIn(SYNTHETIC_URL,str(result))


if __name__ == "__main__":
    unittest.main()
