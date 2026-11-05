# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only source authenticity/semantic gates for official TED XML."""
from __future__ import annotations

import hashlib
import io
import unittest
from unittest.mock import patch

from research_runners import ted_berlin_insurance_original_xml_preflight_v0 as m


def make_notice(notice: str, *, buyer: str = "", title: str = "",
                description: str = "", root: str = "ContractNotice") -> bytes:
    b = buyer or ("Gewobag Wohnungsbau-Aktiengesellschaft Berlin" if notice == "558592-2024"
                  else "WBM Wohnungsbaugesellschaft Berlin-Mitte mbH")
    name = title or ("Gebäudeversicherung" if notice == "558592-2024"
                     else "Industrielle Sachversicherung für reine Gewerbeobjekte")
    desc = description or ("Bauobjekt Hauptvertrag und Nebenvertrag" if notice == "558592-2024"
                           else "Industrielle Sachversicherung für neun reine Gewerbeobjekte")
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<{root} xmlns="urn:oasis:names:specification:ubl:schema:xsd:ContractNotice-2">'
            f'<ID>{notice}</ID><ContractingParty><Name>{b}</Name></ContractingParty>'
            f'<ProcurementTitle>{name}</ProcurementTitle><Description>{desc}</Description>'
            f'</{root}>').encode("utf-8")


class FakeResponse:
    def __init__(self, body: bytes, url: str, status: int = 200):
        self.data = io.BytesIO(body)
        self.url = url
        self.status = status
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return None
    def geturl(self):
        return self.url
    def read(self, n):
        return self.data.read(n)


