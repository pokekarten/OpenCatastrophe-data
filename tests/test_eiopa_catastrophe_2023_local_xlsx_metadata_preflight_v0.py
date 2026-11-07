# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Construct wholly original toy XLSX ZIPs to audit EIOPA quarantine code.

No real third-party EIOPA financial rows, insurer amounts or workbook
source code/test fixtures are copied.
"""
from __future__ import annotations

import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
import eiopa_catastrophe_2023_local_xlsx_metadata_preflight_v0 as gate

XML = (b'<?xml version="1.0" encoding="UTF-8"?>'
       b'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
       b'<sheets><sheet name="Original Synthetic Only" sheetId="1"/></sheets></workbook>')


def fixture(path: Path, *, sheet=XML, extra: dict | None = None,
            omit: str | None = None) -> bytes:
    items = {
        "[Content_Types].xml": b'<Types/>',
        "_rels/.rels": b'<Relationships/>',
        "xl/workbook.xml": sheet,
        "xl/worksheets/sheet1.xml": b'<worksheet><sheetData/></worksheet>',
    }
    if extra:
        items.update(extra)
    if omit:
        items.pop(omit)
    with ZipFile(path, "x", compression=ZIP_DEFLATED) as z:
        for name, raw in sorted(items.items()):
            z.writestr(name, raw)
    return path.read_bytes()


class OfflineEIOPAOriginalXLSXQuarantineTests(unittest.TestCase):
    def test_source_pinned_printer_settings_only_cannot_apply_to_foreign_zip(self):
        part = ZipInfo("xl/printerSettings/printerSettings1.bin")
        part.file_size = 5420
        part.compress_size = 443
        good = gate.allow_source_pinned_printer_metadata_only(
            part, "FLOOD_WIND_EXPOSURE",
            gate.PINNED_EIOPA_EXPOSURE_SHA, gate.PINNED_EIOPA_EXPOSURE_SIZE
        )
        self.assertTrue(good)
        for name, family, sha, length, size in (
            ("xl/printerSettings/printerSettings1.bin", "HISTORICAL_INSURED_LOSSES",
             gate.PINNED_EIOPA_EXPOSURE_SHA, gate.PINNED_EIOPA_EXPOSURE_SIZE, 5420),
            ("xl/printerSettings/printerSettings1.bin", "FLOOD_WIND_EXPOSURE",
             "f"*64, gate.PINNED_EIOPA_EXPOSURE_SIZE, 5420),
            ("xl/printerSettings/printerSettings1.bin", "FLOOD_WIND_EXPOSURE",
             gate.PINNED_EIOPA_EXPOSURE_SHA, 5593552, 5420),
            ("xl/printerSettings/printerSettings1.exe", "FLOOD_WIND_EXPOSURE",
             gate.PINNED_EIOPA_EXPOSURE_SHA, gate.PINNED_EIOPA_EXPOSURE_SIZE, 5420),
            ("xl/printerSettings/../../vbaProject.bin", "FLOOD_WIND_EXPOSURE",
             gate.PINNED_EIOPA_EXPOSURE_SHA, gate.PINNED_EIOPA_EXPOSURE_SIZE, 5420),
            ("xl/vbaProject.bin", "FLOOD_WIND_EXPOSURE",
             gate.PINNED_EIOPA_EXPOSURE_SHA, gate.PINNED_EIOPA_EXPOSURE_SIZE, 5420),
            ("xl/printerSettings/printerSettings1.bin", "FLOOD_WIND_EXPOSURE",
             gate.PINNED_EIOPA_EXPOSURE_SHA, gate.PINNED_EIOPA_EXPOSURE_SIZE, 6000),
        ):
            part = ZipInfo(name)
            part.file_size = size
            part.compress_size = 443
            with self.subTest(name=name, family=family, sha=sha, length=length, size=size):
                self.assertFalse(gate.allow_source_pinned_printer_metadata_only(
                    part, family, sha, length
                ))

    def test_generic_printer_driver_binary_stays_blocked_without_source_sha_pin(self):
        with TemporaryDirectory() as d:
            p = Path(d)/"untrusted.xlsx"
            fixture(p, extra={"xl/printerSettings/printerSettings1.bin":b"S"*5420})
            with self.assertRaisesRegex(gate.EIOPAQuarantineBlocked, "active, external or huge"):
                gate.inspect_original_xlsx(p, "FLOOD_WIND_EXPOSURE")

    def test_two_synthetic_source_families_integrity_and_no_loss_read(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            l, e = root / "loss.xlsx", root / "exposure.xlsx"
            raw_l = fixture(l)
            raw_e = fixture(e, extra={
                "docProps/custom.xml": b"<source>Synthetic only not a real insurer</source>"
            })
            report = gate.inspect_pair(l, e)
            self.assertEqual(len(report["originals"]), 2)
            self.assertEqual(report["originals"][0]["sha256"], hashlib.sha256(raw_l).hexdigest())
            self.assertEqual(report["originals"][1]["sha256"], hashlib.sha256(raw_e).hexdigest())
            self.assertEqual(report["originals"][0]["sheet_count"], 1)
            self.assertEqual(report["originals"][0]["worksheet_names_sanitized"],
                             ["Original Synthetic Only"])
            self.assertTrue(all(x["zip_crc_passed"] for x in report["originals"]))
            for key in ("observations_verified_for_Ciara_2020",
                        "historical_Daria_1990_claims_available",
                        "insured_GUL_IL_RI_OEP_AEP_calculated",
                        "permission_to_redistribute_original_workbooks_inferred"):
                self.assertIs(report[key], False)

    def test_synthetic_xlsx_pair_receipt_is_reproducible_and_does_not_copy_workbooks(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            l, e = root / "loss.xlsx", root / "exposure.xlsx"
            fixture(l)
            fixture(e, extra={"docProps/core.xml": b"<core/>"})
            out = root / "receipt.json"
            self.assertEqual(gate.main(["--local-loss-xlsx", str(l),
                                        "--local-exposure-xlsx", str(e),
                                        "--out-receipt", str(out)]), 0)
            result = json.loads(out.read_text())
            self.assertEqual(result["status"],
                             "LOCAL_EIOPA_ORIGINAL_XLSX_BINARY_INTEGRITY_CHECKED_NOT_MODEL_ADMITTED")
            self.assertTrue(result["originals"][0]["zip_crc_passed"])
            self.assertFalse(result["originals"][0]["worksheet_cells_or_loss_values_read"])
            self.assertNotIn("Synthetic only not a real insurer", out.read_text())
            self.assertEqual(gate.main(["--local-loss-xlsx", str(l),
                                        "--local-exposure-xlsx", str(e),
                                        "--out-receipt", str(out)]), 2)

    def test_unknown_binary_or_active_content_blocked(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            bad = root / "invalid.xlsx"
            bad.write_bytes(b"<html>" + b"x" * 1000)
            with self.assertRaises(gate.EIOPAQuarantineBlocked):
                gate.inspect_original_xlsx(bad, "HISTORICAL_INSURED_LOSSES")
            for idx, member in enumerate((
                "xl/vbaProject.bin", "xl/activeX/active1.xml",
                "xl/externalLinks/externalLink1.xml", "xl/embeddings/file1.bin"
            )):
                p = root / f"active_{idx}.xlsx"
                fixture(p, extra={member: b"1"})
                with self.subTest(member=member):
                    with self.assertRaises(gate.EIOPAQuarantineBlocked):
                        gate.inspect_original_xlsx(p, "HISTORICAL_INSURED_LOSSES")

    def test_traversal_malicious_members_and_source_identity_blocked(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            for idx, name in enumerate(("../outside.xml", "/etc/passwd", "xl\\evil.xml")):
                p = root / f"bad_{idx}.xlsx"
                fixture(p, extra={name: b"unsafe"})
                with self.subTest(name=name):
                    with self.assertRaises(gate.EIOPAQuarantineBlocked):
                        gate.inspect_original_xlsx(p, "HISTORICAL_INSURED_LOSSES")
            p = root / "normal.xlsx"
            fixture(p)
            with self.assertRaises(gate.EIOPAQuarantineBlocked):
                gate.inspect_pair(p, p)

    def test_required_workbook_structure_and_safe_source_sheet_names(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            for idx, part in enumerate((
                "[Content_Types].xml", "_rels/.rels", "xl/workbook.xml",
                "xl/worksheets/sheet1.xml"
            )):
                p = root / f"missing{idx}.xlsx"
                fixture(p, omit=part)
                with self.subTest(part=part):
                    with self.assertRaises(gate.EIOPAQuarantineBlocked):
                        gate.inspect_original_xlsx(p, "HISTORICAL_INSURED_LOSSES")
            p = root / "formula_name.xlsx"
            fixture(p, sheet=XML.replace(b"Original Synthetic Only", b"=1+1"))
            with self.assertRaises(gate.EIOPAQuarantineBlocked):
                gate.inspect_original_xlsx(p, "HISTORICAL_INSURED_LOSSES")

    def test_decompression_bomb_and_enormous_workbook_metadata_rejected(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            p = root / "bomb.xlsx"
            fixture(p, extra={"xl/styles.xml": b"Z" * 8_000_000})
            with self.assertRaises(gate.EIOPAQuarantineBlocked):
                gate.inspect_original_xlsx(p, "HISTORICAL_INSURED_LOSSES")
            p = root / "huge_workbook.xlsx"
            fixture(p, sheet=XML + b" " * (gate.MAX_WORKBOOK_XML + 2))
            with self.assertRaises(gate.EIOPAQuarantineBlocked):
                gate.inspect_original_xlsx(p, "HISTORICAL_INSURED_LOSSES")

    def test_XXE_and_xml_doctype_blocked_without_cell_parsing(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            p = root / "xml.xlsm"
            fixture(p)
            with self.assertRaises(gate.EIOPAQuarantineBlocked):
                gate.inspect_original_xlsx(p, "HISTORICAL_INSURED_LOSSES")
            p = root / "external_entity.xlsx"
            fixture(p, sheet=XML + b"<!DOCTYPE workbook [<!ENTITY malicious SYSTEM 'file:" + b"///etc/passwd'>]>")
            with self.assertRaises(gate.EIOPAQuarantineBlocked):
                gate.inspect_original_xlsx(p, "HISTORICAL_INSURED_LOSSES")

    def test_symlink_not_followed_and_unverified_publisher_origin_is_explicit(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            p = root / "actual.xlsx"
            fixture(p)
            symlink = root / "alias.xlsx"
            symlink.symlink_to(p)
            with self.assertRaises(gate.EIOPAQuarantineBlocked):
                gate.inspect_original_xlsx(symlink, "HISTORICAL_INSURED_LOSSES")
            receipt = gate.inspect_original_xlsx(p, "HISTORICAL_INSURED_LOSSES")
            self.assertFalse(receipt["publisher_web_origin_authenticated_by_this_script"])
            self.assertFalse(receipt["workbook_specific_reuse_rights_verified"])
            self.assertFalse(receipt["ciara_NUTS2_loss_schema_verified"])
            with self.assertRaises(gate.EIOPAQuarantineBlocked):
                gate.inspect_original_xlsx(p, "UNEXPECTED_FAMILY")


if __name__ == "__main__":
    unittest.main()
