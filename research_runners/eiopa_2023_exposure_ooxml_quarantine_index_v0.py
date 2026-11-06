# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Audit exact OOXML quarantine triggers in EIOPA exposure ZIP directory only.

No worksheet XML extraction, cell/formula inspection, relationship targets,
external links, embedded objects, source ZIP file names, or source workbooks
are published. Only pre-approved classification tags, sizes and SHA evidence.
One optional official HTTPS GET for source metadata; HTTP 429 is not retried.
A valid source SHA says nothing about dataset rights or model admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tempfile
from zipfile import ZipFile, BadZipFile

from eiopa_2023_ephemeral_official_xlsx_fetch_v0 import (
    URLS, EIOPAOriginalDownloadBlocked, bounded_single_request
)
from eiopa_catastrophe_2023_local_xlsx_metadata_preflight_v0 import (
    MAX_FILE_BYTES, MAX_MEMBERS, MAX_ONE_MEMBER, MAX_RATIO,
    MAX_TOTAL_UNCOMPRESSED, EIOPAQuarantineBlocked,
    inspect_original_xlsx
)

SOURCE_SHA256 = "f3ec03e25be247a798d94ea9d5ece8bd03a34bcc27b6faf99b597bbd863c3e79"
SOURCE_BYTES = 5593551
SCHEMA = "EIOPA_2023_EXPOSURE_OOXML_CENTRAL_DIRECTORY_QUARANTINE_DIAG_V0"
LIMIT = 40
SUSPECT_EXTENSIONS = (".bin", ".exe", ".dll", ".js", ".vbs")


class EIOPAQuarantineIndexBlocked(ValueError):
    pass


def safe_family(name: str) -> str:
    """Return ONLY fixed labels, never publish original untrusted ZIP paths."""
    for prefix, label in (
        ("xl/externalLinks/", "external_link"),
        ("xl/embeddings/", "embedded_object"),
        ("xl/activeX/", "active_x"),
        ("xl/vbaProject", "vba_project"),
        ("xl/worksheets/", "worksheet"),
        ("xl/printerSettings/", "printer_settings"),
        ("xl/drawings/", "drawing"),
        ("xl/media/", "image_media"),
        ("customXml/", "custom_xml"),
        ("xl/", "other_xl_part"),
        ("docProps/", "document_properties"),
        ("_rels/", "relationship_metadata"),
    ):
        if name.startswith(prefix):
            return label
    return "other_zip_part"


