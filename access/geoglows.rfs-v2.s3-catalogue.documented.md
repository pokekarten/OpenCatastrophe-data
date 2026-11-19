<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/geoglows.rfs-v2.s3-catalogue.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `geoglows.rfs-v2.s3-catalogue.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** geoglows.rfs-v2.s3-catalogue.documented

## Source ids

- geoglows.rfs.v2.global-discharge

**Provider:** GEOGLOWS River Forecast System V2 / AWS Open Data

**Interface type:** object_store

**Status:** documented_only

**Documentation url:** <https://training.geoglows.org/rfs/datasets/catalog/>

**Service root:** `null`

**Api version:** RFS V2

## Access scope

- metadata
- catalogue

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- inspect_public_data_catalogue

### Path templates

- /hydrography-global/
- /retrospective/daily.zarr

**Parameter rules:** These paths describe published S3 object families (s3://geoglows-v2/hydrography-global/ and s3://geoglows-v2/retrospective/daily.zarr) and are NONEXECUTABLE evidence only. Do not issue any HTTP, S3 list, HEAD, GET, Zarr metadata or provider SDK requests under this contract. A future source-specific rights clearance must pin exact dataset version/region/bucket/key, bound request volume and prevent caller-controlled endpoints, range amplification, or entire-array scans.

## Response contract

### Expected media types

- text/html

**Format:** Authoritative GEOGLOWS V2 training data catalogue and AWS Open Data Registry descriptive HTML; no Zarr, GeoPackage, NetCDF or telemetry acquisition is permitted by this contract.

**Scientific semantics:** GEOGLOWS retrospective outputs are modeled river discharge, not surveyed observations, flood extent/depth, insured claims or an admitted probabilistic CAT event catalogue. Published daily/hourly histories begin January 1940; 15-day forecasts are updated operationally. The flow unit is volume per time and must be verified per field. Preserve river LINKNO / exact network version, source bucket, Zarr paths, run issue date, ensemble dimensions, forcing, data-vintage and shared lineage with ERA5, ECMWF and GloFAS.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `262144`

**Max sample bytes:** `262144`

**Retry policy:** none

**Rate limit notes:** Public AWS anonymous access is documented, but no OpenCatastrophe source probe, metadata query or download is authorized because exact output licence and S3 terms have not been reconciled.

**Mutability notes:** Forecast buckets change daily and retrospective datasets are refreshed. An eventual consumer must record immutable release identity, retrieval UTC, object ETag if appropriate (not assumed to be a content hash), byte count and SHA-256 per exact stored artifact; Zarr arrays can mutate between queries. The AWS Registry description and catalogue may differ in bucket structure: only exact source-backed paths should be chosen.

## Rights and policy

**Dataset rights status:** conflicting

**Api terms status:** unknown

**Terms url:** <https://training.geoglows.org/rfs/datasets/catalog/>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Direct conflicting published licence statements as of 2026-11-02: official GEOGLOWS RFS V2 training Data Catalog says CC BY-NC-SA 4.0 for the model; AWS Open Data Registry GEOGLOWS Hydrological Model Version 2 listing says CC BY 4.0 for datasets. Model/software terms must not be silently inherited by the exact S3 objects, nor vice versa. Ask provider/data controller to identify the licence for each needed V2 Zarr/GeoPackage/Parquet product, commercial use, model derivatives and redistribution. No commercial ingestion or publication until resolved.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-02

## Evidence urls

- <https://training.geoglows.org/rfs/datasets/catalog/>
- <https://registry.opendata.aws/geoglows-v2/>
- <https://training.geoglows.org/rfs/tutorials/query-data/>

**Notes:** T0 documented-only contract. The published S3 bucket names geoglows-v2 and geoglows-v2-forecasts are not API credentials or live receipt evidence. Record format and scientific role without granting permission for network access, commercial use, model input or Neon syncing. Resolve licensing, then propose a pinned one-river/one-date metadata-first probe with strict shape/unit/time and source-lineage checks; no bulk scan.
