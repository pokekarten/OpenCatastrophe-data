<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Blue Heart — original rain/sewer archive path crosswalk and a synthetic lag challenge

**Review date:** 2026-11-10. **Scope:** source index/ZIP central-directory **metadata** and deterministic **synthetic-only** model contract. **Not:** original observational loss, insurer model validation, accepted exposure/hazard, real telemetry calibration, or a CAT event set.

## What was checked on original Zenodo v1.0 assets

Blue Heart provider record: [Zenodo 20699635](https://zenodo.org/records/20699635), [record API](https://zenodo.org/api/records/20699635), concept DOI `10.5281/zenodo.20699634`; exact version `v1.0`, record metadata `access_right=open`, `license.id=cc-by-4.0`. The separate [original index evidence](blue-heart-original-readme-temporal-qc-preflight-20261110.md) documents the complete **117,300-byte** `index_telemetry_data.csv`, source SHA-256 `44d53fe95e70cd3665678aec469666c1b22b3323c52424d9838ee5a6d24c4f40`.

Two original ZIP end-of-central-directory structures and their file name tables were checked using **finite, unauthenticated HTTP Range reads** of the official Zenodo source URLs. Requested original asset bytes are intentionally not committed:

| Original provider ZIP | Provider file size | Original bounded bytes examined | ZIP entries | Expected index pairing |
| --- | ---: | ---: | ---: | --- |
| `7_rain_gauge_telemetry_data.zip` | 4,792,692 | last 8,192, including complete 3,988-byte central directory starting at 4,788,682 | 31 | 15 original rain data paths + 15 QC paths |
| `5_sewer_telemetry_data.zip` | 230,886,258 | 112,901 contiguous trailing bytes, including complete 112,879-byte central directory starting at 230,773,357 | 797 | 398 original sewer data paths + 398 QC paths |

The source index's **15/15 rain** and **398/398 sewer** rows were matched by their original relative `dataPath` and `dataQualityFlagsPath` against the corresponding original ZIP central-directory members in memory:

- **826/826** total relative file references resolve; **0** missing and **0** ZIP CSVs unreferenced by the relevant gauge class.
- ZIPs each have one root directory marker; no duplicate filenames, source-directory unsafe paths, encrypted entries or unsupported compression-method IDs were identified in this bounded inventory.
- The original ZIP directory claims **55,829,344** total uncompressed member bytes for the rain archive, and **2,259,048,769** for the sewer archive; these are unverified provider-archive **header claims**, not the number of bytes extracted. Largest ZIP member size from source directory: rain **2,387,872 bytes**, sewer **4,910,242 bytes**.
- The rain ZIP central directory is **3,988 bytes**, the sewer ZIP central directory **112,879 bytes**. All source member identities were used only in-memory to compare to the source index: no raw names, individual coordinates, index rows, sample records, ZIP files, signed links or member bytes were committed to public GitHub.

**Evidence boundary:** Source URL and record identity remain version-bound; the original archive ZIP MD5, full-object SHA-256, decompression CRC, source time-series measurement values, QC pass fractions, clock conventions, sampled time windows, inter-sensor independence and original response lag **were not verified**. A correct ZIP directory and source index link are file-discovery evidence, not proof that any real timeseries can be aligned or used commercially without separate rights review.

## Aggregate spatial reach of the rain gauges (original published index)

Using the **same original 117,300-byte, 497-row v1.0 index**, a bounded in-memory read extracted only the 15 Rain and 398 Sewer latitude/longitude fields. For each of the 398 sewer stations, the shortest *spherical great-circle (Haversine)* distance to any of the 15 rain gauges was computed; output is **aggregate-only**, rounded to 0.1 km. Coordinates are taken at face value as geographic degrees; exact survey/CRS accuracy, altitude, drainage direction and the true rainfall footprint were not established.

| Geometric relationship from original index | Result |
| --- | ---: |
| Nearest rain gauge within 250 m of a sewer gauge | 42/398 (10.6%) |
| Within 500 m | 123/398 (30.9%) |
| Within 1 km | 313/398 (78.6%) |
| Within 2 km | 386/398 (97.0%) |
| Within 3 km | 398/398 (100.0%) |
| Nearest-rain distance median | approx. 0.7 km |
| 90th percentile | approx. 1.4 km |
| 95th percentile | approx. 1.8 km |
| Maximum | approx. 2.2 km |

The minimum distance rounds to **0.0 km**; this is only rounding, **not** a claim of precisely colocated instruments. These results show many *geometrically nearby* rain-to-sewer candidate pairs and help predefine a later stratified spatial holdout. They **do not** prove simultaneous time-series availability, rainfall representativeness, causal drainage linkage, source timezone integrity, or experimental independence. Adjacent sewer sites may share catchment, forcing and infrastructure; avoid treating each of the 398 as an independent storm replication.

No individual station coordinates, identifiers, nearest-neighbour pairings or raw index rows were emitted, included in this document or added to Git. This does not alter privacy, source-admission or insurance modelling gates.

## A minimal synthetic model contract

Implemented in `research_runners/blue_heart_synthetic_rain_sewer_lag_v0.py` with tests `tests/test_blue_heart_synthetic_rain_sewer_lag_v0.py`. Invoke from repository root:

```bash
python -m research_runners.blue_heart_synthetic_rain_sewer_lag_v0 --synthetic-demo
python -m unittest tests.test_blue_heart_synthetic_rain_sewer_lag_v0 -v
```

The command accepts **no downloaded observation or insured-loss input**, generates two internally constructed and chronologically separate synthetic event windows, and emits only an aggregate JSON result. Parameter choices are demonstration fixtures, **not observed Blue Heart coefficients**. The software gate uses:

1. Five-minute, offset-aware UTC samples and exact per-step precipitation depth in `mm_per_5_minutes`; sewer water level in `mm`, **not** `mAOD` or depth per hour.
2. Explicit `QC=1` at every input timestep; any suspect/bad/missing QA, unknown units, raw naive timestamps, time gaps, invalid values, dry periods, or non-stationary initial baseline fail closed. The strict all-good rule is a conservative **software demonstration**, not a justified real-data exclusion policy.
3. One pre-specified first-order response factor `decay=0.55` and training-only lag candidates **0, 5, 10, 15, 20 minutes**. Fit only one synthetic gain per lag from the first event's causal increment equation `(level_t-baseline) - decay*(level_(t-1)-baseline) = gain * rain_(t-lag)`; choose the lowest training RMSE.
4. Holdout **different synthetic event** scored with unchanged selected lag, decay and gain; no holdout-based fitting. Report train and independent holdout response errors in **millimetres of sewer level**, not hazard depths, property damage or loss return periods.
5. Hard negative scientific status fields: `original_blue_heart_telemetry_used=false`, `device_timezone_verified=false`, `real_hydraulic_calibration_completed=false`, `cat_event_set_or_insurer_loss_admitted=false`.

The tests prove no accidental conversion of an unverifiable *highway gully* device-clock reading to UTC, and that this separate rain/sewer software path does **not** waive original rain/sewer logger time-source verification. The synthetic reservoir is deliberately simple: it omits spatial rainfall representativeness, drainage-network topology, physical sensor calibration, water-level thresholds, antecedent soil moisture, observations beyond the demonstration window, nonlinearity, missingness-aware estimation and uncertainty.

## Scientific next step

1. Confirm exact interpretation of the original **rain and sewer** raw timestamps and per-variable QA codes from one license-cleared gauge pair. Offset-bearing *syntax* alone does not prove physical clock correctness.
2. Retrieve a **small, version-pinned and rights-cleared source-local sample** outside Git, verify provider full-file byte identity, CRC, source variable units and timestamp/QC row correspondence, and document its temporal coverage. Do not publish sensor names, coordinates, network layouts or underlying telemetry.
3. Predefine a held-out time window and event-selection rule *without* looking at sewer-level outcomes, then compare a physical/simple baseline model to training/holdout results. Report coverage, missing and suspect rates, event count and uncertainty. Only then consider hydrological calibration.
4. Keep annual exceedance/occurrence (AEP/OEP), insured-loss estimation, location-level exposure use and real source admission separate from this synthetic lag exercise.

**Status:** bounded metadata and synthetic challenge only; source rights, scientific review and admission remain `not_reviewed` / `not_reviewed` / `not_admitted`.
