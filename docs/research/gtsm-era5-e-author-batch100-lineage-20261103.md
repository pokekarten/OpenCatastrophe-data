<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GTSM-ERA5-E: 100-ID batch provenance and source coverage challenge (2026-11-03)

## What the original author scripts actually do

The 2025 GTSM-ERA5-E original statistical release [Zenodo 14671593](https://zenodo.org/records/14671593) is **38,957** native statistics stations and is now proven by the independently pinned producer catalogue (GitHub commit `30580a729be88fea8bf5b4e813b39e381ad9e2f4`) to share exactly the **same native IDs and 0.001-degree packed coordinates at all 38,957 stations**; the catalogue has 43,119 records, 4,162 additional records without published statistics, and 615 integer IDs absent in both catalogues within the occupied original-ID span. The author catalogue itself does **not** establish the same-vintage paper's 44,734 hydrodynamic output-location count.

The authors' [SLURM batch runner](https://github.com/VU-IVM/gtsm3-era5-nrt/blob/30580a729be88fea8bf5b4e813b39e381ad9e2f4/02_analysis_and_validation/p01_sbatch_compute_EVA_GTSM.sh) declares `step=100`, uses station-ID ranges `start..start+99`, and in this *version of the script* iterates `{0..1800..100}`. That source demonstrates the 100-ID processing design **but not a complete production manifest** for the 43,119 producer catalogue IDs.

The authors' [station EVA code](https://github.com/VU-IVM/gtsm3-era5-nrt/blob/30580a729be88fea8bf5b4e813b39e381ad9e2f4/02_analysis_and_validation/p01_computing_return_periods_GTSM_batch_pyextremes.py) generates a `ds_GTSM-ERA5_1950_2024_stations_<first>-<last>_eva.csv` for each source-selected station-range and a corresponding `_stats.nc`. It iterates all native station IDs present in each filtered source range. It calls `pyextremes.EVA` for each station; no per-station `try/except` around failed fits is visible in this current source. This is a reproducibility risk, **not evidence any specific station fit failed**.

The authors' [p04 public release assembler](https://github.com/VU-IVM/gtsm3-era5-nrt/blob/30580a729be88fea8bf5b4e813b39e381ad9e2f4/02_analysis_and_validation/p04_make_dataset_GTSM-ERA5-E_stats.py) uses `glob.glob('ds_GTSM-ERA5_1950_2024_stations*eva.csv')`, sorts existing filenames, concatenates the CSVs, and derives the NetCDF inputs from **those observed filenames**. There is no expected-batch-count/complete-coverage guard in the checked assembly code. Therefore a file excluded from the input directory could be silently omitted from the assembled output. This is a **possible mechanism**, not proof that the actual 2025 Zenodo data had omitted or failed batches.

## Why we need the 100-ID coverage audit

The independently reproducible original native ID audit found 4,777 integer labels unrepresented *within* the occupied 43,734-ID span (in 76 runs), including **two exactly 2,200-ID gaps** and **three exactly 100-ID gaps**. A matched original-author catalogue contains **4,162** of those labels, while **615** IDs are absent in both sources. In particular, only **200** out of **18,714** author records bearing `id_coast_` station-name prefix have no statistic. These are genuine original-pair metadata facts, but a raw ID gap is neither a coast polygon nor proof of a failed process.

The new `audit_hypothetical_100_id_batches` function checks **zero-origin numerical ID bins of 100 labels** within the actual original source ID span. It counts bins with 100 statistics, partial statistics, zero statistics despite 100 author catalogue entries, zero statistics with some catalogue entries, and bins entirely empty in both. It also counts unrepresented-ID runs with lengths divisible by 100 and the subset actually aligned with exact `0..99` / `100..199` index boundaries. **No batch-start ID, native station ID, station name, coordinate or row-level data is emitted.**

The original-author dual-source workflow verifies both complete files first: fixed **Zenodo SHA256** `e366c79683438d03a48b23764f1159d5ed88845a459f625eeb787dff78cbd767` and author catalogue **Git blob SHA1** `07c784f401a1296bea15e7bfbd10332065dc3732`. Only after source hashes, structure and source-to-author ID mapping pass is the 100-ID aggregate diagnostic produced.

## Do not make these unsupported inferences

- A **100-label ID bin** is not guaranteed to be exactly one historical producer job: the public SLURM script is a partial example and input data may skip IDs.
- An author catalogue entry without a statistic is not necessarily a *failed job*: may be excluded by source coverage, missing time-series, numerical fitting limitations, sampling conventions, differences in internal processing vintage or explicit filtering not published in this snapshot.
- `id_coast_` is a **publisher naming convention**, not ground-truth of coastal flood model validity, vertical datum harmonization, building support, defensibility of synthetic insurance loss models or commercial permission.
- The 44,734 published hydrodynamic model-location figure must not be conflated with the verified 43,119-row author catalogue or extrapolated to the 38,957 statistics stations.

## Research tasks after the batch diagnostic

1. Require the original actual 1950–2024 production-job inventory/manifest for the `period_1950_2024_1hr_v4` folder, exact `_eva.csv` and `_stats.nc` file list and any missing retry/failure logs, together with a source-specific station selection filter. These runtime artifacts are **not present in this public author GitHub snapshot**.
2. Resolve the 43,119 author versus 44,734 paper catalogue release/vintage mismatch with a separately hashed complete model output-point table.
3. Verify 200 missing `id_coast_` names with the actual original station selection source, supporting temporal coverage and independent gauge evidence (no synthetic fill).
4. Keep `commercial_rights_approved=false`, `cat_model_admitted=false`, no raw station data in GitHub or Neon and no producer-loss/YLT extrapolation.

**Status:** Automated 100-ID original-dataset results are pending exact-head GitHub Actions; do not invent them or call the source production archive complete.


## Verified original two-source numeric block result (2026-11-03)

The exact original [GitHub Actions run 41713279553](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41713279553), job `126186620451`, passed **17 synthetic/offline tests** and verified the original source bytes (Zenodo SHA-256 `e366c79683438d03a48b23764f1159d5ed88845a459f625eeb787dff78cbd767`, author Git blob SHA-1 `07c784f401a1296bea15e7bfbd10332065dc3732`). It produced these **actual** aggregate counts for **437 complete numeric 100-ID bins** inside the known source ID range:

| Hypothetical 100-ID bin class | Count |
| --- | ---: |
| All 100 station IDs present in source statistics | **364** |
| 1–99 station IDs present in source statistics | **26** |
| No statistics, all 100 station IDs in author catalogue | **31** |
| No statistics, some station IDs in author catalogue | **16** |
| No statistics and no author catalogue IDs | **0** |
| **Total** | **437** |

The 437 complete bins contain **38,923** statistics source IDs and **43,085** author catalogue IDs. The remaining final partial 34-ID bin (excluded from complete-bin analysis by design) has **34** source and **34** author IDs, so the entire author-only difference **43,119 − 38,957 = 4,162** occurs inside complete 100-ID bins. The 31 source-empty but catalogue-full bins account for **3,100** absent statistics; the 16 source-empty partially catalogue-populated bins account for the other **1,062** absent statistics. The independent, exact-head [follow-up GitHub original-source run 41713660098](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41713660098), job `126187951938`, passed **18 synthetic/offline tests** and repeatedly verified the exact Zenodo SHA-256 and author Git blob. It explicitly reports **zero author-only catalogue station IDs in any 100-ID bin containing existing statistical rows** and **zero source-nonempty bins with extra catalogue IDs**. In contrast, *all* 4,162 catalogue-only station IDs occur within the 47 completely source-statistics-empty 100-ID bins. This establishes the blockwise source coverage pattern for the **two pinned files**, but does **not** reveal the producer's actual job history, why bins are absent, or whether omission was intentional.

The original statistics' two 2,200-ID and three 100-ID missing native-ID runs are **all exactly aligned on zero-origin 100-ID numerical boundaries**, totaling **4,700** missing integer labels. The remaining **77** internal labels are separately not represented in the native statistics. This alignment is striking but does **not** prove the original processing batches ran from exactly those ID boundaries, or whether exclusion was intentional. The existing original/author pair proves source ID+coordinate lineage of the *present* 38,957 statistical rows; the cause of the *absent* 4,162 is still unresolved.

### Concrete next reproducibility gate

**Do not impute** any absent author catalogue station's hazard statistic. Seek a source-producer 1950–2024 manifest for expected numeric 100-ID batches, checksums and row counts of each `_eva.csv` and `_stats.nc`, Slurm job IDs/exit statuses, and the source-time-series station coverage and missingness/fitting log. Match and reconcile those originals to the existing independently hashed two-source receipt, then review the 200 `id_coast_`-prefix gaps. Only then can an omitted producer batch or systematic exclusions be asserted, and no author coordinate/name or raw provider losses should be copied to the public data register.
