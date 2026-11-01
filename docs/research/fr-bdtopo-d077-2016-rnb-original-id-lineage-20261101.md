<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Original 2016 BD TOPO v2.1 IDs against current RNB BD TOPO September 2023

**Date:** 2026-11-01. **Scope:** original v2.1 D077 March 2016 SHP DBF records near Saint-Fargeau-Ponthierry versus exactly two current, separately fetched public RNB building records. **Research only.** No original identifiers, provider shapefiles, geometry coordinates, insured values or claims were committed.

## Evidence tested against actual archived source

The full 110,738,399-byte [historical archive mirror](https://files.opendatarchives.fr/professionnels.ign.fr/bdtopo/BDTOPO_2-1_2016-03-24/) was re-downloaded, checked against its previously pinned **mirror SHA-256**
`ab3e1bab127d0e71e372d736572d80e6a8a9578131992475c23a1f0ee1871a06`, decompressed only in temporary GitHub Actions scratch and cleaned after use. [Successful original-byte + DBF+RNB live check 41355664164](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41355664164).

The original archived `BATI_INDIFFERENCIE` Shapefile has **exactly** the following DBF columns, read from the original header: `ID`, `PREC_PLANI`, `PREC_ALTI`, `ORIGIN_BAT`, `HAUTEUR`, `Z_MIN`, `Z_MAX`. The two other building shapefile families contain the same columns with an additional `NATURE`. **No `DATE_CREAT`, `DATE_MAJ`, `DATE_APP` or `DATE_CONF` columns exist in this actual v2.1 archive.** Do not transfer later-version field semantics retroactively to this archive.

The live RNB API responses list `bdtopo_2023_09` in their external identifiers. Full SHA-256 hashes of original archived `ID` strings were compared to SHA-256 of the exact modern RNB BD TOPO external IDs; both source strings were hashed without case changes or invented normalization.

## Historic/current literal ID results plus actual geometry checks

| Current public RNB ID | Archived 2016 selected source ordinal | Exact old ID = modern RNB BD TOPO ID | Geometric IoU, EPSG:2154 |
| --- | ---: | :---: | ---: |
| `5TR6PNH2YQPT` | 2 | **yes** | 0.9999999998 |
| `TCHNNF59Y27V` | 1 | **yes** | 0.9999999999 |

The third archived candidate (ordinal 0, ~1,480.23 m²) has **no** matching `bdtopo_2023_09` external ID in these two current RNB records. This does not mean the source object was demolished or uninsured; the lookup scope is only these two RNB IDs.

For the two matching pairs, both the literal ID match and independent-vintage **mapping-representation** similarity are strongly corroborating evidence that the old 2016 BD TOPO mapped features were carried through to the 2023 reference used by the current RNB. They are **not two independent surveys**: RNB inherits BD TOPO geometry lineage.

## Historic-ID caveat and admission rules

IGN's [current BD TOPO product description](https://www.data.gouv.fr/datasets/bd-topo-r) explicitly describes uniquely stable object IDs **since version 3.0**. Our archived input is **v2.1**. Therefore, the directly proven ID continuity concerns **only these two exact observed old→modern records**; it must not be generalized to all archived v2.1 entries or used as a universal migration contract.

**A 2016 database feature ID plus a pre-event March 2016 published geometry is not an authenticated building construction date or proof of June 2016 occupancy, condition, insured TIV or flood loss.** The archived 2016 building DBF fields have no construction or independent status timestamps. IGN's [later DB TOPO semantics guide](https://geoservices.ign.fr/sites/default/files/2022-11/DC_BDTOPO_3-2.pdf) distinguishes source database creation from physical object appearance; these later fields are absent from the old selected source.

The mirror full archive SHA and `7z t` prove a reproducible *mirror-archive byte receipt*, not a checksum signed/independently published by original IGN, nor unrestricted reuse rights for every vintage. Source rights, provider authenticity, and temporal status remain separate open gates.

The three historical mapped footprints do **not** independently validate the original observed Copernicus AOI04 June 2016 inundation or water depth. No original or derived provider geometry was transferred into Neon, no automated historical→modern **physical** building identity was approved and no CAT model was authorized.

## Reproducible artifacts

- [2016 original DBF hash-only ID and field receipt runner](../../research_runners/fr_bdtopo_2016_rnb_id_provenance_v0.py)
- [Synthetic regression tests](../../tests/test_fr_bdtopo_2016_rnb_id_provenance_v0.py)
- [Approved historic/source CI preflight workflow](../../.github/workflows/ign-bdtopo-2016-d077-receipt.yml)
- [Machine-readable result and non-admission flags](fr-bdtopo-d077-2016-rnb-original-id-lineage-20261101.toml)

**Remaining independent gates:** source-specific licence and provenance against an authoritative IGN-original checksum, precise 2016 AOI04 observed flood extent with temporal and geometric validity, actual historical asset/insured-state verification, and separate financial/insurance sources.
