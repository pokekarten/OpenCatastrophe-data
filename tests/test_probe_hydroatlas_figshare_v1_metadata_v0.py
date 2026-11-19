# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic Figshare metadata only; no original HydroATLAS file bytes in Git."""
from __future__ import annotations

from datetime import datetime, timezone
import copy
import hashlib
import json
import unittest
from unittest.mock import patch

from scripts.probe_hydroatlas_figshare_v1_metadata_v0 import (
    ACCESS_ID, ARTICLE_ID, CONTRACT_PATH, EXPECTED_SIZE, HydroATLASBlocked,
    MAX_BYTES, NoRedirect, REVIEWED_FILES, TIMEOUT, URL,
    inspect_metadata, main, probe, verify_reviewed_contract,
)


def fixture():
    return {
        "id": ARTICLE_ID,
        "title": "HydroATLAS version 1.0",
        "version": 1,
        "doi": "10.6084/m9.figshare.9890531.v1",
        "is_public": True,
        "status": "public",
        "size": EXPECTED_SIZE,
        "license": {"name": "CC BY 4.0",
                    "url": "https://creativecommons.org/licenses/by/4.0/"},
        "files": [
            {"id": fid, "name": name, "size": size,
             "supplied_md5": md5, "computed_md5": md5,
             "is_link_only": False,
             "download_url": f"https://ndownloader.figshare.com/files/{fid}"}
            for fid, (name, size, md5) in sorted(REVIEWED_FILES.items())
        ],
    }


