# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic, offline tests for the trusted-main, fixed-source GRWL evidence runner."""
import hashlib
import io
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from unittest.mock import patch

from research_runners.grwl_trusted_original_byte_proof_v0 import (
    BoundedRedirects, ORIGINAL_URLS, OriginalAcquisitionError, SOURCE_FILES,
    _safe_redirect_host, default_open, download_fixed, main as runner_main, run_live,
)


class FakeResponse(io.BytesIO):
    def __init__(self, payload=b"12345", *, status=200, header_bytes=None, content_type="application/zip"):
        super().__init__(payload)
        self.status = status
        self.headers = {"Content-Type": content_type}
        if header_bytes is not None:
            self.headers["Content-Length"] = str(header_bytes)


class GRWLTrustedOriginalTests(TestCase):
    def _invoke(self, payload=b"12345", **options):
        with TemporaryDirectory() as tmp:
            target = Path(tmp) / SOURCE_FILES["2018"][0]
            frozen = (SOURCE_FILES["2018"][0], len(payload), hashlib.md5(payload).hexdigest())
            with patch.dict(SOURCE_FILES, {"2018": frozen}):
                evidence = download_fixed("2018", target,
                    open_stream=lambda url: FakeResponse(payload, **options))
                self.assertEqual(target.read_bytes(), payload)
        return evidence

    def test_exact_fixed_original_download_receipt(self):
        r = self._invoke()
        self.assertEqual(r["independent_original_zip_sha256"], hashlib.sha256(b"12345").hexdigest())
        self.assertEqual(r["release"], "2018")

    def test_download_second_release_with_exact_frozen_identity(self):
        payload=b"a different synthetic zip payload"
        with TemporaryDirectory() as tmp:
            target=Path(tmp)/SOURCE_FILES["2026"][0]
            frozen=(SOURCE_FILES["2026"][0],len(payload),hashlib.md5(payload).hexdigest())
            with patch.dict(SOURCE_FILES, {"2026": frozen}):
                r=download_fixed("2026",target,open_stream=lambda url: FakeResponse(payload))
        self.assertEqual(r["release"],"2026")

    def test_non_200_rejected(self):
        with self.assertRaises(OriginalAcquisitionError):self._invoke(status=206)

    def test_content_length_mismatch_rejected(self):
        with self.assertRaises(OriginalAcquisitionError):self._invoke(header_bytes=999)

    def test_html_response_rejected(self):
        with self.assertRaises(OriginalAcquisitionError):self._invoke(content_type="text/html")

    def test_missing_content_length_accepted_only_after_full_integrity_check(self):
        result = self._invoke()
        self.assertEqual(result["bytes"], 5)

    def test_response_mime_rejects_html_before_writing(self):
        with TemporaryDirectory() as tmp:
            target = Path(tmp) / SOURCE_FILES["2018"][0]
            with self.assertRaises(OriginalAcquisitionError):
                download_fixed("2018", target,
                    open_stream=lambda url: FakeResponse(b"<html>", content_type="text/html"))
            self.assertFalse(target.exists())

    def test_json_response_rejected(self):
        with self.assertRaises(OriginalAcquisitionError):self._invoke(content_type="application/json")

    def test_short_download_rejected(self):
        with TemporaryDirectory() as tmp:
            target=Path(tmp)/SOURCE_FILES["2018"][0]
            with self.assertRaises(OriginalAcquisitionError):
                download_fixed("2018",target,open_stream=lambda url: FakeResponse(b"123"))

    def test_md5_mismatch_rejected(self):
        with TemporaryDirectory() as tmp:
            target=Path(tmp)/SOURCE_FILES["2018"][0]
            frozen=(SOURCE_FILES["2018"][0],5,"f"*32)
            with patch.dict(SOURCE_FILES, {"2018": frozen}):
                with self.assertRaises(OriginalAcquisitionError):
                    download_fixed("2018",target,open_stream=lambda url: FakeResponse(b"12345"))

    def test_oversized_download_rejected(self):
        with TemporaryDirectory() as tmp:
            target=Path(tmp)/SOURCE_FILES["2018"][0]
            with self.assertRaises(OriginalAcquisitionError):
                download_fixed("2018",target,open_stream=lambda url: FakeResponse(b"x"*10))

    def test_bad_release_rejected(self):
        with self.assertRaises(OriginalAcquisitionError):
            download_fixed("unknown",Path("/tmp/invalid.zip"),open_stream=lambda url: FakeResponse())

    def test_wrong_destination_name_rejected(self):
        with TemporaryDirectory() as tmp:
            with self.assertRaises(OriginalAcquisitionError):
                download_fixed("2018",Path(tmp)/"other.zip",open_stream=lambda url: FakeResponse())

    def test_overwrite_existing_file_rejected(self):
        with TemporaryDirectory() as tmp:
            target=Path(tmp)/SOURCE_FILES["2018"][0]
            target.write_bytes(b"already")
            with self.assertRaises(OriginalAcquisitionError):
                download_fixed("2018",target,open_stream=lambda url: FakeResponse())

    def test_non_allowlisted_url_rejected_before_network(self):
        with self.assertRaises(OriginalAcquisitionError):
            default_open("https://attacker.invalid/evil.zip")

    def test_only_approved_https_redirects(self):
        for value in ("http://zenodo.org/a","https://" + "127" + ".0.0.1/a","https://" + "local" + "host/a",
                      "https://evil.example/a","https://zenodo.org.evil.example/a",
                      "https://user:pass@zenodo.org/a","https://zenodo.org:8443/a"):
            with self.subTest(url=value):
                self.assertFalse(_safe_redirect_host(value))
        self.assertTrue(_safe_redirect_host("https://zenodo.org/api/files/example"))
        self.assertTrue(_safe_redirect_host("https://cdn.zenodo.org/file"))
        self.assertTrue(_safe_redirect_host("https://s3.eu-central-1.amazonaws.com/file"))

    def test_default_no_network(self):
        self.assertEqual(runner_main([]),2)

    def test_original_zip_filenames_are_pinned(self):
        self.assertEqual(list(ORIGINAL_URLS), ["2018", "2026"])
        self.assertEqual(SOURCE_FILES["2026"][1]-SOURCE_FILES["2018"][1],88699)

    def test_run_live_only_returns_false_authority_ceilings(self):
        def fake_download(release,target):
            target.write_bytes(b"synthetic")
            return {"release":release,"independent_original_zip_sha256":"0"*64}
        comparison={"original_zip_sha256_receipts":[{"release":"2018","sha256":"0"*64},
                                                     {"release":"2026","sha256":"0"*64}]}
        with patch("research_runners.grwl_trusted_original_byte_proof_v0.download_fixed",side_effect=fake_download),patch(
                 "research_runners.grwl_trusted_original_byte_proof_v0.compare_original_archives",return_value=comparison):
            out=run_live()
        self.assertEqual(out["schema"],"opencatastrophe-grwl-trusted-original-byte-evidence-v0")
        for key in ("third_party_payloads_printed_or_persisted",
                    "geospatial_justification_for_width_changes","source_data_admitted","production_database_modified"):
            self.assertFalse(out[key])


if __name__ == "__main__":
    main()
