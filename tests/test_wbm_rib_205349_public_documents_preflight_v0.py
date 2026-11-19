# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline-only public RIB landing-page availability and no policy admission."""
from __future__ import annotations

import io
import unittest

from research_runners import wbm_rib_205349_public_documents_preflight_v0 as m


def html(body: str) -> bytes:
    return ('<!doctype html><html><head><title>RIB Tender</title></head>'
            '<body><main>' + body + '</main></body></html>').encode('utf-8')


class Response:
    def __init__(self, body: bytes, *, url=m.OFFICIAL_URL, status=200,
                 content_type="text/html; charset=utf-8"):
        self.stream = io.BytesIO(body)
        self.url = url
        self.status = status
        self.headers = {"Content-Type": content_type}
    def geturl(self):
        return self.url
    def read(self, count):
        return self.stream.read(count)
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False


class WBMRIBPublicDocumentsPreflightTests(unittest.TestCase):
    def test_explicit_english_not_found_is_blocked_not_paperwork(self):
        x = m.inspect(html(
            "Announcement not found. The desired announcement is no longer "
            "publicly available. Download Tender Documents Demo Project"))
        self.assertEqual(x["classification"], "PUBLIC_ANNOUNCEMENT_EXPIRED_OR_NOT_FOUND_RENDERED")
        self.assertTrue(x["explicit_not_available_message_observed_in_html"])
        self.assertFalse(x["public_attachments_enumerated_or_downloaded"])
        self.assertFalse(x["nine_real_insured_locations_or_tiv_observed"])

    def test_german_not_found_translation(self):
        x = m.inspect(html("Bekanntmachung ist nicht mehr öffentlich verfügbar"))
        self.assertTrue(x["explicit_not_available_message_observed_in_html"])

    def test_client_page_only_remains_unresolved(self):
        x = m.inspect(html("Loading public tender interface"))
        self.assertEqual(x["classification"], "PUBLIC_CLIENT_PAGE_OR_DYNAMIC_CONTENT_UNRESOLVED")

    def test_specific_tender_details_not_the_same_as_download(self):
        x = m.inspect(html(
            "VV 2026-0069 Industrielle Sachversicherung für reine Gewerbeobjekte "
            "Tender Documents [Download]"))
        self.assertEqual(x["classification"],
                         "PUBLIC_TENDER_METADATA_VISIBLE_BUT_ATTACHMENTS_UNVERIFIED")
        self.assertFalse(x["public_attachments_enumerated_or_downloaded"])
        self.assertFalse(x["full_insurance_terms_or_signed_contract_observed"])

    def test_generic_demo_not_specific_tender(self):
        x = m.inspect(html(
            "Sample project 08-15 Demo Tender Documents Download "
            "apply for insurance tender"))
        self.assertFalse(x["target_tender_number_and_insurance_subject_visible"])
        self.assertFalse(x["public_attachments_enumerated_or_downloaded"])

    def test_http_404_does_not_mean_original_contract_never_existed(self):
        x = m.inspect(b"", status=404)
        self.assertEqual(x["classification"], "PUBLIC_LANDING_PAGE_HTTP_NOT_FOUND")
        self.assertFalse(x["full_insurance_terms_or_signed_contract_observed"])

    def test_http_410_earlier_announcements_no_longer_public(self):
        self.assertEqual(m.inspect(b"",status=410)["classification"],
                         "PUBLIC_LANDING_PAGE_HTTP_NOT_FOUND")

    def test_nonofficial_redirect_does_not_authenticate_source(self):
        with self.assertRaisesRegex(ValueError, "UNEXPECTED_HOST"):
            m.inspect(html("Announcement not found"),
                      response_url="https://mirror.example/file/205349")

    def test_other_tender_id_must_be_rejected(self):
        with self.assertRaisesRegex(ValueError, "UNEXPECTED_HOST"):
            m.inspect(html("Announcement not found"),
                      response_url=m.OFFICIAL_URL.replace("205349", "205350"))

    def test_same_host_http_downgrade_rejected(self):
        with self.assertRaisesRegex(ValueError, "UNEXPECTED_HOST"):
            m.inspect(html("Announcement not found"),
                      response_url=m.OFFICIAL_URL.replace("https:", "http:"))

    def test_no_provider_url_query_credentials_or_filename(self):
        for url in (m.OFFICIAL_URL + "?session=abc",
                    "https://user:pass@www.meinauftrag.rib.de"
                    + m.EXACT_PATH):
            with self.subTest(url=url), self.assertRaisesRegex(ValueError, "UNEXPECTED_HOST"):
                m.inspect(html("Announcement not found"), response_url=url)

    def test_html_scripts_not_used_as_authentic_published_text(self):
        raw = html(
            '<script>const text="VV 2026-0069 Industrielle Sachversicherung";</script>'
            "Sample announcement")
        x = m.inspect(raw)
        self.assertEqual(x["classification"], "PUBLIC_CLIENT_PAGE_OR_DYNAMIC_CONTENT_UNRESOLVED")

    def test_non_html_content_not_silent_document_import(self):
        with self.assertRaisesRegex(ValueError, "UNEXPECTED_DOCUMENT"):
            m.inspect(html("VV 2026-0069 Industrielle Sachversicherung"),
                      content_type="application/pdf")

    def test_oversize_refused(self):
        with self.assertRaisesRegex(ValueError, "OVERSIZE"):
            m.inspect(b"x"*(m.MAX_BYTES + 1))

    def test_non200_status_403_is_blocked_not_empty_inventory(self):
        with self.assertRaisesRegex(ValueError, "NONPUBLIC_HTTP_STATUS_403"):
            m.inspect(b"blocked",status=403)

    def test_only_official_public_url_fetched_no_login(self):
        found = []
        def opener(req, timeout):
            found.append((req.full_url,req.get_method(),timeout))
            return Response(html("Announcement not found"))
        x = m.fetch(opener=opener)
        self.assertEqual(found, [(m.OFFICIAL_URL,"GET",25)])
        self.assertTrue(x["no_credentials_cookies_or_logins_used"])

    def test_strict_source_receipt_does_not_prove_coinsurance(self):
        x = m.inspect(html("VV 2026-0069 Industrielle Sachversicherung"))
        for k in (
            "full_insurance_terms_or_signed_contract_observed",
            "nine_real_insured_locations_or_tiv_observed",
            "actual_HDI_Helvetia_RV_company_policy_shares_observed",
            "actual_RV_CAT_exposure_admitted",
            "raw_provider_html_committed_or_logged",
        ):
            with self.subTest(k=k):
                self.assertFalse(x[k])


if __name__ == "__main__":
    unittest.main()
