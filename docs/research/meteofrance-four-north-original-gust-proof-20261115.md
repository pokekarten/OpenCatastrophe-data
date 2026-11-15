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
- Original SHA-256 identifiers in the initial source code are explicitly **unset** until each file is acquired. Successful official one-off runs must be captured with exact source bytes and SHA-256; only then pin the reviewed file hashes and change this source workflow to manual-only.
- Original source evidence is **not** a legal admission or model fitness proof. Source rights, historical gust corrections, station siting changes, sensor height, 3-second versus instantaneous gust semantics and independent source agreement all remain scientific gates.

**Model boundary:** No catalogue document or annual storm event completeness has been proved. Do not treat 2020–2024 station-hour samples as independent catastrophe events or use these alone to calculate AAL/OEP/AEP/RI. Reference provider dataset [data.gouv.fr hourly Météo-France](https://www.data.gouv.fr/datasets/donnees-climatologiques-de-base-horaires) under Open Licence 2.0, subject to a documented exact-source review.
