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
- Listed file size: **110,738,399 compressed bytes**. A real ephemeral GitHub Actions download on **2026-11-01 13:25 UTC** now independently confirmed exactly this full byte count.
- The 64-byte HTTP range preflight from the publicly linked mirror responded with MIME `application/x-7z-compressed` and the standard 7z signature hex `377abcaf271c`. The later **full archive** download and SHA-256 receipt extends this header-only preflight.
- Edition/product semantics from filename: BD TOPO **2.1**, all themes, Shapefile, Lambert-93 (expected EPSG:2154, validate original .prj), department `D077`, release **2016-03-24**. An edition date is not necessarily an observation / construction date for every feature.
- Historic IGN download catalogue: https://geoservices.ign.fr/telechargement-api/BDTOPO
- Current provider dataset description and posted licence: https://www.data.gouv.fr/datasets/bd-topo-r
- IGN's own announcement of open access since January 2021 and accessibility of **2015–2018 older March editions**: https://geoservices.ign.fr/actualites/2021-03-26-nouveautes-bdtopo

This archive mirror is a **secondary hosting location**; authenticity against the official original provider bytes/checksum and exact 2016 product licence/attribution needs its own review. Do not assume the current product's Licence Ouverte 2.0 automatically resolves every old archive/reuse question.

The canonical structured research metadata in `landscape/fr_bdtopo_d077_2016_archive_candidate_v0.json` pins a **verified mirror full-file SHA-256** while deliberately keeping `original_sha256=null`, `model_input_approved=false`. The initial IGN GetResource discovery endpoint returned HTTP 403; that failure is **not** evidence that this edition does not exist.

## Executable next operation

If a complete copy is lawfully downloaded into a **non-Git** local working directory, run:

```bash
python research_runners/fr_bdtopo_2016_d077_archive_receipt_v0.py \
  --archive /private/BDTOPO_2-1_TOUSTHEMES_SHP_LAMB93_D077_2016-03-24.7z \
  --descriptor landscape/fr_bdtopo_d077_2016_archive_candidate_v0.json
```

The validator rejects the wrong country department, release, filename, symlink, wrong byte length or missing 7z signature. It **streams the entire local file** to produce a new SHA-256 and a legacy MD5 for possible comparison with a separately established original provider / mirror listing. **The mirror's complete-file SHA-256 was first captured in GitHub CI; subsequent runs now compare against that pinned digest, and mismatch fails closed. This still does NOT independently prove IGN original provider byte identity.** It never extracts archive contents, performs API requests, modifies Neon, or approves CAT model use.

Synthetic tests: `python -m unittest tests.test_fr_bdtopo_2016_d077_archive_receipt_v0 -v` (**11 tests initially executed locally, then expanded to 14 for pinned-hash verification**). CI exercises the synthetic tests on each PR update; a dedicated bounded original-byte mirror job also executes outside Git.

After a complete archive receipt, and only after independently reviewing exact rights and original file integrity, inspect the compressed entry listing with a safely configured archive tool, validate each building shapefile's `.shp/.shx/.dbf/.prj`, resolve path and CRS, and extract only a **bounded polygon near Ponthierry**, not an entire national footprint into model tables. Use the existing `scripts/building_footprint_overlap_v0.py` for **research-only** modern-to-2016 geometry comparison; splits/merges and absent/changed identifiers require human review. The current RNB/IGN source shares upstream BD TOPO lineage, so equal polygons do not establish independent accuracy.

A historical geometry matched to a modern building still supplies **no** reliable historical flood depth, insured value or claims; an observed water-gauge discharge, PPRI regulatory zone, and CEMS activation metadata are distinct from a georeferenced June 2016 inundation footprint. `research.fr_ponthierry_building_2016_exposure_gate_v0` must stay false for historical building/flood/insured-value admission until original spatial/temporal evidence is actually checked.

## Reality check

**Done:** exact historical edition named, mirror filename and 7z header independently probed, **all 110,738,399 compressed bytes downloaded and SHA-256 hashed in an ephemeral GitHub runner**, validator and regression tests authored. Verified full-file mirror SHA-256: `ab3e1bab127d0e71e372d736572d80e6a8a9578131992475c23a1f0ee1871a06`; legacy MD5 for comparing a historical original listing: `fe3523aea6b72fb6643f2cda91dccbd2`. Live evidence: https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41311142370. This is a full mirror receipt, **not** an independent IGN provider checksum.

**Not done:** extracting and checking the archive's inner Shapefiles/CRS, **independent IGN original checksum** comparison, validated historical Ponthierry building footprint extraction, exact-source rights and historical insured CAT exposure admission.

This source is a credible research target, **not yet 2016 building exposure admitted to a model**.

## Verified historic Ponthierry AOI building polygons (2026-11-01 13:36 UTC)

An ephemeral GitHub Actions worker successfully verified the full 2016 D077 compressed archive using `7z t`, then enumerated **321** archive members. The exact **12** `SHP/SHX/DBF/PRJ` components for three source building layer families were extracted *outside the Git checkout*. Historical Shapefile filenames use uppercase extensions; the workflow explicitly normalizes those extensions in the temporary staging directory before reading. This correction is deliberately local to ephemeral extraction.

Original `.prj` contents were verified as equivalent to **EPSG:2154** (Lambert-93). Using `pyshp` bbox filtering and `shapely` polygon intersection within **WGS84 (2.5465,48.5360,2.5490,48.5380)** returned:

| Original 2016 archived layer | Intersecting footprint candidates |
| --- | ---: |
| `BATI_INDIFFERENCIE` | **3** |
| `BATI_INDUSTRIEL` | 0 |
| `BATI_REMARQUABLE` | 0 |
| **Total** | **3** |

CI evidence: https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41312069291. All five synthetic spatial tests passed; the executable real-data source check passed after enforcing exact source-component completeness. All external data were deleted from the ephemeral workspace. No raw building polygon, private insurer exposure or source archive entered Git or Neon.

This count describes **three distinct historical mapped footprint candidates overlapping a tiny bounding box**. It is not yet a confirmed one-to-one historical building identity count, does not imply three individually insured risks, and **must not** be added to the current two RNB/IGN entities. Current-vs-historic polygons are still unlinked; distinct geometry releases may split/merge, reclassify or remap structures. Moreover the raw archive has been verified only against the public mirror SHA-256, **not** independently against an authenticated original IGN file checksum.

Next causal operation: run the existing `scripts/building_footprint_overlap_v0.py` in a bounded research-only comparison once a rights-reviewed historical subset is made available alongside the two contemporary RNB/IGN polygons, then preserve ambiguous split/merge cases; obtain actual licensed 2016 event footprint before claiming flood damage.
