<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: manifests/copernicus.c3s.european-windstorm-reanalysis.v1.0.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Dataset manifest: `copernicus.c3s.european-windstorm-reanalysis.v1.0.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Dataset id:** copernicus.c3s.european-windstorm-reanalysis.v1.0

**Provider:** Copernicus Climate Change Service (C3S) / ECMWF

**Product name:** Windstorm tracks and footprints derived from reanalysis over Europe between 1940 to present

**Version or release:** 1.0

**Canonical source:** <https://cds.climate.copernicus.eu/datasets/sis-european-wind-storm-reanalysis>

**Retrieved at:** 2026-08-10T00:36:00Z

**Retrieval query or filters:** Metadata-only source review. No CDS request was submitted and no source bytes were acquired. Future raw-artifact work must pin exact product, tracking algorithm, footprint configuration, resolution, time selection and returned bytes independently.

**Access class:** registration_required

**Modelling layer:** hazard

**Intended use:** European extratropical-windstorm event-catalogue and hazard-footprint candidate for transparent research, with DWD station observations as an independent Germany validation route. This source is not by itself an exposure, vulnerability, insured-loss or production pricing model.

**Raw artifact:** `null`

**Derived artifact:** `null`

## Licensing

**Status:** verified

**Spdx expression:** CC-BY-4.0

**Licence name:** Creative Commons Attribution 4.0 International

**Terms reference:** <https://cds.climate.copernicus.eu/licences/cc-by>

**Terms reviewed at:** 2026-08-10T00:36:00Z

**Terms version or date:** CDS CC-BY licence rev. 1; CDS Terms of use rev. 11; reviewed 2026-08-10

**Terms content sha256:** `null`

**Commercial use status:** allowed

**Attribution requirements:** Provide attribution required by CC BY 4.0 and the dataset citation/attribution guidance. Do not imply ECMWF or the European Union endorses the use.

**Share alike or derivative requirements:** CC BY 4.0 permits adaptation without a share-alike requirement; attribution, licence reference and indication of changes remain required.

**Notes:** The authoritative CDS dataset page identifies the dataset licence as CC-BY and the current CDS licence page identifies that licence as CC-BY licence rev. 1. Download requires registration under the current CDS Terms of use rev. 11. This is an engineering rights assessment, not legal advice.

## Redistribution

**Status:** allowed

**Scope:** raw

**Conditions:** Source rights support redistribution under CC BY 4.0 subject to attribution and applicable CDS conditions. OpenCatastrophe currently approves metadata only; no raw C3S artifact has been selected, acquired, hashed or approved for Git publication.

## Privacy

**Personal data status:** none

**Confidential or proprietary status:** none

**Notes:** The reviewed product consists of public meteorological reanalysis-derived windstorm tracks, gridded footprints and summary indicators.

## Spatial

**Crs:** Regular latitude-longitude grid; exact CRS/grid metadata must be taken from each acquired product

**Extent:** Windstorm footprints: 25°W–35°E, 30°N–70°N; tracks: 80°W–35°E, 5°N–70°N; summary indicators: Europe

## Temporal

**Extent:** 1940 to present; the service is updated monthly, so 'present' is mutable and is not an exact artifact identity

## Variables and units

### Item 1

**Name:** 10m wind gust

**Unit:** m/s

**Description:** Wind-gust speed used in windstorm tracks and footprints; footprints represent the maximum 10 m wind gust over a 72-hour event-centred window.

### Item 2

**Name:** mean sea level pressure

**Unit:** hPa

**Description:** Mean sea level pressure at the tracked windstorm centre.

### Item 3

**Name:** normalised storm severity index (NSSI)

**Unit:** dimensionless

**Description:** Normalised storm severity indicator supplied in the annual summary product.

### Item 4

**Name:** storm severity index (SSI)

**Unit:** m^5 s^-3

**Description:** Storm severity indicator combining affected area and wind gust exceedance.

### Item 5

**Name:** yearly storm count

**Unit:** count

**Description:** Annual number of windstorms exceeding a configured gust threshold in a region.


**Transformation:** `null`

## Review

**Status:** approved_metadata_only

**Reviewed at:** 2026-08-10T00:36:00Z

**Reviewer:** OpenCatastrophe source audit

**Notes:** Metadata-only engineering approval based on authoritative CDS dataset metadata and current CDS licence/terms pages. The monthly-updated catalogue is not a frozen byte identity. Raw or derived publication remains blocked until an exact request/output is independently identified, acquired outside Git, hashed and reviewed for the requested publication scope.
