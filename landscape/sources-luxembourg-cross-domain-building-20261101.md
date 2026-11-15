<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-luxembourg-cross-domain-building-20261101.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-luxembourg-cross-domain-building-20261101.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-01`  
**Purpose:** Non-admission discovery of 14 mostly non-CAT Luxembourg building attribute/context sources and two European dwelling-calibration products; distinguish directly observable building geometry from aggregate statistics, uncertain rights and derived model evidence.

**Entries:** 14

## Luxembourg 2025 solar potential roof and building shapefile

**Candidate ID:** `lu.klimaagence.solar-roof-cadastre.2025`  
**Provider:** Klima-Agence / tetraeder.solar  
**Categories:** `buildings`, `roof`, `roof_geometry`, `energy`, `luxembourg`  
**Spatial scope:** Luxembourg nationwide  
**Temporal scope:** Solar modelling snapshot September 2025; original geometry and elevation upstream vintage to be checked  
**Resolution / granularity:** Publisher has separate full Shapefile components: 58.8 MB SHP and 212.2 MB DBF plus SHX/PRJ/CPG, building-level 'hid' source identifier, polygon/multipolygon in EPSG:2169; WMS/documentation additionally describes distinct facet tilt, aspect, flat-roof and area3d layers  
**Potential roles:** `roof_geometry_enrichment_research`, `roof_area_and_pv_potential_context`, `act2023_vs_roof_source_segmentation_audit`  
**Access hint:** `other_open_license_file_rights_and_wms_layer_access_review`  
**Authoritative source:** <https://data.public.lu/en/datasets/potentiel-solaire-au-luxembourg/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** High priority. Do not treat 'hid' as ACT 'buildingid' or EUBUCCO id: require spatial/versioned crosswalk. The SHP building layer is NOT proven to contain roof-facet 'tilt/aspect' attributes; these are described separately for the WMS roof-patch layer. The vendor's 2020 existing-panel detection is modelled and differs in year. Source includes street/house number: omit private address/person data from public artifacts. 2025 estimated solar POTENTIAL is not installed/insured PV. License catalogued 'Other (Open)', review exact legal terms, WMS access and share rights.

## Luxembourg STATEC RP2021 housing period-of-construction × building type

**Candidate ID:** `lu.statec.rp2021.housing-construction-age`  
**Provider:** STATEC / LUSTAT  
**Categories:** `housing_census`, `building_age`, `building_stock`, `luxembourg`  
**Spatial scope:** Luxembourg by census reporting geographic scope, including separate municipality housing tables  
**Temporal scope:** 2021 population and housing census; published/updated 2025 and 2026 catalogues  
**Resolution / granularity:** Statistical dwelling (logement) counts classified by building type, period of construction, occupancy/tenure; national/municipal release tables differ, official DSD_CENSUS_NB_LOG_CLA@DF_B1706  
**Potential roles:** `national_age_distribution_prior`, `census_dwelling_vs_building_stock_validation`, `housing_type_regional_calibration`  
**Access hint:** `public_statec_cc0_sdmx_original_table_terms_review`  
**Authoritative source:** <https://data.public.lu/en/datasets/population-et-emploi-recensement-de-la-population-recensement-2021-logement/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Critical gap: EUBUCCO Luxembourg has only 74 nonnull construction years among 186171 features. RP2021 classifies dwellings, NOT individual buildings; apartments in one building appear multiple times. NEVER assign a specific building construction year by disaggregating published age-band totals. Verify B1706 geographic dimensions vs B1707 municipality before any local calibration.

## Luxembourg STATEC authorised buildings and dwellings by type/region/canton

**Candidate ID:** `lu.statec.building-permits-by-type.2026`  
**Provider:** STATEC / LUSTAT  
**Categories:** `construction_permits`, `building_stock`, `construction_age`, `luxembourg`  
**Spatial scope:** Luxembourg; reporting by region and canton, not individual parcels  
**Temporal scope:** Annual and quarterly data updated 2026-10-03  
**Resolution / granularity:** Multiple tables D411x of authorised buildings, permitted dwellings and approved useful area by building type and reporting geography  
**Potential roles:** `regional_growth_prior`, `new_building_flow_validation`, `exposure_asof_change_context`  
**Access hint:** `public_official_lustat_table_scope_and_cc0_review`  
**Authoritative source:** <https://data.public.lu/en/datasets/entreprises-construction-et-logement-autorisations-de-batir/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Building permissions are planned, not completed, occupied or guaranteed erected buildings, and cannot identify a specific ACT2023v2 polygon. Compare same geography, building-vs-dwelling unit and annual vintage with completion statistics. Dataset is statistics, not a building permit geolocation registry.

## Luxembourg STATEC completed building counts and average new residential areas

**Candidate ID:** `lu.statec.completed-buildings.2026`  
**Provider:** STATEC / LUSTAT  
**Categories:** `buildings`, `building_stock`, `construction`, `floor_area`, `luxembourg`  
**Spatial scope:** Luxembourg national and table-dependent geographic detail  
**Temporal scope:** Annual completions official update 2026-05-01  
**Resolution / granularity:** Official 'Les bâtiments achevés par genre de bâtiment' DF_D4200 and 'Surface moyenne ... bâtiments résidentiels achevés' DF_D4202  
**Potential roles:** `completed_building_flow_validation`, `new_residential_floor_area_prior`, `building_stock_temporal_control`  
**Access hint:** `public_official_lustat_download_version_and_reuse_review`  
**Authoritative source:** <https://data.public.lu/en/datasets/entreprises-construction-et-logement-batiments-acheves/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Counts of completed building units, not identified exact buildings; average apartment unit living area is not individual footprint area or total floor area. Can cross-check permits-to-completion pipeline with time lags and national building totals without claiming direct geographic matching.

## Luxembourg national protected monuments official INSPIRE GML and OGC services

**Candidate ID:** `lu.geoportail.inspire-cultural-monuments.2026`  
**Provider:** Géoportail Luxembourg / INPA  
**Categories:** `heritage`, `buildings`, `protected_sites`, `luxembourg`  
**Spatial scope:** Luxembourg national heritage protected sites  
**Temporal scope:** INSPIRE GML revision 2026-07-01, WMS February 2026  
**Resolution / granularity:** 6.4MB INSPIRE GML National Monuments and protected/inventory listed sites; object identifiers/descriptions and geometries, may contain historic buildings or cadastral zones  
**Potential roles:** `heritage_rebuild_value_flag`, `cultural_building_status_context`, `nonstandard_construction_material_research`  
**Access hint:** `source_catalogue_cc0_gml_srs_geometry_and_entity_review`  
**Authoritative source:** <https://data.public.lu/en/datasets/inspire-annex-i-theme-protected-sites-protected-sites-cultural-monuments/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Provider labels CC0. Protected sites may be a parcel, object, site or entire historic complex, NOT always a single building, and designation does not prove building year or wall material. Screen GML geometry semantics, preserve original site ID/status/year, do not classify all unlisted buildings as nonhistoric or assume replacement costs.

## Luxembourg public building inventory under EU Energy Efficiency Directive article 6

**Candidate ID:** `lu.economy.eed2023.public-building-inventory.2026`  
**Provider:** Luxembourg Ministry of the Economy / Klima-Agence  
**Categories:** `public_buildings`, `energy`, `epc`, `floor_area`, `luxembourg`  
**Spatial scope:** Luxembourg public-sector heated or cooled properties with energy reference area &gt;250 m2  
**Temporal scope:** Initial partial inventory reported during 2025, published May 20 2026, planned annual updates  
**Resolution / granularity:** Inventaire.xlsx one row per public building, energy reference area, annual metered energy if available, EPC PDF cross references; hundreds of original individual certificates linked  
**Potential roles:** `nonresidential_public_asset_attributes`, `measured_energy_benchmark`, `large_building_mixed_use_context`  
**Access hint:** `public_portal_unknown_exact_inventory_epc_pdf_licence_and_personal_data_review`  
**Authoritative source:** <https://data.public.lu/en/datasets/inventaire-dans-le-cadre-de-larticle-6-de-la-directive-ue-2023-1791-relative-a-lefficacite-energetique/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Published inventory expressly initial/incomplete and only heated/cooled public bodies &gt;250m2. Downloading a publicly posted EPC PDF is NOT bulk reuse approval. Do not copy address, operator, contact/person details or 826 PDFs into Git/Neon; audit workbook licence and source records separately. Floor 'energy reference area' is not ground footprint nor insured reinstatement cost.

## Luxembourg 1967 countrywide official historic 50cm orthophoto

**Candidate ID:** `lu.act.orthophoto.1967`  
**Provider:** Administration du Cadastre et de la Topographie (ACT)  
**Categories:** `historic_imagery`, `building_age`, `buildings`, `luxembourg`  
**Spatial scope:** Luxembourg nationwide  
**Temporal scope:** Flight 1967-07-12, orthorectification/digital release 2024  
**Resolution / granularity:** 0.5m monochrome JP2 orthophoto, EPSG:2169, approx 12.3GB complete country file; historic roof/settlement presence possible  
**Potential roles:** `historic_pre1967_presence_label`, `construction_age_upper_bound_prior`, `demolition_urban_change_screen`  
**Access hint:** `publisher_license_not_specified_no_ingest_until_clear`  
**Authoritative source:** <https://data.public.lu/en/datasets/orthophoto-1967/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The national dataset portal explicitly states 'License Not Specified'. DO NOT ingest/redistribute raw images without provider rights review. A visible roof in 1967 gives building-presence constraint, not precise construction year; absence can reflect shadows/georeferencing/interpretation or demolition/rebuild. Per-tile access required, not 12.3GB direct load.

## Luxembourg 2001 official orthophoto archived by municipality

**Candidate ID:** `lu.act.orthophoto.2001`  
**Provider:** Administration du Cadastre et de la Topographie (ACT)  
**Categories:** `historic_imagery`, `building_age`, `buildings`, `luxembourg`  
**Spatial scope:** Luxembourg nationwide, divided into regional JP2 assets  
**Temporal scope:** Aerial survey 2001, official resource updated 2025-04-29  
**Resolution / granularity:** 0.5m, 1m, 10m JP2 historic building/roof imagery incl municipality-level tiles; national JP2 2.6GB  
**Potential roles:** `building_presence_2001_change_detection`, `possible_post2001_construction_bounds`, `legacy_roof_geometry_comparison`  
**Access hint:** `publisher_cc0_tile_selection_timing_groundcontrol_review`  
**Authoritative source:** <https://data.public.lu/en/datasets/orthophoto-officielle-du-grand-duche-de-luxembourg-edition-2001/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official CC0 catalogue. Read municipality tiles rather than national asset, and account for imagery interpretation limits. A building existing in 2001 may have been renovated/rebuilt since; historical observation != construction year or structural materials. Map with ACT2023v2 and 2025 aerial dates, never use as independent cadastre ground-truth.

## Luxembourg summer 2025 aerial RGB/CIR building roof imagery

**Candidate ID:** `lu.act.orthophoto.2025-summer`  
**Provider:** Administration du Cadastre et de la Topographie (ACT)  
**Categories:** `imagery`, `roof`, `solar_installations`, `luxembourg`  
**Spatial scope:** Luxembourg nationwide and small overshoot  
**Temporal scope:** Flights 2025-05-10 to 2025-05-13; public 2026 revision  
**Resolution / granularity:** 10cm RGB, CIR and RGBI orthophotos in EPSG:2169, JP2 national assets 64GB/68GB/136GB plus per-tile products and WMS  
**Potential roles:** `building_change_2023_2025`, `independent_photo_roof_obstruction_validation`, `visual_solar_panel_candidate_detection`  
**Access hint:** `official_cc0_tile_or_wms_usage_exact_image_rights_review`  
**Authoritative source:** <https://data.public.lu/en/datasets/orthophoto-officielle-du-grand-duche-de-luxembourg-edition-ete-2025/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Actual 2025 10cm aerial photos are not guaranteed actual current installed PV occupancy; image classification detects appearances with false positives and shadows. Preserve acquisition timestamp; roof material/pitch cannot be fully identified with imagery alone. DO NOT download nation-scale assets into Git or metadata DB.

## Luxembourg national towns, streets and official house-number reference CACLR

**Candidate ID:** `lu.act.caclr.address-registry.2026`  
**Provider:** Administration du Cadastre et de la Topographie (ACT)  
**Categories:** `addresses`, `building_ids`, `luxembourg`  
**Spatial scope:** Luxembourg national addresses and postal geography, no geometry  
**Temporal scope:** Monthly reference, original ZIP updated 2026-10-19  
**Resolution / granularity:** Official house numbers, street/locality and postcode, machine-readable ZIP of text files approx 1.9 MB and optional 41.1MB XLSX  
**Potential roles:** `standardise_legal_building_address_strings`, `municipality_crosswalk_quality`, `avoid_address_typo_false_joins`  
**Access hint:** `official_cc0_source_zip_no_coordinates_api_auth_required`  
**Authoritative source:** <https://data.public.lu/en/datasets/registre-national-des-localites-et-des-rues/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Registry explicitly has NO geographic coordinates and completeness not guaranteed. Street/house number is an address identifier, not unique building/polygon; one address may contain numerous residential units. REST API requires CTIE gateway access request; bulk public ZIP exists. Avoid publishing household-level linked addresses or reverse geolocating personal exposure.

## Luxembourg ministry anonymised residential EPC aggregates on application

**Candidate ID:** `lu.economy.epc.anonymised-on-request`  
**Provider:** Luxembourg Ministry of the Economy / Energy Efficiency  
**Categories:** `energy`, `epc`, `building_age`, `luxembourg`  
**Spatial scope:** Luxembourg residential buildings; currently national aggregate request only  
**Temporal scope:** Official data-request policy updated 2024/2025  
**Resolution / granularity:** On-request nationwide aggregated anonymised residential building EPC statistics; online application form required, no individual building dataset  
**Potential roles:** `aggregate_thermal_vintage_prior`, `energy_rating_distribution_validation`  
**Access hint:** `restricted_request_aggregated_anonymised_only_not_bulk_individual`  
**Authoritative source:** <https://meco.gouvernement.lu/fr/domaines-activites/energie/efficacite-energetique/acces-donnees-batiments.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Government explicitly provides ANONYMISED NATIONAL AGGREGATES ON REQUEST, currently residential only. Cannot scrape private building-energy passports, infer individual building ages from aggregates, or claim immediate public machine downloads. A formal data request would require the user's own action/authorisation.

## Eurostat Census 2021 occupied dwellings by construction period and NUTS3

**Candidate ID:** `eu.eurostat.census21.dwelling-age-nuts3`  
**Provider:** Eurostat / European Commission  
**Categories:** `housing_census`, `building_age`, `europe`  
**Spatial scope:** EU 2021 census countries and reporting NUTS3 regions  
**Temporal scope:** 2021 census, 2026 methodology updates  
**Resolution / granularity:** Official table cens_21dwop_r3: conventional dwellings by occupancy status, construction period and NUTS3, obtainable via Eurostat dissemination/API  
**Potential roles:** `europe_age_distribution_prior`, `regional_housing_stock_age_calibration`, `crosscountry_age_drift_validation`  
**Access hint:** `public_eurostat_sdmx_licence_code_and_missing_cell_review`  
**Authoritative source:** <https://ec.europa.eu/eurostat/databrowser/product/page/cens_21dwop_r3>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** DWELLING counts, not building counts. A multi-unit building contributes many dwellings. Statistical suppression, country coverage, age bands and NUTS3 vintage must be retained; never assign construction year to individual building or treat model downscaling as ground truth.

## JRC-ESTAT Census Dwelling Grid 2021 1 km raster

**Candidate ID:** `ec.jrc.census2021-dwelling-grid-1km`  
**Provider:** European Commission JRC / Eurostat  
**Categories:** `housing_census`, `building_stock`, `europe`  
**Spatial scope:** EU27 plus participating neighbouring European countries by asset scope  
**Temporal scope:** 2021 dwelling counts, publication 2025-11-14  
**Resolution / granularity:** GeoTIFF 1km gridded estimated conventional dwellings, redistributed from official LAU 2021 counts using residential built-up volume proxy  
**Potential roles:** `dwelling_count_grid_aggregate_challenge`, `multifamily_density_prior`, `building_vs_dwelling_count_audit`  
**Access hint:** `ec_reuse_notice_secondary_upstream_license_derived_grid_download_review`  
**Authoritative source:** <https://data.jrc.ec.europa.eu/dataset/50cfa4c6-406e-47ce-a092-64a2c5d18303>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** IMPORTANT: JRC states ancillary layers include EUBUCCO v0.1, DBSM R2023, Overture, GHS-BUILT and other shared source families: NOT independent validation of EUBUCCO/DBSM building footprints. It is a modelled grid constrained to municipal dwelling totals, NOT surveyed exact building geometry/occupancy. Access listing says no login despite site showing 'Log in'; test actual file retrieval before ingest.

## Luxembourg municipal renovation and renewable-energy incentive policy inventory

**Candidate ID:** `lu.klimaagence.municipal-renovation-subsidy-policies.2025`  
**Provider:** Klima-Agence G.I.E.  
**Categories:** `policy`, `renovation`, `luxembourg`  
**Spatial scope:** Luxembourg municipality programme coverage  
**Temporal scope:** Policy schedule snapshot 2025-03-07  
**Resolution / granularity:** 244kB official municipality funding policy Excel table (eligibility categories for insulation, heating, renewables, transport)  
**Potential roles:** `renovation_programme_policy_context`, `regional_incentive_coverage_prior`  
**Access hint:** `other_open_policy_rights_exact_content_review`  
**Authoritative source:** <https://data.public.lu/en/datasets/aides-communales-renovation-energetique-energie-renouvelable-et-electromobilite/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** This describes AVAILABLE GRANTS, not actual executed building renovations, nor roof/wall changes by building, nor receipt of subsidies. Cannot use as observed mitigation or building age. The catalogue licence is 'Other (Open)' requiring legal check.