def blob(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")


class FakeResponse:
    def __init__(self, data=None, status=200, url=URL, media="application/json", extra=None):
        self.raw = blob(fixture()) if data is None else data
        self.status, self.url = status, url
        self.headers = {
            "Content-Type": media, "Content-Encoding": "identity",
            "Content-Length": str(len(self.raw)),
        }
        self.headers.update(extra or {})

    def geturl(self):
        return self.url

    def read(self, n):
        return self.raw[:n]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class HydroATLASMetadataTests(unittest.TestCase):
    def test_contract_and_original_file_metadata_are_exactly_frozen(self):
        verify_reviewed_contract()
        self.assertEqual(ACCESS_ID, "hydrosheds.hydroatlas.v1")
        self.assertEqual(URL, "https://api.figshare.com/v2/articles/9890531")
        self.assertEqual(len(REVIEWED_FILES), 7)
        self.assertEqual(sum(x[1] for x in REVIEWED_FILES.values()), EXPECTED_SIZE)
        self.assertEqual(EXPECTED_SIZE, 12027317200)
        self.assertEqual(REVIEWED_FILES[20082137][0], "BasinATLAS_Data_v10.gdb.zip")
        self.assertEqual(REVIEWED_FILES[20082137][2], "69af94baee68da5a3f80f09e7b85bd04")
        self.assertEqual(TIMEOUT, 30)
        self.assertEqual(MAX_BYTES, 131072)

    def test_valid_synthetic_original_article_metadata(self):
        r = inspect_metadata(blob(fixture()))
        self.assertEqual(r["article_id_verified"], ARTICLE_ID)
        self.assertEqual(r["original_provider_file_metadata_verified"], 7)
        self.assertEqual(r["provider_declared_gis_zip_count"], 4)
        self.assertEqual(r["provider_declared_technical_pdf_count"], 3)
        self.assertFalse(r["original_asset_sha256_independently_verified"])
        self.assertFalse(r["per_attribute_ccby_odbl_licenses_scoped"])
        self.assertEqual(r["gis_archive_files_downloaded"], 0)

    def test_source_publication_identity_rights_or_file_change_fail(self):
        field_changes = (
            ("id", 1),
            ("title", "Other Atlas"),
            ("version", 2),
            ("doi", "10.6084/m9.figshare.other"),
            ("is_public", False),
            ("status", "draft"),
            ("size", 1),
            ("license", {"name": "closed", "url": "https://example.invalid"}),
        )
        for key, value in field_changes:
            with self.subTest(key=key):
                x = fixture()
                x[key] = value
                with self.assertRaises(HydroATLASBlocked):
                    inspect_metadata(blob(x))
        for key, value in (
            ("name", "other.csv"),
            ("id", 99),
            ("size", 4),
            ("supplied_md5", "0" * 32),
            ("computed_md5", "0" * 32),
            ("is_link_only", True),
            ("download_url", "https://unapproved.invalid/file.zip"),
        ):
            with self.subTest(file_key=key):
                x = fixture()
                x["files"][0][key] = value
                with self.assertRaises(HydroATLASBlocked):
                    inspect_metadata(blob(x))
        x = fixture()
        x["files"].pop()
        with self.assertRaises(HydroATLASBlocked):
            inspect_metadata(blob(x))

    def test_duplicate_nonfinite_broken_and_oversized_json_rejected(self):
        for data in (
            b"", b"{}", b"[]", b'{"id":9890531,"id":1}',
            b'{"x":NaN}', b'{"x":Infinity}',
            b"\xff", b"{bad}", b"x" * (MAX_BYTES + 1),
        ):
            with self.subTest(data=data[:30]), self.assertRaises(HydroATLASBlocked):
                inspect_metadata(data)

    def test_exact_one_original_metadata_get_and_sha_without_provider_files(self):
        seen = []

        def open_once(req, timeout):
            seen.append((req.full_url, req.get_method(), timeout))
            return FakeResponse()

        r = probe(open_request=open_once,
                  clock=lambda: datetime(2026, 11, 12, tzinfo=timezone.utc))
        self.assertEqual(seen, [(URL, "GET", TIMEOUT)])
        self.assertEqual(r["response_sha256"], hashlib.sha256(blob(fixture())).hexdigest())
        self.assertEqual(r["response_bytes"], len(blob(fixture())))
        self.assertEqual(r["gis_archive_files_downloaded"], 0)
        self.assertEqual(r["pdf_files_downloaded"], 0)
        self.assertFalse(r["original_provider_payload_persisted"])
        self.assertFalse(r["cat_model_input_approved"])
        self.assertNotIn("files", r)

    def test_http_mime_redirect_encoding_size_and_partial_fail(self):
        for response in (
            FakeResponse(status=206),
            FakeResponse(url="https://another.invalid/"),
            FakeResponse(media="text/html"),
            FakeResponse(extra={"Content-Encoding": "gzip"}),
            FakeResponse(extra={"Content-Length": "abc"}),
            FakeResponse(extra={"Content-Length": str(MAX_BYTES + 1)}),
            FakeResponse(extra={"Content-Length": str(len(blob(fixture())) + 1)}),
            FakeResponse(data=blob(fixture()) + b" " * MAX_BYTES),
        ):
            with self.subTest(headers=response.headers, status=response.status):
                with self.assertRaises(HydroATLASBlocked):
                    probe(open_request=lambda req, timeout: response)

    def test_no_network_without_live_flag(self):
        with patch("scripts.probe_hydroatlas_figshare_v1_metadata_v0.probe") as p:
            with self.assertRaises(SystemExit) as c:
                main([])
        self.assertEqual(c.exception.code, 2)
        p.assert_not_called()

    def test_contract_revocation_disables_probe(self):
        from scripts.probe_hydroatlas_figshare_v1_metadata_v0 import validate_path
        c = copy.deepcopy(validate_path(CONTRACT_PATH))
        c["rights_and_policy"]["commercial_automation_status"] = "unknown"
        with patch("scripts.probe_hydroatlas_figshare_v1_metadata_v0.validate_path", return_value=c):
            with self.assertRaises(HydroATLASBlocked):
                verify_reviewed_contract()

    def test_redirect_handler_never_follows_other_sources(self):
        with self.assertRaises(HydroATLASBlocked):
            NoRedirect().redirect_request(None, None, 302, "moved", {},
                                          "https://other.invalid/")


if __name__ == "__main__":
    unittest.main()
