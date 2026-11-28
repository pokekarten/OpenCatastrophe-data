# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline verification of the EIOPA *binary retrieval evidence*, NOT loss data.

A hash obtained from a source URL by a retrieval proxy is not itself
independent TLS provenance, OOXML sheet/cell inspection, rights clearance,
or an actual German insurer loss observation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import tomllib

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "research/observations/eiopa_2023_original_xlsx_binary_source_receipt_20261106.toml"
SCHEMA = "EIOPA_2023_ORIGINAL_XLSX_BINARY_SOURCE_RECEIPT_V1"
ORIGINAL_SHA = "201bef4a15dccf4cb56edfe80fd2327b9bcd51ce3d815befb0730ffec5394fd6"
EXPOSURE_SHA = "f3ec03e25be247a798d94ea9d5ece8bd03a34bcc27b6faf99b597bbd863c3e79"
EXPECTED_URLS = {
    "HISTORICAL_INSURED_LOSSES":
        "https://www.eiopa.europa.eu/document/download/50e6b095-174c-4d9c-b9dd-1376dc1d43eb_en?filename=Historical+loss+data.xlsx",
    "FLOOD_WIND_EXPOSURE":
        "https://www.eiopa.europa.eu/document/download/d2be6f79-3e44-47f1-821f-97ff41e9d7b6_en?filename=Flood+and+Windstorm_exposure_data.xlsx",
}
EXPECTED_HEAD = {
    "schema": SCHEMA,
    "checked_as_of": "2026-11-06",
    "source_page": "https://www.eiopa.europa.eu/tools-and-data/catastrophe-data-hub_en",
    "publisher_attribution":
        "Source: EIOPA - European Insurance and Occupational Pensions Authority, https://eiopa.europa.eu/",
    "publisher_legal_notice": "https://www.eiopa.europa.eu/legal-notice_en",
    "binary_fetch_method": "Context.dev web_scrape formats.bytes from exact EIOPA publisher URL",
}
FALSE_FLAGS = {
    "third_party_workbook_rights_cleared",
    "original_workbook_bytes_published_or_committed",
    "original_workbook_rows_or_loss_cells_analyzed",
    "workbook_xml_sheet_names_verified",
    "zip_all_members_CRC_verified",
    "same_event_as_original_Daria1990",
    "german_RV_claims_or_insurer_sites_verified",
    "gross_net_GUL_IL_RI_OEP_AEP_admitted",
}
HEADER_FIELDS = set(EXPECTED_HEAD) | FALSE_FLAGS | {
    "proxy_transport_not_independent_origin_TLSPIN",
    "second_full_source_obtained_by_official_TLS_runner",
    "second_source_original_OOXML_security_quarantine_passed",
    "official_TLS_receipt_run_url", "official_TLS_receipt_artifact_id",
    "website_reproduction_attribution_reviewed", "note", "originals",
}
ATTACHMENT_FIELDS = {
    "id", "publisher_url", "publisher_listing_size", "retrieval_status",
    "whole_binary_sha256", "whole_binary_size_bytes", "content_type",
    "zip_central_directory_members", "zip_central_directory_worksheets",
    "full_zip_CRC_tested", "workbook_sheet_names_or_observed_losses_inspected",
    "sha256_repeat_independent_implementation_agreed",
    "licensed_claims_model_use_approved",
}


class EIOPASourceIntegrityBlocked(ValueError):
    """A source bytes/method claim exceeded what original evidence proves."""


