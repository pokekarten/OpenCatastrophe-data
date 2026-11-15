<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg: supplemental original official buildings source (BD-L-GeoBase 2026)

**Date:** 2026-11-01. **Status:** source discovery + exact-resource metadata preflight; not admitted as CAT model input or independently verified building truth.

## Primary original asset and why it matters

Luxembourg Administration du Cadastre et de la Topographie (ACT) publishes
**BD-L-GeoBase**, which includes themed addresses, buildings, cadastral parcels,
transport, elevation and administrative boundaries. The official catalogue
labels the product CC0 and EPSG:2169. Its **October 1, 2026 Buildings-theme
GeoPackage ZIP** is much smaller than the circa 955.8 MB all-theme package.

- Catalogue: https://data.public.lu/en/datasets/bd-l-geobase/
- Exact original resource: https://data.public.lu/en/datasets/r/e93c27f8-1908-442b-9dc4-d10a117cf315
- Original ZIP: https://download.data.public.lu/resources/bd-l-geobase/20261001-010523/buildings-20261001.zip
- Catalogue date: 2026-10-01; listed ZIP size **37.4 MB**, exact catalogue MD5 `f414154f993128a63f539aae2644c75a`.
- Claim: building representations in official GeoBase. **Actual feature layers, individual object meaning, ID stability, footprint relation to ACT2023v2 roof extents and source dates are not assumed.**
- Related, already independently retrieved original sources: ACT2013 CityGML LoD1 `d60f0efd2d66f0a446cd2216be1b40e97ac4f15edfc5e3c8a3aaff390c326fa1`; ACT2023v2 roof GeoPackage `9765b04eaeb9332aa606b8dca44031116588e285553aab061d61037938a002bf`; EUBUCCO LU00 v0.2 original Parquet `d1e554de9db0b1f747575426ebb950ef96bb8b2956657554b5ff2998a91abe8c`.

## Implemented exact-source safety gate

`research_runners/luxembourg_geobase_buildings_20261001_v0.py` validates only
an **already acquired** ZIP against the above publisher-listed MD5 and emits
a new exact SHA-256 receipt. It bounds ZIP size and expansion, rejects unsafe
paths/links/encryption/duplicate names, CRC-checks members, extracts no permanent
bytes and reads only GeoPackage table metadata: layer name, geometry type,
EPSG declaration, field *names* and aggregate feature counts. No source
building IDs, coordinates, person details, policies or individual feature values
are logged or written to Git/Neon.

```bash
python -m unittest tests.test_luxembourg_geobase_buildings_20261001_v0 -v
python -m research_runners.luxembourg_geobase_buildings_20261001_v0 \
  --source-zip /private/BD-L-GeoBase/buildings-20261001.zip
```

The single-source GitHub Action, triggered only for the named source gate or
manually, downloads just this specific **37.4 MB** original Buildings-theme
resource, never the all-theme 955 MB file. All original files stay in the
temporary runner and are discarded; only aggregate schema metadata is logged.
**Publisher catalogue MD5 is not a strong cryptographic authenticity proof**;
the SHA-256 from the acquired bytes is an observed content receipt and must be
pinned for follow-up work. Any source file or schema drift fails closed.

## Concrete follow-on comparisons

1. **ACT 2026 GeoBase vs ACT 2023 roof extents**: compare actual feature dates,
   source primary ID namespaces, geographic coverage and segmented ground/roof
   definitions. This is **same-ACT-family correlated evidence**, not
   independent spatial validation. Do not interpret unmatched geometry as a
   newly built or demolished property without historical controls.
2. **ACT 2026 GeoBase vs EUBUCCO v0.2**: source-specific 2013 LoD1 government
   lineage, OSM/MSFT alternatives and modelled heights must remain separated.
   Never turn EUBUCCO modelled floors into government-observed floors.
3. **ACT 2026 with georeferenced addresses / parcels**: separately freeze the
   official 2026 address and cadastre resources and check one-to-many address
   and building relationships, access rules and privacy. A parcel is not
   equal to a building, an address is not evidence of insured property,
   and parcel owner data are not needed.
4. **LiDAR 2024** (https://data.public.lu/en/datasets/lidar-2024-releve-3d-du-territoire-luxembourgeois/):
   start with the tiny published 3.4 MB tile-assembly GeoPackage and one
   authorised tile (not the 37–40 GB national DTM/DSM). Compare relative
   building height through DSM–DTM, avoiding tree/crown returns and retaining
   resolution/survey epoch.
5. **Official flood depth**, HQ10/HQ100, historical 2021 observations and
   local rainfall/river-gauge coverage:
   https://data.public.lu/en/datasets/flood-hazard-maps-100-year-flood/ ;
   https://inondations.public.lu/en/demande-donnees.html .
   Validate scenario, water depth, return period, vertical datum and
   affected geometry; a risk-zone polygon alone is not an event loss.
6. **Land use change 2007/2015/2018/2021/2024**:
   https://data.public.lu/en/datasets/lis-l-land-use-2007-2015-2018-2021-2024/ .
   This is regional land-use context, not an independently observed
   individual building construction date.

**Source classification:** Existing broad non-admission candidate
`lu.act.bd-l-geobase` covers the product family. This document is an
asset-level refinement, **not a duplicate discovery candidate**. Rights
approval, science, origin feature lineage, and CAT model admission require
separate review. Do not add unapproved data to model inputs.

## Actual official-source result (2026-11-01)

The exact October 2026 ACT Buildings thematic ZIP was successfully retrieved and inspected read-only in [GitHub Actions run 41309562978](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41309562978). All synthetic safety tests passed.

| Exact original evidence | Observed value |
| --- | --- |
| ZIP bytes | **39,209,946** |
| Publisher catalogue MD5 | `f414154f993128a63f539aae2644c75a` (**matches**) |
| Original ZIP SHA-256 | `6630f217b39edde5f20f1078bef8a3d6eb4a09337af48394975f45f208bcfed3` |
| GeoPackage uncompressed bytes | **86,003,712** |
| GeoPackage SHA-256 | `ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676` |
| Exact original GPKG layer | `Buildings_BU_Building` |
| Feature rows | **230,353** |
| Declared source CRS / geometry | **EPSG:2169 MULTIPOLYGON** |
| Exact column names | `id`, `geom`, `BU_BuildingID`, `Source` |

This gives a **fourth real original-data evidence layer** beside ACT2013 LoD1, EUBUCCO LU00 and ACT2023v2. The field `BU_BuildingID` is a candidate stable crosswalk handle and `Source` potentially contains lineage information; the actual contents, uniqueness, nullness, source codes and correspondence to ACT2023v2 `buildingid` remain **UNVERIFIED**. Different counts, 230,353 versus 238,189, cannot be called missing/added buildings without scientifically controlled segmentations and vintage. No original per-building rows were printed and no source objects were saved or admitted.
