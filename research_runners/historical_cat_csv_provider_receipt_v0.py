# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Pinned metadata-only original provider bytes; not CAT model admission."""
import json

SOURCE_RECEIPT = json.loads(r"""{
  "schema_version": "research-source-byte-receipt-v0",
  "observed_on": "2026-10-31",
  "origin": "Full exact-version publisher-hosted Zenodo CSV bytes retrieved through HTTP byte ranges",
  "evidence_stage": "publisher_bytes_observed_not_model_admitted",
  "restriction": "metadata-only receipt; no original third-party data or insured CAT outputs",
  "sources": {
    "hanze_v3_0_2_beta": {
      "record_url": "https://zenodo.org/records/23670886",
      "api_url": "https://zenodo.org/api/records/23670886/files/HANZE_events_v3_0_2b.csv/content",
      "filename": "HANZE_events_v3_0_2b.csv",
      "source_version": "v3.0.2 beta",
      "publisher_date": "2026-10-30",
      "bytes": 699910,
      "publisher_md5": "0e49c409d7cc9b1d42196d9c7cf677a1",
      "observed_sha256": "44dc1861cf620d9e64085dc66159488237ca45df760d64042d921cd8b807ba66",
      "required_profile": {
        "event_count": 2780,
        "economic_loss_present_count": 1173,
        "economic_loss_missing_count": 1607,
        "observed_event_year_range": [
          1871,
          2025
        ]
      },
      "research_observations": {
        "event_country_codes_present": 40,
        "unique_regional_codes": 1290,
        "economic_loss_zero_count": 0,
        "geographic_admin_vintage": "2024",
        "euro_price_reference_year": "2025",
        "publisher_study_area_countries": 42
      },
      "notes": [
        "Reported historical economic losses are not insured claims",
        "No asset-level disaggregation from affected NUTS3 region codes",
        "Study coverage 42 countries differs from 40 observed country codes in current event rows",
        "Missing losses are not zero",
        "Earliest observed event is 1871 although full study period is 1870-2025"
      ],
      "admission_status": "not_admitted"
    },
    "residential_v2025": {
      "record_url": "https://zenodo.org/records/17828544",
      "api_url": "https://zenodo.org/api/records/17828544/files/Residential_exposure_v2025.csv/content",
      "filename": "Residential_exposure_v2025.csv",
      "source_version": "v2025",
      "publisher_date": "2025-12-05",
      "bytes": 177679,
      "publisher_md5": "9b0d11275526159675b91e8a6eacb3e9",
      "observed_sha256": "ce8cc1a1f83b9ee248cd6380597bc21be5a9e75a4e26d3fe1d102ff0ca25d0fa",
      "required_profile": {
        "indicator_country_row_count": 612,
        "numeric_cells_present": 15300,
        "numeric_cells_missing": 0,
        "observed_year_column_range": [
          2000,
          2024
        ]
      },
      "research_observations": {
        "indicator_count": 18,
        "geographic_codes": 34,
        "country_codes": 33,
        "eu_aggregate_present": true,
        "numeric_negative_cells": 0,
        "duplicate_indicator_country_rows": 0
      },
      "notes": [
        "National per-square-metre building and household contents values, not asset-level data",
        "EU geographic aggregate not independent country; avoid double-counting",
        "No insured sums, insurer ownership, exposure distributions or pricing contracts"
      ],
      "admission_status": "not_admitted"
    }
  }
}""")
