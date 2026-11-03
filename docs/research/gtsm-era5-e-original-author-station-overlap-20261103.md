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

## Verified joint original-source evidence (2026-11-03)

The exact-head [two-pinned-originals GitHub Actions run 41708472051](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41708472051), job `126170000614`, passed **13 synthetic/offline tests** and fully verified both provider originals: the fixed 9,652,424-byte Zenodo NetCDF with published MD5 and observed SHA-256 and the exact **1,798,674-byte** author CSV against the pinned GitHub Git blob SHA-1 `07c784f401a1296bea15e7bfbd10332065dc3732`. The entire comparison is in-memory and the original NetCDF is erased at completion.

| Author catalogue / Zenodo v2 statistical source crosscheck | Actual aggregate count |
| --- | ---: |
| Author catalogue rows | **43,119** |
| Original Zenodo statistics rows | **38,957** |
| Zenodo native IDs found in author catalogue | **38,957** |
| Exactly matching station ID **and** coordinates packed at 0.001 degrees | **38,957** |
| Native statistics IDs absent from author catalogue | **0** |
| Original ID matches with differing packed coordinates | **0** |
| Author catalogue IDs **not** represented in Zenodo statistics | **4,162** |
| Author-only IDs inside occupied Zenodo station-ID span | **4,162** |
| Author-only IDs outside occupied Zenodo station-ID span | **0** |
| Integer labels inside original native-ID span absent in **both** files | **615** |
| Width of original source ID span | **43,734** |

The two-dimensional **ID and exact coordinate correspondence for all 38,957 published statistical rows is verified**, rather than merely hypothesized. The author catalogue **is not** the 44,734-point paper count: the actual author CSV has 43,119 records. The two files together occupy 43,119 unique native ID labels inside a 43,734-wide span, leaving 615 unrepresented labels in **both**. The 4,777 internal gaps previously reported in the source NetCDF therefore reconcile exactly to **4,162 author-catalogue-only IDs + 615 IDs in neither**. Comparing the *paper's different 44,734 count* against 43,119 author rows leaves **1,615** positions with still-unresolved catalogue-version/selection provenance; the subset/arithmetic interpretation of 1,000 beyond the observed span remains **conditional**, not a proven mapping to physical sites.

### Original station name-family coverage

These are **prefix-based catalogue classes**, not independent geospatial coast/ocean model support verification:

| Author source name-prefix family | Original author catalogue | Represented in Zenodo statistics | Author-only (missing statistical row) |
| --- | ---: | ---: | ---: |
| `id_coast_` | 18,714 | **18,514** | **200** |
| `id_reg_grid_` | 19,893 | 17,598 | 2,295 |
| `id_obs_` | 829 | 416 | 413 |
| Other source names | 3,683 | 2,429 | 1,254 |
| **Total** | **43,119** | **38,957** | **4,162** |

One noteworthy practical implication: the present statistical file includes **18,514 of 18,714** catalogue rows marked with a `coast` station-name prefix. A claimed building-specific coastal flood model still requires checking the exact coast station's physical support, bathymetry, terrain/geoid and flood-defence mapping, storm and surge components, independent gauge validation, and the station's true membership in that catalogue release.

### Remaining questions, now narrowed

1. Obtain the *run-vintage source catalogue and generation manifests* for the paper's 44,734 hydrodynamic points and reconcile the 43,119-row author CSV with that count. An exact ID and coordinate match for the existing 38,957 records **does not prove** every simulation point was intended to have a statistical result.
2. Identify why the **4,162** author-catalogue entries did not receive a published statistic, especially **200** coast-prefix and **2,295** grid-prefix entries; examine the author batch manifests, NetCDF input inventory, filtering/drop criteria and failed-fit reports. The earlier native IDs had two exactly 2,200-ID holes and three exactly 100-ID holes, suggestive of but not proving whole-batch omissions.
3. Determine the meaning and source of the **615** integer labels found in neither published file; they may belong to another index version, deleted positions or just unused sequence labels. Never fabricate a row or assign a coordinate to these labels.
4. Continue the independent CDS v2/v3 data vintage, 2.5/97.5% versus 5/95% confidence interval label and local mean sea level/geoid harmonization investigations. Do not treat a data identity match as approval to model insured losses.

The original-source verification now confirms *existing station identity and coordinates*; **same processing-run input history, missing-station causes, legal/commercial reuse scope and CAT model physical fitness remain open**. The 2026 paper's 44,734 model output point count is an independent result and cannot automatically be substituted for the 43,119-row author catalogue.

`source_release_identity_and_commercial_rights_approved=false`, `cat_model_admitted=false`; commercial rights and upstream CDS license use must be approved separately, and coordinate/datum alignment to real-world building parcels and hydrodynamic coast support remain unvalidated.
