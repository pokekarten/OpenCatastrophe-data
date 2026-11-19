<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-air-verisk.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-air-verisk.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-02`  
**Purpose:** Non-admission discovery registry for Verisk AIR CAT-model data, open exposure interchange, restricted events, output interoperability, and public benchmark evidence.

**Entries:** 10

## CEDE 13.0 schema and AIRExposure, AIRReference and AIRReinsurance samples

**Candidate ID:** `verisk.cede.13-0.sample`  
**Provider:** Verisk Extreme Event Solutions (AIR Worldwide)  
**Categories:** `exposure`, `schema`, `reinsurance`, `interoperability`  
**Spatial scope:** Global interoperability format; sample coverage unverified  
**Temporal scope:** CEDE 13.0 (2025)  
**Resolution / granularity:** SQL Server 2022 backup files and database reference  
**Potential roles:** `air_exposure_crosswalk`, `reference_dictionary`, `reinsurance_mapping`  
**Access hint:** `public_documentation_and_sample_download_rights_review_pending`  
**Authoritative source:** <https://risksolutions.verisk.com/data-standards/cede-database-2025/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** CEDE is an open exposure schema, NOT an open AIR hazard/vulnerability model. Publisher offers sample .bak backups and separate CEDE License v1.0. Exact asset rights, sample bytes, retrieval, SHA256, and restore have not been checked. No admission or Neon import. CEDE 13.0 docs explicitly specify tLocation fields such as ISOBIN, LocationID, ReplacementValueA-D, AIROccupancyCode and AIRConstructionCodeA; 2025 changes add AverageHazardLevel/AverageHazardUserID and renewable-energy classifications. Use public schema for field mapping, not as evidence of source exposure observations; premium geocode export restrictions require separate review.

## CEDE 12.0 legacy schema and sample backups

**Candidate ID:** `verisk.cede.12-0.legacy`  
**Provider:** Verisk Extreme Event Solutions (AIR Worldwide)  
**Categories:** `exposure`, `schema`, `interoperability`  
**Spatial scope:** Global interchange format; sample coverage unverified  
**Temporal scope:** CEDE 12.0 predecessor  
**Resolution / granularity:** SQL Server 2022 .bak backups and legacy database reference  
**Potential roles:** `cede_version_crosswalk`, `legacy_exposure_interoperability`  
**Access hint:** `public_previous_schema_samples_rights_review_pending`  
**Authoritative source:** <https://risksolutions.verisk.com/data-standards/cede-12.0-database-schema/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Keep 12.0 and 13.0 identities separate; compare field and code differences explicitly. Public sample listing is not proof of data download or redistribution eligibility.

## AIREvents 2025 (13.1) catalogue table and climate-scenario documentation

**Candidate ID:** `verisk.airevents.13-1.catalogue`  
**Provider:** Verisk Extreme Event Solutions (AIR Worldwide)  
**Categories:** `event_catalogue`, `climate_scenario`, `flood`, `model_metadata`  
**Spatial scope:** Selected worldwide models, including Malaysia/Indonesia and Great Britain/Republic of Ireland  
**Temporal scope:** Touchstone 2025 (13.1); SSP horizons 2040 and 2050  
**Resolution / granularity:** Model 17 and 92 stochastic 10K event set tables and SSP scenario catalog descriptions  
**Potential roles:** `event_catalogue_schema`, `climate_scenario_inventory`, `peril_model_registry`  
**Access hint:** `public_schema_only_restricted_event_tables_on_request`  
**Authoritative source:** <https://docs.risksolutions.verisk.com/Database/AIREvents/13.1/topic1.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Verisk documents Malaysia/Indonesia inland flood and GB/ROI inland flood SSP event sets, requested via Verisk representative; notes no geospatial/hazard analysis support for these climate event sets. Underlying event data are not publicly available for arbitrary use. Pin catalog vintage, model, scenario, time horizon.

## AIREvents and AIREventsHistorical catalogue access terms

**Candidate ID:** `verisk.airevents.10-0.access`  
**Provider:** Verisk Extreme Event Solutions (AIR Worldwide)  
**Categories:** `event_catalogue`, `historical_events`, `access_policy`  
**Spatial scope:** Only perils and models covered by purchased licence  
**Temporal scope:** Documentation release 10.0; later terms must be verified separately  
**Resolution / granularity:** 10K and 50K stochastic catalogues; separate historical and extreme scenario tables  
**Potential roles:** `licensed_catalogue_access_decision`, `historical_stochastic_crosswalk`  
**Access hint:** `public_documentation_licensed_data_on_request`  
**Authoritative source:** <https://docs.risksolutions.verisk.com/Database/AIREvents/10.0/topic1.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official documentation says AIREvents are not included in standard software database install and are available on request for licensed models. Do not call event rows open data.

## Touchstone Re 13.0 exportable event, annual and treaty loss reports

**Candidate ID:** `verisk.touchstone-re.13-0.reports`  
**Provider:** Verisk Extreme Event Solutions (AIR Worldwide)  
**Categories:** `loss`, `event_loss`, `annual_loss`, `ep_curve`, `reinsurance`  
**Spatial scope:** Any model-covered licensed portfolio; no open portfolio implied  
**Temporal scope:** Touchstone Re 13.0  
**Resolution / granularity:** Event Distribution nonzero event loss, Annual EP Detail nonzero annual loss, Summary EP, treaty and historical loss CSV reports  
**Potential roles:** `elt_csv_adapter_research`, `annual_loss_yelt_mapping`, `reinsurance_results_semantics`  
**Access hint:** `public_output_documentation_licensed_execution_required`  
**Authoritative source:** <https://docs.risksolutions.verisk.com/TouchstoneRe/13.0/ts-tsre_all/help_tsre_export_reports-to-generate.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Report selection is NOT a public event loss file. Preserve financial perspective, currency, event ID, simulation year, model/catalog version, zero-loss suppression, annual aggregation and secondary-uncertainty assumptions.

## Touchstone Re 13.0 ELT/YELT Analyze Re transfer

**Candidate ID:** `verisk.touchstone-re.13-0.elt-yelt`  
**Provider:** Verisk Extreme Event Solutions (AIR Worldwide)  
**Categories:** `loss`, `elt`, `yelt`, `interoperability`  
**Spatial scope:** Licensed modelled output across supported model regions  
**Temporal scope:** Touchstone Re 13.0  
**Resolution / granularity:** ELT default or YELT integration; Analyze Re upload supports 10K catalog only  
**Potential roles:** `elt_yelt_interoperability`, `year_event_identity_mapping`  
**Access hint:** `public_interface_documentation_licensed_transfer_not_open_data`  
**Authoritative source:** <https://docs.risksolutions.verisk.com/TouchstoneRe/13.0/ts-tsre_all/help_tsre_export_upload-loss-to-analyze-re.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Verisk documents ELT/YELT export to Analyze Re; 50K/100K/500K and ALERT event sets excluded from this upload. No downloadable public ELT is established.

## Touchstone 13.0 encoded Company Loss File export

**Candidate ID:** `verisk.touchstone.13-0.clf`  
**Provider:** Verisk Extreme Event Solutions (AIR Worldwide)  
**Categories:** `loss`, `reinsurance`, `encoded_export`  
**Spatial scope:** Licensed modelled exposures and treaties  
**Temporal scope:** Touchstone 13.0  
**Resolution / granularity:** Encoded CLF and EVT files with descriptive EVI summary; per peril/model/loss perspective  
**Potential roles:** `encoded_clf_boundary`, `licensed_loss_export_contract`  
**Access hint:** `public_format_description_encoded_data_proprietary`  
**Authoritative source:** <https://docs.risksolutions.verisk.com/Touchstone/13.0/ts-tsre_all/help_ts_export_loss-results-clf.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** CLF is not a plain CSV event loss table. Preserve model, catalog, currency, perspective and event ID; export requires authorized software and model data.

## Verisk ALERT recent event bulletins and subscriber scenario assets

**Candidate ID:** `verisk.alert.2026.events`  
**Provider:** Verisk Extreme Event Solutions (AIR Worldwide)  
**Categories:** `hazard`, `real_event`, `flood`, `modelled_footprint`, `access_policy`  
**Spatial scope:** Worldwide, event-dependent  
**Temporal scope:** Rolling historical and contemporary bulletins, checked 2026-11-02  
**Resolution / granularity:** Public event narratives, industry estimates and mentions of subscriber hazard shapefiles/custom event sets  
**Potential roles:** `public_real_event_metadata`, `restricted_footprint_access_registry`  
**Access hint:** `public_bulletins_confidential_subscriber_downloads`  
**Authoritative source:** <https://alert.risksolutions.verisk.com/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** German and Central European 2024 flood postings advertise event sets, loss-based similar stochastic events and shapefiles but explicitly restrict disclosure. No downloads of restricted vendor assets, no inclusion in Neon or Git; bulletin values are not observed ground-truth footprints.

## Verisk 2026 global modelled insured catastrophe loss benchmark

**Candidate ID:** `verisk.global-cat-loss.2026`  
**Provider:** Verisk Extreme Event Solutions (AIR Worldwide)  
**Categories:** `benchmark`, `aal`, `ep_curve`, `insured_loss`, `global`  
**Spatial scope:** Global insurance industry risks within vendor model coverage  
**Temporal scope:** Provider release dated 2026-09-01; long-run modelled metrics, not realised annual loss  
**Resolution / granularity:** AAL USD 171bn; aggregate 100-year EP USD 477bn; 250-year EP USD 606bn  
**Potential roles:** `global_insured_aal_benchmark`, `aggregate_ep_sanity_check`, `peril_mix_context`  
**Access hint:** `public_provider_press_aggregate_only_reuse_rights_unreviewed`  
**Authoritative source:** <https://www.globenewswire.com/news-release/2026/09/01/3353840/0/en/global-insured-catastrophe-losses-now-expected-to-average-171-billion-annually-verisk-finds.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** These are Verisk simulations for global insured industry, not company-specific losses, location-level exposure, stochastic events, or a prediction for 2026. AAL/EP cannot by themselves calibrate hazard/vulnerability. Preserve report date, global insured scope, currency and model vintage.

## Verisk Underwriting AIR Catastrophe Hazard Hurricane location API

**Candidate ID:** `verisk.gateway.air-hurricane-hazard.v1`  
**Provider:** Verisk Analytics, Inc.  
**Categories:** `hazard`, `hurricane`, `underwriting`, `api`, `location_risk`  
**Spatial scope:** Location-based U.S. hurricane underwriting service; service coverage requires contract confirmation  
**Temporal scope:** API v1 documentation checked 2026-11-02; live service/version status not verified  
**Resolution / granularity:** HTTP POST request with address or geocode; JSON/XML report response description; authenticated by service token  
**Potential roles:** `licensed_site_hurricane_hazard_enrichment`, `air_hazard_api_contract_discovery`  
**Access hint:** `public_api_docs_private_token_and_org_entitlement_required_no_live_probe`  
**Authoritative source:** <https://gateway.verisk.com/docs/AIR-Catastrophe-Hazard-Hurricane-PL.ashx>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official gateway documents a hurricane location hazard report with address or geocode POST and bearer authentication. The documentation is not evidence of a free data API, licensed access, open event loss catalogue, or permission to store/export replies. Do not copy example access tokens from public documentation into code or logs. No credential, request or response tested.
