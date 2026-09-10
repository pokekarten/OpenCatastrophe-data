# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
from pathlib import Path
import unittest
from unittest import mock

from scripts import acquire_cems_europe_mask_receipts as mask_receipts
from scripts import acquire_cems_europe_rp10_receipt as rp10_receipt
from scripts import acquire_cems_spurious_support_challenge as worker
from scripts import agent_action_protocol_cems_spurious_support as protocol
from scripts import prepare_agent_action_result_cems_spurious_support as prepare
from scripts import profile_cems_europe_mask_geotiffs as mask_metadata
from scripts import profile_cems_europe_rp10_geotiff as rp10_profile
from scripts import validate_agent_action_request_cems_spurious_support as request_validator
from scripts import validate_agent_action_result_cems_spurious_support as result_validator

MAIN_SHA = "a" * 40
REPOSITORY = "pokekarten/OpenCatastrophe-data"
STARTED_AT = "2026-09-10T20:10:00Z"
RETRIEVED_AT = "2026-09-10T20:11:00Z"
FINISHED_AT = "2026-09-10T20:12:00Z"


def _request(**overrides):
    value = {
        "schema_version": request_validator.SCHEMA_VERSION,
        "action": request_validator.CEMS_SPURIOUS_SUPPORT_ACTION,
        "issue": 823,
        "target_sha": MAIN_SHA,
        "dataset_id": request_validator.CEMS_SPURIOUS_SUPPORT_DATASET_ID,
        "requester": "pokekarten",
    }
    value.update(overrides)
    return value


