<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/meteoswiss.national-hail-climatology.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `meteoswiss.national-hail-climatology.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** meteoswiss.national-hail-climatology

## Source ids

- meteoswiss.national-hail-climatology

**Provider:** Federal Office of Meteorology and Climatology MeteoSwiss / Federal Spatial Data Infrastructure

**Interface type:** stac

**Status:** documented_only

**Documentation url:** <https://opendatadocs.meteoswiss.ch/c-climate-data/c5-radar-based-climate-data>

**Service root:** <https://data.geo.admin.ch>

**Api version:** STAC 1.0.0

## Access scope

- metadata
- catalogue

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- collection_metadata_get

### Path templates

- /api/stac/v1/collections/ch.meteoschweiz.ogd-radar-derived-grid

**Parameter rules:** This initial contract documents only one repository-constructed HTTPS GET of the exact MeteoSwiss hail-climatology STAC collection metadata path, with no query string and no caller-supplied host, path, headers, bbox, search expression, item ID, asset href, product selector, month, year or return period. Selecting or downloading a NetCDF asset requires a later scientific and asset-specific review that freezes one product family and exact STAC item/asset identity before values are inspected.

## Response contract

### Expected media types

- application/json

**Format:** FSDI STAC Collection metadata for ch.meteoschweiz.ogd-radar-derived-grid; hail data assets referenced by the collection are NetCDF.

**Scientific semantics:** The collection contains several non-interchangeable radar-derived hail climate product families: monthly/yearly MESHS and anomalies, monthly/yearly hail-day counts and anomalies, long-term hail-day climatologies and standard deviations, and separate HailStoRe-derived return-value hazard maps. Hail fields are radar/algorithm-derived pseudo-observations rather than comprehensive ground measurements; return-value maps additionally depend on stochastic resampling and represent annual exceedance hazard under today's climate, not observed event catalogues. A hail day uses the provider-defined 06 UTC to 06 UTC window. Monthly and yearly products update over time, while return-value maps are static. Data are provided on the Swiss LV95 / EPSG:2056 grid at approximately 1 km scale. Any later asset consumer must preserve exact product class, temporal/release identity, observed-versus-model-derived status and CRS rather than treating the collection as one homogeneous hail variable.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `262144`

**Max sample bytes:** `5242880`

**Retry policy:** none

**Rate limit notes:** FSDI geoservices are available without registration but are subject to fair-use and operating conditions. Excessive request frequency or volume may be restricted, and high-intensity automated scraping is discouraged. This documented-only contract therefore authorizes no polling cadence and no asset download; any later probe should be one bounded collection-metadata request through the trusted execution plane.

**Mutability notes:** The STAC collection metadata and current monthly/yearly item inventory are mutable as MeteoSwiss publishes updates. Provider documentation states monthly updates are available after the following month and yearly updates at the end of October, while hail-hazard return values are static. Any future asset receipt must bind retrieval UTC, exact collection/item/asset identity, final provider URL, byte count and SHA-256.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://www.geo.admin.ch/en/general-terms-of-use-fsdi>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** MeteoSwiss states that its Open Data may be reused without restriction, including commercially, and publishes it under CC BY 4.0; reproduction or redistribution requires source acknowledgement as 'Source: MeteoSwiss'. Automatic access is delivered through FSDI, whose separately reviewed service terms allow registration-free use subject to fair-use, operating and dataset-specific conditions. These are source/service ceilings only: this contract does not authorize repository persistence or publication of a future NetCDF asset before exact asset identity, attribution, provenance and admission scope are reviewed.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://opendatadocs.meteoswiss.ch/c-climate-data/c5-radar-based-climate-data>
- <https://www.meteoswiss.admin.ch/climate/the-climate-of-switzerland/hail-climatology.html>
- <https://www.meteoswiss.admin.ch/climate/the-climate-of-switzerland/hail-climatology/data-and-methods.html>
- <https://opendatadocs.meteoswiss.ch/general/terms-of-use>
- <https://www.geo.admin.ch/en/general-terms-of-use-fsdi>
- <https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-radar-derived-grid>

**Notes:** Static source-access documentation only. The durable collection identifier is ch.meteoschweiz.ogd-radar-derived-grid and the provider dataset DOI is 10.18751/Climate/Griddata/CHHC/1.0. No STAC probe, item search, asset selection, NetCDF download, provider byte persistence, source admission, publication promotion, event-set construction, damage/loss inference or insured-loss semantics are performed or authorized by this contract.
