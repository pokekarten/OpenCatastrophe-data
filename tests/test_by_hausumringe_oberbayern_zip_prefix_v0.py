# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic ZIP local header fixtures only: never commit original provider bytes."""
import struct
import unittest

from research_runners.by_hausumringe_oberbayern_zip_prefix_v0 import (
    LIMIT,FIRST_NAME,URL,PrefixBlocked,validate_prefix,
)


def fake():
    data=bytearray(LIMIT)
    struct.pack_into("<4sHHHHHIIIHH",data,0,b"PK\x03\x04",20,0,8,0,0,0,100,200,len(FIRST_NAME),0)
    data[30:30+len(FIRST_NAME)]=FIRST_NAME
    return bytes(data)


def headers(**change):
    h={"Content-Range":"bytes 0-4095/162000000","Content-Type":"application/zip","Content-Length":"4096"}
    h.update(change)
    return h


class OriginalPrefixSyntheticTests(unittest.TestCase):
    def test_reviewed_fixed_source_success_is_only_T1_research(self):
        v=validate_prefix(fake(),status=206,response_url=URL,headers=headers())
        self.assertEqual(v["source_id"],"de.bayern.hausumringe")
        self.assertEqual(v["first_original_zip_entry"],"hausumringe.dbf")
        self.assertEqual(v["original_prefix_bytes"],4096)
        self.assertEqual(len(v["original_prefix_sha256"]),64)
        self.assertFalse(v["full_original_archive_downloaded"])
        self.assertFalse(v["original_shapefile_polygons_downloaded"])
        self.assertFalse(v["model_input_approved"])

    def test_provider_must_not_respond_full_unbounded_or_redirect(self):
        for code,url in ((200,URL),(206,"https://other.example/zip")):
            with self.subTest(code=code,url=url):
                with self.assertRaises(PrefixBlocked):
                    validate_prefix(fake(),status=code,response_url=url,headers=headers())

    def test_reject_truncation_or_overlong_prefix(self):
        for data in (fake()[:-1],fake()+b"X"):
            with self.assertRaises(PrefixBlocked):
                validate_prefix(data,status=206,response_url=URL,headers=headers())

    def test_media_range_and_size_are_exact(self):
        for diff in (
            {"Content-Type":"text/html"},
            {"Content-Range":"bytes 0-4094/162000000"},
            {"Content-Range":"bytes 0-4095/*"},
            {"Content-Range":"bytes 0-4095/1000"},
            {"Content-Length":"162000000"},
            {"Content-Encoding":"gzip"},
        ):
            with self.subTest(diff=diff):
                with self.assertRaises(PrefixBlocked):
                    validate_prefix(fake(),status=206,response_url=URL,headers=headers(**diff))

    def test_bad_magic_encryption_compression_or_wrong_entry_blocks(self):
        changes=((0,ord("X")),(6,1),(8,0),(30,ord("X")))
        for index,value in changes:
            data=bytearray(fake())
            data[index]=value
            with self.subTest(index=index):
                with self.assertRaises(PrefixBlocked):
                    validate_prefix(bytes(data),status=206,response_url=URL,headers=headers())

    def test_no_provider_link_or_archive_content_in_static_fixtures(self):
        self.assertEqual(LIMIT,4096)
        self.assertTrue(URL.startswith("https://geodaten.bayern.de/odd/"))
        self.assertEqual(FIRST_NAME,b"hausumringe.dbf")


if __name__=="__main__":
    unittest.main()
