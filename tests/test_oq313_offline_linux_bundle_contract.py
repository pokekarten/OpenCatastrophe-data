# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/oq313-offline-linux-bundle.yml"
LAUNCHER = ROOT / "scripts/run_oq313_offline_linux_runtime.sh"
EXPECTED_DIGEST = "sha256:dcfb88b3f9feb96eddee648690253492ba252619703ff48477affdbbb3c1151c"


class Oq313OfflineLinuxBundleContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = WORKFLOW.read_text(encoding="utf-8")
        self.launcher = LAUNCHER.read_text(encoding="utf-8")

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
        blocked_home = "/" + "home/" + "openquake/"
        self.assertNotIn(blocked_home, self.workflow)
        self.assertIn("rm -rf /root/.cache/pip", self.workflow)

    def test_portable_launcher_never_requires_host_root_alias(self) -> None:
        self.assertIn('OQ_SOURCE="$ROOTFS/oq-engine"', self.launcher)
        self.assertIn('PYTHONPATH="$OC_SOURCE:$OQ_SOURCE:$SITE"', self.launcher)
        self.assertNotIn("ln -s", self.launcher)
        self.assertNotIn("safe.directory /oq-engine", self.launcher)
        self.assertNotIn("requires root permission", self.launcher)
        self.assertNotIn('Path("/oq-engine/openquake")', self.workflow)


if __name__ == "__main__":
    unittest.main()
