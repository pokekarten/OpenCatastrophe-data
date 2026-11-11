# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict source-bound EIOPA OOXML *metadata-only* successful CRC proof.

This is a reproducible independent evidence audit: no original workbook bytes,
no sheet names, no claim cells, no data mining, no extrapolation to R&V GUL/RI.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "research/observations/eiopa_2023_exposure_source_pinned_ooxml_metadata_receipt_20261106.toml"
SCHEMA = "EIOPA_2023_EXPOSURE_SOURCE_PINNED_OOXML_METADATA_RECEIPT_V0"
EXPECTED = {
    "schema": SCHEMA,
    "checked_as_of": "2026-11-06",
    "official_publisher": "EIOPA - European Insurance and Occupational Pensions Authority",
    "source_url": "https://www.eiopa.europa.eu/document/download/d2be6f79-3e44-47f1-821f-97ff41e9d7b6_en?filename=Flood+and+Windstorm_exposure_data.xlsx",
    "source_sha256": "f3ec03e25be247a798d94ea9d5ece8bd03a34bcc27b6faf99b597bbd863c3e79",
    "original_source_bytes": 5593551,
    "original_zip_members": 31,
    "original_zip_total_declared_expanded_bytes": 76586443,
    "diagnosis_run_url": "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42291363788",
    "source_pinned_success_run_url": "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42292320403",
    "source_pinned_evidence_artifact_id": 13540506478,
    "source_pinned_evidence_artifact_expires_utc": "2026-11-20T20:54:55Z",
    "source_pinned_metadata_quarantine_status":
        "PASS_METADATA_AND_CRC_ONLY_NOT_INSURER_CLAIMS",
    "original_printer_settings_blob_count": 1,
    "original_printer_settings_expanded_bytes": 5420,
    "original_printer_settings_compressed_bytes": 443,
    "source_pinned_original_workbook_sheet_count": 1,
}
TRUE_FIELDS = {
    "generic_binary_scanner_reported_single_printer_settings_member",
    "source_sha_pinned_printer_metadata_only_exception_applied",
    "source_pinned_original_zip_all_member_CRC_verified",
}
FALSE_FIELDS = {
    "original_binary_bytes_redistributed",
    "original_filename_or_workbook_cell_data_published",
    "other_macro_external_embedded_object_exceptions_added",
    "printer_driver_binary_interpreted_or_executed",
    "printer_driver_raw_bytes_published",
    "source_pinned_workbook_sheet_names_published",
    "source_pinned_workbook_cells_or_formula_values_read_for_semantics",
    "original_workbook_specific_licence_and_tdm_rights_cleared",
    "insurer_building_exposure_values_or_claim_cells_ingested",
    "ciara2020_event_specific_NUTS2_insured_loss_join_verified",
    "R_V_insurer_portfolio_or_GUL_IL_RI_OEP_AEP_model_admitted",
    "source_sha_independently_repeated_twice",
}


class EIOPAMetadataAdmissionBlocked(ValueError):
    pass


def validate_receipt(data: dict) -> dict:
    if not isinstance(data, dict) or set(data) != set(EXPECTED) | TRUE_FIELDS | FALSE_FIELDS:
        raise EIOPAMetadataAdmissionBlocked("expected original source receipt metadata only")
    for k, v in EXPECTED.items():
        if type(data[k]) is not type(v) or data[k] != v:
            raise EIOPAMetadataAdmissionBlocked("source original hash, archive, method or receipt drift: " + k)
    for k in TRUE_FIELDS:
        if data[k] is not True:
            raise EIOPAMetadataAdmissionBlocked("source pinned metadata CRC evidence missing: " + k)
    for k in FALSE_FIELDS:
        if data[k] is not False:
            raise EIOPAMetadataAdmissionBlocked("unsafe Excel, licence or insurer loss promotion: " + k)
    return {
        "schema": SCHEMA,
        "status": "SOURCE_PINNED_EIOPA_EXPOSURE_CRC_AND_SHEET_METADATA_VERIFIED_NO_CLAIMS",
        "source_SHA_verified": EXPECTED["source_sha256"],
        "original_zip_entries": EXPECTED["original_zip_members"],
        "printer_settings_blob_excluded_from_semantic_interpretation": True,
        "all_zip_CRC_verified": True,
        "sheet_count": 1,
        "source_workbook_licence_approved": False,
        "worksheet_cells_or_insurer_amounts_interpreted": False,
        "R_V_insurer_GUL_IL_RI_OEP_AEP_admitted": False,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--receipt", type=Path, default=RECEIPT)
    args = p.parse_args()
    try:
        target = args.receipt
        if target.is_symlink() or not target.is_file() or target.stat().st_size > 10_000:
            raise EIOPAMetadataAdmissionBlocked("unsafe/oversized local receipt")
        out = validate_receipt(tomllib.loads(target.read_text(encoding="utf-8")))
        print(json.dumps(out, sort_keys=True))
        return 0
    except (EIOPAMetadataAdmissionBlocked, OSError, tomllib.TOMLDecodeError, TypeError) as exc:
        p.exit(2, "EIOPA_OOXML_METADATA_RECEIPT_NO_GO: " + str(exc) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
