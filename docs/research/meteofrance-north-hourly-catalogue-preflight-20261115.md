<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Northern France 2020–2024 hourly wind original-source catalogue preflight (2026-11-15)

## Why this work exists

The already merged [Paris Météo-France original source preflight](meteofrance-hourly-original-3second-gust-preflight-v0.md) acquired and checked one department's 2020–2024 original compressed CSV, with 72,467 quality-1 `FXI3S` records, and pinned the original SHA-256. It did **not** establish geographic station completeness outside Paris, winter-storm event frequency or insurable losses. The official [Météo-France hourly department dataset](https://www.data.gouv.fr/datasets/donnees-climatologiques-de-base-horaires) lists public region/period compressed CSV resources with metropolitan UTC semantics and Open Licence 2.0 label.

This separate, one-off **metadata-only** discovery screen targets the northern mainland departments **02 Aisne, 59 Nord, 62 Pas-de-Calais, 76 Seine-Maritime, 80 Somme** during 2020–2024. These are useful station-observation candidates for cross-border North Sea/Channel storms and EIOPA Ciara/Sabine 2020 validation. No station, original data, selected storm or 3-second gust coverage is presumed from metadata alone.

## Added code and verified scientific scope

- `research_runners/meteofrance_north_hourly_catalogue_v0.py`: one public data.gouv.fr catalogue JSON fetch; scan exactly five department/period titles; require exactly one resource each; validate provider UUID, HTTPS URL host/path/period, byte cap (max 32 MiB per declared original) and global source UUID distinctness. Emit JSON only with source identifiers, declared byte sizes and digest of the public catalogue. Original measured values, source ZIP/GZIP contents, station IDs and locations are never requested, read or published.
- `tests/test_meteofrance_north_hourly_catalogue_v0.py`: offline synthetic positive and negative tests for duplicate/missing resources, swapped departments, bad periods, malicious host/parameters, invalid sizes, duplicate UUID and non-admission flags.
- `.github/workflows/meteofrance-north-hourly-catalogue.yml`: exact-branch PR metadata canary using the approved public catalogue, with no authenticated source or large provider files, and an explicit manual replay option.

Run offline `python -m unittest tests.test_meteofrance_north_hourly_catalogue_v0 -v`; for a public metadata-only canary run `python -m research_runners.meteofrance_north_hourly_catalogue_v0 --live-catalogue`. Full repo `python scripts/check_all.py` remains the definition of done.

## Science/legal gate and next action

This screen records metadata **only**. Each selected department needs its original resource bytes acquired into ephemeral authorized storage, byte-count/SHA-256 receipts, inspected source field dictionary, `FXI3S` quality/derived status, station siting/height/UTC support and matched physical event hours before comparison with CLIMK, ERA5 or C3S. Original provider bytes, signed URLs, credentials, personal data and insurer holdings must not enter Git. The catalogue remains a discovery source, not a licence or automatic production admission.

The existing full European event-frequency/OEP/AEP gate remains blocked until actual complete event/year data and dependence/weights have been independently verified. Treat WISC synthetic storms, CLIMK selected extremes and the same physical Kyrill/Ciara representation from alternative sources as **non-additive**.


## Executed official metadata catalogue (15 November 2026)

One successful targeted GitHub Actions metadata-only run:
https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43724363298
(at commit `9971d32da90f2cb51f95d108fdb6e9254c975a29`).
It parsed **3,459,822 original JSON bytes**, SHA-256
`91fb1a602842d6d7a9ec542acb004db05cecfefff0a8d5f3bc3c15e67fa029f7`.
Exactly five target resources passed. These entries are **source metadata only**,
not original observations or verified compressed-file SHA-256.

| Dept | Provider resource UUID | Original gzip filename | Publisher declared gzip bytes |
|---|---|---|---:|
| 02 | `3ae65545-9ce4-4227-a184-111bad9d0185` | `H_02_previous-2020-2024.csv.gz` | 19,437,733 |
| 59 | `414ca541-fa77-4060-b93c-44fb3a85d693` | `H_59_previous-2020-2024.csv.gz` | 15,928,750 |
| 62 | `fb9e6687-3ae8-4ed9-b106-be22db8d1fa1` | `H_62_previous-2020-2024.csv.gz` | 25,053,359 |
| 76 | `31c4683e-5538-4832-96ef-1f2568051019` | `H_76_previous-2020-2024.csv.gz` | 26,582,693 |
| 80 | `1a936a45-b6ad-4c2b-84cf-cb4c853938b7` | `H_80_previous-2020-2024.csv.gz` | 21,177,200 |

The original provider URLs share the fixed prefix
`https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/BASE/HOR/`
followed by each literal filename. No provider asset bytes are introduced
by documenting these public identifiers.

## Narrow subsequent actual-original canary

A distinct research runner `research_runners/meteofrance_nord_original_gust_v0.py`
pins exactly the **Nord 59** official provider URL, UUID, and declared byte count;
it will attempt one memory-only 15,928,750-byte original source acquisition in
a targeted, single-branch PR workflow. The original source was acquired and hashed once in GitHub Actions; its exact verified SHA-256 is now pinned in the runner for all future manual replays. This is one observed station-cohort source,
not a source-admission manifest or proof of model calibration. As with Paris,
`STATUS_FXI3S=0` does not prove instrumentation provenance; retain
missingness and station heterogeneity.

## Executed original Nord (59) station-file proof (15 November 2026)

The narrowly scoped original-data GitHub Actions job [43724594504](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43724594504) succeeded on the initial candidate execution. This is an **original provider file** (not just catalogue metadata) acquired read-only to ephemeral CI storage and never checked into Git. Five source-catalogue candidates were checked separately in [43724594540](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43724594540).

| Original source identity/QA | Observed |
|---|---:|
| Official provider department | `59` (Nord) |
| Original asset size (bytes) | 15,928,750 |
| Uncompressed CSV bytes | 142,193,945 |
| Original hourly observation rows | 419,543 |
| Distinct station IDs in original (not disclosed) | 10 |
| Nonmissing `FXI3S` + quality-1 validated | 117,487 |
| `STATUS_FXI3S=1` transfer-function-derived among validated | 1,615 |
| `STATUS_FXI3S=0` non-transfer-calculated among validated | 115,872 |
| `QFXI3S=1` (including rows without wind value) | 117,502 |
| `QFXI3S=9` filtered | 100,438 |
| Missing `QFXI3S` | 201,603 |

Original gzip SHA-256: `ee2b7254856875b5445aeaa67ea461f7e68145243bbeb2aa6cf4e5c1b36eb5e8`.
Full archive identifier: `414ca541-fa77-4060-b93c-44fb3a85d693` from the original public catalogue, basename `H_59_previous-2020-2024.csv.gz`. The exact SHA-256 is now a hard gate in the executable parser. A changed original file must fail closed and be reviewed as a new source revision, not silently overwritten. The targeted source-acquisition workflow is **manual-only** after the verified one-off run to prevent uncontrolled repeat downloads.

**Scientific limitation:** these 117,487 quality-1 gusts are not 117,487 independent storms or validated insurer losses. The source quality flag and transfer status do not prove an individual anemometer's height/exposure, station homogeneity, or wind speed equivalence to the event-conditioned CLIMK/C3S/XWS 72-hour 3-second gust maximum. No annual event population, AAL/OEP/AEP, hazard-calibration success or insurer contract reuse is claimed.
