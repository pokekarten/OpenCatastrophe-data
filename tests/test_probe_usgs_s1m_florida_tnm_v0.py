# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline/synthetic negative and positive cases for one fixed TNM metadata GET."""
from __future__ import annotations

import hashlib
import json
import unittest
from unittest.mock import patch

from scripts import probe_usgs_s1m_florida_tnm_v0 as s


class Reply:
    def __init__(self, raw: bytes, *, url: str = s.URL, status: int = 200,
                 media: str = "application/json", encoding: str = "identity",
                 length: str | None = None):
        self.raw = raw
        self.url = url
        self.status = status
        self.headers = {
            "Content-Type": media,
            "Content-Encoding": encoding,
        }
        if length is not None:
            self.headers["Content-Length"] = length

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def geturl(self):
        return self.url

    def read(self, count: int):
        return self.raw[:count]


def example() -> dict:
    return {
        "total": 1,
        "errors": [],
        "messages": ["Retrieved 1 item(s)"],
        "items": [{
            "title": s.PILOT_TITLE,
            "sourceId": s.PILOT_SOURCE_ID,
            "datasets": [],
            "format": "GeoTIFF",
            "downloadURL": s.PILOT_DOWNLOAD_URL,
            "boundingBox": {
                "minX": -81.0028601420002,
                "minY": 25.92070859857935,
                "maxX": -80.8895404313893,
                "maxY": 26.025030076412904,
            },
        }],
    }


def raw_example() -> bytes:
    return json.dumps(example(), sort_keys=True, separators=(",", ":")).encode("utf-8")


class ProbeTests(unittest.TestCase):
    def test_frozen_access_contract(self):
        self.assertEqual(s.verify_frozen_contract()["status"], "probe_ready")

    def test_fixed_query_no_caller_parameter(self):
        self.assertIn("datasets=Seamless%201-m%20DEM%20%28S1M%29", s.URL)
        self.assertTrue(s.URL.endswith("&max=1&offset=0"))

    def test_original_bytes_pinned_identity(self):
        self.assertEqual(s.inspect_original(raw_example())["source_id"], s.PILOT_SOURCE_ID)

    def test_bounded_success_injected_no_network(self):
        original = raw_example()
        def fake_open(req, timeout):
            self.assertEqual(req.full_url, s.URL)
            self.assertEqual(req.get_method(), "GET")
            self.assertEqual(timeout, 20)
            return Reply(original, length=str(len(original)))
        result = s.probe(open_request=fake_open)
        self.assertEqual(result["original_response_sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual(result["source_id"], s.PILOT_SOURCE_ID)
        self.assertFalse(result["original_geotiff_downloaded"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["model_input_admitted"])

    def test_duplicate_json_key_blocked(self):
        raw = b'{"total":1,"total":1,"items":[]}'
        with self.assertRaises(s.ProbeBlocked):
            s.inspect_original(raw)

    def test_bad_provider_id_blocked(self):
        j = example()
        j["items"][0]["sourceId"] = "b" * 24
        with self.assertRaises(s.ProbeBlocked):
            s.inspect_original(json.dumps(j).encode())

    def test_legacy_product_blocked(self):
        j = example()
        j["items"][0]["datasets"] = ["Digital Elevation Model (DEM) 1 meter"]
        with self.assertRaises(s.ProbeBlocked):
            s.inspect_original(json.dumps(j).encode())

    def test_multiple_results_blocked(self):
        j = example()
        j["total"] = 2
        with self.assertRaises(s.ProbeBlocked):
            s.inspect_original(json.dumps(j).encode())

    def test_unsafe_product_url_blocked(self):
        j = example()
        j["items"][0]["downloadURL"] = "https://example.org/other.tif"
        with self.assertRaises(s.ProbeBlocked):
            s.inspect_original(json.dumps(j).encode())

    def test_response_over_byte_limit_blocked(self):
        with self.assertRaises(s.ProbeBlocked):
            s.inspect_original(b" " * (s.MAX_BYTES + 1))

    def test_unexpected_redirect_blocked(self):
        with self.assertRaises(s.ProbeBlocked):
            s.probe(open_request=lambda req, timeout: Reply(raw_example(),
                    url="https://untrusted.invalid/other"))

    def test_compressed_body_blocked(self):
        with self.assertRaises(s.ProbeBlocked):
            s.probe(open_request=lambda req, timeout: Reply(raw_example(), encoding="gzip"))

    def test_media_type_blocked(self):
        with self.assertRaises(s.ProbeBlocked):
            s.probe(open_request=lambda req, timeout: Reply(raw_example(), media="text/html"))

    def test_claimed_huge_content_length_blocked(self):
        with self.assertRaises(s.ProbeBlocked):
            s.probe(open_request=lambda req, timeout: Reply(raw_example(), length=str(s.MAX_BYTES+1)))

    def test_invalid_raw_json_blocked(self):
        with self.assertRaises(s.ProbeBlocked):
            s.inspect_original(b'{"items": [NaN]}')

    def test_cli_no_live_gate(self):
        with patch("sys.argv", ["prog"]):
            with self.assertRaises(SystemExit) as err:
                s.main()
        self.assertEqual(err.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
