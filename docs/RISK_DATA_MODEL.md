<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Risk data model boundary

OpenCatastrophe-data owns **admission, identity, provenance, rights and scientific semantics** for catastrophe-risk data. It deliberately does not invent a second universal file format for every hazard, exposure, vulnerability or model result.

The stable public boundary is standards-first:

| Layer | Native OpenCatastrophe responsibility | Preferred public interoperability |
| --- | --- | --- |
| Dataset admission | exact source/product/version/query identity; rights; privacy; redistribution scope; artifact hashes; review state | `schemas/dataset-manifest.schema.json` |
| Hazard / event catalogue / footprint | source identity, peril, event semantics, intensity measure and unit, spatial/temporal support, transformation lineage | Risk Data Library Standard (RDLS) hazard metadata; source-native scientific formats |
| Exposure | source identity, geography, asset/taxonomy semantics, value basis, valuation date, observed/inferred state | RDLS exposure metadata; Oasis Open Exposure Data (OED) for insurance exposure exchange |
| Vulnerability / fragility / consequence | source identity, hazard-intensity semantics, asset applicability, calibration domain, response stage, uncertainty and transfer limits | RDLS vulnerability metadata; source-native functions with explicit adapters |
| Observed impact / loss | source identity, damage/claim/loss stage, value and currency basis, aggregation and coverage semantics | RDLS loss metadata |
| Model results | reproducible run identity and evidence only; model-result payloads are not a new data-store format here | Oasis Open Results Data (ORD) where an insurance result exchange is needed |
| Execution evidence | exact repository/input/output identities, environment, randomness and validation state | `schemas/run-evidence-v1.schema.json` |

## Why this boundary exists

RDLS 1.0 already provides an open metadata vocabulary for hazard, exposure, vulnerability and loss datasets. OED provides a model-independent insurance exposure exchange structure, while ORD provides a model-result exchange structure. OpenCatastrophe should add project-specific contracts only where rights, provenance, scientific identity or reproducibility require something those standards do not express.

A new generic schema is therefore not justified merely because an internal experiment used one. Source-specific adapters and synthetic fixtures can be narrow without becoming permanent public domain contracts.

## Canonical scientific identities

The following concepts must survive source ingestion and transformation even when the external file format changes.

### Event

An event identity must distinguish at least:

- `event_id` or an explicit source event identifier;
- peril and physical process;
- historical, stochastic or deterministic-scenario meaning;
- start/end time when known;
- source dataset identity;
- annual rate or occurrence-model reference **only when independently evidenced**.

A historical date does not create an annual rate. A return-period raster is not an event catalogue unless an explicit event-construction method exists.

### Hazard footprint

A footprint must preserve:

- event identity;
- spatial support or grid/area-peril identity;
- intensity measure and unit;
- CRS and spatial resolution where applicable;
- deterministic/distribution/sample meaning;
- source and transformation identity;
- missing or unsupported cells as distinct states.

Units may never be inferred only from a column name.

### Exposure

Exposure data should preserve stable portfolio/account/policy/location/building/coverage identities when those concepts exist, plus:

- coordinates or governed geometry and CRS;
- country/region;
- building, contents, business-interruption or other values as separately identified coverages;
- currency, valuation date and value basis;
- occupancy, construction, build year, storeys/height and floor area when available;
- whether each material attribute is observed, supplied, inferred, imputed or synthetic;
- source quality and transformation lineage.

Building counts, building footprints, population or floor area are **not insured total insured value (TIV)**. Any value inference is a separate transformation with its own assumptions and provenance. Missing source attributes must not be replaced by silent OED or project defaults.

### Vulnerability, fragility and consequence

The generic word `vulnerability` is not enough for executable scientific work. A reusable view needs the identity tuple:

- peril;
- hazard intensity measure and unit;
- asset taxonomy/applicability;
- calibration geography and period;
- response stage;
- value/loss basis where economic;
- uncertainty model;
- source/version.

Response stages must remain distinguishable, for example engineering demand, physical damage state, physical damage ratio, repair consequence, direct economic loss, insured impact or claim-stage relationships. A claims-calibrated relationship must not silently become a physical fragility curve.

### Observed loss and claims evidence

Observed impact or claims data require explicit semantics for:

- physical damage versus economic impact versus insured/claim stage;
- paid, incurred or ultimate basis when relevant;
- currency, price date and inflation treatment;
- policy population, deductible/limit treatment and reporting threshold when known;
- event assignment and geographic aggregation;
- selection, insurance-penetration and reporting limitations.

If those properties are unknown, the source may remain validation evidence but must not be presented as a clean physical-damage target.

## Region / peril bundles

A future region-peril bundle may bind admitted manifests for hazard, exposure, vulnerability and validation evidence. It should carry references rather than copy source metadata and should make unresolved mappings and rights explicit.

OpenCatastrophe-data does **not** freeze a generic region-bundle schema yet. The first such contract should be justified by at least one concrete multi-source pilot with exact admitted manifests. Until then, dataset manifests are the durable source identities and GitHub Issues/PRs are the planning layer.

## Contract promotion rule

A proposed data contract becomes a durable schema only when all of the following are true:

1. at least one real public source or interoperable standard demonstrates the need;
2. source rights and scientific meaning are independently reviewable from public evidence;
3. the contract does not duplicate an established open standard without a documented gap;
4. schema, executable validation, negative tests and documentation can evolve together;
5. the contract can be validated without private data, private repositories, proprietary services or hidden chat context.

## Public standards tracked

- Risk Data Library Standard (RDLS) 1.0: `https://docs.riskdatalibrary.org/en/1.0/`
- Oasis Open Data Standards: `https://oasislmf.github.io/sections/OED.html` and `https://oasislmf.github.io/sections/ORD.html`

Exact external standard versions must be pinned by any adapter or mapping that claims compatibility. A documentation link alone is not an interoperability claim.