class TEDSyntheticOriginalXMLSourceTests(unittest.TestCase):
    def setUp(self):
        # Real source code uses immutable publisher original pins. Synthetic
        # fixtures intentionally have different bytes and must not weaken
        # the production exact-hash path or claim to be original TED assets.
        original = {
            key: dict(value, original_xml_sha256_pinned=None,
                      original_xml_bytes_pinned=None)
            for key, value in m.SOURCES.items()
        }
        self.original_pins = {
            key: (value["original_xml_sha256_pinned"], value["original_xml_bytes_pinned"])
            for key, value in m.SOURCES.items()
        }
        patcher = patch.dict(m.SOURCES, original)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_two_real_pinned_original_sha_and_byte_receipts_exist(self):
        self.assertEqual(self.original_pins["558592-2024"],
                         ("51698e01c01caa9a0c58d41baf161d73a585d3b30f3b3dba12d95a3859b56b2f", 39733))
        self.assertEqual(self.original_pins["668506-2026"],
                         ("7650720183d0c26430e0433858bf2e8b854ea68bb93fbf679e96ee696ee8fc78", 21837))

    def test_exact_two_official_notice_identifiers(self):
        self.assertEqual(set(m.SOURCES), {"558592-2024", "668506-2026"})
        self.assertEqual(m.official_url("558592-2024"),
                         "https://ted.europa.eu/en/notice/558592-2024/xml")
        self.assertEqual(m.official_url("668506-2026"),
                         "https://ted.europa.eu/en/notice/668506-2026/xml")

    def test_fake_original_xml_semantics_are_bounded(self):
        for number in sorted(m.SOURCES):
            with self.subTest(number=number):
                body = make_notice(number)
                output = m.inspect(number, body)
                self.assertEqual(output["original_source_bytes"], len(body))
                self.assertEqual(output["original_source_sha256"],
                                 hashlib.sha256(body).hexdigest())
                self.assertTrue(output["buyer_and_notice_subject_markers_present"])
                self.assertFalse(output["original_sha256_immutable_pin_verified"])
                self.assertFalse(output["actual_real_insured_location_or_tiv_admitted"])
                self.assertTrue(output["publication_number_literal_present_in_xml"])

    def test_wbm_award_root_and_scope(self):
        receipt = m.inspect("668506-2026", make_notice(
            "668506-2026", root="ContractAwardNotice"))
        self.assertEqual(receipt["xml_document_root"], "ContractAwardNotice")
        self.assertEqual(receipt["source_document_semantic_marker_count"], 3)
        self.assertFalse(receipt["awarded_insurer_shares_or_per_property_allocation_verified"])

    def test_source_has_no_leaked_issuer_raw_bytes_or_tiv(self):
        result = m.inspect("558592-2024", make_notice("558592-2024"))
        self.assertFalse(result["source_original_bytes_committed_or_printed"])
        self.assertNotIn("body", result)
        self.assertNotIn("xml", result)
        self.assertFalse(result["current_2026_gewobag_carrier_contract_verified"])

    def test_unknown_notice_rejected_before_request(self):
        with self.assertRaisesRegex(ValueError, "NOT_ALLOWLISTED"):
            m.official_url("invalid")
        with self.assertRaisesRegex(ValueError, "NOT_ALLOWLISTED"):
            m.inspect("742-2026", make_notice("558592-2024"))
        with self.assertRaisesRegex(ValueError, "NOT_ALLOWLISTED"):
            m.fetch("wrong")

    def test_official_bounded_fetch(self):
        notice = "668506-2026"
        body = make_notice(notice)
        result = m.fetch(notice, opener=lambda req, timeout: FakeResponse(
            body, m.official_url(notice)))
        self.assertEqual(result, body)
        self.assertEqual(m.inspect(notice, result)["original_source_sha256"],
                         hashlib.sha256(body).hexdigest())

    def test_external_redirect_forbidden(self):
        notice = "668506-2026"
        with self.assertRaisesRegex(ValueError, "REDIRECT_CHANGED"):
            m.fetch(notice, opener=lambda req, timeout: FakeResponse(
                make_notice(notice), "https://evil.example/xml"))

    def test_official_host_wrong_notice_redirect_forbidden(self):
        notice = "668506-2026"
        with self.assertRaisesRegex(ValueError, "REDIRECT_CHANGED"):
            m.fetch(notice, opener=lambda req, timeout: FakeResponse(
                make_notice(notice), m.official_url("558592-2024")))

    def test_wrong_status_fails_even_if_xml_parses(self):
        notice = "668506-2026"
        with self.assertRaisesRegex(ValueError, "NON_200"):
            m.fetch(notice, opener=lambda req, timeout: FakeResponse(
                make_notice(notice), m.official_url(notice), 206))

    def test_bounded_fetch_refuses_large_body(self):
        notice = "668506-2026"
        with self.assertRaisesRegex(ValueError, "EXCEEDS_MAX_BYTES"):
            m.fetch(notice, opener=lambda req, timeout: FakeResponse(
                b"<ContractNotice>" + b" " * (m.MAX_BYTES + 1) + b"</ContractNotice>",
                m.official_url(notice)))

    def test_xml_truncation_or_wrong_type_blocked(self):
        with self.assertRaisesRegex(ValueError, "INVALID_SOURCE_SIZE"):
            m.inspect("558592-2024", b"<a/>")
        with self.assertRaisesRegex(ValueError, "NOT_XML"):
            m.inspect("558592-2024", b"<html>" + b"x" * 500)

    def test_doctype_and_entity_refused(self):
        for injected in (
            b'<!DOCTYPE foo [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>',
            b'<!ENTITY unsafe "anything">',
        ):
            test = b'<?xml version="1.0"?>' + injected + make_notice(
                "558592-2024").replace(b'<?xml version="1.0" encoding="UTF-8"?>', b'')
            with self.subTest(dtd=injected[:15]), self.assertRaisesRegex(
                    ValueError, "DOCTYPE_OR_ENTITY"):
                m.inspect("558592-2024", test)

    def test_non_notice_xml_root_fails(self):
        data = make_notice("558592-2024", root="Portfolio")
        with self.assertRaisesRegex(ValueError, "UNEXPECTED_XML_NOTICE_ROOT"):
            m.inspect("558592-2024", data)

    def test_wrong_buyer_or_title_fails(self):
        for buyer, title in (
            ("A random other company", "Gebäudeversicherung"),
            ("Gewobag Wohnungsbau-Aktiengesellschaft Berlin", "Unrelated car policy"),
        ):
            wrong = make_notice("558592-2024", buyer=buyer, title=title)
            with self.subTest(buyer=buyer), self.assertRaisesRegex(
                    ValueError, "EXPECTED_BUYER_OR_PRODUCT_TEXT_MISSING"):
                m.inspect("558592-2024", wrong)

    def test_wbm_no_nine_object_description_fails(self):
        wrong = make_notice("668506-2026",
                            description="An unspecified number of vehicles")
        with self.assertRaisesRegex(ValueError, "EXPECTED_BUYER_OR_PRODUCT_TEXT_MISSING"):
            m.inspect("668506-2026", wrong)

    def test_pinned_sha_mismatch_never_silent(self):
        notice = "668506-2026"
        original = dict(m.SOURCES[notice])
        original["original_xml_sha256_pinned"] = "0" * 64
        with patch.dict(m.SOURCES, {notice: original}):
            with self.assertRaisesRegex(ValueError, "PINNED_ORIGINAL_SHA256_MISMATCH"):
                m.inspect(notice, make_notice(notice))

    def test_pinned_byte_count_mismatch_never_silent(self):
        notice = "558592-2024"
        original = dict(m.SOURCES[notice])
        original["original_xml_bytes_pinned"] = 1
        with patch.dict(m.SOURCES, {notice: original}):
            with self.assertRaisesRegex(ValueError, "PINNED_ORIGINAL_BYTE_COUNT_MISMATCH"):
                m.inspect(notice, make_notice(notice))

    def test_missing_notice_number_in_xml_is_not_invented(self):
        data = make_notice("558592-2024").replace(b"558592-2024", b"XXX_XX_2024")
        result = m.inspect("558592-2024", data)
        self.assertFalse(result["publication_number_literal_present_in_xml"])
        self.assertFalse(result["original_sha256_immutable_pin_verified"])


if __name__ == "__main__":
    unittest.main()
