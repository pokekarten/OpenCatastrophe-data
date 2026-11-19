<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Independently repeated synthetic 10k SQL receipt — 2026-11-03

**Scope and security:** Executed both original `PR #1081` SQL files **read-only** on Neon
`insurance-risk-core`, database `insurance`, isolated validation branch
`validation-schema-20261031` (`br-summer-sky-bawujqu8`), never the
default/production branch. GitHub PR-head at execution:
`27648fc968753e265b43517f4965fbc84d00b4ef`.

| Original query | Git blob SHA (original GitHub bytes) |
| --- | --- |
| `research_runners/sql/neon_synthetic_gul_10k_v0.sql` | `23f0df69d1e8095bfad6febb7dc9baa0039396f4` |
| `research_runners/sql/neon_synthetic_gul_10k_row_receipts_v0.sql` | `a4647b6c2e4092661fea8ba9258081038e504413` |

## Live PostgreSQL results

- Synthetic locations: **12** exactly, wholly fictional replacement-value proxies **EUR 3,150,000**.
- Annual simulation worlds: **10,000**. Fake windstorm events **1,008**, flood events **533**, total **1,541**, zero-event years **8,509**.
- Asset/event loss rows: **18,492**.
- Aggregate 10k toy ground-up loss: **EUR 285,494,000**; toy AAL **EUR 28,549.40**.
- AEP 99%/99.5%: **EUR 342,500 / EUR 366,250**; OEP 99%/99.5%: **EUR 333,750 / EUR 351,250**.
- Total wind/flood toy loss: **EUR 188,021,000 / EUR 97,473,000**.
- Maximum single toy annual loss: **EUR 638,750**.

| Ordered series | Returned exact MD5 |
| --- | --- |
| 10,000 year gross/max/count | `6aebdda0c542f06a882ec16a4fcaa667` |
| 1,541 peril/year events | `e0b6b2414c0a12459c47785a7de53777` |
| 18,492 asset/event losses | `8cba885a6e1aab7d43e2fe1087fe0d95` |
| 1,541 events and synthetic intensities | `2f11da6a6e1fb752cc410f50bfeffbc6` |

All values match the original documented 2026-11-01 independent Python/SQL
oracle. MD5 is a deterministic **parity check**, not source authentication.
These values cannot be interpreted as physical event recurrence,
geographically calibrated hazard, real-insurer exposure, policy/ceded loss,
retrocession, Solvency II capital or an operational model.

## Still blocked: exact native CAT-to-NextGen acceptance

A clean Git checkout on pinned `OpenCatastrophe` and `NextGen` HEADs is
required to **execute**, not merely inspect, the original synthetic producer,
native insured-loss consumer and negative mutation suite on 10,000 worlds.
The shared source receipts must be independently checked across both
components; the two GitHub PRs do not become a working financial pipeline
by reproducing SQL alone. Model PR #14 and its stacked audit-export PR #18
remain subject to that execution gate; private GitHub Actions are not
available and the remote Mac worker was not accessible at this checkpoint.

**Merge policy:** Keep this research PR in Draft until the latest-head
repository CI and separately reviewed native integration evidence exist.
No automatic Neon write, model admission, provider-rights approval, asset
download or CI bypass is authorized by this research receipt.

## Independent current-branch replay, 2026-11-08 (read-only, no mutations)

The same **exact original Git SQL blobs** were retrieved from original research Draft #1081 and separately executed against only the existing `insurance-risk-core / insurance / validation-schema-20261031` branch `br-summer-sky-bawujqu8`. **Not** the production/main Neon database; no SQL writes or source-row imports.

| Invariant / deterministic toy output | Observed 2026-11-08 |
| --- | ---: |
| Invented asset count / invented proxy value | 12 / EUR 3,150,000 |
| Artificial independent Bernoulli years | 10,000 |
| Fictional wind/flood events | 1,008 / 533 |
| Total invented GUL | EUR 285,494,000 |
| Invented AAL | EUR 28,549.40 |
| Artificial annual AEP 99% / 99.5% | EUR 342,500 / EUR 366,250 |
| Artificial one-event OEP 99% / 99.5% | EUR 333,750 / EUR 351,250 |
| Year rows / event rows / event-asset rows | 10,000 / 1,541 / 18,492 |

The second source-SQL query repeated **all four** exact row-series receipts:
- annual: `6aebdda0c542f06a882ec16a4fcaa667`
- event: `e0b6b2414c0a12459c47785a7de53777`
- event-asset: `8cba885a6e1aab7d43e2fe1087fe0d95`
- event-intensity: `2f11da6a6e1fb752cc410f50bfeffbc6`.

All four MD5 values above match the pinned historic research receipts exactly. This second independent replay proves exact read-only **SQL research fixture reproducibility**, **not** a native OpenCatastrophe/NextGen/Oasis run, insurer TIV, hazard, vulnerability, ceded treaty, source rights, annual physical CAT frequency calibration or any observed portfolio loss. The source model remains entirely fictional, fixed 12-unit, two-peril independent event smoke.
