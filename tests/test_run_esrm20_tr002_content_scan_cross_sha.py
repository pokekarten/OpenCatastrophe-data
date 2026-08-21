# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest

from scripts import run_esrm20_tr002_content_scan_action as subject

CURRENT_SHA = "1" * 40
PRIOR_SHA = "2" * 40


def blocked_terminal_body(execution_sha: str) -> str:
    result = subject._base_result(execution_sha=execution_sha)
    result.update(
        {
            "status": "blocked",
            "failure_class": "content_extraction_failure",
            "byte_identity_verified": True,
            "text_location_scan_verified": False,
            "scan": None,
        }
    )
    return subject.RESULT_MARKER + "\n" + json.dumps(result, sort_keys=True, separators=(",", ":"))


class Tr002ContentScanCrossShaTests(unittest.TestCase):
    def test_blocked_prior_sha_is_validated_but_not_deduplicated(self) -> None:
        body = blocked_terminal_body(PRIOR_SHA)
        self.assertFalse(subject._parse_terminal_result(body, execution_sha=CURRENT_SHA))

    def test_blocked_same_sha_is_terminal_match(self) -> None:
        body = blocked_terminal_body(PRIOR_SHA)
        self.assertTrue(subject._parse_terminal_result(body, execution_sha=PRIOR_SHA))


if __name__ == "__main__":
    unittest.main()
