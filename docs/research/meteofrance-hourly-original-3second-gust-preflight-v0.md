<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Météo-France original hourly 3-second gust preflight (14 November 2026)

## Source and exact documented physics

Original official dataset: https://www.data.gouv.fr/datasets/donnees-climatologiques-de-base-horaires; official public field dictionary: https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/BASE/HOR/H_descriptif_champs.csv. Licensing label: Etalab Licence Ouverte 2.0 with Météo-France attribution. Neither the metadata API nor this document establishes that individual downloaded rows are independent, instrument-unmodified 3-second gusts.

The original dictionary **actually enumerates** `FF` = 10-minute averaged 10 m wind, `FXI` = instantaneous hourly maximum at 10 m, and `FXI3S` = hourly peak of 3-second averaged wind (m/s and 0.1 m/s units). `STATUS_FXI3S=1` means estimated by a transfer function; `0` means *not so calculated*, **not** proof of instrumental direct measurement. `QFXI3S=0/1` indicate protected/validated while `2` doubtful and `9` pre-filtered require separate handling. Station relocation, instrument siting, time coverage, quality flags and missingness must be checked before comparing to CLIMK, XWS, ERA5 or C3S 3-second gust definitions. Mainland hourly times are UTC, unlike some overseas series.

## Executable acquisition and model boundary

`research_runners/meteofrance_hourly_gust_v0.py` can download public, unauthenticated official bytes **only for one fixed test profile**: `HOR_departement_75_periode_2020-2024` / `H_75_previous-2020-2024.csv.gz`. It first resolves the official `data.gouv.fr` catalogue resource, validates a bounded downloaded field dictionary, caps compressed/inflated bytes and CSV rows, checks station/hour schemas, and reports only SHA-256 of the original compressed file, aggregates of data coverage/quality and permanent NO-to-admission flags. It does **not** commit or upload original observations, attach source files to CI artifacts, store station IDs, or claim annual EP, measured gust equivalence, or property damage. Original resource absence, changed title, unsafe redirect, missing quality or implausible data should fail closed. The separate CI workflow runs offline synthetic tests for PRs. **Original provider retrieval is manual-only via `workflow_dispatch`**; the already successful original-source run `43632969638` is the frozen reference. PR updates do not automatically download the 9 MB source again.

Execute:

```bash
python -m unittest tests.test_meteofrance_hourly_gust_v0 -v
python -m research_runners.meteofrance_hourly_gust_v0 --live
```

The second command requires a public-network-enabled host such as GitHub Actions. An offline original `--original-gz /private/H_75_previous-2020-2024.csv.gz --expected-sha256 <sha256>` is also supported. A failed live run is evidence of a live access/schema block, not proof that data do not exist. This is a research-level preflight and does not change `manifests/` or source-admission state.

**Next scientific gate:** pin the precise official file metadata/release and observed source SHA-256, select a complete physical storm time window (Ciara/Sabine 2020), identify station-specific measured vs derived `FXI3S` availability, pair model grid support and station siting, and perform a held-out bias/tail check before ingesting any fitted response or annual loss model.

**Observed live provider identity:** the official resource selected under catalogue title `HOR_departement_75_periode_2020-2024` links to the *different literal filename* `H_75_previous-2020-2024.csv.gz`, verified by an authenticated-by-none public CI metadata request on 2026-11-14. That filename is now frozen in the audit rather than inferred from the title; the file's actual observation period and format remain to be checked by source-byte execution.

## Executed original provider evidence (14 November 2026)

GitHub Actions original-source run: https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43632969638, exact input commit `524478e5e9f0881a604d96d683b4f95c90768337`. The targeted original-gust job and six offline tests **passed**. Original compressed bytes were downloaded into ephemeral CI memory, read, fully hashed and discarded; only non-location-specific aggregated counters and public asset digests are retained in the run log and this report. This proves the exact chosen original file could be acquired and parsed **on this run**, not that every station or variable is eligible for physical hazard calibration.

| Original source receipt | Observed value |
|---|---:|
| Official catalogue title | `HOR_departement_75_periode_2020-2024` |
| Actual source basename | `H_75_previous-2020-2024.csv.gz` |
| Original resource UUID | `a77b4d44-d361-4e59-b6cc-cbbf435a2d89` |
| Original compressed source bytes | 9,084,848 |
| Decompressed UTF-8 semicolon CSV bytes | 87,595,960 |
| Rows | 261,860 |
| Unique station identifiers, not published | 6 |
| Nonmissing `FF` | 130,061 |
| Nonmissing `FXI` | 130,064 |
| Nonmissing `FXI3S` | 130,068 |
| `FXI3S` quality code 1 | 72,467 |
| `FXI3S` quality code 9 | 57,601 |
| Missing `FXI3S` quality code | 131,792 |
| Validated `FXI3S` with `STATUS_FXI3S=1` (transfer-derived) | 10,025 |
| Validated `FXI3S` with `STATUS_FXI3S=0` (not transfer-calculated) | 62,442 |

Original compressed SHA-256: `8d0b0d7cded68110d1e755a085cd5b96956e80b822c81950969bd21ff97b9d76`. Original field-dictionary SHA-256: `1ff2c0febb4a040bf8b400e422bc2bf3e9b8c3e48bdda73a67b1790c532021da`. Dataset-catalogue JSON SHA-256 at request: `d7a205bcc20b115169e3a02a4ffa71cf54bc06d70c273165437e0682bce34277`.

**Strict limitations:** only one Paris-region department and historical period; the quality counts do not establish independent, homogeneous measurement physics, event completeness, sensor heights, actual provider raw byte redistribution rights for Git, a matched Ciara loss observation, or frequency/return-period calibration. In particular, source `STATUS_FXI3S=0` is not an instrument-level provenance attestation. Preserve all `not_admitted` and `annual_ep_authorized=false` flags.


## Post-receipt integrity hardening

The exact verified 2026-11-14 receipt now **pins** all three original-source identifiers in executable code: resource UUID `a77b4d44-d361-4e59-b6cc-cbbf435a2d89`, the literal publisher object `H_75_previous-2020-2024.csv.gz`, compressed file length **9,084,848 bytes**, and full original SHA-256 `8d0b0d7cded68110d1e755a085cd5b96956e80b822c81950969bd21ff97b9d76`. If any changes, this version fails closed pending an explicit reviewed reissue rather than silently treating changed original observations as the same sample.

All HTTP redirects are rejected **before** a second destination request can be sent. This prevents a compromised or mutable public catalogue URL from redirecting the runner to an unapproved network host. The original provider proof was already completed in GitHub run 43632969638; this tightening does not claim to have re-downloaded or verified a later provider version. Future network probes are manual-only; offline PR tests check tampering and rejected redirects.

The existing source-access contract for Météo-France still has `probe_contract.mode=none` and `commercial_automation_status=unknown`: the experimental manual source receipt does not grant an unrestricted scheduled transport entitlement, commercial model admission or a full European storm catalogue.
