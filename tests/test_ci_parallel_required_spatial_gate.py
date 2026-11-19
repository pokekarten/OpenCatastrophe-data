# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Prove independent CI jobs run in parallel without losing the spatial gate.

Checks a workflow *structure*, not a hosted job result. The GitHub Actions
Required job still needs actual execution and must complete successfully.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
CI_FILE = ROOT / ".github" / "workflows" / "ci.yml"
REQUIRED_JOBS = frozenset({
    "check",
    "eu-flood-spatial",
    "glofas-acquisition",
    "luxembourg-lidar-inset-spatial",
    "cems-geotiff-profile",
    "reuse",
    "dependency-review",
})


def required_spatial_graph_errors(document: object) -> list[str]:
    """Reject accidentally sequential tests or removal of mandatory gates."""
    if not isinstance(document, dict) or not isinstance(document.get("jobs"), dict):
        return ["workflow needs a jobs mapping"]
    jobs = document["jobs"]
    check = jobs.get("check")
    required = jobs.get("required")
    if not isinstance(check, dict) or not isinstance(required, dict):
        return ["check and required jobs must both exist"]
    errors: list[str] = []
    if check.get("name") != "Python ${{ matrix.python-version }}":
        errors.append("Python matrix check name changed")
    if required.get("name") != "Required":
        errors.append("stable Required status context changed")
    if required.get("if") != "always()":
        errors.append("Required must execute even on dependency failures")

    check_needs = check.get("needs", [])
    if isinstance(check_needs, str):
        check_needs = [check_needs]
    if not isinstance(check_needs, list):
        errors.append("check.needs must be an optional list")
    elif "eu-flood-spatial" in check_needs:
        errors.append("Python tests must not wait for independent spatial tests")

    needs = required.get("needs")
    if not isinstance(needs, list):
        errors.append("Required must declare explicit dependency list")
    else:
        missing = REQUIRED_JOBS.difference(needs)
        if missing:
            errors.append("Required lacks dependency: " + ", ".join(sorted(missing)))
    steps = required.get("steps")
    if not isinstance(steps, list):
        return errors + ["Required needs a verification step"]
    matches = [s for s in steps if isinstance(s, dict) and s.get("name") == "Verify required jobs"]
    if len(matches) != 1:
        return errors + ["Required needs exactly one Verify required jobs step"]
    step = matches[0]
    env = step.get("env")
    if not isinstance(env, dict) or env.get("EU_FLOOD_SPATIAL_RESULT") != "${{ needs.eu-flood-spatial.result }}":
        errors.append("Required must read the direct eu-flood-spatial result")
    script = step.get("run")
    if not isinstance(script, str) or 'test "$EU_FLOOD_SPATIAL_RESULT" = "success"' not in script:
        errors.append("Required must fail when eu-flood-spatial is not successful")
    return errors


class RequiredSpatialGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = yaml.load(CI_FILE.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

    def test_repository_graph_keeps_required_gates_while_parallelizing(self) -> None:
        self.assertEqual(required_spatial_graph_errors(self.workflow), [])

    def test_missing_direct_spatial_dependency_is_rejected(self) -> None:
        changed = deepcopy(self.workflow)
        changed["jobs"]["required"]["needs"].remove("eu-flood-spatial")
        self.assertIn("Required lacks dependency: eu-flood-spatial", required_spatial_graph_errors(changed))

    def test_ignoring_spatial_failure_is_rejected(self) -> None:
        changed = deepcopy(self.workflow)
        step = changed["jobs"]["required"]["steps"][0]
        step["run"] = step["run"].replace('test "$EU_FLOOD_SPATIAL_RESULT" = "success"', ":")
        self.assertIn("Required must fail when eu-flood-spatial is not successful", required_spatial_graph_errors(changed))

    def test_wrong_spatial_result_source_is_rejected(self) -> None:
        changed = deepcopy(self.workflow)
        changed["jobs"]["required"]["steps"][0]["env"]["EU_FLOOD_SPATIAL_RESULT"] = "success"
        self.assertIn("Required must read the direct eu-flood-spatial result", required_spatial_graph_errors(changed))

    def test_unnecessary_serial_dependency_is_rejected(self) -> None:
        changed = deepcopy(self.workflow)
        changed["jobs"]["check"]["needs"] = ["eu-flood-spatial"]
        self.assertIn("Python tests must not wait for independent spatial tests", required_spatial_graph_errors(changed))

    def test_required_always_runs_and_keeps_stable_context(self) -> None:
        changed = deepcopy(self.workflow)
        changed["jobs"]["required"]["if"] = "success()"
        changed["jobs"]["required"]["name"] = "Required reduced"
        errors = required_spatial_graph_errors(changed)
        self.assertIn("Required must execute even on dependency failures", errors)
        self.assertIn("stable Required status context changed", errors)


if __name__ == "__main__":
    unittest.main()
