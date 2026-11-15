# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Focused offline regression for tracked REUSE .license metadata sidecars."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import check_license_metadata as licensing


SIDE = "SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors\nSPDX-License-Identifier: Apache-2.0\n"


class TrackedSidecarTests(unittest.TestCase):
    def test_valid_tracked_sidecar_does_not_change_source_data(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "receipt.json"
            source.write_text('{"provider_original_sha256":"not-republished"}\n', encoding="utf-8")
            original = source.read_bytes()
            (root / "receipt.json.license").write_text(SIDE, encoding="utf-8")
            with patch.object(licensing, "ROOT", root):
                result = licensing.read_tracked_spdx_metadata(
                    Path("receipt.json"), {Path("receipt.json"), Path("receipt.json.license")}
                )
            self.assertEqual(result, (True, True, ["Apache-2.0"]))
            self.assertEqual(source.read_bytes(), original)

    def test_untracked_sidecar_must_not_authorize_missing_inline_tags(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "receipt.json").write_text("{}\n", encoding="utf-8")
            (root / "receipt.json.license").write_text(SIDE, encoding="utf-8")
            with patch.object(licensing, "ROOT", root):
                result = licensing.read_tracked_spdx_metadata(
                    Path("receipt.json"), {Path("receipt.json")}
                )
            self.assertEqual(result, (False, False, []))

    def test_incomplete_tracked_sidecar_is_not_silently_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "receipt.json").write_text("{}\n", encoding="utf-8")
            (root / "receipt.json.license").write_text(
                "SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors\n",
                encoding="utf-8",
            )
            with patch.object(licensing, "ROOT", root):
                result = licensing.read_tracked_spdx_metadata(
                    Path("receipt.json"), {Path("receipt.json"), Path("receipt.json.license")}
                )
            self.assertEqual(result, (True, False, []))

    def test_inline_tags_without_sidecar_are_still_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "example.py").write_text("# " + SIDE.replace("\n", "\n# "), encoding="utf-8")
            with patch.object(licensing, "ROOT", root):
                result = licensing.read_tracked_spdx_metadata(
                    Path("example.py"), {Path("example.py")}
                )
            self.assertEqual(result, (True, True, ["Apache-2.0"]))

    def test_absent_sidecar_does_not_hide_missing_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "receipt.json").write_text("{}\n", encoding="utf-8")
            with patch.object(licensing, "ROOT", root):
                result = licensing.read_tracked_spdx_metadata(
                    Path("receipt.json"), {Path("receipt.json"), Path("receipt.json.license")}
                )
            self.assertEqual(result, (False, False, []))


if __name__ == "__main__":
    unittest.main()
