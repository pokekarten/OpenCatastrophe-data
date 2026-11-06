# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read-only, offline EIOPA XLSX ORIGINAL FILE metadata quarantine preflight.

No HTTP request. The user/runner provides two local original ZIP/XLSX files.
No worksheets/cell values/insurer claims are read or serialized. This is not
evidence of publisher origin, data licence, privacy, event fit, loss semantics,
calibration or 2020 Ciara / 1990 Daria equivalence.
"""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

SCHEMA = "EIOPA_2023_LOCAL_XLSX_BINARY_METADATA_ONLY_QUARANTINE_V0"
MAX_FILE_BYTES = {"HISTORICAL_INSURED_LOSSES": 1_000_000,
                  "FLOOD_WIND_EXPOSURE": 20_000_000}
MAX_MEMBERS = 250
MAX_TOTAL_UNCOMPRESSED = 500_000_000
MAX_ONE_MEMBER = 150_000_000
MAX_RATIO = 1000
MAX_WORKBOOK_XML = 800_000
NAME_RE = re.compile(r"^[A-Za-z0-9 _().+\-]{1,31}$")
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
# See OOXML ISO/IEC 29500 Printer Settings Part, 15.2.15.
# This is a raw printer-specific blob, *not* financial spreadsheet content.
# For precisely one SHA-pinned original published EIOPA exposure XLSX,
# permit metadata/ZIP integrity inspection while NEVER opening, parsing,
# executing, extracting, or uploading the binary driver settings part.
PINNED_EIOPA_EXPOSURE_SHA = "f3ec03e25be247a798d94ea9d5ece8bd03a34bcc27b6faf99b597bbd863c3e79"
PINNED_EIOPA_EXPOSURE_SIZE = 5593551
PINNED_SOURCE_PRINTER_FILE = re.compile(r"xl/printerSettings/printerSettings[1-9][0-9]*\\.bin\\Z")
PINNED_SOURCE_PRINTER_UNCOMPRESSED = 5420
PINNED_SOURCE_PRINTER_COMPRESSED = 443


def allow_source_pinned_printer_metadata_only(info, family: str, source_sha: str, source_size: int) -> bool:
    """A very narrow original-identity exception; binary content is never read."""
    return (
        family == "FLOOD_WIND_EXPOSURE"
        and source_sha == PINNED_EIOPA_EXPOSURE_SHA
        and source_size == PINNED_EIOPA_EXPOSURE_SIZE
        and bool(PINNED_SOURCE_PRINTER_FILE.fullmatch(info.filename))
        and info.file_size == PINNED_SOURCE_PRINTER_UNCOMPRESSED
        and info.compress_size == PINNED_SOURCE_PRINTER_COMPRESSED
        and not (info.flag_bits & 1)
    )



class EIOPAQuarantineBlocked(ValueError):
    """Blocked malformed, untrusted or overpromoted original EIOPA spreadsheet."""


def _readonly_file(path: Path, family: str) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise EIOPAQuarantineBlocked("original local XLSX path must be a regular file")
    if path.suffix.lower() != ".xlsx":
        raise EIOPAQuarantineBlocked("EIOPA source must be an XLSX, not xlsm or xls")
    size = path.stat().st_size
    if not 300 <= size <= MAX_FILE_BYTES[family]:
        raise EIOPAQuarantineBlocked("local original XLSX exceeds source family bounds")
    raw = path.read_bytes()
    if len(raw) != size or not raw.startswith(b"PK\x03\x04"):
        raise EIOPAQuarantineBlocked("source file is not a complete OOXML ZIP")
    return raw


def inspect_original_xlsx(path: Path, family: str) -> dict:
    """Inspect ZIP/member metadata and workbook.xml only, never worksheet cells."""
    if family not in MAX_FILE_BYTES:
        raise EIOPAQuarantineBlocked("original EIOPA family unknown")
    raw = _readonly_file(path, family)
    original_sha = hashlib.sha256(raw).hexdigest()
    try:
        from io import BytesIO
        with zipfile.ZipFile(BytesIO(raw), "r") as z:
            infos = z.infolist()
            if not 3 <= len(infos) <= MAX_MEMBERS:
                raise EIOPAQuarantineBlocked("OOXML member count outside allowed bounds")
            names = [i.filename for i in infos]
            if len(set(names)) != len(names):
                raise EIOPAQuarantineBlocked("duplicate ZIP member names blocked")
            required = {"[Content_Types].xml", "_rels/.rels", "xl/workbook.xml"}
            if not required.issubset(names):
                raise EIOPAQuarantineBlocked("missing core XLSX workbook parts")
            total = 0
            sheet_parts = 0
            ignored_source_printer_blobs = 0
            for info in infos:
                name = info.filename
                p = PurePosixPath(name)
                if (name.startswith("/") or "\\" in name or ".." in p.parts
                    or not name or info.flag_bits & 1 or info.is_dir()):
                    raise EIOPAQuarantineBlocked("encrypted/unsafe XLSX ZIP paths are blocked")
                original_printer_metadata_only = allow_source_pinned_printer_metadata_only(
                    info, family, original_sha, len(raw)
                )
                if original_printer_metadata_only:
                    ignored_source_printer_blobs += 1
                    if ignored_source_printer_blobs != 1:
                        raise EIOPAQuarantineBlocked("multiple pinned printer device blobs")
                if (name.startswith("xl/externalLinks/")
                    or name.startswith("xl/embeddings/")
                    or name.startswith("xl/activeX/")
                    or name.startswith("xl/vbaProject")
                    or (name.endswith((".bin", ".exe", ".dll", ".js", ".vbs"))
                        and not original_printer_metadata_only)
                    or info.file_size > MAX_ONE_MEMBER):
                    raise EIOPAQuarantineBlocked("active, external or huge OOXML member")
                if info.compress_size == 0 and info.file_size > 0:
                    raise EIOPAQuarantineBlocked("ZIP member compression metadata impossible")
                if (info.compress_size and
                    info.file_size > info.compress_size * MAX_RATIO):
                    raise EIOPAQuarantineBlocked("ZIP decompression ratio exceeds bounds")
                total += info.file_size
                if name.startswith("xl/worksheets/") and name.endswith(".xml"):
                    sheet_parts += 1
            if total > MAX_TOTAL_UNCOMPRESSED:
                raise EIOPAQuarantineBlocked("uncompressed OOXML size exceeds limit")
            # testzip streams all compressed parts for CRC without reading or
            # serializing any cell contents into model memory or Git output.
            if z.testzip() is not None:
                raise EIOPAQuarantineBlocked("bad original file CRC")
            part = z.getinfo("xl/workbook.xml")
            if part.file_size > MAX_WORKBOOK_XML:
                raise EIOPAQuarantineBlocked("workbook metadata XML too large")
            xml = z.read("xl/workbook.xml")
            if b"<!DOCTYPE" in xml.upper() or b"<!ENTITY" in xml.upper():
                raise EIOPAQuarantineBlocked("XML entities not accepted")
            root = ET.fromstring(xml)
            sheets = root.find("s:sheets", NS)
            if sheets is None or not 1 <= len(sheets) <= 100:
                raise EIOPAQuarantineBlocked("missing/oversized original workbook sheet set")
            names_safe = []
            for sheet in sheets:
                n = sheet.attrib.get("name", "")
                if not NAME_RE.fullmatch(n):
                    # Do not emit arbitrary strings from third-party XLSX.
                    raise EIOPAQuarantineBlocked("untrusted or unusual worksheet name; manual review")
                names_safe.append(n)
            if len(set(names_safe)) != len(names_safe):
                raise EIOPAQuarantineBlocked("duplicate workbook sheet names")
            if sheet_parts < len(names_safe):
                raise EIOPAQuarantineBlocked("missing workbook worksheet parts")
    except (zipfile.BadZipFile, ET.ParseError, RuntimeError, OverflowError) as exc:
        raise EIOPAQuarantineBlocked("original XLSX ZIP/XML malformed") from exc

    return {
        "source_family": family,
        "input_type": "LOCAL_BYTES_ORIGIN_NOT_INDEPENDENTLY_ATTESTED",
        "sha256": original_sha,
        "original_file_size_bytes": len(raw),
        "zip_member_count": len(infos),
        "zip_crc_passed": True,
        "source_pinned_printer_metadata_only_blob_count": ignored_source_printer_blobs,
        "printer_driver_blob_opened_parsed_or_executed": False,
        "sheet_count": len(names_safe),
        "worksheet_names_sanitized": names_safe,
        "worksheet_cells_or_loss_values_read": False,
        "original_XLSX_rows_exported_or_committed": False,
        "publisher_web_origin_authenticated_by_this_script": False,
        "workbook_specific_reuse_rights_verified": False,
        "ciara_NUTS2_loss_schema_verified": False,
    }


def inspect_pair(loss_path: Path, exposure_path: Path) -> dict:
    if loss_path.resolve() == exposure_path.resolve():
        raise EIOPAQuarantineBlocked("must supply two independent EIOPA source files")
    loss = inspect_original_xlsx(loss_path, "HISTORICAL_INSURED_LOSSES")
    exposure = inspect_original_xlsx(exposure_path, "FLOOD_WIND_EXPOSURE")
    if loss["sha256"] == exposure["sha256"]:
        raise EIOPAQuarantineBlocked("EIOPA original source bytes must differ")
    return {
        "schema": SCHEMA,
        "status": "LOCAL_EIOPA_ORIGINAL_XLSX_BINARY_INTEGRITY_CHECKED_NOT_MODEL_ADMITTED",
        "observations_verified_for_Ciara_2020": False,
        "historical_Daria_1990_claims_available": False,
        "company_level_or_individual_claims_extracted": False,
        "insurer_RV_policy_or_building_exposure_inferred": False,
        "insured_GUL_IL_RI_OEP_AEP_calculated": False,
        "permission_to_redistribute_original_workbooks_inferred": False,
        "originals": [loss, exposure],
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--local-loss-xlsx", type=Path, required=True)
    p.add_argument("--local-exposure-xlsx", type=Path, required=True)
    p.add_argument("--out-receipt", type=Path, required=True)
    a = p.parse_args(argv)
    try:
        if a.out_receipt.is_symlink() or a.out_receipt.exists() or not a.out_receipt.parent.is_dir():
            raise EIOPAQuarantineBlocked("safe fresh receipt output path required")
        result = inspect_pair(a.local_loss_xlsx, a.local_exposure_xlsx)
        with a.out_receipt.open("x", encoding="utf-8") as out:
            out.write(json.dumps(result, sort_keys=True, indent=2) + "\n")
        print(json.dumps({
            "status": result["status"],
            "input_files": 2,
            "zip_CRC_passed": True,
            "source_attested_and_licensed": False,
            "cells_or_claims_loaded": False,
            "R_V_model_or_annual_EP_admitted": False,
        }, sort_keys=True))
        return 0
    except (EIOPAQuarantineBlocked, OSError, KeyError, TypeError) as exc:
        print("EIOPA_LOCAL_XLSX_QUARANTINE_BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
