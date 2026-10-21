# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest
from unittest import mock

from research_runners import esrm20_country_viewer_exact_bytes as subject
from research_runners import esrm20_country_viewer_provenance as provenance


CANONICAL_URL = (
    "https://gitlab.seismo.ethz.ch/efehr/esrm20/-/raw/main/"
    "Risk/European_Risk_Country.csv?inline=false"
)
SYNTHETIC = b"Name,Synthetic\nKosovo,not-a-model-result\n"


class ViewerExactBytesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.hash_patch = mock.patch.multiple(
            provenance,
            FROZEN_V10_BYTE_COUNT=len(SYNTHETIC),
            FROZEN_V10_SHA256=hashlib.sha256(SYNTHETIC).hexdigest(),
            FROZEN_V10_BLOB_SHA1=subject._git_blob_sha1(SYNTHETIC),
        )
        self.hash_patch.start()
        self.addCleanup(self.hash_patch.stop)

    @staticmethod
    def receipt() -> dict:
        return {
            "project_id": 269,
            "project_path": "efehr/esrm20",
            "commit_sha": provenance.FROZEN_V10_COMMIT,
            "repository_path": provenance.COUNTRY_RISK_PATH,
            "byte_count": len(SYNTHETIC),
            "sha256": hashlib.sha256(SYNTHETIC).hexdigest(),
            "external_bytes_persisted": False,
        }

    def compare(self, *, viewer=SYNTHETIC, frozen=SYNTHETIC, url=CANONICAL_URL, receipt=None):
        return subject.compare_viewer_to_frozen(
            viewer_payload=viewer,
            viewer_final_url=url,
            frozen_payload=frozen,
            frozen_receipt=self.receipt() if receipt is None else receipt,
        )

    def test_exact_octets_prove_viewer_matches_frozen_v10(self):
        result = self.compare()
        self.assertEqual(result["status"], "VERIFIED")
        self.assertTrue(result["viewer_bytes_match_frozen_v10"])
        self.assertEqual(result["viewer_byte_count"], len(SYNTHETIC))
        self.assertEqual(result["viewer_sha256"], hashlib.sha256(SYNTHETIC).hexdigest())
        self.assertEqual(result["viewer_git_blob_sha1"], subject._git_blob_sha1(SYNTHETIC))
        for flag in (
            "provider_rows_returned",
            "provider_numeric_values_interpreted",
            "external_bytes_persisted",
            "denominator_semantics_verified",
            "threshold_compatibility_verified",
            "annualization_semantics_verified",
            "reference_loss_agreement_verified",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIs(result[flag], False, flag)
        self.assertNotIn("not-a-model-result", json.dumps(result))

    def test_one_byte_change_blocks_without_reporting_rows(self):
        result = self.compare(viewer=SYNTHETIC.replace(b"Kosovo", b"Kosova"))
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(result["viewer_bytes_match_frozen_v10"])
        self.assertNotIn("not-a-model-result", json.dumps(result))

    def test_wrong_frozen_receipt_rejected(self):
        receipt = self.receipt()
        receipt["sha256"] = "0" * 64
        with self.assertRaisesRegex(subject.ViewerExactBytesError, "not trusted"):
            self.compare(receipt=receipt)

    def test_modified_frozen_payload_rejected(self):
        with self.assertRaisesRegex(subject.ViewerExactBytesError, "differs"):
            self.compare(frozen=SYNTHETIC + b"x")

    def test_legacy_login_page_cannot_be_used_as_original_result(self):
        with self.assertRaises(subject.ViewerExactBytesError):
            self.compare(url="https://gitlab.seismo.ethz.ch/users/sign_in")

    def test_cross_host_redirect_cannot_claim_equivalence(self):
        with self.assertRaises(provenance.ViewerProvenanceError):
            self.compare(url="https://example.org/efehr/esrm20/-/raw/main/Risk/European_Risk_Country.csv")

    def test_large_viewer_or_frozen_body_rejected(self):
        with self.assertRaisesRegex(subject.ViewerExactBytesError, "bounded"):
            self.compare(viewer=b"x" * (subject.MAX_VIEWER_BYTES + 1))
        with self.assertRaisesRegex(subject.ViewerExactBytesError, "bounded"):
            self.compare(frozen=b"x" * (subject.MAX_VIEWER_BYTES + 1))

    def test_run_uses_existing_fixed_source_worker_not_another_downloader(self):
        with mock.patch.object(
            subject, "_acquire_viewer_body", return_value=(SYNTHETIC, CANONICAL_URL)
        ), mock.patch.object(
            subject.country,
            "acquire_country_risk_receipt_with_payload",
            return_value=(self.receipt(), SYNTHETIC),
        ) as acquire:
            result = subject.run()
        self.assertTrue(result["viewer_bytes_match_frozen_v10"])
        acquire.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
