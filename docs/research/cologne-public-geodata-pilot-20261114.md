<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Cologne public geodata pilot — 2026-11-14

This note explains a *bounded source-access experiment*, not a model-data
admission, new insured portfolio or approved loss calculation.

Canonical candidate metadata belongs to
[`landscape/sources-cologne-hazard-exposure-20261114.json`](../../landscape/sources-cologne-hazard-exposure-20261114.json).
The generated Markdown view must not be edited independently.

## Why Cologne?

Cologne is a useful small-region validation slice because the city provides
statistical geography, a managed-tree inventory and an interactive urban-flood
viewer, while NRW publishes official multi-scenario river-flood depth rasters,
boundaries and velocities. These inputs have sharply different legal and
scientific meanings. They must not be conflated.

## Safe first technical step

The repository contains a **read-only, fixed-endpoint WMS metadata probe**:

```bash
python -m unittest tests.test_cologne_hwrm_service_probe_v0
python research_runners/cologne_hwrm_service_probe_v0.py --live
```

The second command requires deliberate `--live` opt-in. It requests only
`GetCapabilities` at the exact official NRW service URL. Redirects, non-XML
responses, unexpected WMS versions, empty layer inventories and responses
above 4 MB fail closed. It prints only a JSON receipt containing bounded
layer metadata, SHA-256 of received XML and explicit non-admission flags. It
does **not** download or retain source rasters, tile images, GeoJSON, building
features or external raw bytes. The first command is fully offline.

A confirmed content-type from a website fetch or a source catalogue link
is not the same as the above complete live receipt. Until the real command
returns a parse-verified receipt on an authorized runner, the live canary
status is **not verified**.

## Original-provider flood-data path

The authoritative NRW source directory is:

https://www.opengeodata.nrw.de/produkte/umwelt_klima/wasser/hochwasser/hwrm/

It lists distinct EPSG:25832 ZIP distributions for HQ10–50, HQ100 and
extreme scenarios, including raster depth and vector boundary/velocity
products. The original directory identifies 2026-01 release dates and
the **Datenlizenz Deutschland – Zero 2.0**. The high-probability depth ZIP is
publisher-listed as approximately 2.4 GB. No original ZIP bytes were
downloaded or hashed during this change.

Next acquisition must select a single exact archive, confirm release
identity, obtain and hash its original bytes *outside Git* where separately
reviewed, inspect CRS and field/raster units, NoData, source vintage,
per-scenario depth semantics and local Cologne clipping, and log the source
selection and transformation. Never replace a full-file SHA-256 with an
HTTP ETag or a synthetic digest.

## Boundaries for model consumers

- Cologne statistics GeoPackage: confirm **exact ZIP/WFS distribution URLs**,
  asset-specific reuse terms, stable identifiers and geometrical/CRS
  semantics before local joins. Addresses and ALKIS building attributes
  are not insured asset or policy records.
- Cologne tree register: verify exact WFS endpoint, published terms,
  response schema, positional precision and municipality-managed coverage.
  Incomplete managed-tree inventory cannot be converted to complete
  urban tree exposure or a fall probability without independent science.
- StEB Köln 2025 3D pluvial maps: **viewer only** under current evidence.
  No authorized raw machine endpoint or redistribution scope is shown.
  Do not scrape internal map tiles or model payloads.
- NRW river-flood data: public publisher licensing is promising, but
  asset-identity, scientific fitness and OpenCatastrophe source-admission
  gates remain independent. Regulatory HQ classes are scenario
  descriptors, not directly event-specific stochastic occurrence rates.

A future model experiment needs a reviewed `manifests/` admission, raw or
derived artifact identity, full hashes, science and rights review, and a
`schemas/run-evidence-v2.schema.json` binding before consuming these
data as hazard, exposure or validation inputs.

## Checked provider entry points

- https://open.nrw/dataset/053549cf-b9c4-4633-80f9-680888ae5a04
- https://www.offenedaten-koeln.de/dataset/geopackage-raumbezugssystem-koeln
- https://www.offenedaten-koeln.de/dataset/baumkataster-koeln-fortlaufend-aktualisiert
- https://steb-koeln.de/service/karten-und-anwendungen/ueberflutungsgefahrenkarten
