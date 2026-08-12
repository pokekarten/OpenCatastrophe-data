# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path

from scripts import schema_reference as reference


class SchemaReferenceTests(unittest.TestCase):
    def _schema(self) -> dict[str, object]:
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "urn:opencatastrophe:test:synthetic:1",
            "title": "Synthetic <Schema> & reference",
            "description": "Synthetic schema for deterministic reference tests.",
            "$comment": "scripts/validate_synthetic.py is the stronger executable authority.",
            "type": "object",
            "additionalProperties": False,
            "required": ["mode", "payload"],
            "properties": {
                "mode": {"enum": ["alpha", "beta"]},
                "maybe": {"type": ["string", "null"], "maxLength": 12},
                "payload": {"$ref": "#/$defs/payload"},
            },
            "$defs": {
                "payload": {
                    "type": "object",
                    "required": ["value"],
                    "properties": {
                        "value": {"type": "number", "minimum": 0, "maximum": 1},
                        "tags": {
                            "type": "array",
                            "items": {"type": "string", "pattern": "^[a-z]+$"},
                        },
                    },
                }
            },
        }

    def test_reference_is_readable_complete_and_authority_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            schema_dir = Path(tmp) / "schemas"
            schema_dir.mkdir()
            path = schema_dir / "synthetic.schema.json"
            path.write_text(json.dumps(self._schema(), indent=2) + "\n", encoding="utf-8")

            rendered = reference.render_schema_reference(schema_dir)

        self.assertIn(reference.GENERATED_MARKER, rendered)
        self.assertIn("**Schemas represented:** 1", rendered)
        self.assertIn("Synthetic &lt;Schema&gt; &amp; reference", rendered)
        self.assertIn("urn:opencatastrophe:test:synthetic:1", rendered)
        self.assertIn("scripts/validate_synthetic.py", rendered)
        self.assertIn("`mode` — **required**", rendered)
        self.assertIn('`enum`=`["alpha","beta"]`', rendered)
        self.assertIn("type=`string | null`", rendered)
        self.assertIn("#### $defs", rendered)
        self.assertIn("`minimum`=`0`", rendered)
        self.assertIn("`maximum`=`1`", rendered)
        self.assertIn("`pattern`=`^[a-z]+$`", rendered)

    def test_write_check_drift_and_repair_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            schema_dir = root / "schemas"
            schema_dir.mkdir()
            output = root / "docs" / "SCHEMA_REFERENCE.md"
            (schema_dir / "synthetic.schema.json").write_text(
                json.dumps(self._schema(), indent=2) + "\n",
                encoding="utf-8",
            )

            self.assertEqual(reference.write_schema_reference(schema_dir, output), (output,))
            first = output.read_bytes()
            self.assertEqual(reference.write_schema_reference(schema_dir, output), ())
            self.assertEqual(output.read_bytes(), first)
            self.assertTrue(reference.check_schema_reference(schema_dir, output, stream=io.StringIO()))

            output.write_text(output.read_text(encoding="utf-8") + "manual drift\n", encoding="utf-8")
            diagnostics = io.StringIO()
            self.assertFalse(reference.check_schema_reference(schema_dir, output, stream=diagnostics))
            self.assertIn("DRIFT", diagnostics.getvalue())

            reference.write_schema_reference(schema_dir, output)
            self.assertEqual(output.read_bytes(), first)
            self.assertTrue(reference.check_schema_reference(schema_dir, output, stream=io.StringIO()))

    def test_duplicate_schema_keys_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            schema_dir = Path(tmp)
            (schema_dir / "duplicate.schema.json").write_text(
                '{"type":"object","type":"string"}\n',
                encoding="utf-8",
            )
            with self.assertRaises(reference.ProjectionError):
                reference.render_schema_reference(schema_dir)

    def test_empty_schema_set_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(reference.ProjectionError, "no \\*\\.schema\\.json files found"):
                reference.render_schema_reference(Path(tmp))


if __name__ == "__main__":
    unittest.main()
