<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# ISIMIP3a tropical-cyclone historical maximum-rain annual filelist — 2026-11-03

## What was checked

The official [ISIMIP3a tropical cyclone protocol](https://www.isimip.org/gettingstarted/input-data-bias-adjustment/details/182/) identifies gridded wind and rain reconstructions derived from IBTrACS tracks, with track gap-filling, ERA5 meteorological inputs and modelling by the H08/ER11/TCR methods. The documentation describes **1950–2021** historical inputs, 300-arc-second (~10-km) gridded fields, 3-hourly track variables and time-varying/aggregated gridded fields.

The [official ISIMIP repository API documentation](https://www.isimip.org/outputdata/isimip-repository/#using-the-api) describes its metadata search and plain-text filelist endpoints. A public research fetch on 2026-11-03 returned an annual filelist at the **exact dataset ID**:

- Dataset UUID: `f08ab32e-b3ad-4984-81d1-495235765b6c`
- Public filelist: https://data.isimip.org/api/v1/datasets/f08ab32e-b3ad-4984-81d1-495235765b6c/filelist/
- Exact observed file family: `https://files.isimip.org/ISIMIP3a/InputData/climate/tropical_cyclones/obsclim/global/storm/historical/ER11-wind/er11-wind_obsclim_historical_maxrain_YYYY.nc`
- Public metadata response listed **72 names**, one for each year **1950–2021 inclusive**, in ascending order.
- IMPORTANT: **The directory is named `ER11-wind` but the filenames are `maxrain`**. This is an annual **maximum rainfall** product, not an observed wind footprint. Do not silently substitute it for `windlifetimemax` or for a wind-damage model input.
- The provider-supplied URL list is **metadata only**; no netCDF original-file bytes, sizes, variable attributes or dataset checksums were retrieved or established here. The 72 listed file names are not proof that 72 NetCDF downloads will succeed.

## Rights and scientific gates

[ISIMIP data licensing guidance](https://www.isimip.org/gettingstarted/terms-of-use/licenses-publicly-available-isimip-data/) encourages CC0 for ISIMIP3 *model outputs*, but **does not establish the licence of this specific ISIMIP3a InputData product**, or blanket commercial rights to derived IBTrACS/ERA5 inputs. Review the DOI [10.48364/ISIMIP.605192](https://doi.org/10.48364/ISIMIP.605192), dataset-level licence/attribution, input-provider agreements and insurer reuse before download or commercial model admission.

Do not conflate this product with **ISIMIP3b CHAZ** synthetic TC tracks: separate source, forcing, regime and restrictions, including an explicitly noncommercial licence described in the [ISIMIP3b scenario setup paper](https://gmd.copernicus.org/articles/19/4095/2026/).

All file outputs are *modelled* hazard intensity estimates derived from historical TC positions, rather than independently observed storm footprints. They must not be counted as a second independent hurricane track observation alongside IBTrACS. The storm-event IDs and daily/annual netCDF aggregation semantics, units and missing data still require original-file review.

## New offline preflight: fail-closed and no download

- Runner: `research_runners/isimip3a_er11_maxrain_filelist_preflight_v0.py`
- Synthetic negative tests: `tests/test_isimip3a_er11_maxrain_filelist_preflight_v0.py`
- Input: **locally supplied** original ASCII plain-text filelist with separate independently pinned SHA256.
- Output: only aggregate source metadata and non-admission flags, no original file links, raw NetCDF, storm data, insurer values, location-level data, or public database writes.
- Fixed scheme, host, exact path/filename, 72 complete consecutive years (1950–2021), no duplicate/other-model URLs, byte cap 32 KiB; credentials, signed links, fragments, unexpected parameters and out-of-order years fail closed.
- No network/HTTP libraries or automatic downloads in the runner. All output flags explicitly leave scientific, legal, commercial and model admission unapproved.
- The `--expected-sha256` should come from **independent filelist receipt evidence**. Hashing the input itself and passing the value as the expected digest is useful only for local format regression, **not** source authenticity.

### Example *after* acquiring and separately pinning the authorised metadata-only filelist

```sh
python3 research_runners/isimip3a_er11_maxrain_filelist_preflight_v0.py \
  --filelist /path/to/independently-obtained-filelist.txt \
  --expected-sha256 YOUR_INDEPENDENTLY_RECORDED_64_HEX_SHA256 \
  --out /tmp/isimip-filelist-receipt.json
python3 -m unittest tests.test_isimip3a_er11_maxrain_filelist_preflight_v0 -v
```

## Next steps

1. Confirm exact dataset-level rights and content provenance (input vs output, ERA5/IBTrACS attribution, relevant secondary licensing, commercial/reinsurance automation). **Not yet approved.**
2. Produce a pinned, original provider filelist SHA256/metadata receipt from an authorised read-only metadata run; compare the full 72-file inventory with this recorded source family. No raw NetCDF acquisition implied.
3. After dataset access approval, perform a strictly bounded **one-file NetCDF header** check for time/grid, unit, variable name, fill value, version, storm aggregation and product ID; do not begin a 72-file bulk download.
4. Crosswalk the hazard field to NextGen event identities while preserving year, source, force model, provenance, original grid and distinct loss components (TC wind, TC rain, coastal surge). Integrate with losses and FFBK only after independent vulnerability calibration, source governance and model validation.

**Status:** A single ISIMIP3a annual filelist has been documented through public metadata. No product byte download, no insurer portfolio enrichment, no Neon ingest, no independent hurricane observation, no CAT model admission and no dataset licence clearance is claimed.
