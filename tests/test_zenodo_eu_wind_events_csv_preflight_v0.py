# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline synthetic positive and negative cases for exact Zenodo wind events."""

from __future__ import annotations

import csv
import io
import tempfile
import unittest
from pathlib import Path

from scripts.zenodo_eu_wind_events_csv_preflight_v0 import (
    EXPECTED_HEADER,
    EXPECTED_UNIT,
    WindEventPreflightError,
    audit_original_file,
    parse_wind_events,
)


def csv_rows(**change: str) -> bytes:
    fields = [
        "ws", "ws1641", "2015-01-09", "2015-01-12",
        "-24.5", "35.0", "48.5", "69.5", "19.8", EXPECTED_UNIT,
    ]
    for k, value in change.items():
        fields[EXPECTED_HEADER.index(k)] = value
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(EXPECTED_HEADER)
    writer.writerow(fields)
    return out.getvalue().encode("utf-8")


class TestZenodoEuWindEventsCSV(unittest.TestCase):
    def test_good_synthetic_one_row(self) -> None:
        result = parse_wind_events(csv_rows())
        self.assertEqual(result["event_count"], 1)
        self.assertEqual(result["mean_wind_speed_unit"], EXPECTED_UNIT)
        self.assertEqual(result["first_event_start"], "2015-01-09")
        self.assertTrue(result["source_event_not_loss"])

    def test_wrong_header(self) -> None:
        data = csv_rows().replace(b"intensity unit", b"peak wind gust")
        with self.assertRaisesRegex(WindEventPreflightError, "header"):
            parse_wind_events(data)

    def test_wind_gust_mislabelling_blocked(self) -> None:
        with self.assertRaisesRegex(WindEventPreflightError, "mean wind"):
            parse_wind_events(csv_rows(**{"intensity unit": "Max gust (m/s)"}))

    def test_duplicate_event_id(self) -> None:
        data = csv_rows()
        last = data.splitlines(keepends=True)[-1]
        with self.assertRaisesRegex(WindEventPreflightError, "duplicate event"):
            parse_wind_events(data + last)

    def test_wrong_hazard_type(self) -> None:
        with self.assertRaisesRegex(WindEventPreflightError, "hazard/event"):
            parse_wind_events(csv_rows(hazardtype="fl"))

    def test_reversed_date(self) -> None:
        with self.assertRaisesRegex(WindEventPreflightError, "reversed"):
            parse_wind_events(csv_rows(start_date="2015-02-10", end_date="2015-02-09"))

    def test_invalid_date(self) -> None:
        with self.assertRaisesRegex(WindEventPreflightError, "impossible"):
            parse_wind_events(csv_rows(start_date="2015-02-31"))

    def test_bad_bbox(self) -> None:
        with self.assertRaisesRegex(WindEventPreflightError, "bounding box"):
            parse_wind_events(csv_rows(minlon="90", maxlon="60"))

    def test_nan_speed(self) -> None:
        with self.assertRaisesRegex(WindEventPreflightError, "non-finite"):
            parse_wind_events(csv_rows(intensity="nan"))

    def test_nonpositive_speed(self) -> None:
        with self.assertRaisesRegex(WindEventPreflightError, "non-positive"):
            parse_wind_events(csv_rows(intensity="-1"))

    def test_invalid_utf8(self) -> None:
        with self.assertRaisesRegex(WindEventPreflightError, "UTF-8"):
            parse_wind_events(b"\xff\xfe")

    def test_exact_original_bytes_required(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.csv"
            path.write_bytes(csv_rows())
            with self.assertRaisesRegex(WindEventPreflightError, "byte-size"):
                audit_original_file(path)


if __name__ == "__main__":
    unittest.main()
