<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GTSM-ERA5-E: independent author station catalogue overlap receipt (2026-11-03)

## Finding the actual original catalogue

The public GTSM producer GitHub source at commit `30580a729be88fea8bf5b4e813b39e381ad9e2f4` includes a catalogue `04_supplementary_data/GTSM_output_locations_list.csv`, used by independent Deltares `dfm_tools` source `gtsm3_era5_cds_ssh_read_catalog()`. This is a concrete potential identity and position reference for the 38,957 original statistical file rows, rather than an assumed numerical parent-index range.

- Original catalogue: https://github.com/VU-IVM/gtsm3-era5-nrt/blob/30580a729be88fea8bf5b4e813b39e381ad9e2f4/04_supplementary_data/GTSM_output_locations_list.csv
- Author GitHub blob SHA-1, as returned by the native GitHub connector: `07c784f401a1296bea15e7bfbd10332065dc3732`. This is a *Git object identifier*, not the original file's separately published checksum. It is checked over `b"blob <length>\\0" + exact bytes` before parsing.
- Deltares catalogue consumer: https://github.com/Deltares/dfm_tools/blob/f24fa6c92e3fe51a3128a43cd99cb30a9599e625/dfm_tools/observations.py . The reader uses TSV columns `station_id`, `station_name`, `lon`, `lat` and `EPSG:4326`, with a `gtsm3-era5-` namespace.
- Original GTSM descriptive-statistics asset: https://zenodo.org/records/14671593 , exactly 9,652,424 bytes, original MD5 `0f2b7071c6ec3585768be6cf427e6eab`, independently observed SHA-256 `e366c79683438d03a48b23764f1159d5ed88845a459f625eeb787dff78cbd767`.

The historical `stations` uint16 ID list in the Zenodo statistics file has 38,957 unique increasing records, 4,777 internal missing index labels in 76 blocks (two exactly 2,200; three exactly 100) and a conditional 1,000 labels above its last occupied native index, under the **unproven shared 44,734-position parent catalogue** hypothesis. See [previous source evidence](gtsm-era5-e-station-catalogue-lineage-20261103.md).

## New exact-source matching workflow

`scripts/gtsm_era5_e_author_catalogue_overlap_v0.py` and `scripts/gtsm_era5_e_author_catalogue_original_v0.py` implement an **ephemeral, fixed-source** comparison:

1. Acquire the pinned Zenodo file from the fixed HTTPS publisher and verify exact size, provider MD5, observed SHA-256 and native NetCDF schema using the merged original receipt.
2. Acquire **only** the exact author GitHub commit URL and verify its entire file against the author Git object blob ID. Reject unpinned or changed files and cross-host redirects.
3. Parse bounded TSV columns `station_id`, `station_name`, `lon`, `lat`, rejecting duplicates/invalid uint16 IDs, invalid coordinates and row-count drift.
4. Read exactly the 38,957 source-native Zenodo station uint16 IDs and native packed int32 longitudes/latitudes, using the original known `0.001 degree` scaling. Compare candidate ID matches and corresponding packed coordinates at exact and 0.001-degree comparison tolerance.
5. Report *only aggregate counts*: catalogue rows, IDs matched/missing, exact/within-one-packed-unit/contradictory position counts, and source-name-prefix classes `id_coast_`, `id_reg_grid_`, `id_obs_` / other.
6. Delete both originals at end. No original station ID, coordinate pair, original CSV, NetCDF, source model water level, source file array or location-level record reaches Git, CI artifacts or Neon.

The catalogue's **station-name prefixes are a provenance/consumer convention**, not stand-alone physical or hydrodynamic validation of a coastal asset, flood footprint or insured location. Even an exact ID+coordinate match does not establish the missing 5,777 records' physical locations or why any omission occurred: this requires checking the authoritative same-run producer selection/filtering and original batch output manifests.

Code/CI:
- `scripts/gtsm_era5_e_author_catalogue_overlap_v0.py`
- `tests/test_gtsm_era5_e_author_catalogue_overlap_v0.py`
- `scripts/gtsm_era5_e_author_catalogue_original_v0.py`
- `.github/workflows/gtsm-original-author-catalogue.yml`

## Pending evidence and scientific gates

The exact-head original dataset run must determine whether the catalogue is truly co-indexed with the published 2025 statistical asset. Until it succeeds, **do not claim** any parent catalogue row count, overlap count, ID membership or coastline-class fraction as observed. The 2026 paper's 44,734 output-point figure is independent evidence for *model output positions* and does not guarantee this precise CSV's vintage or cardinality.

`source_release_identity_and_commercial_rights_approved=false`, `cat_model_admitted=false`; commercial rights and upstream CDS license use must be approved separately, and coordinate/datum alignment to real-world building parcels and hydrodynamic coast support remain unvalidated.
