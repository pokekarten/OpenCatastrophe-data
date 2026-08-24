# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from scripts import run_esrm20_source_model_child_profiles_action as subject

EXECUTION_SHA = "1" * 40
OLD_SHA = "2" * 40
WORKFLOW_PATH = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "esrm20-source-model-child-profiles.yml"
)


class FakeResponse:
    def __init__(self, url: str, payload: bytes):
        self.status = 200
        self._url = url
        self._payload = payload
        self._offset = 0
        self.headers = {
            "Content-Type": "application/xml",
            "Content-Length": str(len(payload)),
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def geturl(self) -> str:
        return self._url

    def read(self, size: int = -1) -> bytes:
        if self._offset >= len(self._payload):
            return b""
        if size < 0:
            size = len(self._payload) - self._offset
        chunk = self._payload[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk


class OneShotOpener:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.calls = 0

    def __call__(self, request, timeout: float):
        self.calls += 1
        if self.calls > 1:
            raise AssertionError("unexpected extra provider request")
        return FakeResponse(request.full_url, self.payload)


def request_body(sha: str = EXECUTION_SHA) -> str:
    payload = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": subject.SOURCE_ISSUE,
        "target_sha": sha,
        "dataset_id": subject.DATASET_ID,
        "requester": "unit-test",
    }
    return subject.REQUEST_MARKER + "\n" + json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    )


