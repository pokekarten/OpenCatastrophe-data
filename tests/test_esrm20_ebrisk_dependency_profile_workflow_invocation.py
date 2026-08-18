# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import unittest


WORKFLOW = Path(".github/workflows/esrm20-ebrisk-risk-config-dependency-profiles.yml")
MODULE = "scripts.run_esrm20_ebrisk_risk_config_dependency_profiles_action"


class EbriskDependencyProfileWorkflowInvocationTests(unittest.TestCase):
    def test_runner_uses_package_safe_module_invocation(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        execute = text.split("execute-dependency-profiles:", 1)[1].split(
            "publish-dependency-profiles:", 1
        )[0]

        self.assertIn(f"python -m {MODULE} \\", execute)
        self.assertNotIn(
            "python scripts/run_esrm20_ebrisk_risk_config_dependency_profiles_action.py",
            execute,
        )

    def test_closed_runner_arguments_are_preserved(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        execute = text.split("execute-dependency-profiles:", 1)[1].split(
            "publish-dependency-profiles:", 1
        )[0]

        for expected in (
            "--comment-body-env OC_EBRISK_DEP_REQUEST",
            "--expected-issue 281",
            '--execution-sha "$EXECUTION_SHA"',
            '--repository "$GITHUB_REPOSITORY"',
            "--token-env GH_TOKEN",
            '--output "$RESULT_PATH"',
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, execute)


if __name__ == "__main__":
    unittest.main()
