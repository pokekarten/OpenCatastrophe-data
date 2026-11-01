# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict synthetic-only EMSC bounded source-probe tests."""
from __future__ import annotations

from datetime import datetime, timezone
import io
import json
import unittest

from scripts.probe_emsc_fdsn_event_v0 import (
    EMSCProbeError,
    MAX_RESPONSE_BYTES,
    PROBE_URL,
    inspect_json_bytes,
    probe,
    verify_frozen_contract,
)


def fake_event() -> dict:
    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "id": "synthetic-one",
            "geometry": {"type": "Point", "coordinates": [12.5, 45.0, 11.0]},
            "properties": {"source_id": "synthetic-not-provider-data", "mag": 5.2},
        }],
    }


def raw_event() -> bytes:
    return json.dumps(fake_event(), sort_keys=True).encode("utf-8")


class SyntheticResponse(io.BytesIO):
    status = 200

    def __init__(self, raw: bytes, content_type: str = "application/json", url: str = PROBE_URL):
        super().__init__(raw)
        self.headers = {"Content-Type": content_type}
        self.url = url

    def geturl(self) -> str:
        return self.url


class EMSCEventProbeTests(unittest.TestCase):
    def test_repository_contract_is_exact_and_probe_ready(self) -> None:
        data = verify_frozen_contract()
        self.assertEqual(data["request_contract"]["allowed_operations"], ["latest_event_json"])
        self.assertEqual(data["status"], "probe_ready")

    def test_synthetic_geojson_one_event(self) -> None:
        shape = inspect_json_bytes(raw_event())
        self.assertEqual(shape["event_count"], 1)
        self.assertEqual(shape["geometry"], "Point")

    def test_injected_network_probe_returns_only_provenance_receipt(self) -> None:
        def fake_open(req, timeout):
            self.assertEqual(req.full_url, PROBE_URL)
            self.assertEqual(req.get_method(), "GET")
            self.assertEqual(timeout, 30)
            self.assertEqual(req.get_header("Accept"), "application/json")
            return SyntheticResponse(raw_event())

        receipt = probe(
            open_request=fake_open,
            utc_clock=lambda: datetime(2026, 11, 1, tzinfo=timezone.utc),
        )
        self.assertEqual(receipt["http_status"], 200)
        self.assertEqual(receipt["event_count"], 1)
        self.assertEqual(receipt["response_bytes"], len(raw_event()))
        self.assertEqual(len(receipt["response_sha256"]), 64)
        self.assertFalse(receipt["external_bytes_persisted"])
        self.assertFalse(receipt["model_input_admitted"])
        self.assertNotIn("features", receipt)
        self.assertNotIn("coordinates", receipt)
        self.assertNotIn("source_id_value", receipt)

    def test_rejects_duplicate_properties_nonfinite_and_wrong_shape(self) -> None:
        invalids = [
            b'{"type":"FeatureCollection","type":"FeatureCollection","features":[]}',
            b'{"type":"FeatureCollection","features":[NaN]}',
            b'{"type":"FeatureCollection","features":[]}',
            b'{"type":"Feature","features":[]}',
            b'',
            b'not json',
            b'\xff',
            b"x" * (MAX_RESPONSE_BYTES + 1),
        ]
        for raw in invalids:
            with self.subTest(raw=raw[:40]):
                with self.assertRaises(EMSCProbeError):
                    inspect_json_bytes(raw)

    def test_rejects_more_than_one_event_boolean_and_out_of_bounds_coords(self) -> None:
        payload = fake_event()
        payload["features"].append(payload["features"][0])
        with self.assertRaisesRegex(EMSCProbeError, "exactly one"):
            inspect_json_bytes(json.dumps(payload).encode())
        for coords in ([True, 1], [181, 0], [0, -91], [float("inf"), 2], [12]):
            payload = fake_event()
            payload["features"][0]["geometry"]["coordinates"] = coords
            with self.subTest(coords=coords):
                with self.assertRaises(EMSCProbeError):
                    inspect_json_bytes(json.dumps(payload).encode())

    def test_rejects_redirect_http_error_media_mismatch_and_oversize(self) -> None:
        cases = [
            SyntheticResponse(raw_event(), url="https://example.org/redirect"),
            SyntheticResponse(raw_event(), content_type="text/html"),
            SyntheticResponse(b"x" * (MAX_RESPONSE_BYTES + 1)),
        ]
        for response in cases:
            with self.subTest(url=response.geturl(), content_type=response.headers["Content-Type"]):
                with self.assertRaises(EMSCProbeError):
                    probe(open_request=lambda req, timeout: response)

    def test_receipt_requires_timezone_aware_clock(self) -> None:
        with self.assertRaisesRegex(EMSCProbeError, "timezone-aware"):
            probe(
                open_request=lambda req, timeout: SyntheticResponse(raw_event()),
                utc_clock=lambda: datetime(2026, 11, 1),
            )


if __name__ == "__main__":
    unittest.main()
