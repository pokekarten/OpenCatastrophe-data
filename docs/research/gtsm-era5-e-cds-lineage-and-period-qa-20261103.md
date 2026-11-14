<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GTSM-ERA5-E: fixed-original return-period QA and upstream CDS lineage risk (2026-11-03)

This is public **research/evidence**, not source-data admission, loss model validation or a licence determination. No raw Zenodo/CDS data may be committed or persisted to the insurance database.

## Version identity: do not conflate three different "versions"

| Identity | Observed source | Scientific/operational meaning |
| --- | --- | --- |
| GTSM hydrodynamic model v3.0 | ESSD paper: https://essd.copernicus.org/articles/18/5759/2026/ | Source model generation of tides/surges; **not** the dataset or file version |
| Zenodo statistical asset v2, 2025-02-25 | https://zenodo.org/records/14671593 | One **9,652,424 byte** NetCDF with fixed observed SHA-256 `e366c79683438d03a48b23764f1159d5ed88845a459f625eeb787dff78cbd767`; includes 38,957 station coordinates and 8 year-axis return periods |
| Copernicus CDS reanalysis experiment v2 (deprecated) and v3 (current) | https://cds.climate.copernicus.eu/datasets/sis-water-level-change-timeseries-cmip6?tab=overview | **Upstream time-series release**, DOI 10.24381/cds.a6d42d60. Its version scheme is independent of the Zenodo v2 statistical file |

## Upstream CDS corrections warrant a targeted provenance check

