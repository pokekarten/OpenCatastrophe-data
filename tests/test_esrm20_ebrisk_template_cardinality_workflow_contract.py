# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "esrm20-ebrisk-template-cardinality.yml"


class EbriskTemplateCardinalityWorkflowContractTests(unittest.TestCase):
    def publish_job(self) -> str:
        text = WORKFLOW.read_text(encoding="utf-8")
        return text.split("  publish-diagnostic:", 1)[1]

    def test_publish_job_is_checkoutless_and_issue_write_only(self) -> None:
        publish = self.publish_job()
        self.assertNotIn("actions/checkout@", publish)
        self.assertIn("permissions:\n      issues: write\n", publish)
        self.assertNotIn("contents: write", publish)

    def test_publish_job_requires_exact_closed_top_level_field_set(self) -> None:
        publish = self.publish_job()
        expected_fields = (
            '"execution_sha"',
            '"external_bytes_persisted"',
            '"historical_group_assignment_authorized"',
            '"model_use_authorized"',
            '"provider_file_bytes_read"',
            '"publication_authorized"',
            '"schema_version"',
            '"source_issue"',
            '"status"',
            '"target_sha"',
            '"template_resolution"',
        )
        key_block = publish.split("(keys == [", 1)[1].split("])", 1)[0]
        self.assertEqual(tuple(line.strip().rstrip(",") for line in key_block.splitlines() if line.strip()), expected_fields)

    def test_publish_job_requires_exact_closed_item_shape(self) -> None:
        publish = self.publish_job()
        self.assertIn(
            '(.template_resolution | all(.[]; (keys == ["basename","state"])))',
            publish,
        )

    def test_publish_job_keeps_authority_ceilings_false(self) -> None:
        publish = self.publish_job()
        for field in (
            "provider_file_bytes_read",
            "external_bytes_persisted",
            "historical_group_assignment_authorized",
            "publication_authorized",
            "model_use_authorized",
        ):
            with self.subTest(field=field):
                self.assertIn(f".{field} == false", publish)


if __name__ == "__main__":
    unittest.main()
