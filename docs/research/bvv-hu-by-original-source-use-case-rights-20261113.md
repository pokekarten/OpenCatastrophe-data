<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Bavaria HU-BY Oberbayern: licensed original SHP research proof and exact use-case gates (2026-11-13)

## Why this candidate matters

Canonical source ID: `de.bayern.hausumringe` (official Bayerische
Vermessungsverwaltung/LDBV **HU-BY**, not the German federal
BKG/AdV `HU-DE` product).

The [official product description](https://www.ldbv.bayern.de/produkte/liegenschaftsinformationen/hausumringe.html)
identifies georeferenced cadastral-derived 2D building outline polygons
used as an authoritative basis for geospatial analyses and maps.
The [BVV OpenData terms](https://www.geodaten.bayern.de/odd/m/3/html/nutzungsbedingungen.html)
and [FAQ](https://www.geodaten.bayern.de/odd/m/3/html/faq.html)
explicitly permit **commercial use, redistribution and modification
under CC BY 4.0**, provided the rights holder is attributed, a licence
link provided and modifications disclosed.

Required credit:

> Bayerische Vermessungsverwaltung – www.geodaten.bayern.de

The CC BY 4.0 data-product licence is **not** a model suitability
approval, an authorization for an unconstrained provider service request
rate, or a grant applying to the separately licensed `HU-DE`,
`ALKIS` parcel service and other geographic products.

## Native original source proof already completed

The separate trusted `main` source workflow
[43471636096](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43471636096)
**succeeded**, and its derived original-content research receipt is
private insurance Neon **sample #94**. This is a verified original
source-member observation (not an estimate invented from metadata).
The underlying main repository documents the original
full-member/ROI streaming proof in
[`docs/research/bvv-original-full-shp-ghsl-e2020-roi-stream-20261113.md`](bvv-original-full-shp-ghsl-e2020-roi-stream-20261113.md).

| Independently evidenced attribute | Scoped fact |
| --- | --- |
| Exact source | Official `091_Oberbayern_Hausumringe.zip` |
| Original full ZIP object | 174,299,765 bytes, **full ZIP hash not verified** |
| Bounded original transfer | Exactly 20 verified source HTTP 206 segments, at most 8 MiB each |
| Full compressed original `hausumringe.shp` member | 166,172,236 bytes |
| Decoded native `hausumringe.shp` member | 501,212,696 bytes |
| Original full native polygon records | **2,703,736** |
| Native SHP member SHA-256 | `977e35aa7764564be115776ea56f78ef228d3cc79939b28f08c6cbe96e2e7a0c` |
| Compressed member SHA-256 | `22364ef161d6411e2010be590d791508242ec6d36ffc3a314833cedcd6afc615` |
| Source native geometry CRS | ETRS89 / UTM zone 32N, EPSG:25832 |
| Raw geometry or original source bytes retained in Neon/Git? | **No** |

The full member's original CRC32 and record chain were also verified;
that does **not** establish a checksum for the entire original ZIP
archive or every separate member, nor a point-in-time census of
insured buildings.

The actual research compares source-era cadastral geometry to a
**different-vintage GHSL E2020** 32×32 analysis window. The original
ROI included 417,565 intersecting polygon records and 204 bounded
union batches. These numbers represent **polygon records and
geometric overlap**, not unique insurance-covered buildings, building
reconstruction values, policy TIV or an independent proof of 2020
cadastral truth. Preserve the geographic and temporal mismatch.

## Seven explicit private use-case rights records

As of 2026-11-13, the separate insurance research Neon
`research.source_usage_rights_v0` now has exactly seven scoped
entries for **this original Oberbayern HU-BY product**. All seven
specify `scientific_model_admission=false` and
`original_asset_admitted=false`.

| Use case | Rights decision | Scope and required boundary |
| --- | --- | --- |
| Commercial research/data-product CAT analysis | **Allowed legally** | CC BY 4.0 data use with credit; **not** risk calibration or model admission |
| Private internal research | **Allowed** | Source-bound geometry/coverage diagnostics with citation |
| Private Neon source metadata | **Allowed** | Hashes, byte lengths, CRS and abstract ROI statistics, no coordinates/raw bytes |
| Private Neon source sample | **Conditional** | Anonymized derived aggregates only, no original protected properties or historical 2020 assumption |
| Automated source access | **Conditional** | Product is openly licensed, but server request cadence, unlimited mirror/bulk service policy and transport need separate source-specific review |
| External original raw redistribution | **Conditional in this pipeline** | CC BY 4.0 may permit licensed redistribution with attribution; **public OpenCatastrophe-data remains source-reference-only, never an original SHP/ZIP mirror** |
| Publication of derived comparisons | **Conditional** | Attribution, licence/link/change notice and correct version/units; no invented insurer exposure figures |

The official terms themselves allow redistribution and commercial use;
the conditional decision for publishing raw material expresses a
**separate project-pipeline handling policy**, not a false claim that
CC BY prohibits redistribution. Likewise the programme's `unknown`
automation flag is a missing *service-specific* cadence review, not a
claim that the original dataset licence is unknown.

## New machine-readable source-access gate

This PR adds `access/de.bayern.hausumringe.json` and its exactly
generated Markdown projection. The contract intentionally remains
**`documented_only`**, with `probe_contract.mode=none`,
`implementation_decision=document_only`,
`dataset_rights_status=verified`,
`api_terms_status=separate_unreviewed` and
`commercial_automation_status=unknown`.
This preserves the completed source proof without accidentally
authorizing a second 166 MB source download or extrapolating
provider-bulk-service rights from a dataset licence.

```sh
python -m unittest tests.test_bvv_hu_by_oberbayern_access_rights_v0 -v
python -m scripts.validate_source_access access/de.bayern.hausumringe.json
```

The tests and ordinary CI are **offline**, without source network,
credentials, building geometry, database writes or source-model
status mutation. The full-membership trusted GHSL/geometry workflow
is separate, already executed, and this new contract does not replay it.

**Before CAT portfolio admission:** independently establish the
cadastral release/survey vintage, full archive and current-file
identity, geometric building grouping and semantic attributes,
cadastral-to-exposure coverage, building age/use/height,
replacement-cost/TIV calibration and insurer-specific source
permission. A source-complete 2D polygon record is not an actual
individual insured building record.
