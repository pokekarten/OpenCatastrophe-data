<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# PLATEAU REST / GraphQL release cross-check (offline-only, 2026-11-01)

## Why this step exists

One municipal CityGML release can be listed through two official PLATEAU interfaces, REST `GET /datacatalog/plateau-datasets` and GraphQL `POST /datacatalog/graphql`, with a city/year filter. Each interface is experimental; neither a URL nor a matching catalogue response proves that exact ZIP bytes were acquired or that commercial data use and redistribution are licensed. The REST and GraphQL views can derive from a **shared upstream publisher database**, so even exact agreement **is not independent scientific verification** of coverage, measured building heights or building identity.

Primary provider documentation:
- REST [full catalogue](https://docs.plateauview.mlit.go.jp/api/rest/operations/datacatalogplateau-datasets/).
- GraphQL [CityGMLDataset schema and filter](https://docs.plateauview.mlit.go.jp/api/graphql/schema/).
- [Stable fiscal-year composite redirect](https://docs.plateauview.mlit.go.jp/api/rest/operations/datacatalogcitygmlspeccitygmlzip/).
- [Experimental API limitations](https://docs.plateauview.mlit.go.jp/api/).
- [CityGML catalogue semantics and optional file sizes](https://docs.plateauview.mlit.go.jp/datasets/citygml/).

## Executable local operation

```bash
python research_runners/plateau_metadata_crosscheck_v0.py \
  --rest-input /path/to/lawfully-supplied-rest-catalogue.json \
  --graphql-input /path/to/lawfully-supplied-city-year-graphql.json
```

The two inputs must already exist as separately lawfully supplied **local regular files**. The runner performs **no HTTP requests**, credentials, scraping, downloads or provider rights decisions. It reuses the existing bounded, symlink/FIFO-safe local file reader (8 MiB REST, 64 KiB GraphQL) and both existing strict structural preflight validators. The exact target remains **Shinjuku, Japan, municipality 13104, fiscal release 2024**; existence of this specific live release is NOT established. No `latest` alias is allowed.

It fails closed unless the two views declare the same municipality, fiscal year, registration year, set of feature types including `bldg`, **exact original CMS ZIP URL**, and **the same present fixed-city/year composite URL**. A difference in feature list ordering alone is ignored. Absent/mismatched fixed release links block the cross-check. Provider URLs, GraphQL native IDs and raw file sizes are not printed.

On successful *synthetic* inputs, output consists solely of the structural consistency verdict, bounded receipt hashes/byte counts, source/year/registration-year metadata, which **REST CMS original ZIP size metadata is known**, explicit flags that the GraphQL optional size field was **not selected**, G-Spatial file sizes are not comparable to CMS sizes, the source may be shared upstream, and **false** for independent building verification, provider original bytes verified, rights review, model admission and network acquisition. Neither the hashes nor a successful pair means the original ZIP exists or can lawfully be used.

## Admission gates remain blocked

The static Japan contracts remain `document_only` for PLATEAU REST/GraphQL, `blocked_registration` for GSI, and `restricted_by_terms` for J-SHIS. Zero Japanese source bytes are committed, no live API request is authorized by this comparison, no geospatial join is created, and no insured exposures or damage rates are inferred.

A next scientific step requires a separately reviewed endpoint-specific API/rights decision, **actual** bounded original catalogue response receipts, an independently identified provider-licensed CityGML release, verified raw ZIP byte size and SHA-256, versioned CRS and source identity, then independent holdout geometry comparison before model admission.
