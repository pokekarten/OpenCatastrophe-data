# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import math
from pathlib import Path
import unittest

from scripts import run_esrm20_mixed_component_numeric_probe as subject

SHA = "a" * 40
WORKFLOW_PATH = (
    Path(__file__).resolve().parents[1]
    / ".github/workflows/esrm20-mixed-component-numeric-probe.yml"
)


def _request(**overrides: object) -> str:
    payload: dict[str, object] = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "issue": subject.SOURCE_ISSUE,
        "target_sha": SHA,
        "requester": "test",
    }
    payload.update(overrides)
    return subject.REQUEST_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))


class MixedComponentNumericProbeTests(unittest.TestCase):
    def test_request_is_exact_sha_fenced(self) -> None:
        parsed = subject.validate_request(
            _request(), expected_issue=subject.SOURCE_ISSUE, execution_sha=SHA
        )
        self.assertEqual(parsed["target_sha"], SHA)

    def test_request_drift_fails_closed(self) -> None:
        bodies = (
            "",
            subject.REQUEST_MARKER + "\n{}",
            _request(target_sha="b" * 40),
            subject.REQUEST_MARKER
            + "\n"
            + json.dumps(
                {
                    "schema_version": subject.REQUEST_SCHEMA_VERSION,
                    "issue": subject.SOURCE_ISSUE,
                    "target_sha": SHA,
                    "requester": "test",
                    "extra": True,
                }
            ),
            subject.REQUEST_MARKER
            + '\n{"schema_version":"x","schema_version":"y"}',
        )
        for body in bodies:
            with self.subTest(body=body):
                with self.assertRaises(subject.MixedComponentNumericProbeError):
                    subject.validate_request(
                        body,
                        expected_issue=subject.SOURCE_ISSUE,
                        execution_sha=SHA,
                    )

    def test_probe_branch_selection_is_exact_and_zero_argument(self) -> None:
        self.assertEqual(
            subject.SELECTED_BRANCHES,
            (
                {
                    "branch_set_id": "CratonModel",
                    "branch_id": "CRParamMidMidSite",
                    "requested_gsim_token": "ESHM20Craton",
                    "native_component": "RotD50",
                    "distance_field": "rrup",
                },
                {
                    "branch_set_id": "Volcanic",
                    "branch_id": "b61",
                    "requested_gsim_token": "LanzanoLuzi2019shallow",
                    "native_component": "GEOMETRIC_MEAN",
                    "distance_field": "rhypo",
                },
            ),
        )
        self.assertEqual(
            subject.SYNTHETIC_CONTEXT,
            {
                "mag": 4.5,
                "vs30": 760.0,
                "rrup_km": 20.0,
                "rhypo_km": 20.0,
            },
        )

    def test_non_finite_numeric_output_fails_closed(self) -> None:
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaises(subject.MixedComponentNumericProbeError):
                    subject._finite(value, field="test")
        self.assertEqual(subject._finite(0.0, field="test"), 0.0)

    def test_workflow_keeps_trusted_trigger_and_publication_guards(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        required_fragments = (
            "github.event.issue.number == 287",
            "github.event.comment.user.login == github.event.repository.owner.login",
            "github.event.comment.author_association == 'OWNER'",
            "oc-eq1-esrm20-mixed-component-numeric-probe-request-v1",
            '.gmm_identity.repository_path == "Hazard/gmpe_logic_tree_5br_slope_geology.xml"',
            '.synthetic_context == {"mag":4.5,"rhypo_km":20,"rrup_km":20,"vs30":760}',
        )
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertEqual(workflow.count(fragment), 1, fragment)


if __name__ == "__main__":
    unittest.main()
