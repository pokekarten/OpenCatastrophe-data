# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only metadata provenance tests; never retrieve original insurer data."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
from unittest import TestCase
from unittest.mock import patch
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
import eiopa_2023_exposure_ooxml_quarantine_index_v0 as diag


def synthetic_xlsx(path: Path, extra: dict[str, bytes] | None = None):
    parts = {
        "[Content_Types].xml": b"<Types/>",
        "_rels/.rels": b"<Relationships/>",
        "xl/workbook.xml": b"<book/>",
        "xl/worksheets/sheet1.xml": b"<sheet><synthetic-not-insurer>nothing</synthetic-not-insurer></sheet>",
    }
    parts.update(extra or {})
    with ZipFile(path, "x", compression=ZIP_DEFLATED) as zipout:
        for name, content in sorted(parts.items()):
            zipout.writestr(name, content)
    raw = path.read_bytes()
    return len(raw), hashlib.sha256(raw).hexdigest()


def inspect_fixture(path, extra=None):
    n, sha = synthetic_xlsx(path, extra)
    with patch.object(diag, "SOURCE_BYTES", n), patch.object(diag, "SOURCE_SHA256", sha):
        return diag.inspect_zip_directory_without_cells(path)


class OriginalSourceQuarantineMetadataTests(TestCase):
    def test_simple_synthetic_member_index_has_no_blockers(self):
        with tempfile.TemporaryDirectory() as temp:
            receipt = inspect_fixture(Path(temp)/"toy.xlsx")
        self.assertFalse(receipt["strict_gate_observed_zip_metadata_blocker"])
        self.assertEqual(receipt["member_count"], 4)
        self.assertEqual(receipt["flagged_member_entries_count"], 0)
        self.assertFalse(receipt["workbook_XML_or_worksheet_cells_read"])
        self.assertFalse(receipt["data_mining_reuse_rights_verified"])

    def test_synthetic_external_links_and_embedded_object_are_blocked_with_fixed_tags(self):
        extra = {
            "xl/externalLinks/externalLink_SecretInsurer1.xml": b"NO PRIVATE DATA",
            "xl/embeddings/SecretInsurerSource.bin": b"NO EXCEL EXECUTION",
            "xl/activeX/activeX3.xml": b"NO EXECUTION",
            "xl/vbaProject.bin": b"NO MACROS",
            "xl/printerSettings/printerSettings7.bin": b"NO PRINTER DRIVER",
        }
        with tempfile.TemporaryDirectory() as temp:
            receipt = inspect_fixture(Path(temp)/"toy.xlsx", extra)
        self.assertTrue(receipt["strict_gate_observed_zip_metadata_blocker"])
        output = json.dumps(receipt, sort_keys=True)
        for forbidden in ("SecretInsurerSource", "SecretInsurer1", "printerSettings7", "activeX3"):
            self.assertNotIn(forbidden, output)
        all_reasons = {
            reason
            for entry in receipt["flagged_member_categories_and_sizes_only"]
            for reason in entry["why_original_strict_gate_blocks"]
        }
        self.assertTrue({
            "EXTERNAL_LINK", "EMBEDDED_OBJECT", "ACTIVE_X", "VBA_PROJECT",
            "BINARY_OR_EXECUTABLE_EXTENSION",
        }.issubset(all_reasons))
        self.assertFalse(receipt["original_member_filenames_published"])

    def test_untrusted_zip_path_does_not_leave_original_name_in_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            receipt = inspect_fixture(
                Path(temp)/"toy.xlsx",
                {"../Confidential_Insurer_Accounts.xml": b"<x/>"}
            )
        self.assertTrue(receipt["strict_gate_observed_zip_metadata_blocker"])
        self.assertIn("UNSAFE_OR_ENCRYPTED_ZIP_PATH",
                      receipt["flagged_member_categories_and_sizes_only"][0]
                      ["why_original_strict_gate_blocks"])
        self.assertNotIn("Confidential_Insurer_Accounts", json.dumps(receipt))

    def test_compression_ratio_guard_identifies_bomb_without_expanding_cells(self):
        with tempfile.TemporaryDirectory() as temp:
            receipt = inspect_fixture(
                Path(temp)/"toy.xlsx", {"xl/worksheets/sheet2.xml": b"Z"*2_000_000}
            )
        self.assertIn("COMPRESSION_RATIO_LIMIT", str(receipt["flagged_member_categories_and_sizes_only"]))
        self.assertFalse(receipt["all_ZIP_member_CRCs_checked"])
        self.assertFalse(receipt["workbook_XML_or_worksheet_cells_read"])

    def test_expensive_original_metadata_replay_must_be_manual_only(self):
        yml = (ROOT/".github/workflows/eiopa-2023-exposure-zip-index-one-shot.yml"
               ).read_text(encoding="utf-8")
        block = yml.split("\non:\n",1)[1].split("\npermissions:",1)[0]
        self.assertEqual(block, "  workflow_dispatch:\n")
        self.assertIn("contents: read", yml)
        self.assertIn("retention-days: 14", yml)
        self.assertIn("eiopa-2023-exposure-original-OOXML-members-NOT-CLAIMS.json", yml)
        self.assertNotIn("*.xlsx", yml)
        self.assertNotIn("actions: write", yml)

    def test_wrong_original_sha_and_size_rejected_before_zip_index_audit(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)/"toy.xlsx"
            size, sha = synthetic_xlsx(p)
            with patch.object(diag, "SOURCE_BYTES", size), patch.object(diag, "SOURCE_SHA256", "0"*64):
                with self.assertRaises(diag.EIOPAQuarantineIndexBlocked):
                    diag.inspect_zip_directory_without_cells(p)
            with patch.object(diag, "SOURCE_BYTES", size+1), patch.object(diag, "SOURCE_SHA256", sha):
                with self.assertRaises(diag.EIOPAQuarantineIndexBlocked):
                    diag.inspect_zip_directory_without_cells(p)
            alias = Path(temp)/"alias.xlsx"
            alias.symlink_to(p)
            with patch.object(diag, "SOURCE_BYTES", size), patch.object(diag, "SOURCE_SHA256", sha):
                with self.assertRaises(diag.EIOPAQuarantineIndexBlocked):
                    diag.inspect_zip_directory_without_cells(alias)


if __name__ == "__main__":
    import unittest
    unittest.main()
