# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts import run_esrm20_scenario_v10_greece_shakemap_openquake3121_runtime_action as subject

SHA = "a" * 40
IMAGE = "sha256:" + "b" * 64


def request_body(**updates):
    payload = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": 285,
        "target_sha": SHA,
        "dataset_id": "efehr.esrm20.scenario-tests.v1.0",
        "grid_receipt_sha256": subject._GRID_SHA256,
        "uncertainty_receipt_sha256": subject._UNCERTAINTY_SHA256,
        "requester": "TEST-OQ3121-SHAKEMAP",
    }
    payload.update(updates)
    return subject.REQUEST_MARKER + "\n" + json.dumps(payload, sort_keys=True)


class _FakeDType:
    def __init__(self, names):
        self.names = tuple(names)


class _FakeField(list):
    def __init__(self, values, *, names=()):
        super().__init__(values)
        self.dtype = _FakeDType(names)


class _FakeNativeArray:
    def __init__(self, rows):
        self.dtype = _FakeDType(("lon", "lat", "vs30", "val", "std"))
        self._fields = {
            "lon": _FakeField([23.0] * rows),
            "lat": _FakeField([38.0] * rows),
            "vs30": _FakeField([760.0] * rows),
            "val": _FakeField([None] * rows, names=subject._EXPECTED_IMTS),
            "std": _FakeField([None] * rows, names=subject._EXPECTED_IMTS),
        }

    def __len__(self):
        return len(self._fields["lon"])

    def __getitem__(self, field):
        return self._fields[field]


class _FakeFiniteResult:
    def __init__(self, values):
        self._values = values

    def all(self):
        return all(value == value and value not in (float("inf"), float("-inf")) for value in self._values)


class _FakeNumpyModule:
    @staticmethod
    def isfinite(values):
        return _FakeFiniteResult(values)


def native_array(rows=subject._EXPECTED_ROW_COUNT):
    return _FakeNativeArray(rows)


class RequestContractTests(unittest.TestCase):
    def test_exact_request_passes(self):
        parsed = subject.validate_request(
            request_body(), expected_issue=285, execution_sha=SHA
        )
        self.assertEqual(parsed["target_sha"], SHA)

    def test_request_cannot_change_receipt(self):
        with self.assertRaisesRegex(
            subject.GreeceShakeMapOpenQuake3121RuntimeError,
            "grid_receipt_sha256 drifted",
        ):
            subject.validate_request(
                request_body(grid_receipt_sha256="0" * 64),
                expected_issue=285,
                execution_sha=SHA,
            )

    def test_duplicate_json_key_is_rejected(self):
        body = (
            subject.REQUEST_MARKER
            + '\n{"schema_version":"x","schema_version":"y"}'
        )
        with self.assertRaisesRegex(
            subject.GreeceShakeMapOpenQuake3121RuntimeError,
            "duplicate JSON key",
        ):
            subject.validate_request(body, expected_issue=285, execution_sha=SHA)


@mock.patch.dict("sys.modules", {"numpy": _FakeNumpyModule()})
class NativeReaderTests(unittest.TestCase):
    def test_expected_native_array_is_bounded(self):
        result = subject._validate_native_array(native_array())
        self.assertEqual(result["native_row_count"], 96_525)
        self.assertEqual(
            result["native_top_level_fields"],
            ["lon", "lat", "vs30", "val", "std"],
        )
        self.assertEqual(result["native_value_imts"], list(subject._EXPECTED_IMTS))
        self.assertTrue(result["native_grid_uncertainty_coordinate_match_verified"])

    def test_wrong_row_count_is_rejected(self):
        with self.assertRaises(subject.NativeReaderRejected):
            subject._validate_native_array(native_array(rows=2))

    def test_nonfinite_coordinates_are_rejected(self):
        data = native_array()
        data["lon"][0] = float("nan")
        with self.assertRaises(subject.NativeReaderRejected):
            subject._validate_native_array(data)

    def test_unbound_reader_gets_two_local_files_and_usgs_xml_kind(self):
        observed = {}

        def reader(kind, grid_path, uncertainty_path):
            observed["kind"] = kind
            observed["grid"] = Path(grid_path).read_bytes()
            observed["uncertainty"] = Path(uncertainty_path).read_bytes()
            return native_array()

        result = subject._native_read_unbound(
            b"grid-bytes", b"uncertainty-bytes", reader=reader
        )
        self.assertEqual(observed["kind"], "usgs_xml")
        self.assertEqual(observed["grid"], b"grid-bytes")
        self.assertEqual(observed["uncertainty"], b"uncertainty-bytes")
        self.assertEqual(result["native_row_count"], 96_525)


