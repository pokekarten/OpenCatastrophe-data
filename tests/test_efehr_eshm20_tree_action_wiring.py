# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts.acquire_efehr_eshm20_tree_metadata import (
    BRANCH,
    DATASET_ID,
    MAX_TOTAL_METADATA_BYTES,
    MAX_TREE_ENTRIES,
    MAX_TREE_PAGES,
    OPERATION_ID,
    PROJECT_ID,
    PROJECT_PATH,
    SCHEMA_VERSION,
    SOURCE_ISSUE,
    TREE_PREFIX,
)
from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError
from scripts.agent_action_protocol import (
    ProtocolError,
    canonical_result_comment,
    semantic_request_id,
)
from scripts.efehr_gitlab_receipt import PROVIDER_HOST
from scripts.prepare_agent_action_result import (
    build_acquisition_result,
    prepare_completed_result,
)
from scripts.validate_agent_action_request import RequestError, validate_request
from scripts.validate_agent_action_result import ResultError, validate_result

REPOSITORY = "pokekarten/OpenCatastrophe-data"
EXECUTION_SHA = "c" * 40
PROVIDER_COMMIT = "a" * 40
STARTED = "2026-08-13T11:00:00Z"
FINISHED = "2026-08-13T11:00:02Z"

REQUEST = {
    "schema_version": "oc-action-request-v1",
    "action": "efehr_eshm20_tree_metadata",
    "issue": 332,
    "target_sha": EXECUTION_SHA,
    "dataset_id": DATASET_ID,
    "requester": "slot24-eshm20-tree",
}

ENTRIES = [
    {
        "path": TREE_PREFIX + "a.xml",
        "type": "blob",
        "id": "1" * 40,
        "mode": "100644",
    },
    {
        "path": TREE_PREFIX + "nested",
        "type": "tree",
        "id": "2" * 40,
        "mode": "040000",
    },
]

RECEIPT = {
    "schema_version": SCHEMA_VERSION,
    "operation_id": OPERATION_ID,
    "source_issue": SOURCE_ISSUE,
    "dataset_id": DATASET_ID,
    "provider_host": PROVIDER_HOST,
    "project_id": PROJECT_ID,
    "project_path": PROJECT_PATH,
    "branch": BRANCH,
    "resolved_commit_sha": PROVIDER_COMMIT,
    "tree_prefix": TREE_PREFIX,
    "retrieved_at": "2026-08-13T11:00:01Z",
    "tree_page_count": 1,
    "tree_entry_count": len(ENTRIES),
    "metadata_byte_count": 2048,
    "entries": ENTRIES,
    "external_bytes_persisted": False,
    "publication_authorized": False,
}


def acquisition_result(receipt=RECEIPT):
    return build_acquisition_result(
        REQUEST,
        repository=REPOSITORY,
        execution_sha=EXECUTION_SHA,
        source_comment_id=100,
        run_id=200,
        run_attempt=1,
        started_at=STARTED,
        finished_at=FINISHED,
        receipt=receipt,
    )


