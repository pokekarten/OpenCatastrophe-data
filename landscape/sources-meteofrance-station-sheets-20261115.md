<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-meteofrance-station-sheets-20261115.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-meteofrance-station-sheets-20261115.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-15`  
**Purpose:** Non-admission discovery of official Météo-France weather station instrumentation and siting metadata relevant to verifying actual 3-second wind-gust observations in the Windstorm Europe hazard model.

**Entries:** 1

## Meteo-France station information sheets: siting, location history and instrument metadata

**Candidate ID:** `fr.meteofrance.station-sheets.2026`  
**Provider:** Meteo-France via data.gouv.fr  
**Categories:** `windstorm`, `station_metadata`, `instruments`, `station_history`, `observation_validation`  
**Spatial scope:** France mainland and overseas station metadata; exact instrument coverage and site-vintage vary per station  
**Temporal scope:** Official public catalogue shown updated in September 2026; each station PDF carries its own opening/closure/site history  
**Resolution / granularity:** Individual station PDF sheet listing position, successive locations, opening and closure dates, site quality, measured parameters, sensor/instrument descriptions and station photos; one PDF is not one meteorological hourly sample  
**Potential roles:** `nord_france_gust_station_site_history`, `instrument_wind_measurement_class_validation`, `station_relocation_and_observational_holdout`  
**Access hint:** `public_data_gouv_meteofrance_open_licence_v2_per_station_pdf_ids_and_original_bytes_not_yet_verified`  
**Authoritative source:** <https://www.data.gouv.fr/datasets/fiches-dinformations-sur-les-stations>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official Météo-France publisher description covers station positions, successive site placements, opening/closure, site quality, measurement classes, instrumentation and photos. Portal displays about 15,184 publicly listed PDF resources, NOT a validated count of unique physical measurement sites or historic independent stations. No station PDF original bytes or SHA-256 were acquired in this pass. Pin exact station IDs and PDF vintage, original bytes, site class and instrument changes before independent FXI3S vs CLIMK/ERA5/C3S validation; matched measurements remain external and the recorded station PDFs do not imply insurable event-loss evidence.
