# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import io
import unittest

from scripts.efehr_gitlab_receipt import (
    ESHM20_PREFIX,
    EfehrReceiptError,
    raw_file_api_url,
    receipt_from_stream,
    validate_final_url,
    validate_public_addresses,
    validate_target,
)

COMMIT = "a" * 40
RETRIEVED = "2026-08-13T00:30:00Z"


class EfehrGitlabReceiptTests(unittest.TestCase):
    def _mapping_target(self):
        return validate_target(
            source_issue=283,
            dataset_id="efehr.esrm20.risk-inputs.v1.0",
            project_id=269,
            commit_sha=COMMIT,
            repository_path="Vulnerability/esrm20_exposure_vulnerability_mapping.csv",
        )

    def _site_target(self):
        return validate_target(
            source_issue=284,
            dataset_id="efehr.esrm20.risk-inputs.v1.0",
            project_id=269,
            commit_sha=COMMIT,
            repository_path="Vs30/Site_model_Kosovo.xml",
        )

    def test_kosovo_exposure_targets_are_exactly_allowlisted(self) -> None:
        target = validate_target(
            source_issue=282,
            dataset_id="efehr.esrm20.european-exposure-model.v1.0",
            project_id=186,
            commit_sha=COMMIT,
            repository_path="_exposure_models/Exposure_Model_Kosovo_Res.csv",
        )
        self.assertEqual(target.project_path, "efehr/esrm20_exposure")
        self.assertIn("%2F", raw_file_api_url(target))
        for path in (
            "_exposure_models/Exposure_Model_Kosovo_Ind.csv",
            "_exposure_models/Exposure_Model_Italy_Res.csv",
            "_exposure_models/subdir/../Exposure_Model_Kosovo_Res.csv",
        ):
            with self.subTest(path=path), self.assertRaises(EfehrReceiptError):
                validate_target(
                    source_issue=282,
                    dataset_id="efehr.esrm20.european-exposure-model.v1.0",
                    project_id=186,
                    commit_sha=COMMIT,
                    repository_path=path,
                )

    def test_kosovo_site_model_is_exactly_allowlisted_under_issue_284(self) -> None:
        site = self._site_target()
        self.assertEqual(site.project_path, "efehr/esrm20")
        self.assertEqual(site.dataset_id, "efehr.esrm20.risk-inputs.v1.0")
        self.assertEqual(site.repository_path, "Vs30/Site_model_Kosovo.xml")
        self.assertIn("Vs30%2FSite_model_Kosovo.xml", raw_file_api_url(site))

        for mutation in (
            {"source_issue": 283},
            {"dataset_id": "efehr.esrm20.vulnerability.v1.1"},
            {"project_id": 188},
            {"repository_path": "Vs30/Site_model_Albania.xml"},
            {"repository_path": "Vs30/Site_model_Kosovo.csv"},
            {"repository_path": "Vulnerability/esrm20_exposure_vulnerability_mapping.csv"},
        ):
            base = dict(
                source_issue=284,
                dataset_id="efehr.esrm20.risk-inputs.v1.0",
                project_id=269,
                commit_sha=COMMIT,
                repository_path="Vs30/Site_model_Kosovo.xml",
            )
            with self.subTest(mutation=mutation), self.assertRaises(EfehrReceiptError):
                validate_target(**dict(base, **mutation))

        payload = b"<siteModel>synthetic-test-only</siteModel>"
        receipt = receipt_from_stream(
            site,
            io.BytesIO(payload),
            final_url=raw_file_api_url(site),
            retrieved_at=RETRIEVED,
            headers={"Content-Length": str(len(payload)), "Content-Type": "application/xml"},
        )
        self.assertEqual(receipt["source_issue"], 284)
        self.assertEqual(receipt["repository_path"], "Vs30/Site_model_Kosovo.xml")
        self.assertEqual(receipt["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertFalse(receipt["external_bytes_persisted"])
        self.assertFalse(receipt["publication_authorized"])

    def test_mapping_has_distinct_risk_input_identity_and_vulnerability_stays_separate(self) -> None:
        mapping = self._mapping_target()
        self.assertEqual(mapping.project_path, "efehr/esrm20")
        self.assertEqual(mapping.dataset_id, "efehr.esrm20.risk-inputs.v1.0")

        with self.assertRaisesRegex(EfehrReceiptError, "binding is not allow-listed"):
            validate_target(
                source_issue=283,
                dataset_id="efehr.esrm20.vulnerability.v1.1",
                project_id=269,
                commit_sha=COMMIT,
                repository_path="Vulnerability/esrm20_exposure_vulnerability_mapping.csv",
            )

        with self.assertRaisesRegex(EfehrReceiptError, "source-derived"):
            validate_target(
                source_issue=283,
                dataset_id="efehr.esrm20.vulnerability.v1.1",
                project_id=188,
                commit_sha=COMMIT,
                repository_path="vulnerability_models/example.csv",
            )

    def test_eshm20_is_restricted_to_selected_configuration_and_safe_file_types(self) -> None:
        valid = ESHM20_PREFIX + "source_model_logic_tree_eshm20_model_v12e.xml"
        validate_target(
            source_issue=281,
            dataset_id="efehr.eshm20",
            project_id=197,
            commit_sha=COMMIT,
            repository_path=valid,
        )
        for path in (
            "oq_computational/other_config/job.ini",
            ESHM20_PREFIX + "payload.zip",
            ESHM20_PREFIX + "../secret.xml",
        ):
            with self.subTest(path=path), self.assertRaises(EfehrReceiptError):
                validate_target(
                    source_issue=281,
                    dataset_id="efehr.eshm20",
                    project_id=197,
                    commit_sha=COMMIT,
                    repository_path=path,
                )

    def test_mutable_refs_wrong_bindings_and_unsafe_paths_fail_closed(self) -> None:
        base = dict(
            source_issue=282,
            dataset_id="efehr.esrm20.european-exposure-model.v1.0",
            project_id=186,
            commit_sha=COMMIT,
            repository_path="_exposure_models/Exposure_Model_Kosovo_Res.csv",
        )
        for mutation in (
            {"commit_sha": "v1.0"},
            {"commit_sha": "A" * 40},
            {"project_id": 197},
            {"source_issue": 281},
            {"repository_path": "/etc/passwd"},
            {"repository_path": "_exposure_models\\Exposure_Model_Kosovo_Res.csv"},
            {"repository_path": "_exposure_models/%2e%2e/file.csv"},
        ):
            with self.subTest(mutation=mutation), self.assertRaises(EfehrReceiptError):
                validate_target(**dict(base, **mutation))

    def test_receipt_hashes_exact_bytes_without_persistence(self) -> None:
        target = self._mapping_target()
        payload = b"taxonomy,vulnerability_id\nA,vm1\n"
        url = raw_file_api_url(target)
        receipt = receipt_from_stream(
            target,
            io.BytesIO(payload),
            final_url=url,
            retrieved_at=RETRIEVED,
            headers={"Content-Length": str(len(payload)), "Content-Type": "text/csv"},
        )
        self.assertEqual(receipt["dataset_id"], "efehr.esrm20.risk-inputs.v1.0")
        self.assertEqual(receipt["byte_count"], len(payload))
        self.assertEqual(receipt["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertFalse(receipt["external_bytes_persisted"])
        self.assertFalse(receipt["publication_authorized"])
        self.assertEqual(receipt["commit_sha"], COMMIT)

    def test_stream_bounds_length_mismatch_empty_and_nonbytes_fail_closed(self) -> None:
        target = self._mapping_target()
        url = raw_file_api_url(target)
        cases = (
            (io.BytesIO(b""), {}, 10),
            (io.BytesIO(b"abc"), {"Content-Length": "4"}, 10),
            (io.BytesIO(b"abcd"), {}, 3),
        )
        for stream, headers, max_bytes in cases:
            with self.subTest(headers=headers, max_bytes=max_bytes), self.assertRaises(EfehrReceiptError):
                receipt_from_stream(
                    target,
                    stream,
                    final_url=url,
                    retrieved_at=RETRIEVED,
                    headers=headers,
                    max_bytes=max_bytes,
                )

        class BadStream:
            def read(self, size: int):
                return "not-bytes"

        with self.assertRaisesRegex(EfehrReceiptError, "non-byte"):
            receipt_from_stream(
                target,
                BadStream(),
                final_url=url,
                retrieved_at=RETRIEVED,
            )

    def test_receipt_timestamp_must_be_canonical_and_calendar_valid(self) -> None:
        target = self._mapping_target()
        url = raw_file_api_url(target)
        payload = b"x"
        receipt = receipt_from_stream(
            target,
            io.BytesIO(payload),
            final_url=url,
            retrieved_at="2026-08-13T00:30:00.123456Z",
        )
        self.assertEqual(receipt["retrieved_at"], "2026-08-13T00:30:00.123456Z")

        for timestamp in (
            "xxxxxxxxxxxxxxxxxxxZ",
            "2026-13-13T00:30:00Z",
            "2026-08-13T24:30:00Z",
            "2026-08-13T00:30:00+00:00",
            "2026-08-13T00:30Z",
            "2026-08-13T00:30:00.1234567Z",
        ):
            with self.subTest(timestamp=timestamp), self.assertRaises(EfehrReceiptError):
                receipt_from_stream(
                    target,
                    io.BytesIO(payload),
                    final_url=url,
                    retrieved_at=timestamp,
                )

    def test_receipt_headers_reject_control_characters_and_oversize_values(self) -> None:
        target = self._mapping_target()
        url = raw_file_api_url(target)
        payload = b"x"
        for headers in (
            {"Content-Type": "text/csv\r\nInjected: true"},
            {"ETag": "unsafe\x00value"},
            {"ETag": "x" * 1025},
            {"Content-Length": "1\t"},
        ):
            with self.subTest(headers=headers), self.assertRaises(EfehrReceiptError):
                receipt_from_stream(
                    target,
                    io.BytesIO(payload),
                    final_url=url,
                    retrieved_at=RETRIEVED,
                    headers=headers,
                )

    def test_final_url_and_dns_boundary_fail_closed(self) -> None:
        target = self._mapping_target()
        expected = raw_file_api_url(target)
        self.assertEqual(validate_final_url(target, expected), expected)
        for url in (
            expected.replace("https://", "http://", 1),
            expected.replace("gitlab.seismo.ethz.ch", "example.com", 1),
            expected + "#fragment",
        ):
            with self.subTest(url=url), self.assertRaises(EfehrReceiptError):
                validate_final_url(target, url)

        self.assertEqual(validate_public_addresses(["8.8.8.8"]), ("8.8.8.8",))
        for addresses in (["127.0.0.1"], ["10.0.0.1"], ["169.254.1.1"], ["::1"], []):
            with self.subTest(addresses=addresses), self.assertRaises(EfehrReceiptError):
                validate_public_addresses(addresses)


if __name__ == "__main__":
    unittest.main()
