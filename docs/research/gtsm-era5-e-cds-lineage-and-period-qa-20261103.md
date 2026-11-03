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

`scripts/gtsm_era5_e_return_level_qa_v0.py` now partitions these aggregate counters by each of the eight **native source return-year** labels (1/2/5/10/25/50/75/100 years), together with nonfinite counts by variable. The aggregated period labels will help identify whether apparent bounds discrepancies are concentrated in longer return periods without leaking individual modelled water levels or original coordinates. Tests enforce exact reconciliation to global totals. The **new** per-period counts cannot be asserted until the exact-head original-source GitHub workflow completes; do not assume any distribution from the six flagged station rows.

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
