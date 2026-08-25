# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import unittest

from scripts import run_eshm20_source_model_trt_profiles_action as subject

EXECUTION_SHA = "1" * 40
WORKFLOW_PATH = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "eshm20-source-model-trt-profiles.yml"
)


def valid_result() -> dict:
    source_count = subject.EXPECTED_CHILD_COUNT
    aggregate = {
        "schema_version": subject.profiler.AGGREGATE_SCHEMA_VERSION,
        "source_issue": subject.SOURCE_ISSUE,
        "control_issue": subject.profiler.CONTROL_ISSUE,
        "dataset_id": subject.DATASET_ID,
        "child_count": subject.EXPECTED_CHILD_COUNT,
        "child_paths_sha256": subject.EXPECTED_PATHS_SHA256,
        "source_count": source_count,
        "source_type_counts": {"pointSource": source_count},
        "tectonic_region_type_counts": {"Active Shallow Crust": source_count},
        "trt_provenance_counts": {"direct_source": source_count},
        "unique_source_types": ["pointSource"],
        "unique_tectonic_region_types": ["Active Shallow Crust"],
        "receipt_set_locator": {
            "result_comment_id": subject.RECEIPT_RESULT_COMMENT_ID,
            "run_id": subject.RECEIPT_RESULT_RUN_ID,
            "execution_sha": subject.RECEIPT_RESULT_EXECUTION_SHA,
            "provider_commit": subject.COMMIT_SHA,
        },
        "receipt_payload_identities_verified": True,
        "canonical_414_ledger_binding_verified": True,
        "source_structure_profile_verified": True,
        "source_physics_validity_verified": False,
        "source_gsim_trt_compatibility_verified": False,
        "branch_weight_validity_verified": False,
        "numerical_hazard_reproduction_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    return {
        **subject._base_result(execution_sha=EXECUTION_SHA),
        "status": "pass",
        "failure_class": None,
        "aggregate_profile": aggregate,
        "provider_file_bytes_read": True,
        "raw_xml_returned": False,
        "canonical_414_ledger_binding_verified": True,
    }


def publisher_filter() -> str:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    start_marker = 'jq -e --arg sha "$EXECUTION_SHA" \'\n'
    start = workflow.index(start_marker) + len(start_marker)
    end = workflow.index("\n          ' >/dev/null", start)
    return workflow[start:end]


def publisher_accepts(result: dict) -> bool:
    completed = subprocess.run(
        ["jq", "-e", "--arg", "sha", EXECUTION_SHA, publisher_filter()],
        input=json.dumps(result, sort_keys=True, separators=(",", ":")),
        text=True,
        capture_output=True,
        check=False,
        timeout=5,
    )
    return completed.returncode == 0


class Eshm20SourceModelTrtPublisherTests(unittest.TestCase):
    def test_valid_bounded_result_is_accepted(self) -> None:
        self.assertTrue(publisher_accepts(valid_result()))

    def test_unique_source_types_must_match_source_count_keys(self) -> None:
        result = copy.deepcopy(valid_result())
        result["aggregate_profile"]["unique_source_types"] = ["forgedSource"]
        self.assertFalse(publisher_accepts(result))

    def test_unique_trts_must_match_trt_count_keys(self) -> None:
        result = copy.deepcopy(valid_result())
        result["aggregate_profile"]["unique_tectonic_region_types"] = ["forgedTRT"]
        self.assertFalse(publisher_accepts(result))

    def test_unknown_source_type_is_rejected_even_when_counts_reconcile(self) -> None:
        result = copy.deepcopy(valid_result())
        result["aggregate_profile"]["source_type_counts"] = {"forgedSource": 51}
        result["aggregate_profile"]["unique_source_types"] = ["forgedSource"]
        self.assertFalse(publisher_accepts(result))

    def test_unknown_trt_provenance_is_rejected(self) -> None:
        result = copy.deepcopy(valid_result())
        result["aggregate_profile"]["trt_provenance_counts"] = {"forged": 51}
        self.assertFalse(publisher_accepts(result))

    def test_control_bearing_trt_label_is_rejected(self) -> None:
        result = copy.deepcopy(valid_result())
        result["aggregate_profile"]["tectonic_region_type_counts"] = {"bad\u0000TRT": 51}
        result["aggregate_profile"]["unique_tectonic_region_types"] = ["bad\u0000TRT"]
        self.assertFalse(publisher_accepts(result))

    def test_authority_widening_is_rejected(self) -> None:
        result = copy.deepcopy(valid_result())
        result["publication_authorized"] = True
        self.assertFalse(publisher_accepts(result))


if __name__ == "__main__":
    unittest.main()
