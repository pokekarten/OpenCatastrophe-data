# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Keep Swiss crop-hail original replay disabled pending source-access review."""
from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = {
    "swiss-crop-hail-event-alignment.yml": 1,
    "swiss-crop-hail-hdf5-structural-evidence.yml": 1,
    "swiss-crop-hail-n-fields-support.yml": 1,
    "swiss-crop-hail-original-1km-skill-pilot.yml": 1,
    "swiss-crop-hail-original-coarse-skill.yml": 1,
    "swiss-crop-hail-original-zenodo-receipts.yml": 2,
}


class SwissCropHailDocumentedWorkflowBoundaryTests(unittest.TestCase):
    def test_original_steps_disabled_but_offline_tests_enabled(self):
        for name, count in WORKFLOWS.items():
            with self.subTest(workflow=name):
                workflow = yaml.load(
                    (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8"),
                    Loader=yaml.BaseLoader,
                )
                live = []
                for job in workflow["jobs"].values():
                    steps = job["steps"]
                    tests = [step for step in steps
                             if step.get("run", "").startswith("python -m unittest")]
                    self.assertTrue(tests, "offline regression step missing")
                    self.assertTrue(all("if" not in step for step in tests))
                    live.extend(step for step in steps if step.get("run", "").startswith(
                        "python -m research_runners.swiss_crop_hail_"
                    ))
                self.assertEqual(len(live), count)
                for step in live:
                    self.assertEqual(step.get("if"), "${{ false }}",
                                     "documented-only source replay must stay disabled")


if __name__ == "__main__":
    unittest.main()
