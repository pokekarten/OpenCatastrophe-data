<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-crossborder-exposure-loss-proxies-20261105.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-crossborder-exposure-loss-proxies-20261105.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-05`  
**Purpose:** Non-admission public-source research: cross-border building and property value priors, insurer product mix, government impact benchmarks and overlooked ground-instability layers; no source-data bytes, rights, science or CAT model admission.

**Entries:** 8

## Belgian FPS Finance cadastral building condition statistics, 2026 vintage

**Candidate ID:** `be.fpsfin.cadastral-building-condition.20260101`  
**Provider:** Belgian FPS Finance, General Administration of Patrimonial Documentation  
**Categories:** `building_attributes`, `building_age`, `cadastral_aggregates`, `europe`  
**Spatial scope:** Belgium; national, regional, province, arrondissement, municipality, cadastral division and statistical sector aggregates; no building-level insured-site claim  
**Temporal scope:** 2026-01-01 technical vintage; official catalogue metadata revised 2026-07-24; annual series  
**Resolution / granularity:** Downloadable zipped CSV by type of built parcel, including totals, physical-condition indicators, central heating and pre-1900 construction; administrative and statistical-sector class summaries  
**Potential roles:** `regional_building_stock_prior`, `construction_age_sensitivity`, `occupancy_archetype_challenge`  
**Access hint:** `public_zip_csv_provider_unified_ccby_based_license_commercial_use_yes_exact_scope_review`  
**Authoritative source:** <https://www.geo.be/catalog/details/857b351e-51ca-11eb-a86d-3448ed25ad7c?l=en>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher FPS Finance explicitly says ALL its open patrimony datasets share one licence based on CC BY and can be used commercially (https://finance.belgium.be/en/experts-partners/open-data-patrimony/datasets). The individual geo.be catalogue links a bespoke 'plan cadastral' PDF whose defined scope is cadastral map, so do not label the exact statistical CSV ZIP automatically as standard CC BY 4.0 or assert raw redistribution eligibility without reviewing the applicable licence text and attribution obligations. Original source catalogue gives 2026-01-01 ZIP and seven administrative statistical levels. Physical parcel counts are neither actual building or dwelling totals nor insured risk locations or replacement values. Freeze original ZIP bytes and source specification outside Git before any numerical model use.

## Belgian FPS Finance real estate transactions by cadastral geography

**Candidate ID:** `be.fpsfin.real-estate-transactions.20250630`  
**Provider:** Belgian FPS Finance, General Administration of Patrimonial Documentation  
**Categories:** `property_transactions`, `asset_valuation`, `cadastral_aggregates`, `europe`  
**Spatial scope:** Belgium; seven published administrative/cadastral geography levels down to statistical sectors  
**Temporal scope:** Quarterly maintained series; provider technical specifications identify 2025-06-30 vintage; exact current downloadable extract to be version-pinned  
**Resolution / granularity:** Zipped CSV with real estate transaction counts and market values by type of property/right and cadastral nature, aggregated geographically  
**Potential roles:** `regional_property_value_prior`, `replacement_cost_crosscheck_not_direct_measure`, `asset_class_distribution_challenge`  
**Access hint:** `public_zip_csv_provider_unified_ccby_based_license_commercial_use_yes_exact_scope_review`  
**Authoritative source:** <https://www.geo.be/catalog/details/89209670-51ca-11eb-beeb-3448ed25ad7c?l=en>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher FPS Finance explicitly says ALL its open patrimony datasets share one licence based on CC BY and can be used commercially (https://finance.belgium.be/en/experts-partners/open-data-patrimony/datasets). The individual geo.be catalogue links a bespoke 'plan cadastral' PDF whose defined scope is cadastral map, so do not label the exact statistical CSV ZIP automatically as standard CC BY 4.0 or assert raw redistribution eligibility without reviewing the applicable licence text and attribution obligations. Original source catalogue gives 2025-06-30 ZIP and technical specification; counts and market values concern selected real-property transfers, not all asset stock, building-only replacement TIV, policy contracts or insured risk locations. Freeze source bytes, assess selection and land-share before valuation modelling.

## Belgian Statbel 2026 cadastral building stock and dwelling characteristics

**Candidate ID:** `be.statbel.cadastral-building-stock.2026`  
**Provider:** Statistics Belgium (Statbel), using Belgian FPS Finance patrimonial documentation  
**Categories:** `building_stock`, `housing`, `building_attributes`, `construction_age`, `exposure_calibration`  
**Spatial scope:** Belgium; national and regional be.STAT tables, further administrative geography available in official bulk archives pending exact member and code list verification  
**Temporal scope:** Annual building-stock register as of 1 January reference year; online 2026 be.STAT view last modified 2026-10-15; archived yearly source files also available through Statbel Open Data  
**Resolution / granularity:** Be.STAT 2026 building and dwelling counts by four displayed residential construction types, post-1981 age indicator, built-ground-surface bins, heating, bathrooms and parking indicators where applicable; machine-accessible yearly XLSX and TXT ZIP offerings  
**Potential roles:** `official_building_count_mass_control`, `building_dwelling_parcel_definition_reconciliation`, `regional_construction_type_prior`, `building_size_footprint_distribution_prior`  
**Access hint:** `public_xlsx_zip_statbel_open_data_cc_by_4_2026_exact_archive_and_lineage_review`  
**Authoritative source:** <https://statbel.fgov.be/en/open-data?category=1489>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Statbel explicitly states its Open Data use CC BY 4.0 and are usable commercially. Its official 2026 be.STAT table (https://bestat.statbel.fgov.be/bestat/crosstable.xhtml?view=43d7cdce-3647-4f5c-86f1-a4e0c864f692) was modified 2026-10-15. This counts buildings and dwellings rather than cadastral built-on parcels in the separate FPS Finance condition dataset; four displayed residential types are NOT a complete total of all insured buildings or business classes. Freeze exact 2026 ZIP/XLSX member and version, check administrative geography, suppression/blank bins, stock-vintage alignment and publisher attribution; no original data or inferred insurer coverage is committed.

## France Cerema DVF+ geolocated real-estate transactions

**Candidate ID:** `fr.cerema.dvfplus.opendata.2026`  
**Provider:** Cerema and DGALN, based on French DGFiP property transaction data  
**Categories:** `property_transactions`, `geocoded_property`, `valuation_prior`, `europe`  
**Spatial scope:** France with DVF geographic/legal exclusions and cadastral-geocoding coverage; not a nationwide inventory of every existing building  
**Temporal scope:** Historical five-year rolling DVF transaction source; Cerema data product updated during 2026, exact download release to be pinned  
**Resolution / granularity:** Transaction-level DVF+ database and cadastral localisation; source page advertises CSV/Shapefile or PostgreSQL/PostGIS distribution routes  
**Potential roles:** `local_property_value_prior`, `geospatial_transaction_validation`, `synthetic_tiv_sensitivity`  
**Access hint:** `public_distribution_open_licence_2_provider_specific_dvf_privacy_rules_review`  
**Authoritative source:** <https://www.data.gouv.fr/datasets/dvf-open-data>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official Cerema portal identifies Licence Ouverte/Open Licence v2.0, but underlying DGFiP DVF rules warn against indirect reidentification and search-index exposure. Do not ingest parcel-level person-linkable transaction rows into public Git. Sale price is not reinstatement cost and sale population is not insured stock. Validate current asset endpoints, exact version, rights and aggregation before use.

## UK FCA general insurance value measures 2025 by firm and retail product

**Candidate ID:** `uk.fca.gi-value-measures.2025`  
**Provider:** UK Financial Conduct Authority  
**Categories:** `insurance_market`, `insurer_product_mix`, `claims_frequency`, `portfolio_calibration`  
**Spatial scope:** United Kingdom reporting firms and retail products; firm-by-region building exposure and insured-address locations are not supplied  
**Temporal scope:** Reporting year 2025; published 2026-07-21 and updated 2026-09-11; underlying fixed snapshot 2026-05-05  
**Resolution / granularity:** FCA-published XLSX with product/firm level claims frequency, acceptance, average paid amount and complaints; market product-level claims-cost/premium ratios  
**Potential roles:** `insurer_product_loss_ratio_prior`, `home_buildings_contents_business_mix_screen`, `cross_carrier_claim_severity_challenge`  
**Access hint:** `public_fca_xlsx_publication_exact_table_and_reuse_rights_review_required`  
**Authoritative source:** <https://www.fca.org.uk/data/general-insurance-value-measures-data-2025>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** FCA source is the 2025 firm/product Value Measures publication, with direct provider XLSX at https://www.fca.org.uk/publication/data/gi-value-measures-data-2025.xlsx (publication/link verified, original XLSX bytes not obtained). Firm product reporting applies above GBP400k written retail premiums AND above 3000 in-force policies; home buildings/contents aggregate claim costs are 48 percent of premiums but individual firm statistics do not identify natural-peril claims, risk locations or TIV. FCA explicitly warns of home acceptance-rate reporting inconsistency and post-snapshot corrections. Rights to distribute/downloaded workbook require independent verification.

## Indonesia BNPB post-disaster rehabilitation and reconstruction damage-loss proposals 2017-2024

**Candidate ID:** `id.bnpb.rrrp-damage-loss-proposals.2017-2024`  
**Provider:** Indonesia National Disaster Management Authority (BNPB), Directorate of Rehabilitation and Reconstruction Planning  
**Categories:** `observed_impacts`, `post_disaster_reconstruction`, `loss_benchmarks`, `asia`  
**Spatial scope:** Indonesia province and district-level reported rehabilitation/reconstruction proposal records; event and geographic completeness must be measured  
**Temporal scope:** Named 2017-2024 reconstruction proposals, portal published 2025-03-14  
**Resolution / granularity:** Government CKAN catalogue offering year-wise XLSX damage and loss amount tables, province/district, event year and disaster category fields where present  
**Potential roles:** `post_disaster_economic_impact_validation`, `peril_event_date_reconciliation`, `observed_vs_model_loss_boundary_test`  
**Access hint:** `public_xlsx_download_ckan_dataset_resource_license_reconfirm`  
**Authoritative source:** <https://data.bnpb.go.id/dataset/rekapr3p2017-2024>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Amounts originate from local-government rehabilitation and reconstruction submissions; they must not be equated with independently verified paid insured claims, final damage cost or ground-up CAT loss. Catalogue lists multiple XLSX resources; exact resource IDs, vintages, file hashes and licence need independent verification. BNPB DIBI event maps already have a separate source candidate; this is a distinct loss-proposal product.

## Mexico City reconstruction-program damaged-building point layer

**Candidate ID:** `mx.cdmx.reconstruction-damaged-buildings.featureserver`  
**Provider:** Mexico City Secretariat for Comprehensive Risk Management and Civil Protection (SGIRPC)  
**Categories:** `building_damage`, `earthquake_validation`, `geospatial`, `latin_america`  
**Spatial scope:** Mexico City reconstruction programme coverage only; neither complete city building stock nor comprehensive earthquake damage universe  
**Temporal scope:** 2017 earthquake reconstruction context; ArcGIS service current visible state must be pinned with a dated response before analysis  
**Resolution / granularity:** ArcGIS REST FeatureServer layer 4: point geometries, phenomena and building typology fields; query supports JSON/GeoJSON and pagination; provider also exposes potentially sensitive address fields  
**Potential roles:** `earthquake_damage_footprint_holdout`, `building_typology_damage_challenge`, `event_specific_damage_validation`  
**Access hint:** `public_queryable_arcgis_rest_no_clear_reuse_licence_privacy_review_required`  
**Authoritative source:** <https://serviciosatlas.sgirpc.cdmx.gob.mx/arcgis/rest/services/AtlasCapasPublicas/Reconstruccion/FeatureServer/4>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Live provider service metadata identifies feature layer, geometry type point, JSON/GeoJSON and query capabilities, not independent proof of unrestricted redistribution. Do not import individual building/address fields or claims into public repo. Reconstruct programme inclusion criteria, observation dates, missingness, taxonomy, coordinate system EPSG:6369 and authoritative reuse rules; insured losses are not reported.

## Lithuanian INSPIRE natural risk zones: flooding, subsidence, karst and ground instability

**Candidate ID:** `lt.inspire.natural-risk-zones.flood-instability`  
**Provider:** Lithuanian Environment Protection Agency and Geological Survey via national INSPIRE geoportal  
**Categories:** `flood`, `ground_instability`, `subsidence`, `karst`, `europe`  
**Spatial scope:** Lithuania; national INSPIRE risk-zone coverage with source-layer gaps and class-specific map-scale limits  
**Temporal scope:** INSPIRE portal dataset publication and resource update dates vary; exact ZIP and WMS service response versions must be recorded  
**Resolution / granularity:** INSPIRE ATOM download ZIP with natural risk zones and WMS service layers including NZ.Flood, NZ.SubsidenceAndCollapse and NZ.NaturalGroundInstability  
**Potential roles:** `national_flood_hazard_context`, `ground_subsidence_susceptibility`, `non_flood_multi_peril_validation`  
**Access hint:** `public_inspire_atom_zip_wms_metadata_declares_cc_by_4_rights_scope_review`  
**Authoritative source:** <https://inspire-geoportal.ec.europa.eu/srv/api/records/a72edbdc-7c24-428c-a085-b3b4b7c4d28d>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The official INSPIRE metadata records CC BY 4.0 as an 'Other restrictions' use constraint, a 2023-01-06 dataset revision and 2026-04-14 metadata timestamp; original national ZIP URL https://inspire-geoportal.lt/resources/atom/nz/data/NZ_INSPIRE2.zip. This is catalogue-level license evidence, not completed artifact-specific rights/attribution and privacy review. Check original ZIP, GML layer content, area coverage, hazard-zone taxonomy and class vintage before risk interpretation. Flood/instability susceptibility layers are not return-period event loss or insurer portfolios.
