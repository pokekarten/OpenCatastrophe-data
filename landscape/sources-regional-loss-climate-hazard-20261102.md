<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-regional-loss-climate-hazard-20261102.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-regional-loss-climate-hazard-20261102.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-02`  
**Purpose:** Non-admission targeted discovery of independent climate precipitation, disaster impact and official regional flood/landslide GIS sources not represented by matching candidate identities on OpenCatastrophe-data main or currently examined source research PRs. No source bytes, scientific validation or commercial-use rights are included.

**Entries:** 5

## Climate Hazards Center CHIRPS version 3 precipitation estimates

**Candidate ID:** `ucsb.chc.chirps.v3.0`  
**Provider:** UC Santa Barbara Climate Hazards Center  
**Categories:** `precipitation`, `extreme_rainfall`, `drought`, `satellite`, `gauge`, `global`  
**Spatial scope:** Land between 60 degrees N and 60 degrees S, all longitudes  
**Temporal scope:** 1981 to near present; preliminary pentads and monthly final version are different product states  
**Resolution / granularity:** 0.05 degree gridded rain totals; native pentad/monthly with daily ERA5- or IMERG-disaggregated products; GeoTIFF, NetCDF, BIL and COG  
**Potential roles:** `flood_rainfall_forcing`, `drought_history_context`, `extreme_precipitation_event_validation`, `temporal_product_vintage_reconciliation`  
**Access hint:** `official_public_chc_bulk_directory_v3_rights_and_exact_asset_review`  
**Authoritative source:** <https://www.chc.ucsb.edu/data/chirps3>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Distinct replacement product from CHIRPS v2 and not the NASA IMERG v07 data already in the register. Source page reports CC BY 4.0 and original data directory but exact licence, attribution and asset-scope review is pending. Daily rnl uses ERA5 and daily sat uses IMERG Late V07 for disaggregation: never count those as independent of their parent products. Pentad/monthly are the native source; use correct preliminary/final vintage and avoid interpreting downscaled daily timing as independent daily ground observations.

## Brazil Atlas Digital de Desastres municipal historical disaster and loss records

**Candidate ID:** `br.midr.atlasdigital.disaster-loss.1991-2025`  
**Provider:** Brazil Secretaria Nacional de Protecao e Defesa Civil (SEDEC/MIDR) and CEPED/UFSC  
**Categories:** `observed_losses`, `disaster_events`, `economic_damage`, `municipal`, `brazil`  
**Spatial scope:** Brazil, municipal and state reporting units  
**Temporal scope:** Official public portal describes 1991-2025 event records; the current download export's actual end date and monetary reference period require original-file verification  
**Resolution / granularity:** Municipality, disaster type and reported impact; official Excel/semicolon-separated CSV, including monetary values corrected to December 2022 on the documented downloads page  
**Potential roles:** `post_event_economic_loss_benchmark`, `municipality_event_crosswalk`, `historical_disaster_severity_validation`, `monetary_vintage_and_inflation_audit`  
**Access hint:** `public_website_csv_xlsx_download_claim_exact_export_terms_and_bytes_unverified`  
**Authoritative source:** <https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Government-reported civil-defense disaster and damage data, not insurer claims, insured TIV, physical footprints or independent ground truth. Preserve disaster taxonomy, municipality boundary vintage, event key, actual export date, currency and 2022 price-index conversion; verify missingness and manual correction logs before calibration. Provider publication/access and commercial redistribution terms have not been reviewed. Website may reject automated requests; no scraping bypass or provider bytes acquired.

## Ontario Emergency Management Historical Events vector catalogue

**Candidate ID:** `ca.ontario.mnr.emergency-historical-events`  
**Provider:** Government of Ontario Ministry of Natural Resources  
**Categories:** `multi_hazard`, `observed_events`, `flood`, `wildfire`, `dam_failure`, `landslide`, `canada`  
**Spatial scope:** Ontario, Canada  
**Temporal scope:** Historical provincial events; source record exists since 2020, individual event years and completeness not yet profiled  
**Resolution / granularity:** Vector event geometries; Ontario ArcGIS REST MapServer layer 20 and published complete zipped Shapefile/File Geodatabase products  
**Potential roles:** `post_event_footprint_alignment`, `regional_event_identity_crosswalk`, `dam_failure_and_wildfire_observation_validation`  
**Access hint:** `government_catalogue_offers_esri_rest_and_zip_original_scope_rights_review_required`  
**Authoritative source:** <https://open.canada.ca/data/en/dataset/3ddd1967-a5a1-47b2-b3b9-554495581ea2>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official record lists dam failures, drought, erosion, floods, forest fires and soil/bedrock instability, but inclusion depends on involvement of Ontario emergency response officers: not a complete loss census. The catalogue states Open Government Licence - Ontario; check exact attribution, official metadata revision, layer geometry and true event timestamps before use. 'Structural loss' in description is not a quantified building-loss observation. No source bytes have been downloaded.

## Philippines MGB GDI Detailed Flood Susceptibility MapServer

**Candidate ID:** `ph.mgb.gdi.detailed-flood-susceptibility`  
**Provider:** Philippines Mines and Geosciences Bureau (MGB)  
**Categories:** `flood`, `hazard_susceptibility`, `philippines`, `government_gis`  
**Spatial scope:** Philippines, published service geographic footprint only; actual province/tile coverage unverified  
**Temporal scope:** Current public web service, production/model vintage not established  
**Resolution / granularity:** ArcGIS REST MapServer with published service/layer metadata and cached map tiles; vector export or scientific class definitions not established  
**Potential roles:** `flood_susceptibility_screening`, `local_hazard_class_crosswalk`, `high_resolution_hazard_availability_gap_review`  
**Access hint:** `public_mapserver_metadata_only_research_rights_and_feature_download_unverified`  
**Authoritative source:** <https://controlmap.mgb.gov.ph/arcgis/rest/services/GeospatialDataInventory_Public/GDI_Detailed_Flood_Susceptibility_Public/MapServer>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Classified flood susceptibility is not observed event inundation, depth or return-period probability. Actual vector feature/query accessibility, legend class meaning, regional holes, vintage and licence require original-source review. Public map display does not establish permission for commercial modelling or bulk export. Keep distinct from BNPB Indonesia and PAGASA products.

## Philippines MGB GDI Detailed Rain-Induced Landslide Susceptibility MapServer

**Candidate ID:** `ph.mgb.gdi.rain-landslide-susceptibility`  
**Provider:** Philippines Mines and Geosciences Bureau (MGB)  
**Categories:** `landslide`, `rainfall_trigger`, `hazard_susceptibility`, `philippines`, `government_gis`  
**Spatial scope:** Philippines, published service geographic footprint only; actual coverage unverified  
**Temporal scope:** Current public service listing, hazard-model vintage not established  
**Resolution / granularity:** Government ArcGIS REST MapServer layer listed in MGB GDI public service directory; underlying vector access and class definitions not yet tested  
**Potential roles:** `rain_landslide_hazard_screening`, `rainfall_and_slope_trigger_crosswalk`, `regional_landslide_model_validation_context`  
**Access hint:** `public_official_directory_service_identity_only_original_layer_preflight_pending`  
**Authoritative source:** <https://controlmap.mgb.gov.ph/arcgis/rest/services/GeospatialDataInventory_Public/GDI_Detailed_Rain_induced_Landslide_Susceptibility_Public/MapServer>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The official MGB GDI directory lists this MapServer separately from the flood service; direct per-layer metadata was not retrieved in this research. Susceptibility is not an event footprint or probability of loss. Confirm published layer geometry, legend/classes, access terms, vintage and spatial completeness before any API probe, use or source admission.
