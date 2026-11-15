<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-peer-cat-repositories-20261102.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-peer-cat-repositories-20261102.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-02`  
**Purpose:** Non-admission review of external original datasets and access leads found while auditing 20 peer catastrophe-risk, disaster-data, satellite-damage and insurance model repositories. Software references are not dataset admissions; accepted existing GEM GEID, GFDRR Risk Data Library and Oasis/USGS source identities are not duplicated.

**Entries:** 11

## IFRC Montandon Global Crisis Data Bank event, hazard and impact API

**Candidate ID:** `ifrc.montandon.global-crisis-data-bank.api`  
**Provider:** IFRC / Montandon  
**Categories:** `multi_hazard`, `historical_disasters`, `event_catalogue`, `observed_impact`  
**Spatial scope:** global, depending on upstream source and reporting completeness  
**Temporal scope:** historical and current event, hazard and impact records; provider vintages vary  
**Resolution / granularity:** Linked disaster event/hazard/impact records, country and spatial joins, multiple original source IDs  
**Potential roles:** `event_source_crosswalk`, `post_event_impact_validation`, `source_lineage_research`  
**Access hint:** `ifrc_go_account_approved_token_required_and_upstream_per_source_rights_review`  
**Authoritative source:** <https://montandondata.org/get-started.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** IFRCGo/GCDB performs multi-provider ETL; IFRCGo/monty-stac-extension and IFRCGo/pystac-monty implement STAC event/hazard/impact relationships. Montandon requires an IFRC GO token due to upstream restrictions. Check ETL provenance, original ID, impact type, known-at time and allowed redistribution separately. Do not merge related earthquakes or treat a humanitarian impact estimate as insured loss. Discovery: https://github.com/IFRCGo/GCDB ; https://github.com/IFRCGo/monty-stac-extension ; https://github.com/IFRCGo/pystac-monty.

## CLIMADA Data API v2 hazard and exposure dataset catalogue

**Candidate ID:** `eth.climada.data-api.v2`  
**Provider:** ETH Zurich CLIMADA  
**Categories:** `multi_hazard`, `hazard`, `exposure`, `probabilistic_events`, `data_catalogue`  
**Spatial scope:** global for selected datasets, spatial/time coverage differs by product  
**Temporal scope:** historical, present and future climate scenario sets; dataset and version specific  
**Resolution / granularity:** API v2 dataset IDs and metadata, downloadable input files and event-set references  
**Potential roles:** `hazard_dataset_discovery`, `independent_risk_model_challenge`, `uncertainty_benchmark`  
**Access hint:** `public_api_and_cc_by4_platform_notice_individual_dataset_metadata_review`  
**Authoritative source:** <https://climada.ethz.ch/data-api/v2/docs>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official data API documents v2 dataset and data_type endpoints. Provider publicly describes CC BY 4.0 data and GPL-3.0 software; verify each dataset's upstream provenance, units, spatial support, source licences, climate scenario and revision before admission. CLIMADA hazard sets are not automatically independent of copied IBTrACS or other underlying providers; 4 km products cannot be assumed building-resolution. Code: https://github.com/CLIMADA-project/climada_python ; https://github.com/CLIMADA-project/climada_petals.

## GFDRR ThinkHazard multi-peril administrative hazard scores

**Candidate ID:** `worldbank.gfdrr.thinkhazard.screening-scores`  
**Provider:** World Bank / GFDRR  
**Categories:** `multi_hazard`, `hazard_screening`, `risk_classification`, `admin_boundaries`  
**Spatial scope:** global with national and subnational availability depending on selected layer  
**Temporal scope:** Dated 2026 ThinkHazard integration-site publication (production equivalence unverified); distinct 2021 World Bank score-table archive (2025 catalog metadata); underlying hazard-layer vintages vary  
**Resolution / granularity:** Portal: ADM0/ADM1/ADM2 screening classes and approximately 3,000 urban areas in the 2026 version; World Bank catalogue dataset 0060151 is a separate 2021 Excel ADM0/ADM1/ADM2 snapshot  
**Potential roles:** `regional_hazard_priority_screening`, `risk_source_discovery`, `cross_peril_gap_analysis`  
**Access hint:** `public_report_api_and_downloads_underlying_layers_independent_licenses`  
**Authoritative source:** <https://gfdrr.github.io/thinkhazard/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Version trap confirmed from publisher: https://int.thinkhazard.org/en/about reports a 2026-09-18 data publication on an integration-site host; equivalence with the public production portal is not established; https://datacatalog.worldbank.org/search/dataset/0060151/thinkhazard-hazard-ranking describes a 2021 Excel snapshot (file last updated 2021-11-29; catalog metadata 2025-03-07), with CC BY 4.0 *for that dated product*. Neither proves that the 2021 file equals the 2026 portal classification nor licenses underlying third-party hazard layers. Pin platform version, source-layer revisions, admin-boundary/urban method, exact country+peril class and original item attribution before any use. Scores VLO/LOW/MED/HIG are hazard screening, never physical ground intensity, earthquake source annual occurrence, insured loss or event timing. Code GPL-3.0 is separate from dataset rights.

## Maxar Open Data Program pre/post-disaster high-resolution imagery

**Candidate ID:** `maxar.open-data.ard-disaster-imagery`  
**Provider:** Maxar  
**Categories:** `remote_sensing`, `disaster_impact`, `buildings`, `post_event`, `satellite_imagery`  
**Spatial scope:** global event activations, not continuous worldwide coverage  
**Temporal scope:** pre/post event releases by activation, with product-dependent acquisition dates  
**Resolution / granularity:** Event-scoped cloud optimized imagery and STAC footprints, collection date and provider mosaic metadata  
**Potential roles:** `post_event_building_visual_validation`, `damage_change_detection`, `remote_sensing_training_candidate`  
**Access hint:** `public_event_based_stac_cog_noncommercial_cc_by_nc_4_0`  
**Authoritative source:** <https://registry.opendata.aws/maxar-open-data/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The official AWS registry states CC BY-NC 4.0 and activation-only coverage. Distinguish image acquisition, processing, publication and controlled receipt. Commercial use, derived imagery and redistribution need separate rights review; no unapproved bytes in Git. Discovery from Microsoft's building-damage assessment workflow: https://github.com/microsoft/building-damage-assessment.

## xView2 xBD annotated pre/post disaster building damage dataset

**Candidate ID:** `xview2.xbd.annotated-building-damage`  
**Provider:** xView2 / Maxar Open Data Program collaborators  
**Categories:** `buildings`, `satellite_imagery`, `damage_labels`, `post_event`, `validation`  
**Spatial scope:** selected disaster events across multiple countries, non-exhaustive  
**Temporal scope:** selected labelled disasters and static published benchmark splits  
**Resolution / granularity:** Paired optical satellite images, building polygons and damage classes no/minor/major/destroyed  
**Potential roles:** `building_damage_validation`, `image_segmentation_research`, `damage_class_taxonomy_crosswalk`  
**Access hint:** `registration_or_approved_download_noncommercial_dataset_rights`  
**Authoritative source:** <https://xview2.org/dataset>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Benchmark includes many building polygons across multiple perils; registration and noncommercial conditions apply to datasets, regardless of permissive code wrappers in TorchGeo or Microsoft. Prevent image-tile leakage across training/holdout and treat subjective damage labels as annotated observations, not insured economic losses. Discoverer: https://github.com/microsoft/building-damage-assessment.

## NASA JPL ARIA satellite radar damage proxy maps

**Candidate ID:** `nasa.jpl.aria.post-event-damage-proxy-maps`  
**Provider:** NASA JPL / ARIA; contributing satellite partners  
**Categories:** `earthquake`, `remote_sensing`, `damage_proxy`, `post_event`, `sar`  
**Spatial scope:** individual earthquake/disaster regions, includes 2023 Turkiye event  
**Temporal scope:** post-event acquisitions and derived maps with case-specific timestamps  
**Resolution / granularity:** SAR coherence/change-based mapped areas; 2023 Turkiye release example has approximately 30 m pixels  
**Potential roles:** `independent_post_event_spatial_challenge`, `earthquake_damage_proxy_comparison`, `satellite_evidence_lineage`  
**Access hint:** `public_product_example_jaxa_and_partner_upstream_terms_review`  
**Authoritative source:** <https://www.jpl.nasa.gov/images/pia25564-satellites-assess-earthquake-damage-in-turkey/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** NASA JPL article links a 2023 earthquake damage-proxy-map download; ALOS-2 data involve JAXA and EO Singapore contributors. SAR change is not a confirmed collapsed building or financial loss; urban/vegetation bias, before/after dates and earthquake sequence timing must be captured. Evaluate each mapped original file licence separately.

## IFRC GO disaster event and field-report API v2

**Candidate ID:** `ifrc.go.disaster-events-fieldreports-v2`  
**Provider:** International Federation of Red Cross and Red Crescent Societies  
**Categories:** `multi_hazard`, `disaster_event`, `response`, `humanitarian_impact`  
**Spatial scope:** global national society reports, uneven coverage  
**Temporal scope:** reports and situation updates by event, publication and edit time  
**Resolution / granularity:** IFRC event identity, appeals, situation/field reports, affected population and response indicators  
**Potential roles:** `event_identity_crosswalk`, `impact_report_timeline`, `post_event_response_context`  
**Access hint:** `public_api_metadata_some_visibility_and_content_rights_restricted`  
**Authoritative source:** <https://go-wiki.ifrc.org/en/go-api/Data_dictionary_situation_report>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** IFRC GO v2 situation_report docs provide created_at and event linkage. Some records are visibility-scoped; preserve permission and reporting qualifiers, not all textual attachments are reusable. Monty may derive its IFRC entries from the same API: do not count Monty and IFRC as independent evidence. Differentiate DREF from emergency appeals and field reports.

## UN OCHA CERF grants and humanitarian allocations API

**Candidate ID:** `unocha.cerf.gms-data-api`  
**Provider:** UN OCHA Central Emergency Response Fund  
**Categories:** `humanitarian_finance`, `response`, `disaster_impact_context`, `api`  
**Spatial scope:** global CERF supported operations, limited to funded countries/crises  
**Temporal scope:** historic and current allocations with funding/application release dates  
**Resolution / granularity:** Applications, projects, country/agency/sector, allocation and donor-contribution values  
**Potential roles:** `post_event_response_finance_context`, `indirect_disaster_impact_validation`, `event_crosswalk_hypothesis`  
**Access hint:** `public_documented_api_provider_reuse_and_attribution_review`  
**Authoritative source:** <https://cerfgms-webapi.unocha.org/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** CERF amounts represent response grants and fundraising, NOT actual physical damage, insured losses or reconstruction cost. Match to original crisis event identifiers with versioned and uncertainty-aware mappings; guard double counting with ReliefWeb/IFRC. Confirm exact endpoint and redistribution policy before automated ingestion.

## UNDRR DesInventar Sendai country disaster loss inventories

**Candidate ID:** `undrr.desinventar.sendai-disaster-loss-records`  
**Provider:** United Nations Office for Disaster Risk Reduction / country custodians  
**Categories:** `multi_hazard`, `disaster_loss`, `historical_event`, `subnational`  
**Spatial scope:** country-dependent, historical inventories for participating countries  
**Temporal scope:** historic inventory vintages differ by jurisdiction; programme evolving toward DELTA  
**Resolution / granularity:** Local-level disaster reports on fatalities, affected/damaged buildings and economic effects, with inconsistent definitions  
**Potential roles:** `historical_disaster_impact_benchmark`, `country_event_crosswalk`, `loss_reporting_bias_research`  
**Access hint:** `public_discovery_country_database_permissions_and_successor_version_review`  
**Authoritative source:** <https://desinventar-api.undrr.org/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Country databases are contributed by national custodians; software Apache licensing DOES NOT license all underlying records. UNDRR describes a transition to DELTA Resilience. Confirm national version, original source, admin boundary and report-date uncertainty; economic damage is not insurer paid loss. Monty GCDB uses DesInventar as an upstream source.

## GLIDE global disaster identifier registry

**Candidate ID:** `adrc.glide.disaster-identifiers`  
**Provider:** Asian Disaster Reduction Center (ADRC)  
**Categories:** `multi_hazard`, `disaster_event`, `event_identifier`, `crosswalk`  
**Spatial scope:** global event identifiers where partner reporting exists  
**Temporal scope:** historical disaster identifiers since 2004, updated with reports  
**Resolution / granularity:** Per-disaster hazard type, year, sequential number and ISO country components  
**Potential roles:** `event_alias_crosswalk`, `catalogue_deduplication_challenge`, `source_id_reconciliation`  
**Access hint:** `public_search_registration_optional_statistics_disclaimer_and_terms_review`  
**Authoritative source:** <https://glidenumber.net/glide/public/about.jsp>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** ADRC explicitly cautions that GLIDE IDs serve linking across disparate databases and discourages use of the registry for statistical secondary analysis. One GLIDE ID is not evidence of one physical seismic shock nor of one insurance occurrence; cross-border and multi-shock relations must remain explicit. Monty/MapAction/other upstream crosswalk evidence.

## International Charter Space and Major Disasters activation and map-product archive

**Candidate ID:** `international-charter.space-major-disasters.activations`  
**Provider:** International Charter: Space and Major Disasters  
**Categories:** `multi_hazard`, `satellite_disaster`, `activation_catalogue`, `post_event_mapping`  
**Spatial scope:** global supported disaster activations, selective event coverage  
**Temporal scope:** public activation archive since 2000, individual product acquisition and release dates vary  
**Resolution / granularity:** Activation event links, disaster area, satellite-derived map products, mapped damage/flood/fire interpretation  
**Potential roles:** `new_event_source_discovery`, `post_event_mapping_source_discovery`, `impact_footprint_validation_candidate`  
**Access hint:** `public_activations_authorized_raw_imagery_and_map_specific_rights`  
**Authoritative source:** <https://disasterscharter.org/activations>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The public activation list and example maps do not authorize downloading/reusing underlying satellite acquisitions. Commercial rights and redistribution vary by original agency/provider and map product; modelled damage overlays do not constitute insured loss. Source used in MapAction disaster-impact harmonization.
