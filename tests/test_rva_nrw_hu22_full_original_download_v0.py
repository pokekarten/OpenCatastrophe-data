# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fake original publisher full GET; no 901MB network access in these tests."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
from unittest.mock import patch
import unittest
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
import rva_nrw_hu22_full_original_download_v0 as m
from rva_nrw_hu_full_zip_stratified_reservoir_v0 import SourceBlocked


class Fake:
    def __init__(self,data,length,status=200,url=m.ORIGINAL_URL):
        self.data=data
        self.status=status
        self._url=url
        self.headers={"Content-Length":str(length)}
        self.pos=0
    def geturl(self):return self._url
    def read(self,n):
        v=self.data[self.pos:self.pos+n]
        self.pos+=len(v)
        return v
    def __enter__(self):return self
    def __exit__(self,*args):pass


class TestOneShotHUDownload(unittest.TestCase):
    def test_one_bounded_get_and_source_byte_sha(self):
        with patch.object(m,"MAX_BYTES",6), \
             patch.object(m,"EXPECTED_ORIGINAL_SHA256",hashlib.sha256(b"ABCDEF").hexdigest()), \
             tempfile.TemporaryDirectory() as t:
            calls=[]
            def fake(req,timeout):
                calls.append((req.full_url,req.get_method(),timeout))
                return Fake(b"ABCDEF",6)
            result=m.download_original_once(Path(t)/"official.zip",urlopen_=fake)
            self.assertEqual(result["official_archive_full_bytes"],6)
            self.assertEqual(result["official_source_sha256_computed_after_full_get"],
                             hashlib.sha256(b"ABCDEF").hexdigest())
            self.assertFalse(result["source_derived_insured_locations"])
            self.assertEqual(calls,[(m.ORIGINAL_URL,"GET",70)])

    def test_fail_closed_and_remove_unusable_partial_archive(self):
        with patch.object(m,"MAX_BYTES",6), \
             patch.object(m,"EXPECTED_ORIGINAL_SHA256",hashlib.sha256(b"ABCDEF").hexdigest()), \
             tempfile.TemporaryDirectory() as t:
            d=Path(t)
            for value in (
                Fake(b"AB",6),
                Fake(b"ABCDEFG",6),
                Fake(b"ABXDEF",6),  # exact six-byte payload, wrong SHA256
                Fake(b"ABCDEF",5),
                Fake(b"ABCDEF",6,status=206),
                Fake(b"ABCDEF",6,url="https://example.net/not-original"),
            ):
                out=d/"output.zip"
                with self.assertRaises(SourceBlocked):
                    m.download_original_once(out,urlopen_=lambda request,timeout:value)
                self.assertFalse(out.exists())

    def test_same_size_wrong_sha_fails_before_archive_is_consumed(self):
        good_digest=hashlib.sha256(b"ABCDEF").hexdigest()
        with patch.object(m,"MAX_BYTES",6), \
             patch.object(m,"EXPECTED_ORIGINAL_SHA256",good_digest), \
             tempfile.TemporaryDirectory() as t:
            output=Path(t)/"original.zip"
            with self.assertRaisesRegex(SourceBlocked,"SHA256 identity drift"):
                m.download_original_once(output,urlopen_=lambda req,timeout:Fake(b"XXXXXX",6))
            self.assertFalse(output.exists())

    def test_refuse_to_overwrite_existing_source_or_missing_parent(self):
        with patch.object(m,"MAX_BYTES",6),tempfile.TemporaryDirectory() as t:
            p=Path(t)/"existing.zip"
            p.write_bytes(b"x")
            with self.assertRaises(SourceBlocked):
                m.download_original_once(p,urlopen_=lambda request,timeout:Fake(b"ABCDEF",6))
            with self.assertRaises(SourceBlocked):
                m.download_original_once(Path(t)/"nonexistent"/"archive.zip",
                    urlopen_=lambda request,timeout:Fake(b"ABCDEF",6))


if __name__=="__main__":
    unittest.main()
