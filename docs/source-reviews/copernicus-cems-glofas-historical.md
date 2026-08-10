<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source review: Copernicus CEMS GloFAS historical river discharge and related data

- Review date: **2026-08-10**
- Admission state: **metadata only**
- Manifest: `manifests/copernicus.cems.glofas-historical.json`
- Provider: Copernicus Emergency Management Service (CEMS), implemented by the European Commission Joint Research Centre and distributed through the CEMS Early Warning Data Store
- Product: River discharge and related historical data from the Global Flood Awareness System (GloFAS)
- DOI: `10.24381/cds.a4fdd6b9`
- Release model: rolling dataset; no immutable byte release is inferred from the DOI

## Why this source is useful

GloFAS historical data provide a strong open hydrology source for the flood foundation. The product supplies gridded modelled daily hydrological time series across a global domain, including river discharge and related hydrological variables.

This is useful for hydrological history, event-detection research, forcing/benchmark workflows and reproducibility tests. It is deliberately **not** treated as a ready-made flood inundation, flood-depth, stochastic-event or insured-loss dataset.

## Source identity and mutability

The reviewed catalogue entry is the CEMS/EWDS dataset `River discharge and related historical data from the Global Flood Awareness System`, DOI `10.24381/cds.a4fdd6b9`.

The catalogue is updated over time and exposes configurable requests. The DOI identifies the product, not the exact bytes returned by a future request. A reproducible acquisition must therefore pin at least:

- request date/time and catalogue state;
- selected hydrological variable(s);
- date range;
- geographic area/subset;
- available system/data-type/version choices relevant to the request;
- output format and archive mode;
- exact returned file set;
- byte size and SHA-256 for every returned artifact.

No GloFAS data bytes are admitted by this review.

## Access and rights assessment

The EWDS download surface requires login/registration to submit a request, so this manifest records `registration_required` rather than conflating public availability with anonymous download.

The authoritative `CEMS-FLOODS datasets licence (rev. 1)` grants free access and permits reproduction, distribution, communication to the public, adaptation, modification and combination with other data/information, subject to its terms. It also requires source notices when CEMS information is distributed or modified.

Engineering interpretation for this metadata review:

- licence identity: `CEMS-FLOODS datasets licence (rev. 1)`; no SPDX identifier is invented for these bespoke terms;
- commercial use: no non-commercial restriction is stated for the covered CEMS EFAS/GloFAS data uses;
- redistribution/adaptation: allowed subject to the CEMS-FLOODS terms and notices;
- access: registration required for the reviewed download workflow;
- repository review scope: metadata only.

The CEMS-FLOODS licence notes that some CEMS data can be restricted. That general statement does not justify assuming rights for a different CEMS product. This admission is limited to the exact historical GloFAS catalogue entry that points to the CEMS-FLOODS licence.

## Scientific semantics

### Modelled hydrology, not observations

The catalogue describes gridded **modelled** daily hydrological time series produced with the LISFLOOD hydrological model forced by ERA5 meteorological reanalysis data. These values must not be labelled as direct river-gauge observations.

Independent gauge observations may later be used for validation, but require their own source identities and rights.

### Discharge is not inundation depth

River discharge is a hydrological state/flow variable. It does not by itself define:

- flood extent;
- water depth at buildings;
- velocity or duration at exposed assets;
- a stochastic event catalogue;
- vulnerability or damage;
- insured loss.

Any conversion from discharge to inundation requires an explicit hydraulic/inundation method, additional terrain/channel information, configuration and validation.

### Variables and units

The reviewed catalogue documents, among other variables:

- river discharge in the last 24 hours — `m3 s-1`;
- runoff water equivalent — `kg m-2`;
- snow depth water equivalent — `kg m-2`;
- soil wetness index — dimensionless;
- ancillary upstream area — `m2`;
- ancillary elevation — `m`.

A future acquisition must preserve the exact variable name, unit and processing/version metadata returned for the selected request rather than relying only on this review summary.

### Time and event semantics

A daily gridded time series is not automatically an event catalogue. If OpenCatastrophe later derives flood events, the event-segmentation rule, threshold, spatial grouping, temporal declustering and transformation identity must be explicit and reproducible.

## Suitable initial OpenCatastrophe uses

Good initial uses:

- global/regional hydrological-history research;
- deterministic retrieval/provenance tests;
- discharge-based event-detection experiments with explicit derived lineage;
- comparison with independently admitted flood maps or hydraulic-model outputs;
- cross-peril source-contract tests.

Not sufficient by itself for inundation footprint, property damage, insurance loss, pricing, capital or flood-warning claims.

## Requirements before raw admission

Before GloFAS historical bytes can move beyond metadata-only status, a proposal must:

1. re-check the current exact catalogue entry and CEMS-FLOODS licence;
2. freeze the complete retrieval request;
3. acquire the returned files outside Git;
4. record byte size and SHA-256 for every artifact;
5. record variables, units, spatial grid/CRS, time range, system/version/data type and known issues applicable to the selected request;
6. keep ancillary files and dependencies explicitly identified;
7. preserve required CEMS source/modification notices;
8. record any event extraction or other transformation independently; and
9. obtain explicit asset-specific publication review.

Until then, no raw or derived GloFAS bytes belong in this repository.

## Authoritative public references

- GloFAS historical dataset: `https://ewds.climate.copernicus.eu/datasets/cems-glofas-historical`
- CEMS-FLOODS datasets licence: `https://cds.climate.copernicus.eu/licences/cems-floods`
- Dataset DOI: `https://doi.org/10.24381/cds.a4fdd6b9`
