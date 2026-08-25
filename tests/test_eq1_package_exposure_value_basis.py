# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
import unittest


PACKAGE = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "EARTHQUAKE_DATA_PACKAGE.md"
)


class Eq1PackageExposureValueBasisTest(unittest.TestCase):
    def test_runtime_structural_token_is_not_structural_component_cost(self) -> None:
        text = PACKAGE.read_text(encoding="utf-8")

        self.assertIn("`TOTAL_REPL_COST_EUR`", text)
        self.assertIn("`COST_STRUCTURAL_EUR`", text)
        self.assertIn(
            "the exact source/runtime value relation ties this field to source\n"
            "  `TOTAL_REPL_COST_EUR`",
            text,
        )
        self.assertIn(
            "must **not** be read as source\n"
            "  `COST_STRUCTURAL_EUR`",
            text,
        )
        self.assertNotIn(
            "- `structural`: aggregated structural replacement-cost input in EUR;",
            text,
        )

    def test_transform_authority_remains_fail_closed(self) -> None:
        text = PACKAGE.read_text(encoding="utf-8")

        self.assertIn(
            "does **not** establish the exact converter, causal generation rule",
            text,
        )
        self.assertIn(
            "Project-186 source → project-269 runtime exact transform | **BLOCKED**",
            text,
        )


if __name__ == "__main__":
    unittest.main()
