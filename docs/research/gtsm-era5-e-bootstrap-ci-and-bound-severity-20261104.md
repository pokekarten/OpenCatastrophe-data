<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GTSM-ERA5-E: historical bootstrap confidence semantics and original-bound severity QA

*Research-only original-source audit — 2026-11-04. No raw provider data included.*

## Scientific motivation

The already [verified original author-family QA](gtsm-era5-e-coastal-family-return-level-qa-20261103.md) confirmed **38,957** Zenodo original statistics rows at eight return years. Of six source station rows exhibiting an original best-fit estimate outside the reported return-level band, **five carry the producer's `id_coast_` name prefix**, accounting for 22 of the 26 reported-bound crossing cells (18 best-fit above reported upper; four below reported lower). One further grid-prefixed station has four above-upper cells. There are no inverted published intervals and no descending best-fit return-year curves. The single missing original station-period triplet occurs in the regular grid, not the coast-prefix group.

A **best-fit/percentile-band crossing is an audit symptom and not automatically an invalid point fit**: bootstrap percentiles of the simulated fitted parameter distribution need not enclose the point-estimator value. We must understand the exact statistical implementation and the size of deviations before authorizing any coastal model use.

## Historical code evidence, pinned to exact source revisions

1. The public GTSM author `environment.yml` at pinned [VU-IVM commit `30580a729be88fea8bf5b4e813b39e381ad9e2f4`](https://github.com/VU-IVM/gtsm3-era5-nrt/blob/30580a729be88fea8bf5b4e813b39e381ad9e2f4/environment.yml), Git blob SHA-1 `2029c2c6a648465b4f7922f4c0e7fab1e99731e7`, specifies **`pyextremes=2.3.1`**. This is a **checked-in environment specification**, not proof of exact historical runner package installation.
2. The pinned producer [`p01_computing_return_periods_GTSM_batch_pyextremes.py`](https://github.com/VU-IVM/gtsm3-era5-nrt/blob/30580a729be88fea8bf5b4e813b39e381ad9e2f4/02_analysis_and_validation/p01_computing_return_periods_GTSM_batch_pyextremes.py) calls **`model.get_summary(return_period=rps, alpha=0.95)`**, *without* `n_samples` or a reproducible bootstrap seed. It uses 99th-percentile POT threshold, 72h declustering and GPD MLE.
3. Historical [`pyextremes` v2.3.1 `model_mle.py`](https://github.com/georgebv/pyextremes/blob/a268301993d6be247e24c58518beb6d70f586d2a/src/pyextremes/models/model_mle.py), Git blob SHA-1 `5ce0ccf795795df0ab0fe6e933456476e5512546`, explicitly calculates confidence limits as **`np.quantile(rv_sample, [(1-alpha)/2, (1+alpha)/2])`**. Thus `alpha=0.95` selects **2.5th and 97.5th percentiles**, nominal **95% central bootstrap band**. The historical `get_return_value` defaults to **`n_samples=100`** and the bootstrap parameter sampler requests random seeds through NumPy; absent a producer seed/fit-cache state, bit-exact bootstrap CI reproduction is **not** established.
4. The pinned author [`p04_make_dataset_GTSM-ERA5-E_stats.py`](https://github.com/VU-IVM/gtsm3-era5-nrt/blob/30580a729be88fea8bf5b4e813b39e381ad9e2f4/02_analysis_and_validation/p04_make_dataset_GTSM-ERA5-E_stats.py) copies the output's `*_lower`/`*_higher` columns into variables **`wl_extreme_5perc`/`wl_extreme_95perc`**. Those variable names nominally suggest 5th/95th bootstrap percentiles (central 90%), while the historical source call and library formula suggest 2.5th/97.5th percentiles (central 95%). **A source-level semantic naming inconsistency is supported**. Do not assert the actual deposited file's interval coverage is definitively incorrect without verifying exact production runtime and source execution lineage.

If someone wants to reproduce original *bootstrap* confidence limits exactly, request the versioned 1950–2024 detrended hourly series, actual environment lock/installed package versions, random states/seed cache or saved sample parameter draws, fitting settings and exact batch outputs. Bootstrapping from the published return-level table alone cannot recreate the original stochastic parameter-fit samples or random draws.

## New in-memory, source-original severity and return-year audit

New executable `scripts/gtsm_era5_e_return_band_severity_v0.py` is run by the existing fixed-original workflow `.github/workflows/gtsm-original-author-catalogue.yml`. Its original inputs are **fully verified before numerical inspection**:

- Zenodo v2 original byte-length 9,652,424, publisher MD5 `0f2b7071c6ec3585768be6cf427e6eab`, previously observed SHA-256 `e366c79683438d03a48b23764f1159d5ed88845a459f625eeb787dff78cbd767`, plus native header/axes.
- Original publisher station catalogue at immutable author commit `30580a729be88fea8bf5b4e813b39e381ad9e2f4`, Git blob SHA-1 `07c784f401a1296bea15e7bfbd10332065dc3732`, with prior exact 38,957/38,957 ID+coordinate proof.

The audit counts **per return period (1,2,5,10,25,50,75,100 years)** × **four verified author station-name prefixes**: original best-fit above upper, below lower, and nonfinite triplets. It bins the *distance* between best fit and violated bound in **(0–0.01], (0.01–0.1], (0.1–1], >1 metres**, separately above and below. Every per-period/size category is reconciled to the established author-family original return QA and global original counts; any mismatch fails closed.

**No** source return-level value, source station row/ID, coordinate, source matrix, original author catalogue entry, per-station outlier or individual original bootstrap draw is logged, persisted to Git or copied into Neon. Only small, aggregate quality-category counts are emitted. The original files remain ephemeral and are deleted after the job.

### Interpretation and required gates

- The author station-name family `id_coast_` is **not independent physical evidence** of flood/inundation support at insured buildings.
- Absolute threshold bins only triage deviation *scale*; they do not reconstruct the original bootstrap statistic, prove 90% or 95% actual coverage, assess physical return-level calibration, or provide an independent gauge holdout.
- Source original data quality does not imply commercial use permission, vertical datum conversion to local site elevation, storm/surge event generation, ELT/YLT derivation or portfolio insured losses.
- **The actual original group-period and severity bucket counts remain pending exact-head CI**; report only verified workflow values.
- Model rights and scientific admission remain **`commercial_rights_approved=false`**, **`cat_model_admitted=false`**.

## Next falsifiable steps

1. If original crossings are mostly **small deviations relative to the published interval width**, investigate numerical tolerance, finite bootstrap samples and whether a percentile-based band must enclose MLE return point estimates; if larger, examine source fit stability and parameter bootstrap input for the coast-prefixed subset.
2. Obtain actual producer bootstrap seed/cache evidence; run independently reproducible `pyextremes 2.3.1` on *licensed, pinned* detrended hourly source data and compare 100-sample and higher-sample intervals, without substituting unverified results into the published native tables.
3. Maintain a distinct scientific escalation for the **200 coast-prefixed author catalogue sites without published statistics**: original time-series coverage/SLURM batch manifests needed, no imputation or fictitious coastal exposure.
