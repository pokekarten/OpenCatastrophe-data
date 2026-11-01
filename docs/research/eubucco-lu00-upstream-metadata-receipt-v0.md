<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EUBUCCO v0.2: Luxembourg original upstream-source workbook

**Research only.** This independent source-lineage check closes a different
gap from PR #919, which downloads the LU00 buildings themselves.

## Why this matters

The original EUBUCCO v0.2 LU00 Parquet profile identifies individual
`geometry_source` values such as `gov-*`, `osm` and `msft`. A
government-labelled feature does not establish **which government data
product/release** contributed it, what original licence and vintage applies,
or whether those footprints are independent of the newer ACT2023v2 Luxembourg
roof extents. Treating both products as independent building-ground-truth
without source metadata would inflate validation confidence.

Official EUBUCCO documentation identifies `input-datasets-metadata.xlsx`
as the source-dataset reference workbook (name, original owner, licence,
access date, original data access and integration details). The official v0.2
data portal provides its exact direct S3 download:

https://s3.eubucco.com/eubucco/v0.2/additional/input-datasets-metadata.xlsx

Official pages:
- https://eubucco.com/data/download/v0.2
- https://docs.eubucco.com/v0.2/data-format/metadata/
- https://docs.eubucco.com/v0.2/license/

## Implemented reproducible check

`research_runners/eubucco_lu_original_metadata_xlsx_v0.py` is an
offline read-only XLSX ZIP/XML parser using only Python's standard library.
It deliberately does **not** parse the dataset's individual buildings. It
checks the downloaded workbook's exact SHA-256, ZIP traversal / symlinks /
external link safety, compressed and expanded size budgets, worksheet and
shared-string structures and only prints **public source-metadata rows
mentioning Luxembourg or LU**.

```bash
python -m unittest tests.test_eubucco_lu_original_metadata_xlsx_v0 -v
python -m research_runners.eubucco_lu_original_metadata_xlsx_v0 \
  --original-xlsx /private/official-input-datasets-metadata.xlsx
```

The first original-file run **computes** a byte-identifying SHA-256. It
does not pretend that the first computed value is a prior independent
publisher checksum. Subsequent retrievals should use
`--expected-sha256` with that frozen value. A provider revision must
block or be explicitly reviewed, never silently become equivalent to the
previous workbook.

A dedicated, source-specific GitHub Action fetches just this small
provider-hosted metadata workbook into the temporary runner, checks
synthetic fixtures and logs only the relevant source-metadata summary.
No original XLSX, building geometry, individual IDs or insurance records
are committed, uploaded or placed in insurance Neon.

## Verified **original** EUBUCCO upstream metadata receipt, 2026-11-01

First official retrieval succeeded in GitHub Actions:
https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41308007003

- Exact provider original workbook: **39,473 bytes**, SHA-256
  `c505cdaa04a296a057f046ccc95c5cfdff277f6fb847f8b725fd85007cff2e0e`.
- One XML worksheet contains **990 data/header rows**; one public source
  metadata row explicitly matches Luxembourg, at worksheet row 51.
- The original metadata source identifier (column A) is
  **`gov-luxembourg`**, exactly the government-family source label implied
  by EUBUCCO LU00's 144,088 government-labelled original geometries.
- The named original upstream provider product (column E) is
  **`Bâtiments 3D (LOD 1 – Level of Detail 1)`**.
- Original upstream dataset year (column G) contains **2013**, while
  the publisher historical description explicitly ties the survey to 2013
  aerial/topographical measurements. Do not treat other Excel numeric date
  serials in the original row as a known ISO date without header interpretation.
- Original source URL in EUBUCCO metadata:
  https://data.public.lu/en/datasets/batiments-3d-lod-1-level-of-detail-1-1/
  (the portal has since introduced an explicit `2013` title in its
  discoverable canonical page).
- Original publisher: **Administration du cadastre et de la topographie
  du Grand-Duché de Luxembourg**; source label **CC0-1.0**, declared
  **EPSG:2169**, file format **GML**.
- Independent current publisher catalogue:
  https://data.public.lu/en/datasets/batiments-3d-2013-lod-1-level-of-detail-1/
  confirms BD-TOPO-L / **2013** aerial-image photogrammetric origins,
  coarse LOD1 building-block segmentation, EPSG:2169, CC0 and a
  **2019-05-28** file publication. These are the source dataset's stated
  properties, not proof that a particular original file revision was
  ingested by EUBUCCO.
- This EUBUCCO upstream original is **not ACT2023v2**; however both are
  ACT-derived photogrammetry/topography family products. Their agreement
  cannot serve as an independent geometry-validation holdout, and observed
  differences cannot be classified as newly constructed/demolished buildings
  until changes in vintages, roof-vs-block segmentation, spatial coverage,
  and original identifier namespace are controlled.

The first retrieval computed its SHA-256; **it was not pre-pinned**.
The subsequent exact-URL workflow now requires this frozen SHA before it
reproduces the same result. Both original workbook bytes and building
geometries remain outside Git and Neon.

### Practical implications

1. Preserve `gov-luxembourg` as provenance family `ACT2013-LOD1`,
   separately from the later `ACT2023v2-BATI3D` resource.
2. Reconcile 2013 building-block LOD1 geometry to the 2023 *roof extent*
   footprint **as a temporal/segmentation comparison**, not a one-to-one
   independently confirmed building identity. A 2013 LOD1 block can
   correspond to multiple newer roofs without true construction.
3. Independently resolve both EPSG:2169 native coordinate order and
   precise original EUBUCCO input revision; do not assume EUBUCCO and ACT
   publication snapshots are contemporaneous.
4. Never use these origin/coverage counts to invent 2013/2023 insurance
   exposure or attribute a 2013/2023 difference to catastrophe event loss.

## Validation limits and next causal decision

The workbook may describe several Luxembourg upstream sources or none
in a simple country field; distinguish the actual original dataset name,
the government provenance label (including provider-specific `gov-*`
codes), retrieval date, licence and vintage. An original source older than
ACT2023v2 can be a useful temporal cross-check, but **may share cadastral
lineage**. Agreement cannot be counted as two independent observations
without an explicit upstream-source crosswalk.

This script has **no authority to admit** source files or CAT model inputs.
Neither a common building polygon nor its government label proves building
identity, insured replacement value, construction age or commercial
redistribution rights.
