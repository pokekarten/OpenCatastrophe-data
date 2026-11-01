<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Exact 2016 IGN BD TOPO D077 archive: verified acquisition target, not yet model input

**Research date:** 2026-11-01. **Peril use case:** reconstruct the building stock near Ponthierry, Seine-et-Marne, *before* the May–June 2016 Seine/Loing flooding. Research-only; source bytes are not in Git or Neon.

## Material new source identification

The historical target is no longer an unspecified 2015/2016 archive. A public copy of the old official departmental distribution is indexed here:

- Archived directory: https://files.opendatarchives.fr/professionnels.ign.fr/bdtopo/BDTOPO_2-1_2016-03-24/
- **Exactly listed file:** `BDTOPO_2-1_TOUSTHEMES_SHP_LAMB93_D077_2016-03-24.7z`
- Listed file size: **110,738,399 compressed bytes** (not a measured successful full transfer).
- The 64-byte HTTP range preflight from the publicly linked mirror responded with MIME `application/x-7z-compressed` and the standard 7z signature hex `377abcaf271c`. **This does not prove the remaining bytes are intact.**
- Edition/product semantics from filename: BD TOPO **2.1**, all themes, Shapefile, Lambert-93 (expected EPSG:2154, validate original .prj), department `D077`, release **2016-03-24**. An edition date is not necessarily an observation / construction date for every feature.
- Historic IGN download catalogue: https://geoservices.ign.fr/telechargement-api/BDTOPO
- Current provider dataset description and posted licence: https://www.data.gouv.fr/datasets/bd-topo-r
- IGN's own announcement of open access since January 2021 and accessibility of **2015–2018 older March editions**: https://geoservices.ign.fr/actualites/2021-03-26-nouveautes-bdtopo

This archive mirror is a **secondary hosting location**; authenticity against the official original provider bytes/checksum and exact 2016 product licence/attribution needs its own review. Do not assume the current product's Licence Ouverte 2.0 automatically resolves every old archive/reuse question.

The canonical structured research metadata in `landscape/fr_bdtopo_d077_2016_archive_candidate_v0.json` deliberately keeps `original_sha256=null`, `model_input_approved=false`. The initial IGN GetResource discovery endpoint returned HTTP 403; that failure is **not** evidence that this edition does not exist.

## Executable next operation

If a complete copy is lawfully downloaded into a **non-Git** local working directory, run:

```bash
python research_runners/fr_bdtopo_2016_d077_archive_receipt_v0.py \
  --archive /private/BDTOPO_2-1_TOUSTHEMES_SHP_LAMB93_D077_2016-03-24.7z \
  --descriptor landscape/fr_bdtopo_d077_2016_archive_candidate_v0.json
```

The validator rejects the wrong country department, release, filename, symlink, wrong byte length or missing 7z signature. It **streams the entire local file** to produce a new SHA-256 and a legacy MD5 for possible comparison with a separately established original provider / mirror listing. **Local SHA-256 alone is not provider verification**. It never extracts archive contents, performs API requests, modifies Neon, or approves CAT model use.

Synthetic tests: `python -m unittest tests.test_fr_bdtopo_2016_d077_archive_receipt_v0 -v` (**11 locally tested**). CI will check the repository when the PR opens.

After a complete archive receipt, and only after independently reviewing exact rights and original file integrity, inspect the compressed entry listing with a safely configured archive tool, validate each building shapefile's `.shp/.shx/.dbf/.prj`, resolve path and CRS, and extract only a **bounded polygon near Ponthierry**, not an entire national footprint into model tables. Use the existing `scripts/building_footprint_overlap_v0.py` for **research-only** modern-to-2016 geometry comparison; splits/merges and absent/changed identifiers require human review. The current RNB/IGN source shares upstream BD TOPO lineage, so equal polygons do not establish independent accuracy.

A historical geometry matched to a modern building still supplies **no** reliable historical flood depth, insured value or claims; an observed water-gauge discharge, PPRI regulatory zone, and CEMS activation metadata are distinct from a georeferenced June 2016 inundation footprint. `research.fr_ponthierry_building_2016_exposure_gate_v0` must stay false for historical building/flood/insured-value admission until original spatial/temporal evidence is actually checked.

## Reality check

**Done:** unique historic edition named, mirror index and 7z header independently probed, original-archive receipt validator and tests authored.

**Not done:** full 110.7-MB archive download/hash/decompression, provider original checksum comparison, validated historical Ponthierry building footprint extraction, rights and historical insured CAT exposure admission.

This source is a credible research target, **not yet 2016 building exposure admitted to a model**.
