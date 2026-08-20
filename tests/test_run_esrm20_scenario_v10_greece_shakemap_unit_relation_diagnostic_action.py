# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

from scripts import (
    run_esrm20_scenario_v10_greece_shakemap_unit_relation_diagnostic_action
    as diagnostic,
)

SHA = "a" * 40


def _request(**updates):
    payload = {
        "schema_version": diagnostic.REQUEST_SCHEMA_VERSION,
        "action": diagnostic.ACTION,
        "issue": 285,
        "target_sha": SHA,
        "dataset_id": "efehr.esrm20.scenario-tests.v1.0",
        "grid_receipt_sha256": diagnostic.base.GRID_SHA256,
        "uncertainty_receipt_sha256": diagnostic.base.UNCERTAINTY_SHA256,
        "requester": "TEST-RUNNER",
    }
    payload.update(updates)
    return diagnostic.REQUEST_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))


def _receipt(role):
    identity = diagnostic.base._file_identity(role=role)
    return {
        "role": role,
        "retrieved_at": "2026-08-20T16:10:00Z",
        "byte_count": identity["receipt_byte_count"],
        "sha256": identity["receipt_sha256"],
        "git_blob_sha1": identity["git_blob_sha1"],
        "content_type": "application/xml",
        "etag": None,
    }


def _receipts():
    return {
        "grid": _receipt(diagnostic.base._CANONICAL_GRID_ROLE),
        "uncertainty": _receipt(diagnostic.base._CANONICAL_UNCERTAINTY_ROLE),
    }


def _xml(fields):
    rows = "".join(
        f'<grid_field index="{index}" name="{name}" units="{units}"/>'
        for index, (name, units) in enumerate(fields, 1)
    )
    return f'<shakemap_grid xmlns="urn:test">{rows}</shakemap_grid>'.encode()


