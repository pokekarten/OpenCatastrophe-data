# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import io
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.acquire_dwd_extreme_wind_receipt import (  # noqa: E402
    AcquisitionError,
    SOURCE_URL,
    acquire,
)

HEADER = "STATIONS_ID;MESS_DATUM;QN;FX_10;FNX_10;FMX_10;DX_10;eor\r\n"
END_ROW = "3;201103312350;2;2.0;0.2;1.0;190;eor\r\n"


class FakeResponse(io.BytesIO):
    def __init__(self, payload: bytes):
        super().__init__(payload)
        self.status = 200
        self.headers = {
            "Content-Length": str(len(payload)),
            "Content-Type": "application/zip",
        }

    def geturl(self) -> str:
        return SOURCE_URL

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False


def make_zip(first_row: str) -> bytes:
    buffer = io.BytesIO()
    payload = (HEADER + first_row + END_ROW).encode()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "produkt_extrema_wind_00003_20100101_20110331_hist.txt",
            payload,
        )
    return buffer.getvalue()


def acquire_rows(first_row: str):
    payload = make_zip(first_row)
    return acquire(opener=lambda request, timeout: FakeResponse(payload))


class DwdAcquisitionReceiptHardeningTests(unittest.TestCase):
    def test_rejects_impossible_calendar_date(self):
        with self.assertRaisesRegex(AcquisitionError, "valid calendar time"):
            acquire_rows("3;201002300000;2;1.0;0.1;0.5;180;eor\r\n")

    def test_rejects_impossible_hour(self):
        with self.assertRaisesRegex(AcquisitionError, "valid calendar time"):
            acquire_rows("3;201001012400;2;1.0;0.1;0.5;180;eor\r\n")

    def test_rejects_impossible_minute(self):
        with self.assertRaisesRegex(AcquisitionError, "valid calendar time"):
            acquire_rows("3;201001010060;2;1.0;0.1;0.5;180;eor\r\n")

    def test_rejects_non_finite_measurements(self):
        for value in ("NaN", "Inf", "-Inf"):
            with self.subTest(value=value), self.assertRaisesRegex(
                AcquisitionError, "non-finite declared measurement"
            ):
                acquire_rows(
                    f"3;201001010000;2;{value};0.1;0.5;180;eor\r\n"
                )

    def test_finite_measurements_and_valid_calendar_time_still_pass(self):
        receipt = acquire_rows(
            "3;201001010000;2;-999.0;0.0;0.5;180;eor\r\n"
        )
        self.assertTrue(receipt["product_structure_validated"])
        self.assertEqual(receipt["product_row_count"], 2)


if __name__ == "__main__":
    unittest.main()
