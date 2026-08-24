# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/oq313-offline-linux-bundle.yml"
EXPECTED_DIGEST = "sha256:dcfb88b3f9feb96eddee648690253492ba252619703ff48477affdbbb3c1151c"


class Oq313OfflineLinuxBundleContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_bootstrap_image_is_immutable_and_fail_closed(self) -> None:
        self.assertIn(f"BASE_IMAGE: openquake/engine@{EXPECTED_DIGEST}", self.workflow)
        self.assertIn(f"EXPECTED_BOOTSTRAP_DIGEST: {EXPECTED_DIGEST}", self.workflow)
        self.assertIn('test "$BOOTSTRAP_DIGEST" = "$EXPECTED_BOOTSTRAP_DIGEST"', self.workflow)
        self.assertIn("ARG BASE_IMAGE\n          FROM ${BASE_IMAGE}", self.workflow)
        self.assertIn('--build-arg BASE_IMAGE="$BASE_IMAGE"', self.workflow)
        self.assertNotIn("BASE_IMAGE: openquake/engine:3.13.0", self.workflow)
        self.assertNotIn("FROM openquake/engine:3.13.0", self.workflow)

    def test_rootfs_is_probed_but_not_distributed(self) -> None:
        self.assertIn('"rootfs_distributed": False', self.workflow)
        self.assertIn('"rootfs_redistribution_authorized": False', self.workflow)
        self.assertIn('"$OUT/offline-probe.sh"', self.workflow)
        self.assertIn("rootfs_distributed: `false`", self.workflow)
        self.assertNotIn("actions/upload-artifact@", self.workflow)
        self.assertNotIn("artifact-url", self.workflow)

    def test_tracked_workflow_has_no_user_home_literal(self) -> None:
        self.assertNotIn("/home/openquake/", self.workflow)
        self.assertIn("rm -rf /root/.cache/pip", self.workflow)


if __name__ == "__main__":
    unittest.main()
