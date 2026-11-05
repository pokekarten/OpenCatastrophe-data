# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline ZIP/package proof for two exact official TED daily XML entries."""
from __future__ import annotations

import hashlib
import io
import unittest
import zipfile

from research_runners import ted_berlin_insurance_daily_xml_preflight_v0 as m


def notice_xml(notice):
    subject = ("Gewobag Wohnungsbau-Aktiengesellschaft Berlin Gebäudeversicherung"
               if notice == "558592-2024"
               else "WBM Wohnungsbaugesellschaft Berlin-Mitte mbH "
                    "Industrielle Sachversicherung für neun reine Gewerbeobjekte")
    return (f'<?xml version="1.0" encoding="UTF-8"?>'
            f'<ContractAwardNotice><ID>{notice}</ID><Description>{subject}'
            f'</Description></ContractAwardNotice>').encode("utf-8")


def archive_for(notice, *, filename=None, body=None, duplicates=False):
    stem = notice.replace("-", "_")
    if filename is None:
        filename = "00" + stem + ".xml"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("archive/notices/" + filename, body or notice_xml(notice))
        if duplicates:
            z.writestr("other/" + filename, body or notice_xml(notice))
    return buf.getvalue()


class FakeResponse:
    def __init__(self, blob, url, status=200):
        self.file = io.BytesIO(blob)
        self.url = url
        self.status = status
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def geturl(self):
        return self.url
    def read(self, n):
        return self.file.read(n)


class TEDDailyArchiveOriginalPreflight(unittest.TestCase):
    def test_two_pinned_daily_oj_s_packages(self):
        self.assertEqual(m.url_for("558592-2024"),
                         "https://ted.europa.eu/packages/notice/daily/202400181")
        self.assertEqual(m.url_for("668506-2026"),
                         "https://ted.europa.eu/packages/notice/daily/202600188")

    def test_valid_zip_selects_exact_one_original_notice(self):
        for number in sorted(m.DAILY_SOURCE):
            with self.subTest(notice=number):
                raw = archive_for(number)
                out = m.audit_package(number, raw)
                self.assertEqual(out["original_source_sha256"],
                                 hashlib.sha256(notice_xml(number)).hexdigest())
                self.assertEqual(out["original_zip_sha256"],
                                 hashlib.sha256(raw).hexdigest())
                self.assertEqual(out["original_xml_acquisition_mode"],
                                 "publisher_daily_oj_s_archive")
                self.assertFalse(out["original_xml_sha256_immutable_pin_verified"])
                self.assertFalse(out["actual_real_insured_location_or_tiv_admitted"])

    def test_normal_short_filename_is_accepted(self):
        number = "558592-2024"
        out = m.audit_package(number, archive_for(number, filename="558592_2024.xml"))
        self.assertEqual(out["notice"], number)

    def test_lookalike_wrong_year_or_publication_number_rejected(self):
        notice = "668506-2026"
        for name in ("00668506_2025.xml", "00668507_2026.xml", "9688506_2026.xml"):
            with self.subTest(name=name), self.assertRaisesRegex(
                    ValueError, "EXACT_NOTICE_XML_MISSING"):
                m.audit_package(notice, archive_for(notice, filename=name))

    def test_duplicate_original_entries_refused(self):
        with self.assertRaisesRegex(ValueError, "EXACT_NOTICE_XML_MISSING_OR_DUPLICATE"):
            m.audit_package("668506-2026", archive_for("668506-2026", duplicates=True))

    def test_no_fake_xml_or_broken_zip(self):
        with self.assertRaisesRegex(ValueError, "INVALID_ARCHIVE"):
            m.audit_package("558592-2024", b"PK\x03\x04" + b"x" * 600)

    def test_daily_wrong_buyer_no_source_receipt(self):
        notice = "668506-2026"
        body = notice_xml(notice).replace(b"WBM", b"FRAUD")
        with self.assertRaisesRegex(ValueError, "EXPECTED_BUYER_OR_PRODUCT_TEXT_MISSING"):
            m.audit_package(notice, archive_for(notice, body=body))

    def test_huge_uncompressed_xml_size_fails(self):
        notice = "668506-2026"
        huge = notice_xml(notice) + b" " * (m.MAX_BYTES + 200)
        with self.assertRaisesRegex(ValueError, "SUSPICIOUS_XML_ENTRY"):
            m.audit_package(notice, archive_for(notice, body=huge))

    def test_zip_traversal_not_unpacked_or_printed(self):
        notice = "668506-2026"
        raw = archive_for(notice, filename="00668506_2026.xml")
        out = m.audit_package(notice, raw)
        self.assertFalse(out["original_daily_zip_bytes_stored_in_repository"])
        self.assertNotIn("full_xml_body", out)
        self.assertNotIn("full_zip_bytes", out)

    def test_daily_source_wrong_host_redirect_refused(self):
        notice = "668506-2026"
        with self.assertRaisesRegex(ValueError, "REDIRECT_UNREVIEWED"):
            m.fetch_package(notice, opener=lambda req, timeout:
                            FakeResponse(archive_for(notice), "https://other.example/archive"))

    def test_daily_source_202_is_not_complete_xml(self):
        notice = "558592-2024"
        with self.assertRaisesRegex(ValueError, "HTTP_STATUS_202"):
            m.fetch_package(notice, opener=lambda req, timeout:
                            FakeResponse(archive_for(notice), m.url_for(notice), 202))

    def test_bounded_daily_original_zip_fetch(self):
        notice = "558592-2024"
        blob = archive_for(notice)
        actual = m.fetch_package(notice, opener=lambda req, timeout:
                                 FakeResponse(blob, m.url_for(notice)))
        self.assertEqual(actual, blob)

    def test_large_daily_package_fails_before_inflation(self):
        notice = "558592-2024"
        with self.assertRaisesRegex(ValueError, "PACKAGE_OVERSIZE"):
            m.fetch_package(notice, opener=lambda req, timeout:
                            FakeResponse(b"PK\x03\x04" + b"x" * (m.MAX_ARCHIVE_BYTES + 20),
                                         m.url_for(notice)))

    def test_not_allowlisted(self):
        with self.assertRaisesRegex(ValueError, "NOT_ALLOWLISTED"):
            m.url_for("1000-2022")
        with self.assertRaisesRegex(ValueError, "NOT_ALLOWLISTED"):
            m.audit_package("1000-2022", archive_for("558592-2024"))


if __name__ == "__main__":
    unittest.main()
