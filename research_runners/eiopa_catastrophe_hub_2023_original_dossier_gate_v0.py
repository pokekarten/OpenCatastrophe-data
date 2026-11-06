# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline source-identity and scientific no-admission gate for EIOPA 2023.

Uses only public publisher metadata and the EIOPA technical document.
No remote GET, original EIOPA workbook bytes, personal/company rows,
training/calibration, annual occurrence model or insurer loss execution.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tomllib
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research/observations/eiopa_catastrophe_hub_2023_original_dossier_v0.toml"
SCHEMA = "EIOPA_CATASTROPHE_HUB_2023_OFFICIAL_DOCS_NO_WORKBOOK_INGEST_V0"
EXPECTED_ATTACHMENTS = {
    "TECHNICAL_NOTE": (
        "https://www.eiopa.europa.eu/document/download/874847f3-8ff1-4471-ad04-056855d05a3d_en?filename=Technical+description+-+Catastrophe+Data+Hub.pdf",
        "582.04 KB", 14,
    ),
    "HISTORICAL_INSURED_LOSSES": (
        "https://www.eiopa.europa.eu/document/download/50e6b095-174c-4d9c-b9dd-1376dc1d43eb_en?filename=Historical+loss+data.xlsx",
        "27.55 KB", 0,
    ),
    "FLOOD_WIND_EXPOSURE": (
        "https://www.eiopa.europa.eu/document/download/d2be6f79-3e44-47f1-821f-97ff41e9d7b6_en?filename=Flood+and+Windstorm_exposure_data.xlsx",
        "5.33 MB", 0,
    ),
}
EXPECTED_STRING = {
    "schema": SCHEMA,
    "checked_as_of": "2026-11-06",
    "publisher": "EIOPA - European Insurance and Occupational Pensions Authority",
    "publication_date": "2023-12-05",
    "technical_note_id": "EIOPA-BoS-22/505",
    "technical_note_date": "2023-11-27",
    "hub_url": "https://www.eiopa.europa.eu/tools-and-data/catastrophe-data-hub_en",
    "technical_note_pdf": "https://www.eiopa.europa.eu/system/files/2023-12/Technical%20description%20-%20Catastrophe%20Data%20Hub.pdf",
    "legal_notice_url": "https://www.eiopa.europa.eu/legal-notice_en",
    "original_pdf_sha256": "NOT_ACQUIRED",
    "historical_loss_workbook_sha256": "201bef4a15dccf4cb56edfe80fd2327b9bcd51ce3d815befb0730ffec5394fd6",
    "exposure_workbook_sha256": "f3ec03e25be247a798d94ea9d5ece8bd03a34bcc27b6faf99b597bbd863c3e79",
    "historical_loss_workbook_original_source_byte_receipt":
        "research/observations/eiopa_2023_original_xlsx_binary_source_receipt_20261106.toml",
    "insured_wind_claim_event": "CIARA_SABINE_FEBRUARY_2020",
    "other_insured_claim_event_1": "PORTUGAL_WILDFIRE_JUNE_2017",
    "other_insured_claim_event_2": "CENTRAL_EUROPE_FLOOD_JUNE_2013",
    "observed_loss_class": "INCURRED_REPORTED_BUILDING_AND_OTHER_INSURED_CLAIMS",
    "insured_exposure_reference_date": "2020-12-31",
    "original_exposure_resolution": "CRESTA_LOW_RESOLUTION_OR_NUTS3",
    "public_exposure_and_loss_resolution": "NUTS2_ANONYMIZED_NO_SITE",
    "building_sum_insured_basis": "EIOPA_DESCRIPTION_NET_OF_REINSURANCE_BUSINESS_AND_COINSURANCE",
    "sample_EEA_2020_property_fire_GWP_coverage_numerator":
        "58.3PCT_TABLE_4_APPROX_59PCT_TEXT",
    "sample_Germany_2020_property_fire_GWP_coverage": "63.6PCT_TABLE_4",
    "admission": "PUBLIC_METADATA_REFERENCE_ONLY_NO_DARIA_FIT_NO_RV_POLICY_NO_EP",
    "source_event_and_workbook_rights_status":
        "Official EIOPA HTTPS GitHub Actions run 42270505316 delivered both originals: historical loss 28209 bytes SHA256 201bef4a15dccf4cb56edfe80fd2327b9bcd51ce3d815befb0730ffec5394fd6 and exposure 5593551 bytes SHA256 f3ec03e25be247a798d94ea9d5ece8bd03a34bcc27b6faf99b597bbd863c3e79. Generic OOXML quarantine initially blocked one printerSettings binary; original source-SHA-pinned 5420B printerSettings metadata-only exception passed full ZIP CRC and one workbook sheet in GitHub Actions 42292320403. No insurer claim cells, workbook-specific third-party rights, German wind loss calibration or annual EP verified.",
}
EXPECTED_BOOLEANS = {
    "workbook_content_read_or_modelled": False,
    "publisher_general_reproduction_requires_credit": True,
    "publisher_transformed_redistribution_requires_special_notice": True,
    "publisher_third_party_rights_automatically_cleared": False,
    "insurer_site_data_or_German_model_calibration_admitted": False,
    "reinsurance_treaty_or_annual_frequency_verified": False,
    "insurer_Daria_1990_claim_event_available": False,
    "residential_commercial_loss_split_always_available": False,
    "direct_GUL_IL_RI_definition_usable_without_contract_terms": False,
    "same_2020_wind_claim_event_and_1990_Daria_hazard": False,
    "sample_is_100_percent_market": False,
    "premium_share_can_be_treated_as_buildings_or_contracts_share": False,
    "GWP_sample_covers_RV_geolocated_NRW_book": False,
    "licence_workbook_specific_restrictions_checked": False,
    "actual_eiopa_xlsx_bytes_obtained_in_this_research": True,
    "exposure_generic_unpinned_OOXML_policy_passed": False,
    "exposure_source_pinned_CRC_sheet_metadata_passed": True,
    "exposure_financial_cells_model_admitted": False,
}
EXPECTED_INTEGERS = {
    "each_disclosed_data_point_minimum_independent_company_submissions": 3,
    "historical_loss_workbook_binary_bytes": 28209,
    "exposure_workbook_binary_bytes": 5593551,
    "sample_groups": 35,
    "sample_solo_undertakings": 9,
}
EXPECTED_MISC = {"insured_exposure_perils", "original_attachments"}


