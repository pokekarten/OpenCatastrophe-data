# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Regression tests for acquisition target/execution semantic binding."""

from __future__ import annotations

import unittest

from scripts.agent_action_protocol import ProtocolError, semantic_request_id
from scripts.prepare_agent_action_result import prepare_completed_result

REPOSITORY = "pokekarten/OpenCatastrophe-data"
EXECUTION_SHA = "b" * 40
DATASET_ID = "dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03"
ACQUISITION_REQUEST = {
    "schema_version": "oc-action-request-v1",
    "action": "acquisition_receipt",
    "issue": 162,
    "target_sha": EXECUTION_SHA,
    "dataset_id": DATASET_ID,
    "requester": "slot-target-binding-a",
}


class AcquisitionTargetBindingTests(unittest.TestCase):
    def test_acquisition_requires_target_to_equal_trusted_execution(self) -> None:
        semantic_id = semantic_request_id(ACQUISITION_REQUEST, EXECUTION_SHA, REPOSITORY)
        self.assertEqual(len(semantic_id), 64)

        mismatched = dict(ACQUISITION_REQUEST, target_sha="c" * 40)
        with self.assertRaisesRegex(
            ProtocolError,
            "target_sha must equal trusted execution_sha",
        ):
            semantic_request_id(mismatched, EXECUTION_SHA, REPOSITORY)

    def test_mismatched_acquisition_never_reaches_acquirer(self) -> None:
        calls: list[str] = []

        def acquirer():
            calls.append("called")
            self.fail("mismatched acquisition must not execute provider worker")

        mismatched = dict(ACQUISITION_REQUEST, target_sha="c" * 40)
        with self.assertRaisesRegex(
            ProtocolError,
            "target_sha must equal trusted execution_sha",
        ):
            prepare_completed_result(
                mismatched,
                [],
                repository=REPOSITORY,
                execution_sha=EXECUTION_SHA,
                source_comment_id=101,
                run_id=201,
                run_attempt=1,
                started_at="2026-08-11T08:00:00Z",
                acquirer=acquirer,
            )
        self.assertEqual(calls, [])

    def test_transport_only_requester_change_keeps_acquisition_identity(self) -> None:
        first = semantic_request_id(ACQUISITION_REQUEST, EXECUTION_SHA, REPOSITORY)
        second = semantic_request_id(
            dict(ACQUISITION_REQUEST, requester="slot-target-binding-b"),
            EXECUTION_SHA,
            REPOSITORY,
        )
        self.assertEqual(first, second)

    def test_sample_audit_keeps_independent_target_semantics(self) -> None:
        request = dict(
            ACQUISITION_REQUEST,
            action="sample_audit",
            target_sha="a" * 40,
        )
        semantic_id = semantic_request_id(request, EXECUTION_SHA, REPOSITORY)
        self.assertEqual(len(semantic_id), 64)


if __name__ == "__main__":
    unittest.main()
