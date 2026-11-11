<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Environment Agency 3.3% AEP river/sea flood: published depth captions vs feature semantics

**Research status 2026-11-11:** The dataset's *published description*
now independently confirms seven depth-band captions; the already observed
OGC API Features **queryables schema** confirms a field named
`depth_band` with JSON type `string`. **There is not yet a verified
mapping from actual feature field values to those published captions.**
No feature rows, geometry, ZIP, building exposure, risk estimate, or damage
function has been ingested. This evidence does not change rights/science
review or source admission.

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

### Next causal validation step

Obtain and independently pin **one** legally permitted, fixed small
original feature record and relevant producer attribute/dictionary
documentation; verify actual `depth_band` lexical values, explicit
`Unavailable` semantics, `flood_source` categories, coordinate
representation, and interval conventions. Do not translate these captions
into insured building depth, event frequencies or loss until validated.
