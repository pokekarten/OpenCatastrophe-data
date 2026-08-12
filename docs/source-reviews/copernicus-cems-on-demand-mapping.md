<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source review: Copernicus CEMS On-Demand Mapping

- Review date: **2026-08-12**
- Admission state: **metadata only**
- Manifest: `manifests/copernicus.cems.on-demand-mapping.json`
- Provider: Copernicus Emergency Management Service (CEMS) / European Commission
- Product family: On-Demand Mapping, with the first documented machine-access slice bounded to public Rapid Mapping activations and activation/product metadata
- Release model: rolling operational catalogue; activation and product versions are mutable operational records rather than one immutable dataset release

## Why this source is useful

CEMS On-Demand Mapping provides event-specific geospatial products for real emergencies. Rapid Mapping products are produced by service providers from satellite imagery and other geospatial information for defined Areas of Interest (AOIs) and acquisition times. For OpenCatastrophe, their strongest current role is **independent post-event evidence for validation and model challenge**.

That role is deliberately narrower than “ground truth”. CEMS products can help compare an independently modelled event footprint with provider-derived delineation, grading, reference or situational information, while preserving each product type's own meaning and limitations. They do not independently prove physical hazard intensity, surveyed damage, exposure truth, vulnerability, insured loss or model correctness.

The admission is intentionally narrower than the complete CEMS service. It does not make every Preparedness, Recovery or restricted/sensitive activation an approved OpenCatastrophe dataset.

## Source identity and mutability

The reviewed source is the public Copernicus EMS On-Demand Mapping portal and its documented harvesting interfaces. The service includes Emergency Response (Rapid Mapping) and Risk & Recovery Mapping. The initial access contract documents only the anonymous public Rapid Mapping activation catalogue and bounded activation metadata.

The catalogue is operational and changes over time. Reproducible scientific use must therefore freeze at least:

- retrieval UTC;
- activation code;
- event and activation timestamps;
- AOI identifier and extent;
- product type and feasibility/status;
- product version identifier/number and delivery time;
- satellite sensor/acquisition metadata relevant to the selected product;
- exact returned URLs/files;
- response/file byte sizes and SHA-256 hashes;
- layer/format/CRS semantics; and
- provider quality and limitation notes applicable to the selected product.

No CEMS activation or product bytes are admitted by this review.

## Machine access

CEMS documents public JSON routes for Rapid Mapping activation discovery and activation details. The documentation establishes that public activation information can be accessed programmatically without authentication and exposes activation, AOI, product, imagery, layer and summary-statistics metadata.

That is a **technical access fact, not an automation-rights decision**. The reviewed On-Demand Mapping dataset terms permit reuse of covered public CEMS data, but no authoritative service/API-specific term has been identified that proves those data-reuse terms also govern automated use of the Rapid Mapping service endpoints.

The OpenCatastrophe access contract therefore remains documentation-only:

- public/anonymous technical interface documented;
- no active probe;
- no provider request performed by this remediation;
- no arbitrary caller-supplied host, path, headers or download URL;
- no automatic product ZIP/GeoPackage/GeoJSON/COG ingestion;
- no external response bytes persisted; and
- future execution requires an independent service/API-use terms review before any probe can be enabled.

## Access and rights assessment

The CEMS On-Demand Mapping terms state that users have free access to covered service information and permit reproduction, distribution, public communication, adaptation, modification and combination with other data/information, subject to the terms and required source citation.

Engineering interpretation for this metadata review:

- dataset licence identity: bespoke `Copernicus EMS On-Demand Mapping Terms and Conditions`; no SPDX identifier is invented;
- dataset commercial use: no non-commercial restriction is recorded for the covered reuse path;
- dataset redistribution/adaptation: allowed for covered public CEMS On-Demand Mapping data subject to source attribution and the terms;
- technical API access: public Rapid Mapping catalogue/metadata endpoints are documented without authentication;
- API/service-use terms: **unknown under current evidence**;
- commercial API automation: **unknown under current evidence**;
- repository review scope: metadata only.

The distinction is intentional: public connectivity does not itself grant automation rights, and dataset reuse rights must not be silently copied into the API/service policy field.

Three fail-closed boundaries remain essential:

1. no API/service execution while service-use terms remain unresolved;
2. restricted/sensitive CEMS records are outside this admission; and
3. third-party information linked or incorporated through the service may carry separate licence terms and must not inherit CEMS reuse rights automatically.

## Scientific semantics

### Rapid Mapping products are provider-derived geospatial interpretations

