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
    def _schema(self, *, title: str = "Synthetic <Schema> & reference") -> dict[str, object]:
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "urn:opencatastrophe:test:synthetic:1",
            "title": title,
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

    def _write_schema(self, schema_dir: Path, name: str, payload: dict[str, object] | None = None) -> Path:
        path = schema_dir / f"{name}.schema.json"
        path.write_text(json.dumps(payload or self._schema(), indent=2) + "\n", encoding="utf-8")
        return path

    def test_projection_is_readable_complete_and_authority_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            schema_dir = Path(tmp) / "schemas"
            schema_dir.mkdir()
            path = self._write_schema(schema_dir, "synthetic")
            rendered = reference.render_schema_markdown(path)

        self.assertIn(reference.GENERATED_MARKER, rendered)
        self.assertIn("Canonical source: schemas/synthetic.schema.json", rendered)
        self.assertIn("Renderer: scripts/schema_reference.py", rendered)
        self.assertIn("Synthetic &lt;Schema&gt; &amp; reference", rendered)
        self.assertIn("urn:opencatastrophe:test:synthetic:1", rendered)
        self.assertIn("scripts/validate_synthetic.py", rendered)
        self.assertIn("`mode` — **required**", rendered)
        self.assertIn('`enum`=`["alpha","beta"]`', rendered)
        self.assertIn("type=`string | null`", rendered)
        self.assertIn("### $defs", rendered)
        self.assertIn("`minimum`=`0`", rendered)
        self.assertIn("`maximum`=`1`", rendered)
        self.assertIn("`pattern`=`^[a-z]+$`", rendered)

    def test_write_creates_one_deterministic_projection_per_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            schema_dir = Path(tmp) / "schemas"
            schema_dir.mkdir()
            self._write_schema(schema_dir, "alpha", self._schema(title="Alpha"))
            self._write_schema(schema_dir, "beta", self._schema(title="Beta"))

            changed = reference.write_schema_reference(schema_dir)
            alpha = schema_dir / "alpha.schema.md"
            beta = schema_dir / "beta.schema.md"
            self.assertEqual(set(changed), {alpha, beta})
            first = {path.name: path.read_bytes() for path in (alpha, beta)}

            self.assertEqual(reference.write_schema_reference(schema_dir), ())
            self.assertEqual({path.name: path.read_bytes() for path in (alpha, beta)}, first)
            self.assertTrue(reference.check_schema_reference(schema_dir, stream=io.StringIO()))

    def test_manual_drift_and_missing_projection_fail_closed_and_repair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            schema_dir = Path(tmp) / "schemas"
            schema_dir.mkdir()
            self._write_schema(schema_dir, "synthetic")
            reference.write_schema_reference(schema_dir)
            output = schema_dir / "synthetic.schema.md"
            canonical = output.read_bytes()

            output.write_text(output.read_text(encoding="utf-8") + "manual drift\n", encoding="utf-8")
            diagnostics = io.StringIO()
            self.assertFalse(reference.check_schema_reference(schema_dir, stream=diagnostics))
            self.assertIn("DRIFT", diagnostics.getvalue())

            reference.write_schema_reference(schema_dir)
            self.assertEqual(output.read_bytes(), canonical)

            output.unlink()
            diagnostics = io.StringIO()
            self.assertFalse(reference.check_schema_reference(schema_dir, stream=diagnostics))
            self.assertIn("MISSING", diagnostics.getvalue())
            reference.write_schema_reference(schema_dir)
            self.assertEqual(output.read_bytes(), canonical)

    def test_generated_orphan_fails_check_and_write_removes_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            schema_dir = Path(tmp) / "schemas"
            schema_dir.mkdir()
            self._write_schema(schema_dir, "synthetic")
            reference.write_schema_reference(schema_dir)
            orphan = schema_dir / "removed.schema.md"
            orphan.write_text(f"<!-- {reference.GENERATED_MARKER} -->\n", encoding="utf-8")

            diagnostics = io.StringIO()
            self.assertFalse(reference.check_schema_reference(schema_dir, stream=diagnostics))
            self.assertIn("ORPHAN", diagnostics.getvalue())
            changed = reference.write_schema_reference(schema_dir)
            self.assertIn(orphan, changed)
            self.assertFalse(orphan.exists())
            self.assertTrue(reference.check_schema_reference(schema_dir, stream=io.StringIO()))

    def test_write_refuses_to_delete_unmarked_orphan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            schema_dir = Path(tmp) / "schemas"
            schema_dir.mkdir()
            self._write_schema(schema_dir, "synthetic")
            orphan = schema_dir / "manual.schema.md"
            orphan.write_text("manual file\n", encoding="utf-8")
            with self.assertRaisesRegex(reference.ProjectionError, "refusing to delete orphan"):
                reference.write_schema_reference(schema_dir)
            self.assertTrue(orphan.exists())

    def test_duplicate_schema_keys_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            schema_dir = Path(tmp)
            path = schema_dir / "duplicate.schema.json"
            path.write_text('{"type":"object","type":"string"}\n', encoding="utf-8")
            with self.assertRaises(reference.ProjectionError):
                reference.render_schema_markdown(path)

    def test_empty_schema_set_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(reference.ProjectionError, "no \\*\\.schema\\.json files found"):
                reference.write_schema_reference(Path(tmp))


if __name__ == "__main__":
    unittest.main()
