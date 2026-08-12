<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source review: Copernicus CEMS Global Flood Monitoring v4.1.1

- Review date: **2026-08-12**
- Admission state: **metadata only**
- Manifest: `manifests/copernicus.cems.gfm.v4.1.1.json`
- Provider: Copernicus Emergency Management Service (CEMS) / European Commission Joint Research Centre
- Product: Global Flood Monitoring (GFM)
- Frozen version: **4.1.1**, released **2026-06-11**

## Why this source is useful

GFM fills a distinct observation layer in the OpenCatastrophe flood-validation stack. It continuously processes Sentinel-1 Synthetic Aperture Radar imagery in near real time and derives flood/water extent products using an ensemble of three independent flood-mapping algorithms.

The accepted role is deliberately narrow: **satellite-derived flood-footprint observation for validation and model challenge**. GFM can be compared with independently modelled flood outputs or used alongside in-situ and operational mapping evidence, but it is not river discharge, gauge observation, flood depth or velocity, return-period intensity, vulnerability, surveyed damage, insured loss or universal ground truth.

This capability is not duplicated by the already admitted GloFAS historical hydrology source, which is modelled discharge/hydrological history, or by CEMS On-Demand Mapping, which is event-specific provider-derived emergency mapping.

## Version identity and reproducibility

GFM uses semantic versioning. Current GFM version documentation states:

- MAJOR increments may make data layers incompatible; data from different MAJOR versions must not be used together silently;
- MINOR increments preserve backwards compatibility while changing the production system; and
- PATCH increments represent backwards-compatible fixes or auxiliary-data changes.

Version 4.1.1 was released on 2026-06-11 and integrated Sentinel-1D into the operational workflow. During 2026-06-11 through 2026-06-29 operations relied on Sentinel-1A plus Sentinel-1D while Sentinel-1C transitioned to its operational orbit. From 2026-06-29 onward the documented operational constellation is Sentinel-1C plus Sentinel-1D.

A reproducible OpenCatastrophe validation asset must therefore freeze at least the GFM version, Sentinel-1 scene/acquisition time, footprint/AOI, exact selected layer(s), response/file identity and relevant quality/mask context.

## Current product semantics

The current Product User Manual and Product Definition Document describe **ten** GFM output layers. Older/deprecated documentation may describe eleven; this admission follows the current PUM/PDD and does not infer current semantics from deprecated pages.

The primary validation layer is **Observed Flood Extent**, an ensemble Sentinel-1 SAR-derived classification of floodwater extent. Important supporting semantics include:

- **Observed Water Extent** — open/calm water; distinct from flood-only extent;
- **Reference Water Mask** — normal permanent/seasonal water used when distinguishing flood from normal water;
- **Exclusion Mask** — locations where robust SAR flood/water classification is not technically feasible;
- **Likelihood Values** — product-specific classification-confidence appraisal;
- **Advisory Flags** — environmental/input conditions that may reduce flood/water-detection quality without necessarily masking the pixel; and
- **Sentinel-1 Footprint and Metadata** — acquisition provenance needed to bind observations to scenes.

The current PUM states that processing uses the 20 m spatial resolution of the pre-processed Sentinel-1 data cube. Exact delivered asset CRS, grid, footprint and file semantics must still be frozen from the selected product.

## Scientific limitations

SAR flood mapping has both false-alarm and missed-alarm modes. CEMS documentation specifically identifies water-look-alike surfaces and conditions such as dry/sandy ground, frozen ground, wet snow and smooth impervious surfaces. Static conditions, topography and radar-shadow limitations are represented through the Exclusion Mask; dynamic conditions such as wind, frozen conditions, wet snow or dry soil are surfaced through Advisory Flags.

Consequently:

1. absence of mapped flooding does not prove absence of flooding;
2. excluded/no-data pixels must not be interpreted as unflooded;
3. Advisory Flags must remain available to downstream validation logic;
4. Likelihood Values are not a generic probabilistic flood-hazard model;
5. product-version and algorithm changes can affect comparability; and
6. agreement with GFM is evidence for a bounded product/model comparison, not proof of model correctness.

