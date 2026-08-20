# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import run_esrm20_scenario_v10_greece_shakemap_profile_diagnostic_action as diagnostic

SHA = "a" * 40
COORD_SHA = "1" * 64


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
        "retrieved_at": "2026-08-20T14:24:00Z",
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


def _profile():
    specification = {
        "nlon": 2,
        "nlat": 2,
        "lon_min": 22.0,
        "lat_min": 37.0,
        "lon_max": 23.0,
        "lat_max": 38.0,
        "nominal_lon_spacing": 0.5,
        "nominal_lat_spacing": 0.5,
    }
    return {
        "schema_version": "oc-esrm20-scenario-v10-greece-shakemap-profile-v1",
        "receipt_event_id": "Greece_07-9-1999",
        "root_local_name": "shakemap_grid",
        "root_namespace": "http://earthquake.usgs.gov/eqcenter/shakemap",
        "metadata": {
            "event_id": "19990907115650",
            "shakemap_id": "19990907115650",
            "shakemap_version": "1",
            "code_version": "3.5",
            "shakemap_originator": "us",
            "map_status": "RELEASED",
            "shakemap_event_type": "ACTUAL",
        },
        "grid": {
            "byte_count": diagnostic.base.GRID_BYTE_COUNT,
            "sha256": diagnostic.base.GRID_SHA256,
            "fields": [
                {"index": 1, "name": "LON", "units": "dd"},
                {"index": 2, "name": "LAT", "units": "dd"},
                {"index": 3, "name": "PGA", "units": "pctg"},
            ],
            "specification": specification,
            "observed_row_count": 4,
            "coordinate_sha256": COORD_SHA,
            "openquake_3_12_1_present_imts": ["PGA"],
            "ignored_fields": [],
        },
        "uncertainty": {
            "byte_count": diagnostic.base.UNCERTAINTY_BYTE_COUNT,
            "sha256": diagnostic.base.UNCERTAINTY_SHA256,
            "fields": [
                {"index": 1, "name": "LON", "units": "dd"},
                {"index": 2, "name": "LAT", "units": "dd"},
                {"index": 3, "name": "STDPGA", "units": "ln(pctg)"},
            ],
            "specification": specification,
            "observed_row_count": 4,
            "coordinate_sha256": COORD_SHA,
            "openquake_3_12_1_present_imts": ["PGA"],
            "ignored_fields": [],
        },
        "openquake_3_12_1_paired_imts": ["PGA"],
        "coordinate_grids_equal": True,
        "provider_file_content_profiled": True,
        "event_location_inference_authorized": False,
        "scenario_selection_authorized": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


class GreeceShakeMapProfileDiagnosticTests(unittest.TestCase):
    def test_request_is_bound_to_exact_head_and_both_receipts(self):
        parsed = diagnostic.validate_request(_request(), expected_issue=285, execution_sha=SHA)
        self.assertEqual(parsed["target_sha"], SHA)
        for updates in (
            {"target_sha": "b" * 40},
            {"grid_receipt_sha256": "0" * 64},
            {"uncertainty_receipt_sha256": "0" * 64},
            {"issue": 999},
        ):
            with self.subTest(updates=updates), self.assertRaises(
                diagnostic.ShakeMapProfileDiagnosticError
            ):
                diagnostic.validate_request(_request(**updates), expected_issue=285, execution_sha=SHA)

    def test_request_has_no_provider_or_science_selector(self):
        parsed = diagnostic.validate_request(_request(), expected_issue=285, execution_sha=SHA)
        for forbidden in ("provider", "project_id", "ref", "path", "event_id", "url", "imt"):
            self.assertNotIn(forbidden, parsed)

    def test_duplicate_request_key_fails_closed(self):
        body = diagnostic.REQUEST_MARKER + '\n{"schema_version":"x","schema_version":"y"}'
        with self.assertRaisesRegex(diagnostic.ShakeMapProfileDiagnosticError, "duplicate JSON key"):
            diagnostic.validate_request(body, expected_issue=285, execution_sha=SHA)

    def test_all_parser_owned_messages_have_closed_codes(self):
        for message, expected in diagnostic._PROFILE_ERROR_CODE_BY_MESSAGE.items():
            with self.subTest(message=message):
                exc = diagnostic.base.ShakeMapProfileError(message)
                self.assertEqual(diagnostic.classify_profile_error(exc), expected)
                self.assertIn(expected, diagnostic.PROFILE_FAILURE_CODES)

    def test_unknown_exception_text_collapses_without_leak(self):
        secret = "provider-secret-xml-fragment"
        exc = diagnostic.base.ShakeMapProfileError(secret)
        code = diagnostic.classify_profile_error(exc)
        self.assertEqual(code, "unclassified_profile_rejection")
        self.assertNotIn(secret, code)

    def test_profile_rejection_reports_only_closed_stage_and_code(self):
        grid_raw = b"grid"
        uncertainty_raw = b"uncertainty"

        def profiler(_grid, _uncertainty):
            raise diagnostic.base.ShakeMapProfileError("unsupported_grid_field_name")

        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: ((grid_raw, uncertainty_raw), _receipts()),
            profiler=profiler,
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_stage"], "profile")
        self.assertEqual(result["failure_code"], "unsupported_grid_field_name")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertTrue(result["byte_identity_verified"])
        self.assertFalse(result["provider_file_content_profiled"])

    def test_unknown_profile_error_never_serializes_exception_text(self):
        secret = "SECRET_PROVIDER_TEXT_123"

        def profiler(_grid, _uncertainty):
            raise diagnostic.base.ShakeMapProfileError(secret)

        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: ((b"grid", b"uncertainty"), _receipts()),
            profiler=profiler,
        )
        encoded = json.dumps(result, sort_keys=True)
        self.assertEqual(result["failure_code"], "unclassified_profile_rejection")
        self.assertNotIn(secret, encoded)

    def test_acquisition_failure_preserves_partial_byte_fact_only(self):
        def fetcher():
            raise diagnostic.base.ShakeMapAcquisitionError(completed_files=1)

        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=fetcher,
            profiler=lambda _grid, _uncertainty: _profile(),
        )
        self.assertEqual(result["failure_stage"], "acquisition")
        self.assertEqual(result["failure_code"], "acquisition_failed")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertFalse(result["byte_identity_verified"])

    def test_byte_identity_failure_stops_before_profile(self):
        def fetcher():
            raise diagnostic.base.ShakeMapByteIdentityError("mismatch")

        profiler = mock.Mock()
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=fetcher,
            profiler=profiler,
        )
        self.assertEqual(result["failure_stage"], "byte_identity")
        self.assertEqual(result["failure_code"], "byte_identity_mismatch")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertFalse(result["byte_identity_verified"])
        profiler.assert_not_called()

    def test_pass_requires_existing_receipt_and_profile_validators(self):
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: ((b"grid", b"uncertainty"), _receipts()),
            profiler=lambda _grid, _uncertainty: _profile(),
        )
        self.assertEqual(result["status"], "pass")
        self.assertIsNone(result["failure_stage"])
        self.assertIsNone(result["failure_code"])
        self.assertTrue(result["provider_file_content_profiled"])
        self.assertTrue(result["byte_identity_verified"])

    def test_terminal_validator_rejects_authority_promotion(self):
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: ((b"grid", b"uncertainty"), _receipts()),
            profiler=lambda _grid, _uncertainty: _profile(),
        )
        result["publication_authorized"] = True
        with self.assertRaisesRegex(
            diagnostic.ShakeMapProfileDiagnosticError,
            "result publication_authorized drifted",
        ):
            diagnostic._validate_terminal_result(result)

    def test_historical_profile_terminal_is_not_reinterpreted(self):
        old = (
            "<!-- oc-eq1-esrm20-scenario-v10-greece-shakemap-profile-result-v1 -->\n"
            '{"execution_sha":"' + SHA + '"}'
        )
        self.assertIsNone(diagnostic.parse_terminal_result(old))

    def test_trusted_bot_terminal_deduplicates_exact_execution_sha(self):
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: ((b"grid", b"uncertainty"), _receipts()),
            profiler=lambda _grid, _uncertainty: _profile(),
        )
        body = diagnostic.RESULT_MARKER + "\n" + json.dumps(result, separators=(",", ":"))
        comments = [{"user": {"login": "github-actions[bot]"}, "body": body}]
        with mock.patch.object(diagnostic.base, "fetch_repository_comments", return_value=comments):
            self.assertTrue(
                diagnostic.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=SHA,
                )
            )

    def test_untrusted_terminal_does_not_deduplicate(self):
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: ((b"grid", b"uncertainty"), _receipts()),
            profiler=lambda _grid, _uncertainty: _profile(),
        )
        body = diagnostic.RESULT_MARKER + "\n" + json.dumps(result, separators=(",", ":"))
        comments = [{"user": {"login": "pokekarten"}, "body": body}]
        with mock.patch.object(diagnostic.base, "fetch_repository_comments", return_value=comments):
            self.assertFalse(
                diagnostic.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=SHA,
                )
            )


if __name__ == "__main__":
    unittest.main()