def _valid_profile():
    return {
        "schema_version": "oc-esrm20-scenario-v10-greece-shakemap-profile-v1",
        "receipt_event_id": "Greece_07-9-1999",
        "root_local_name": "shakemap_grid",
        "root_namespace": "urn:test",
        "metadata": {
            "event_id": "",
            "shakemap_id": "",
            "shakemap_version": "",
            "code_version": "",
            "shakemap_originator": "",
            "map_status": "",
            "shakemap_event_type": "",
        },
        "grid": {},
        "uncertainty": {},
        "openquake_3_12_1_paired_imts": [],
        "coordinate_grids_equal": True,
        "provider_file_content_profiled": True,
        "event_location_inference_authorized": False,
        "scenario_selection_authorized": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


class GreeceShakeMapUnitRelationDiagnosticTests(unittest.TestCase):
    def test_request_is_bound_to_exact_head_and_receipts(self):
        parsed = diagnostic.validate_request(
            _request(),
            expected_issue=285,
            execution_sha=SHA,
        )
        self.assertEqual(parsed["target_sha"], SHA)
        for updates in (
            {"target_sha": "b" * 40},
            {"grid_receipt_sha256": "0" * 64},
            {"uncertainty_receipt_sha256": "0" * 64},
            {"issue": 999},
        ):
            with self.subTest(updates=updates), self.assertRaises(
                diagnostic.ShakeMapUnitRelationDiagnosticError
            ):
                diagnostic.validate_request(
                    _request(**updates),
                    expected_issue=285,
                    execution_sha=SHA,
                )

    def test_request_has_no_provider_or_science_selector(self):
        parsed = diagnostic.validate_request(
            _request(),
            expected_issue=285,
            execution_sha=SHA,
        )
        for forbidden in (
            "provider",
            "project_id",
            "ref",
            "path",
            "event_id",
            "url",
            "imt",
            "units",
        ):
            self.assertNotIn(forbidden, parsed)

    def test_duplicate_request_key_fails_closed(self):
        body = diagnostic.REQUEST_MARKER + '\n{"schema_version":"x","schema_version":"y"}'
        with self.assertRaisesRegex(
            diagnostic.ShakeMapUnitRelationDiagnosticError,
            "duplicate JSON key",
        ):
            diagnostic.validate_request(
                body,
                expected_issue=285,
                execution_sha=SHA,
            )

    def test_documented_global_unit_wrong_for_field_is_closed(self):
        result = diagnostic._classify_member_unit_mismatch(
            _xml([("LON", "dd"), ("LAT", "dd"), ("MMI", "pctg")]),
            member="grid",
            allowed_units=diagnostic._EXPECTED_GRID_FIELD_UNITS,
        )
        self.assertEqual(
            result,
            {
                "unit_failure_member": "grid",
                "unit_failure_field": "MMI",
                "unit_relation": "documented_global_unit_wrong_for_field",
            },
        )

    def test_blank_unexpected_is_distinct(self):
        result = diagnostic._classify_member_unit_mismatch(
            _xml([("LON", "dd"), ("LAT", "dd"), ("STDPGA", "")]),
            member="uncertainty",
            allowed_units=diagnostic._EXPECTED_UNCERTAINTY_FIELD_UNITS,
        )
        self.assertEqual(result["unit_relation"], "blank_unexpected")

    def test_outside_vocabulary_never_serializes_raw_token(self):
        secret = "SECRET_PROVIDER_UNIT"
        result = diagnostic._classify_member_unit_mismatch(
            _xml([("LON", "dd"), ("LAT", "dd"), ("STDPGA", secret)]),
            member="uncertainty",
            allowed_units=diagnostic._EXPECTED_UNCERTAINTY_FIELD_UNITS,
        )
        encoded = json.dumps(result, sort_keys=True)
        self.assertEqual(
            result["unit_relation"],
            "outside_frozen_usgs_unit_vocabulary",
        )
        self.assertNotIn(secret, encoded)

    def test_unknown_field_fails_without_leaking_field_name(self):
        secret = "SECRET_FIELD"
        with self.assertRaises(
            diagnostic.ShakeMapUnitRelationDiagnosticError
        ) as caught:
            diagnostic._classify_member_unit_mismatch(
                _xml([("LON", "dd"), ("LAT", "dd"), (secret, "pctg")]),
                member="grid",
                allowed_units=diagnostic._EXPECTED_GRID_FIELD_UNITS,
            )
        self.assertNotIn(secret, str(caught.exception))

    def test_unit_rejection_publishes_only_closed_classification(self):
        secret = b"SECRET_PROVIDER_UNIT"

        def profile_pair(_grid, _uncertainty):
            raise diagnostic.base.ShakeMapProfileError(
                "unsupported_grid_field_units"
            )

        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: ((secret, b"uncertainty"), _receipts()),
            profile_pair=profile_pair,
            unit_classifier=lambda _grid, _uncertainty: {
                "unit_failure_member": "grid",
                "unit_failure_field": "MMI",
                "unit_relation": "documented_global_unit_wrong_for_field",
            },
        )
        encoded = json.dumps(result, sort_keys=True)
        self.assertEqual(result["failure_code"], "unsupported_grid_field_units")
        self.assertEqual(result["unit_failure_member"], "grid")
        self.assertNotIn(secret.decode(), encoded)
        self.assertFalse(result["provider_file_content_profiled"])

    def test_changed_profile_rejection_collapses_without_exception_text(self):
        secret = "SECRET_PROFILE_TEXT"

        def profile_pair(_grid, _uncertainty):
            raise diagnostic.base.ShakeMapProfileError(secret)

        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: ((b"grid", b"uncertainty"), _receipts()),
            profile_pair=profile_pair,
            unit_classifier=mock.Mock(),
        )
        encoded = json.dumps(result, sort_keys=True)
        self.assertEqual(result["failure_code"], "profile_rejection_changed")
        self.assertNotIn(secret, encoded)
        self.assertIsNone(result["unit_relation"])

    def test_non_reproduced_rejection_remains_blocked(self):
        with mock.patch.object(diagnostic.base, "_validate_profile") as validate:
            result = diagnostic._run_diagnostic_with(
                execution_sha=SHA,
                fetcher=lambda: ((b"grid", b"uncertainty"), _receipts()),
                profile_pair=lambda _grid, _uncertainty: _valid_profile(),
                unit_classifier=mock.Mock(),
            )
        validate.assert_called_once()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(
            result["failure_code"],
            "profile_rejection_not_reproduced",
        )
        self.assertTrue(result["provider_file_content_profiled"])
        self.assertIsNone(result["unit_failure_field"])

    def test_byte_identity_failure_stops_before_profile_and_classifier(self):
        def fetcher():
            raise diagnostic.base.ShakeMapByteIdentityError("mismatch")

        profile_pair = mock.Mock()
        unit_classifier = mock.Mock()
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=fetcher,
            profile_pair=profile_pair,
            unit_classifier=unit_classifier,
        )
        self.assertEqual(result["failure_stage"], "byte_identity")
        self.assertEqual(result["failure_code"], "byte_identity_mismatch")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertFalse(result["byte_identity_verified"])
        profile_pair.assert_not_called()
        unit_classifier.assert_not_called()

    def test_terminal_validator_rejects_authority_promotion(self):
        result = diagnostic._base_result(SHA)
        result["publication_authorized"] = True
        with self.assertRaisesRegex(
            diagnostic.ShakeMapUnitRelationDiagnosticError,
            "result publication_authorized drifted",
        ):
            diagnostic._validate_terminal_result(result)

    def test_trusted_bot_terminal_deduplicates_exact_execution_sha(self):
        result = diagnostic._base_result(SHA)
        body = diagnostic.RESULT_MARKER + "\n" + json.dumps(
            result,
            separators=(",", ":"),
        )
        comments = [{"user": {"login": "github-actions[bot]"}, "body": body}]
        with mock.patch.object(
            diagnostic.base,
            "fetch_repository_comments",
            return_value=comments,
        ):
            self.assertTrue(
                diagnostic.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=SHA,
                )
            )

    def test_historical_diagnostic_terminal_is_not_reinterpreted(self):
        old = (
            "<!-- oc-eq1-esrm20-scenario-v10-greece-shakemap-profile-diagnostic-result-v1 -->\n"
            '{"execution_sha":"' + SHA + '"}'
        )
        self.assertIsNone(diagnostic.parse_terminal_result(old))

    def test_workflow_is_trusted_main_only_and_no_raw_selector_exists(self):
        workflow = Path(
            ".github/workflows/"
            "esrm20-scenario-v10-greece-shakemap-unit-relation-diagnostic.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("github.event.repository.default_branch", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("issues: write", workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertNotIn("workflow_dispatch:", workflow)
        self.assertNotIn("raw_unit", workflow)
        self.assertNotIn("provider_url", workflow)


if __name__ == "__main__":
    unittest.main()
