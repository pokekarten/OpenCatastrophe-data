# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import io
import unittest

from scripts.efehr_gitlab_receipt import (
    EfehrReceiptError,
    raw_file_api_url,
    receipt_from_stream,
    validate_target,
)


SOURCE_ISSUE = 291
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 278
COMMIT_SHA = "038c91d2bf5a07f6b54ff51639aad874d6837ea9"
REPOSITORY_PATH = "ExposureReadme.pdf"
RETRIEVED_AT = "2026-08-25T21:20:00Z"


class Project278ExposureReadmeReceiptTests(unittest.TestCase):
    def _target(self):
        return validate_target(
            source_issue=SOURCE_ISSUE,
            dataset_id=DATASET_ID,
            project_id=PROJECT_ID,
            commit_sha=COMMIT_SHA,
            repository_path=REPOSITORY_PATH,
        )

    def test_exact_fixed_pdf_target_is_admitted(self) -> None:
        target = self._target()
        self.assertEqual(target.project_path, "efehr/esrm20_sitemodel")
        self.assertEqual(target.source_issue, SOURCE_ISSUE)
        self.assertEqual(target.commit_sha, COMMIT_SHA)
        self.assertEqual(target.repository_path, REPOSITORY_PATH)
        url = raw_file_api_url(target)
        self.assertIn("projects/278/", url)
        self.assertIn("ExposureReadme.pdf", url)
        self.assertIn(COMMIT_SHA, url)

    def test_target_identity_mutations_fail_closed(self) -> None:
        base = {
            "source_issue": SOURCE_ISSUE,
            "dataset_id": DATASET_ID,
            "project_id": PROJECT_ID,
            "commit_sha": COMMIT_SHA,
            "repository_path": REPOSITORY_PATH,
        }
        mutations = (
            {"source_issue": 284},
            {"dataset_id": "efehr.esrm20.vulnerability.v1.1"},
            {"project_id": 269},
            {"repository_path": "README.md"},
            {"repository_path": "docs/ExposureReadme.pdf"},
            {"commit_sha": "a" * 40},
            {"commit_sha": "main"},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(EfehrReceiptError):
                validate_target(**dict(base, **mutation))

    def test_receipt_hashes_synthetic_pdf_bytes_without_persistence(self) -> None:
        target = self._target()
        payload = b"%PDF-1.4\n% synthetic test only\n%%EOF\n"
        receipt = receipt_from_stream(
            target,
            io.BytesIO(payload),
            final_url=raw_file_api_url(target),
            retrieved_at=RETRIEVED_AT,
            headers={
                "Content-Length": str(len(payload)),
                "Content-Type": "application/pdf",
            },
        )
        self.assertEqual(receipt["source_issue"], SOURCE_ISSUE)
        self.assertEqual(receipt["project_id"], PROJECT_ID)
        self.assertEqual(receipt["project_path"], "efehr/esrm20_sitemodel")
        self.assertEqual(receipt["commit_sha"], COMMIT_SHA)
        self.assertEqual(receipt["repository_path"], REPOSITORY_PATH)
        self.assertEqual(receipt["byte_count"], len(payload))
        self.assertEqual(receipt["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertFalse(receipt["external_bytes_persisted"])
        self.assertFalse(receipt["publication_authorized"])


if __name__ == "__main__":
    unittest.main()
