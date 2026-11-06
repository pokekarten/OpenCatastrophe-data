# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline tests for single-shot official EIOPA source and host pinning."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"research_runners"))
import eiopa_2023_ephemeral_official_xlsx_fetch_v0 as gate


class Response:
    def __init__(self, url, body: bytes, ctype: str):
        self._url=url
        self._buffer=BytesIO(body)
        self.headers={"Content-Type":ctype,"Content-Length":str(len(body))}
    def geturl(self):
        return self._url
    def read(self, n):
        return self._buffer.read(n)
    def __enter__(self):
        return self
    def __exit__(self,*args):
        self._buffer.close()
        return False


class Opener:
    def __init__(self, action):
        self.calls=0
        self.action=action
    def open(self, request, timeout):
        self.calls+=1
        assert timeout<=45
        return self.action(request)


class SourceOriginalURLPreflightTests(unittest.TestCase):
    def test_exact_original_url_and_strict_host_only(self):
        for url in gate.URLS.values():
            gate.validate_publisher_url(url)
        for bad in (
            "http://www.eiopa.europa.eu/document/download/source",
            "https://not-eiopa.europa.eu/document/download/any",
            "https://www.eiopa.europa.eu.evil.example/document/download/x",
            "https://www.eiopa.europa.eu@fake.example/document/download/x",
            "https://www.eiopa.europa.eu:444/document/download/x",
            "https://www.eiopa.europa.eu/download/not-original.xlsx",
        ):
            with self.subTest(url=bad):
                with self.assertRaises(gate.EIOPAOriginalDownloadBlocked):
                    gate.validate_publisher_url(bad)

    def test_one_original_request_is_bounded_and_writes_only_ephemeral_file(self):
        url=gate.URLS["HISTORICAL_INSURED_LOSSES"]
        payload=b"PK\x03\x04"+b"S"*402
        opener=Opener(lambda req:Response(req.full_url,payload,gate.MIME))
        with TemporaryDirectory() as tmp:
            dest=Path(tmp)/"source.xlsx"
            gate.bounded_single_request(url,dest,"HISTORICAL_INSURED_LOSSES",opener)
            self.assertEqual(dest.read_bytes(),payload)
            self.assertEqual(opener.calls,1)
            with self.assertRaises(gate.EIOPAOriginalDownloadBlocked):
                gate.bounded_single_request(url,dest,"HISTORICAL_INSURED_LOSSES",opener)
            self.assertEqual(opener.calls,1)

    def test_rate_limit_denies_without_retry_or_workbook_output(self):
        url=gate.URLS["HISTORICAL_INSURED_LOSSES"]
        def reject(req):
            raise HTTPError(req.full_url,429,"Too Many Requests",{},None)
        opener=Opener(reject)
        with TemporaryDirectory() as tmp:
            dest=Path(tmp)/"original.xlsx"
            with self.assertRaisesRegex(gate.EIOPAOriginalDownloadBlocked,"HTTP 429"):
                gate.bounded_single_request(url,dest,"HISTORICAL_INSURED_LOSSES",opener)
            self.assertEqual(opener.calls,1)
            self.assertFalse(dest.exists())

    def test_publisher_redirect_or_false_content_type_denied(self):
        url=gate.URLS["HISTORICAL_INSURED_LOSSES"]
        for final,ctype in (
            ("https://evil.example/file",gate.MIME),
            (url,"text/html"),
        ):
            with self.subTest(final=final,ctype=ctype):
                opener=Opener(lambda req:Response(final,b"<html>"+b"a"*700,ctype))
                with TemporaryDirectory() as tmp:
                    dest=Path(tmp)/"original.xlsx"
                    with self.assertRaises(gate.EIOPAOriginalDownloadBlocked):
                        gate.bounded_single_request(url,dest,"HISTORICAL_INSURED_LOSSES",opener)
                    self.assertFalse(dest.exists())

    def test_midstream_original_read_failure_removes_partial_file(self):
        url=gate.URLS["HISTORICAL_INSURED_LOSSES"]
        class Midstream(Response):
            def __init__(self):
                super().__init__(url,b"PK\x03\x04"+b"S"*1200,gate.MIME)
                self.calls=0
            def read(self,n):
                self.calls+=1
                if self.calls==1:
                    return b"PK\x03\x04"+b"S"*650
                raise OSError("synthetic transport interrupted")
        opener=Opener(lambda req:Midstream())
        with TemporaryDirectory() as tmp:
            dest=Path(tmp)/"partial.xlsx"
            with self.assertRaises(gate.EIOPAOriginalDownloadBlocked):
                gate.bounded_single_request(url,dest,"HISTORICAL_INSURED_LOSSES",opener)
            self.assertFalse(dest.exists())
            self.assertEqual(opener.calls,1)

    def test_original_eiopa_workflow_is_manual_only_and_never_uploads_xlsx(self):
        workflow=(ROOT/".github/workflows/eiopa-2023-original-xlsx-provenance-one-shot.yml").read_text()
        trigger=workflow.split("\non:\n",1)[1].split("\npermissions:",1)[0]
        self.assertEqual(trigger,"  workflow_dispatch:\n")
        self.assertNotIn("pull_request:",trigger)
        self.assertIn("contents: read",workflow)
        self.assertIn("retention-days: 14",workflow)
        self.assertIn("eiopa-official-two-original-workbooks-metadata-NOT-CLAIMS.json",workflow)
        self.assertNotIn("path: *.xlsx",workflow)

    def test_oversized_original_response_fails_closed(self):
        url=gate.URLS["HISTORICAL_INSURED_LOSSES"]
        payload=b"PK\x03\x04"+b"A"*(gate.MAX_FILE_BYTES["HISTORICAL_INSURED_LOSSES"]+1)
        opener=Opener(lambda req:Response(url,payload,gate.MIME))
        with TemporaryDirectory() as tmp:
            dest=Path(tmp)/"original.xlsx"
            with self.assertRaises(gate.EIOPAOriginalDownloadBlocked):
                gate.bounded_single_request(url,dest,"HISTORICAL_INSURED_LOSSES",opener)
            self.assertFalse(dest.exists())
            self.assertEqual(opener.calls,1)


if __name__=="__main__":
    unittest.main()
