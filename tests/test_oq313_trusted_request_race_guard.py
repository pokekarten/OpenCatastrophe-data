# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
import unittest


WORKFLOW = Path(".github/workflows/oq313-kosovo-reconstructed-run.yml")


class OQ313TrustedRequestRaceGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_earliest_canonical_owner_request_wins_before_provider_access(self) -> None:
        text = self.text
        guard = "Select earliest canonical trusted request and deduplicate terminal"
        provider = "Fetch exact ESRM20 v1.0 provider snapshot"

        self.assertIn(guard, text)
        self.assertIn("CURRENT_REQUEST_COMMENT_ID: ${{ github.event.comment.id }}", text)
        self.assertIn("REPOSITORY_OWNER: ${{ github.event.repository.owner.login }}", text)
        self.assertIn(
            "from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313_action as request_contract",
            text,
        )
        self.assertIn("request_contract.validate_request(", text)
        self.assertIn('comment.get("author_association") != "OWNER"', text)
        self.assertIn('comment.get("user", {}).get("login") != owner', text)
        self.assertIn("winner_comment_id = min(canonical_requests)[1]", text)
        self.assertIn("current_comment_id != winner_comment_id", text)
        self.assertIn(
            "duplicate trusted request is not earliest canonical OWNER request",
            text,
        )
        self.assertLess(text.index(guard), text.index(provider))

    def test_terminal_dedup_remains_a_second_pre_provider_guard(self) -> None:
        text = self.text
        guard = "Select earliest canonical trusted request and deduplicate terminal"
        provider = "Fetch exact ESRM20 v1.0 provider snapshot"

        self.assertIn("oc-eq1-esrm20-kosovo-oq313-run-result-v1", text)
        self.assertIn("trusted terminal authority drifted", text)
        self.assertIn("skip={'true' if found else 'false'}", text)
        self.assertLess(text.index(guard), text.index(provider))


if __name__ == "__main__":
    unittest.main()
