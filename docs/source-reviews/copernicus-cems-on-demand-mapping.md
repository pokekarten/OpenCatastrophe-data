<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source review: Copernicus CEMS On-Demand Mapping

- Review date: **2026-08-12**
- Admission state: **metadata only**
- Manifest: `manifests/copernicus.cems.on-demand-mapping.json`
- Provider: Copernicus Emergency Management Service (CEMS) / European Commission
- Product family: On-Demand Mapping, with the first machine-access slice bounded to public Rapid Mapping activations and activation/product metadata
- Release model: rolling operational catalogue; activation and product versions are mutable operational records rather than one immutable dataset release

## Why this source is useful

CEMS On-Demand Mapping provides event-specific geospatial evidence produced for real emergencies from satellite imagery and other geospatial information. For OpenCatastrophe, its strongest current role is **post-event validation**: public activation, AOI, imagery and product metadata can connect a real event to mapped event extents, grading products and impact/exposure statistics.

This complements modelled hazard histories such as GloFAS. A modelled discharge, wind, seismic or wildfire hazard field can be compared against a separately sourced post-event mapping product without pretending that either source is universal ground truth.

The admission is intentionally narrower than the complete CEMS service. It does not make every Preparedness, Recovery or restricted/sensitive activation an approved OpenCatastrophe dataset.

## Source identity and mutability

The reviewed source is the public Copernicus EMS On-Demand Mapping portal and its documented harvesting interfaces. The service includes Emergency Response (Rapid Mapping) and Risk & Recovery Mapping. The initial access contract uses only the anonymous public Rapid Mapping activation catalogue and bounded activation metadata.

The catalogue is operational and changes over time. Reproducible scientific use must therefore freeze at least:

- retrieval UTC;
- activation code;
- event and activation timestamps;
- AOI identifier and extent;
- product type and feasibility state;
- product version identifier/number and delivery time;
- satellite sensor/acquisition metadata relevant to the selected product;
- exact returned URLs/files;
- response/file byte sizes and SHA-256 hashes;
- layer/format/CRS semantics and any provider quality or limitation notes applicable to the selected product.

No CEMS activation or product bytes are admitted by this review.

## Machine access

CEMS documents a programmatic Mapping API for activation discovery, activation metadata, areas of interest, product enumeration and links to vector/raster outputs. The Rapid Mapping documentation additionally describes public JSON endpoints for activation lists and activation details, including product, imagery, layer and statistics metadata.

The first OpenCatastrophe access contract is deliberately small:

- anonymous read-only access;
- public Rapid Mapping activations only;
- a one-record catalogue probe;
- no arbitrary caller-supplied host, path, headers or download URL;
- no automatic product ZIP/GeoPackage/GeoJSON/COG ingestion;
- response bytes ephemeral unless a later exact sample is independently reviewed.

This creates a safe API-first integration point without turning the repository into an uncontrolled data harvester.

## Access and rights assessment

The CEMS On-Demand Mapping terms state that users have free access to covered service information and permit reproduction, distribution, public communication, adaptation, modification and combination with other data/information, subject to the terms and required source citation.

Engineering interpretation for this metadata review:

- licence identity: bespoke `Copernicus EMS On-Demand Mapping Terms and Conditions`; no SPDX identifier is invented;
- commercial use: no non-commercial restriction is stated for the covered uses;
- redistribution/adaptation: allowed for covered public CEMS On-Demand Mapping data subject to source attribution and the terms;
- API access: public Rapid Mapping catalogue/metadata access is documented without authentication;
- repository review scope: metadata only.

Two fail-closed boundaries remain essential:

1. some CEMS On-Demand Mapping data may be restricted/sensitive and are not cleared here; and
2. third-party information linked or incorporated through the portal may carry separate licence terms and must not inherit CEMS reuse rights automatically.

## Scientific semantics

### Post-event mapping is not universal ground truth

CEMS products are produced for operational emergency-management purposes using available Earth-observation imagery and other geospatial information. Feasibility, sensor type, timing, cloud/visibility conditions, mapping method and product version can vary by activation and AOI.

A successful match between a model and a CEMS product therefore validates a bounded observation/product comparison, not the universal correctness of the model or mapping product.

### Product classes must remain distinct

Rapid Mapping exposes different product types and versions. Delineation, grading, reference/baseline and other product layers must not be collapsed into one generic hazard truth field. A downstream adapter must preserve the provider's product type, version, AOI and acquisition/delivery semantics.

### Damage grading is not insured loss

Grading products and summary statistics can describe affected buildings, land use, roads, population or event extent. These are not insurance claims, policy exposure, vulnerability functions or insured-loss observations. Any insurance-loss inference requires independent exposure, vulnerability, financial and validation layers.

### Event and activation times are different

The underlying event time, CEMS activation time, satellite acquisition time, product delivery time and later update/version timestamps represent different concepts. They must remain separate in any normalized OpenCatastrophe event record.

## Suitable initial OpenCatastrophe uses

Good initial uses:

- post-event spatial validation of independently modelled flood, wildfire, storm or earthquake footprints;
- event/AOI lookup and reproducible provenance linking;
- testing model event-detection outputs against independently produced mapping activations;
- satellite-acquisition/context metadata for validation windows;
- bounded extraction of published impact/exposure summary statistics with exact field/unit semantics;
- cross-peril API and provenance contract testing.

Not sufficient by itself for stochastic event generation, vulnerability calibration without additional methodological review, insured-loss estimation, pricing, capital or claims validation.

## Requirements before raw admission

Before any CEMS product bytes can move beyond metadata-only status, a proposal must:

1. select an exact public non-sensitive activation, AOI and product/version;
2. re-check the current CEMS terms and any product-specific/third-party rights notices;
3. record the exact API request or provider download identity;
4. acquire bytes outside Git unless repository policy explicitly allows the selected bounded artifact;
5. record byte size and SHA-256 for every response/file admitted to the evidence chain;
6. preserve event, activation, imagery, delivery and version timestamps separately;
7. preserve product type, layer names, units, CRS/geometry semantics and missing-value conventions;
8. record known provider limitations/quality notes relevant to the selected product;
9. keep restricted/sensitive activations fail-closed; and
10. obtain explicit asset-specific publication review.

Until then, no raw or derived CEMS On-Demand Mapping product bytes belong in this repository.

## Authoritative public references

- CEMS On-Demand Mapping portal: `https://mapping.emergency.copernicus.eu/`
- Harvesting/API overview: `https://mapping.emergency.copernicus.eu/about/how-to-harvest-cems-mapping-data/`
- Emergency Response / Rapid Mapping API: `https://mapping.emergency.copernicus.eu/about/how-to-harvest-cems-mapping-data/emergency-response-data/`
- Rapid Mapping manual: `https://mapping.emergency.copernicus.eu/about/rapid-mapping-manual/`
- Terms and conditions: `https://mapping.emergency.copernicus.eu/terms-and-conditions/`