class EIOPAEvidenceBlocked(ValueError):
    """Source claim not grounded by original EIOPA official documentation."""


def validate_evidence(doc: dict) -> dict:
    if not isinstance(doc, dict) or set(doc) != (
        set(EXPECTED_STRING) | set(EXPECTED_BOOLEANS) |
        set(EXPECTED_INTEGERS) | EXPECTED_MISC
    ):
        raise EIOPAEvidenceBlocked("EIOPA original evidence shape changed")
    for name, value in EXPECTED_STRING.items():
        if type(doc[name]) is not str or doc[name] != value:
            raise EIOPAEvidenceBlocked("EIOPA original documented event, rights or vintage changed: " + name)
    for name, value in EXPECTED_BOOLEANS.items():
        if type(doc[name]) is not bool or doc[name] is not value:
            raise EIOPAEvidenceBlocked("unsupported EIOPA insurer-model or workbook-rights promotion: " + name)
    for name, value in EXPECTED_INTEGERS.items():
        if type(doc[name]) is not int or doc[name] != value:
            raise EIOPAEvidenceBlocked("EIOPA company/anonymous minimum denominator changed: " + name)
    if doc["insured_exposure_perils"] != ["WINDSTORM", "FLOOD"]:
        raise EIOPAEvidenceBlocked("EIOPA exposure-peril set differs from publication")
    att = doc["original_attachments"]
    if not isinstance(att, list) or len(att) != len(EXPECTED_ATTACHMENTS):
        raise EIOPAEvidenceBlocked("missing one of three original source attachments")
    seen = set()
    for item in att:
        if not isinstance(item, dict) or set(item) != {
            "id", "name", "publisher_size_label", "page", "original_url", "source_sha256"
        }:
            raise EIOPAEvidenceBlocked("EIOPA publication attachment contract drift")
        ident = item["id"]
        if ident not in EXPECTED_ATTACHMENTS or ident in seen:
            raise EIOPAEvidenceBlocked("missing or repeated original EIOPA file identity")
        seen.add(ident)
        expected_url, expected_size, page = EXPECTED_ATTACHMENTS[ident]
        if (
            item["original_url"] != expected_url
            or item["publisher_size_label"] != expected_size
            or type(item["page"]) is not int or item["page"] != page
            or item["source_sha256"] != {
                "TECHNICAL_NOTE": "NOT_ACQUIRED",
                "HISTORICAL_INSURED_LOSSES":
                    "201bef4a15dccf4cb56edfe80fd2327b9bcd51ce3d815befb0730ffec5394fd6",
                "FLOOD_WIND_EXPOSURE":
                    "f3ec03e25be247a798d94ea9d5ece8bd03a34bcc27b6faf99b597bbd863c3e79",
            }[ident]
            or not item["name"].endswith(".pdf" if page else ".xlsx")
            or urlparse(item["original_url"]).hostname != "www.eiopa.europa.eu"
        ):
            raise EIOPAEvidenceBlocked("original EIOPA document URL/size/sha unverified or drifted")
    if seen != set(EXPECTED_ATTACHMENTS):
        raise EIOPAEvidenceBlocked("EIOPA expected appendix source population incomplete")
    return {
        "schema": SCHEMA,
        "status": "EIOPA_CIARA_2020_NUTS2_SAMPLE_REFERENCE_ONLY_NOT_DARIA_1990",
        "public_original_publisher_attachments_named": 3,
        "original_loss_workbook_bytes_fetched_via_proxy": True,
        "original_exposure_workbook_complete_bytes_fetched": True,
        "original_exposure_workbook_sha256_from_official_TLS": "f3ec03e25be247a798d94ea9d5ece8bd03a34bcc27b6faf99b597bbd863c3e79",
        "original_exposure_generic_unpinned_OOXML_policy_passed": False,
        "original_exposure_source_pinned_CRC_sheet_metadata_passed": True,
        "original_exposure_financial_cells_rights_admitted": False,
        "original_loss_workbook_sha256_from_source_proxy": "201bef4a15dccf4cb56edfe80fd2327b9bcd51ce3d815befb0730ffec5394fd6",
        "original_exposure_workbook_sha256_verified": True,
        "wind_insured_loss_event_is_only_Ciara_2020": True,
        "Daria_1990_insured_claims_provided": False,
        "source_residential_commercial_splits_can_be_suppressed": True,
        "source_sample_coverage_is_premium_not_building_share": True,
        "German_insurer_site_loss_calibration_approved": False,
        "insured_GUL_IL_RI_OEP_AEP_model_executed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=SOURCE)
    a = parser.parse_args()
    try:
        if a.evidence.is_symlink() or not a.evidence.is_file() or a.evidence.stat().st_size > 25_000:
            raise EIOPAEvidenceBlocked("untrusted or overly large source register")
        doc = tomllib.loads(a.evidence.read_text(encoding="utf-8"))
        print(json.dumps(validate_evidence(doc), sort_keys=True))
        return 0
    except (EIOPAEvidenceBlocked, OSError, tomllib.TOMLDecodeError, TypeError, KeyError) as exc:
        parser.exit(2, "EIOPA_ORIGINAL_DOC_SCIENCE_BLOCKED: " + str(exc) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
