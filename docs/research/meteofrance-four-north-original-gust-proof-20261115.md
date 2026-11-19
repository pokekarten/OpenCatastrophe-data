<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Four new exact Météo-France hourly wind originals: source receipts and boundaries

**Review date:** 2026-11-15. Four previously catalogue-confirmed northern original weather products (02 Aisne, 62 Pas-de-Calais, 76 Seine-Maritime, 80 Somme) are tested as four separate, precise provider assets. This extends the merged [five-department catalogue and Nord-59 original](meteofrance-north-hourly-catalogue-preflight-20261115.md). They are all from **one provider/source family**, not independent science models.

| Department | Original Météo-France UUID | Declared source bytes |
|---|---|---:|
| 02 | `3ae65545-9ce4-4227-a184-111bad9d0185` | 19,437,733 |
| 62 | `fb9e6687-3ae8-4ed9-b106-be22db8d1fa1` | 25,053,359 |
| 76 | `31c4683e-5538-4832-96ef-1f2568051019` | 26,582,693 |
| 80 | `1a936a45-b6ad-4c2b-84cf-cb4c853938b7` | 21,177,200 |

All URL identities use the canonical original path `https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/BASE/HOR/H_DD_previous-2020-2024.csv.gz` replacing DD with the explicit department.

## Execution and scientific access gate

- The code `research_runners/meteofrance_four_north_original_v0.py` requires exact catalogue UUID, source HTTPS URL and publisher declared compressed-byte count for each explicit department. It retrieves the official FF/FXI/FXI3S dictionary before treating any physical variables as equivalent.
- Each one-off PR canary runs a separate bounded source acquisition (at most 32 MiB compressed per department); streaming gzip decompression has a **384 MiB total-inflation cap**; CSV validity, 1.6 million row bound, source-department station prefix, precise UTC 2020–2024 timestamps, numeric 0–120 m/s wind cap, FXI3S quality and reconstructed-vs-not-reconstructed status are checked. Station identities/coordinates, original rows, credentials, source bytes and insurer assets are never printed, committed or uploaded.
- **Completed source proof:** the four exact original file hashes were successfully observed in GitHub Actions run 43727037428 and are pinned in executable source constants. Future mismatched original bytes fail closed. The source workflow is now **manual-only** to avoid unintended repeat downloads.
- Original source evidence is **not** a legal admission or model fitness proof. Source rights, historical gust corrections, station siting changes, sensor height, 3-second versus instantaneous gust semantics and independent source agreement all remain scientific gates.

**Model boundary:** No catalogue document or annual storm event completeness has been proved. Do not treat 2020–2024 station-hour samples as independent catastrophe events or use these alone to calculate AAL/OEP/AEP/RI. Reference provider dataset [data.gouv.fr hourly Météo-France](https://www.data.gouv.fr/datasets/donnees-climatologiques-de-base-horaires) under Open Licence 2.0, subject to a documented exact-source review.

## Executed source-original receipts — 15 November 2026

GitHub Actions [run 43727037428](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43727037428) ran four independent successful source-original jobs. Each job inspected the official catalogue, data dictionary and entire original compressed station-hour CSV with exact source-UUID/URL/size checks. No raw original data, station locations or station IDs were committed, logged or uploaded.

| Dept | Original gzip bytes | Uncompressed CSV bytes | Hourly rows | Distinct IDs | Quality-checked FXI3S | Derived by transfer | Not transfer-derived |
|---|---:|---:|---:|---:|---:|---:|---:|
| 02 | 19,437,733 | 175,116,916 | 521,959 | 14 | 103,063 | 3,334 | 99,729 |
| 62 | 25,053,359 | 208,462,760 | 600,799 | 15 | 195,264 | 7,408 | 187,856 |
| 76 | 26,582,693 | 241,136,823 | 710,551 | 24 | 227,932 | 6,601 | 221,331 |
| 80 | 21,177,200 | 212,497,199 | 645,870 | 18 | 133,433 | 7,804 | 125,629 |

Exact original compressed SHA-256 receipts, now pinned in `ASSETS`:

- `02`: `4c093caad74f854612485504d6d21ba67c7879e4d005e6b51ca6d1acb2b017e3` (successful GitHub job `132851119512`)
- `62`: `12a33b7c67f703aad2bcc95c06d91b81cb8e2cba95738da7e9bbb7971a81db7f` (successful GitHub job `132851119752`)
- `76`: `406dbf752f042254bfade674f606c2035eeb2560d06314324c9bd4694936780d` (successful GitHub job `132851119807`)
- `80`: `1d46879bd4c3ba1180b881cfb28eacccc4e8a5405e783bdc09ab5dae5418124f` (successful GitHub job `132851119921`)

The **71 file-specific station IDs, 2,479,179 station-hour rows, and 659,692 quality-checked FXI3S values** are descriptive source counts, *not* 659,692 independent storms or complete annual event sets. With earlier Paris (75) and Nord (59) original receipts, six separately hash-verified departmental assets yield 849,646 quality-checked FXI3S rows. No source is admitted to commercial hazard calibration or insurer loss modelling; station siting/instrument lineage, seasonal event selection, licence review, and storm model comparison are still outstanding.
