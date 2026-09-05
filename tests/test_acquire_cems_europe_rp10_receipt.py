# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import inspect
import socket
import types
import unittest
from unittest import mock

from scripts import acquire_cems_europe_rp10_receipt as mod


class FakeResponse:
    def __init__(self, payload: bytes, *, url: str = mod.SOURCE_URL, status: int = 200, headers=None):
        self._payload = payload
        self._offset = 0
        self._url = url
        self.status = status
        self.headers = dict(headers or {})
        self.read_calls = 0
        self.socket_timeouts: list[float] = []
        self._oc_response_socket = types.SimpleNamespace(
            settimeout=self.socket_timeouts.append
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def geturl(self) -> str:
        return self._url

    def read(self, size: int) -> bytes:
        self.read_calls += 1
        chunk = self._payload[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk


class Monotonic:
    def __init__(self) -> None:
        self.value = 100.0

    def __call__(self) -> float:
        self.value += 0.001
        return self.value


def run_with(response: FakeResponse):
    observed = {}

    def opener(request, timeout):
        observed["url"] = request.full_url
        observed["method"] = request.get_method()
        observed["timeout"] = timeout
        observed["accept_encoding"] = request.headers.get("Accept-encoding")
        return response

    result = mod.acquire_cems_rp10_receipt(
        opener=opener,
        clock=lambda: "2026-09-04T16:40:00Z",
        monotonic=Monotonic(),
    )
    return result, observed


class CemsRp10ReceiptTests(unittest.TestCase):
    def test_success_is_exact_receipt_only(self) -> None:
        payload = b"II*\x00" + b"synthetic-tiff-bytes"
        response = FakeResponse(
            payload,
            headers={"Content-Type": "image/tiff", "Content-Length": str(len(payload))},
        )
        result, observed = run_with(response)

        self.assertEqual(observed["url"], mod.SOURCE_URL)
        self.assertEqual(observed["method"], "GET")
        self.assertEqual(observed["accept_encoding"], "identity")
        self.assertGreater(observed["timeout"], 0)
        self.assertEqual(result["dataset_id"], mod.DATASET_ID)
        self.assertEqual(result["source_issue"], 793)
        self.assertEqual(result["release"], "3.1.1")
        self.assertEqual(result["return_period_years"], 10)
        self.assertEqual(result["filename"], "Europe_RP10_filled_depth.tif")
        self.assertEqual(result["byte_count"], len(payload))
        self.assertEqual(result["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(result["retrieved_at"], "2026-09-04T16:40:00Z")
        self.assertIs(result["external_bytes_persisted"], False)
        self.assertIs(result["geotiff_semantics_verified"], False)
        self.assertIs(result["benchmark_use_authorized"], False)
        self.assertIs(result["publication_authorized"], False)
        self.assertIs(result["model_use_authorized"], False)
        self.assertNotIn("payload", result)
        self.assertNotIn("values", result)

    def test_public_surface_has_no_target_selector(self) -> None:
        params = set(inspect.signature(mod.acquire_cems_rp10_receipt).parameters)
        self.assertEqual(params, {"opener", "clock", "monotonic"})
        for forbidden in {"url", "path", "filename", "return_period", "provider", "dataset_id"}:
            self.assertNotIn(forbidden, params)

    def test_final_url_drift_fails_closed(self) -> None:
        response = FakeResponse(
            b"II*\x00x",
            url="https://example.com/other.tif",
            headers={"Content-Type": "image/tiff", "Content-Length": "5"},
        )
        with self.assertRaisesRegex(mod.CemsRp10ReceiptError, "final URL drifted"):
            run_with(response)
        self.assertEqual(response.read_calls, 0)

    def test_non_200_status_fails_before_body_read(self) -> None:
        response = FakeResponse(
            b"II*\x00x",
            status=206,
            headers={"Content-Type": "image/tiff", "Content-Length": "5"},
        )
        with self.assertRaisesRegex(mod.CemsRp10ReceiptError, "exact HTTP 200"):
            run_with(response)
        self.assertEqual(response.read_calls, 0)

    def test_media_type_fails_before_body_read(self) -> None:
        response = FakeResponse(
            b"II*\x00x",
            headers={"Content-Type": "text/html", "Content-Length": "5"},
        )
        with self.assertRaisesRegex(mod.CemsRp10ReceiptError, "media type"):
            run_with(response)
        self.assertEqual(response.read_calls, 0)

    def test_declared_oversize_fails_before_body_read(self) -> None:
        response = FakeResponse(
            b"II*\x00x",
            headers={"Content-Type": "image/tiff", "Content-Length": str(mod.MAX_BYTES + 1)},
        )
        with self.assertRaisesRegex(mod.CemsRp10ReceiptError, "Content-Length"):
            run_with(response)
        self.assertEqual(response.read_calls, 0)

    def test_actual_oversize_fails_closed(self) -> None:
        payload = b"II*\x00abcdef"
        response = FakeResponse(payload, headers={"Content-Type": "image/tiff"})
        with mock.patch.object(mod, "MAX_BYTES", 8), mock.patch.object(mod, "CHUNK_SIZE", 4):
            with self.assertRaisesRegex(mod.CemsRp10ReceiptError, "exceeded bounded byte size"):
                run_with(response)

    def test_declared_length_mismatch_fails_closed(self) -> None:
        payload = b"II*\x00abc"
        response = FakeResponse(
            payload,
            headers={"Content-Type": "application/octet-stream", "Content-Length": str(len(payload) + 1)},
        )
        with self.assertRaisesRegex(mod.CemsRp10ReceiptError, "disagrees with Content-Length"):
            run_with(response)

    def test_non_tiff_payload_fails_closed(self) -> None:
        payload = b"<html>not a tif</html>"
        response = FakeResponse(
            payload,
            headers={"Content-Type": "image/tiff", "Content-Length": str(len(payload))},
        )
        with self.assertRaisesRegex(mod.CemsRp10ReceiptError, "TIFF/BigTIFF signature"):
            run_with(response)

    def test_content_encoding_must_be_identity(self) -> None:
        response = FakeResponse(
            b"II*\x00x",
            headers={
                "Content-Type": "image/tiff",
                "Content-Length": "5",
                "Content-Encoding": "gzip",
            },
        )
        with self.assertRaisesRegex(mod.CemsRp10ReceiptError, "content encoding"):
            run_with(response)
        self.assertEqual(response.read_calls, 0)

    def test_stream_read_timeout_tracks_remaining_total_deadline(self) -> None:
        payload = b"II*\x00" + b"abcdefgh"
        response = FakeResponse(
            payload,
            headers={"Content-Type": "image/tiff", "Content-Length": str(len(payload))},
        )
        with mock.patch.object(mod, "CHUNK_SIZE", 4):
            run_with(response)
        self.assertEqual(len(response.socket_timeouts), response.read_calls)
        self.assertGreaterEqual(len(response.socket_timeouts), 2)
        self.assertTrue(
            all(
                0 < later < earlier
                for earlier, later in zip(response.socket_timeouts, response.socket_timeouts[1:])
            )
        )

    def test_deadline_response_retains_socket_after_connection_close(self) -> None:
        response_socket, peer = socket.socketpair()
        response = mod.DeadlineHTTPResponse(response_socket)
        try:
            self.assertIs(
                mod.PublicOnlyHTTPSConnection.response_class,
                mod.DeadlineHTTPResponse,
            )
            self.assertIs(response._oc_response_socket, response_socket)
            response_socket.close()
            mod._set_response_timeout(response, 0.25)
            self.assertEqual(response_socket.gettimeout(), 0.25)
        finally:
            response.close()
            response_socket.close()
            peer.close()

    def test_missing_response_socket_fails_closed(self) -> None:
        response = FakeResponse(
            b"II*\x00x",
            headers={"Content-Type": "image/tiff", "Content-Length": "5"},
        )
        del response._oc_response_socket
        with self.assertRaisesRegex(mod.CemsRp10ReceiptError, "cannot enforce the total deadline"):
            run_with(response)
        self.assertEqual(response.read_calls, 0)

    def test_url_constant_is_exact_https_without_selectors(self) -> None:
        self.assertTrue(mod._safe_source_url(mod.SOURCE_URL))
        self.assertFalse(mod._safe_source_url(mod.SOURCE_URL + "?x=1"))
        self.assertFalse(mod._safe_source_url(mod.SOURCE_URL.replace("https://", "http://")))

    def test_dns_classifier_rejects_non_global_address(self) -> None:
        infos = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))]
        with self.assertRaisesRegex(mod.CemsRp10ReceiptError, "non-global"):
            mod._classify_public_sockaddrs(infos)

    def test_dns_classifier_rejects_returned_port_drift(self) -> None:
        infos = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 8443))]
        with self.assertRaisesRegex(mod.CemsRp10ReceiptError, "provider port"):
            mod._classify_public_sockaddrs(infos)

    def test_dns_classifier_accepts_unique_public_addresses(self) -> None:
        infos = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443)),
        ]
        admitted = mod._classify_public_sockaddrs(infos)
        self.assertEqual(len(admitted), 1)

    def test_dns_resolution_rejects_provider_drift(self) -> None:
        with self.assertRaisesRegex(mod.CemsRp10ReceiptError, "provider boundary"):
            mod._resolve_with_timeout("example.com", 443, 1.0)
        with self.assertRaisesRegex(mod.CemsRp10ReceiptError, "provider boundary"):
            mod._resolve_with_timeout(mod.EXPECTED_HOST, 8443, 1.0)

    def test_redirect_handler_rejects_even_same_target(self) -> None:
        handler = mod.NoRedirectHandler()
        with self.assertRaisesRegex(mod.CemsRp10ReceiptError, "redirect is forbidden"):
            handler.redirect_request(None, None, 302, "Found", {}, mod.SOURCE_URL)


if __name__ == "__main__":
    unittest.main()
