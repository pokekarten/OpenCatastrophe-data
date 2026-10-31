# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Metadata-only reproducibility receipt; not provider data or model admission."""

GISCO_2024_HANZE_RECEIPT = {
    "schema_version": "gisco-hanze-region-id-evidence-v0",
    "source": "Eurostat GISCO NUTS_AT_2024.csv",
    "source_url": "https://gisco-services.ec.europa.eu/distribution/v2/nuts/csv/NUTS_AT_2024.csv",
    "source_sha256": "2dab51394b7dc50eb18eb2ec37c5a69993a1b955af8d203d19e899581c4d9ee1",
    "source_original_byte_length": 92282,
    "source_attribute_rows": 1971,
    "source_country_count": 39,
    "source_nuts_level_row_counts": {"0": 39, "1": 123, "2": 326, "3": 1483},
    "original_data_reproduction_run": "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41248637806",
    "hanze_and_dfo_original_sources_sha256_pinned": True,
    "dfo_hanze_country_time_candidate_pairs": 9,
    "gisco_exact_single_region_eligible_pairs": 0,
    "hanze_noncanonical_or_multi_region_raw_code_pairs": 9,
    "unmatched_id_implies_no_geographic_exposure": False,
    "admin_code_is_a_flood_geometry": False,
    "insurer_assets_or_losses_computed": False,
    "source_data_redistributed": False,
    "rights_review_completed": False,
    "commercial_use_approved": False,
    "source_admitted": False,
    "geography_source_notice": (
        "Eurostat GISCO territorial/statistical geodata terms limit ordinary "
        "downloads to noncommercial use and require attribution. "
        "Commercial use requires separate EuroGeographics licensing review."
    ),
    "rights_url": "https://ec.europa.eu/eurostat/en/web/gisco/geodata/statistical-units",
    "interpretation": (
        "This GISCO table is verified and contains no polygons. "
        "All 9 candidate HANZE original admin-unit-code cells are composite or "
        "noncanonical relative to one 2024 NUTS_ID. They must NOT be treated "
        "as nine absent places. Prefer separate exact HANZE v3 region glossary "
        "and 2024 mapping review before any geometry."
    ),
}
