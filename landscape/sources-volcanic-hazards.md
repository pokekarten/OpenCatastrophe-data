<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-volcanic-hazards.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-volcanic-hazards.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-08-10`  
**Purpose:** Non-admission discovery registry of volcanic-hazard sources relevant to catastrophe risk, event validation and secondary atmospheric impacts.

**Entries:** 3

## WOVOdat Database of Volcanic Unrest v2

**Candidate ID:** `iavcei.wovodat.v2`  
**Provider:** World Organization of Volcano Observatories / IAVCEI, hosted by Earth Observatory of Singapore  
**Categories:** `volcano`, `volcanic_unrest`, `seismicity`, `deformation`, `gas_emissions`, `monitoring`  
**Spatial scope:** global contributions from volcano observatories and research institutions  
**Temporal scope:** event- and station-dependent historical and modern unrest records  
**Resolution / granularity:** station, network and episode data organized by measured parameters under the WOVOdat 2.0 schema  
**Potential roles:** `eruption_precursor_research`, `unrest_analogue_analysis`, `monitoring_feature_validation`  
**Access hint:** `public_web_with_contributor_use_policy`  
**Authoritative source:** <https://www.wovodat.org/doc/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Coverage and measurement semantics are heterogeneous across observatories, stations and episodes. WOVOdat's published policy attributes ownership to original contributors, restricts redistribution and frames free use around crisis response, education and research; this candidate therefore requires especially careful rights review before any commercial or redistributed use.

## Copernicus Sentinel-5P TROPOMI Level-2 Sulfur Dioxide

**Candidate ID:** `copernicus.s5p.tropomi.so2.l2`  
**Provider:** Copernicus Sentinel-5P / ESA  
**Categories:** `volcano`, `sulfur_dioxide`, `satellite_observation`, `atmospheric_plume`, `secondary_peril`  
**Spatial scope:** global  
**Temporal scope:** April 2018-present for the non-time-critical Level-2 archive  
**Resolution / granularity:** orbit/granule-based Level-2 total-column SO2 retrievals with product-version-dependent pixel geometry, quality fields and processing  
**Potential roles:** `volcanic_plume_detection`, `eruption_footprint_validation`, `so2_burden_context`, `event_timing_cross_check`  
**Access hint:** `copernicus_data_space`  
**Authoritative source:** <https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-missions/sentinel-5p>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** SO2 is a retrieved atmospheric column rather than a direct ash or damage observation, and non-volcanic sources also contribute. Processor and collection changes are scientifically material: the mission-wide SO2 reprocessing completed in 2025 superseded older products for much of the archive, so exact product class, collection, processor version and quality filtering must be frozen before comparison.

## NCEI/WDS Global Significant Volcanic Eruptions Database

**Candidate ID:** `noaa.ncei.significant-volcanic-eruptions`  
**Provider:** NOAA National Centers for Environmental Information / World Data Service  
**Categories:** `volcano`, `eruption_catalogue`, `historical_impact`, `damage`, `casualties`, `validation`  
**Spatial scope:** global  
**Temporal scope:** 4360 BC-present  
**Resolution / granularity:** eruption-event records with hazard, location, VEI and available socio-economic impact attributes  
**Potential roles:** `historical_impact_validation`, `catastrophe_event_benchmark`, `cross_peril_event_linkage`, `severity_context`  
**Access hint:** `public_metadata_and_download`  
**Authoritative source:** <https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ngdc.mgg.hazards%3AG10147>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** This is deliberately a significance-selected impact catalogue, not a complete eruption-frequency catalogue. Inclusion criteria favor fatalities, damage, VEI 6+ events and eruptions associated with tsunamis or significant earthquakes, so sampling and reporting biases must be preserved when using it for model validation.
