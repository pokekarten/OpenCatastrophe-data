# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import run_esrm20_gsim_reference_runtime as subject

EXECUTION_SHA = "1" * 40
IMAGE_DIGEST = "sha256:" + "a" * 64


class Esrm20RuntimeImageDigestRegressionTests(unittest.TestCase):
    def test_adapter_reuses_reviewed_digest_syntax(self) -> None:
        self.assertEqual(subject._validate_image_digest(IMAGE_DIGEST), IMAGE_DIGEST)
        for invalid in (
            None,
            True,
            "",
            "a" * 64,
            "sha256:" + "a" * 63,
            "sha256:" + "A" * 64,
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(
                    subject.Esrm20GsimReferenceRuntimeError,
                    "runtime image digest is invalid",
                ):
                    subject._validate_image_digest(invalid)

    def test_adapter_fails_closed_if_reviewed_digest_surface_disappears(self) -> None:
        with mock.patch.object(subject._runtime, "_DIGEST_RE", None):
            with self.assertRaisesRegex(
                subject.Esrm20GsimReferenceRuntimeError,
                "image-digest syntax surface drifted",
            ):
                subject._validate_image_digest(IMAGE_DIGEST)

    def test_execution_cli_no_longer_calls_nonexistent_digest_helper(self) -> None:
        request_env = "OC_TEST_ESRM20_RUNTIME_REQUEST"
        digest_env = "OC_TEST_ESRM20_RUNTIME_DIGEST"
        result = {"schema_version": subject.SCHEMA_VERSION, "status": "synthetic-test"}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            with (
                mock.patch.dict(
                    os.environ,
                    {request_env: "synthetic-request", digest_env: IMAGE_DIGEST},
                    clear=False,
                ),
                mock.patch.object(subject, "validate_request") as validate,
                mock.patch.object(subject, "run_reference_runtime", return_value=result) as run,
            ):
                status = subject.main(
                    [
                        "--comment-body-env",
                        request_env,
                        "--expected-issue",
                        str(subject.SOURCE_ISSUE),
                        "--execution-sha",
                        EXECUTION_SHA,
                        "--runtime-image-digest-env",
                        digest_env,
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(status, 0)
            validate.assert_called_once_with(
                "synthetic-request",
                expected_issue=subject.SOURCE_ISSUE,
                execution_sha=EXECUTION_SHA,
            )
            run.assert_called_once_with(
                execution_sha=EXECUTION_SHA,
                image_digest=IMAGE_DIGEST,
            )
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), result)


if __name__ == "__main__":
    unittest.main()