The official CDS **Documentation / Known issues** page (https://cds.climate.copernicus.eu/datasets/sis-water-level-change-timeseries-cmip6?tab=documentation), consulted 2026-11-03, records two closed issues raised **2025-04-17** for extended reanalysis v2:

1. Hourly `total water level` and `storm surge residual` series had a **30-minute timestamp shift** due to temporal aggregation. Official CDS documentation says corrected center-of-interval averaging was implemented in reanalysis **v3**.
2. Storm surge at the beginning of January **1950** was affected by an insufficient model spin-up. The corresponding values were replaced in reanalysis **v3**.

The Zenodo statistical v2 file was published **2025-02-25**, before the known-issue announcement; source chronology alone **does not establish** whether its statistics are affected, whether it was separately regenerated, or whether a particular tide/storm fitting output shifted. Obtain exact source-code run identity (input CDS vintage, source checksums, processing dates, 72-hour declustering, POT/GPD threshold, missingness treatment) from the GTSM authors before comparing time-series v2/v3 or claiming a quantified impact.

A 30-minute timestamp correction may leave some marginal return-level magnitudes unchanged, but can matter for event timing/coincident peril and temporal joining. January 1950 spin-up can matter for sample threshold/peak sets; do not guess the size. The paper's fitted extremes use detrended *hourly total water level* from 1950–2024, 99th percentile exceedance threshold and 72-hour declustering. The statistics are **not** independent storm events/YLTs.

## Native extreme return-level numeric QA (original, verified 2026-11-03)

Earlier bounded original-source run https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41640280655 found for 38,957 stations × 8 return periods:

- 311,656 possible (best-fit, lower 5%, upper 95%) triplets; **311,655** finite and **1** missing/nonfinite;
- **22** best-fit-above-upper comparisons and **4** below-lower comparisons, across **6** station rows;
- **0** inverted uncertainty intervals and **0** descending adjacent best-fit return levels, and **38,950** station rows without any of these test flags.

`scripts/gtsm_era5_e_return_level_qa_v0.py` now partitions these aggregate counters by each of the eight **native source return-year** labels (1/2/5/10/25/50/75/100 years), together with nonfinite counts by variable. The aggregated period labels will help identify whether apparent bounds discrepancies are concentrated in longer return periods without leaking individual modelled water levels or original coordinates. Tests enforce exact reconciliation to global totals. The actual per-period counts were subsequently established by exact-source GitHub Actions run 41690641744 and are tabulated below; no distribution was inferred from the six flagged station rows.

There is no mathematical guarantee that every fitted point estimate must lie within a separately produced bootstrap or Monte-Carlo confidence interval under all fitting and summarization conventions. Flagged crossings require scientific interpretation and source-method review. The 5/95% *confidence interval* bounds on fitted extreme return levels are distinct from the seven *time-series percentiles* in the original `wl_quantiles` array.

## Vertical reference / physical-model block

The original ESSD paper states the time-series includes sea-level-rise mean sea level relative to **1986–2005 local mean sea level**, while the published extreme return-level statistics are calculated on **detrended hourly** water levels. The GTSM model is a barotropic depth-averaged hydrodynamic model and does not fully resolve wave setup/runup, local coastline/bathymetry, structures, flood defences, or a parcel's first-floor height. A statistical still-water-level estimate in metres is **not** a flood depth or building hazard intensity.

Before any coastal peril geometry join, require:
- a specific coastal-only subset (not merely the unique 38,957 valid geographic coordinates, which include ocean sites), support/coverage and model-grid lineage;
- a documented horizontal CRS, local mean sea-level reference epoch, independent geoid/DEM/vertical-datum conversion and local topology/flow connectivity;
- validation against independent tide gauges and held-out event footprints without double counting related GTSM/Aqueduct families;
- explicit event-frequency and spatial dependence model to produce stochastic CAT event sets / YLT / ELT; return periods alone are not an event catalogue.

## Data licence and retention boundary

OpenAIRE describes the Zenodo record as **CC BY** (https://explore.openaire.eu/search/dataset?pid=10.5281%2Fzenodo.14671593). Official CDS page separately presents its underlying time-series dataset's licence as **CC-BY**: https://cds.climate.copernicus.eu/datasets/sis-water-level-change-timeseries-cmip6?tab=download . The ESSD article itself is **CC BY 4.0**, but its publication licence is **not** independently conclusive for every data file, or for each upstream model dependency. Confirm the exact deposited Zenodo file licence/SPDX identity, attribution requirements, upstream applicable CDS terms (including changes announced for October 2026), third-party derived-data conditions and intended commercial/redistribution scope before changing `data_rights_approved`. Until then all original files remain ephemeral, only aggregate QA receipts go in public GitHub, no raw source in Neon, and `cat_model_admitted=false`.

## Evidence chain and next tasks

- Merged source registry and byte/axis/coordinate QA: PR #1132.
- Merged original extreme return-level QA: PR #1175.
- This isolated research increment: per-return-period aggregate counts plus explicit upstream CDS version-drift/vertical-datum/rights review.
- **Scientific next action**: ask the source producer to confirm the CDS original run/version and exactly which statistical array the revised CDS v3 reanalysis supersedes; then design a controlled comparison, not blind data replacement.

## Verified original per-return-period quality receipt (2026-11-03)

GitHub Actions same-repository original-source run [41690641744](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41690641744), job `126107980612`, reproduced original exact SHA-256 `e366c79683438d03a48b23764f1159d5ed88845a459f625eeb787dff78cbd767` and passed **59** wholly synthetic/offline regression tests before the original-byte in-memory examination. The complete original 38,957 × 8 station-period array was checked, and only these per-period **aggregate counts** were emitted:

| Return years | Best fit above upper 95% confidence bound | Best fit below lower 5% confidence bound | Missing/nonfinite triplets |
| ---: | ---: | ---: | ---: |
| 1 | 4 | 2 | 1 |
| 2 | 4 | 2 | 0 |
| 5 | 4 | 0 | 0 |
| 10 | 4 | 0 | 0 |
| 25 | 2 | 0 | 0 |
| 50 | 2 | 0 | 0 |
| 75 | 1 | 0 | 0 |
| 100 | 1 | 0 | 0 |
| **Total** | **22** | **4** | **1** |

For that one nonfinite 1-year triplet, **all three source-native fields** (`wl_extreme_bestfit`, `wl_extreme_5perc`, `wl_extreme_95perc`) were nonfinite. The exact original also confirmed **zero** inverted 5%-95% intervals and **zero** descending best-fit levels across increasing return periods. Earlier source audit found **six distinct station rows** containing the 26 band/estimate crossings (not 26 distinct stations). Most crossings occur at low return periods; there is **no statistical evidence from these counts alone** to identify a cause. Do not infer the positions, physical causes, spatial clustering, probability calibration or commercial viability.

No individual numerical water level, original site position, original file, event catalogue, building exposure or insured loss was exported.

## Verified CDS terms and outstanding rights

The official ECMWF CDS [Terms of Use (rev. 13)](https://cds.climate.copernicus.eu/licences/terms-of-use-cds), together with ECMWF's [28 October 2026 update notice](https://forum.ecmwf.int/t/upcoming-cds-terms-of-use-change/15374), confirms the CDS terms update. Article (4) says individual CDS products remain governed by the licence **attributed to that product**, and Article (5) prohibits implying ECMWF/EU endorsement. The upstream GTSM CDS product page identifies its licence as CC-BY, while OpenAIRE labels the Zenodo statistics CC BY. Those statements improve the rights evidence but **do not automatically establish exact file-level obligations, all source derivatives, or completed approval for the intended commercial insurer product**. Maintain `data_rights_approved=false` and `cat_model_admitted=false` until attribution, per-file source conditions and specific use-case are reviewed.

## Official upstream producer code and planned native metadata receipt

Research on the public GTSM author repository, inspected at commit `30580a729be88fea8bf5b4e813b39e381ad9e2f4`:

- Original analysis code [p01 computing return periods](https://github.com/VU-IVM/gtsm3-era5-nrt/blob/30580a729be88fea8bf5b4e813b39e381ad9e2f4/02_analysis_and_validation/p01_computing_return_periods_GTSM_batch_pyextremes.py) explicitly requests the **nine** fraction percentiles `0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99`; it fits `pyextremes.EVA` using a 99%-threshold POT, 72-hour declustering, `genpareto` / MLE and `model.get_summary(..., alpha=0.95)`.
- Original assembly code [p04 create statistics dataset](https://github.com/VU-IVM/gtsm3-era5-nrt/blob/30580a729be88fea8bf5b4e813b39e381ad9e2f4/02_analysis_and_validation/p04_make_dataset_GTSM-ERA5-E_stats.py) specifies NetCDF global `license="Creative Commons Attribution 4.0 International"`, `history="This is version 2 of the dataset"`, source model `GTSMv3`, native output fields, and vertical reference **Mean Sea Level**, all as **author-intended metadata**. The direct original-file header must confirm exact values; repository source alone does not prove what was deposited.
- `pyextremes` API defines `alpha` as interval *width* (https://georgebv.github.io/pyextremes/api/models/). The `alpha=0.95` call therefore warrants a **scientific consistency check** against the original return-level field names `5perc`/`95perc` and the paper's 5%-95% wording. We have not established the exact upstream code revision or installed `pyextremes` version used in creating the Zenodo 2025 asset. Treat this as a hypothesis to verify, not proof of a mismarked interval.
- The author source code requests nine quantiles while the exact original stats file has **seven**. Neither code path's request alone explains why 1% and 99% are missing from the published array; do not fabricate them.

The pinned GitHub original-byte workflow reads only eight predeclared, bounded **global NetCDF release metadata strings** (`license`, `history`, `source`, `title`, `time_coverage_start`, `time_coverage_end`, `geospatial_vertical_units`, `geospatial_vertical_positive`). The code rejects oversize/non-ASCII/multiline/unexpected values, prints no variable arrays or coordinates, and retains all data-rights/model-admission flags **false**.

### Actual original release-attribute receipt, run 41691573859

The exact-head [GitHub original-source run 41691573859](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41691573859), job `126111225573`, succeeded on **2026-11-03**, with **61 synthetic/offline tests** and repeated publisher-size/MD5 and independently observed source SHA-256 verification: `e366c79683438d03a48b23764f1159d5ed88845a459f625eeb787dff78cbd767`.

The actual original NetCDF global file header contains:

| Native key | Observed original file value |
| --- | --- |
| `license` | **Creative Commons Attribution 4.0 International** |
| `history` | This is version 2 of the dataset |
| `source` | GTSMv3 forced with ERA5 climate reanalysis |
| `time_coverage_start` | 1950-01-01 |
| `time_coverage_end` | 2024-12-31 |
| `geospatial_vertical_units` | m |
| `geospatial_vertical_positive` | up |
| `title` | Statistics of detrended still water level timeseries for GTSM-ERA5-E dataset (1950-2024) |

This significantly narrows **file-native licensing and vertical metadata provenance**, but does **not** by itself prove all upstream CDS source rights, attribution completeness, the source-producing code's exact commit, the original pyextremes sampling/CI convention, or the local mean-sea-level-to-DEM/geoid transform. Provider data remain ephemeral and `data_rights_approved=false`, `vertical_datum_validated=false`, `cat_model_admitted=false`. The original source version is now evidenced as a file header and must not be conflated with CDS reanalysis v2/v3 or GTSM model v3.0.

## Historical pyextremes 2.3.1 confidence-level semantics (2026-11-03)

A reproducible version-specific software review narrowed the interval naming ambiguity:

- The GTSM authors' [versioned environment](https://github.com/VU-IVM/gtsm3-era5-nrt/blob/30580a729be88fea8bf5b4e813b39e381ad9e2f4/environment.yml) specifies **pyextremes 2.3.1**, Python 3.10.6, NumPy 1.25.1 and SciPy 1.12.0. This is an **environment definition**, not proof that exactly these wheels were used for the Zenodo statistical file.
- The actual historical [pyextremes 2.3.1 MLE model implementation](https://github.com/georgebv/pyextremes/blob/a268301993d6be247e24c58518beb6d70f586d2a/src/pyextremes/models/model_mle.py#L168-L170) computes the lower and upper bootstrap return-level bounds with `np.quantile(..., q=[(1-alpha)/2, (1+alpha)/2])`. For the GTSM authors' explicit `get_summary(alpha=0.95)`, this maps to **2.5th and 97.5th percentiles of the bootstrap return-level distribution**, i.e. a two-sided **95% confidence interval**. By contrast, literal 5th/95th bootstrap quantiles would form a central **90% interval** (`alpha=0.90`).
- GTSM source [p04 assembly](https://github.com/VU-IVM/gtsm3-era5-nrt/blob/30580a729be88fea8bf5b4e813b39e381ad9e2f4/02_analysis_and_validation/p04_make_dataset_GTSM-ERA5-E_stats.py) names the file fields `wl_extreme_5perc` and `wl_extreme_95perc`. Hence the `5perc`/`95perc` names **may not reflect the actual bootstrap quantiles**. The statistical-file labels should not be silently treated as independently verified central 90% confidence bounds. The exact Zenodo producer environment/code commit has not been established.
- The subsequent [pyextremes v2.3.2 release commit](https://github.com/georgebv/pyextremes/commit/b003286e436db73e7f12c9f7c3298c05773bdf88) includes a "SciPy interval hotfix" that only changes `scipy.stats.norm.interval(alpha=alpha, ...)` to a positional call inside **`plot_mean_residual_life`**. It **does not patch** the MLE return-level interval computation, so this hotfix is not evidence of a cause for the original six-site best-fit/band crossings.
- Unlike the true native seven `wl_quantiles` labels (5, 10, 25, 50, 75, 90, 95%), the naming of the **separate fitted return-level confidence-band fields** is still a semantic research question. Do not mix up time-series percentiles, return-level intervals, event probabilities, or recurrence periods.

**Next scientific checks:** trace original execution logs/dependency lock and ask the source maintainers whether the published fields are 2.5/97.5 bootstrap bounds mislabeled as 5/95, whether they intentionally recomputed them with different `alpha`, and why source-native time-series quantiles omit the 1st/99th levels requested by the author script. None of this authorises statistical re-labelling of provider variables or commercial model admission.
