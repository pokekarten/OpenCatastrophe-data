<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GTSM-ERA5-E — pinned-original return-level quality by publisher station family

*Research proof / 2026-11-03. Pure registry and executable research, not an admitted CAT model.*

## Goal and verified upstream inputs

The existing [GTSM return-level original audit](gtsm-era5-e-cds-lineage-and-period-qa-20261103.md) pinned to [Zenodo 14671593](https://zenodo.org/records/14671593) found **38,957** source rows × **8** return periods, one nonfinite triplet and **26 best-fit-versus-reported-bound crossings across 6 source station rows**. It did not establish whether those anomalies occurred at coast-prefixed or offshore/grid stations.

The subsequent independently verified [author catalogue join](gtsm-era5-e-original-author-station-overlap-20261103.md) showed the source IDs and packed source coordinates match **all 38,957** corresponding entries in the 43,119-row author catalogue from [VU-IVM commit `30580a7`](https://github.com/VU-IVM/gtsm3-era5-nrt/tree/30580a729be88fea8bf5b4e813b39e381ad9e2f4/04_supplementary_data). Of those entries **18,514** have original `id_coast_` name prefix, **17,598** `id_reg_grid_`, **416** `id_obs_` and **2,429** other source names. These are manufacturer/producer labels, **not** independent inundation footprint or land-proximity classification.

The [100-ID batch coverage challenge](gtsm-era5-e-author-batch100-lineage-20261103.md) further proved that all 4,162 catalogue IDs without a published statistic occur in **47 entirely statistics-empty numerical 100-ID bins**, not scattered within already populated bins. The actual producer batch-file manifest and job logs remain unavailable; this does not prove missing jobs.

## New executable original-data QA

A new, wholly read-only `scripts/gtsm_era5_e_author_family_return_qa_v0.py` cross-classifies original `wl_extreme_bestfit`, `wl_extreme_5perc`, `wl_extreme_95perc` from the **exact 9,652,424-byte pinned original Zenodo file**, *after* verifying file-size, publisher MD5, independently pinned SHA-256 `e366c79683438d03a48b23764f1159d5ed88845a459f625eeb787dff78cbd767`, native axes and scalar period labels. The author catalogue is independently downloaded at immutable commit `30580a729be88fea8bf5b4e813b39e381ad9e2f4` and fully matched to Git blob SHA1 `07c784f401a1296bea15e7bfbd10332065dc3732` before interpreting a station's family.

The QA runs the existing **unchanged original per-station return-level checker** once for all source rows and once for each original author name-family. Counts include source rows, finite/nonfinite triplets, inverted reported bounds, best-fit below/above the reported bounds, descending best fit across consecutive periods, and station rows with any anomaly. It independently reconciles **every aggregate category** back to the original full-source QA receipt from the established workflow. Mixed/missing family identities or mismatched aggregate totals fail closed.

The procedure emits only **four group-level counts** and already-public global QA totals: never provider-return-level values, source station IDs, coordinates, per-station exception rows, raw arrays, copied source CSV/NetCDF, or catalogue entries. Both original inputs are ephemeral. No Neon write, no exposure join.

### Scientific caveats and pending exact-run result

- Historical authors' Python [`pyextremes` `alpha=0.95`](https://github.com/VU-IVM/gtsm3-era5-nrt/blob/30580a729be88fea8bf5b4e813b39e381ad9e2f4/02_analysis_and_validation/p01_computing_return_periods_GTSM_batch_pyextremes.py) implies nominal central 95% bootstrap return-level confidence intervals with 2.5%/97.5% tails in historical pyextremes 2.3.1. NetCDF variable names `5perc`/`95perc` are **not proof** of central 90% bounds. Do not relabel native fields without exact producer revision evidence.
- A best-fit estimate appearing outside the reported bound is a QA diagnostic, **not** proof of source error, model unfitness, flood depth or insured catastrophe loss.
- The exact-head two-original CI must complete before publishing any group-level original anomaly counts. The full repository CI, Berlin flood regression and source-original comparison all have to pass before merge.
- Physical coastline/geoid/DEM, independent gauge validation, statistical-producer batch logs, complete historical CRS/source coverage, commercial reuse and catastrophe model admission remain **unresolved**.

**Flags:** `physical_coastal_cat_model_validated=false`, `source_commercial_rights_approved=false`, `cat_model_admitted=false`.
