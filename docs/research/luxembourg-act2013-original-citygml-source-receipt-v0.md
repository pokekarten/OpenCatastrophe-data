<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg ACT2013 LoD1: authoritative original CityGML archive receipt

**Research only; source metadata/ZIP integrity, NOT model admission or building matching.**

## Why this source is materially new

The official EUBUCCO v0.2 Luxembourg source metadata workbook identifies `gov-luxembourg` as **Administration du cadastre et de la topographie** `Bâtiments 3D (LOD 1 – Level of Detail 1)`, 2013, original licence CC0-1.0, native EPSG:2169. EUBUCCO LU00 v0.2 has **144,088** government-labelled geometries in its 186,171 building rows, but a source label by itself does not confirm the original release or per-record geometries. The 2023 ACT2023v2 data contain **238,189 roof extent polygons**: newer and geometrically different from the 2013 LoD1 generalized building blocks.

The **official ACT2013 provider dataset exists independently**, with a publisher-shared exact 2019 national ZIP of the 2013 imagery-derived product:

- Original source: https://data.public.lu/en/datasets/batiments-3d-2013-lod-1-level-of-detail-1/
- Exact resource: https://data.public.lu/en/datasets/r/c54d412a-23f9-4ee8-bfbe-002f7e6d3213
- Publisher original ZIP: https://download.data.public.lu/resources/batiments-3d-lod-1-level-of-detail-1-1/20190528-082153/lod1-par-pays.zip
- Published **SHA-1:** `83b9b4b3ff4f4f145ecd1322cfd7fd4ad9688652`, not a self-computed digest.
- Publisher listed size **30.1 MB**, May 28, 2019 update; licence label **CC0**; 2013 aerial-observation basis and EPSG:2169.
- Original format **CityGML LoD1**. Generalized building blocks *cannot* resolve every adjoining building or detailed roof feature. The publisher describes mean roof-perimeter height rather than building-specific insured replacement value.

## Strict offline first stage

`research_runners/luxembourg_act2013_original_zip_receipt_v0.py` accepts **only a locally supplied** national ZIP. It checks the already-published SHA-1, produces a new exact ZIP SHA-256 receipt, rejects unsafe, symlink, duplicate, encrypted, too-large or highly compressed members and stream-decompresses each member through CRC verification. It outputs only archive counts and extension families: no original CityGML coordinates, building IDs or any data records.

```bash
python -m unittest tests.test_luxembourg_act2013_original_zip_receipt_v0 -v
python -m research_runners.luxembourg_act2013_original_zip_receipt_v0 \
  --source-zip /private/original/2013/lod1-par-pays.zip
```

The narrowly scoped GitHub Action `.github/workflows/luxembourg-act2013-original-citygml.yml` executes this on one fixed publisher HTTPS URL with size and runtime bounds and deletes the source file after use. A failed provider download, SHA-1 mismatch or unsafe ZIP member blocks use. **SHA-1 is a publisher-listed source identity** (not a cryptographically collision-resistant authenticity guarantee); the independently computed SHA-256 and transfer identity must be retained for all later experiments. Never silently swap another national/canton/commune original ZIP or later year into this exact contract.

## Before comparing to ACT2023v2 and EUBUCCO

1. Read the exact CityGML national ZIP structure and confirm actual XML/CityGML namespaces, `gml:id`, stored coordinate order, LoD1 building-unit semantics and number of geometric objects; **the archive validator does not do this**.
2. Confirm EUBUCCO v0.2 Luxembourg original `gov-luxembourg` source lineage against this exact ACT2013 archive or a known regional extraction; the source name/format are consistent but raw-byte derivation is NOT proved.
3. Compare bounded source-qualified polygons only after reviewed EPSG:2169 native-axis controls, cross-source CRS conversion and stable original `gml:id` interpretation. A single LoD1 CityGML construction block may represent several newer roof footprints or several EUBUCCO building records.
4. Keep observation time (2013), publication date (2019), EUBUCCO release time and ACT2023v2 imagery date (2023) separate. Building appearance/disappearance, roof changes and survey segmentation are unresolved before audited samples.
5. Treat EUBUCCO aggregate ODbL obligations and possible upstream regional exceptions separately from this official ACT2013 CC0 product and the ACT2023v2 CC0 label. No raw external bytes or joins may enter Git or the CAT-only Neon metadata DB without bounded admission.

This source receipt **does not establish** individual building identity, independent validation, measured building height uncertainty, insured TIV, weather hazard, vulnerability or CAT model readiness.
