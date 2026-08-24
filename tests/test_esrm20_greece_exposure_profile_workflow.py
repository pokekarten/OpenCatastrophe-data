# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import unittest


WORKFLOW = Path(".github/workflows/esrm20-greece-exposure-profile.yml")


class GreeceExposureProfileWorkflowTests(unittest.TestCase):
    def test_pre_provider_dedup_gh_api_has_explicit_github_token(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        step_name = "Select earliest canonical trusted request and deduplicate terminal"
        start = text.index(step_name)
        next_step = text.index("      - name:", start + len(step_name))
        dedup_step = text[start:next_step]

        self.assertIn("gh api --paginate --slurp", dedup_step)
        self.assertIn("GH_TOKEN: ${{ github.token }}", dedup_step)
        self.assertLess(
            dedup_step.index("GH_TOKEN: ${{ github.token }}"),
            dedup_step.index("gh api --paginate --slurp"),
        )


if __name__ == "__main__":
    unittest.main()
