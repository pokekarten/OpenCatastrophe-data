# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import run_esrm20_scenario_v10_greece_shakemap_profile_action as subject

SHA = "a" * 40
COORD_SHA = "1" * 64


def request_body(**updates):
    value = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": 285,
        "target_sha": SHA,
        "dataset_id": subject.DATASET_ID,
        "grid_receipt_sha256": subject.GRID_SHA256,
        "uncertainty_receipt_sha256": subject.UNCERTAINTY_SHA256,
        "requester": "CHAT-TEST",
    }
    value.update(updates)
    return subject.REQUEST_MARKER + "\n" + json.dumps(value, separators=(",", ":"))


def receipt(role):
    identity = subject._file_identity(role=role)
    return {
        "role": role,
        "retrieved_at": "2026-08-20T13:30:00Z",
        "byte_count": identity["receipt_byte_count"],
        "sha256": identity["receipt_sha256"],
        "git_blob_sha1": identity["git_blob_sha1"],
        "content_type": "application/xml",
        "etag": None,
    }


def receipts():
    return {
        "grid": receipt(subject._CANONICAL_GRID_ROLE),
        "uncertainty": receipt(subject._CANONICAL_UNCERTAINTY_ROLE),
    }


def profile(**updates):
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
    value = {
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
            "byte_count": subject.GRID_BYTE_COUNT,
            "sha256": subject.GRID_SHA256,
            "fields": [
                {"index": 1, "name": "LON", "units": "dd"},
                {"index": 2, "name": "LAT", "units": "dd"},
                {"index": 3, "name": "PGA", "units": "pctg"},
                {"index": 4, "name": "PGV", "units": "cms"},
            ],
            "specification": specification,
            "observed_row_count": 4,
            "coordinate_sha256": COORD_SHA,
            "openquake_3_12_1_present_imts": ["PGA"],
            "ignored_fields": ["PGV"],
        },
        "uncertainty": {
            "byte_count": subject.UNCERTAINTY_BYTE_COUNT,
            "sha256": subject.UNCERTAINTY_SHA256,
            "fields": [
                {"index": 1, "name": "LON", "units": "dd"},
                {"index": 2, "name": "LAT", "units": "dd"},
                {"index": 3, "name": "STDPGA", "units": "ln(pctg)"},
                {"index": 4, "name": "STDPGV", "units": "ln(cms)"},
            ],
            "specification": specification,
            "observed_row_count": 4,
            "coordinate_sha256": COORD_SHA,
            "openquake_3_12_1_present_imts": ["PGA"],
            "ignored_fields": ["STDPGV"],
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
    value.update(updates)
    return value


class ActionTests(unittest.TestCase):
    def test_request_is_exact_head_and_both_receipts_bound(self):
        parsed = subject.validate_request(request_body(), expected_issue=285, execution_sha=SHA)
        self.assertEqual(parsed["requester"], "CHAT-TEST")
        for updates in (
            {"target_sha": "b" * 40},
            {"grid_receipt_sha256": "0" * 64},
            {"uncertainty_receipt_sha256": "0" * 64},
            {"issue": 999},
            {"dataset_id": "other"},
        ):
            with self.subTest(updates=updates), self.assertRaises(subject.GreeceShakeMapProfileActionError):
                subject.validate_request(request_body(**updates), expected_issue=285, execution_sha=SHA)

    def test_request_has_no_provider_ref_path_event_or_imt_selector(self):
        parsed = subject.validate_request(request_body(), expected_issue=285, execution_sha=SHA)
        for forbidden in ("provider", "project_id", "ref", "path", "event_id", "url", "imt"):
            self.assertNotIn(forbidden, parsed)

    def test_duplicate_json_keys_fail_closed(self):
        body = subject.REQUEST_MARKER + '\n{"schema_version":"x","schema_version":"y"}'
        with self.assertRaisesRegex(subject.GreeceShakeMapProfileActionError, "duplicate JSON key"):
            subject.validate_request(body, expected_issue=285, execution_sha=SHA)

    def test_pass_profiles_pair_only_in_memory_and_preserves_ceilings(self):
        grid_raw = b"grid"
        uncertainty_raw = b"uncertainty"
        result = subject._run_profile_with(
            execution_sha=SHA,
            fetcher=lambda: ((grid_raw, uncertainty_raw), receipts()),
            profiler=lambda grid, uncertainty: profile()
            if grid is grid_raw and uncertainty is uncertainty_raw
            else self.fail("raw byte objects were replaced"),
        )
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertTrue(result["provider_file_content_profiled"])
        self.assertFalse(result["output_payload_bytes_read"])
        self.assertFalse(result["external_bytes_persisted"])
        for field in (
            "event_location_inference_authorized",
            "scenario_selection_authorized",
            "independent_validation_established",
            "holdout_status_established",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertFalse(result[field])
        self.assertNotIn("raw", result)
        self.assertEqual(subject._validate_terminal_result(result), SHA)

    def test_acquisition_failure_after_first_complete_file_is_bounded(self):
        def fail():
            raise subject.ShakeMapAcquisitionError(completed_files=1)

        result = subject._run_profile_with(
            execution_sha=SHA,
            fetcher=fail,
            profiler=lambda _grid, _uncertainty: profile(),
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failure")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertIsNone(result["receipts"])
        self.assertIsNone(result["profile"])

    def test_byte_identity_failure_is_static_and_bounded(self):
        def fail():
            raise subject.ShakeMapByteIdentityError("mutated provider bytes: secret")

        result = subject._run_profile_with(
            execution_sha=SHA,
            fetcher=fail,
            profiler=lambda _grid, _uncertainty: profile(),
        )
        self.assertEqual(result["failure_class"], "byte_identity_mismatch")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertFalse(result["provider_file_content_profiled"])
        self.assertIsNone(result["failure_code"])
        self.assertNotIn("secret", json.dumps(result, sort_keys=True))

    def test_profile_rejection_cannot_leak_parser_text(self):
        secret = "provider-derived-grid-value"

        def reject(_grid, _uncertainty):
            raise subject.ShakeMapProfileError(secret)

        result = subject._run_profile_with(
            execution_sha=SHA,
            fetcher=lambda: ((b"grid", b"uncertainty"), receipts()),
            profiler=reject,
        )
        self.assertEqual(result["failure_class"], "profile_failure")
        self.assertEqual(result["failure_code"], "shakemap_pair_profile_rejected")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertFalse(result["provider_file_content_profiled"])
        self.assertNotIn(secret, json.dumps(result, sort_keys=True))

    def test_terminal_rejects_top_level_authority_widening(self):
        result = subject._run_profile_with(
            execution_sha=SHA,
            fetcher=lambda: ((b"grid", b"uncertainty"), receipts()),
            profiler=lambda _grid, _uncertainty: profile(),
        )
        for field in (
            "event_location_inference_authorized",
            "scenario_selection_authorized",
            "independent_validation_established",
            "holdout_status_established",
            "publication_authorized",
            "model_use_authorized",
        ):
            mutated = dict(result)
            mutated[field] = True
            with self.subTest(field=field), self.assertRaises(subject.GreeceShakeMapProfileActionError):
                subject._validate_terminal_result(mutated)

    def test_profile_rejects_nested_authority_widening(self):
        for field in (
            "event_location_inference_authorized",
            "scenario_selection_authorized",
            "independent_validation_established",
            "holdout_status_established",
            "publication_authorized",
            "model_use_authorized",
        ):
            with self.subTest(field=field), self.assertRaises(subject.GreeceShakeMapProfileActionError):
                subject._validate_profile(profile(**{field: True}))

    def test_profile_rejects_coordinate_or_imt_pair_drift(self):
        bad = profile()
        bad["uncertainty"] = dict(bad["uncertainty"])
        bad["uncertainty"]["coordinate_sha256"] = "2" * 64
        with self.assertRaisesRegex(subject.GreeceShakeMapProfileActionError, "coordinate pairing"):
            subject._validate_profile(bad)

        bad = profile(openquake_3_12_1_paired_imts=[])
        with self.assertRaisesRegex(subject.GreeceShakeMapProfileActionError, "paired IMTs"):
            subject._validate_profile(bad)

    def test_receipts_cannot_be_swapped_or_widened(self):
        bad = receipts()
        bad["grid"] = dict(bad["grid"])
        bad["grid"]["role"] = subject._CANONICAL_UNCERTAINTY_ROLE
        with self.assertRaisesRegex(subject.GreeceShakeMapProfileActionError, "receipt role"):
            subject._validate_receipts(bad)

    def test_terminal_rejects_arbitrary_failure_code(self):
        result = subject._base_result(SHA)
        result["failure_class"] = "profile_failure"
        result["provider_file_bytes_read"] = True
        result["failure_code"] = "provider-derived-secret"
        with self.assertRaisesRegex(subject.GreeceShakeMapProfileActionError, "invalid profile failure state"):
            subject._validate_terminal_result(result)

    def test_dedup_counts_only_trusted_bot_same_sha(self):
        terminal = subject._run_profile_with(
            execution_sha=SHA,
            fetcher=lambda: ((b"grid", b"uncertainty"), receipts()),
            profiler=lambda _grid, _uncertainty: profile(),
        )
        body = subject.RESULT_MARKER + "\n" + json.dumps(terminal, sort_keys=True, separators=(",", ":"))
        comments = [
            {"user": {"login": "someone"}, "body": body},
            {"user": {"login": subject.TRUSTED_RESULT_LOGIN}, "body": "noise"},
            {"user": {"login": subject.TRUSTED_RESULT_LOGIN}, "body": body},
        ]
        with mock.patch.object(subject, "fetch_repository_comments", return_value=comments):
            self.assertTrue(
                subject.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=SHA,
                )
            )

    def test_profile_shape_is_closed(self):
        bad = profile(extra_field=True)
        with self.assertRaisesRegex(subject.GreeceShakeMapProfileActionError, "profile fields drifted"):
            subject._validate_profile(bad)


if __name__ == "__main__":
    unittest.main()
