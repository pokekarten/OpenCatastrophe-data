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