def inspect_zip_directory_without_cells(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise EIOPAQuarantineIndexBlocked("nonregular original XLSX")
    if path.suffix.lower() != ".xlsx" or path.stat().st_size != SOURCE_BYTES:
        raise EIOPAQuarantineIndexBlocked("original exposure file size/version not pinned")
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            sha.update(chunk)
    if sha.hexdigest() != SOURCE_SHA256:
        raise EIOPAQuarantineIndexBlocked("source original ZIP SHA changed from EIOPA TLS run")
    try:
        with ZipFile(path, "r") as z:
            infos = z.infolist()  # central ZIP headers only: NO open/read/testzip
    except BadZipFile as exc:
        raise EIOPAQuarantineIndexBlocked("original XLSX central directory malformed") from exc
    if not 3 <= len(infos) <= MAX_MEMBERS:
        raise EIOPAQuarantineIndexBlocked("unexpected source member count")
    if len({info.filename for info in infos}) != len(infos):
        raise EIOPAQuarantineIndexBlocked("duplicate source ZIP members")
    total = sum(info.file_size for info in infos)
    if total > MAX_TOTAL_UNCOMPRESSED * 4:
        raise EIOPAQuarantineIndexBlocked("central directory expansion exceeds audit cap")
    blocked = []
    families = {}
    for info in infos:
        n = info.filename
        family = safe_family(n)
        families[family] = families.get(family, 0) + 1
        reason = []
        p = PurePosixPath(n)
        if (not n or n.startswith("/") or "\\" in n or ".." in p.parts
            or info.flag_bits & 1 or info.is_dir()):
            reason.append("UNSAFE_OR_ENCRYPTED_ZIP_PATH")
        if n.startswith("xl/externalLinks/"):
            reason.append("EXTERNAL_LINK")
        if n.startswith("xl/embeddings/"):
            reason.append("EMBEDDED_OBJECT")
        if n.startswith("xl/activeX/"):
            reason.append("ACTIVE_X")
        if n.startswith("xl/vbaProject"):
            reason.append("VBA_PROJECT")
        if n.endswith(SUSPECT_EXTENSIONS):
            reason.append("BINARY_OR_EXECUTABLE_EXTENSION")
        if info.file_size > MAX_ONE_MEMBER:
            reason.append("SINGLE_MEMBER_EXPANDED_SIZE_LIMIT")
        if info.compress_size == 0 and info.file_size > 0:
            reason.append("IMPOSSIBLE_ZERO_COMPRESSED_BYTES")
        if info.compress_size and info.file_size > info.compress_size * MAX_RATIO:
            reason.append("COMPRESSION_RATIO_LIMIT")
        if reason and len(blocked) < LIMIT:
            blocked.append({
                "member_family_fixed_label": family,
                "why_original_strict_gate_blocks": reason,
                "declared_uncompressed_bytes": info.file_size,
                "declared_compressed_bytes": info.compress_size,
                "contains_any_spreadsheet_cell_values": False,
            })
    if len(blocked) == LIMIT:
        raise EIOPAQuarantineIndexBlocked("too many source offending entries to publish a useful bounded receipt")
    # Independent *source-pinned* metadata/CRC admission check. Only the
    # previously exact-SHA-pinned 5,420-byte printer driver blob is ignored
    # as nonfinancial metadata. All other macro/ActiveX/externalLink/unsafe
    # ZIP classes remain fail-closed. Never publish returned sheet names.
    try:
        source_pinned = inspect_original_xlsx(path, "FLOOD_WIND_EXPOSURE")
    except EIOPAQuarantineBlocked:
        source_pinned = None
    return {
        "source_pinned_original_workbook_metadata_CRC_quarantine_passed": source_pinned is not None,
        "source_pinned_original_workbook_sheet_count": (
            source_pinned["sheet_count"] if source_pinned is not None else None
        ),
        "source_pinned_printer_settings_blob_count_only": (
            source_pinned["source_pinned_printer_metadata_only_blob_count"]
            if source_pinned is not None else None
        ),
        "source_pinned_original_workbook_sheet_names_published": False,
        "source_pinned_nonfinancial_printer_settings_data_executed_or_interpreted": False,
        "schema": SCHEMA,
        "status": "SOURCE_OOXML_METADATA_ONLY_DIAGNOSTIC_NOT_CONTENT_ADMISSION",
        "source_family": "FLOOD_WIND_EXPOSURE",
        "official_source": URLS["FLOOD_WIND_EXPOSURE"],
        "whole_original_source_SHA256": SOURCE_SHA256,
        "original_file_size_bytes": SOURCE_BYTES,
        "member_count": len(infos),
        "aggregate_declared_uncompressed_bytes": total,
        "member_family_counts_fixed_labels": dict(sorted(families.items())),
        "strict_gate_observed_zip_metadata_blocker": bool(blocked),
        "flagged_member_entries_count": len(blocked),
        "flagged_member_categories_and_sizes_only": blocked,
        "all_ZIP_member_CRCs_checked": False,
        "original_member_filenames_published": False,
        "workbook_XML_or_worksheet_cells_read": False,
        "workbook_credentials_or_external_target_urls_read": False,
        "unsafe_original_OOXML_tolerated_or_executed": False,
        "data_mining_reuse_rights_verified": False,
        "EIOPA_individual_insurer_claims_or_property_locations_observed": False,
        "Ciara2020_insurer_NUTS2_loss_model_admitted": False,
        "Daria1990_insured_loss_or_Gross_Net_OEP_AEP_admitted": False,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--receipt", type=Path, required=True)
    a = p.parse_args()
    try:
        if a.receipt.is_symlink() or a.receipt.exists() or not a.receipt.parent.is_dir():
            raise EIOPAQuarantineIndexBlocked("source-only receipt must be a new regular path")
        with tempfile.TemporaryDirectory(prefix="eiopa-zip-metadata-only-") as tmp:
            path = Path(tmp) / "eiopa_official_exposure.xlsx"
            bounded_single_request(
                URLS["FLOOD_WIND_EXPOSURE"], path, "FLOOD_WIND_EXPOSURE"
            )
            result = inspect_zip_directory_without_cells(path)
            with a.receipt.open("x", encoding="utf-8") as output:
                json.dump(result, output, indent=2, sort_keys=True)
                output.write("\n")
        print(json.dumps({
            "status": result["status"],
            "member_count": result["member_count"],
            "flagged_member_count": result["flagged_member_entries_count"],
            "source_hash_pinned": True,
            "workbook_cell_data_read": False,
            "model_admitted": False,
        }, sort_keys=True))
        return 0
    except (EIOPAQuarantineIndexBlocked, EIOPAOriginalDownloadBlocked, OSError) as exc:
        p.exit(2, "EIOPA_ORIGINAL_OOXML_SOURCE_DIAG_BLOCKED: " + str(exc) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
