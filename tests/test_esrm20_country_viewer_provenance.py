# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from research_runners import esrm20_country_viewer_provenance as subject


class ViewerProvenanceTests(unittest.TestCase):
    def project(self) -> dict:
        return {
            "project_id": 269,
            "project_path": "efehr/esrm20",
            "default_branch": "main",
            "web_url": "https://gitlab.seismo.ethz.ch/efehr/esrm20",
        }

    def file(self, *, blob: str | None = None, size: int | None = None) -> dict:
        return {
            "blob_id": blob or subject.FROZEN_V10_BLOB_SHA1,
            "content_sha256": subject.FROZEN_V10_SHA256,
            "size": size or subject.FROZEN_V10_BYTE_COUNT,
            "ref": "main",
            "file_path": subject.COUNTRY_RISK_PATH,
            "commit_id": "1" * 40,
            "last_commit_id": "2" * 40,
        }

    def test_happy_path_proves_exact_blob_equivalence(self) -> None:
        result = subject.build_result(
            legacy_final_url=(
                "https://gitlab.seismo.ethz.ch/efehr/esrm20/-/raw/main/"
                "Risk/European_Risk_Country.csv?inline=false"
            ),
            project_metadata=self.project(),
            file_metadata=self.file(),
        )
        self.assertTrue(result["viewer_main_byte_equivalence_verified"])
        self.assertEqual(
            result["conclusion"],
            "VIEWER_MAIN_BLOB_IDENTICAL_TO_FROZEN_V1_0",
        )
        self.assertFalse(result["provider_file_body_read"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["reference_loss_agreement_verified"])

    def test_changed_blob_fails_equivalence(self) -> None:
        result = subject.build_result(
            legacy_final_url=(
                "https://gitlab.seismo.ethz.ch/efehr/esrm20/-/raw/main/"
                "Risk/European_Risk_Country.csv?inline=false"
            ),
            project_metadata=self.project(),
            file_metadata=self.file(blob="3" * 40),
        )
        self.assertFalse(result["viewer_main_byte_equivalence_verified"])
        self.assertEqual(
            result["conclusion"],
            "VIEWER_MAIN_BLOB_DIFFERS_FROM_FROZEN_V1_0",
        )

    def test_redirect_chain_can_prove_canonicalization_before_sign_in(self) -> None:
        result = subject.build_result(
            legacy_final_url="https://gitlab.seismo.ethz.ch/users/sign_in",
            legacy_redirect_chain=[
                (
                    "https://gitlab.seismo.ethz.ch/efehr/esrm20/-/raw/main/"
                    "Risk/European_Risk_Country.csv?inline=false"
                ),
                "https://gitlab.seismo.ethz.ch/users/sign_in",
            ],
            project_metadata=self.project(),
            file_metadata=self.file(),
        )
        self.assertTrue(result["legacy_raw_redirects_to_canonical"])
        self.assertTrue(result["viewer_main_byte_equivalence_verified"])
        self.assertEqual(
            result["conclusion"],
            "VIEWER_MAIN_BLOB_IDENTICAL_TO_FROZEN_V1_0",
        )

    def test_wrong_redirect_fails_closed(self) -> None:
        result = subject.build_result(
            legacy_final_url=(
                "https://gitlab.seismo.ethz.ch/efehr/other/-/raw/main/"
                "Risk/European_Risk_Country.csv?inline=false"
            ),
            project_metadata=self.project(),
            file_metadata=self.file(),
        )
        self.assertFalse(result["viewer_main_byte_equivalence_verified"])
        self.assertEqual(
            result["conclusion"],
            "LEGACY_VIEWER_RAW_TARGET_NOT_CANONICALIZED",
        )

    def test_project_metadata_requires_exact_canonical_identity(self) -> None:
        with self.assertRaises(subject.ViewerProvenanceError):
            subject._parse_project_metadata(
                b'{"id":270,"path_with_namespace":"efehr/esrm20",'
                b'"default_branch":"main",'
                b'"web_url":"https://gitlab.seismo.ethz.ch/efehr/esrm20"}'
            )

    def test_file_head_parser_binds_blob_size_and_path(self) -> None:
        parsed = subject._parse_file_head(
            {
                "X-Gitlab-Blob-Id": subject.FROZEN_V10_BLOB_SHA1,
                "X-Gitlab-Content-Sha256": subject.FROZEN_V10_SHA256,
                "X-Gitlab-Size": str(subject.FROZEN_V10_BYTE_COUNT),
                "X-Gitlab-Ref": "main",
                "X-Gitlab-File-Path": subject.COUNTRY_RISK_PATH,
                "X-Gitlab-Commit-Id": "4" * 40,
                "X-Gitlab-Last-Commit-Id": "5" * 40,
            }
        )
        self.assertEqual(parsed["blob_id"], subject.FROZEN_V10_BLOB_SHA1)
        self.assertEqual(parsed["size"], subject.FROZEN_V10_BYTE_COUNT)

    def test_file_head_parser_rejects_wrong_ref(self) -> None:
        with self.assertRaises(subject.ViewerProvenanceError):
            subject._parse_file_head(
                {
                    "X-Gitlab-Blob-Id": subject.FROZEN_V10_BLOB_SHA1,
                    "X-Gitlab-Content-Sha256": subject.FROZEN_V10_SHA256,
                    "X-Gitlab-Size": str(subject.FROZEN_V10_BYTE_COUNT),
                    "X-Gitlab-Ref": "v1.0",
                    "X-Gitlab-File-Path": subject.COUNTRY_RISK_PATH,
                }
            )


if __name__ == "__main__":
    unittest.main()
