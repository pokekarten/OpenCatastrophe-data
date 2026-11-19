<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Official source-byte identity and modelling gates: NGI PTHA, NOAA SWDI, GEM ATLAS (2026-11-03)

Research only: no original source bytes committed, no Neon write, no licence/science/model admission. This note supplements the canonical discovery entries in landscape/sources-global-atlas-swdi-tsunami-20261103.json.

## NGI / Geoscience Australia global tsunami PTHA 2017

Official record: https://zenodo.org/records/16964551

The publisher lists globalPTHA.txt (approximately 7.3 MB; MD5 d8dd8ad55fe89bd56b455e392387a99e) and README.txt (MD5 f52a37706b789f343b970e51b0076980). The publisher states CC BY 3.0 AU, subject to exact rights and scope review, and expressly warns that the global analysis is not recommended for local-scale risk assessment.

The publisher README describes shapefile attributes whereas the Zenodo file preview is semicolon-delimited text. The description names ari500LZ, but the visible table header names ari500ZL. The new offline runner accepts either naming variant but never treats them as two fields or independent events. The provider preview includes longitudes above 180 degrees, so a 0–360 convention must be considered in any geospatial join.

The fields rate_N represent **annual mean exceedance rates** for N **centimetres** runup; ariN gives a runup height in **metres** for return period N years. Heights of exactly 0.1 or 20 metres are boundary-censored, not exact values. These curves are not event IDs, individual annual event probabilities, synthetic event catalogues, or insured losses.

Offline original-file check:

    python research_runners/ngi_global_ptha_preflight_v0.py /external/provider-original/globalPTHA.txt
    python -m unittest tests.test_ngi_global_ptha_preflight_v0 -v

The preflight compares the full file to the publisher MD5 before parsing; reports SHA-256, row counts, censored values and aggregate scientific anomalies; rejects invalid data; and never prints provider rows or individual coordinates. Exit 0 means only no flagged anomalies, not model-readiness or admission. Five synthetic-only tests passed locally on 2026-11-03. **The actual original file was not downloaded or run through the validator in this session.**

## NOAA NCEI SWDI v2

Official product: https://www.ncei.noaa.gov/products/severe-weather-data-inventory
Official HTTP index: https://www.ncei.noaa.gov/pub/data/swdi/database-csv/v2/

The fetched official index exposes annual and monthly gzip CSV objects including hail-2025.csv.gz, hail-202610.csv.gz and hail-202611.csv.gz. The November file was listed as only 160 bytes at the time of source checking; publication of a filename does not mean an observation month is complete or usable. The source mixes NEXRAD radar signatures, preliminary NWS storm reports and other records, with provider warnings about incomplete spatial/temporal reporting and lack of additional QC. Do not equate radar hail signatures with measured hail damage or zero reports with zero risk.

The Vaisala NLDN lightning layer has separate third-party data-rights implications. Before ingestion, select one bounded historical **non-NLDN** radar CSV and record original SHA-256, provider file vintage, schema, time zone, identifiers and units externally. Reconcile radar signatures with existing NOAA Storm Events lineage; do not count shared underlying NWS records as independent holdout observations.

No SWDI source-data file was downloaded or admitted in this session.

## GEM ATLAS 2.0

Official provider: https://www.globalquakemodel.org/products/atlas

GEM describes ~3.6M globally distributed H3 hazard curve sites and a web/API offering. API and commercial use require a use-case-specific arrangement/subscription; public-good access is also on request. These are GEM mosaic-derived hazard curves, not independent rupture event sets. No provider account or API token was used in this session.

## Next causal steps

1. Obtain the exact tsunami original outside Git, run the MD5-bound preflight, and independently record SHA-256 and scientific QA before any benchmark.
2. Perform a bounded radar-only historical SWDI gzip probe; check source terms and source lineage prior to an adapter.
3. Clarify ATLAS commercial API terms before evaluating it as an actual NextGen component.
