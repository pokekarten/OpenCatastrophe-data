# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest

from scripts import acquire_cems_europe_mask_receipts as mod


class _Socket:
    def settimeout(self, _timeout: float) -> None:
        pass


class _Response:
    def __init__(self, url: str, payload: bytes, *, final_url: str | None = None):
        self.status = 200
        self._url = final_url or url
        self._payload = payload
        self._offset = 0
        self._oc_response_socket = _Socket()
        self.headers = {
            "Content-Type": "image/tiff",
            "Content-Length": str(len(payload)),
        }

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def geturl(self) -> str:
        return self._url

    def read(self, size: int) -> bytes:
        if self._offset >= len(self._payload):
            return b""
        chunk = self._payload[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk


class CemsMaskReceiptTests(unittest.TestCase):
    def test_acquires_both_frozen_masks_in_fixed_order(self) -> None:
        payloads = {
            mod.BASE_URL + "Europe_permanent_water_bodies.tif": b"II*\x00permanent-water",
            mod.BASE_URL + "Europe_spurious_depth_areas.tif": b"II*\x00spurious-depth",
        }
        seen: list[str] = []

        def opener(request, _timeout):
            seen.append(request.full_url)
            return _Response(request.full_url, payloads[request.full_url])

        result = mod.acquire_cems_mask_receipts(
            opener=opener,
            clock=lambda: "2026-09-06T18:20:00Z",
            monotonic=lambda: 1.0,
        )

        expected_urls = [mod.BASE_URL + filename for _kind, filename in mod.ASSETS]
        self.assertEqual(seen, expected_urls)
        self.assertEqual(result["schema_version"], "oc-cems-europe-mask-receipts-v1")
        self.assertEqual(result["source_issue"], 809)
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["geotiff_semantics_verified"])
        self.assertFalse(result["mask_values_inspected"])
        self.assertFalse(result["benchmark_use_authorized"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

        receipts = result["receipts"]
        self.assertEqual([item["mask_kind"] for item in receipts], ["permanent_water", "spurious_depth"])
        for receipt, expected_url in zip(receipts, expected_urls, strict=True):
            payload = payloads[expected_url]
            self.assertEqual(receipt["requested_url"], expected_url)
            self.assertEqual(receipt["final_url"], expected_url)
            self.assertEqual(receipt["byte_count"], len(payload))
            self.assertEqual(receipt["sha256"], hashlib.sha256(payload).hexdigest())
            self.assertFalse(receipt["external_bytes_persisted"])
            self.assertFalse(receipt["geotiff_semantics_verified"])
            self.assertFalse(receipt["mask_values_inspected"])

    def test_rejects_redirect_drift(self) -> None:
        def opener(request, _timeout):
            return _Response(request.full_url, b"II*\x00mask", final_url="https://example.com/mask.tif")

        with self.assertRaisesRegex(mod.CemsMaskReceiptError, "final URL drifted"):
            mod.acquire_cems_mask_receipts(opener=opener, monotonic=lambda: 1.0)

    def test_rejects_non_tiff_payload(self) -> None:
        def opener(request, _timeout):
            return _Response(request.full_url, b"not-a-tiff")

        with self.assertRaisesRegex(mod.CemsMaskReceiptError, "TIFF/BigTIFF signature"):
            mod.acquire_cems_mask_receipts(opener=opener, monotonic=lambda: 1.0)

    def test_allowlist_has_exactly_two_code_owned_urls(self) -> None:
        self.assertEqual(len(mod.ALLOWED_URLS), 2)
        self.assertTrue(all(mod._safe_source_url(url) for url in mod.ALLOWED_URLS))
        self.assertFalse(mod._safe_source_url(mod.BASE_URL + "Europe_RP10_filled_depth.tif"))
        self.assertFalse(mod._safe_source_url("http://jeodpp.jrc.ec.europa.eu/x.tif"))


if __name__ == "__main__":
    unittest.main()