class RuntimeStateMachineTests(unittest.TestCase):
    def _fetcher(self):
        receipts = {
            "grid": {
                "role": "usgs_shakemap_grid",
                "retrieved_at": "2026-08-29T07:14:38Z",
                "byte_count": subject.base.GRID_BYTE_COUNT,
                "sha256": subject.base.GRID_SHA256,
                "git_blob_sha1": "21e323dec41b8efb012b2595145fded5fb35fd3a",
                "content_type": "text/plain; charset=utf-8",
                "etag": None,
            },
            "uncertainty": {
                "role": "usgs_shakemap_uncertainty",
                "retrieved_at": "2026-08-29T07:14:41Z",
                "byte_count": subject.base.UNCERTAINTY_BYTE_COUNT,
                "sha256": subject.base.UNCERTAINTY_SHA256,
                "git_blob_sha1": "30d5635260a83cd0ac91ee559d0109ff126a7b57",
                "content_type": "text/plain; charset=utf-8",
                "etag": None,
            },
        }
        return (b"grid", b"uncertainty"), receipts

    @mock.patch.object(subject.base, "_validate_receipts", return_value=None)
    @mock.patch.object(subject.base, "_validate_profile", return_value={})
    def test_pass_requires_all_preconditions_and_native_postconditions(
        self, _validate_profile, _validate_receipts
    ):
        native = {
            "native_row_count": 96_525,
            "native_top_level_fields": ["lon", "lat", "vs30", "val", "std"],
            "native_value_imts": list(subject._EXPECTED_IMTS),
            "native_stddev_imts": list(subject._EXPECTED_IMTS),
            "native_grid_uncertainty_coordinate_match_verified": True,
        }
        result = subject._run_native_with(
            execution_sha=SHA,
            image_digest=IMAGE,
            runtime_verifier=lambda: None,
            fetcher=self._fetcher,
            identity_checker=lambda _g, _u: None,
            profile_checker=lambda _g, _u: {},
            native_reader=lambda _g, _u: native,
        )
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["runtime_source_commit_verified"])
        self.assertTrue(result["byte_identity_verified"])
        self.assertTrue(result["trusted_profile_precondition_verified"])
        self.assertTrue(result["native_reader_acceptance_verified"])

    def test_runtime_identity_failure_stops_before_provider_access(self):
        called = False

        def fetcher():
            nonlocal called
            called = True
            raise AssertionError("provider access must not occur")

        def fail_runtime():
            raise subject.GreeceShakeMapOpenQuake3121RuntimeError("drift")

        result = subject._run_native_with(
            execution_sha=SHA,
            image_digest=IMAGE,
            runtime_verifier=fail_runtime,
            fetcher=fetcher,
            identity_checker=lambda _g, _u: None,
            profile_checker=lambda _g, _u: {},
            native_reader=lambda _g, _u: {},
        )
        self.assertFalse(called)
        self.assertEqual(result["failure_stage"], "runtime_identity")
        self.assertFalse(result["provider_file_bytes_read"])

    @mock.patch.object(subject.base, "_validate_receipts", return_value=None)
    @mock.patch.object(subject.base, "_validate_profile", return_value={})
    def test_native_failure_publishes_no_partial_native_values(
        self, _validate_profile, _validate_receipts
    ):
        def fail_native(_grid, _uncertainty):
            raise subject.NativeReaderRejected("native_reader_rejected")

        result = subject._run_native_with(
            execution_sha=SHA,
            image_digest=IMAGE,
            runtime_verifier=lambda: None,
            fetcher=self._fetcher,
            identity_checker=lambda _g, _u: None,
            profile_checker=lambda _g, _u: {},
            native_reader=fail_native,
        )
        self.assertEqual(result["failure_stage"], "native_reader")
        self.assertTrue(result["native_reader_attempted"])
        self.assertFalse(result["native_reader_acceptance_verified"])
        self.assertIsNone(result["native_row_count"])
        self.assertIsNone(result["native_value_imts"])


class WorkflowContractTests(unittest.TestCase):
    def test_workflow_is_trusted_main_only_and_has_no_pr_trigger(self):
        workflow = (
            Path(__file__).resolve().parents[1]
            / ".github"
            / "workflows"
            / "esrm20-scenario-v10-greece-shakemap-openquake3121-runtime.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("issue_comment:", workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertIn("github.event.comment.author_association == 'OWNER'", workflow)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", workflow)
        self.assertIn("refs/tags/v3.12.1:refs/tags/v3.12.1", workflow)
        self.assertIn("0bb8441aa202cd6ec075bf2044dd4aaeb26919b9", workflow)
        self.assertIn("openquake/engine:3.12.1", workflow)
        self.assertIn("persist-credentials: false", workflow)

    def test_publisher_has_no_checkout_and_rechecks_authority_ceiling(self):
        workflow = (
            Path(__file__).resolve().parents[1]
            / ".github"
            / "workflows"
            / "esrm20-scenario-v10-greece-shakemap-openquake3121-runtime.yml"
        ).read_text(encoding="utf-8")
        publisher = workflow.split("  publish-native-runtime:", 1)[1]
        self.assertNotIn("actions/checkout", publisher)
        self.assertIn("issues: write", publisher)
        self.assertIn(".scientific_validity_verified == false", publisher)
        self.assertIn(".publication_authorized == false", publisher)
        self.assertIn(".model_use_authorized == false", publisher)


if __name__ == "__main__":
    unittest.main()
