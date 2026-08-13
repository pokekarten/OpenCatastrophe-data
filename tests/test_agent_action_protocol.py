# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import urllib.parse
import unittest
from pathlib import Path

from scripts.acquire_dwd_extreme_wind_receipt import AcquisitionError
from scripts.agent_action_protocol import RESULT_MARKER, canonical_result_comment, semantic_request_id
from scripts.post_agent_action_result import PostError, post_result
from scripts.prepare_agent_action_result import (
    PER_PAGE,
    LedgerError,
    build_acquisition_result,
    build_result,
    fetch_repository_comments,
    find_existing_result,
    prepare_completed_result,
)
from scripts.validate_agent_action_result import ResultError, validate_result

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/agent-action-dispatch.yml"
SCHEMA = ROOT / "schemas/agent-action-result-v1.schema.json"
REPOSITORY = "pokekarten/OpenCatastrophe-data"
STARTED = "2026-08-11T08:00:00Z"
FINISHED = "2026-08-11T08:00:02Z"

REQUEST = {
    "schema_version": "oc-action-request-v1",
    "action": "sample_audit",
    "issue": 162,
    "target_sha": "a" * 40,
    "dataset_id": "dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03",
    "requester": "slot36-run-a",
}
ACQUISITION_REQUEST = dict(REQUEST, action="acquisition_receipt", target_sha="b" * 40)
EXECUTION_SHA = "b" * 40

ACQUISITION_RECEIPT = {
    "schema_version": "oc-acquisition-receipt-v1",
    "dataset_id": "dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03",
    "source_issue": 162,
    "requested_url": (
        "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/"
        "10_minutes/extreme_wind/historical/"
        "10minutenwerte_extrema_wind_00003_20100101_20110331_hist.zip"
    ),
    "final_url": (
        "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/"
        "10_minutes/extreme_wind/historical/"
        "10minutenwerte_extrema_wind_00003_20100101_20110331_hist.zip"
    ),
    "filename": "10minutenwerte_extrema_wind_00003_20100101_20110331_hist.zip",
    "retrieved_at": "2026-08-11T08:00:01Z",
    "byte_count": 488338,
    "sha256": "c" * 64,
    "content_type": "application/zip",
    "last_modified": "Tue, 30 Nov 2021 10:59:16 GMT",
    "etag": None,
    "archive_member_count": 2,
    "archive_uncompressed_bytes": 1000000,
    "product_member": "produkt_extrema_wind_20100101_20110331_00003.txt",
    "product_station_id": "00003",
    "product_begin_date": "20100101",
    "product_end_date": "20110331",
    "product_row_count": 65000,
    "product_structure_validated": True,
    "external_bytes_persisted": False,
    "publication_authorized": False,
}


class FakeResponse:
    def __init__(self, payload: object) -> None:
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def read(self) -> bytes:
        return self.payload


def result_for(request=REQUEST, **kwargs):
    parameters = {
        "repository": REPOSITORY,
        "execution_sha": EXECUTION_SHA,
        "source_comment_id": 100,
        "run_id": 200,
        "run_attempt": 1,
        "started_at": STARTED,
        "finished_at": FINISHED,
    }
    parameters.update(kwargs)
    return build_result(request, **parameters)


def acquisition_result_for(receipt=ACQUISITION_RECEIPT, **kwargs):
    parameters = {
        "repository": REPOSITORY,
        "execution_sha": EXECUTION_SHA,
        "source_comment_id": 100,
        "run_id": 200,
        "run_attempt": 1,
        "started_at": STARTED,
        "finished_at": FINISHED,
        "receipt": receipt,
    }
    parameters.update(kwargs)
    return build_acquisition_result(ACQUISITION_REQUEST, **parameters)


