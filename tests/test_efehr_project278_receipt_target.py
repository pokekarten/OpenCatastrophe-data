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
DATASET_ID = "efehr.esrm20.sitemodel-source"
PROJECT_ID = 278
COMMIT = "038c91d2bf5a07f6b54ff51639aad874d6837ea9"
PATH = "ExposureReadme.pdf"
RETRIEVED = "2026-08-25T21:20:00Z"


class EfehrProject278ReceiptTargetTests(unittest.TestCase):
    def _target(self):
        return validate_target(
            source_issue=SOURCE_ISSUE,
            dataset_id=DATASET_ID,
            project_id=PROJECT_ID,
            commit_sha=COMMIT,
            repository_path=PATH,
        )

    def test_exact_exposure_readme_pdf_target_and_binary_receipt(self) -> None:
        target = self._target()
        self.assertEqual(target.project_path, "efehr/esrm20_sitemodel")
        self.assertEqual(target.source_issue, SOURCE_ISSUE)
        self.assertEqual(target.dataset_id, DATASET_ID)
        self.assertEqual(target.project_id, PROJECT_ID)
        self.assertEqual(target.commit_sha, COMMIT)
        self.assertEqual(target.repository_path, PATH)

        url = raw_file_api_url(target)
        self.assertIn("/projects/278/", url)
        self.assertIn("ExposureReadme.pdf", url)
        self.assertIn(COMMIT, url)

        payload = b"%PDF-1.7\nsynthetic-test-only\n%%EOF\n"
        receipt = receipt_from_stream(
            target,
            io.BytesIO(payload),
            final_url=url,
            retrieved_at=RETRIEVED,
            headers={
                "Content-Length": str(len(payload)),
                "Content-Type": "application/pdf",
            },
        )
        self.assertEqual(receipt["project_id"], PROJECT_ID)
        self.assertEqual(receipt["project_path"], "efehr/esrm20_sitemodel")
        self.assertEqual(receipt["commit_sha"], COMMIT)
        self.assertEqual(receipt["repository_path"], PATH)
        self.assertEqual(receipt["byte_count"], len(payload))
        self.assertEqual(receipt["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(receipt["content_type"], "application/pdf")
        self.assertFalse(receipt["external_bytes_persisted"])
        self.assertFalse(receipt["publication_authorized"])

    def test_wrong_issue_dataset_project_commit_or_path_fail_closed(self) -> None:
        base = {
            "source_issue": SOURCE_ISSUE,
            "dataset_id": DATASET_ID,
            "project_id": PROJECT_ID,
            "commit_sha": COMMIT,
            "repository_path": PATH,
        }
        mutations = (
            {"source_issue": 284},
            {"dataset_id": "efehr.esrm20.risk-inputs.v1.0"},
            {"project_id": 269},
            {"commit_sha": "b" * 40},
            {"repository_path": "README.md"},
            {"repository_path": "ExposureReadme.PDF"},
            {"repository_path": "docs/ExposureReadme.pdf"},
            {"repository_path": "subdir/../ExposureReadme.pdf"},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(EfehrReceiptError):
                validate_target(**dict(base, **mutation))


if __name__ == "__main__":
    unittest.main()
