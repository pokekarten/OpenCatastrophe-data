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

    def test_partial_day_coverage_is_not_silently_full_or_zero(self):
        summary = inspect_json_bytes(encode(payload()))
        self.assertEqual(summary["expected_six_minute_slots"], 240)
        self.assertEqual(summary["missing_six_minute_slots"], 238)
        self.assertEqual(summary["missing_before_first_observation"], 0)
        self.assertEqual(summary["missing_between_observations"], 0)
        self.assertEqual(summary["missing_after_last_observation"], 238)
        self.assertFalse(summary["full_utc_day_covered"])
        self.assertFalse(summary["missing_measurements_inferred_as_zero"])

    def test_full_day_and_interior_missing_slots_have_separate_counts(self):
        value = payload()
        template = value["data"][0].copy()
        value["data"] = [
            {**template, "t": f"2026-01-01 {slot // 10:02d}:{(slot % 10) * 6:02d}"}
            for slot in range(240)
        ]
        full = inspect_json_bytes(encode(value))
        self.assertEqual(full["observation_rows"], 240)
        self.assertEqual(full["missing_six_minute_slots"], 0)
        self.assertTrue(full["full_utc_day_covered"])
        self.assertFalse(full["quality_scientifically_assessed"])

        # A sparse day is still structurally valid, but its gaps must be explicit.
        value["data"].pop(120)
        missing = inspect_json_bytes(encode(value))
        self.assertEqual(missing["missing_six_minute_slots"], 1)
        self.assertEqual(missing["missing_between_observations"], 1)
        self.assertFalse(missing["full_utc_day_covered"])

        value["data"].pop(0)
        value["data"].pop()
        edges = inspect_json_bytes(encode(value))
        self.assertEqual(edges["missing_six_minute_slots"], 3)
        self.assertEqual(edges["missing_before_first_observation"], 1)
        self.assertEqual(edges["missing_between_observations"], 1)
        self.assertEqual(edges["missing_after_last_observation"], 1)
        self.assertFalse(edges["missing_measurements_inferred_as_zero"])

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

    def test_sigma_means_one_second_standard_deviation_not_cat_uncertainty(self):
        summary = inspect_json_bytes(encode(payload()))
        self.assertTrue(summary["sigma_is_one_second_sample_standard_deviation"])
        self.assertFalse(summary["sigma_is_calibrated_cat_uncertainty"])
        self.assertTrue(summary["provider_quality_codes_structurally_validated"])
        self.assertFalse(summary["quality_scientifically_assessed"])
        self.assertEqual(summary["reported_verified_observation_rows"], 2)
        self.assertEqual(summary["reported_preliminary_observation_rows"], 0)
        self.assertEqual(summary["observations_with_nonzero_provider_flags"], 0)
        # The metadata-only receipt must not leak raw sigma or water-level values.
        self.assertNotIn("0.033", json.dumps(summary))
        self.assertNotIn("-0.098", json.dumps(summary))

    def test_preliminary_outlier_count_is_not_a_verified_inference_flag(self):
        value = payload()
        value["data"][0]["q"] = "p"
        value["data"][0]["f"] = "4,0,0,0"  # Preliminary O=count, not boolean.
        value["data"][1]["f"] = "1,0,0,0"  # Verified I=inferred flag.
        summary = inspect_json_bytes(encode(value))
        self.assertEqual(summary["reported_preliminary_observation_rows"], 1)
        self.assertEqual(summary["reported_verified_observation_rows"], 1)
        self.assertEqual(summary["observations_with_nonzero_provider_flags"], 2)
        self.assertFalse(summary["quality_scientifically_assessed"])
        self.assertFalse(summary["sigma_is_calibrated_cat_uncertainty"])

    def test_rejects_bad_one_second_sigma_without_borrowing_uncertainty_rights(self):
        for sigma in (None, -0.03, "-0.01", "NaN", "Infinity",
                      "not-a-number", "1e309", True):
            value = payload()
            if sigma is None:
                del value["data"][0]["s"]
            else:
                value["data"][0]["s"] = sigma
            with self.subTest(sigma=sigma), self.assertRaises(COOPSProbeError):
                inspect_json_bytes(encode(value))

    def test_rejects_invalid_quality_codes_or_flag_shapes(self):
        for quality, flags in (
            ("unknown", "0,0,0,0"),
            ("V", "0,0,0,0"),
            ("v", "2,0,0,0"),  # Verified inferred flag is binary.
            ("v", "0,0,0"),  # Missing quality flag.
            ("v", "0,0,0,0,0"),
            ("v", "0,2,0,0"),
            ("v", "0,0,0,-1"),
            ("v", "0,0,0,x"),
            ("p", "361,0,0,0"),  # At most 360 1-second samples per 6 min.
            ("p", "-1,0,0,0"),
            ("p", "x,0,0,0"),
            ("p", "０,0,0,0"),
        ):
            value = payload()
            value["data"][0]["q"] = quality
            value["data"][0]["f"] = flags
            with self.subTest(quality=quality, flags=flags), self.assertRaises(COOPSProbeError):
                inspect_json_bytes(encode(value))

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
