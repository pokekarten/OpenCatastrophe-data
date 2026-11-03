# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only single DOI public metadata probe controls; never network."""
from __future__ import annotations

from datetime import datetime, timezone
import io
import json
import unittest
from urllib import error

from research_runners.storm_v4_datacite_probe_v0 import (
    MAX_BYTES, MEDIA_TYPES, ProbeBlocked, TIMEOUT, URL, probe, verify_contract,
)


def sample_bytes() -> bytes:
    payload = {
        "data": {
            "type": "dois",
            "id": "10.4121/12706085.v4",
            "attributes": {
                "doi": "10.4121/12706085.v4",
                "types": {"resourceTypeGeneral": "Dataset"},
                "titles": [{"title": "STORM IBTrACS present climate synthetic tropical cyclone tracks"}],
                "publisher": "4TU.ResearchData",
                "version": "4",
                "rightsList": [{"rightsIdentifier": "CC0-1.0"}],
            },
        },
    }
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


class FakeResponse(io.BytesIO):
    status = 200

    def __init__(self, body: bytes, *, url: str = URL, media: str = "application/json", status: int = 200):
        super().__init__(body)
        self.url = url
        self.status = status
        self.headers = {"Content-Type": media}

    def geturl(self) -> str:
        return self.url


class STORMv4ProbeTests(unittest.TestCase):
    def test_reviewed_exact_contract(self):
        self.assertEqual(verify_contract()["probe_contract"]["mode"], "metadata_get")

    def test_one_exact_get_and_nonadmission_receipt(self):
        raw = sample_bytes()

        def fake_open(req, timeout):
            self.assertEqual(req.full_url, URL)
            self.assertEqual(req.get_method(), "GET")
            self.assertEqual(timeout, TIMEOUT)
            self.assertEqual(req.get_header("Accept"), "application/json")
            return FakeResponse(raw)

        receipt = probe(open_request=fake_open,
                        utc_clock=lambda: datetime(2026, 11, 3, 12, tzinfo=timezone.utc))
        self.assertEqual(receipt["response_bytes"], len(raw))
        self.assertEqual(receipt["retrieved_at_utc"], "2026-11-03T12:00:00+00:00")
        self.assertEqual(len(receipt["response_sha256"]), 64)
        self.assertTrue(receipt["metadata_identity_checked"])
        self.assertFalse(receipt["provider_body_persisted"])
        self.assertFalse(receipt["provider_track_file_downloaded"])
        self.assertFalse(receipt["model_input_approved"])

    def test_jsonapi_media_type_accepted(self):
        self.assertIn("application/vnd.api+json", MEDIA_TYPES)
        receipt = probe(open_request=lambda req, timeout:
                        FakeResponse(sample_bytes(), media="application/vnd.api+json; charset=utf-8"))
        self.assertEqual(receipt["response_media_type"], "application/vnd.api+json")

    def test_bad_status_redirect_media_and_oversize_blocked(self):
        for response in (
            FakeResponse(sample_bytes(), status=404),
            FakeResponse(sample_bytes(), url="https://evil.example/doi"),
            FakeResponse(sample_bytes(), media="text/html"),
            FakeResponse(b"x" * (MAX_BYTES + 1)),
            FakeResponse(b"not valid JSON"),
        ):
            with self.subTest(status=response.status, url=response.url), self.assertRaises(ProbeBlocked):
                probe(open_request=lambda req, timeout: response)

    def test_metadata_license_conflict_blocks(self):
        raw = sample_bytes().replace(b"CC0-1.0", b"CC-BY-4.0")
        with self.assertRaises(ProbeBlocked):
            probe(open_request=lambda req, timeout: FakeResponse(raw))

    def test_network_failure_blocks_without_retries(self):
        attempts = [0]

        def fails(req, timeout):
            attempts[0] += 1
            raise error.URLError("disconnected")

        with self.assertRaises(ProbeBlocked):
            probe(open_request=fails)
        self.assertEqual(attempts, [1])

    def test_naive_timestamp_blocked(self):
        with self.assertRaisesRegex(ProbeBlocked, "timezone-aware"):
            probe(open_request=lambda req, timeout: FakeResponse(sample_bytes()),
                  utc_clock=lambda: datetime(2026, 11, 3, 12))


if __name__ == "__main__":
    unittest.main()
