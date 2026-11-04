<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-singapore-ils-acra-mas-20261104.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-singapore-ils-acra-mas-20261104.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-04`  
**Purpose:** Non-admission discovery of Singapore original company-register, insurance regulator and ILS financial-source products with legal identity, historic claims and model-provenance constraints.

**Entries:** 3

## Singapore ACRA registered-entities government open-data snapshot

**Candidate ID:** `sg.acra.entities-registered.20261014`  
**Provider:** Accounting and Corporate Regulatory Authority (ACRA), Singapore  
**Categories:** `insurance`, `legal_entity`, `regulatory_identity`, `singapore`, `ils`  
**Spatial scope:** Singapore legal companies including insurance and special-purpose reinsurance entities  
**Temporal scope:** Monthly government dataset last updated 2026-10-14; coverage ending 2026-10-11  
**Resolution / granularity:** Exact company name, UEN, issuing agency, registration status, entity type, UEN issue date and street; four SPRV identifiers independently checked  
**Potential roles:** `singapore_uen_verification`, `insurance_spv_identity`, `mas_license_crosswalk`, `prevent_false_lei_fuzzy_matching`  
**Access hint:** `government_open_data_api_rights_and_current_company_status_review_pending`  
**Authoritative source:** <https://data.gov.sg/datasets/d_3f960c10fed6145404ca7b821f263b87/view>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original ACRA issuer and four exact UEN matches are checked and original JSON response SHA256 receipts are recorded. This dated public dataset is not a certified live Bizfile registry extract. Company registration does not establish a GLEIF LEI, licensed insurer portfolio, equity ownership or geolocated insured asset.

## MAS Singapore Financial Institutions Directory special-purpose reinsurance vehicles

**Candidate ID:** `sg.mas.fid.special-purpose-reinsurance.20261104`  
**Provider:** Monetary Authority of Singapore (MAS)  
**Categories:** `insurance`, `reinsurance`, `ils`, `legal_entity`, `regulation`, `singapore`  
**Spatial scope:** Licensed Singapore special-purpose reinsurance vehicles and service managers  
**Temporal scope:** Live official regulator directory viewed 2026-11-04; original page version must be independently archived  
**Resolution / granularity:** Institution name, regulator institution code, permitted reinsurance category and named operating manager; Astro RA16G, Manatee RA03G, Nakama RA18G and Tomoni RA21G  
**Potential roles:** `ils_legal_entity_and_license_crosswalk`, `special_purpose_vehicle_type`, `service_manager_is_not_parent_guard`  
**Access hint:** `public_regulator_directory_discovery_without_original_page_license_review`  
**Authoritative source:** <https://eservices.mas.gov.sg/fid/institution/detail/224391-MANATEE-RE-III-PTE-LTD>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Distinct from separately registered MAS annual company financial returns. A MAS-listed operating manager such as Marsh or Aon is not automatically a cedant, contract issuer, ultimate legal parent, equity owner or holder of insured risk. No complete customer or policy book is present.

## Signed audited Manatee Re III FY2024 and Hurricane Ida public claim observation

**Candidate ID:** `sg.manatee-re-iii.fy2024.audited-financial-statements`  
**Provider:** Manatee Re III Pte. Ltd., signed accounts hosted by Bermuda Stock Exchange  
**Categories:** `insurance`, `reinsurance`, `ils`, `company_report`, `cat_claim`, `reserving`  
**Spatial scope:** Singapore special-purpose reinsurer with one disclosed United States Hurricane Ida 2021 reinsurance loss  
**Temporal scope:** Fiscal year ended 2024-12-31 with 2023 comparative; directors signed 2025-04-29  
**Resolution / granularity:** Audited company notes identify Manatee Shares Trust ownership role, Safepoint Hurricane Ida Class A estimate, cumulative paid and remaining reserve, plus principal-at-risk notes  
**Potential roles:** `historical_ils_claim_validation`, `reinsurance_cedant_to_spv_claim_bridge`, `claims_paid_reserve_reconciliation`, `ownership_vs_ils_manager_separation`  
**Access hint:** `public_issuer_signed_financial_pdf_reuse_rights_and_actual_treaty_wording_review_pending`  
**Authoritative source:** <https://content.bsx.com/CompanyDocuments/1099939271/Manatee%20Re%20III%20-%20FS%20FY2024_final%20%28SIGNED%29.pdf>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original note 4 reports two-year exact paid-plus-reserve identities for one Ida event. Printed 28.57 percent is rounded and cannot be promoted as confirmed contract share; historical settlement is not complete policy wording, vendor event loss, insured TIV, retro settlement, FRS117 liability bridge or a CAT risk calibration.
