# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import render_public_views as views
from scripts import structured_public_views as structured


class RepositoryJsonProjectionCoverageTests(unittest.TestCase):
    def test_every_repository_json_has_a_projection_family(self) -> None:
        self.assertEqual(views.unsupported_repository_json_paths(), ())

    def test_all_scope_includes_schemas(self) -> None:
        self.assertEqual(
            views._selected_scopes("all"),
            ("landscape", "access", "manifests", "schemas"),
        )

    def test_schema_keyword_labels_are_readable(self) -> None:
        self.assertEqual(structured._label("additionalProperties"), "Additional properties")
        self.assertEqual(structured._label("minItems"), "Min items")
        self.assertEqual(structured._label("allOf"), "All of")
        self.assertEqual(structured._label("$ref"), "$ref")

    def test_schema_projection_is_human_readable(self) -> None:
        payload = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://example.invalid/schema.json",
            "title": "Synthetic schema",
            "type": "object",
            "properties": {
                "value": {
                    "type": "number",
                    "minimum": 0,
                }
            },
            "required": ["value"],
            "additionalProperties": False,
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic.schema.json"
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            rendered = structured.render_structured_markdown(path, payload, kind="schema")

        self.assertIn("# JSON Schema: `synthetic.schema.json`", rendered)
        self.assertIn("Synthetic schema", rendered)
        self.assertIn("## Properties", rendered)
        self.assertIn("**Minimum:** `0`", rendered)
        self.assertIn("- value", rendered)
        self.assertIn("**Additional properties:** `false`", rendered)


if __name__ == "__main__":
    unittest.main()
