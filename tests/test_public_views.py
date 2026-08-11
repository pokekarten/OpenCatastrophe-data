# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path

from scripts import render_public_views as views


class PublicViewTests(unittest.TestCase):
    def _payload(self) -> dict[str, object]:
        return {
            "schema_version": "1.0.0",
            "purpose": "Non-admission synthetic projection fixture.",
            "review_date": "2026-08-10",
            "entries": [
                {
                    "candidate_id": "synthetic.example.v1",
                    "name": "Synthetic <Example> & test",
                    "provider": "Example & Research",
                    "categories": ["hazard_context", "validation"],
                    "spatial_scope": "synthetic global",
                    "temporal_scope": "synthetic period",
                    "resolution_or_granularity": "one synthetic record",
                    "potential_roles": ["projection_test", "human_readability"],
                    "authoritative_url": "https://example.invalid/public?dataset=synthetic&v=1",
                    "access_class_hint": "public_catalog",
                    "candidate_status": "evidence_checked",
                    "rights_review_status": "not_reviewed",
                    "scientific_review_status": "not_reviewed",
                    "admission_status": "not_admitted",
                    "note": "Synthetic note with <markup> & punctuation.",
                }
            ],
        }

    def _structured_payload(self) -> dict[str, object]:
        return {
            "schema_version": "1.0.0",
            "record_id": "synthetic.structured.v1",
            "documentation_url": "https://example.invalid/docs?x=1&y=2",
            "enabled": False,
            "optional": None,
            "limit": 3,
            "nested": {
                "note": "Literal <tag> & markdown *text* `code`.",
                "items": ["alpha", "beta"],
            },
            "objects": [
                {"name": "first", "value": 1.25},
                {"name": "second", "value": 2.5},
            ],
        }

    def test_markdown_projection_carries_every_landscape_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sources-synthetic.json"
            payload = self._payload()
            path.write_text(json.dumps(payload), encoding="utf-8")
            rendered = views.render_landscape_markdown(path, payload)

        entry = payload["entries"][0]
        for key, value in entry.items():
            with self.subTest(field=key):
                if isinstance(value, list):
                    for item in value:
                        self.assertIn(item, rendered)
                elif key == "authoritative_url":
                    self.assertIn("https://example.invalid/public?dataset=synthetic&v=1", rendered)
                else:
                    escaped = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    self.assertIn(escaped, rendered)
        self.assertIn(views.GENERATED_MARKER, rendered)
        self.assertIn("canonical JSON", rendered)

    def test_write_then_check_is_byte_stable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            source = directory / "sources-synthetic.json"
            source.write_text(json.dumps(self._payload(), indent=2) + "\n", encoding="utf-8")

            changed = views.write_landscape_projections(directory)
            self.assertEqual(changed, (directory / "sources-synthetic.md",))
            first = (directory / "sources-synthetic.md").read_bytes()

            second_changed = views.write_landscape_projections(directory)
            self.assertEqual(second_changed, ())
            self.assertEqual((directory / "sources-synthetic.md").read_bytes(), first)
            self.assertTrue(views.check_landscape_projections(directory, stream=io.StringIO()))

    def test_renderer_rejects_landscape_policy_escalation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            payload = self._payload()
            payload["entries"][0]["admission_status"] = "admitted"
            (directory / "sources-synthetic.json").write_text(
                json.dumps(payload, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(views.ProjectionError, "admission_status must remain not_admitted"):
                views.write_landscape_projections(directory)

    def test_check_fails_on_manual_edit_and_write_repairs_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            source = directory / "sources-synthetic.json"
            source.write_text(json.dumps(self._payload(), indent=2) + "\n", encoding="utf-8")
            views.write_landscape_projections(directory)
            projection = directory / "sources-synthetic.md"
            projection.write_text(projection.read_text(encoding="utf-8") + "manual drift\n", encoding="utf-8")

            diagnostics = io.StringIO()
            self.assertFalse(views.check_landscape_projections(directory, stream=diagnostics))
            self.assertIn("DRIFT", diagnostics.getvalue())
            views.write_landscape_projections(directory)
            self.assertTrue(views.check_landscape_projections(directory, stream=io.StringIO()))

    def test_orphan_generated_projection_is_removed_but_handwritten_markdown_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            source = directory / "sources-synthetic.json"
            source.write_text(json.dumps(self._payload(), indent=2) + "\n", encoding="utf-8")
            views.write_landscape_projections(directory)

            orphan = directory / "sources-retired.md"
            orphan.write_text(f"<!-- {views.GENERATED_MARKER} -->\n", encoding="utf-8")
            handwritten = directory / "sources-not-generated.md"
            handwritten.write_text("# Handwritten\n", encoding="utf-8")

            self.assertFalse(views.check_landscape_projections(directory, stream=io.StringIO()))
            views.write_landscape_projections(directory)
            self.assertFalse(orphan.exists())
            self.assertTrue(handwritten.exists())

    def test_duplicate_keys_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sources-bad.json"
            path.write_text('{"schema_version":"1", "schema_version":"2"}', encoding="utf-8")
            with self.assertRaises(views.ProjectionError):
                views.load_canonical_json(path)

    def test_structured_projection_is_lossless_and_markdown_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            path = directory / "synthetic.json"
            canonical = json.dumps(self._structured_payload(), indent=2, ensure_ascii=False) + "\n"
            path.write_text(canonical, encoding="utf-8")

            outputs = views.expected_structured_projections(directory, record_kind="access")
            rendered = outputs[directory / "synthetic.md"]

        self.assertIn(views.GENERATED_MARKER, rendered)
        self.assertIn("# Access contract: `synthetic.json`", rendered)
        self.assertIn("```json\n" + canonical.rstrip("\n") + "\n```", rendered)
        self.assertIn("https://example.invalid/docs?x=1&y=2", rendered)
        self.assertIn('"enabled": false', rendered)
        self.assertIn('"optional": null', rendered)
        self.assertIn('Literal <tag> & markdown *text* `code`.', rendered)

    def test_structured_write_check_is_byte_stable_and_generated_orphans_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            source = directory / "record.json"
            source.write_text(
                json.dumps(self._structured_payload(), indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            changed = views.write_structured_projections(directory, record_kind="manifests")
            self.assertEqual(changed, (directory / "record.md",))
            first = (directory / "record.md").read_bytes()
            self.assertEqual(views.write_structured_projections(directory, record_kind="manifests"), ())
            self.assertEqual((directory / "record.md").read_bytes(), first)
            self.assertTrue(
                views.check_structured_projections(
                    directory,
                    record_kind="manifests",
                    stream=io.StringIO(),
                )
            )

            orphan = directory / "retired.md"
            orphan.write_text(f"<!-- {views.GENERATED_MARKER} -->\n", encoding="utf-8")
            handwritten = directory / "notes.md"
            handwritten.write_text("# Handwritten notes\n", encoding="utf-8")
            self.assertFalse(
                views.check_structured_projections(
                    directory,
                    record_kind="manifests",
                    stream=io.StringIO(),
                )
            )
            views.write_structured_projections(directory, record_kind="manifests")
            self.assertFalse(orphan.exists())
            self.assertTrue(handwritten.exists())

    def test_structured_loader_rejects_duplicate_keys_nonfinite_and_nonobject_root(self) -> None:
        fixtures = {
            "duplicate.json": '{"a": 1, "a": 2}',
            "nan.json": '{"a": NaN}',
            "infinity.json": '{"a": Infinity}',
            "array.json": '[1, 2, 3]',
        }
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            for name, text in fixtures.items():
                with self.subTest(name=name):
                    path = directory / name
                    path.write_text(text, encoding="utf-8")
                    with self.assertRaises(views.ProjectionError):
                        views.load_structured_json(path)


if __name__ == "__main__":
    unittest.main()