def verify_source_receipt(d: dict) -> dict:
    if not isinstance(d, dict) or set(d) != HEADER_FIELDS:
        raise EIOPASourceIntegrityBlocked("original binary receipt schema drift")
    for key, val in EXPECTED_HEAD.items():
        if d[key] != val:
            raise EIOPASourceIntegrityBlocked("original publisher or receipt method changed: " + key)
    if any(d[k] is not False for k in FALSE_FLAGS):
        raise EIOPASourceIntegrityBlocked("unverified original-insurer/science/licence promotion")
    if (
        d["proxy_transport_not_independent_origin_TLSPIN"] is not True
        or d["website_reproduction_attribution_reviewed"] is not True
        or d["second_full_source_obtained_by_official_TLS_runner"] is not True
        or d["second_source_original_OOXML_security_quarantine_passed"] is not False
        or d["official_TLS_receipt_run_url"] != "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42270505316"
        or d["official_TLS_receipt_artifact_id"] != 13528648193
        or len(d["note"]) < 250
    ):
        raise EIOPASourceIntegrityBlocked("proxy provenance limitation or licence notice suppressed")
    originals = d["originals"]
    if not isinstance(originals, list) or len(originals) != 2:
        raise EIOPASourceIntegrityBlocked("two exact EIOPA original files expected")
    seen = set()
    for row in originals:
        if not isinstance(row, dict) or set(row) != ATTACHMENT_FIELDS:
            raise EIOPASourceIntegrityBlocked("original XLSX member evidence schema drift")
        ident = row["id"]
        if ident not in EXPECTED_URLS or ident in seen or row["publisher_url"] != EXPECTED_URLS[ident]:
            raise EIOPASourceIntegrityBlocked("original publisher URL identity mismatch or duplicate")
        seen.add(ident)
        if row["content_type"] != (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ):
            raise EIOPASourceIntegrityBlocked("original XLSX media type mismatch")
        for no in ("full_zip_CRC_tested", "workbook_sheet_names_or_observed_losses_inspected",
                   "licensed_claims_model_use_approved"):
            if row[no] is not False:
                raise EIOPASourceIntegrityBlocked("claims/workbook CRC/license not independently verified")
        if ident == "HISTORICAL_INSURED_LOSSES":
            if not (
                row["publisher_listing_size"] == "27.55 KB"
                and row["retrieval_status"] == "COMPLETE_BYTES_RETURNED_BY_SOURCE_PROXY"
                and row["whole_binary_sha256"] == ORIGINAL_SHA
                and row["whole_binary_size_bytes"] == 28209
                and row["zip_central_directory_members"] == 29
                and row["zip_central_directory_worksheets"] == 1
                and row["sha256_repeat_independent_implementation_agreed"] is True
            ):
                raise EIOPASourceIntegrityBlocked("unreproduced complete loss workbook SHA or ZIP facts")
        elif not (
            row["publisher_listing_size"] == "5.33 MB"
            and row["retrieval_status"] == "FULL_BYTES_FROM_EIOPA_TLS_GITHUB_RUNNER_OOXML_QUARANTINED"
            and row["whole_binary_sha256"] == EXPOSURE_SHA
            and row["whole_binary_size_bytes"] == 5593551
            and row["zip_central_directory_members"] == 0
            and row["zip_central_directory_worksheets"] == 0
            and row["sha256_repeat_independent_implementation_agreed"] is False
        ):
            raise EIOPASourceIntegrityBlocked("full exposure SHA does not clear OOXML safety or scientific rights")
    if seen != set(EXPECTED_URLS):
        raise EIOPASourceIntegrityBlocked("original EIOPA family identity drift")
    return {
        "schema": SCHEMA,
        "status": "TWO_ORIGINAL_XLSX_BINARY_SHAS_VERIFIED_EXPOSURE_OOXML_QUARANTINE_BLOCKED",
        "publisher_link_complete_binary_count": 2,
        "publisher_link_full_hash": ORIGINAL_SHA,
        "publisher_link_complete_bytes": 28209,
        "other_publisher_xlsx_has_full_binary": True,
        "original_exposure_full_SHA": EXPOSURE_SHA,
        "original_exposure_complete_bytes": 5593551,
        "original_exposure_SHA_independently_repeated": False,
        "original_exposure_OOXML_quarantine_passed": False,
        "insurer_claim_cells_analyzed": False,
        "original_XLSX_bytes_committed": False,
        "workbook_specific_rights_clearance": False,
        "actual_Daria1990_or_German_RV_loss_calibration": False,
        "annual_gross_net_OEP_AEP": False,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--receipt", type=Path, default=RECEIPT)
    args = p.parse_args()
    try:
        f = args.receipt
        if f.is_symlink() or not f.is_file() or f.stat().st_size > 14_000:
            raise EIOPASourceIntegrityBlocked("unsafe or unexpectedly large receipt")
        result = verify_source_receipt(tomllib.loads(f.read_text(encoding="utf-8")))
        print(json.dumps(result, sort_keys=True))
        return 0
    except (EIOPASourceIntegrityBlocked, OSError, tomllib.TOMLDecodeError,
            KeyError, TypeError, ValueError) as exc:
        p.exit(2, "EIOPA_BINARY_SOURCE_RECEIPT_BLOCKED: " + str(exc) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