def child_profile(path: str, byte_count: int, sha256: str) -> dict:
    return {
        "repository_path": path,
        "byte_count": byte_count,
        "sha256": sha256,
        "root_element": "nrml",
        "element_count": 3,
        "element_type_counts": {"nrml": 1, "sourceModel": 1, "pointSource": 1},
        "tectonic_region_type_counts": {"Active Shallow Crust": 1},
        "trt_provenance_counts": {"direct_source": 1},
        "byte_identity_verified": True,
        "source_model_content_profiled": True,
        "external_reference_scan_performed": False,
        "transitive_dependency_byte_closure_verified": False,
        "runtime_compatibility_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def synthetic_profile_set() -> dict:
    profiles = [
        child_profile(path, byte_count, sha256)
        for path, (byte_count, sha256) in subject._FIXED_RECEIPTS.items()
    ]
    return {
        "schema_version": subject.PROFILE_SET_SCHEMA_VERSION,
        "source_issue": subject.SOURCE_ISSUE,
        "consumer_issue": subject.CONSUMER_ISSUE,
        "receipt_issue": subject.RECEIPT_ISSUE,
        "receipt_result_comment_id": subject.RECEIPT_RESULT_COMMENT_ID,
        "dataset_id": subject.DATASET_ID,
        "project_id": subject.PROJECT_ID,
        "project_path": subject.PROJECT_PATH,
        "commit_sha": subject.COMMIT_SHA,
        "receipt_set_sha256": subject.RECEIPT_SET_SHA256,
        "source_model_paths": list(subject._FIXED_RECEIPTS),
        "profile_count": subject.EXPECTED_OBJECT_COUNT,
        "total_byte_count": subject.EXPECTED_TOTAL_BYTE_COUNT,
        "profiles": profiles,
        "provider_file_bytes_read": True,
        "raw_xml_returned": False,
        "source_model_content_profiled": True,
        "external_reference_scan_performed": False,
        "external_bytes_persisted": False,
        "transitive_dependency_byte_closure_verified": False,
        "runtime_compatibility_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def result_body(
    sha: str = EXECUTION_SHA,
    *,
    target_sha: str | None = None,
    publication_authorized: bool = False,
) -> str:
    result = {
        **subject._base_result(execution_sha=sha),
        "status": "pass",
        "failure_class": None,
        "profile_set": synthetic_profile_set(),
    }
    if target_sha is not None:
        result["target_sha"] = target_sha
    if publication_authorized:
        result["publication_authorized"] = True
    return subject.RESULT_MARKER + "\n" + json.dumps(
        result, sort_keys=True, separators=(",", ":")
    )


def _valid_result() -> dict:
    return json.loads(result_body().split("\n", 1)[1])


def _publisher_filter() -> str:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    start_marker = 'jq -e --arg sha "$EXECUTION_SHA" \'\n'
    start = workflow.index(start_marker) + len(start_marker)
    end = workflow.index("\n          ' >/dev/null", start)
    return workflow[start:end]


def _publisher_accepts(result: dict) -> bool:
    completed = subprocess.run(
        ["jq", "-e", "--arg", "sha", EXECUTION_SHA, _publisher_filter()],
        input=json.dumps(result, sort_keys=True, separators=(",", ":")),
        text=True,
        capture_output=True,
        check=False,
        timeout=5,
    )
    return completed.returncode == 0


class SourceModelChildProfileActionTests(unittest.TestCase):
    def test_fixed_contract_matches_exact_receipted_ten_object_set(self) -> None:
        subject._assert_fixed_contract()
        self.assertEqual(len(subject._FIXED_RECEIPTS), 10)
        self.assertEqual(
            sum(item[0] for item in subject._FIXED_RECEIPTS.values()),
            23_781_485,
        )
        self.assertEqual(
            subject._receipt_set_sha(subject._FIXED_RECEIPTS),
            "621d16b35166cb66c86079106f1a7fd717ff07ef155184c5eed5a028292e4eb8",
        )

    def test_raw_url_is_fixed_to_receipted_path_and_immutable_commit(self) -> None:
        path = next(iter(subject._FIXED_RECEIPTS))
        url = subject._raw_url(path)
        self.assertIn("/api/v4/projects/269/repository/files/", url)
        self.assertIn("ref=" + subject.COMMIT_SHA, url)
        with self.assertRaises(subject.SourceModelChildProfileActionError):
            subject._raw_url("Hazard/source_models/not-receipted.xml")

    def test_fetch_verifies_receipt_before_profiler_and_returns_no_xml(self) -> None:
        path = "Hazard/source_models/test.xml"
        payload = b"<nrml/>"
        identity = (len(payload), hashlib.sha256(payload).hexdigest())
        receipts = {path: identity}
        calls: list[tuple[str, bytes]] = []

        def profiler(observed_path: str, observed_payload: bytes) -> dict:
            calls.append((observed_path, observed_payload))
            return child_profile(
                observed_path,
                len(observed_payload),
                hashlib.sha256(observed_payload).hexdigest(),
            )

        profile = subject._fetch_verified_profile(
            path,
            identity,
            deadline=10.0,
            opener=OneShotOpener(payload),
            monotonic=lambda: 0.0,
            profiler=profiler,
            receipts=receipts,
        )
        self.assertEqual(calls, [(path, payload)])
        self.assertEqual(profile["sha256"], identity[1])
        self.assertNotIn("<nrml", json.dumps(profile))

    def test_receipt_mismatch_blocks_before_profiler(self) -> None:
        path = "Hazard/source_models/test.xml"
        payload = b"<nrml/>"
        identity = (len(payload), hashlib.sha256(b"different").hexdigest())
        called = False

        def profiler(observed_path: str, observed_payload: bytes) -> dict:
            nonlocal called
            called = True
            return child_profile(
                observed_path,
                len(observed_payload),
                hashlib.sha256(observed_payload).hexdigest(),
            )

        with self.assertRaises(subject.SourceModelChildProfileActionError):
            subject._fetch_verified_profile(
                path,
                identity,
                deadline=10.0,
                opener=OneShotOpener(payload),
                monotonic=lambda: 0.0,
                profiler=profiler,
                receipts={path: identity},
            )
        self.assertFalse(called)

    def test_request_is_exact_head_and_exposes_no_provider_selector(self) -> None:
        parsed = subject.validate_request(
            request_body(),
            expected_issue=subject.SOURCE_ISSUE,
            execution_sha=EXECUTION_SHA,
        )
        self.assertEqual(set(parsed), subject._REQUEST_FIELDS)
        for forbidden in ("path", "project_id", "url", "commit_sha", "operation"):
            self.assertNotIn(forbidden, parsed)
        with self.assertRaises(subject.SourceModelChildProfileActionError):
            subject.validate_request(
                request_body(OLD_SHA),
                expected_issue=subject.SOURCE_ISSUE,
                execution_sha=EXECUTION_SHA,
            )

    def test_profile_validator_rejects_authority_widening_and_bad_count_reconciliation(self) -> None:
        profile_set = synthetic_profile_set()
        subject.validate_profile_set(profile_set)

        widened = synthetic_profile_set()
        widened["profiles"][0]["model_use_authorized"] = True
        with self.assertRaises(subject.SourceModelChildProfileActionError):
            subject.validate_profile_set(widened)

        inconsistent = synthetic_profile_set()
        inconsistent["profiles"][0]["element_type_counts"]["nrml"] = 2
        with self.assertRaises(subject.SourceModelChildProfileActionError):
            subject.validate_profile_set(inconsistent)

    def test_historical_valid_result_is_validated_under_its_own_sha_then_not_deduped(self) -> None:
        comments = [
            {
                "user": {"login": subject.TRUSTED_RESULT_LOGIN},
                "body": result_body(OLD_SHA),
            }
        ]
        with mock.patch.object(subject, "_FETCH_COMMENTS", return_value=comments):
            self.assertFalse(
                subject.has_terminal_result(
                    repository="o/r",
                    token="x",
                    execution_sha=EXECUTION_SHA,
                )
            )

    def test_historical_authority_widening_fails_closed_even_on_other_sha(self) -> None:
        comments = [
            {
                "user": {"login": subject.TRUSTED_RESULT_LOGIN},
                "body": result_body(OLD_SHA, publication_authorized=True),
            }
        ]
        with mock.patch.object(subject, "_FETCH_COMMENTS", return_value=comments):
            with self.assertRaises(subject.SourceModelChildProfileActionError):
                subject.has_terminal_result(
                    repository="o/r",
                    token="x",
                    execution_sha=EXECUTION_SHA,
                )

    def test_internally_inconsistent_historical_sha_fails_closed(self) -> None:
        comments = [
            {
                "user": {"login": subject.TRUSTED_RESULT_LOGIN},
                "body": result_body(OLD_SHA, target_sha="3" * 40),
            }
        ]
        with mock.patch.object(subject, "_FETCH_COMMENTS", return_value=comments):
            with self.assertRaises(subject.SourceModelChildProfileActionError):
                subject.has_terminal_result(
                    repository="o/r",
                    token="x",
                    execution_sha=EXECUTION_SHA,
                )

    def test_blocked_result_is_atomic(self) -> None:
        result = {
            **subject._base_result(execution_sha=EXECUTION_SHA),
            "status": "blocked",
            "failure_class": "source_model_profile_failure",
            "profile_set": None,
        }
        body = subject.RESULT_MARKER + "\n" + json.dumps(
            result, sort_keys=True, separators=(",", ":")
        )
        self.assertTrue(subject.parse_terminal_result(body, execution_sha=EXECUTION_SHA))
        result["profile_set"] = synthetic_profile_set()
        body = subject.RESULT_MARKER + "\n" + json.dumps(
            result, sort_keys=True, separators=(",", ":")
        )
        with self.assertRaises(subject.SourceModelChildProfileActionError):
            subject.parse_terminal_result(body, execution_sha=EXECUTION_SHA)

    @unittest.skipUnless(shutil.which("jq"), "jq is required for publisher mutation tests")
    def test_no_checkout_publisher_rejects_dynamic_payload_mutations(self) -> None:
        valid = _valid_result()
        self.assertTrue(_publisher_accepts(valid))

        blocked = {
            **subject._base_result(execution_sha=EXECUTION_SHA),
            "status": "blocked",
            "failure_class": "source_model_profile_failure",
            "profile_set": None,
        }
        self.assertTrue(_publisher_accepts(blocked))

        mutations: list[tuple[str, dict]] = []

        mutated = json.loads(json.dumps(valid))
        mutated["unexpected_result_field"] = "forbidden"
        mutations.append(("unknown result key", mutated))

        mutated = json.loads(json.dumps(valid))
        mutated["profile_set"]["unexpected_profile_set_field"] = "forbidden"
        mutations.append(("unknown profile-set key", mutated))

        mutated = json.loads(json.dumps(valid))
        mutated["profile_set"]["dataset_id"] = "attacker.dataset"
        mutations.append(("profile-set dataset identity", mutated))

        mutated = json.loads(json.dumps(valid))
        mutated["profile_set"]["profiles"][0]["unexpected_child_field"] = "forbidden"
        mutations.append(("unknown child key", mutated))

        mutated = json.loads(json.dumps(valid))
        mutated["profile_set"]["profiles"][0]["sha256"] = "0" * 64
        mutations.append(("child SHA-256", mutated))

        mutated = json.loads(json.dumps(valid))
        mutated["profile_set"]["profiles"][0]["byte_count"] += 1
        mutations.append(("child byte count", mutated))

        mutated = json.loads(json.dumps(valid))
        mutated["profile_set"]["profiles"][0]["root_element"] = ""
        mutations.append(("child root element", mutated))

        mutated = json.loads(json.dumps(valid))
        mutated["profile_set"]["profiles"][0]["element_count"] += 1
        mutations.append(("child element count", mutated))

        mutated = json.loads(json.dumps(valid))
        mutated["profile_set"]["profiles"][0]["element_type_counts"]["nrml"] += 1
        mutations.append(("child element-type reconciliation", mutated))

        for label, mutation in mutations:
            with self.subTest(label=label):
                self.assertFalse(_publisher_accepts(mutation))

    def test_workflow_is_trusted_main_only_and_publishes_bounded_evidence(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        header, jobs = workflow.split("\njobs:\n", 1)
        self.assertTrue(jobs)
        self.assertIn("concurrency:", header)
        self.assertIn("github.event.issue.number == 281", header)
        self.assertIn(
            "github.event.comment.user.login == github.event.repository.owner.login",
            header,
        )
        self.assertIn("github.event.comment.author_association == 'OWNER'", header)
        self.assertIn(subject.REQUEST_MARKER, header)
        self.assertIn("'trusted-request'", header)
        self.assertIn("github.event.repository.default_branch", jobs)
        self.assertNotIn("github.event.pull_request", workflow)
        self.assertIn("persist-credentials: false", jobs)
        self.assertIn(
            "printf '%s\\n%s' '<!-- oc-eq1-esrm20-source-model-child-profiles-result-v2 -->' \"$RESULT_JSON\" | wc -c",
            jobs,
        )
        self.assertIn("test \"$(printf '%s' \"$BODY\" | wc -c)\" -le 64000", jobs)
        self.assertIn(subject.RECEIPT_SET_SHA256, jobs)
        self.assertIn(".publication_authorized == false", jobs)
        self.assertIn(".model_use_authorized == false", jobs)


if __name__ == "__main__":
    unittest.main()
