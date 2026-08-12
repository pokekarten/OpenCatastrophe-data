# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path

from scripts import structured_public_views as views


class StructuredPublicViewTests(unittest.TestCase):
    def _payload(self) -> dict[str, object]:
        return {
            "schema_version": "1.0.0",
            "access_id": "synthetic.access.v1",
            "provider": "Synthetic <Provider> & *markup*",
            "status": "documented_only",
            "api_version": None,
            "authentication": {
                "mode": "none",
                "secret_in_repository": False,
            },
            "limits": {
                "timeout_seconds": 30,
                "max_probe_bytes": 65536,
            },
            "evidence_urls": ["https://example.invalid/docs?a=1&b=2"],
            "variables_and_units": [
                {
                    "name": "synthetic variable",
                    "unit": "m/s",
                    "description": "Synthetic description.",
                },
                {
                    "name": "second variable",
                    "unit": None,
                    "description": "Nested object list coverage.",
                },
            ],
            "nested_arrays": [[1, 2], ["a", "b"]],
            "notes": "Literal [brackets], # heading text and <script> are data, not Markdown.",
        }

    def test_projection_is_complete_and_safely_escaped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic.json"
            payload = self._payload()
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            rendered = views.render_structured_markdown(path, payload, kind="access")

        for needle in (
            "synthetic.access.v1",
            "documented_only",
            "`null`",
            "`false`",
            "`30`",
            "`65536`",
            "https://example.invalid/docs?a=1&amp;b=2",
            "synthetic variable",
            "second variable",
            "m/s",
            "Nested object list coverage.",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, rendered)

        self.assertIn("Synthetic &lt;Provider&gt; &amp; \\*markup\\*", rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertNotIn("<script>", rendered)
        self.assertIn(views.GENERATED_MARKER, rendered)
        self.assertIn("The JSON remains authoritative", rendered)

    def test_write_check_and_repair_are_byte_stable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            source = directory / "synthetic.json"
            source.write_text(json.dumps(self._payload(), indent=2) + "\n", encoding="utf-8")

            changed = views.write_structured_projections(directory, kind="access")
            self.assertEqual(changed, (directory / "synthetic.md",))
            first = (directory / "synthetic.md").read_bytes()
            self.assertEqual(views.write_structured_projections(directory, kind="access"), ())
            self.assertEqual((directory / "synthetic.md").read_bytes(), first)
            self.assertTrue(
                views.check_structured_projections(
                    directory,
                    kind="access",
                    stream=io.StringIO(),
                )
            )

            projection = directory / "synthetic.md"
            projection.write_text(projection.read_text(encoding="utf-8") + "manual drift\n", encoding="utf-8")
            diagnostics = io.StringIO()
            self.assertFalse(
                views.check_structured_projections(
                    directory,
                    kind="access",
                    stream=diagnostics,
                )
            )
            self.assertIn("DRIFT", diagnostics.getvalue())
            views.write_structured_projections(directory, kind="access")
            self.assertEqual(projection.read_bytes(), first)

    def test_orphan_cleanup_preserves_handwritten_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "synthetic.json").write_text(
                json.dumps(self._payload(), indent=2) + "\n",
                encoding="utf-8",
            )
            views.write_structured_projections(directory, kind="manifest")

            orphan = directory / "retired.md"
            orphan.write_text(f"<!-- {views.GENERATED_MARKER} -->\n", encoding="utf-8")
            handwritten = directory / "README.md"
            handwritten.write_text("# Handwritten\n", encoding="utf-8")

            self.assertFalse(
                views.check_structured_projections(
                    directory,
                    kind="manifest",
                    stream=io.StringIO(),
                )
            )
            views.write_structured_projections(directory, kind="manifest")
            self.assertFalse(orphan.exists())
            self.assertTrue(handwritten.exists())

    def test_duplicate_keys_and_nonfinite_numbers_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            duplicate = directory / "duplicate.json"
            duplicate.write_text('{"x": 1, "x": 2}', encoding="utf-8")
            with self.assertRaisesRegex(views.ProjectionError, "duplicate JSON key"):
                views.load_structured_json(duplicate)

            for name, source in (
                ("nonfinite-literal.json", '{"x": NaN}'),
                ("positive-overflow.json", '{"x": 1e400}'),
                ("negative-overflow.json", '{"x": -1e400}'),
            ):
                with self.subTest(source=source):
                    nonfinite = directory / name
                    nonfinite.write_text(source, encoding="utf-8")
                    with self.assertRaisesRegex(views.ProjectionError, "non-finite JSON number"):
                        views.load_structured_json(nonfinite)

            finite = directory / "finite-large.json"
            finite.write_text('{"x": 1e308}', encoding="utf-8")
            self.assertEqual(views.load_structured_json(finite), {"x": 1e308})

    def test_root_must_be_an_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text('["not", "an", "object"]', encoding="utf-8")
            with self.assertRaisesRegex(views.ProjectionError, "must be a JSON object"):
                views.load_structured_json(path)


if __name__ == "__main__":
    unittest.main()
