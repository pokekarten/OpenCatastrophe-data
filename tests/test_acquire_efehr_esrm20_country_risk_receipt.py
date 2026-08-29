# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import inspect
import unittest
from unittest import mock

from scripts import acquire_efehr_esrm20_country_risk_receipt as subject
from scripts.efehr_gitlab_receipt import EfehrReceiptError, raw_file_api_url, validate_target

RETRIEVED_AT = "2026-08-29T09:05:00Z"
PAYLOAD = b"synthetic_col_a,synthetic_col_b\nsynthetic_row,1.25\n"


class FakeResponse:
    def __init__(self, payload: bytes, url: str, *, status: int = 200, headers=None) -> None:
        self._payload = payload
        self._offset = 0
        self._url = url
        self.status = status
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def geturl(self) -> str:
        return self._url

    def read(self, size: int = -1) -> bytes:
        if self._offset >= len(self._payload):
            return b""
        end = len(self._payload) if size is None or size < 0 else min(
            len(self._payload), self._offset + size
        )
        chunk = self._payload[self._offset:end]
        self._offset = end
        return chunk


def _url() -> str:
    target = validate_target(
        source_issue=subject.SOURCE_ISSUE,
        dataset_id=subject.DATASET_ID,
        project_id=subject.PROJECT_ID,
        commit_sha=subject.COMMIT_SHA,
        repository_path=subject.REPOSITORY_PATH,
    )
    return raw_file_api_url(target)


class Esrm20CountryRiskReceiptTests(unittest.TestCase):
    def test_fixed_worker_hashes_only_the_immutable_country_table(self) -> None:
        url = _url()
        calls = []

        def opener(request, timeout):
            calls.append((request, timeout))
            return FakeResponse(
                PAYLOAD,
                url,
                headers={
                    "Content-Length": str(len(PAYLOAD)),
                    "Content-Type": "text/csv",
                    "ETag": '"synthetic"',
                },
            )

        receipt = subject.acquire_country_risk_receipt(
            opener=opener,
            now=lambda: RETRIEVED_AT,
            monotonic=lambda: 0.0,
        )

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0].full_url, url)
        self.assertEqual(calls[0][0].method, "GET")
        self.assertEqual(receipt["source_issue"], 778)
        self.assertEqual(receipt["dataset_id"], "efehr.esrm20.risk-inputs.v1.0")
        self.assertEqual(receipt["project_id"], 269)
        self.assertEqual(receipt["project_path"], "efehr/esrm20")
        self.assertEqual(receipt["commit_sha"], subject.COMMIT_SHA)
        self.assertEqual(receipt["repository_path"], "Risk/European_Risk_Country.csv")
        self.assertEqual(receipt["byte_count"], len(PAYLOAD))
        self.assertEqual(receipt["sha256"], hashlib.sha256(PAYLOAD).hexdigest())
        self.assertEqual(receipt["content_type"], "text/csv")
        self.assertFalse(receipt["external_bytes_persisted"])
        self.assertFalse(receipt["provider_rows_exposed"])
        self.assertFalse(receipt["reference_loss_agreement_verified"])
        self.assertFalse(receipt["publication_authorized"])
        self.assertFalse(receipt["model_use_authorized"])
        self.assertNotIn("rows", receipt)
        self.assertNotIn(PAYLOAD.decode(), str(receipt))

    def test_issue_778_allowlist_is_exact_path_and_exact_commit(self) -> None:
        target = validate_target(
            source_issue=778,
            dataset_id=subject.DATASET_ID,
            project_id=269,
            commit_sha=subject.COMMIT_SHA,
            repository_path=subject.REPOSITORY_PATH,
        )
        self.assertEqual(target.repository_path, subject.REPOSITORY_PATH)

        with self.assertRaisesRegex(EfehrReceiptError, "exact source-derived commit"):
            validate_target(
                source_issue=778,
                dataset_id=subject.DATASET_ID,
                project_id=269,
                commit_sha="0" * 40,
                repository_path=subject.REPOSITORY_PATH,
            )
        with self.assertRaisesRegex(EfehrReceiptError, "exact P0 file allow-list"):
            validate_target(
                source_issue=778,
                dataset_id=subject.DATASET_ID,
                project_id=269,
                commit_sha=subject.COMMIT_SHA,
                repository_path="Risk/another.csv",
            )

    def test_worker_has_no_provider_target_selectors(self) -> None:
        signature = inspect.signature(subject.acquire_country_risk_receipt)
        self.assertEqual(set(signature.parameters), {"opener", "now", "monotonic"})
        for forbidden in (
            "project_id",
            "project_path",
            "commit_sha",
            "repository_path",
            "dataset_id",
            "source_issue",
            "url",
        ):
            self.assertNotIn(forbidden, signature.parameters)

    def test_declared_oversize_fails_before_payload_read(self) -> None:
        url = _url()
        response = FakeResponse(
            PAYLOAD,
            url,
            headers={"Content-Length": str(subject.MAX_COUNTRY_RISK_BYTES + 1)},
        )

        with self.assertRaisesRegex(
            subject.Esrm20CountryRiskReceiptError, "provider country-risk acquisition failed"
        ):
            subject.acquire_country_risk_receipt(
                opener=lambda request, timeout: response,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )
        self.assertEqual(response._offset, 0)

    def test_production_identity_rejects_path_drift(self) -> None:
        with mock.patch.object(subject, "REPOSITORY_PATH", "Risk/Other.csv"):
            with self.assertRaisesRegex(
                subject.Esrm20CountryRiskReceiptError, "frozen country-risk authority drifted"
            ):
                subject._require_production_identity()


if __name__ == "__main__":
    unittest.main()
