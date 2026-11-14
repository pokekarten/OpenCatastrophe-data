# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline test harness; no HTTP calls, original GeoParquet or licensed rows."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import tempfile
import unittest

from research_runners.eurocrops_jrc_acquire_v0 import (
    Blocked, FILE, SOURCE, acquire, allowed,
)


class Response:
    def __init__(self, content: bytes, *, url: str = SOURCE,
                 content_length: str | None = None, status: int = 200):
        self._stream = BytesIO(content)
        self._url = url
        self.status = status
        self.headers = {}
        if content_length is not None:
            self.headers["Content-Length"] = content_length

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._stream.close()

    def geturl(self):
        return self._url

    def read(self, n: int) -> bytes:
        return self._stream.read(n)


class JrcAcquisitionTests(unittest.TestCase):
    def test_limited_explicit_source_and_same_publisher_redirect(self):
        self.assertTrue(allowed(SOURCE))
        self.assertTrue(allowed(
            "https://jeodpp.jrc.ec.europa.eu/ftp/public/JRC-OpenData/DRLL/"
            "EuroCropsV2/gpqtv202/de4_2023.parquet"
        ))
        for bad in (
            SOURCE + "?v=1",
            SOURCE.replace("de4_2023", "dea_2023"),
            SOURCE.replace("https:", "http:"),
            SOURCE.replace("jeodpp.jrc.ec.europa.eu", "example.com"),
        ):
            self.assertFalse(allowed(bad))

    def test_hashed_receipt_and_no_overwrite(self):
        content = b"PAR1" + b"fake bounded invented test data" + b"PAR1"
        with tempfile.TemporaryDirectory() as name:
            out = Path(name)
            result = acquire(
                out, open_response=lambda request: Response(
                    content, content_length=str(len(content)),
                ),
            )
            self.assertEqual(result["original_bytes"], len(content))
            self.assertEqual((out / FILE).read_bytes(), content)
            self.assertEqual(len(result["original_sha256"]), 64)
            self.assertFalse(result["cat_model_ready"])
            self.assertFalse(result["publisher_checksum_independently_verified"])
            with self.assertRaisesRegex(Blocked, "already exists"):
                acquire(out, open_response=lambda request: self.fail("must not fetch"))

    def test_untrusted_final_url_blocks_without_writing(self):
        with tempfile.TemporaryDirectory() as name:
            out = Path(name)
            with self.assertRaisesRegex(Blocked, "unexpected final"):
                acquire(
                    out,
                    open_response=lambda request: Response(
                        b"PAR1xxxxxxxxPAR1", url="https://example.com/a.parquet"
                    ),
                )
            self.assertFalse((out / FILE).exists())

    def test_bounded_stream_failure_cleans_partial(self):
        content = b"PAR1" + b"x" * 100 + b"PAR1"
        with tempfile.TemporaryDirectory() as name:
            out = Path(name)
            with self.assertRaisesRegex(Blocked, "download exceeded"):
                acquire(
                    out, open_response=lambda request: Response(content),
                    byte_limit=32,
                )
            self.assertFalse((out / FILE).exists())

    def test_non_parquet_cleans_partial(self):
        with tempfile.TemporaryDirectory() as name:
            out = Path(name)
            with self.assertRaisesRegex(Blocked, "not Parquet"):
                acquire(
                    out, open_response=lambda request: Response(
                        b"<html>not really Parquet</html>"
                    ),
                )
            self.assertFalse((out / FILE).exists())

    def test_source_length_mismatch_cleans_partial(self):
        with tempfile.TemporaryDirectory() as name:
            out = Path(name)
            with self.assertRaisesRegex(Blocked, "mismatch"):
                acquire(
                    out, open_response=lambda request: Response(
                        b"PAR1fakebytesPAR1", content_length="19",
                    ),
                )
            self.assertFalse((out / FILE).exists())


if __name__ == "__main__":
    unittest.main()
