# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import io
import unittest
import zipfile

from scripts.acquire_dwd_extreme_wind_receipt import AcquisitionError, SOURCE_URL, acquire


VALID_HEADER = "STATIONS_ID;MESS_DATUM;QN;FX_10;FNX_10;FMX_10;DX_10;eor\r\n"
VALID_ROWS = (
    "3;201001010000;2;1.0;0.1;0.5;180;eor\r\n"
    "3;201103312350;2;2.0;0.2;1.0;190;eor\r\n"
)
VALID_PRODUCT = (VALID_HEADER + VALID_ROWS).encode()


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


def make_zip(members: list[tuple[str, bytes]]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in members:
            archive.writestr(name, payload)
    return buffer.getvalue()


def acquire_zip(members: list[tuple[str, bytes]]) -> dict:
    payload = make_zip(members)
    return acquire(
        opener=lambda request, timeout: FakeResponse(payload),
        now=lambda: "2026-08-11T20:00:00Z",
    )


class DwdProductMemberDetectionTests(unittest.TestCase):
    def test_selects_product_by_header_not_filename_prefix(self):
        receipt = acquire_zip(
            [
                ("Metadaten_Geographie_00003.txt", b"Stationsname;Breite;Laenge\r\n"),
                ("produkt_zehn_min_ff_00003_20100101_20110331_hist.txt", VALID_PRODUCT),
            ]
        )
        self.assertEqual(
            receipt["product_member"],
            "produkt_zehn_min_ff_00003_20100101_20110331_hist.txt",
        )
        self.assertTrue(receipt["product_structure_validated"])

    def test_old_prefix_does_not_override_header_contract(self):
        receipt = acquire_zip(
            [
                ("produkt_extrema_wind_decoy.txt", b"not;a;product\r\n"),
                ("unexpected-but-safe-name.txt", VALID_PRODUCT),
            ]
        )
        self.assertEqual(receipt["product_member"], "unexpected-but-safe-name.txt")

    def test_rejects_when_no_text_member_matches_product_header(self):
        with self.assertRaisesRegex(AcquisitionError, "exactly one.*product header"):
            acquire_zip(
                [
                    ("readme.txt", b"description only\r\n"),
                    ("metadata.txt", b"STATIONS_ID;NAME\r\n"),
                ]
            )

    def test_rejects_ambiguous_multiple_matching_headers(self):
        with self.assertRaisesRegex(AcquisitionError, "exactly one.*product header"):
            acquire_zip(
                [
                    ("candidate-a.txt", VALID_PRODUCT),
                    ("candidate-b.txt", VALID_PRODUCT),
                ]
            )

    def test_non_product_text_with_overlong_or_non_utf8_header_is_ignored(self):
        receipt = acquire_zip(
            [
                ("long-metadata.txt", (b"x" * 5000) + b"\n"),
                ("binary-metadata.txt", b"\xff\xfe\xfd\n"),
                ("actual-product.txt", VALID_PRODUCT),
            ]
        )
        self.assertEqual(receipt["product_member"], "actual-product.txt")


if __name__ == "__main__":
    unittest.main()
