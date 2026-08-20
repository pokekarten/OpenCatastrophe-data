# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import run_esrm20_scenario_v10_greece_shakemap_profile_diagnostic_action as predecessor
from scripts import run_esrm20_scenario_v10_greece_shakemap_unit_diagnostic_action as subject


SHA = "a" * 40


def _xml(*fields: tuple[str, str]) -> bytes:
    values = "".join(
        f'<grid_field index="{index}" name="{name}" units="{units}" />'
        for index, (name, units) in enumerate(fields, start=1)
    )
    return f"<shakemap_grid>{values}</shakemap_grid>".encode()


def _request() -> str:
    payload = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": 285,
        "target_sha": SHA,
        "dataset_id": "efehr.esrm20.scenario-tests.v1.0",
        "grid_receipt_sha256": "3c2fe7a2a7182fac999442ce3d88ddfd99004b7f999462ef2327f2eebc1ccd9f",
        "uncertainty_receipt_sha256": "eb08df5ff78f265fb45bf31dbd3dddf4f01bf10632382d4156a2bdf016e46417",
        "requester": "test-runner",
    }
    return subject.REQUEST_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))


class UnitClassificationTests(unittest.TestCase):
    def test_documented_unit_wrong_for_field_is_closed_classification(self) -> None:
        result = subject._classify_member(
            _xml(("LON", "dd"), ("LAT", "dd"), ("PGA", "cms")),
            member="grid",
            allowed_units=subject._EXPECTED_GRID_UNITS,
        )
        self.assertEqual(
            result,
            {
                "member": "grid",
                "field_name": "PGA",
                "unit_relation": "documented_global_unit_wrong_for_field",
            },
        )

    def test_blank_unexpected_is_classified_without_token(self) -> None:
        result = subject._classify_member(
            _xml(("LON", "dd"), ("LAT", "dd"), ("PGA", "")),
            member="grid",
            allowed_units=subject._EXPECTED_GRID_UNITS,
        )
        self.assertEqual(result["unit_relation"], "blank_unexpected")
        self.assertEqual(result["field_name"], "PGA")

    def test_unknown_unit_token_never_escapes(self) -> None:
        secret = "provider-secret-unit-9173"
        result = subject._classify_member(
            _xml(("LON", "dd"), ("LAT", "dd"), ("PGA", secret)),
            member="grid",
            allowed_units=subject._EXPECTED_GRID_UNITS,
        )
        encoded = json.dumps(result, sort_keys=True)
        self.assertEqual(result["unit_relation"], "unrecognized_unit_token")
        self.assertNotIn(secret, encoded)

    def test_grid_precedes_uncertainty_like_production_profiler(self) -> None:
        grid = _xml(("LON", "dd"), ("LAT", "dd"), ("PGA", "cms"))
        uncertainty = _xml(("LON", "dd"), ("LAT", "dd"), ("STDPGA", "cms"))
        result = subject.classify_unit_failure(grid, uncertainty)
        self.assertEqual(result["member"], "grid")
        self.assertEqual(result["field_name"], "PGA")

    def test_uncertainty_is_checked_after_clean_grid(self) -> None:
        grid = _xml(("LON", "dd"), ("LAT", "dd"), ("PGA", "pctg"))
        uncertainty = _xml(("LON", "dd"), ("LAT", "dd"), ("STDPGA", "pctg"))
        result = subject.classify_unit_failure(grid, uncertainty)
        self.assertEqual(
            result,
            {
                "member": "uncertainty",
                "field_name": "STDPGA",
                "unit_relation": "documented_global_unit_wrong_for_field",
            },
        )

    def test_unknown_field_fails_closed(self) -> None:
        with self.assertRaises(subject.ShakeMapUnitDiagnosticError):
            subject._classify_member(
                _xml(("LON", "dd"), ("LAT", "dd"), ("SECRET", "pctg")),
                member="grid",
                allowed_units=subject._EXPECTED_GRID_UNITS,
            )


class ContractTests(unittest.TestCase):
    def test_request_is_exactly_bound(self) -> None:
        result = subject.validate_request(_request(), expected_issue=285, execution_sha=SHA)
        self.assertEqual(result["target_sha"], SHA)

    def test_duplicate_request_key_is_rejected(self) -> None:
        body = _request().replace('"requester":"test-runner"', '"requester":"test-runner","requester":"other"')
        with self.assertRaises(subject.ShakeMapUnitDiagnosticError):
            subject.validate_request(body, expected_issue=285, execution_sha=SHA)

    def test_historical_diagnostic_marker_is_not_reinterpreted(self) -> None:
        old = predecessor.RESULT_MARKER + "\n{}"
        self.assertIsNone(subject.parse_terminal_result(old))

    def test_false_authority_flags_require_actual_booleans(self) -> None:
        result = subject._base_result(SHA)
        result["event_location_inference_authorized"] = 0
        with self.assertRaises(subject.ShakeMapUnitDiagnosticError):
            subject._validate_terminal_result(result)

    def test_classified_result_has_only_closed_diagnostic_values(self) -> None:
        result = subject._base_result(SHA)
        result.update(
            {
                "failure_stage": "profile",
                "failure_code": "unsupported_grid_field_units",
                "provider_file_bytes_read": True,
                "byte_identity_verified": True,
                "profile_failure_reproduced": True,
                "provider_unit_metadata_classified": True,
                "unit_diagnostic": {
                    "member": "grid",
                    "field_name": "PGA",
                    "unit_relation": "unrecognized_unit_token",
                },
            }
        )
        self.assertEqual(subject._validate_terminal_result(result), SHA)
        result["unit_diagnostic"]["unit_relation"] = "provider-secret"
        with self.assertRaises(subject.ShakeMapUnitDiagnosticError):
            subject._validate_terminal_result(result)

    def test_production_path_reproduces_unit_failure_before_classifying(self) -> None:
        def fetcher():
            return ((b"grid", b"uncertainty"), {})

        def profile_func(_grid: bytes, _uncertainty: bytes):
            raise subject.base.ShakeMapProfileError("unsupported_grid_field_units")

        classified = {
            "member": "grid",
            "field_name": "PGA",
            "unit_relation": "unrecognized_unit_token",
        }
        with mock.patch.object(subject.base, "_validate_receipts", return_value=None):
            result = subject._run_with(
                execution_sha=SHA,
                fetcher=fetcher,
                profile_func=profile_func,
                classifier=lambda _grid, _uncertainty: classified,
            )
        self.assertEqual(result["failure_code"], "unsupported_grid_field_units")
        self.assertTrue(result["profile_failure_reproduced"])
        self.assertTrue(result["provider_unit_metadata_classified"])
        self.assertEqual(result["unit_diagnostic"], classified)

    def test_other_profile_failure_is_not_reclassified(self) -> None:
        def fetcher():
            return ((b"grid", b"uncertainty"), {})

        def profile_func(_grid: bytes, _uncertainty: bytes):
            raise subject.base.ShakeMapProfileError("foreign_xml_namespace")

        classifier = mock.Mock()
        with mock.patch.object(subject.base, "_validate_receipts", return_value=None):
            result = subject._run_with(
                execution_sha=SHA,
                fetcher=fetcher,
                profile_func=profile_func,
                classifier=classifier,
            )
        self.assertEqual(result["failure_code"], "precondition_profile_failure_drift")
        classifier.assert_not_called()


if __name__ == "__main__":
    unittest.main()
