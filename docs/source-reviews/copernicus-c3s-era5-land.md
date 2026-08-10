<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source review: Copernicus C3S ERA5-Land

- Review date: **2026-08-10**
- Admission state: **metadata only**
- Manifest: `manifests/copernicus.c3s.era5-land.json`
- Provider: Copernicus Climate Change Service (C3S) / ECMWF
- Product: ERA5-Land hourly data from 1950 to present
- DOI: `10.24381/cds.e2161bac`
- Release model: rolling catalogue

## Why this source is useful

ERA5-Land is a cross-peril land-state layer rather than a disaster catalogue. It can provide consistent antecedent and forcing context for flood, drought, wildfire, snow, heat and landslide research, allowing downstream workflows to reuse one well-described physical-state source instead of collecting unrelated peril-specific proxies.

## Scientific semantics

The catalogue describes a global land-surface reanalysis/simulation product at 0.1 degree distribution resolution with native model resolution around 9 km, hourly coverage from 1950 to present and daily updates.

The values are **model estimates**, not direct station or satellite observations. ECMWF explicitly documents uncertainty, with uncertainty generally increasing further back in time as fewer observations are available to constrain the atmospheric forcing. Any validation claim should therefore use independently admitted observations where feasible.

Important retrieval semantics include the exact variable, accumulation/instantaneous convention, soil layer, time range, geographic subset, format and catalogue state. A mutable `present` endpoint is discovery metadata, not a frozen artifact identity.

## Access and rights assessment

The authoritative CDS entry identifies ERA5-Land as `CC-BY-4.0`. CDS download requires login/registration and acceptance of the licence/terms.

Engineering interpretation:

- commercial use: allowed under CC BY 4.0;
- redistribution/adaptation: allowed subject to attribution and applicable CDS conditions;
- access: registration required for the reviewed download workflow;
- repository review scope: metadata only.

## Suitable initial OpenCatastrophe uses

- antecedent soil-moisture and land-state research;
- flood/drought/fire conditioning and benchmark features;
- snow and temperature context;
- reproducible cross-peril retrieval experiments;
- comparison with independently admitted gauge, station, radar or satellite observations.

ERA5-Land is not by itself an observed event catalogue, flood extent, wildfire perimeter, landslide inventory, vulnerability model or loss dataset.

## Requirements before raw admission

A future raw proposal must freeze the full CDS request and catalogue state, acquire bytes outside Git, record size and SHA-256, preserve parameter units/time semantics/grid information and document applicable uncertainty/known issues. Any resampling, aggregation or event extraction requires independent transformation lineage.

## Authoritative public references

- Dataset: `https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land`
- CC-BY terms: `https://cds.climate.copernicus.eu/licences/cc-by`
- DOI: `https://doi.org/10.24381/cds.e2161bac`
