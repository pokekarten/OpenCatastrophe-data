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

**Retrieval query or filters:** Metadata-only review of the public CEMS On-Demand Mapping portal, harvesting documentation, Emergency Response API documentation, Rapid Mapping product documentation and terms. No activation product bytes were downloaded or admitted. The documented machine-access scope is the anonymous public Rapid Mapping activation catalogue and bounded activation metadata, but no execution is authorized until service/API-use terms are independently cleared. The admitted metadata slice excludes free-text narrative, sensitive/restricted records and third-party-bearing content. Any future product acquisition must freeze activation code, AOI, product type/version, imagery acquisition/sensor, feasibility/status, delivery time, returned files and byte hashes.

**Access class:** open

**Modelling layer:** other

**Intended use:** Post-event validation and model-challenge evidence from provider-derived Earth-observation/geospatial mapping outputs for floods, wildfires, storms, earthquakes and other mapped emergencies. Public activation, AOI, product and imagery metadata can link independently modelled event footprints to CEMS delineation, grading, reference or situational products while preserving each product type's distinct semantics. CEMS Rapid Mapping products are operational interpretations derived from satellite imagery and other geospatial data; they are not direct physical hazard-intensity observations, surveyed damage, exposure inventory, vulnerability functions, insured-loss observations or universal ground truth.

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

**Notes:** The reviewed terms grant free access and permit reproduction, distribution, public communication, adaptation, modification and combination for covered CEMS On-Demand Mapping data. Some CEMS data may be restricted under applicable law, and third-party information linked from or incorporated through the service can have separate licence terms. Those cases require asset-specific review and are not cleared by this manifest. These dataset reuse terms do not by themselves establish service/API automation rights; those are represented separately in the source-access contract. This is an engineering rights assessment, not legal advice.

## Redistribution

**Status:** allowed

**Scope:** raw

**Conditions:** The reviewed CEMS terms support redistribution of covered public On-Demand Mapping data with required source attribution. OpenCatastrophe currently admits metadata only: no activation product bytes are committed. Restricted/sensitive records and third-party inputs or linked information require separate rights review before acquisition or publication.

## Privacy

**Personal data status:** none

**Confidential or proprietary status:** none

**Notes:** The admitted metadata slice is limited to public provider/product/event geospatial metadata and organisational activation context; it contains no natural-person, customer, policy, claims, portfolio or confidential/proprietary fields. Free-text narrative, sensitive/restricted activations and third-party-bearing content are outside this admission and require separate review before persistence or publication.

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

**Name:** AOI and product geometry metadata

**Unit:** `null`

**Description:** Area of Interest and product geometries exposed by the public mapping interfaces; geometry representation/CRS and the provider product type must be preserved from the exact response or product metadata.

### Item 3

**Name:** provider-derived delineation and grading product metadata

**Unit:** `null`

**Description:** Metadata describing CEMS products derived from Earth-observation imagery and other geospatial information. Delineation/event-extent and grading/damage-assessment semantics must remain distinct and must not be represented as direct physical hazard measurements or surveyed damage.

### Item 4

**Name:** exposure and consequence summary metadata

**Unit:** varies

**Description:** Product-specific summary metadata can refer to event extent, affected or exposed population, assets, land use and related counts/areas/lengths. These provider-derived estimates are product/context dependent and must not be collapsed into hazard, exposure-inventory, vulnerability or insured-loss observations.

### Item 5

**Name:** satellite acquisition metadata

**Unit:** `null`

**Description:** Sensor type/name, resolution class, acquisition time and product imagery metadata used for mapping context and provenance.


**Transformation:** `null`

## Review

**Status:** approved_metadata_only

**Reviewed at:** 2026-08-12T08:31:00Z

**Reviewer:** OpenCatastrophe source audit

**Notes:** Metadata-only engineering approval for public CEMS On-Demand Mapping activation and mapping-product metadata, with a bounded role as provider-derived post-event evidence for validating or challenging independently modelled event outputs. Product classes and mixed hazard/impact/exposure semantics must remain explicit. Raw/derived publication remains blocked until an exact public activation/product is selected, sensitivity and third-party rights are checked, product/version and imagery semantics are pinned and returned bytes are hashed and reviewed.
