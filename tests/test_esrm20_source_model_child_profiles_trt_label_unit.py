# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
import unittest

from scripts import profile_esrm20_source_model_children as profiler
from scripts import run_esrm20_source_model_child_profiles_action as action


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/esrm20-source-model-child-profiles.yml"


class TrtLabelUnitContractTests(unittest.TestCase):
    def test_python_contract_counts_multibyte_trt_labels_as_characters(self) -> None:
        at_limit = "é" * profiler.MAX_TRT_CHARS
        over_limit = at_limit + "é"

        self.assertEqual(len(at_limit), 256)
        self.assertEqual(len(at_limit.encode("utf-8")), 512)
        self.assertEqual(profiler._safe_trt(at_limit, "test tectonicRegion"), at_limit)
        with self.assertRaisesRegex(
            profiler.SourceModelContentProfileError, "exceeds bounds"
        ):
            profiler._safe_trt(over_limit, "test tectonicRegion")

        validated, total = action._validate_positive_count_map(
            {at_limit: 1},
            label="tectonic-region",
            maximum_items=profiler.MAX_UNIQUE_TRTS_PER_FILE,
        )
        self.assertEqual(validated, {at_limit: 1})
        self.assertEqual(total, 1)
        with self.assertRaisesRegex(
            action.SourceModelChildProfileActionError, "label is invalid"
        ):
            action._validate_positive_count_map(
                {over_limit: 1},
                label="tectonic-region",
                maximum_items=profiler.MAX_UNIQUE_TRTS_PER_FILE,
            )

    def test_publisher_uses_the_same_character_unit_for_trt_labels(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        start = workflow.index("all(.tectonic_region_type_counts | to_entries[];")
        end = workflow.index(
            "([.tectonic_region_type_counts[]] | add)",
            start,
        )
        trt_validation = workflow[start:end]

        self.assertIn("(.key | length) >= 1", trt_validation)
        self.assertIn("(.key | length) <= 256", trt_validation)
        self.assertNotIn("utf8bytelength", trt_validation)


if __name__ == "__main__":
    unittest.main()
