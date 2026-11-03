<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# ISIMIP3a ER11 tropical-cyclone maximum rain: original dataset metadata review — 2026-11-03

## Publisher metadata reviewed

Official original ISIMIP dataset metadata (read-only research inspection, not NetCDF source acquisition):
https://data.isimip.org/api/v1/datasets/f08ab32e-b3ad-4984-81d1-495235765b6c/

| Property | Publisher-declared value / observed metadata consistency |
| --- | --- |
| Dataset UUID | `f08ab32e-b3ad-4984-81d1-495235765b6c` |
| Dataset name | `er11-wind_obsclim_historical_maxrain` |
| Dataset edition/version | `20240402` |
| Public status | `public=true`, `restricted=false` |
| Model/product identity | ISIMIP3a / InputData / climate / tropical_cyclones / obsclim / global / storm / historical / ER11-wind / maxrain |
| Published original-file inventory | 72 annual `.nc` files from 1950 through 2021, one per year |
| Published total size | **1,911,545,255 bytes** (sum of 72 declared file sizes equals dataset-level declared size) |
| Dataset-level licence declaration | **CC0 1.0 Universal Public Domain Dedication** (`https://creativecommons.org/publicdomain/zero/1.0/`) |
| Per-file licence declarations | **72/72 report CC0 1.0**, with the same published edition `20240402` |
| Publisher file checksums | **72/72 report SHA-512** (128-character hex strings); these digests are **not independently verified against original NetCDF bytes** |
| Original-file semantics | Annual *containers* of modelled maximum 24-hour tropical cyclone precipitation; directory prefix `ER11-wind` is **not proof of wind-speed raster content** |
| Metadata scope | Dataset/product/filenames/rights/length/checksum declarations only; **no full NetCDF content** was fetched |

For reproducible follow-up, provider-published sample entries in the API include:

- 1950: `er11-wind_obsclim_historical_maxrain_1950.nc`, **22,073,838 bytes**, SHA-512 `023d2f53b95c5c4fc2e4e5f9ba23cca743be743272da2c4d63cc000a11212398ae5c84da6073173927e5965bf2a25caf02897742780f98e0190a240a293cdcfa`.
- 2021: `er11-wind_obsclim_historical_maxrain_2021.nc`, **29,818,152 bytes**, SHA-512 `dab41d074d41e9c3d5ce67401cb7457075084a5569af213a804187f8730b6cb0871e5867d9587668ab781834d142b4e8c5767ed772e330cf801d4211729c677b`.

**Important licence clarification:** Earlier source notes correctly refused to infer a licence from a generic ISIMIP3 CC0 *recommendation*. The exact **dataset metadata and every listed file** now explicitly declare **CC0 1.0**. This is meaningful new evidence but **does not remove the independent terms gate**: the official [ISIMIP repository terms](https://www.isimip.org/gettingstarted/terms-of-use/terms-use-publicly-available-isimip-data-after-embargo-period/) include a *no data sale* condition and mandate following each assigned licence. Source-input dependencies (IBTrACS, ERA5, reconstruction methods), commercial insurer modelling rights, attribution/redistribution, and possible differences between public terms and API metadata must be reconciled explicitly. Do **not** mark rights fully verified or permit model ingestion merely from CC0 labels.

## Technical readiness, not product admission

The previous offline text filelist validator in `research_runners/isimip3a_er11_maxrain_filelist_preflight_v0.py` validates only 72 syntactically correct annual URLs. It **cannot** determine dataset-level or file-level licences, published file sizes, file SHA-512 declarations, edition, or source file content integrity.

The new offline publisher-JSON metadata preflight checks the stricter original metadata shape and **fails closed** on inconsistent year coverage, edition, CC0 declarations, sums, checksums, URI identities, or source status. It never issues HTTP, never downloads NetCDF content and does not mark any dataset admitted. Metadata response bytes must be obtained and independently pinned through a separate authorised research receipt before running a provenance-valid audit. A test fixture digest is **not** real publisher authentication.

## Additional model gates

1. Rights review against the official terms and model input provenance; remember CC0 declaration and terms-of-service obligations can coexist.
2. Read-only metadata byte/source SHA-256 receipt and any catalogue revision comparison.
3. One rights-cleared NetCDF original-byte header/sample check (variable names, maximum-24-hour accumulation meaning, event identity, units, grid, missingness and source SHA-512), **not** a 72-file download.
4. Map dependent wind/rain/surge hazards through one verified cyclone parent ID, then join to independently calibrated building vulnerability. Do not infer insured loss from the meteorological reconstruction itself.

**Status: documented publisher metadata, not independently verified NetCDF contents; no source admission, no insurer commercial-use approval, no Neon ingest and no NextGen model execution.**
