# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_agent_action_result as validator


ROOT = Path(__file__).resolve().parents[1]
RESULT_SCHEMA = ROOT / "schemas" / "agent-action-result-v1.schema.json"


class DwdMetadataResultReviewRegressions(unittest.TestCase):
    def _metadata_receipt(self, *, archive_member_count: int) -> dict[str, object]:
        return {
            "schema_version": validator.DWD_METADATA_SCHEMA_VERSION,
            "dataset_id": validator.DWD_METADATA_DATASET_ID,
            "source_issue": validator.DWD_METADATA_SOURCE_ISSUE,
            "requested_url": validator.DWD_METADATA_SOURCE_URL,
            "final_url": validator.DWD_METADATA_SOURCE_URL,
            "filename": validator.DWD_METADATA_FILENAME,
            "retrieved_at": "2026-08-12T10:00:00Z",
            "byte_count": 1,
            "sha256": "0" * 64,
            "content_type": "application/zip",
            "last_modified": None,
            "etag": None,
            "archive_member_count": archive_member_count,
            "archive_uncompressed_bytes": 3,
            "station_id": validator.DWD_METADATA_STATION_ID,
            "required_metadata_families": sorted(validator.REQUIRED_METADATA_FAMILIES),
            "metadata_members": [
                {"path": "Metadaten_Geraete_00003.txt", "family": "equipment"},
                {"path": "Metadaten_Geographie_00003.txt", "family": "geography"},
                {"path": "Metadaten_Parameter_00003.txt", "family": "parameter"},
            ],
            "temporal_coverage_status": "unverified",
            "external_bytes_persisted": False,
            "publication_authorized": False,
        }

    def test_acquisition_phase_portable_schema_excludes_sample_audit(self) -> None:
        schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))
        matching_rules = [
            rule
            for rule in schema["allOf"]
            if rule.get("if")
            == {
                "properties": {"phase": {"const": "acquisition_receipt"}},
                "required": ["phase"],
            }
        ]
        self.assertEqual(len(matching_rules), 1)
        allowed_actions = matching_rules[0]["then"]["properties"]["action"]["enum"]
        self.assertEqual(
            set(allowed_actions),
            {
                "acquisition_receipt",
                "dwd_metadata_receipt",
                "efehr_readme_receipt",
                "efehr_eshm20_tree_metadata",
            },
        )
        self.assertNotIn("sample_audit", allowed_actions)

    def test_metadata_member_evidence_cannot_exceed_archive_member_count(self) -> None:
        receipt = self._metadata_receipt(archive_member_count=1)
        with self.assertRaisesRegex(
            validator.ResultError,
            "metadata_members cannot exceed archive_member_count",
        ):
            validator.validate_dwd_metadata_receipt(receipt)

    def test_metadata_member_evidence_count_equal_to_archive_count_is_valid(self) -> None:
        receipt = self._metadata_receipt(archive_member_count=3)
        self.assertIs(validator.validate_dwd_metadata_receipt(receipt), receipt)


if __name__ == "__main__":
    unittest.main()
