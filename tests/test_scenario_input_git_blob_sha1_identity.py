# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from unittest import mock

from scripts import acquire_efehr_esrm20_scenario_v10_event_input_receipts as worker


class ScenarioInputGitBlobIdentityTests(unittest.TestCase):
    def test_git_blob_sha1_is_explicitly_non_security_identity(self) -> None:
        digest = mock.Mock()
        digest.hexdigest.return_value = "git-object-id"

        with mock.patch.object(worker.hashlib, "sha1", return_value=digest) as sha1:
            result = worker._git_blob_sha1(b"abc")

        self.assertEqual(result, "git-object-id")
        sha1.assert_called_once_with(b"blob 3\0abc", usedforsecurity=False)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
