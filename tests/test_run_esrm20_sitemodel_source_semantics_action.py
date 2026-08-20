# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest
from unittest import mock

from scripts import run_esrm20_sitemodel_source_semantics_action as action


def git_blob(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


class FakeResponse:
    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0
        self.headers = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, amount: int) -> bytes:
        if self.offset >= len(self.data):
            return b""
        chunk = self.data[self.offset : self.offset + amount]
        self.offset += len(chunk)
        return chunk


class FakeOpener:
    def __init__(self, bodies: dict[str, bytes]):
        self.bodies = bodies
        self.requests: list[str] = []

    def __call__(self, request, timeout):
        del timeout
        url = request.full_url
        self.requests.append(url)
        for path, body in self.bodies.items():
            if action._raw_url(path) == url:
                return FakeResponse(body)
        raise AssertionError(f"unexpected URL: {url}")


class SiteModelSourceSemanticsTests(unittest.TestCase):
    SHA = "a" * 40

    def request_body(self, **updates):
        payload = {
            "schema_version": action.REQUEST_SCHEMA_VERSION,
            "issue": action.SOURCE_ISSUE,
            "target_sha": self.SHA,
            "requester": "unit-test",
        }
        payload.update(updates)
        return action.REQUEST_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))

    def test_git_blob_sha1_matches_canonical_object_formula(self):
        data = b"hello\n"
        self.assertEqual(action._git_blob_sha1(data), git_blob(data))

    def test_request_is_closed_and_target_sha_bound(self):
        parsed = action.validate_request(
            self.request_body(),
            expected_issue=action.SOURCE_ISSUE,
            execution_sha=self.SHA,
        )
        self.assertEqual(parsed["target_sha"], self.SHA)
        with self.assertRaises(action.SiteModelSourceSemanticsError):
            action.validate_request(
                self.request_body(path="README.md"),
                expected_issue=action.SOURCE_ISSUE,
                execution_sha=self.SHA,
            )
        with self.assertRaises(action.SiteModelSourceSemanticsError):
            action.validate_request(
                self.request_body(target_sha="b" * 40),
                expected_issue=action.SOURCE_ISSUE,
                execution_sha=self.SHA,
            )

    def test_request_rejects_duplicate_and_float_overflow_json(self):
        duplicate = (
            action.REQUEST_MARKER
            + '\n{"schema_version":"'
            + action.REQUEST_SCHEMA_VERSION
            + '","issue":291,"target_sha":"'
            + self.SHA
            + '","requester":"a","requester":"b"}'
        )
        with self.assertRaises(action.SiteModelSourceSemanticsError):
            action.validate_request(
                duplicate,
                expected_issue=action.SOURCE_ISSUE,
                execution_sha=self.SHA,
            )
        overflow = (
            action.REQUEST_MARKER
            + '\n{"schema_version":"'
            + action.REQUEST_SCHEMA_VERSION
            + '","issue":291,"target_sha":"'
            + self.SHA
            + '","requester":"a","extra":1e400}'
        )
        with self.assertRaises(action.SiteModelSourceSemanticsError):
            action.validate_request(
                overflow,
                expected_issue=action.SOURCE_ISSUE,
                execution_sha=self.SHA,
            )

    def test_raw_url_is_fixed_to_project_ref_and_allow_list(self):
        url = action._raw_url("README.md")
        self.assertIn("/projects/278/repository/files/README.md/raw", url)
        self.assertIn(action.SOURCE_REF, url)
        with self.assertRaises(action.SiteModelSourceSemanticsError):
            action._raw_url("../README.md")
        with self.assertRaises(action.SiteModelSourceSemanticsError):
            action._raw_url("ExposureReadme.pdf")

    def test_profile_verifies_blobs_before_parsing_and_returns_bounded_facts(self):
        readme = b"CRS notes mention EPSG:4326 and Unknown geology.\nNo raw source return.\n"
        tools = (
            b"import numpy\nimport pyproj\n"
            b"def f():\n    x = -9999\n    return 'WGS84', 'VS30', 'geology', x\n"
        )
        nodes = (
            b"from math import isnan\n"
            b"def node():\n    return 'xvf', 'region', 'slope', 'nodata', None\n"
        )
        targets = (
            ("README.md", git_blob(readme), "text"),
            ("exposure2site/exposure_to_site_tools.py", git_blob(tools), "python"),
            ("exposure2site/node_handler.py", git_blob(nodes), "python"),
        )
        bodies = {item[0]: data for item, data in zip(targets, (readme, tools, nodes))}
        opener = FakeOpener(bodies)
        with (
            mock.patch.object(action, "SOURCE_TARGETS", targets),
            mock.patch.object(action, "_VALIDATE_RESPONSE", lambda response, url: None),
            mock.patch.object(action, "_DECLARED_LENGTH", lambda response, maximum: None),
            mock.patch.object(action, "_SET_RESPONSE_TIMEOUT", lambda response, timeout: None),
            mock.patch.object(action, "_REMAINING", lambda deadline, monotonic: 10.0),
        ):
            profile = action.profile_source_semantics(opener=opener, monotonic=lambda: 1.0)
            action.validate_profile(profile)
        self.assertEqual(profile["file_count"], 3)
        self.assertTrue(profile["provider_source_bytes_read"])
        self.assertTrue(profile["source_semantics_profiled"])
        self.assertFalse(profile["raw_source_returned"])
        self.assertFalse(profile["external_bytes_persisted"])
        self.assertFalse(profile["exact_kosovo_generator_commit_verified"])
        self.assertFalse(profile["crs_coordinate_semantics_verified"])
        self.assertFalse(profile["missingness_semantics_verified"])
        by_path = {item["repository_path"]: item for item in profile["files"]}
        self.assertTrue(by_path["README.md"]["literal_flags"]["epsg_4326_literal"])
        self.assertTrue(
            by_path["exposure2site/exposure_to_site_tools.py"]["literal_flags"][
                "negative_9999_literal"
            ]
        )
        self.assertEqual(
            by_path["exposure2site/exposure_to_site_tools.py"]["import_roots"],
            ["numpy", "pyproj"],
        )
        self.assertNotIn("source_text", by_path["README.md"])
        self.assertNotIn("raw_bytes", by_path["README.md"])

    def test_blob_mismatch_fails_before_utf8_or_ast_semantics(self):
        data = b"not python at all \xff"
        targets = (("README.md", "0" * 40, "text"),)
        opener = FakeOpener({"README.md": data})
        with (
            mock.patch.object(action, "SOURCE_TARGETS", targets),
            mock.patch.object(action, "_VALIDATE_RESPONSE", lambda response, url: None),
            mock.patch.object(action, "_DECLARED_LENGTH", lambda response, maximum: None),
            mock.patch.object(action, "_SET_RESPONSE_TIMEOUT", lambda response, timeout: None),
            mock.patch.object(action, "_REMAINING", lambda deadline, monotonic: 10.0),
        ):
            with self.assertRaisesRegex(
                action.SiteModelSourceSemanticsError, "Git blob identity drifted"
            ):
                action._read_source(
                    "README.md", deadline=20.0, opener=opener, monotonic=lambda: 1.0
                )

    def test_invalid_utf8_and_invalid_python_fail_closed_after_blob_match(self):
        invalid_utf8 = b"\xff"
        invalid_python = b"def broken(:\n"
        for path, data, kind, message in (
            ("README.md", invalid_utf8, "text", "not UTF-8"),
            ("x.py", invalid_python, "python", "does not parse"),
        ):
            targets = ((path, git_blob(data), kind),)
            with mock.patch.object(action, "SOURCE_TARGETS", targets):
                with self.assertRaisesRegex(action.SiteModelSourceSemanticsError, message):
                    action._profile_file(path, data)

    def sample_profile(self):
        readme = b"EPSG:4326 Unknown\n"
        tools = b"import pyproj\nX = -9999\n"
        nodes = b"import math\nY = None\n"
        targets = (
            ("README.md", git_blob(readme), "text"),
            ("exposure2site/exposure_to_site_tools.py", git_blob(tools), "python"),
            ("exposure2site/node_handler.py", git_blob(nodes), "python"),
        )
        with mock.patch.object(action, "SOURCE_TARGETS", targets):
            files = [
                action._profile_file(path, data)
                for (path, _, _), data in zip(targets, (readme, tools, nodes))
            ]
            profile = {
                "schema_version": action.PROFILE_SCHEMA_VERSION,
                "source_issue": action.SOURCE_ISSUE,
                "science_parent": action.SCIENCE_PARENT,
                "project_id": action.PROJECT_ID,
                "project_path": action.PROJECT_PATH,
                "source_ref": action.SOURCE_REF,
                "source_paths": [item[0] for item in targets],
                "files": files,
                "file_count": 3,
                "total_byte_count": sum(item["byte_count"] for item in files),
                "provider_source_bytes_read": True,
                "raw_source_returned": False,
                "source_semantics_profiled": True,
                "external_bytes_persisted": False,
                "exact_kosovo_generator_commit_verified": False,
                "crs_coordinate_semantics_verified": False,
                "missingness_semantics_verified": False,
                "site_model_compatibility_verified": False,
                "publication_authorized": False,
                "model_use_authorized": False,
            }
            action.validate_profile(profile)
            return profile, targets

    def test_profile_validation_rejects_unknown_dynamic_fields(self):
        profile, targets = self.sample_profile()
        mutated = json.loads(json.dumps(profile))
        mutated["files"][0]["unexpected"] = True
        with mock.patch.object(action, "SOURCE_TARGETS", targets):
            with self.assertRaises(action.SiteModelSourceSemanticsError):
                action.validate_profile(mutated)

    def test_terminal_pass_binds_provider_evidence_but_keeps_science_ceilings_false(self):
        profile, targets = self.sample_profile()
        result = {
            **action._base_result(execution_sha=self.SHA),
            "status": "pass",
            "failure_class": None,
            "profile": profile,
            "provider_source_bytes_read": True,
            "source_semantics_profiled": True,
        }
        body = action.RESULT_MARKER + "\n" + json.dumps(result, separators=(",", ":"))
        with mock.patch.object(action, "SOURCE_TARGETS", targets):
            self.assertTrue(action.parse_terminal_result(body, execution_sha=self.SHA))

    def test_foreign_trusted_result_is_fully_validated_before_sha_skip(self):
        bad = {
            **action._base_result(execution_sha="b" * 40),
            "status": "pass",
            "failure_class": None,
            "profile": {"not": "valid"},
            "provider_source_bytes_read": True,
            "source_semantics_profiled": True,
        }
        body = action.RESULT_MARKER + "\n" + json.dumps(bad, separators=(",", ":"))
        with self.assertRaises(action.SiteModelSourceSemanticsError):
            action.parse_terminal_result(body, execution_sha=self.SHA)

    def test_matching_terminal_does_not_short_circuit_later_trusted_validation(self):
        matching = {
            **action._base_result(execution_sha=self.SHA),
            "status": "duplicate",
            "failure_class": None,
            "profile": None,
        }
        matching_body = action.RESULT_MARKER + "\n" + json.dumps(
            matching, separators=(",", ":")
        )
        malformed_body = action.RESULT_MARKER + "\n" + "{}"
        comments = [
            {"user": {"login": action.TRUSTED_RESULT_LOGIN}, "body": matching_body},
            {"user": {"login": action.TRUSTED_RESULT_LOGIN}, "body": malformed_body},
        ]
        with (
            mock.patch.object(action, "_FETCH_COMMENTS", return_value=comments),
            mock.patch.object(action, "profile_source_semantics") as profiler,
        ):
            with self.assertRaises(action.SiteModelSourceSemanticsError):
                action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=self.SHA,
                )
            profiler.assert_not_called()

    def test_execute_duplicate_never_profiles_provider(self):
        with (
            mock.patch.object(action, "has_terminal_result", return_value=True),
            mock.patch.object(action, "profile_source_semantics") as profiler,
        ):
            result = action.execute_profile(
                repository="pokekarten/OpenCatastrophe-data",
                token="x",
                execution_sha=self.SHA,
            )
        self.assertEqual(result["status"], "duplicate")
        profiler.assert_not_called()

    def test_execute_profile_failure_is_atomic_and_has_no_partial_evidence(self):
        with (
            mock.patch.object(action, "has_terminal_result", return_value=False),
            mock.patch.object(
                action,
                "profile_source_semantics",
                side_effect=action.SiteModelSourceSemanticsError("boom"),
            ),
        ):
            result = action.execute_profile(
                repository="pokekarten/OpenCatastrophe-data",
                token="x",
                execution_sha=self.SHA,
            )
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["profile"])
        self.assertFalse(result["provider_source_bytes_read"])
        self.assertFalse(result["source_semantics_profiled"])

    def test_execute_transport_failure_is_sanitized_atomic_blocked_result(self):
        sensitive_detail = "sensitive provider detail"
        with (
            mock.patch.object(action, "has_terminal_result", return_value=False),
            mock.patch.object(
                action,
                "profile_source_semantics",
                side_effect=action.transport.EfehrAcquisitionError(sensitive_detail),
            ),
        ):
            result = action.execute_profile(
                repository="pokekarten/OpenCatastrophe-data",
                token="x",
                execution_sha=self.SHA,
            )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "source_acquisition_or_profile_failure")
        self.assertIsNone(result["profile"])
        self.assertFalse(result["provider_source_bytes_read"])
        self.assertFalse(result["source_semantics_profiled"])
        encoded = json.dumps(result, sort_keys=True, separators=(",", ":"))
        self.assertNotIn(sensitive_detail, encoded)
        self.assertTrue(
            action.parse_terminal_result(
                action.RESULT_MARKER + "\n" + encoded,
                execution_sha=self.SHA,
            )
        )

    def test_workflow_contract_has_trusted_main_and_no_checkout_publisher(self):
        workflow = (
            Path(__file__).resolve().parents[1]
            / ".github"
            / "workflows"
            / "esrm20-sitemodel-source-semantics.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("github.event.issue.number == 291", workflow)
        self.assertIn("github.event.repository.owner.login", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("git rev-parse HEAD", workflow)
        self.assertIn(action.REQUEST_MARKER, workflow)
        self.assertIn(action.RESULT_MARKER, workflow)
        publish = workflow.split("publish-sitemodel-source-semantics:", 1)[1]
        self.assertNotIn("actions/checkout", publish)
        self.assertIn("issues: write", publish)
        self.assertIn("raw_source_returned == false", publish)
        self.assertIn("publication_authorized == false", publish)
        self.assertIn("model_use_authorized == false", publish)
        self.assertIn("wc -c", publish)


if __name__ == "__main__":
    unittest.main()