## Access boundary

Current GFM documentation lists multiple dissemination channels: GloFAS/EFAS map viewers, REST APIs, Web Map Service, dedicated web portal and GFM STAC catalogue. The REST API documentation states that API use requires an access token. STAC/WMS availability does not authorize OpenCatastrophe to perform an unreviewed crawl or to persist arbitrary provider bytes.

This PR therefore creates **no executable access contract** and performs no provider request. Issue #173 remains the owner of any future machine-route selection, probe recipe, authentication/service-terms decision or bounded sample execution.

Before a live sample is proposed, the access lane must freeze one exact route and establish current service/API-use terms for that route separately from dataset reuse rights.

## Rights assessment

The reviewed CEMS Early Warning Data Store terms explicitly include Global Flood Monitoring among CEMS early-warning and monitoring systems. They grant covered users free access and permit reproduction, distribution, public communication, adaptation, modification and combination, subject to the stated terms.

The terms also require source notices for distributed/communicated data and a modified-information notice for adapted or modified data. They warn that some CEMS data can be restricted and that third-party information may have separate licence terms.

Engineering interpretation for this metadata admission:

- licence identity: bespoke `Terms of use of the CEMS Early Warning Data Store (rev. 11)`; no SPDX identifier is invented;
- covered-data commercial use: no non-commercial restriction is recorded in the reviewed reuse grant;
- covered-data redistribution/adaptation: allowed subject to notices and the other terms;
- restricted or third-party information: does not inherit this approval automatically;
- service/API automation policy: remains a separate future access review; and
- repository admission: metadata only.

No raw GFM asset, response or derived product is approved for Git publication by this review.

## Suitable OpenCatastrophe use

The preferred next use is a single-event, predeclared validation slice that keeps the evidence layers distinct, for example:

`forcing/precipitation -> GloFAS modelled discharge -> gauge observation -> GFM flood extent -> CEMS Rapid Mapping product -> exposure/context`

For that pilot, GFM should supply satellite-derived observed flood extent and its quality/mask provenance. Selection criteria and comparison metrics must be frozen before inspecting validation outcomes.

## Requirements before raw/API sample use

A later asset-specific proposal must:

1. freeze GFM version and exact Sentinel-1 acquisition/scene identity;
2. freeze AOI/time selection and requested GFM output layers;
3. preserve Exclusion Mask, Advisory Flags, Reference Water Mask and relevant metadata with the validation layer;
4. record the exact machine route, authentication state and current service/API-use terms;
5. record request identity, retrieval UTC, response/file byte count and SHA-256;
6. keep different GFM MAJOR versions separate unless an explicit compatibility method is reviewed;
7. preserve product-specific missing/no-data and classification semantics;
8. keep provider bytes outside Git until exact publication rights and repository value are independently reviewed; and
9. obtain independent science/rights review before any admission promotion.

## Authoritative public references

- GFM versioning: `https://extwiki.eodc.eu/GFM/GFMVersioning`
- GFM Product User Manual: `https://extwiki.eodc.eu/GFM/PUM`
- GFM Product User Manual — output layers: `https://extwiki.eodc.eu/GFM/PUM/Products`
- GFM Product User Manual — recommendations/caveats: `https://extwiki.eodc.eu/GFM/PUM/Recommendations`
- GFM Product User Manual — data access: `https://extwiki.eodc.eu/GFM/PUM/DataAccess`
- GFM Product User Manual — REST APIs: `https://extwiki.eodc.eu/GFM/PUM/DataAccess/REST-APIs`
- GFM Product User Manual — STAC: `https://extwiki.eodc.eu/GFM/PUM/DataAccess/STAC`
- GFM Product Definition Document: `https://extwiki.eodc.eu/GFM/PDD/Introduction`
- CEMS v4.1.1 announcement: `https://global-flood.emergency.copernicus.eu/react/news/246-gfm-version-411-welcomes-sentinel-1d`
- CEMS Early Warning Data Store terms: `https://ewds.climate.copernicus.eu/licences/terms-of-use-cems`
