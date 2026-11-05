# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No-network negative tests for original R+V 2025 financial PDF receipts."""
from __future__ import annotations

import io
import unittest
from pathlib import Path

from research_runners import rva_solo_original_financial_pdf_receipt_v0 as m


class FakeResponse:
    def __init__(self, raw: bytes, url: str) -> None:
        self.source = io.BytesIO(raw)
        self.url = url

    def geturl(self) -> str:
        return self.url

    def read(self, size: int) -> bytes:
        return self.source.read(size)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None


class OriginalFinancialSourceReceiptTests(unittest.TestCase):
    def test_exact_two_solo_publishers_no_false_sha_pin(self):
        self.assertEqual(len(m.URLS), 2)
        self.assertEqual([s["pages_expected"] for s in m.URLS], [86, 98])
        self.assertEqual([s["exact_original_sha256"] for s in m.URLS],
                         ["0a941b729dc6b490a5ad285ae1e1f15f4aa8ec183fb00b3d470f780a99ff996a",
                          "85a82b7a199d583e1e07efbc93317ce8bd3bab99381f54b742e997d70e2c19fa"])
        self.assertEqual([s["exact_original_bytes"] for s in m.URLS], [2069226, 1468631])
        self.assertTrue(all(s["url"].startswith("https://www.ruv.de/dam/") for s in m.URLS))

    def test_foreign_source_url_fails(self):
        with self.assertRaisesRegex(ValueError, "NOT_ALLOWLISTED"):
            m.bounded_publisher_pdf("https://unapproved.example/file.pdf")

    def test_foreign_redirect_fails(self):
        raw = b"%PDF-1.7\n" + b"x" * 52000 + b"%%EOF"
        with self.assertRaisesRegex(ValueError, "REDIRECT_NOT_PUBLISHER"):
            m.bounded_publisher_pdf(
                m.URLS[0]["url"],
                opener=lambda req, timeout: FakeResponse(raw, "https://unapproved.example/file.pdf"))

    def test_bounded_real_shape_pdf(self):
        raw = b"%PDF-1.7\n" + b"x" * 52000 + b"%%EOF"
        got = m.bounded_publisher_pdf(
            m.URLS[0]["url"],
            opener=lambda req, timeout: FakeResponse(raw, m.URLS[0]["url"]))
        self.assertEqual(got, raw)

    def test_truncated_pdf_fails(self):
        raw = b"%PDF-1.7\n" + b"x" * 52000
        with self.assertRaisesRegex(ValueError, "TRUNCATED_OR_NOT_PDF"):
            m.bounded_publisher_pdf(
                m.URLS[1]["url"],
                opener=lambda req, timeout: FakeResponse(raw, m.URLS[1]["url"]))

    def test_oversize_fails_before_return(self):
        raw = b"%PDF-1.7\n" + b"x" * (m.MAX_BYTES + 1) + b"%%EOF"
        with self.assertRaisesRegex(ValueError, "OVERSIZE"):
            m.bounded_publisher_pdf(
                m.URLS[0]["url"],
                opener=lambda req, timeout: FakeResponse(raw, m.URLS[0]["url"]))

    def test_sfcr_all_markers_required(self):
        good = ("R+V Allgemeine Versicherung AG Stichtag: 31.12.2025 "
                "Feuer- und andere Sachversicherungen 2.223.182 Gesamt 5.992.306")
        self.assertEqual(m.semantic_check(good, m.URLS[0]["required_markers"]), 4)
        with self.assertRaisesRegex(ValueError, "MARKER_MISSING"):
            m.semantic_check(good.replace("2.223.182", "2.223.183"),
                             m.URLS[0]["required_markers"])

    def test_hgb_year_end_is_not_premium(self):
        good = ("R+V Allgemeine Versicherung AG "
                "Verbundene Gebäude 997.710 895.090 "
                "Verbundene Gebäude 1.060.546 1.073.802 "
                "R+V Direktversicherung AG")
        self.assertEqual(m.semantic_check(good, m.URLS[1]["required_markers"]), 4)
        with self.assertRaisesRegex(ValueError, "MARKER_MISSING"):
            m.semantic_check(good.replace("1.060.546", "1.160.546"),
                             m.URLS[1]["required_markers"])

    def test_missing_text_fails(self):
        with self.assertRaisesRegex(ValueError, "TEXT_INVALID"):
            m.semantic_check("", m.URLS[0]["required_markers"])

    def test_pinned_sha_drift_fails_even_without_poppler(self):
        raw = b"%PDF-1.7\n" + b"x" * 60000 + b"%%EOF"
        src = dict(m.URLS[0], exact_original_sha256="0" * 64)
        with self.assertRaisesRegex(ValueError, "SHA_DRIFT"):
            m.inspect(src, raw)

    def test_explicit_nonadmission_flags_in_report_contract(self):
        names = m.inspect.__code__.co_consts
        source = Path(m.__file__).read_text(encoding="utf-8")
        for marker in ("production_financial_metric_admitted",
                       "copyright_and_bulk_reuse_rights_cleared",
                       "insurer_building_coordinates_or_tiv_observed",
                       "ORIGINAL_SOURCE_DISCOVERY_ONLY_NOT_ADMITTED"):
            self.assertIn(marker, source)
        self.assertTrue(names)


if __name__ == "__main__":
    unittest.main()
