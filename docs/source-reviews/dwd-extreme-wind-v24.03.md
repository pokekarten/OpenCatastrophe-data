<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source review: DWD 10-minute extreme-wind observations v24.03

- Review date: 2026-08-09
- Admission state: **metadata only**
- Manifest: `manifests/dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03.json`

## Authoritative source identity

- Provider: Deutscher Wetterdienst (DWD), Climate Data Center (CDC)
- Product: `10-minute station observations of extreme wind for Germany`
- DWD dataset citation version: `v24.03`
- DWD dataset identifier: `urn:x-wmo:md:de.dwd.cdc::obsgermany-climate-10min-extreme_wind`

Product root:

`https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/`

Dataset description:

`https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/DESCRIPTION_obsgermany_climate_10min_extreme_wind_en.pdf`

The DWD description explicitly labels/cites the dataset as version `v24.03` (publication date 2024-03-29). The same document states that the `historical/` files are updated annually; completed quality control makes values constant **for a particular historical version**, while annual version changes can incorporate corrections and historical additions.

Therefore `v24.03` is retained as the authoritative DWD dataset citation version for this metadata admission, but it is **not treated as a substitute for exact raw-byte identity**. A historical ZIP acquired later must additionally be bound by its exact DWD filename/time coverage, retrieval evidence, byte count and SHA-256. A current directory file must never be assumed immutable merely because the dataset description carries `v24.03`.

CDC source-specific terms of use:

`https://opendata.dwd.de/climate_environment/CDC/Terms_of_use.pdf`

The CDC directory identifies this terms document with status **May 2024**. The document states that CC BY 4.0 applies to data in the CDC Open Data area and points to the DWD copyright information for details.

DWD Open Data FAQ:

`https://www.dwd.de/DE/leistungen/opendata/faqs_opendata.html`

DWD legal notices:

`https://www.dwd.de/DE/service/rechtliche_hinweise/rechtliche_hinweise.html`

DWD attribution guidance:

`https://www.dwd.de/DE/service/rechtliche_hinweise/vorlagen_quellenangabe.html`

## Rights assessment

The source-specific dataset description states that CC BY 4.0 applies. The CDC-specific terms-of-use document states the same for the CDC Open Data area. Current DWD Open Data and legal pages likewise identify CC BY 4.0 as the reuse licence for freely accessible DWD geodata and require source attribution.

Engineering interpretation for this exact source/version:

- licence identity: `CC-BY-4.0`;
- commercial use: allowed by the standard licence;
- redistribution: source rights support raw redistribution subject to the licence/attribution conditions;
- adaptation: permitted under CC BY 4.0; attribution and indication of modifications remain relevant;
- share-alike: not required by CC BY 4.0;
- access: public DWD Open Data access, no registration required for the Open Data server.

This rights assessment is source-specific and time-specific. It does not automatically apply to unrelated DWD paid/restricted services, third-party material separately marked by DWD, or later releases whose terms change.

`terms_content_sha256` remains intentionally unset until the exact source bytes of the terms document are acquired and hashed directly. A digest must not be inferred from rendered text or screenshots.

OpenCatastrophe's repository review is intentionally narrower than the source-rights ceiling: only metadata is approved at this stage. No DWD measurement ZIP has been given an OpenCatastrophe raw-artifact identity or approved for Git publication.

## Scientific content

The DWD description identifies station observations of:

- extreme/gust wind speed;
- wind direction;
- wind velocity;
- units of metres per second and degrees;
- WGS 84 station coordinates;
- temporal coverage beginning in 1989.

The extreme-wind product includes fields such as:

- `FX_10` — maximum wind speed in the preceding ten-minute interval;
- `FNX_10` — minimum wind speed in the preceding ten-minute interval;
- `FMX_10` — a maximum based on shorter-period wind maxima summarized over the interval;
- `DX_10` — direction associated with the maximum wind speed.

The dataset also provides station/instrument/algorithm metadata needed to interpret long records.

## Quality-state distinction

The product has materially different operational subsets:

- `historical/` — versioned; DWD states quality control is completed for the version;
- `recent/` — rolling/daily updates; quality control is not complete;
- `now/` — near-real-time updates; quality control is not complete;
- `meta_data/` — station, instrument and measurement-rule metadata.

For a first reproducible OpenCatastrophe research adapter, `historical/` is therefore the preferred initial source class. `recent/` and `now/` should not be silently mixed into a frozen reference dataset.

## Time semantics

The source description notes a historical timestamp convention change: older historical measurements before 2000 use MEZ, while data from 2000 onward are assigned UTC timestamps. Any ingestion adapter must preserve/source this distinction and normalize time only through an explicit, tested transformation.

Do not infer that every historical timestamp is UTC merely because recent files are UTC.

## Known uncertainty / station-history considerations

DWD documents multiple reasons long station series need metadata-aware interpretation, including station relocation, instrumentation changes, changes in quality-control procedures, local/regional influences and other operational changes.

For trend, extreme-value or event validation work, OpenCatastrophe should therefore preserve links to station geography/instrument metadata rather than treating a station ID as a time-invariant physical measurement configuration.

The source also notes that some partner-network stations may differ from DWD/WMO operating conventions. This is a scientific-quality consideration, not a reason to reinterpret the dataset-level licence.

## Raw-artifact admission boundary

This metadata admission does not select or approve a station/file for raw publication. Any later raw-artifact proposal must identify the exact DWD filename/time coverage and the relevant station/instrument metadata independently, then bind each acquired file to its own retrieval timestamp, byte count, SHA-256 and logical `external://...` identity.

Mutable directory state or dataset-level version labels are not substitutes for exact artifact identity. Live pilot selection and acquisition sequencing belong in public GitHub Issues until reviewed evidence is ready to become durable repository state.

## Suitable OpenCatastrophe use

Good initial uses:

- observational validation of a wind-hazard model at station locations;
- checking event dates/times and local gust magnitudes;
- studying measurement/QC sensitivity;
- later calibration evidence, with explicit station-history handling;
- testing data-ingestion/provenance pipelines.

Not sufficient by itself for:

- a spatially complete windstorm hazard footprint;
- an event catalogue frequency model;
- loss/vulnerability calibration without exposure/damage evidence;
- tail extrapolation at unobserved locations;
- production catastrophe pricing/capital claims.

Station observations are point measurements. Spatial hazard reconstruction requires a separately specified and validated method or gridded/reanalysis source.

## Requirements before any raw admission

Before any DWD raw measurement file can move beyond metadata-only status, the proposal must re-check current DWD terms, identify exact source and supporting metadata artifacts, acquire them outside Git, record independent byte identities and retrieval evidence, verify those bytes against the recorded identity before use, and obtain an explicit asset-specific review. Until then, raw and derived publication remain blocked.
