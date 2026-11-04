<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg ACT CACLR-address versus GeoBase-building ID namespace challenge

**Date:** 2026-11-04. **Status:** actual-source diagnostic proposed, no
insurance/exposure or data-rights admission.

## Falsifiable question

In the independently SHA-pinned **2026-11-02 ACT BD-Adresses CSV**
(179,768 rows), does source column `id_caclr_bat` or `id_geoportail`
contain *exactly the same text* as any `BU_BuildingID` in the
**2026-10-01 ACT GeoBase Buildings** original GeoPackage (230,353 rows)?
And how many original address rows share address-level IDs?

A string intersection test is low-cost and useful to **reject unsupported
simple equality joins**. It does not establish namespace equivalence,
the same physical building, construction/demolition, one risk per address,
an insurer interest, or independent geographic accuracy, even if text overlaps.

## Previously independently observed original source objects

- [ACT BD-Adresses official publisher](https://data.public.lu/en/datasets/adresses-georeferencees-bd-adresses/) — CSV
  `20261102-033122/addresses.csv`, SHA-256
  `f163ed856200eedd8b501da2d7787e01ee373be1a55a4d79abcf57c96982a99c`,
  observed **179,768** rows, full original byte and metadata test
  [PR #1256](https://github.com/pokekarten/OpenCatastrophe-data/pull/1256).
  Prior full-source quality gate measured **584 repeated CACLR building ID rows**,
  zero missing IDs, and ~0.002 metre internal EPSG2169-to-4326 discrepancy.
- [ACT BD-L-GeoBase official publisher](https://data.public.lu/en/datasets/bd-l-geobase/) — Buildings ZIP
  `20261001-010523/buildings-20261001.zip`, SHA-256
  `6630f217b39edde5f20f1078bef8a3d6eb4a09337af48394975f45f208bcfed3`,
  original Buildings GeoPackage SHA-256
  `ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676`,
  **230,353** unique original `BU_BuildingID` values.
- Prior **ACT2023v2 `buildingid` ↔ GeoBase2026 `BU_BuildingID`**
  full-national exact-text ID intersection was **zero**; that source pairing
  is separate from the new CACLR-versus-GeoBase question.

## Implementation and no-leak receipt

`research_runners/lu_caclr_geobase_original_id_namespace_v0.py`
reuses the full source-byte verifier
`lu_bd_adresses_original_csv_quality_v0.py` and the reviewed
`luxembourg_geobase_2026_id_quality_v0.py` original ZIP/GPKG archive
safety receipts. Both exact originals are downloaded into temporary
GitHub runner storage with fixed source URLs, size budgets and
cryptographic SHA checks; GeoBase is reopened **read-only**.
No individual ID, address, geometry, matched pair, or original source byte
is returned, stored in Git or uploaded. Output includes only:

- Rows, empty/nonempty/unique and duplicate-excess counts for
  `id_caclr_bat`, `id_geoportail` and `BU_BuildingID`.
- The count of distinct **literal shared strings** and number of rows
  represented by shared values, with no values or mapping.
- Explicit `id_namespace_equivalence_proven=false`,
  `common_string_proves_same_physical_building=false`,
  `rights_review_approved=false` and
  `scientific_model_input_admitted=false`.

The isolated standalone workflow
`.github/workflows/luxembourg-caclr-geobase-original-id-namespace.yml`
runs deterministic synthetic regressions and this exact-source worker.
This does not edit the main CI workflow or the currently open
[PR #1272](https://github.com/pokekarten/OpenCatastrophe-data/pull/1272)
on two bounded building-geometry sites.

## Interpretation guardrails

If overlap is **zero**, a direct equality join between these pinned
releases is rejected. If overlap is positive, same-text overlap is a
**namespace hypothesis**, not an authoritative crosswalk.
ACT address points can be parcel or largest-building centroids,
are not guaranteed entrances, and multiple addresses may share one
original building feature.

Do not create insurance exposure rows, deduplicate actual buildings,
assign TIV, infer construction or demolition, or promote to CAT model inputs.
Independent, adjudicated truth and source-rights review remain required.

**Execution status:** this note records the experiment contract only.
An actual observed overlap count must be appended **only after**
the original-source GitHub job completes successfully at exact head.
