# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest

from scripts import profile_eq1_kosovo_spatial_interop as profile
from scripts import run_eq1_kosovo_spatial_interop_action as action

EXECUTION_SHA = "b" * 40


def _threshold(threshold: str, exposure_count: int, associated: int) -> dict:
    return {
        "threshold_km": threshold,
        "associated_exposure_record_count": associated,
        "discarded_exposure_record_count": exposure_count - associated,
        "all_exposure_records_associated": associated == exposure_count,
    }


def _valid_profile() -> dict:
    exposure_count = 100
    diagnostics = [
        _threshold("1", exposure_count, 20),
        _threshold("5", exposure_count, 60),
        _threshold("10", exposure_count, 90),
        _threshold("15", exposure_count, 100),
        _threshold("20", exposure_count, 100),
        _threshold("25", exposure_count, 100),
        _threshold("50", exposure_count, 100),
    ]
    return {
        "schema_version": profile.SCHEMA_VERSION,
        "source_issue": 287,
        "reference_runtime": {
            "repository": "gem/oq-engine",
            "tag": profile.OPENQUAKE_REFERENCE_TAG,
            "commit_sha": profile.OPENQUAKE_REFERENCE_COMMIT,
            "association_contract": (
                "when the supplied site-model mesh is the selected hazard mesh, exposure "
                "asset locations are associated to nearest hazard sites by zero-depth "
                "spherical Cartesian distance"
            ),
            "hazard_mesh_precondition": (
                "no higher-precedence explicit sites, sites input, hazard-curves mesh, "
                "or region_grid_spacing path overrides the supplied site-model mesh"
            ),
        },
        "exposure_identity": {
            "dataset_id": profile._CANONICAL_EXPOSURE_DATASET_ID,
            "project_id": profile._CANONICAL_EXPOSURE_PROJECT_ID,
            "project_path": profile._CANONICAL_EXPOSURE_PROJECT_PATH,
            "commit_sha": profile._CANONICAL_EXPOSURE_COMMIT_SHA,
            "repository_path": profile._CANONICAL_EXPOSURE_REPOSITORY_PATH,
            "byte_count": profile._CANONICAL_EXPOSURE_BYTE_COUNT,
            "sha256": profile._CANONICAL_EXPOSURE_SHA256,
        },
        "site_identity": {
            "dataset_id": profile._CANONICAL_SITE_DATASET_ID,
            "project_id": profile._CANONICAL_SITE_PROJECT_ID,
            "project_path": profile._CANONICAL_SITE_PROJECT_PATH,
            "commit_sha": profile._CANONICAL_SITE_COMMIT_SHA,
            "repository_path": profile._CANONICAL_SITE_REPOSITORY_PATH,
            "byte_count": profile._CANONICAL_SITE_BYTE_COUNT,
            "sha256": profile._CANONICAL_SITE_SHA256,
        },
        "profile": {
            "exposure_record_count": exposure_count,
            "distinct_exposure_location_count": 90,
            "site_record_count": 20,
            "distinct_site_location_count": 20,
            "nearest_site_distance_km": {"minimum": "0.01", "maximum": "12.5"},
            "threshold_diagnostics": diagnostics,
            "openquake_default_asset_hazard_distance_km": "15",
            "default_distance_association": dict(diagnostics[3]),
            "raw_coordinates_returned": False,
        },
        "reference_runtime_coordinate_role_verified": True,
        "source_crs_datum_epsg_verified": False,
        "reprojection_performed": False,
        "reprojection_authorized": False,
        "geographic_cross_source_equivalence_authorized": False,
        "raw_provider_coordinates_returned": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


class KosovoSpatialInteropActionTests(unittest.TestCase):
    def test_request_is_exact_issue_and_execution_sha_bound(self) -> None:
        body = action.REQUEST_MARKER + "\n" + json.dumps(
            {
                "schema_version": action.REQUEST_SCHEMA_VERSION,
                "issue": 287,
                "target_sha": EXECUTION_SHA,
                "requester": "test-runner",
            },
            separators=(",", ":"),
        )
        parsed = action.validate_request(body, expected_issue=287, execution_sha=EXECUTION_SHA)
        self.assertEqual(parsed["target_sha"], EXECUTION_SHA)
        with self.assertRaises(action.KosovoSpatialInteropExecutionError):
            action.validate_request(body, expected_issue=287, execution_sha="c" * 40)

    def test_request_rejects_duplicate_json_key_and_nonfinite_constant(self) -> None:
        duplicate = (
            action.REQUEST_MARKER
            + '\n{"schema_version":"'
            + action.REQUEST_SCHEMA_VERSION
            + '","issue":287,"target_sha":"'
            + EXECUTION_SHA
            + '","target_sha":"'
            + EXECUTION_SHA
            + '","requester":"x"}'
        )
        with self.assertRaisesRegex(action.KosovoSpatialInteropExecutionError, "duplicate JSON key"):
            action.validate_request(duplicate, expected_issue=287, execution_sha=EXECUTION_SHA)
        nonfinite = (
            action.REQUEST_MARKER
            + '\n{"schema_version":"'
            + action.REQUEST_SCHEMA_VERSION
            + '","issue":287,"target_sha":"'
            + EXECUTION_SHA
            + '","requester":NaN}'
        )
        with self.assertRaisesRegex(action.KosovoSpatialInteropExecutionError, "non-finite"):
            action.validate_request(nonfinite, expected_issue=287, execution_sha=EXECUTION_SHA)

    def test_profile_accepts_exact_frozen_identity_and_aggregate_shape(self) -> None:
        value = _valid_profile()
        self.assertEqual(action.validate_profile(value), value)

    def test_profile_rejects_identity_or_authority_widening(self) -> None:
        widened = _valid_profile()
        widened["source_crs_datum_epsg_verified"] = True
        with self.assertRaisesRegex(action.KosovoSpatialInteropExecutionError, "source_crs_datum_epsg_verified"):
            action.validate_profile(widened)

        drifted = _valid_profile()
        drifted["site_identity"] = dict(drifted["site_identity"])
        drifted["site_identity"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(action.KosovoSpatialInteropExecutionError, "site identity sha256"):
            action.validate_profile(drifted)

        runtime = _valid_profile()
        runtime["reference_runtime"] = dict(runtime["reference_runtime"])
        runtime["reference_runtime"]["hazard_mesh_precondition"] = "site model always wins"
        with self.assertRaisesRegex(action.KosovoSpatialInteropExecutionError, "hazard_mesh_precondition"):
            action.validate_profile(runtime)

    def test_profile_rejects_threshold_reconciliation_order_and_default_drift(self) -> None:
        nonmonotonic = _valid_profile()
        nonmonotonic["profile"] = dict(nonmonotonic["profile"])
        nonmonotonic["profile"]["threshold_diagnostics"] = [
            dict(item) for item in nonmonotonic["profile"]["threshold_diagnostics"]
        ]
        nonmonotonic["profile"]["threshold_diagnostics"][1] = _threshold("5", 100, 10)
        with self.assertRaisesRegex(action.KosovoSpatialInteropExecutionError, "not monotonic"):
            action.validate_profile(nonmonotonic)

        wrong_threshold = _valid_profile()
        wrong_threshold["profile"] = dict(wrong_threshold["profile"])
        wrong_threshold["profile"]["threshold_diagnostics"] = [
            dict(item) for item in wrong_threshold["profile"]["threshold_diagnostics"]
        ]
        wrong_threshold["profile"]["threshold_diagnostics"][2]["threshold_km"] = "9"
        with self.assertRaisesRegex(action.KosovoSpatialInteropExecutionError, "threshold_km"):
            action.validate_profile(wrong_threshold)

        bad_default = _valid_profile()
        bad_default["profile"] = dict(bad_default["profile"])
        bad_default["profile"]["default_distance_association"] = dict(
            bad_default["profile"]["default_distance_association"]
        )
        bad_default["profile"]["default_distance_association"]["associated_exposure_record_count"] = 99
        bad_default["profile"]["default_distance_association"]["discarded_exposure_record_count"] = 1
        bad_default["profile"]["default_distance_association"]["all_exposure_records_associated"] = False
        with self.assertRaisesRegex(action.KosovoSpatialInteropExecutionError, "disagrees"):
            action.validate_profile(bad_default)

    def test_pass_and_blocked_results_are_fail_closed(self) -> None:
        passed = {
            **action._base_result(execution_sha=EXECUTION_SHA),
            "status": "pass",
            "failure_class": None,
            "profile": _valid_profile(),
        }
        body = action.RESULT_MARKER + "\n" + json.dumps(
            passed, sort_keys=True, separators=(",", ":")
        )
        self.assertTrue(action.parse_terminal_result(body, execution_sha=EXECUTION_SHA))

        blocked = {
            **action._base_result(execution_sha=EXECUTION_SHA),
            "status": "blocked",
            "failure_class": action.BLOCKED_FAILURE_CLASS,
            "profile": None,
        }
        blocked_body = action.RESULT_MARKER + "\n" + json.dumps(
            blocked, sort_keys=True, separators=(",", ":")
        )
        self.assertTrue(action.parse_terminal_result(blocked_body, execution_sha=EXECUTION_SHA))
        blocked["profile"] = _valid_profile()
        widened_body = action.RESULT_MARKER + "\n" + json.dumps(
            blocked, sort_keys=True, separators=(",", ":")
        )
        with self.assertRaisesRegex(action.KosovoSpatialInteropExecutionError, "widened evidence"):
            action.parse_terminal_result(widened_body, execution_sha=EXECUTION_SHA)

    def test_dedup_scans_only_trusted_bot_terminal_results(self) -> None:
        terminal = {
            **action._base_result(execution_sha=EXECUTION_SHA),
            "status": "pass",
            "failure_class": None,
            "profile": _valid_profile(),
        }
        body = action.RESULT_MARKER + "\n" + json.dumps(
            terminal, sort_keys=True, separators=(",", ":")
        )
        original_fetch = action.fetch_repository_comments
        original_authority = action._FETCH_COMMENTS
        try:
            def fake_fetch(repository, token, *, issue, max_pages):
                self.assertEqual(issue, 287)
                return [
                    {"user": {"login": "someone"}, "body": body},
                    {"user": {"login": action.TRUSTED_RESULT_LOGIN}, "body": body},
                ]

            action.fetch_repository_comments = fake_fetch
            action._FETCH_COMMENTS = fake_fetch
            self.assertTrue(
                action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=EXECUTION_SHA,
                )
            )
        finally:
            action.fetch_repository_comments = original_fetch
            action._FETCH_COMMENTS = original_authority

    def test_execute_deduplicates_before_profile_execution(self) -> None:
        terminal = {
            **action._base_result(execution_sha=EXECUTION_SHA),
            "status": "pass",
            "failure_class": None,
            "profile": _valid_profile(),
        }
        body = action.RESULT_MARKER + "\n" + json.dumps(
            terminal, sort_keys=True, separators=(",", ":")
        )
        original_fetch = action.fetch_repository_comments
        original_fetch_authority = action._FETCH_COMMENTS
        original_profile = profile.acquire_and_profile_kosovo_spatial_interop
        original_profile_authority = action._PROFILE
        calls = 0
        try:
            def fake_fetch(repository, token, *, issue, max_pages):
                return [{"user": {"login": action.TRUSTED_RESULT_LOGIN}, "body": body}]

            def forbidden_profile():
                nonlocal calls
                calls += 1
                raise AssertionError("provider profiler must not run after dedup")

            action.fetch_repository_comments = fake_fetch
            action._FETCH_COMMENTS = fake_fetch
            profile.acquire_and_profile_kosovo_spatial_interop = forbidden_profile
            action._PROFILE = forbidden_profile
            result = action.execute_profile(
                repository="pokekarten/OpenCatastrophe-data",
                token="x",
                execution_sha=EXECUTION_SHA,
            )
            self.assertEqual(result["status"], "duplicate")
            self.assertEqual(calls, 0)
        finally:
            action.fetch_repository_comments = original_fetch
            action._FETCH_COMMENTS = original_fetch_authority
            profile.acquire_and_profile_kosovo_spatial_interop = original_profile
            action._PROFILE = original_profile_authority

    def test_execute_converts_only_profile_failure_to_closed_block(self) -> None:
        original_fetch = action.fetch_repository_comments
        original_fetch_authority = action._FETCH_COMMENTS
        original_profile = profile.acquire_and_profile_kosovo_spatial_interop
        original_profile_authority = action._PROFILE
        try:
            def no_results(repository, token, *, issue, max_pages):
                return []

            def blocked_profile():
                raise profile.SpatialInteropProfileError("synthetic fixed-provider failure")

            action.fetch_repository_comments = no_results
            action._FETCH_COMMENTS = no_results
            profile.acquire_and_profile_kosovo_spatial_interop = blocked_profile
            action._PROFILE = blocked_profile
            result = action.execute_profile(
                repository="pokekarten/OpenCatastrophe-data",
                token="x",
                execution_sha=EXECUTION_SHA,
            )
            self.assertEqual(
                result,
                {
                    **action._base_result(execution_sha=EXECUTION_SHA),
                    "status": "blocked",
                    "failure_class": action.BLOCKED_FAILURE_CLASS,
                    "profile": None,
                },
            )
        finally:
            action.fetch_repository_comments = original_fetch
            action._FETCH_COMMENTS = original_fetch_authority
            profile.acquire_and_profile_kosovo_spatial_interop = original_profile
            action._PROFILE = original_profile_authority

    def test_execution_rejects_profile_or_ledger_authority_rebinding(self) -> None:
        original_profile = profile.acquire_and_profile_kosovo_spatial_interop
        original_fetch = action.fetch_repository_comments
        try:
            profile.acquire_and_profile_kosovo_spatial_interop = lambda: _valid_profile()
            with self.assertRaisesRegex(
                action.KosovoSpatialInteropExecutionError, "execution authority drifted"
            ):
                action.execute_profile(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=EXECUTION_SHA,
                )
        finally:
            profile.acquire_and_profile_kosovo_spatial_interop = original_profile

        try:
            action.fetch_repository_comments = lambda *args, **kwargs: []
            with self.assertRaisesRegex(
                action.KosovoSpatialInteropExecutionError, "execution authority drifted"
            ):
                action.execute_profile(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=EXECUTION_SHA,
                )
        finally:
            action.fetch_repository_comments = original_fetch


if __name__ == "__main__":
    unittest.main()
