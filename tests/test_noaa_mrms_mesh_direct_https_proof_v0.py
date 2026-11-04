# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Pure synthetic, offline regressions of fixed NOAA HTTP provenance gate."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from research_runners import noaa_mrms_mesh_direct_https_proof_v0 as direct
from research_runners import noaa_mrms_mesh_original_preflight_v0 as offline

ROOT = Path(__file__).resolve().parents[1]


def _section(number: int, size: int) -> bytearray:
    a = bytearray(size)
    a[:4] = size.to_bytes(4, "big")
    a[4] = number
    return a


def _minimal_grib2() -> bytes:
    """Minimal synthetic framing. NO source pixels or valid scientific data."""
    sec1 = _section(1, 21)
    sec1[5:7] = (161).to_bytes(2, "big")
    sec1[12:14] = (2020).to_bytes(2, "big")
    sec1[14:19] = bytes([10, 14, 0, 0, 25])
    sec3 = _section(3, 14)
    sec3[6:10] = (100).to_bytes(4, "big")
    sec4 = _section(4, 11)
    sec4[9] = 3
    sec4[10] = 28
    body = b"".join(map(bytes, (sec1, sec3, sec4,
                                _section(5, 11), _section(6, 6), _section(7, 6))))
    return b"GRIB\x00\x00" + bytes([209, 2]) + (16 + len(body) + 4).to_bytes(8, "big") + body + b"7777"


class FakeResponse(io.BytesIO):
    def __init__(self, body: bytes, url: str, *, status: int = 200,
                 content_encoding: str = "identity", content_length: str | None = None):
        super().__init__(body)
        self._url = url
        self.status = status
        self.headers = {"Content-Encoding": content_encoding}
        if content_length is not None:
            self.headers["Content-Length"] = content_length

    def geturl(self):
        return self._url


class FakeOpener:
    def __init__(self, response: FakeResponse):
        self.response = response
        self.requests = []

    def open(self, request, timeout=None):
        self.requests.append((request, timeout))
        return self.response


class NOAAFixedDirectHTTPSProofTests(unittest.TestCase):
    def test_valid_synthetic_receipt_keeps_admission_blocked(self) -> None:
        fake_bytes = gzip.compress(_minimal_grib2(), mtime=0)
        pinned = dict(offline.SOURCE_OBJECTS["mesh"])
        pinned["compressed_size"] = len(fake_bytes)
        pinned["compressed_sha256"] = hashlib.sha256(fake_bytes).hexdigest()
        url = direct.ORIGIN + pinned["key"]
        opener = FakeOpener(FakeResponse(fake_bytes, url,
                                         content_length=str(len(fake_bytes))))
        with patch.dict(offline.SOURCE_OBJECTS, {"mesh": pinned}):
            result = direct.fetch_and_audit("mesh", opener)
        self.assertEqual(result["direct_http_status"], 200)
        self.assertTrue(result["gzip_crc32_verified"])
        self.assertTrue(result["fixed_object_identity_verified"])
        self.assertFalse(result["source_bytes_written_to_disk"])
        self.assertFalse(result["source_bytes_uploaded_to_github"])
        self.assertFalse(result["scientific_model_admission"])
        self.assertFalse(result["raw_grid_pixels_decoded"])
        self.assertFalse(result["physical_hail_intensity_validated"])
        self.assertFalse(result["insured_losses_or_tiv_inferred"])
        self.assertEqual(opener.requests[0][1], 15)
        self.assertEqual(opener.requests[0][0].full_url, url)
        self.assertEqual(result["product_definition"]["parameter_number"], 28)
        self.assertNotIn("pixels", json.dumps(result).lower().split("raw_grid_pixels_decoded")[0])

    def test_unknown_product_rejected_without_network(self):
        with self.assertRaisesRegex(direct.DirectSourceProofError, "unknown"):
            direct.fetch_and_audit("other", FakeOpener(FakeResponse(b"", "bad")))

    def test_fail_closed_redirect_status_encoding_and_content_length(self):
        source = offline.SOURCE_OBJECTS["mesh"]
        url = direct.ORIGIN + source["key"]
        for test, kwargs in (
            ("redirect", {"url": "https://other.example/object"}),
            ("status", {"status": 206}),
            ("encoding", {"content_encoding": "gzip"}),
            ("length", {"content_length": "999"}),
            ("unparseable_length", {"content_length": "x"}),
        ):
            with self.subTest(test=test):
                response = FakeResponse(b"abc", url, **kwargs)
                with self.assertRaises(direct.DirectSourceProofError):
                    direct.fetch_and_audit("mesh", FakeOpener(response))

    def test_truncated_hash_and_oversized_download_blocked(self):
        url = direct.ORIGIN + offline.SOURCE_OBJECTS["mesh"]["key"]
        for data in (b"abc", b"x" * (offline.MAX_COMPRESSED_BYTES + 1)):
            with self.subTest(size=len(data)):
                with self.assertRaises(direct.DirectSourceProofError):
                    direct.fetch_and_audit("mesh", FakeOpener(FakeResponse(data, url)))

    def test_http_error_blocked_with_no_data_or_token_logging(self):
        import urllib.error
        err = urllib.error.HTTPError(
            direct.ORIGIN + offline.SOURCE_OBJECTS["mesh"]["key"],
            code=302, msg="Redirect denied", hdrs=None, fp=None)
        class RaisingOpener:
            def open(self, *args, **kwargs):
                raise err
        with self.assertRaisesRegex(direct.DirectSourceProofError, "HTTPS request failed"):
            direct.fetch_and_audit("mesh", RaisingOpener())

    def test_no_uncontrolled_cli_source_selection(self):
        result = subprocess.run(
            [sys.executable, "-m",
             "research_runners.noaa_mrms_mesh_direct_https_proof_v0",
             "--product", "unapproved"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("https://", result.stdout)


if __name__ == "__main__":
    unittest.main()
