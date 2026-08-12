<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/ec-jrc.ghsl.ghs-obat.r2024a.csv-cyp.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `ec-jrc.ghsl.ghs-obat.r2024a.csv-cyp.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** ec-jrc.ghsl.ghs-obat.r2024a.csv-cyp

## Source ids

- ec-jrc.ghsl.ghs-obat.r2024a

**Provider:** European Commission Joint Research Centre / Global Human Settlement Layer

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://data.jrc.ec.europa.eu/dataset/f41a22f1-5741-4c41-86eb-6384654f6927>

**Service root:** <https://jeodpp.jrc.ec.europa.eu>

**Api version:** GHS-OBAT R2024A footprint CSV / V1-0 / CYP E2020; DOI 10.2905/JRC.9ZB4R6G

## Access scope

- metadata
- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- fetch_cyp_csv_archive

### Path templates

- /ftp/jrc-opendata/GHSL/GHS_OBAT_GLOBE_R2024A/GHS_OBAT_CSV_GLOBE_R2024A/V1-0/GHS_OBAT_CSV_CYP_E2020_R2024A_V1_0.zip

**Parameter rules:** Documentation-only exact-asset contract. No request is authorized yet. A future reviewed worker may request only the repository-controlled Cyprus V1-0 ZIP path above; callers must not supply a country code, filename, directory, host, query string, header, redirect target, alternate representation or release substitution. No directory crawling, wildcard expansion, GeoPackage substitution, CountryStats/GridStats substitution or global mirror is authorized. This Cyprus asset is deliberately chosen as a small EU-relevant representation canary; expanding to another country requires an explicit contract change and fresh rights/size review.

## Response contract

### Expected media types

- application/zip
- application/octet-stream

**Format:** ZIP-packaged footprint-level CSV attribute table for Cyprus (CYP), GHS-OBAT R2024A V1-0. The provider catalogue describes the CSV representation as building-footprint attribute rows split by country and GADM 4.1 administrative subdivisions.

**Scientific semantics:** GHS-OBAT R2024A links attributes to Overture Buildings release 2024-07-22.0 at reference epoch 2020. Footprint-level CSV rows include Overture-linked identifiers/location context and GHSL-derived attributes such as height, compactness/shape factor, functional use, construction-year/age class, area and perimeter; building age is provided in decade classes over 1980-2020. These attributes are derived through vector-raster integration from GHSL R2023/R2024 products and inherit footprint and model completeness/error. They are not cadastral records, surveyed structure characteristics, insured exposure values, vulnerability functions, damage observations or loss measurements. Exact Overture/GADM/GHSL lineage and row identifiers must remain material in any future parser or join.

## Operational constraints

**Timeout seconds:** `60`

**Max probe bytes:** `65536`

**Max sample bytes:** `26214400`

**Retry policy:** none

**Rate limit notes:** JRC exposes the V1-0 archive anonymously and the current directory listing reports the Cyprus ZIP at approximately 16 MiB. This contract authorizes no network request, retry loop, directory crawl or batch acquisition. No repository-specific numeric service budget or durable automated-download entitlement for the JEODPP host was established.

**Mutability notes:** Scientific identity is pinned to GHS-OBAT R2024A, DOI 10.2905/JRC.9ZB4R6G, footprint-level CSV representation, V1-0, CYP, epoch 2020 and the exact filename. The current provider index records this asset as last modified 2024-12-20 and about 16 MiB, while catalogue metadata has been updated later. Any future acquisition must freeze requested/final URL, retrieval UTC, byte count, SHA-256, ZIP member inventory, CSV schema and representation-specific rights evidence. Do not silently substitute GeoPackage, aggregate statistics, another country or a later release.

## Rights and policy

**Dataset rights status:** conflicting

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Current JRC resource-level catalogue metadata labels \`GHS-OBAT_CSV_GLOBE_R2024A\` under the Open Data Commons Open Database License v1.0 (ODbL 1.0) with anonymous/no-limitations access. However, the generic \`GHS_OBAT_CSV_GLOBE_R2024A/copyright.txt\` currently states that copyright and/or sui-generis rights on the dataset are licensed under CC BY 4.0. Because these are materially different database/reuse regimes and the provider has not been shown here to reconcile which notice controls this exact CSV asset, repository rights remain \`conflicting\`. Do not infer commercial/publication/redistribution authority from either notice alone. The GeoPackage footprint resource is also catalogued ODbL, while CountryStats and GridStats are catalogued CC BY 4.0; those representations are outside this contract.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://data.jrc.ec.europa.eu/dataset/f41a22f1-5741-4c41-86eb-6384654f6927>
- <https://doi.org/10.2905/JRC.9ZB4R6G>
- <https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_OBAT_GLOBE_R2024A/GHS_OBAT_CSV_GLOBE_R2024A/V1-0/>
- <https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_OBAT_GLOBE_R2024A/GHS_OBAT_CSV_GLOBE_R2024A/copyright.txt>
- <https://opendatacommons.org/licenses/odbl/1-0/>

**Notes:** Bounded representation-specific access documentation for Issue \#263 / \#173. This is intentionally a single Cyprus CSV canary contract, not a provider-wide GHS-OBAT licence or country-template connector. No provider request, ZIP/CSV byte, parser, Overture join, adapter, workflow, admission promotion or publication decision is introduced. The next required step is independent rights review of the ODbL-vs-CC-BY conflict before any acquisition or persisted derivative is considered.
