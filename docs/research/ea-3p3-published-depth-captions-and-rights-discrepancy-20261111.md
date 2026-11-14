<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Environment Agency 3.3% AEP river/sea flood: published depth captions vs feature semantics

**Research status 2026-11-11:** The official publisher description
confirms seven human-readable depth-band captions, while the OGC API Features
queryables schema confirms `depth_band: string`. **New subsequent
read-only, limit=1 original-provider feature probes verified the eight
actual field labels and four `flood_source` labels** documented below.
A single original MultiPolygon was transiently returned per bounded query;
**no original geometries, source feature bytes, building exposures, ZIPs or
claims were committed to the repository**. The real label vocabulary is
research evidence, not a licence/scientific/admission approval or a
property-depth measurement.

## Two exact publisher descriptions

- [Defra Environment Agency present-day 3.3% defended flood-depth catalogue](https://www.data.gov.uk/dataset/2b1dc7a4-ff9f-42fd-9971-11638eabf814/rivers-and-sea-3-3-defended-flood-risk-depths-present-day).
- [Defra Environment Agency climate-change 3.3% defended flood-depth catalogue](https://www.data.gov.uk/dataset/9d5e56d5-7713-42a1-890f-3d0a3e895cd5/rivers-and-sea-3-3-defended-flood-risk-depths-climate-change).

Both describe **3.3% annual exceedance probability** (approximately 1 in 30),
**defended-only river and sea** hazards and these seven **published prose
captions**, in millimetres:

| Published caption text | Nominal lower bound (mm) | Nominal upper bound (mm) | Interpretation |
| --- | ---: | ---: | --- |
| `Up to 150mm` | *unknown* | 150 | Does not establish dry depth = 0 or a measured lower boundary |
| `150 – 300mm` | 150 | 300 | Interval caption only |
| `300 – 600mm` | 300 | 600 | Interval caption only |
| `600 – 900mm` | 600 | 900 | Interval caption only |
| `900 – 1200mm` | 900 | 1200 | Interval caption only |
| `1200 – 2300mm` | 1200 | 2300 | Interval caption only |
| `Over 2300mm` | 2300 | *open* | No finite upper bound |
| `Unavailable` | *missing* | *missing* | Incomplete national-model support; **never zero-depth** |

The descriptions do not settle the exact handling of endpoints (whether a
boundary is inclusive or exclusive). Do not choose an arbitrary midpoint,
representative numerical depth, per-building depth or vulnerability ratio.

The previously obtained original OGC API JSON schema for the present-day
3.3% layer identifies fields `depth_band:string`,
`flood_source:string`, `shape_length:number`, `shape_area:number`,
and `shape:Geometry`, with storage CRS EPSG:27700 and extent CRS84.
See [original OGC API receipt and schema audit](ea-river-3p3-present-ogc-metadata-proof-20261110.md).
The actual recorded lexical values of the `depth_band` field have **not**
been observed and must not be guessed from the description's captions.

## Executable bounded, synthetic-only check

The new offline `scripts/ea_flood_published_depth_bands_v0.py`
requires **one exact published-caption string**. It returns only a
descriptive nominal mm interval with explicit non-admission flags. For
example:

```sh
python scripts/ea_flood_published_depth_bands_v0.py --published-caption "150 – 300mm"
python scripts/ea_flood_published_depth_bands_v0.py --published-caption Unavailable
```

Every alternative spelling, unobserved feature value, non-string input and
invented dry-depth label fails closed. The 8 synthetic-only unit tests
`tests/test_ea_flood_published_depth_bands_v0.py` cover all seven classes,
missingness, unknown field strings and zero/damage/admission safeguards.
This is intentionally **not** a feature adapter or licensed data-ingestion
pipeline. Once a permitted original source feature sample and exact product
field documentation are verified, add a *separate* original-label mapping
with explicit raw-value evidence rather than making this helper permissive.

## Licence metadata discrepancy requiring product-level review

The official CKAN `package_show` catalogue bodies for both 3.3% products
show `private=false` and a record in `extras` with
`licence=["Open Government Licence"]`, but the top-level
`license_id=null` and `isopen=false`. The legacy CKAN dataset web
representation can therefore display **"No Licence Provided"**, while the
National Data Library frontend surfaces a licence-details link and the
Defra product overview gives an Environment Agency attribution statement.
This is **a metadata representation discrepancy, not proof that the actual
licensed layer may be redistributed without restrictions**, and it is also
not proof that the OGL metadata statement is invalid.

The [official Defra source product overview](https://environment.data.gov.uk/defra/767c96e6-b149-4744-9d4d-34b32f6c0e1b)
states access is subject to the licence identified and gives
`© Environment Agency copyright and/or database right 2026`
attribution. Before exact asset download, data redistribution, automated
commercial service use, and source admission, verify the *specific original
asset* licence, rights of contributors, attribution and service conditions.
Keep both source candidates `rights_review_status=not_reviewed`,
`scientific_review_status=not_reviewed`,
`admission_status=not_admitted`.

## Original present-day OGC Feature label evidence (2026-11-11)

A deliberately bounded, read-only OGC API request to the original
[EA 3.3% defended present-day feature collection](https://environment.data.gov.uk/geoservices/datasets/767c96e6-b149-4744-9d4d-34b32f6c0e1b/ogc/features/v1/collections/Rivers_1in30_Sea_1in30_defended_depths)
used `limit=1`, `filter-lang=cql2-text` and a fixed, single-value
`depth_band` equality filter (one query used a suffix LIKE to discover
`<150mm`). The service returned a single limited original GeoJSON feature
with the requested field value and a server-reported `numberMatched`
for that class. **These are counts of polygon features, not land area,
exposure, flooded buildings, events or modelled losses.** The returned
geometry bytes were not copied to the codebase or audit logs.

| Verified original `depth_band` value | Public caption | Publisher-reported polygon feature count |
| --- | --- | ---: |
| `<150mm` | Up to 150mm | 52,290 |
| `150-300mm` | 150 – 300mm | 51,936 |
| `300-600mm` | 300 – 600mm | 51,397 |
| `600-900mm` | 600 – 900mm | 47,971 |
| `900-1200mm` | 900 – 1200mm | 41,601 |
| `1200-2300mm` | 1200 – 2300mm | 33,712 |
| `>2300mm` | Over 2300mm | 13,497 |
| `unavailable` | Unavailable | 55,358 |
| **Total for this service snapshot** | | **347,762** |

For `depth_band`, the eight individual filters sum **exactly** to
the unfiltered service's `numberMatched=347762` at this observation
time. Direct `depth_band='Unavailable'` (uppercase) and
`depth_band IS NULL` returned no hits. The missing code observed
in actual features is lowercase **`unavailable`**, not a numeric 0
or proof a polygon is dry.

For `flood_source`, an additional bounded source-label discovery and
four exact equality checks independently returned:

| Actual `flood_source` string | Polygon feature count |
| --- | ---: |
| `river` | 267,810 |
| `sea` | 25,604 |
| `rivers and sea` | 7,717 |
| `unavailable` | 46,631 |
| **Total** | **347,762** |

`depth_band=unavailable` and `flood_source=unavailable` have
**different counts**; they are not interchangeable missingness flags.
The source-category totals also sum to the same 347,762 polygon count,
but no complete joint cross-tabulation, property polygon overlap, or
geometric coverage has been established. Counts are a time-dependent
publisher query result, not a stable source-release manifest or spatial
risk weight. Because the provider returns geometries even when
`skipGeometry=true` was requested, preserve original-byte limits and
**do not use polygon count as a substitute for area-weighted exposure**.

### Implemented fail-closed actual-feature QA

`scripts/ea_flood_original_feature_label_qa_v0.py` accepts exactly
**one independently saved bounded original FeatureCollection response** and
returns only whitelisted `depth_band`/`flood_source` labels, nominal
millimetre *interval boundaries*, byte count and SHA-256. It checks the
expected collection's feature-ID prefix and known four properties; it never
reports IDs, coordinates, geometry, depth midpoints, loss ratios, or building
hits, nor does it execute a provider call. Unrecognized values and extra
features fail closed; all commercial-rights, physical-depth, shape-unit,
geometry-CRS and model-admission flags remain negative. Synthetic-only
unit tests exercise the observed vocabulary and malformed payload cases.

The *separate* `scripts/ea_flood_published_depth_bands_v0.py`
continues to recognise the **prose captions only**. Never feed a provider
feature string directly to that caption helper; real values such as
`>2300mm` and `unavailable` deliberately differ from the public
labels.

### Next causal validation step

Review the official product description's exact interval-edge rules and
the rights/attribution specific to this feature service, then repeat
a **spatially bounded, independently versioned** source sample with
verified feature-ID provenance and geometry CRS. The current original
samples do not establish the property's actual ground-level inundation,
physical flood-exposure coverage, or vulnerability. Before joining
buildings, retain `unavailable` as missing and perform location-level
CRS, polygon topology and hazard lineage checks. Do not infer
event-frequency series, OEP/AEP or loss from class-count totals.
