<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Swiss crop-hail: original-source verification and source-coordinate reconciliation (2026-11-06)

## Research status: original bytes verified; spatial source mismatch is real

This is a **research-only, non-admission** proof for the four related public Swiss crop-hail datasets and software release supporting Portmann et al., *NHESS* 24 (2024), DOI https://doi.org/10.5194/nhess-24-2541-2024. All four Zenodo landing pages display CC BY 4.0; this alone does not resolve underlying insurer-derived aggregated claim data or upstream MeteoSwiss terms and any downstream rights checks.

The eight source-file checksums (all original publisher-listed MD5 recomputed from actual downloaded bytes and independent SHA-256) are pinned in `research/observations/swiss_crop_hail_zenodo_original_eight_file_receipts_v0.toml`. The source bytes were held in ephemeral GitHub runner directories and **are not in the repository or Neon**.

Original evidence runs:

- Seven dataset and metadata assets: https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42114240145
- Exact version 1.0 software archive, 21 ZIP entries, never executed: https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42184430327
- HDF5 structure on 50 real original files: https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42184189276
- Spatial key, source-event and nonzero-impact reconciliation over all 24 crop/resolution pairs: https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42185656526

The exhaustive **aggregate-only** row-by-row evidence is versioned at `research/observations/swiss_crop_hail_original_24_crop_spatial_source_proof_v0.toml`, generated from the passing run's JSON result rather than manually extrapolated.

## Observed actual source structure

- **Hazard**: MESHS and POH HDF5, each with 12 selected 2017–2021 events over 454,400 grid centroids. The sparse intensity datasets have 107,263 (MESHS) and 446,470 (POH) stored values. These are sparse matrix entries, **not unique hailstorms, exposed farms, or insured losses**.
- **Exposure**: 24 HDF5s for barley, aggregate field crops, grapevine, maize, rapeseed and wheat at 1/2/4/8 km. The exposure file is a 2021 land-use grid, not an observed insurer insured-value/location file.
- **Reported damage**: 24 crop/resolution HDF5s, with 10–12 selected event dates depending on crop. These dates are proven subsets of the 12 radar dates. The damage matrices use sparse event-by-position arrays, not independently validated monetary claim severity.
- **Source geometry**: geographic position keys were constructed by rounding source latitude/longitude to 5 decimals. This is a diagnostic match, not a fully reviewed CRS/spatial-tolerance licence to apply an insured portfolio.

## Five nonmatching crop-grid comparisons

In **19 of 24** crop-resolution pairs, every observed-damage location has a matching source-exposure coordinate key. Five pairs have extra damage-grid locations outside the corresponding exposure file:

| Crop | Resolution | Unmatched damage-grid positions | Positions with positive impact indicators | Positive sparse impact entries |
|---|---:|---:|---:|---:|
| Maize | 2 km | 367 | 201 | 247 |
| Rapeseed | 2 km | 311 | 121 | 133 |
| Wheat | 2 km | 323 | 139 | 170 |
| Rapeseed | 4 km | 1 | 0 | 0 |
| Rapeseed | 8 km | 1 | 0 | 0 |
| **Aggregate across five comparisons** | | **1,003** | **461** | **550** |

These are **source-grid positions and nonzero matrix observations**, not 1,003 individual claims, 461 individual policyholders or 550 currency amounts. The same physical geography can recur across crop/resolution comparisons. The sparse impacts on 461 unmatched positions show that treating all unjoined records as harmless empty cells would **silently exclude real observed damage indicators**.

The 2021 exposure snapshot is temporally different from the 2017–2021 damage observations; crop rotation, historical land-use changes, raster-generation details or coordinate conventions are **candidate explanations**, not a demonstrated root cause. The mismatches must remain explicit in validation metrics.

## Next science gates (not yet passed)

1. Verify reference CRS, coordinates, units, missing-value semantics and which crop-year geographic layer produced each historical damage cell. Review exact Zenodo source-metadata CSV contents and related CLIMADA dataset lineage.
2. Build event-specific crop exposure masks or a documented union source support; reconcile the 461 positively impacted out-of-exposure positions without silently assigning exposure, inventing insured TIV, or deleting observed impacts.
3. Calibrate and compare the **binary damage-footprint detection** against held-out selected events, explicit false-alarm/miss trade-offs and the Portmann et al. reference settings (roughly 8 km for field crops, 1 km for grapevine). Beware dependence of published model/training data and test data.
4. Only with independent exposure values, insured interest/treaty terms, damage-severity functions, representative annual occurrence statistics and explicit rights clearance can crop-hail be promoted toward GUL/IL/RI and annual OEP/AEP research. None are established by these checks.

**Model status:** original files confirmed and structurally parsed; event subset and basic sparse matrix shape checks passed; coordinate coverage partially mismatched; historical annual occurrence, insured monetary loss, rights clearance, and production CAT model admission remain **blocked**. No original source bytes, raw coordinates, insurer claims or third-party executable code were committed or published by this work.