def _rp10_receipt() -> dict:
    return {
        "schema_version": rp10_receipt.SCHEMA_VERSION,
        "dataset_id": rp10_receipt.DATASET_ID,
        "source_issue": rp10_receipt.SOURCE_ISSUE,
        "release": rp10_receipt.RELEASE,
        "release_date": rp10_receipt.RELEASE_DATE,
        "doi": rp10_receipt.DOI,
        "return_period_years": rp10_receipt.RETURN_PERIOD_YEARS,
        "filename": rp10_receipt.FILENAME,
        "requested_url": rp10_receipt.SOURCE_URL,
        "final_url": rp10_receipt.SOURCE_URL,
        "retrieved_at": RETRIEVED_AT,
        "http_status": 200,
        "media_type": "image/tiff",
        "content_length_header": rp10_profile.ACCEPTED_BYTE_COUNT,
        "byte_count": rp10_profile.ACCEPTED_BYTE_COUNT,
        "sha256": rp10_profile.ACCEPTED_SHA256,
        "external_bytes_persisted": False,
        "geotiff_semantics_verified": False,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _spurious_receipt() -> dict:
    accepted = mask_metadata.MASK_RECEIPTS[worker.SPURIOUS_KIND]
    url = mask_receipts.BASE_URL + worker.SPURIOUS_FILENAME
    return {
        "schema_version": mask_receipts.RECEIPT_SCHEMA_VERSION,
        "dataset_id": mask_receipts.DATASET_ID,
        "source_issue": mask_receipts.SOURCE_ISSUE,
        "release": mask_receipts.RELEASE,
        "release_date": mask_receipts.RELEASE_DATE,
        "doi": mask_receipts.DOI,
        "mask_kind": worker.SPURIOUS_KIND,
        "filename": worker.SPURIOUS_FILENAME,
        "requested_url": url,
        "final_url": url,
        "retrieved_at": RETRIEVED_AT,
        "http_status": 200,
        "media_type": "image/tiff",
        "content_length_header": accepted["byte_count"],
        "byte_count": accepted["byte_count"],
        "sha256": accepted["sha256"],
        "external_bytes_persisted": False,
        "geotiff_semantics_verified": False,
        "mask_values_inspected": False,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _challenge(*, farther: int) -> dict:
    candidate = worker.EXPECTED_CANDIDATE_SUPPORT_CELLS
    within = candidate - farther
    return {
        "schema_version": result_validator._challenge.SCHEMA_VERSION,
        "candidate_support_rule": "finite_value_exactly_1",
        "rp10_seed_rule": "finite_depth_strictly_gt_10_m",
        "candidate_support_cells": candidate,
        "rp10_seed_cells": 100,
        "same_cell_candidate_seed_overlap_cells": 0,
        "candidate_with_seed_within_threshold_cells": within,
        "candidate_farther_than_threshold_cells": farther,
        "verdict": (
            "NOT_FALSIFIED_BY_CURRENT_RP10_NECESSARY_CONDITION"
            if farther == 0
            else "CURRENT_RP10_NECESSARY_CONDITION_FAIL"
        ),
        "distance_model": "WGS84_GEOD",
        "base_distance_metres": 2000.0,
        "north_cell_diagonal_metres": result_validator._EXPECTED_NORTH_DIAGONAL_METRES,
        "south_cell_diagonal_metres": result_validator._EXPECTED_SOUTH_DIAGONAL_METRES,
        "cell_diagonal_tolerance_metres": result_validator._EXPECTED_TOLERANCE_METRES,
        "distance_threshold_metres": result_validator._EXPECTED_DISTANCE_THRESHOLD_METRES,
        "max_row_offset": result_validator._EXPECTED_MAX_ROW_OFFSET,
        "max_col_offset": result_validator._EXPECTED_MAX_COL_OFFSET,
        "pyproj_version": result_validator._EXPECTED_PYPROJ_VERSION,
        "small_channel_filter_reconstructed": False,
        "mask_value_semantics_verified": False,
        "per_cell_scientific_correctness_verified": False,
        "benchmark_use_authorized": False,
        "model_use_authorized": False,
        "publication_authorized": False,
        "external_bytes_persisted": False,
    }


def _aggregate(*, farther: int = 0) -> dict:
    return {
        "schema_version": worker.SCHEMA_VERSION,
        "dataset_id": rp10_receipt.DATASET_ID,
        "source_issue": 823,
        "release": rp10_receipt.RELEASE,
        "rp10_receipt": _rp10_receipt(),
        "spurious_depth_receipt": _spurious_receipt(),
        "challenge": _challenge(farther=farther),
        "receipt_to_reader_binding": "verified_bytes_memoryfile",
        "external_bytes_persisted": False,
        "mask_value_semantics_verified": False,
        "per_cell_scientific_correctness_verified": False,
        "benchmark_use_authorized": False,
        "model_use_authorized": False,
        "publication_authorized": False,
    }


def _run(*, comments=None, challenge_acquirer=None):
    validated = request_validator.validate_request(_request(), expected_issue=823)
    with mock.patch.object(prepare._base, "utc_now", return_value=FINISHED_AT):
        return prepare.prepare_completed_result(
            validated,
            comments or [],
            repository=REPOSITORY,
            execution_sha=MAIN_SHA,
            source_comment_id=1,
            run_id=2,
            run_attempt=1,
            started_at=STARTED_AT,
            challenge_acquirer=challenge_acquirer or _aggregate,
        )


class CemsSpuriousSupportActionTests(unittest.TestCase):
    def test_request_is_closed_to_issue_dataset_and_exact_execution_sha(self) -> None:
        request = _request()
        self.assertIs(
            request_validator.validate_request(request, expected_issue=823),
            request,
        )
        self.assertIn(request["action"], protocol.NETWORK_ACQUISITION_ACTIONS)
        self.assertIn(request["action"], prepare.NETWORK_ACTIONS)
        self.assertEqual(prepare.ledger_issue_for_request(request), 823)

        for selector in (
            "url",
            "filename",
            "mask",
            "provider",
            "reader",
            "parser",
            "output",
            "candidate_value",
            "rp10_threshold",
            "distance",
            "threshold",
            "max_row_offset",
            "max_col_offset",
        ):
            selected = _request()
            selected[selector] = "forbidden"
            with self.subTest(selector=selector), self.assertRaises(
                request_validator.RequestError
            ):
                request_validator.validate_request(selected, expected_issue=823)

        with self.assertRaises(protocol.ProtocolError):
            protocol.semantic_request_id(
                _request(target_sha="0" * 40),
                MAIN_SHA,
                REPOSITORY,
            )

    def test_both_preregistered_scientific_verdicts_are_valid_evidence(self) -> None:
        for farther, verdict in (
            (0, "NOT_FALSIFIED_BY_CURRENT_RP10_NECESSARY_CONDITION"),
            (1, "CURRENT_RP10_NECESSARY_CONDITION_FAIL"),
        ):
            with self.subTest(farther=farther):
                aggregate = _aggregate(farther=farther)
                self.assertIs(
                    result_validator.validate_cems_spurious_support_challenge(aggregate),
                    aggregate,
                )
                self.assertEqual(aggregate["challenge"]["verdict"], verdict)
                self.assertFalse(aggregate["benchmark_use_authorized"])
                self.assertFalse(aggregate["model_use_authorized"])
                self.assertFalse(aggregate["publication_authorized"])

    def test_result_validation_rejects_geometry_verdict_and_authority_drift(self) -> None:
        tampered = copy.deepcopy(_aggregate())
        tampered["challenge"]["distance_threshold_metres"] += 0.001
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_cems_spurious_support_challenge(tampered)

        tampered = copy.deepcopy(_aggregate(farther=1))
        tampered["challenge"]["verdict"] = (
            "NOT_FALSIFIED_BY_CURRENT_RP10_NECESSARY_CONDITION"
        )
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_cems_spurious_support_challenge(tampered)

        tampered = copy.deepcopy(_aggregate())
        tampered["challenge"]["benchmark_use_authorized"] = True
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_cems_spurious_support_challenge(tampered)

    def test_success_scientific_fail_and_dedup_are_durable_states(self) -> None:
        passed = _run()
        self.assertEqual(passed["status"], "pass")
        self.assertIs(result_validator.validate_result(passed), passed)

        scientific_fail = _run(challenge_acquirer=lambda: _aggregate(farther=1))
        self.assertEqual(scientific_fail["status"], "pass")
        self.assertEqual(
            scientific_fail["evidence"][prepare.CEMS_SPURIOUS_SUPPORT_FIELD]["challenge"][
                "verdict"
            ],
            "CURRENT_RP10_NECESSARY_CONDITION_FAIL",
        )
        self.assertIs(result_validator.validate_result(scientific_fail), scientific_fail)

        prior = {
            "id": 900,
            "user": {"login": "github-actions[bot]"},
            "body": protocol.canonical_result_comment(passed),
        }
        acquirer = mock.Mock(return_value=_aggregate())
        duplicate = _run(comments=[prior], challenge_acquirer=acquirer)
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(duplicate["duplicate_result_comment_id"], 900)
        acquirer.assert_not_called()
        self.assertIs(result_validator.validate_result(duplicate), duplicate)

    def test_worker_failure_is_closed_without_provider_detail_in_result(self) -> None:
        def fail():
            raise RuntimeError("provider detail must not persist")

        result = _run(challenge_acquirer=fail)
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(
            result["evidence"][prepare.CEMS_SPURIOUS_SUPPORT_FIELD]
        )
        self.assertIs(result_validator.validate_result(result), result)

    def test_workflow_uses_stage_d_entrypoints_and_support_runtime(self) -> None:
        text = Path(".github/workflows/agent-action-dispatch.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "requirements-cems-mask-support-challenge.txt",
            text,
        )
        self.assertIn(
            "python -m scripts.prepare_agent_action_result_cems_spurious_support",
            text,
        )
        self.assertIn(
            "python -m scripts.post_agent_action_result_cems_spurious_support",
            text,
        )
        for legacy in (
            "prepare_agent_action_result_cems_mask_values",
            "post_agent_action_result_cems_mask_values",
            "prepare_agent_action_result_cems_mask_profiles",
            "post_agent_action_result_cems_mask_profiles",
            "repository-owned frozen DWD worker",
            "python scripts/post_agent_action_result.py",
        ):
            with self.subTest(legacy=legacy):
                self.assertIn(legacy, text)


if __name__ == "__main__":
    unittest.main()
