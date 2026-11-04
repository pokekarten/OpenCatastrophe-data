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

## Executed full-original result (2026-11-04)

The pinned [GitHub original-source workflow 41884857865](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41884857865)
completed successfully at tested code head `9aad5a4baec73aa8edda1bca968335f2465c4bcd`.
**12/12 synthetic anti-false-join tests passed**, then the exact original
ACT BD-Adresses CSV and ACT GeoBase Buildings ZIP/GPKG were independently
SHA-verified and compared in temporary runner storage.

| Measured original national identifier population | Distinct nonblank strings | Blank rows | Duplicate-excess rows | Maximum rows per original ID |
| --- | ---: | ---: | ---: | ---: |
| BD-Adresses `id_caclr_bat` (179,768 rows) | **179,184** | **0** | **584** | **5** |
| BD-Adresses `id_geoportail` (179,768 rows) | **179,768** | **0** | **0** | **1** |
| GeoBase Buildings `BU_BuildingID` (230,353 rows) | **230,353** | **0** | **0** | **1** |

**Literal exact text intersection between all 179,184 distinct
`id_caclr_bat` and all 230,353 `BU_BuildingID`: 0.**

**Literal exact text intersection between all 179,768 distinct
`id_geoportail` and all 230,353 `BU_BuildingID`: 0.**

All three nonblank original populations were fully accounted for, no
surrounding-whitespace anomalies were observed, and the outputs included
`id_namespace_equivalence_proven=false` and
`scientific_model_input_admitted=false`. These are **original-source
measurements**, not estimates or sampled counts.

**Conclusion specific to pinned releases:** the simple raw equality join
between BD-Adresses' either address ID and GeoBase's building ID **has no
matching rows**. Do **not** retry by stripping an arbitrary prefix, converting
numeric strings or reformatting IDs without an independently documented
namespace mapping. The zero overlap does not mean there are no common real
buildings, uninsured buildings, or an absence of physical correspondence.

## Primary ACT schema documentation

The ACT's official
[BD-L-GeoBase dataset contents description, version 1.0 (2024)](https://download.data.public.lu/resources/bd-l-geobase/20240925-163507/contentsdescription-bd-l-geobase-v1.pdf)
states:
- **Section 4.1**: the *Addresses* theme is drawn from the CACLR register;
  `AD_AddressID` is the unique GeoBase address identifier, and
  `AlternativeIdentifier` is an identifier from CACLR.
- **Section 4.4**: `BU_BuildingID` is a **unique GeoBase building identifier**,
  with footprints sourced from Bati3DACT, Bati3DVDL, cadastral PCN,
  official mensuration (MO) or orthophotos.

This documentation distinguishes the **Address** and **Building**
feature layers and identifies their separate key roles. It does **not**
declare that BD-Adresses CSV `id_caclr_bat` or `id_geoportail`
equals GeoBase `BU_BuildingID`. The original 2026 source QA above
independently rejects such a verbatim equality hypothesis for the actual
two frozen releases. To investigate an authoritative address crosswalk,
first inspect and pin the official GeoBase **Addresses theme**, particularly
`AD_AddressID` and `AlternativeIdentifier`, instead of equating
addresses to building objects; verify its 2026 revision and source dependencies.

## Recommendation

Keep both source namespaces separate and use the already validated small
address-to-footprint point containment proof in merged PR #1272 as a
**geometric candidate relationship**. For proper insurer exposure units,
record one-to-many and many-to-one address-building mappings, area/vintage,
source-family dependence and independent adjudication. No source admission
or production CAT calculation is authorized here.
