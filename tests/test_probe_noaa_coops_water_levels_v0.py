# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline negative/positive gates for the frozen NOAA CO-OPS provider probe."""
from __future__ import annotations

from datetime import datetime, timezone
import io
import json
import unittest

from scripts.probe_noaa_coops_water_levels_v0 import (
    COOPSProbeError, MAX_BYTES, URL, inspect_json_bytes, probe,
    verify_frozen_contract,
)


def payload() -> dict:
    return {
        "metadata": {
            "id": "9414290", "name": "San Francisco",
            "lat": "37.8063", "lon": "-122.4659",
        },
        "data": [
            {"t": "2026-01-01 00:00", "v": "-0.098", "s": "0.033", "f": "0,0,0,0", "q": "v"},
            {"t": "2026-01-01 00:06", "v": "-0.078", "s": "0.035", "f": "0,0,0,0", "q": "v"},
        ],
    }


def encode(value: dict) -> bytes:
    return json.dumps(value, separators=(",", ":"), allow_nan=False).encode("utf-8")


class Response:
    def __init__(self, raw: bytes, *, url: str = URL, status: int = 200,
                 media: str = "application/json; charset=utf-8"):
        self.body = io.BytesIO(raw)
        self.url = url
        self.status = status
        self.headers = {"Content-Type": media}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.body.close()

    def geturl(self):
        return self.url

    def read(self, limit):
        return self.body.read(limit)


class NOAACoopsProbeTests(unittest.TestCase):
    def test_frozen_source_contract(self):
        contract = verify_frozen_contract()
        self.assertEqual(contract["status"], "probe_ready")
        self.assertIn("station=9414290", contract["request_contract"]["parameter_rules"])
        self.assertEqual(contract["probe_contract"]["mode"], "provider_specific")

    def test_one_day_shape_has_no_measurement_values_in_result(self):
        summary = inspect_json_bytes(encode(payload()))
        self.assertEqual(summary["observation_rows"], 2)
        self.assertEqual(summary["datum"], "MLLW")
        self.assertFalse(summary["quality_scientifically_assessed"])
        self.assertNotIn("data", summary)
        self.assertNotIn("height", summary)

    def test_mock_network_emits_receipt_only(self):
        raw = encode(payload())
        calls = []
        def open_request(req, timeout):
            calls.append((req.full_url, req.get_method(), timeout))
            return Response(raw)
        result = probe(open_request=open_request,
                       utc_clock=lambda: datetime(2026, 11, 2, 8, 0, tzinfo=timezone.utc))
        self.assertEqual(calls, [(URL, "GET", 30)])
        self.assertEqual(result["observation_rows"], 2)
        self.assertEqual(result["response_bytes"], len(raw))
        self.assertEqual(result["retrieved_at_utc"], "2026-11-02T08:00:00+00:00")
        self.assertFalse(result["original_bytes_persisted"])
        self.assertFalse(result["model_input_admitted"])
        self.assertNotIn("-0.098", json.dumps(result))

    def test_rejects_provider_error(self):
        with self.assertRaises(COOPSProbeError):
            inspect_json_bytes(encode({"error": {"message": "invalid request"}}))

    def test_rejects_wrong_station(self):
        value = payload()
        value["metadata"]["id"] = "8518750"
        with self.assertRaises(COOPSProbeError):
            inspect_json_bytes(encode(value))

    def test_rejects_duplicate_provider_property(self):
        with self.assertRaises(COOPSProbeError):
            inspect_json_bytes(b'{"metadata":{"id":"9414290","id":"9414290"},"data":[]}')

    def test_rejects_nonfinite_provider_measurement(self):
        value = payload()
        value["data"][0]["v"] = "NaN"
        with self.assertRaises(COOPSProbeError):
            inspect_json_bytes(encode(value))

    def test_rejects_outside_day_and_wrong_interval(self):
        for timestamp in ("2026-01-02 00:00", "2026-01-01 00:07", "not-a-date"):
            value = payload()
            value["data"][0]["t"] = timestamp
            with self.subTest(timestamp=timestamp), self.assertRaises(COOPSProbeError):
                inspect_json_bytes(encode(value))

    def test_rejects_nonmonotonic_or_repeated_timestamps(self):
        value = payload()
        value["data"][1]["t"] = value["data"][0]["t"]
        with self.assertRaises(COOPSProbeError):
            inspect_json_bytes(encode(value))

    def test_rejects_missing_quality_flag(self):
        value = payload()
        value["data"][0].pop("q")
        with self.assertRaises(COOPSProbeError):
            inspect_json_bytes(encode(value))

    def test_rejects_more_than_one_day(self):
        value = payload()
        value["data"] = value["data"] * 121
        with self.assertRaises(COOPSProbeError):
            inspect_json_bytes(encode(value))

    def test_rejects_large_response_and_unexpected_media(self):
        with self.assertRaises(COOPSProbeError):
            inspect_json_bytes(b"x" * (MAX_BYTES + 1))
        with self.assertRaises(COOPSProbeError):
            probe(open_request=lambda req, timeout: Response(
                encode(payload()), media="text/html"
            ))

    def test_rejects_redirect(self):
        with self.assertRaises(COOPSProbeError):
            probe(open_request=lambda req, timeout: Response(
                encode(payload()), url="https://example.org/"
            ))

    def test_rejects_naive_receipt_clock(self):
        with self.assertRaises(COOPSProbeError):
            probe(
                open_request=lambda req, timeout: Response(encode(payload())),
                utc_clock=lambda: datetime(2026, 11, 2, 8, 0),
            )


if __name__ == "__main__":
    unittest.main()