CEMS describes a Rapid Mapping product as a set of geospatial information outputs derived from acquisition, processing and analysis of satellite imagery and other geospatial data sources for a specific AOI and acquisition time. These are operational emergency-mapping products, not direct sensor measurements of physical hazard intensity and not universal event truth.

Successful spatial agreement with an OpenCatastrophe model is therefore evidence for one bounded model/product comparison. It does not establish universal correctness of the model or of the mapping product.

### Product classes must remain distinct

Rapid Mapping offers different product types with different meanings. In particular:

- First Estimate Product provides a rapid, rough early assessment from suitable post-event imagery;
- Delineation products assess event impact/extent from post-event imagery;
- Grading products add provider damage-grade information and spatial distribution;
- Reference products provide pre-event territory/assets context; and
- Situational Reporting aggregates activation information and can include information from other sources.

A downstream adapter must preserve product type, AOI, version/delivery, imagery acquisition/sensor, feasibility/status and known limitations rather than collapsing these classes into one hazard field.

### Exposure and consequence summaries are mixed derived semantics

CEMS exposure/consequence tables can include event extent, affected or exposed population, assets, land use and related counts/areas/lengths. Some quantities may rely on external supporting datasets and provider analysis. These values must remain tagged as product-specific provider-derived summaries; they are not an OpenCatastrophe exposure inventory, vulnerability function, physical hazard measurement, claims record or insured-loss observation.

### Damage grading is not surveyed damage or insured loss

Grading products provide provider damage-assessment information derived from imagery and other geospatial analysis. They are useful for post-event comparison but must not be described as surveyed loss truth. Any insurance-loss inference requires independent exposure, vulnerability, financial and validation layers.

### Event and activation times are different

The underlying event time, CEMS activation time, satellite acquisition time, product delivery time and later update/version timestamps represent different concepts. They must remain separate in any normalized OpenCatastrophe event record.

## Suitable initial OpenCatastrophe uses

Good initial uses after exact product-specific review:

- post-event spatial validation/challenge of independently modelled flood, wildfire, storm or earthquake footprints;
- event/AOI lookup and reproducible provenance linking;
- satellite-acquisition/context metadata for validation windows;
- preserving product-specific delineation/grading/reference semantics for model comparison;
- bounded analysis of published exposure/consequence summaries with exact field/unit/source semantics; and
- cross-peril provenance-contract testing.

Not sufficient by itself for stochastic event generation, direct hazard-intensity calibration, vulnerability calibration without additional methodological review, insured-loss estimation, pricing, capital or claims validation.

## Requirements before any API execution or raw admission

Before an API probe can be enabled, a proposal must identify and review authoritative service/API-use terms separately from the dataset reuse terms and explicitly clear the intended automation posture.

Before any CEMS product bytes can move beyond metadata-only status, a proposal must:

1. select an exact public non-sensitive activation, AOI and product type/version;
2. re-check the current CEMS data terms, service/API-use terms and any product-specific/third-party rights notices;
3. record the exact API request or provider download identity;
4. acquire bytes outside Git unless repository policy explicitly allows the selected bounded artifact;
5. record byte size and SHA-256 for every response/file admitted to the evidence chain;
6. preserve event, activation, imagery, delivery and version timestamps separately;
7. preserve product type, layer names, units, CRS/geometry semantics and missing-value conventions;
8. record known provider limitations/quality notes relevant to the selected product;
9. keep restricted/sensitive activations fail-closed; and
10. obtain explicit asset-specific publication review.

Until those gates are satisfied, no live CEMS Rapid Mapping API execution and no raw or derived CEMS On-Demand Mapping product bytes are authorized by this source review.

## Authoritative public references

- CEMS On-Demand Mapping portal: `https://mapping.emergency.copernicus.eu/`
- Harvesting/API overview: `https://mapping.emergency.copernicus.eu/about/how-to-harvest-cems-mapping-data/`
- Emergency Response / Rapid Mapping API: `https://mapping.emergency.copernicus.eu/about/how-to-harvest-cems-mapping-data/emergency-response-data/`
- Rapid Mapping manual: `https://mapping.emergency.copernicus.eu/about/rapid-mapping-manual/`
- Product definition: `https://mapping.emergency.copernicus.eu/about/rapid-mapping-manual/product-overview/what-is-a-product/`
- Rapid Mapping portfolio: `https://mapping.emergency.copernicus.eu/about/rapid-mapping-portfolio/`
- Exposure and consequences summary tables: `https://mapping.emergency.copernicus.eu/about/rapid-mapping-manual/product-overview/what-is-delivered-in-a-product/map/map-marginalia/summary-table-exposure-and-consequences/`
- Terms and conditions: `https://mapping.emergency.copernicus.eu/terms-and-conditions/`
