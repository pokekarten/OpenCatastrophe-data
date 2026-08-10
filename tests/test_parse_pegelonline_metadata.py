# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.parse_pegelonline_metadata import (
    PEGELONLINE_Q_LONGNAME,
    PEGELONLINE_Q_UNIT,
    PEGELONLINE_STATION_SHORTNAME,
    PEGELONLINE_WATER_SHORTNAME,
    PegelonlineMetadataError,
    canonical_metadata_bytes,
    load_provider_json_bytes,
    parse_pegelonline_metadata_bytes,
    parse_pegelonline_station_metadata,
    pegelonline_metadata_request_url,
)

ROOT = Path(__file__).resolve().parents[1]


class PegelonlineMetadataTests(unittest.TestCase):
    def _station(self) -> dict[str, object]:
        # Provider-shaped fixture using the pre-target metadata resolved from the
        # official PEGELONLINE REST-v2 station response on 2026-08-10. This is a
        # regression fixture, not a substitute for preserving the exact response
        # bytes and SHA-256 in acquisition evidence.
        return {
            "uuid": "70272185-b2b3-4178-96b8-43bea330dcae",
            "number": "501060",
            "shortname": "DRESDEN",
            "longname": "DRESDEN",
            "km": 55.63,
            "agency": "WSA ELBE, STANDORT DRESDEN",
            "longitude": 13.738832,
            "latitude": 51.054460,
            "water": {"shortname": "ELBE", "longname": "ELBE", "provider_extension": True},
            "timeseries": [
                {
                    "shortname": "W",
                    "longname": "WASSERSTAND_ROHDATEN",
                    "unit": "cm",
                    "equidistance": 15,
                },
                {
                    "shortname": "Q",
                    "longname": "ABFLUSS_ROHDATEN",
                    "unit": "m³/s",
                    "equidistance": 15,
                    "provider_extension": {"may_be_added": "without breaking REST v2"},
                },
            ],
            "provider_extension": "accepted",
        }

    def test_exact_pre_target_dresden_metadata_is_resolved(self) -> None:
        metadata = parse_pegelonline_station_metadata(self._station())
        self.assertEqual(metadata["station_number"], "501060")
        self.assertEqual(metadata["station_uuid"], "70272185-b2b3-4178-96b8-43bea330dcae")
        self.assertEqual(metadata["station_shortname"], PEGELONLINE_STATION_SHORTNAME)
        self.assertEqual(metadata["water_shortname"], PEGELONLINE_WATER_SHORTNAME)
        self.assertEqual(metadata["latitude_wgs84"], 51.054460)
        self.assertEqual(metadata["longitude_wgs84"], 13.738832)
        self.assertEqual(metadata["q_longname"], PEGELONLINE_Q_LONGNAME)
        self.assertEqual(metadata["q_unit"], PEGELONLINE_Q_UNIT)
        self.assertEqual(metadata["q_equidistance_minutes"], 15)
        self.assertEqual(metadata["q_sampling_interval_seconds"], 900)
        self.assertEqual(metadata["expected_observations_per_24h"], 96)
        self.assertEqual(metadata["request_url"], pegelonline_metadata_request_url())
        self.assertNotIn("currentMeasurement", canonical_metadata_bytes(metadata).decode("utf-8"))

    def test_station_array_selects_exact_uuid_and_is_order_independent(self) -> None:
        other = {
            "uuid": "11111111-1111-1111-1111-111111111111",
            "number": "other",
            "shortname": "OTHER",
        }
        station = self._station()
        forward = parse_pegelonline_station_metadata([other, station])
        reverse = parse_pegelonline_station_metadata([station, other])
        self.assertEqual(forward, reverse)

    def test_provider_additive_fields_are_ignored(self) -> None:
        station = self._station()
        station["new_backward_compatible_attribute"] = [1, 2, 3]
        station["water"]["another_attribute"] = "future"
        station["timeseries"][1]["future_metadata"] = 42
        parsed = parse_pegelonline_station_metadata(station)
        self.assertEqual(parsed["q_equidistance_minutes"], 15)

    def test_current_measurement_is_rejected_before_any_value_is_used(self) -> None:
        station = self._station()
        station["timeseries"][1]["currentMeasurement"] = {
            "timestamp": "2026-08-10T15:00:00+02:00",
            "value": 123.4,
        }
        with self.assertRaisesRegex(PegelonlineMetadataError, "must not include currentMeasurement"):
            parse_pegelonline_station_metadata(station)

    def test_station_identity_and_water_semantics_fail_closed(self) -> None:
        mutations = (
            ("uuid", "different", "station.uuid"),
            ("number", "999999", "station.number"),
            ("shortname", "NOT-DRESDEN", "station.shortname"),
        )
        for field, value, message in mutations:
            station = self._station()
            station[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(PegelonlineMetadataError, message):
                parse_pegelonline_station_metadata(station)

        station = self._station()
        station["water"]["shortname"] = "RHEIN"
        with self.assertRaisesRegex(PegelonlineMetadataError, "station.water.shortname"):
            parse_pegelonline_station_metadata(station)

    def test_station_array_requires_exactly_one_frozen_uuid(self) -> None:
        station = self._station()
        with self.assertRaisesRegex(PegelonlineMetadataError, "exactly one"):
            parse_pegelonline_station_metadata([])
        with self.assertRaisesRegex(PegelonlineMetadataError, "exactly one"):
            parse_pegelonline_station_metadata([station, copy.deepcopy(station)])

    def test_q_series_must_be_unique_raw_discharge_with_exact_unit(self) -> None:
        station = self._station()
        station["timeseries"] = [value for value in station["timeseries"] if value["shortname"] != "Q"]
        with self.assertRaisesRegex(PegelonlineMetadataError, "exactly one Q"):
            parse_pegelonline_station_metadata(station)

        station = self._station()
        station["timeseries"].append(copy.deepcopy(station["timeseries"][1]))
        with self.assertRaisesRegex(PegelonlineMetadataError, "exactly one Q"):
            parse_pegelonline_station_metadata(station)

        station = self._station()
        station["timeseries"][1]["longname"] = "ABFLUSS"
        with self.assertRaisesRegex(PegelonlineMetadataError, "Q.longname"):
            parse_pegelonline_station_metadata(station)

        station = self._station()
        station["timeseries"][1]["unit"] = "l/s"
        with self.assertRaisesRegex(PegelonlineMetadataError, "Q.unit"):
            parse_pegelonline_station_metadata(station)

    def test_equidistance_is_type_strict_and_must_define_exact_24h_grid(self) -> None:
        for value in (True, 0, -15):
            station = self._station()
            station["timeseries"][1]["equidistance"] = value
            with self.subTest(value=value), self.assertRaisesRegex(PegelonlineMetadataError, "positive integer"):
                parse_pegelonline_station_metadata(station)

        station = self._station()
        station["timeseries"][1]["equidistance"] = 17
        with self.assertRaisesRegex(PegelonlineMetadataError, "exact 24-hour sampling grid"):
            parse_pegelonline_station_metadata(station)

    def test_coordinates_reject_type_confusion_nonfinite_and_noncanonical_ranges(self) -> None:
        cases = (
            ("latitude", True),
            ("latitude", math.nan),
            ("latitude", 91.0),
            ("longitude", math.inf),
            ("longitude", 180.0),
            ("longitude", -181.0),
        )
        for field, value in cases:
            station = self._station()
            station[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(PegelonlineMetadataError):
                parse_pegelonline_station_metadata(station)

    def test_strict_json_loader_rejects_duplicate_keys_nan_and_invalid_utf8(self) -> None:
        duplicate = (
            b'{"uuid":"70272185-b2b3-4178-96b8-43bea330dcae",'
            b'"number":"501060","number":"501060"}'
        )
        with self.assertRaisesRegex(PegelonlineMetadataError, "duplicate JSON key"):
            load_provider_json_bytes(duplicate)
        with self.assertRaisesRegex(PegelonlineMetadataError, "non-finite JSON"):
            load_provider_json_bytes(b'{"bad":NaN}')
        with self.assertRaisesRegex(PegelonlineMetadataError, "valid UTF-8"):
            load_provider_json_bytes(b"\xff")

    def test_bytes_parser_matches_object_parser(self) -> None:
        station = self._station()
        raw = json.dumps(station, ensure_ascii=False).encode("utf-8")
        self.assertEqual(
            parse_pegelonline_metadata_bytes(raw),
            parse_pegelonline_station_metadata(station),
        )

    def test_cli_outputs_only_canonical_parsed_metadata(self) -> None:
        station = self._station()
        station["sensitive_uninterpreted_provider_field"] = "must-not-be-republished"
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "station.json"
            path.write_text(json.dumps(station, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "parse_pegelonline_metadata.py"), str(path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["station_number"], "501060")
        self.assertEqual(output["q_equidistance_minutes"], 15)
        self.assertNotIn("sensitive_uninterpreted_provider_field", result.stdout)
        self.assertEqual(
            result.stdout.encode("utf-8"),
            canonical_metadata_bytes(output) + b"\n",
        )

    def test_cli_fails_closed_on_measurement_bearing_response(self) -> None:
        station = self._station()
        station["timeseries"][1]["currentMeasurement"] = {"value": 123.4}
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "station.json"
            path.write_text(json.dumps(station, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "parse_pegelonline_metadata.py"), str(path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("currentMeasurement", result.stderr)


if __name__ == "__main__":
    unittest.main()
