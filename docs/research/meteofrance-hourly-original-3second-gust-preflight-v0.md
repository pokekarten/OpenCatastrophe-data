<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Météo-France original hourly 3-second gust preflight (14 November 2026)

## Source and exact documented physics

Original official dataset: https://www.data.gouv.fr/datasets/donnees-climatologiques-de-base-horaires; official public field dictionary: https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/BASE/HOR/H_descriptif_champs.csv. Licensing label: Etalab Licence Ouverte 2.0 with Météo-France attribution. Neither the metadata API nor this document establishes that individual downloaded rows are independent, instrument-unmodified 3-second gusts.

The original dictionary **actually enumerates** `FF` = 10-minute averaged 10 m wind, `FXI` = instantaneous hourly maximum at 10 m, and `FXI3S` = hourly peak of 3-second averaged wind (m/s and 0.1 m/s units). `STATUS_FXI3S=1` means estimated by a transfer function; `0` means *not so calculated*, **not** proof of instrumental direct measurement. `QFXI3S=0/1` indicate protected/validated while `2` doubtful and `9` pre-filtered require separate handling. Station relocation, instrument siting, time coverage, quality flags and missingness must be checked before comparing to CLIMK, XWS, ERA5 or C3S 3-second gust definitions. Mainland hourly times are UTC, unlike some overseas series.

## Executable acquisition and model boundary

`research_runners/meteofrance_hourly_gust_v0.py` can download public, unauthenticated official bytes **only for one fixed test profile**: `HOR_departement_75_periode_2020-2024` / `H_75_2020-2024.csv.gz`. It first resolves the official `data.gouv.fr` catalogue resource, validates a bounded downloaded field dictionary, caps compressed/inflated bytes and CSV rows, checks station/hour schemas, and reports only SHA-256 of the original compressed file, aggregates of data coverage/quality and permanent NO-to-admission flags. It does **not** commit or upload original observations, attach source files to CI artifacts, store station IDs, or claim annual EP, measured gust equivalence, or property damage. Original resource absence, changed title, unsafe redirect, missing quality or implausible data should fail closed. The separate CI workflow deliberately runs original retrieval only on the specific PR paths or manually.

Execute:

```bash
python -m unittest tests.test_meteofrance_hourly_gust_v0 -v
python -m research_runners.meteofrance_hourly_gust_v0 --live
```

The second command requires a public-network-enabled host such as GitHub Actions. An offline original `--original-gz /private/H_75_2020-2024.csv.gz --expected-sha256 <sha256>` is also supported. A failed live run is evidence of a live access/schema block, not proof that data do not exist. This is a research-level preflight and does not change `manifests/` or source-admission state.

**Next scientific gate:** pin the precise official file metadata/release and observed source SHA-256, select a complete physical storm time window (Ciara/Sabine 2020), identify station-specific measured vs derived `FXI3S` availability, pair model grid support and station siting, and perform a held-out bias/tail check before ingesting any fitted response or annual loss model.
