<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# XWS Kyrill (18 January 2007): original 3-second gust NetCDF research preflight

**2026-11-05 | Draft | Not insurer CAT admitted.** This work **extends** the pre-existing XWS landscape entry in `landscape/sources-europe-cat-model-components.json` (`xws.european-extreme-windstorms`); **do not create a second source definition** or reclassify real insurer exposures.

## Stronger original source opportunity than a metadata-only register

The [official XWS extreme European windstorms catalogue](https://www.europeanwindstorms.org/) is a freely accessible publisher original of **50 hand-selected extreme European storm events** between 1979 and approximately 2013. For Kyrill, 18 January 2007, it directly serves NetCDF3 Classic (`CDF\x01`) footprint views. Unlike Copernicus CDS, these four direct publisher NetCDF links require no CDS API credentials:

- [Uncontaminated raw Kyrill physical footprint](https://www.europeanwindstorms.org/repository/Kyrill/Kyrill_rawFootUncon.nc)
- [Recalibrated gust lower 95% bound](https://www.europeanwindstorms.org/repository/Kyrill/Kyrill_biasL95.nc)
- [Recalibrated gust mean](https://www.europeanwindstorms.org/repository/Kyrill/Kyrill_biasMean.nc)
- [Recalibrated gust upper 95% bound](https://www.europeanwindstorms.org/repository/Kyrill/Kyrill_biasU95.nc)

Official methodology: <https://www.europeanwindstorms.org/method/footprint/>. The publisher specifically states **CC BY 4.0, including research and commercial use with attribution** to the Met Office, University of Reading and University of Exeter. Retain attribution, quality and warranty caveats and do not infer authorisation of unrelated third-party model data. The original XWS website exposes the original static files at individual URLs, not just a JPEG/plot preview.

## Physical data semantics: a critical projection incompatibility

The source data model follows **CF-1.0 NetCDF Classic** with coordinate dimensions `time`, `lat` and `lon`, a `rotated_pole` mapping and a `wind_speed_of_gust` field whose original units are `metres per second`. The grid has a **rotated pole** (as documented by the publisher: 177.5° longitude, 37.5° latitude) and angular spacing **0.22° in the rotated CRS**, approximately 25 km. These values are NOT the WGS84 longitude and latitude of real sites. The NextGen C3S adapter expects a normal EPSG:4326 rectangular 0.25° or 0.016° gridded event with cell centres, fixed microdegrees and a genuinely authenticated C3S product. Feeding XWS rotated lat/lon in as C3S will cause physically incorrect site lookup.

The first proof therefore **does not** attempt a site impact map. It downloads the four pinned **exact allowlisted** original URLs ephemerally, enforces a 256,000 byte per-product bound, original-host HTTPS redirect, CDF1 magic and source header signatures, and parses selected original source axes and gust statistics with pinned `scipy==1.16.3`. It prints original publisher byte SHA-256/length, finite-wind count, rotated-grid dimensions, source projection and physical units. **No downloaded NetCDF file** is saved in Git, Neon, artifacts or persistent output; workflow artifacts contain only log receipts. Original source SHA pins can be locked after a verified successful run and then independently reproduced in a second environment.

The source repository's `tests/test_xws_kyrill_original_netcdf_hazard_receipt_v0.py` provides fake-source security negative tests (nonpublisher redirect, wrong MIME/formats, truncation, bounds and intentional non-admission). A passing offline unit test is **not** proof of any original Kyrill source values. Exact original source pass must be separately confirmed in CI, not assumed.

## Strict model boundaries

- One real historical **Kyrill event** has four **alternative wind representations**. Four NetCDF files do **not** equal four independent annual storms. The lower and upper 95% bounds express footprint uncertainty, not simulation frequencies or insurance loss percentiles.
- The catalogue is a **biased selected-extreme sample** (originally 23 expensive insurance storms and 27 non-insurance storms). Dividing 50 by a 1979–2013 year count is **not** a valid total hazard rate or AEP/OEP measure; historical overlap with C3S and CLIMK must be reconciled.
- A raw/decontaminated/recalibrated wind field is **hazard only**, not wind vulnerability. The 2022 NRW HU `GFK` building-function code does not establish wall or roof material, construction period, height, wind damage rate or insurance excess.
- A future **separate** XWS-to-true-WGS84 reprojection test must verify the CF rotated-pole transform, grid centres, no-data mask and 2–3 independent source control points, then map **only** the fictitious 10,000-site OED book. The direct NextGen C3S NetCDF extractor must **not** receive XWS bytes because the source CF dimension/axis model is different.
- A historical Kyrill *single-event* gross-damage **sensitivity** may later be computed only with independently licensed vulnerability and explicit fictitious policy terms. It would remain **one-event counterfactual**; native Oasis IL/RI and Monte-Carlo yearly curves still need an actual model-compatible events/occurrence/period probability measure.

## Reproduction / source acceptance

```sh
python -m unittest discover -s tests -p 'test_xws_kyrill_original_netcdf_hazard_receipt_v0.py' -v
python -m pip install --no-input scipy==1.16.3
python research_runners/xws_kyrill_original_netcdf_hazard_receipt_v0.py
```

No secret, credentials, raw insured data or external model source are needed. Input is four publisher original small NetCDF files. Do **not** promote this draft or attach the source values to R+V legal entity as observed underwriting risks. The next stages are exact source file SHA pins, independently tested true geocoding and the German wind-vulnerability source/period bridge.


## Original-source PASS and complete 10,000 fictitious NRW site wind-hazard integration — 2026-11-05

The earlier original-source gate is now **PASS**, not pending: [source workflow #42106677697](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42106677697) acquired all four **original** official XWS Kyrill 2007 CDF1 files, each 122,304 bytes, 158×178 cells, with original SHA-256 pinned in [typed original source receipt](../../research/observations/xws_kyrill_2007_original_netcdf_receipts_v0.toml) and enforced in the bounded downloader:

- Original uncontaminated: `bf18bd37b0fa441bd02a00860c0fa74474c77691efe316efd46bde0ca8b483f5`
- Original recalibrated L95: `5ac73f78239ef62bb177c210dbefaf7608e0dbac7cccc53cf10819bf3cbb64e0`
- Original recalibrated mean: `aef5c8cd7ed2cf475c190e08f5dc0148231fd91dd47bdb541a6360552ccd28bb`
- Original recalibrated U95: `ab4bc78cc1b330f5c3a4a5ab9e67422865a0fbd44c0c6585dd127a0e95826f82`

**New real historical-source-to-fictional-exposure milestone:** [source/geo workflow #42107349622](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42107349622) used exact pre-reviewed fictional [NRW 2022 HU 10k OED ZIP SHA `5b0055ce...`](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42097472463/artifacts/13447603258), fetched all four original storm views by pinned SHA, and **transformed 10,000 WGS84 public physical building-candidate coordinates into XWS CF rotated-pole coordinates (177.5E/37.5N) using pinned pyproj 3.7.2**. It then joined to *nearest original* wind grid cells (0.22° rotated grid; do not call this 0.25° EPSG:4326 C3S or source-site wind anemometer readings).

A separate independent local artifact audit verified two published ZIP members, internal CSV SHA-256, **10,000 unique fictitious site IDs, all 53 Kreise, 79 occupied original rotated-grid cells**, and all 10k normalized **historical** mean/raw/L95/U95 windfield representations (0 missing site values; lower95 ≤ mean ≤ upper95 for every site). No external original provider NetCDF was republished. Exact derived [artifact 13452772144](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42107349622/artifacts/13452772144) ZIP digest `631ef3b4f25ac5512bb8c71d936fc2d1ee6922af2f3ab01df17ca3f987a0f918`, site-joined CSV digest `80ad88ddcb8860d7f2396a35a2e3ce57d3b73eb4b98353503e9a04bd3dac8cdf`. Persisted non-geocoded original-source/site summary metadata in [typed receipt](../../research/observations/xws_kyrill_2007_nrw_10k_fictional_hazard_join_receipt_v0.toml), no provider raw file or actual insured customer data.

| Measured original XWS hazard sampled on **fictional** NRW physical site positions | Mean | Median | Range |
| --- | ---: | ---: | ---: |
| Recalibrated Kyrill 3s gust over 72h, m/s | 29.020927 | 29.009979 | 27.325–33.041 |
| Recalibrated lower95 3s gust, m/s | not claim independent sample mean | 19.536 | source-product uncertainty |
| Recalibrated upper95 3s gust, m/s | not claim independent sample mean | 43.079 | source-product uncertainty |
| Original uncontaminated raw 3s gust, m/s | not claim independent sample mean | 25.750 | alternative field |

**Hard stop:** This is a **real historical source-hazard → physically authentic public building-coordinate** join, attached to **fictional** insurance contracts and hypothetical EUR 4.826bn TIV. It is **not** the real R+V insured-site population, 2025 carrier market-share distribution, source-observed rebuilding valuation, scientific German wind fragility curve, contractual insured retention, or stochastic year catalogue. The 95% windfield intervals are **weather-field uncertainty**, not loss confidence intervals. The ~50 hand-selected historical XWS storms are a selection-biased tail dataset, **not** the annual event rate. Any gross/insured/net GUL/IL/RI or OEP/AEP must be introduced as distinctly declared *fictional model assumptions*, and native Oasis compatibility independently tested. This stage reports `native_Oasis_GUL_IL_RI_ran_for_Kyrill=false` and `annual_Gross_Net_OEP_AEP_authorized=false`.

Unlike the previous C3S-mimic demo adapter in PR #1373, this experiment used a **real licensed historical XWS gust grid and its CF rotated-pole mapping**. Do not merge XWS/C3S event IDs or treat Kyrill 4 field versions as independent storm events.