class EfehrEshm20TreeActionWiringTests(unittest.TestCase):
    def test_request_accepts_only_closed_issue_and_dataset(self) -> None:
        self.assertEqual(validate_request(dict(REQUEST), expected_issue=332), REQUEST)
        with self.assertRaisesRegex(RequestError, "restricted to issue 332"):
            validate_request(dict(REQUEST, issue=320))
        with self.assertRaisesRegex(RequestError, "frozen ESHM20 dataset"):
            validate_request(dict(REQUEST, dataset_id="efehr.other"))

    def test_request_rejects_every_caller_controlled_provider_target(self) -> None:
        for field, value in (
            ("host", "example.invalid"),
            ("project_id", 186),
            ("ref", PROVIDER_COMMIT),
            ("prefix", "other/"),
            ("url", "https://example.invalid/tree"),
            ("parser", "generic"),
        ):
            with self.subTest(field=field):
                with self.assertRaisesRegex(RequestError, "unexpected"):
                    validate_request(dict(REQUEST, **{field: value}))

    def test_network_identity_requires_trusted_execution_head(self) -> None:
        semantic_request_id(REQUEST, EXECUTION_SHA, REPOSITORY)
        with self.assertRaisesRegex(
            ProtocolError, "target_sha must equal trusted execution_sha"
        ):
            semantic_request_id(REQUEST, "d" * 40, REPOSITORY)

    def test_dispatch_and_result_bind_only_metadata_receipt(self) -> None:
        calls = []

        def worker():
            calls.append("called")
            return dict(RECEIPT, entries=[dict(item) for item in ENTRIES])

        result = prepare_completed_result(
            REQUEST,
            [],
            repository=REPOSITORY,
            execution_sha=EXECUTION_SHA,
            source_comment_id=100,
            run_id=200,
            run_attempt=1,
            started_at=STARTED,
            eshm20_tree_acquirer=worker,
        )
        self.assertEqual(calls, ["called"])
        self.assertEqual(result["action"], "efehr_eshm20_tree_metadata")
        self.assertEqual(result["source_issue"], 332)
        self.assertEqual(result["phase"], "acquisition_receipt")
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["evidence"]["efehr_eshm20_tree_metadata"], RECEIPT)
        self.assertFalse(result["external_bytes_persisted"])

    def test_receipt_rejects_identity_target_and_authority_drift(self) -> None:
        for field, value in (
            ("source_issue", 332),
            ("dataset_id", "efehr.other"),
            ("provider_host", "example.invalid"),
            ("project_id", 186),
            ("project_path", "efehr/other"),
            ("branch", "main"),
            ("resolved_commit_sha", "A" * 40),
            ("tree_prefix", "other/"),
            ("external_bytes_persisted", True),
            ("publication_authorized", True),
        ):
            with self.subTest(field=field):
                with self.assertRaises(ResultError):
                    acquisition_result(dict(RECEIPT, **{field: value}))

    def test_receipt_rejects_entry_and_bound_drift(self) -> None:
        mutations = [
            dict(RECEIPT, tree_page_count=MAX_TREE_PAGES + 1),
            dict(RECEIPT, tree_entry_count=MAX_TREE_ENTRIES + 1),
            dict(RECEIPT, metadata_byte_count=MAX_TOTAL_METADATA_BYTES + 1),
            dict(RECEIPT, tree_entry_count=1),
            dict(RECEIPT, entries=list(reversed(ENTRIES))),
            dict(RECEIPT, entries=[dict(ENTRIES[0], path="other/a.xml"), ENTRIES[1]]),
            dict(RECEIPT, entries=[dict(ENTRIES[0], id="bad"), ENTRIES[1]]),
            dict(RECEIPT, entries=[dict(ENTRIES[0], mode="10064"), ENTRIES[1]]),
            dict(RECEIPT, entries=[dict(ENTRIES[0], content="provider bytes"), ENTRIES[1]]),
        ]
        for index, mutated in enumerate(mutations):
            with self.subTest(index=index):
                with self.assertRaises(ResultError):
                    acquisition_result(mutated)

    def test_blocked_and_duplicate_paths_never_expose_or_repeat_provider_work(self) -> None:
        def blocked_worker():
            raise EfehrAcquisitionError("synthetic provider failure")

        blocked = prepare_completed_result(
            REQUEST,
            [],
            repository=REPOSITORY,
            execution_sha=EXECUTION_SHA,
            source_comment_id=101,
            run_id=201,
            run_attempt=1,
            started_at=STARTED,
            eshm20_tree_acquirer=blocked_worker,
        )
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(blocked["failure_class"], "acquisition_failed")
        self.assertIsNone(blocked["evidence"]["efehr_eshm20_tree_metadata"])

        prior = acquisition_result()
        duplicate = prepare_completed_result(
            REQUEST,
            [{
                "id": 999,
                "body": canonical_result_comment(prior),
                "user": {"login": "github-actions[bot]"},
            }],
            repository=REPOSITORY,
            execution_sha=EXECUTION_SHA,
            source_comment_id=102,
            run_id=202,
            run_attempt=1,
            started_at=STARTED,
            eshm20_tree_acquirer=lambda: self.fail(
                "deduplicated action must not call EFEHR"
            ),
        )
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(duplicate["duplicate_result_comment_id"], 999)

    def test_outer_result_rejects_issue_or_dataset_drift(self) -> None:
        result = acquisition_result()
        for field, value in (("source_issue", 320), ("dataset_id", "efehr.other")):
            with self.subTest(field=field):
                with self.assertRaises(ResultError):
                    validate_result(dict(result, **{field: value}))


if __name__ == "__main__":
    unittest.main()
