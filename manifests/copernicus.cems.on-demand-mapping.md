<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: manifests/copernicus.cems.on-demand-mapping.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Dataset manifest: `copernicus.cems.on-demand-mapping.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Dataset id:** copernicus.cems.on-demand-mapping

**Provider:** Copernicus Emergency Management Service (CEMS) / European Commission

**Product name:** Copernicus EMS On-Demand Mapping public activation metadata and mapping products

**Version or release:** `null`

**Canonical source:** <https://mapping.emergency.copernicus.eu/>

**Retrieved at:** 2026-08-12T08:31:00Z

**Retrieval query or filters:** Metadata-only review of the public CEMS On-Demand Mapping portal, harvesting documentation, Emergency Response API documentation and terms. No activation product bytes were downloaded or admitted. Initial machine-access scope is the anonymous public Rapid Mapping activation catalogue and activation metadata; any future product acquisition must freeze activation code, AOI, product type/version, acquisition time, returned files and byte hashes.

**Access class:** open

**Modelling layer:** hazard

**Intended use:** Post-event event-footprint, hazard-observation and damage-grading validation source for floods, wildfires, storms, earthquakes and other mapped emergencies. Public activation/AOI/product metadata can link observed event geometry, satellite acquisition context and mapped impact statistics to independently modelled hazard outputs. CEMS mapping products are not a stochastic event catalogue, vulnerability function, insured-loss dataset or universal ground-truth layer, and product feasibility/quality varies by activation and sensor conditions.

**Raw artifact:** `null`

**Derived artifact:** `null`

## Licensing

**Status:** verified

**Spdx expression:** `null`

**Licence name:** Copernicus EMS On-Demand Mapping Terms and Conditions

**Terms reference:** <https://mapping.emergency.copernicus.eu/terms-and-conditions/>

**Terms reviewed at:** 2026-08-12T08:31:00Z

**Terms version or date:** Terms page last modified 2023-06-07; reviewed 2026-08-12

**Terms content sha256:** `null`

**Commercial use status:** allowed

**Attribution requirements:** When CEMS On-Demand Mapping data are communicated to the public or distributed, recipients must be informed of the source using the applicable Copernicus/CEMS citation guidance.

**Share alike or derivative requirements:** The reviewed terms permit adaptation, modification and combination with other data and information; no share-alike requirement is recorded. Source attribution and all other applicable terms remain required.

**Notes:** The reviewed terms grant free access and permit reproduction, distribution, public communication, adaptation, modification and combination for CEMS On-Demand Mapping data. Some CEMS data may be restricted under applicable law, and third-party information linked from the portal can have separate licence terms. Those cases require asset-specific review and are not cleared by this manifest. This is an engineering rights assessment, not legal advice.

## Redistribution

**Status:** allowed

**Scope:** raw

**Conditions:** The reviewed CEMS terms support redistribution of covered public On-Demand Mapping data with required source attribution. OpenCatastrophe currently admits metadata only: no activation product bytes are committed. Restricted/sensitive records and third-party inputs or linked information require separate rights review before acquisition or publication.

## Privacy

**Personal data status:** unknown

**Confidential or proprietary status:** unknown

**Notes:** Public activation metadata and geospatial products are the reviewed scope, but activation records can identify requesting organisations and may contain operational narrative. Sensitive/restricted activations are explicitly outside this admission. Any future persisted sample must be reviewed for personal, sensitive or third-party content before publication.

## Spatial

**Crs:** `null`

**Extent:** Global, event-specific Areas of Interest and product extents; exact CRS/geometry semantics and layer metadata must be frozen per selected activation/product

## Temporal

**Extent:** Operational catalogue of past and active mapping activations; exact event, activation, satellite-acquisition, delivery and product-version timestamps are activation/product specific

## Variables and units

### Item 1

**Name:** activation metadata

**Unit:** `null`

**Description:** Activation code, event/category, countries, event/activation/update times, status and related identifiers.

### Item 2

**Name:** AOI and event/product extent geometry

**Unit:** `null`

**Description:** Event, Area of Interest and product geometries exposed by the public mapping interfaces; geometry representation/CRS must be preserved from the exact response or product metadata.

### Item 3

**Name:** mapped event delineation or grading

**Unit:** `null`

**Description:** Product-specific observed-event, delineation or grading layers derived from Earth-observation imagery and other geospatial information.

### Item 4

**Name:** impact and exposure summary statistics

**Unit:** varies

**Description:** Product-specific statistics can include affected area in hectares, road length in kilometres, building counts and estimated population; field names, units and missing-value semantics must be retained exactly.

### Item 5

**Name:** satellite acquisition metadata

**Unit:** `null`

**Description:** Sensor type/name, resolution class, acquisition time and product imagery metadata used for mapping context and provenance.


**Transformation:** `null`

## Review

**Status:** approved_metadata_only

**Reviewed at:** 2026-08-12T08:31:00Z

**Reviewer:** OpenCatastrophe source audit

**Notes:** Metadata-only engineering approval for public CEMS On-Demand Mapping activation and mapping-product metadata, with a concrete validation role against independently modelled hazard/event outputs. Raw/derived publication remains blocked until an exact public activation/product is selected, sensitivity and third-party rights are checked, product/version semantics are pinned and returned bytes are hashed and reviewed.
