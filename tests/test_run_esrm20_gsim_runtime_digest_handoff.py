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


class Esrm20RuntimeDigestHandoffTests(unittest.TestCase):
    def test_cli_forwards_digest_to_reviewed_runtime_without_private_helper(self) -> None:
        self.assertFalse(hasattr(subject._runtime, "_validate_image_digest"))
        request = subject.REQUEST_MARKER + "\n" + json.dumps(
            {
                "schema_version": subject.REQUEST_SCHEMA_VERSION,
                "issue": subject.SOURCE_ISSUE,
                "target_sha": EXECUTION_SHA,
                "requester": "unit-test",
            },
            separators=(",", ":"),
        )

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            with mock.patch.dict(
                os.environ,
                {"OC_REQUEST": request, "OC_IMAGE_DIGEST": IMAGE_DIGEST},
                clear=False,
            ), mock.patch.object(
                subject,
                "run_reference_runtime",
                return_value={"status": "pass"},
            ) as runtime:
                exit_code = subject.main(
                    [
                        "--comment-body-env",
                        "OC_REQUEST",
                        "--expected-issue",
                        str(subject.SOURCE_ISSUE),
                        "--execution-sha",
                        EXECUTION_SHA,
                        "--runtime-image-digest-env",
                        "OC_IMAGE_DIGEST",
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(exit_code, 0)
            runtime.assert_called_once_with(
                execution_sha=EXECUTION_SHA,
                image_digest=IMAGE_DIGEST,
            )
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), {"status": "pass"})


if __name__ == "__main__":
    unittest.main()
