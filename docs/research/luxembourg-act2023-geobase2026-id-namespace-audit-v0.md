<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# ACT2023v2 versus GeoBase 2026: original building-ID namespace audit

**Research only.** Compare two *actual* full national Luxembourg ACT source
identifiers for possible shared keys, without exporting a crosswalk or claiming
the records describe the same physical building.

## Why this is the next causal experiment

The prior genuine ACT2023/EUBUCCO LU00 **250 m × 250 m** pilot produced
**149 ACT rooftop polygons**, **45 EUBUCCO polygons**, **9** unique high-IoU
candidates and **136 ambiguous** ACT-side associations. EUBUCCO's original
government source is ACT's 2013 LoD1 roof-derived product. This high mismatch
cannot justify a geometric or property identity join or inflated exposure.

A newer independent ACT product in the same organisational source family,
BD-L-GeoBase Buildings **2026-10-01**, was verified from its real original
GeoPackage in merged PR #926: **230,353** `Buildings_BU_Building` MultiPolygons,
EPSG:2169, with a field named `BU_BuildingID`. The previously verified
ACT2023v2 roof-extent GeoPackage has **238,189**
`ACT2023v2_Buildings3d_Footprints` polygons and a different field named
`buildingid`. Do the same exact IDs occur in both? An aggregate literal
comparison is a cheaper, safer first question than imputation by geometry.

## Executable original-source comparison

The offline
`research_runners/luxembourg_act_geobase_id_overlap_v0.py` reads both
locally supplied GeoPackages only after verifying the **pre-observed**
full original SHA-256 values:

- ACT2023v2 original GPKG
  `9765b04eaeb9332aa606b8dca44031116588e285553aab061d61037938a002bf`;
  original ZIP
  `a271b1cbcc22ded018f9bab0c150e9f33efa6cb7ebca8cf4dc4bdb1f5d84859a`.
- GeoBase20261001 original GPKG
  `ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676`;
  original ZIP
  `6630f217b39edde5f20f1078bef8a3d6eb4a09337af48394975f45f208bcfed3`
  plus independently published catalogue MD5
  `f414154f993128a63f539aae2644c75a`.

It verifies the exact original table populations, required columns,
GeoPackage application IDs and declared EPSG:2169 MultiPolygon geometry,
then performs an **aggregate-only** cross-file exact textual ID comparison.
Results include null/blank ID counts, duplicate nonblank counts,
integer-versus-text representation counts, IDs shared verbatim as canonical
strings and IDs present on only one side. It never prints, exports or
persists any individual source ID, address, coordinate, shape, row, linked
building or original source file.

A source-side GitHub workflow pins the provider URLs and SHA receipts,
extracts the two GeoPackages only to temporary runner storage, executes
six synthetic safety tests and then the source comparison.

## Original full-source result: exact ID join is **not available**

The actual exact-source GitHub Actions job passed, including its synthetic
tests, both independently pre-observed source ZIP/GPKG digests and the two
full national identifier populations:

https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41310404396

| Observed measure | ACT2023v2 `buildingid` | GeoBase20261001 `BU_BuildingID` |
| --- | ---: | ---: |
| Original features | **238,189** | **230,353** |
| Distinct nonblank full-text IDs | **238,189** | **230,353** |
| Blank/null ID rows | 0 | 0 |
| Duplicate nonblank ID rows | 0 | 0 |
| SQLite-stored text ID rows | **238,189** | **230,353** |
| SQLite-stored integer ID rows | 0 | 0 |

**Exact literal text intersection between the complete two original ID
sets: zero.** All **238,189** ACT roof IDs and **230,353** GeoBase building
IDs are therefore unique to their respective source namespace in this
exact-value test. No crosswalk or per-building IDs were exported.

**Scientific interpretation:** This directly rules out a simple raw
`buildingid = BU_BuildingID` equality join between these two specific
pinned product releases. It does **not** rule out a documented official
ID translation, stable common physical buildings, or geometric overlap.
It also does **not** measure construction/demolition, true exposure, value,
historical change or dataset completeness. These are two different product
entity definitions and dates, both from the same ACT family.

The next useful technical comparison is a **small native-CRS candidate
geometry overlay** of ACT2023 roof polygons versus ACT2026 GeoBase polygons,
with explicit 1:n and n:1 ambiguity/coverage metrics. In parallel search
the official ACT schema/model for an authoritative crosswalk linking
`buildingid`, `BU_BuildingID`, CityGML/GeoBase identifiers; never guess
a string manipulation that makes IDs equal.

## Interpretation guardrails

- A common text value across `buildingid` and `BU_BuildingID` is
  **a namespace hypothesis**. It does not establish that the two names refer
  to the same physical building, that an ID is temporally stable, or that
  different numbers represent different buildings.
- A mismatch is **NOT a new, destroyed or uninsured building**. Rooftop
  shapes, ground/cadastral polygons, generalised source objects,
  acquisition years, identifiers and splitting/merging may all differ.
- Even an exact matching primary ID is **same-ACT-family dependent
  evidence**, not independent external validation.
- A real crosswalk requires audited original ID semantics, feature-level
  geometry/attribute/date quality and a manually adjudicated urban/rural
  sample. No insured TIV, construction age, direct claims or CAT model
  admission is proven by this ID audit.

## Reproduce

```bash
python -m unittest tests.test_luxembourg_act_geobase_id_overlap_v0 -v
python -m research_runners.luxembourg_act_geobase_id_overlap_v0 \
  --act-gpkg /private/exact-act2023v2.gpkg \
  --geobase-gpkg /private/exact-geobase2026.gpkg
```

An original hash match is evidence of previously observed exact bytes,
**not** a cryptographically signed publisher release. Official catalogue
licence labels, scientific admissibility and EUBUCCO ODbL obligations must
be reviewed per product, not assumed from public URL availability.

**Provider URLs:** https://data.public.lu/en/datasets/base-de-donnees-nationale-des-batiments-3d-2023/
and https://data.public.lu/en/datasets/bd-l-geobase/.
