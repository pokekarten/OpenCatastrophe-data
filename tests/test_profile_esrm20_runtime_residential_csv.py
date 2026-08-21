# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest
from unittest import mock

from scripts import profile_esrm20_runtime_residential_csv as subject


class RuntimeResidentialCsvProfileTests(unittest.TestCase):
    def test_receipt_identity_is_frozen_to_trusted_terminal(self):
        self.assertEqual(subject.PROJECT_ID, 269)
        self.assertEqual(
            subject.COMMIT_SHA,
            "05f83bbc9df81d02ee8ddb1801d9d781355ce783",
        )
        self.assertEqual(
            subject.REPOSITORY_PATH,
            "Exposure/OQ_Exposure_Input_Kosovo_Res.csv",
        )
        self.assertEqual(subject.RECEIPT_COMMENT_ID, 5369154884)
        self.assertEqual(subject.EXPECTED_BYTE_COUNT, 160_627)
        self.assertEqual(
            subject.EXPECTED_SHA256,
            "12a20d393c8d677d304263aed96eb05f81098104fd7e3fb0d119aafc336aa00f",
        )

    def test_identity_mismatch_blocks_before_csv_profiler(self):
        raw = b"a,b\n1,2\n"
        receipt = {
            "byte_count": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
        with self.assertRaises(subject.ByteIdentityMismatch):
            subject._verify_receipt_identity(raw, receipt)

    def test_profile_delegates_only_after_exact_identity_and_preserves_authority_ceiling(self):
        raw = b"x" * subject.EXPECTED_BYTE_COUNT
        receipt = {
            "retrieved_at": "2026-08-21T11:18:50Z",
            "byte_count": subject.EXPECTED_BYTE_COUNT,
            "sha256": subject.EXPECTED_SHA256,
            "content_type": "text/plain; charset=utf-8",
            "etag": None,
        }
        profile = {
            "schema_version": "oc-esrm20-exposure-content-profile-v0",
            "parser": {
                "encoding": "utf-8",
                "bom_present": False,
                "delimiter": ",",
                "line_endings": {"crlf_count": 0, "lf_count": 1, "cr_count": 0},
            },
            "record_count": 1,
            "header": ["a", "b"],
            "columns": [],
            "raw_rows_returned": False,
            "external_bytes_persisted": False,
            "publication_authorized": False,
        }
        digest = mock.Mock()
        digest.hexdigest.return_value = subject.EXPECTED_SHA256
        with (
            mock.patch.object(subject, "_fetch_exact_payload", return_value=(raw, receipt)),
            mock.patch.object(subject.hashlib, "sha256", return_value=digest),
            mock.patch.object(subject, "profile_verified_csv_bytes", return_value=profile) as profiler,
        ):
            result = subject.profile_runtime_residential_csv(
                opener=object(),
                now=lambda: "unused",
                monotonic=lambda: 0.0,
            )
        profiler.assert_called_once_with(
            raw,
            expected_byte_count=subject.EXPECTED_BYTE_COUNT,
            expected_sha256=subject.EXPECTED_SHA256,
        )
        self.assertIs(result["external_bytes_persisted"], False)
        self.assertIs(result["publication_authorized"], False)
        self.assertIs(result["model_use_authorized"], False)

    def test_profiler_authority_widening_fails_closed(self):
        raw = b"x" * subject.EXPECTED_BYTE_COUNT
        receipt = {
            "retrieved_at": "2026-08-21T11:18:50Z",
            "byte_count": subject.EXPECTED_BYTE_COUNT,
            "sha256": subject.EXPECTED_SHA256,
            "content_type": "text/plain; charset=utf-8",
            "etag": None,
        }
        profile = {
            "raw_rows_returned": True,
            "external_bytes_persisted": False,
            "publication_authorized": False,
        }
        digest = mock.Mock()
        digest.hexdigest.return_value = subject.EXPECTED_SHA256
        with (
            mock.patch.object(subject, "_fetch_exact_payload", return_value=(raw, receipt)),
            mock.patch.object(subject.hashlib, "sha256", return_value=digest),
            mock.patch.object(subject, "profile_verified_csv_bytes", return_value=profile),
        ):
            with self.assertRaises(subject.CsvContentProfileError):
                subject.profile_runtime_residential_csv(
                    opener=object(),
                    now=lambda: "unused",
                    monotonic=lambda: 0.0,
                )


if __name__ == "__main__":
    unittest.main()