class AgentActionProtocolTests(unittest.TestCase):
    def test_semantic_identity_ignores_transport_only_fields(self) -> None:
        first = semantic_request_id(REQUEST, EXECUTION_SHA, REPOSITORY)
        changed = dict(REQUEST, issue=165, requester="slot12-run-b")
        self.assertEqual(first, semantic_request_id(changed, EXECUTION_SHA, REPOSITORY))

    def test_semantic_identity_changes_with_execution_code_or_repository(self) -> None:
        baseline = semantic_request_id(REQUEST, EXECUTION_SHA, REPOSITORY)
        self.assertNotEqual(baseline, semantic_request_id(REQUEST, "c" * 40, REPOSITORY))
        self.assertNotEqual(
            baseline,
            semantic_request_id(REQUEST, EXECUTION_SHA, "pokekarten/OtherRepo"),
        )

    def test_pass_duplicate_and_blocked_results_are_closed(self) -> None:
        passed = result_for()
        self.assertEqual(passed["status"], "pass")
        self.assertFalse(passed["external_bytes_persisted"])
        self.assertEqual(
            passed["evidence"],
            {"request_validated": True, "ledger_scan_complete": True, "prior_result_reused": False},
        )

        duplicate = result_for(source_comment_id=101, run_id=201, duplicate_result_comment_id=99)
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(duplicate["failure_class"], "duplicate_request")
        self.assertTrue(duplicate["evidence"]["prior_result_reused"])

        blocked = result_for(source_comment_id=102, run_id=202, ledger_incomplete=True)
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(blocked["failure_class"], "ledger_incomplete")
        self.assertFalse(blocked["evidence"]["ledger_scan_complete"])

    def test_acquisition_result_binds_closed_metadata_receipt(self) -> None:
        result = acquisition_result_for()
        self.assertEqual(result["action"], "acquisition_receipt")
        self.assertEqual(result["phase"], "acquisition_receipt")
        self.assertEqual(result["status"], "pass")
        self.assertFalse(result["external_bytes_persisted"])
        self.assertEqual(result["evidence"]["acquisition_receipt"], ACQUISITION_RECEIPT)

        blocked = acquisition_result_for(receipt=None)
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(blocked["failure_class"], "acquisition_failed")
        self.assertIsNone(blocked["evidence"]["acquisition_receipt"])

    def test_acquisition_result_rejects_receipt_identity_drift_and_payload_controls(self) -> None:
        for field, value in (
            ("dataset_id", "other.dataset"),
            ("source_issue", 163),
            ("final_url", "https://example.invalid/data.zip"),
            ("external_bytes_persisted", True),
            ("publication_authorized", True),
            ("product_station_id", "99999"),
        ):
            with self.subTest(field=field):
                mutated_receipt = dict(ACQUISITION_RECEIPT)
                mutated_receipt[field] = value
                with self.assertRaises(ResultError):
                    acquisition_result_for(receipt=mutated_receipt)

        mutated_receipt = dict(ACQUISITION_RECEIPT, etag="ok\nforged")
        with self.assertRaisesRegex(ResultError, "control characters"):
            acquisition_result_for(receipt=mutated_receipt)

    def test_acquisition_receipt_timestamp_must_be_inside_action_bounds(self) -> None:
        mutated_receipt = dict(ACQUISITION_RECEIPT, retrieved_at="2026-08-11T08:00:03Z")
        with self.assertRaisesRegex(ResultError, "start/finish"):
            acquisition_result_for(receipt=mutated_receipt)

    def test_prepare_executes_acquisition_only_after_dedup_and_never_on_duplicate(self) -> None:
        calls = []

        def acquirer():
            calls.append("called")
            return dict(ACQUISITION_RECEIPT)

        result = prepare_completed_result(
            ACQUISITION_REQUEST,
            [],
            repository=REPOSITORY,
            execution_sha=EXECUTION_SHA,
            source_comment_id=100,
            run_id=200,
            run_attempt=1,
            started_at=STARTED,
            acquirer=acquirer,
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(calls, ["called"])

        prior = acquisition_result_for()
        comments = [
            {
                "id": 999,
                "body": canonical_result_comment(prior),
                "user": {"login": "github-actions[bot]"},
            }
        ]
        duplicate = prepare_completed_result(
            ACQUISITION_REQUEST,
            comments,
            repository=REPOSITORY,
            execution_sha=EXECUTION_SHA,
            source_comment_id=101,
            run_id=201,
            run_attempt=1,
            started_at=STARTED,
            acquirer=lambda: self.fail("duplicate acquisition must not execute worker"),
        )
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(duplicate["duplicate_result_comment_id"], 999)
        self.assertEqual(duplicate["phase"], "request_validation")

    def test_blocked_acquisition_is_completed_for_same_semantic_identity(self) -> None:
        blocked = acquisition_result_for(receipt=None)
        comments = [
            {
                "id": 998,
                "body": canonical_result_comment(blocked),
                "user": {"login": "github-actions[bot]"},
            }
        ]
        self.assertEqual(find_existing_result(comments, blocked["semantic_request_id"]), 998)

    def test_result_validator_rejects_bool_as_integer_and_external_bytes(self) -> None:
        result = result_for()
        for field in ("source_issue", "source_comment_id", "run_id", "run_attempt"):
            with self.subTest(field=field):
                mutated = dict(result)
                mutated[field] = True
                with self.assertRaises(ResultError):
                    validate_result(mutated)
        mutated = dict(result)
        mutated["external_bytes_persisted"] = True
        with self.assertRaises(ResultError):
            validate_result(mutated)

    def test_result_validator_recomputes_semantic_binding(self) -> None:
        result = result_for()
        for field, value in (
            ("semantic_request_id", "0" * 64),
            ("dataset_id", "other.dataset"),
            ("target_sha", "c" * 40),
            ("execution_sha", "d" * 40),
            ("repository", "pokekarten/OtherRepo"),
        ):
            with self.subTest(field=field):
                mutated = dict(result)
                mutated[field] = value
                with self.assertRaisesRegex(ResultError, "semantic_request_id"):
                    validate_result(mutated)

    def test_result_validator_rejects_time_reversal_and_evidence_drift(self) -> None:
        result = result_for()
        reversed_time = dict(result, started_at=FINISHED, finished_at=STARTED)
        with self.assertRaisesRegex(ResultError, "must not precede"):
            validate_result(reversed_time)

        wrong_state = dict(result)
        wrong_state["evidence"] = dict(result["evidence"], prior_result_reused=True)
        with self.assertRaisesRegex(ResultError, "pass result requires"):
            validate_result(wrong_state)

        type_confused = dict(result)
        type_confused["evidence"] = dict(result["evidence"], ledger_scan_complete=1)
        with self.assertRaisesRegex(ResultError, "must be boolean"):
            validate_result(type_confused)

    def test_cross_thread_dedup_accepts_only_actions_bot_results(self) -> None:
        result = result_for()
        semantic_id = result["semantic_request_id"]
        comments = [
            {"id": 9, "body": canonical_result_comment(result), "user": {"login": "untrusted-user"}},
            {"id": 10, "body": canonical_result_comment(result), "user": {"login": "pokekarten"}},
            {"id": 11, "body": canonical_result_comment(result), "user": {"login": "github-actions[bot]"}},
        ]
        self.assertEqual(find_existing_result(comments, semantic_id), 11)

    def test_owner_authored_result_cannot_satisfy_execution_ledger(self) -> None:
        result = result_for()
        self.assertIsNone(
            find_existing_result(
                [{"id": 10, "body": canonical_result_comment(result), "user": {"login": "pokekarten"}}],
                result["semantic_request_id"],
            )
        )

    def test_semantically_forged_trusted_result_fails_closed(self) -> None:
        result = result_for()
        forged = dict(result, dataset_id="other.dataset")
        comments = [{"id": 11, "body": canonical_result_comment(forged), "user": {"login": "github-actions[bot]"}}]
        with self.assertRaisesRegex(LedgerError, "fails result validation"):
            find_existing_result(comments, result["semantic_request_id"])

    def test_malformed_trusted_result_fails_closed_but_nonbot_lookalike_is_ignored(self) -> None:
        malformed = RESULT_MARKER + "\n{not-json}"
        for login in ("untrusted-user", "pokekarten"):
            with self.subTest(login=login):
                self.assertIsNone(
                    find_existing_result(
                        [{"id": 10, "body": malformed, "user": {"login": login}}],
                        "a" * 64,
                    )
                )
        with self.assertRaises(LedgerError):
            find_existing_result(
                [{"id": 11, "body": malformed, "user": {"login": "github-actions[bot]"}}],
                "a" * 64,
            )

    def test_repository_comment_ledger_reads_until_short_page(self) -> None:
        calls = []

        def opener(request, timeout):
            page = int(urllib.parse.parse_qs(urllib.parse.urlsplit(request.full_url).query)["page"][0])
            calls.append(page)
            if page == 1:
                return FakeResponse([{"id": index} for index in range(PER_PAGE)])
            return FakeResponse([{"id": PER_PAGE + 1}])

        comments = fetch_repository_comments(REPOSITORY, "token", opener=opener, max_pages=3)
        self.assertEqual(calls, [1, 2])
        self.assertEqual(len(comments), PER_PAGE + 1)

    def test_repository_comment_ledger_fails_closed_at_completeness_bound(self) -> None:
        def opener(request, timeout):
            return FakeResponse([{"id": index} for index in range(PER_PAGE)])

        with self.assertRaisesRegex(LedgerError, "exceeds the fail-closed scan bound"):
            fetch_repository_comments(REPOSITORY, "token", opener=opener, max_pages=1)

    def test_result_schema_matches_closed_observability_and_acquisition_boundary(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["external_bytes_persisted"], {"const": False})
        self.assertEqual(
            set(schema["properties"]["phase"]["enum"]),
            {"request_validation", "acquisition_receipt"},
        )
        self.assertEqual(
            set(schema["properties"]["action"]["enum"]),
            {"sample_audit", "acquisition_receipt", "dwd_metadata_receipt", "efehr_readme_receipt"},
        )
        self.assertEqual(set(schema["properties"]["status"]["enum"]), {"pass", "duplicate", "blocked"})
        for field in ("repository", "started_at", "finished_at", "evidence"):
            self.assertIn(field, schema["required"])
        self.assertIn("acquisitionReceipt", schema["$defs"])
        self.assertIn("dwdMetadataReceipt", schema["$defs"])
        self.assertIn("efehrReadmeReceipt", schema["$defs"])
        receipt_schema = schema["$defs"]["acquisitionReceipt"]
        self.assertFalse(receipt_schema["additionalProperties"])
        self.assertEqual(receipt_schema["properties"]["source_issue"], {"const": 162})
        self.assertEqual(receipt_schema["properties"]["external_bytes_persisted"], {"const": False})
        self.assertEqual(receipt_schema["properties"]["publication_authorized"], {"const": False})
        metadata_schema = schema["$defs"]["dwdMetadataReceipt"]
        self.assertFalse(metadata_schema["additionalProperties"])
        self.assertEqual(metadata_schema["properties"]["source_issue"], {"const": 211})
        self.assertEqual(metadata_schema["properties"]["temporal_coverage_status"], {"const": "unverified"})
        self.assertEqual(metadata_schema["properties"]["external_bytes_persisted"], {"const": False})
        self.assertEqual(metadata_schema["properties"]["publication_authorized"], {"const": False})
        efehr_schema = schema["$defs"]["efehrReadmeReceipt"]
        self.assertFalse(efehr_schema["additionalProperties"])
        self.assertEqual(efehr_schema["properties"]["source_issue"], {"const": 282})
        self.assertEqual(efehr_schema["properties"]["project_id"], {"const": 186})
        self.assertEqual(
            efehr_schema["properties"]["repository_path"],
            {"const": "_exposure_models/ReadMe_Exposure_Model_Format.txt"},
        )
        self.assertEqual(efehr_schema["properties"]["external_bytes_persisted"], {"const": False})
        self.assertEqual(efehr_schema["properties"]["publication_authorized"], {"const": False})
        self.assertIn("scripts/validate_agent_action_result.py", schema["description"])

    def test_poster_revalidates_receipt_repository_and_posts_only_canonical_body(self) -> None:
        result = result_for()
        seen = {}

        def opener(request, timeout):
            seen["url"] = request.full_url
            seen["body"] = json.loads(request.data.decode("utf-8"))
            seen["authorization"] = request.headers.get("Authorization")
            return FakeResponse({"id": 321})

        comment_id = post_result(
            result,
            repository=REPOSITORY,
            expected_issue=162,
            token="test-token",
            opener=opener,
        )
        self.assertEqual(comment_id, 321)
        self.assertEqual(seen["url"], f"https://api.github.com/repos/{REPOSITORY}/issues/162/comments")
        self.assertEqual(seen["body"], {"body": canonical_result_comment(result)})
        self.assertEqual(seen["authorization"], "Bearer test-token")

        with self.assertRaisesRegex(PostError, "repository does not match"):
            post_result(
                result,
                repository="pokekarten/OtherRepo",
                expected_issue=162,
                token="test-token",
                opener=opener,
            )

    def test_workflow_isolates_untrusted_comments_queues_authorized_slots_and_uses_minimal_permissions(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("'authorized-v1' || github.event.comment.id", workflow)
        self.assertIn("github.event.comment.user.login == github.event.repository.owner.login", workflow)
        self.assertIn("github.event.comment.author_association == 'OWNER'", workflow)
        self.assertIn("contains(github.event.comment.body, '<!-- oc-action-request-v1 -->')", workflow)
        self.assertIn("queue: max", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertNotIn("group: agent-action-dispatch-v1\n", workflow)
        self.assertIn("name: Validate and classify authorized action request", workflow)
        self.assertEqual(workflow.count("issues: read"), 1)
        self.assertIn("name: Publish validated action result", workflow)
        self.assertEqual(workflow.count("issues: write"), 1)
        self.assertNotIn("pull-requests:", workflow)
        self.assertNotIn("OC_ACTION_OWNER_LOGIN", workflow)
        self.assertNotIn("--owner-login", workflow)
        self.assertIn("execution_sha: ${{ steps.prepare-result.outputs.execution_sha }}", workflow)
        self.assertIn("ref: ${{ needs.validate-request.outputs.execution_sha }}", workflow)
        self.assertIn("python scripts/post_agent_action_result.py", workflow)
        self.assertIn("repository-owned frozen DWD worker", workflow)
        self.assertNotIn("run_command", workflow)
        self.assertNotIn("curl ", workflow)
        self.assertNotIn("github.event.pull_request.head", workflow)
        self.assertNotIn(RESULT_MARKER, "<!-- oc-action-request-v1 -->")


if __name__ == "__main__":
    unittest.main()
