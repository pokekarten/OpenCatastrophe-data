<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-material-flood-insurance-priors-20261108.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-material-flood-insurance-priors-20261108.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-08`  
**Purpose:** Non-admission discovery of three source-specific 2026 global building material, Korean industrial property insurance, and US flood claim validation candidates; source bytes and use approval excluded.

**Entries:** 3

## MaterialCities 2026.9 global floor area and construction material stocks

**Candidate ID:** `leiden.materialcities.global-floor-material-stock.2026-9`  
**Provider:** Leiden University and MaterialCities research consortium / Zenodo  
**Categories:** `buildings`, `building_typologies`, `construction_materials`, `gross_floor_area`, `exposure_prior`  
**Spatial scope:** Worldwide settlements and administrative aggregations, with country, ADM1, ADM2 and urban-centre products  
**Temporal scope:** Version 2026.9 released 2026-09-08; a modelled historical/representative stock estimate, not an annually observed 2026 building census  
**Resolution / granularity:** CSV and GeoPackage data with gross floor area and eight material masses by three building functions and five structural types; NLC settlement geography, ADM0-ADM2 and 2026.9 urban-centre views; model uncertainty variants p05/p25/p50/p75/p95  
**Potential roles:** `global_structural_type_prior`, `building_floor_area_regional_control`, `construction_material_exposure_proxy`, `synthetic_portfolio_vulnerability_covariate`  
**Access hint:** `public_zenodo_2026_9_csv_gpkg_download_license_and_upstream_gadm_4_1_rights_review_required`  
**Authoritative source:** <https://zenodo.org/records/22306604>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The original publisher describes floor area and modelled material stocks for 1.8 million settlements; this is not an inventory of individually insured buildings. ADM labels use GADM 4.1 and floor-area modelling draws on WSF3D and GHSL; upstream lineage, geographical vintage, release-specific rights, adaptation/commercial permissions and the limits of class imputation must be verified. Use ADM2 and structural-type shares as uncertain regional priors, not building-level occupancy, exact TIV or insurer market share. No data bytes downloaded or admitted in this source-landscape entry.

## Korean Financial Services Commission corporate property insurance subscriptions API

**Candidate ID:** `kr.fsc.corporate-property-insurance-subscription.api`  
**Provider:** Financial Services Commission / Republic of Korea Open Government Data Portal  
**Categories:** `insurance`, `property_insurance`, `commercial_industrial`, `premiums`, `insurance_penetration`  
**Spatial scope:** Republic of Korea, national contract/property categories; no confirmed geocoded insurer-site coverage  
**Temporal scope:** Government endpoint registered 2023-11-09, revised 2025-07-17; query by statistical reference year, available years and refresh need live authenticated confirmation  
**Resolution / granularity:** REST API JSON/XML; aggregate insurance contract counts and written premiums differentiated by insured object (such as factories and warehouses) and coverage including fire and explosion  
**Potential roles:** `industrial_insurance_coverage_prior`, `synthetic_sector_portfolio_weights`, `market_premium_benchmark`, `commercial_property_class_control`  
**Access hint:** `public_catalogue_free_api_requires_registered_servicekey_authentication_and_exact_licence_review`  
**Authoritative source:** <https://www.data.go.kr/en/data/15124894/openapi.do>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher lists free use and a broad permission scope, but API operation needs an issued serviceKey and applicable portal/service terms still require product-specific review. No authorized key was used, and response rows, availability for 2025/2026 or field-level semantics have not been independently tested. Contract and premium aggregates are not insured sums, catastrophe premium, insured building coordinates, claims, insurer market shares or TIV; do not derive TIV from premiums without explicit sensitivity assumptions. Keep source research-only and do not put credentials or retrieved records in Git.

## Kawakami 2026 v2 spatially and temporally refined CONUS pluvial NFIP claims

**Candidate ID:** `us.nfip.pluvial-claims-spatiotemporal-refinement.v2`  
**Provider:** Yuya Kawakami, UC Davis / Zenodo; underlying FEMA OpenFEMA NFIP and NOAA AORC  
**Categories:** `flood`, `insurance_claims`, `loss_validation`, `pluvial_flood`, `geospatial_uncertainty`  
**Spatial scope:** Contiguous United States and District of Columbia; not all United States and not global; public NFIP program claims only  
**Temporal scope:** Zenodo v2 published 2026-09-28, derived from FEMA redacted claims v3 snapshot 2026-09-25; source claims cover multiple loss years  
**Resolution / granularity:** Parquet release of 1,150,659 pluvial claim rows and 115 columns; loss dollars in constant 2021 currency, bounded location polygons and rainfall-conditioned alternative loss-date candidate  
**Potential roles:** `pluvial_claim_frequency_validation`, `flood_damage_out_of_sample_challenge`, `location_uncertainty_sensitivity`, `historical_event_loss_timing_challenge`  
**Access hint:** `public_zenodo_cc_by_4_claimed_derived_claim_level_parquet_underlying_fema_privacy_rights_and_scientific_review_pending`  
**Authoritative source:** <https://zenodo.org/records/23020968>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Public dataset is derived from FEMA NFIP redacted claims; approximate reported spatial signals only bound the location polygon and date changes within +/-7 days are heuristic, never verified ground truth. Do not reconstruct insured addresses or imply precise claims geography. Zenodo lists CC BY 4.0 for the released dataset, but underlying FEMA data terms, re-identification/privacy risk, source date and event leakage must be independently assessed before any sample acquisition, publication or loss-model admission. No claim rows or provider bytes acquired or committed.
