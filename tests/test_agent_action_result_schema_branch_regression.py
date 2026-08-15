# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RESULT_SCHEMA = ROOT / "schemas" / "agent-action-result-v1.schema.json"


class AgentActionResultSchemaBranchRegressionTests(unittest.TestCase):
    def _load_schema(self) -> dict[str, object]:
        return json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))

    def _find_acquisition_branch(
        self,
        schema: dict[str, object],
        *,
        action: str,
        status: str | None,
    ) -> dict[str, object]:
        matches: list[dict[str, object]] = []
        for branch in schema["allOf"]:  # type: ignore[index]
            condition = branch.get("if", {})
            properties = condition.get("properties", {})
            if properties.get("phase") != {"const": "acquisition_receipt"}:
                continue
            if properties.get("action") != {"const": action}:
                continue
            if status is None:
                if "status" in properties:
                    continue
                if condition.get("required") != ["phase", "action"]:
                    continue
            else:
                if properties.get("status") != {"const": status}:
                    continue
                if condition.get("required") != ["phase", "action", "status"]:
                    continue
            matches.append(branch)
        self.assertEqual(
            len(matches),
            1,
            f"expected exactly one acquisition branch for action={action!r}, status={status!r}",
        )
        return matches[0]

    def test_esrm20_group2_blocked_branch_remains_isolated(self) -> None:
        schema = self._load_schema()
        branch = self._find_acquisition_branch(
            schema,
            action="esrm20_event_hazard_group2_receipt",
            status="blocked",
        )
        then_properties = branch["then"]["properties"]
        self.assertEqual(
            then_properties["evidence"],
            {
                "properties": {
                    "esrm20_event_hazard_group2_receipt": {"type": "null"}
                }
            },
        )
        self.assertEqual(
            then_properties["failure_class"],
            {"const": "acquisition_failed"},
        )
        self.assertNotIn("source_issue", then_properties)
        self.assertNotIn("dataset_id", then_properties)
        self.assertNotIn("efehr_eshm20_first_order_receipts", json.dumps(branch, sort_keys=True))

    def test_eshm20_first_order_binding_remains_a_distinct_branch(self) -> None:
        schema = self._load_schema()
        branch = self._find_acquisition_branch(
            schema,
            action="efehr_eshm20_first_order_receipts",
            status=None,
        )
        then_properties = branch["then"]["properties"]
        self.assertEqual(then_properties["source_issue"], {"const": 361})
        self.assertEqual(then_properties["dataset_id"], {"const": "efehr.eshm20"})
        self.assertEqual(
            then_properties["evidence"],
            {"required": ["efehr_eshm20_first_order_receipts"]},
        )
        self.assertNotIn("esrm20_event_hazard_group2_receipt", json.dumps(branch, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
