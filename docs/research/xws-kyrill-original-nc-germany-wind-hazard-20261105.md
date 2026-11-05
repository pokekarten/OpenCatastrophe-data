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


## Governance correction and isolated Neon research registry — 2026-11-05

The first actual original NetCDF acquisition and complete 10k-geocoded-hazard join **both succeeded** as historical one-shot workflows, and their original research-only proof artifacts were checked independently. The first general GitHub CI then correctly rejected `actions/upload-artifact` in the two **new** XWS workflow definitions because the global `tests/test_public_surface.py` policy allowlists only specific pinned action families. **The global allowlist was not weakened.** Both XWS workflows were revised to rely on source/original and joined-output **SHA receipts in job logs**, delete their ephemeral generated files, and never use a disallowed upload action. The already successfully generated original proof [artifact #13452772144](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42107349622/artifacts/13452772144) remains a **historical one-shot output expiring in 14 days** (through 2026-11-19); new reruns **do not publish artifacts**. The pinned SHA, source-geometry proof and this typed receipt provide persistent audit metadata; full output re-generation requires locally supplying the original-fictional OED source artifact (or re-running its original trusted source builder). Never call a past artifact upload proof of upload success for subsequent reruns.

**Isolated Neon research-branch only:** two `registry.source_record` metadata entries are read-back verified, one for the four original Kyrill NetCDF file hashes (`research:xws:kyrill:original_four_netcdf_2007`) and one for 10k historical-hazard-to-fictitious-site join receipt (`research:xws:kyrill:nrw10k_fictional_hazard_2007`). Both are `classification=landscape_candidate`, `admissible_for_raw=false`, `rights_status=publisher_cc_by_4_attribution_required_research_only`; they retain original Git blob/source workflow/SHA evidence and explicitly set insurer-loss and annual EP flags to false. This **did not insert individual XWS grids, customer data, 10k site locations or insurer exposures into Neon**; a direct select on default Neon `main` found **0 XWS research registry rows**. The research-branch source join remains distinct from the existing 53-county fictional NRW aggregation and from the separate native UK PiWind technical GUL/IL/RI demo. No source-derived real insured GUL/IL/RI, annual OEP/AEP, or catastrophe-model release is asserted.


## First conditional one-event loss sensitivity with documented Schwierz-2010 numbers — 2026-11-05

**Actually run end-to-end:** original, unchanged source-receipt ZIPs from the successfully source-verified [XWS Kyrill physical 10k site-gust artifact #13452772144](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42107349622/artifacts/13452772144) and [NRW original-physical-HU/OED 10k fictional insured-positions artifact #13447603258](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42097472463/artifacts/13447603258) were downloaded into temporary CI storage. Exact outer SHA-256, derived XWS site-CSV SHA, OED manifest SHA, source HU22 SHA, inner CSV SHA, unique 10k policies and one-to-one fictional LocNumber/AccNumber identities, all **53 Kreis codes**, the **EUR 4,826,029,500 FICTIONAL** national toy TIV and no-actual-R+V insurance flags were checked **before** computation.

The new stdlib-only [source-locked conditional sensitivity runner](../../research_runners/xws_kyrill_nrw10k_schwierz_conditional_loss_v0.py) independently implements the *numerical PAA and MDD point values* attributed to [Schwierz et al. 2010, Climatic Change, DOI 10.1007/s10584-009-9712-1](https://doi.org/10.1007/s10584-009-9712-1), as publicly tabulated in [CLIMADA's `ImpfStormEurope.from_schwierz` source](https://climada-python.readthedocs.io/en/latest/_modules/climada/entity/impact_funcs/storm_europe.html). The upstream CLIMADA Python program is licensed under **GPLv3**; **no CLIMADA implementation code is vendored or executed** in this Apache-2.0 repo; this is independent arithmetic driven by attributed numeric literature parameters. The reference PAA/MDD intensities and loss definition are **not calibrated to 2025 R+V, to 2022 NRW HU original material/roof attributes, or to the 25-km XWS spatial interpolation uncertainty**. Literature in [Welker et al. 2021](https://doi.org/10.5194/nhess-21-279-2021) explicitly discusses case-study adjustments to this family.

For original XWS `wind_speed_of_gust` (m/s, original **2007 Kyrill one-event** physical 72-hour maximum), the fictional asset's conditional expected fractional damage is computed as **linearly interpolated PAA(wind) × separately linearly interpolated MDD(wind)**; this is the documented CLIMADA impact-function convention. Each fictitious original `BuildingTIV` is multiplied by the conditional factor and an expressly **invented ×0.5 / ×1 / ×2 multiplicative scenario**; each conditional fictitious asset expectation is rounded to EUR cents, then aggregated by 53 real-source Kreis groups (636 total county/scenario rows), and finally to a study-wide conditional expected euro amount. Multipliers **are not** a fitted confidence interval, a published Welker correction or a licensed German claims-based vulnerability. PAA is not treated as a stochastic Bernoulli policy loss distribution, and MDD is not treated as complete 0–100% secondary uncertainty.

**Live pass:** [exact pinned source-bytes workflow #42110341601](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42110341601), seven new arithmetic/provenance tests passed, plus 12 source-conserving result cases. County CSV SHA-256 `d106dac99d6981cd0c4cb3c30839b97f40c5df75aef4076f6b3b3fe01b96c40b`, exact JSON summary SHA-256 `cfe72cab3ffa39a66244dd463eba609f2f51e3fcc6316d66e5ecc97cb3623409`. The derived per-county numeric output was kept ephemeral under the workflow's global pinned-action governance. Exact monetary/assumption conclusions persist as the [typed TOML receipt](../../research/observations/xws_kyrill_2007_nrw10k_schwierz_one_event_sensitivity_v0.toml) and are retested by CI.

| Single 2007 historic Kyrill field on 10k fictional NRW policy positions | 0.5× reference assumption | Published numeric reference 1× | 2× reference assumption |
| --- | ---: | ---: | ---: |
| Lower95 windfield alternative | EUR 4.84 | EUR 13.13 | EUR 27.25 |
| Recalibrated mean historic windfield | EUR 26,845.16 | **EUR 53,686.91** | EUR 107,374.62 |
| Upper95 windfield alternative | EUR 5,518,768.68 | EUR 11,037,541.04 | EUR 22,075,083.03 |
| Original uncontaminated raw windfield | EUR 5,689.49 | EUR 11,384.17 | EUR 22,763.46 |

The immense conditional range is a **diagnostic**, not the 95% confidence interval for an insurer's CAT loss or uncertainty distribution. In particular, a change in windfield physical intensity near Schwierz' onset (20 m/s) produces nonlinear financial response. XWS source lower/upper gust uncertainty does not imply joint correlated gust uncertainty/insurance stochastic damage or annual frequency. No event-size scaling to an actual carrier, no paid-claims backtesting, no policy deductibles or limits, no QS or cat-XL RI, no CLIMADA/Oasis `gulcalc` native model run for Kyrill and **no valid OEP/AEP** has been performed.

### Next admission and independent validation checkpoints

1. Independently corroborate the source gust field using a second physical observation/reference (e.g. DWD storms and/or C3S reanalysis), explicitly accounting for model 25-km spatial resolution, 3-second gust semantics and retrospective source version.
2. Compare literature/CLIMADA reference PAA/MDD with another *published, German-relevant, legally permissible* residential building structural vulnerability curve using the same intensity basis; do not repurpose GFK occupancy class as roof/masonry fragility.
3. Rebuild a plausible **gross floor-area** value basis using documented storey-number, construction cost and coverage proxies; the original OED values are an arbitrary EUR 4.826bn toy distribution and not a true R+V balance sheet.
4. Specify a named, explicitly **fictional** building-policy deductible, limits, currency, location versus coverage structure, and QS/occurrence cat-XL agreement. A per-site *expected* loss cannot simply have an occurrence aggregate deductible applied to it to compute a valid **expected net** CAT loss: site-loss dependence and stochastic damage sampling are required.
5. Only after admitted joint occurrence/rate and loss distributions do native Oasis/NextGen `GUL → IL → RI` and proper gross/net OEP/AEP become scientifically meaningful.

This is a **major engineering demonstration** of a physical original historical storm hazard joining public buildings through a literature-based conditional loss-reference sensitivity; it is **not** an insurer-calibrated stochastic CAT model. Both PR #1389 and related #1372/#1373 remain Draft; productive Neon main remains unchanged.
