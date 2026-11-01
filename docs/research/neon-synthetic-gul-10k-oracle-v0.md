<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Neon synthetic 10,000-year ground-up loss oracle (research v0)

**Status:** synthetic-only, **NOT** native OpenCatastrophe/NextGen/Oasis/OpenQuake, **NOT** scientifically calibrated. No policy loss, CAT-XL/Retro, Solvency II or actual insurer loss may be inferred.

## Live read-only source and scientific limits

- Database: Neon project `insurance-risk-core`, database `insurance`, **isolated validation branch** `validation-schema-20261031` (`br-summer-sky-bawujqu8`), **never main**.
- Source portfolio `oc-synthetic-exposure-smoke-v0`: 12 wholly invented test exposure positions `SYNTH-01` through `SYNTH-12`, total made-up EUR 3,150,000. They are fictional insured-value fields repurposed as **toy replacement-cost proxies**, not real insured or physical replacement values. All geographic positions are arbitrary and all source rows are synthetic.
- The fictional policy has `policy_terms` without executable coverage/deductible rules. The CAT-XL smoke contract has loss ordering and reinstatement premium **unspecified**. It is not safe to calculate ceded/net loss from these records without additional declared contract assumptions.
- `research_runners/sql/neon_synthetic_gul_10k_v0.sql` is a **read-only SQL statement**. An asset count/ID/value fixture gate must match before it emits simulated worlds. Empty or malformed input is blocked. It writes no `model.simulation_run`, provider data or object storage.
- Each of 10,000 annual worlds has one hypothetical wind event (probability 26/256) and one hypothetical flood event (13/256), independently decided using PostgreSQL MD5 bytes. Conditional event intensity is `1 + second_byte % 5` and per-asset vulnerability multiplier is `1 + asset_hash_third_byte % 3`. Toy loss = invented value × intensity × multiplier / 100. **All frequencies, intensities and damage factors are invented.** Peril events are separate, not physically overlapping components of a true joint event.

## Verified Neon SQL outputs, 2026-11-01

| Metric | Value |
| --- | ---: |
| Simulated years / synthetic assets | 10,000 / 12 |
| Synthetic wind / flood events | 1,008 / 533 |
| Years with no event | 8,509 |
| Sum of all annual ground-up proxy losses | EUR 285,494,000 |
| Arithmetic average annual loss (toy AAL) | EUR 28,549.40 |
| Empirical AEP 99% / 99.5% quantiles | EUR 342,500 / 366,250 |
| Empirical OEP 99% / 99.5% quantiles | EUR 333,750 / 351,250 |
| Maximum simulated annual toy loss | EUR 638,750 |

The independent `tests/test_neon_synthetic_gul_10k_v0.py` was executed locally: **4/4 PASS**. It replays the 10,000 worlds without database access, checks numeric parity with the live SQL output, rejects changed synthetic exposure amounts, rejects any non-synthetic input flag, and checks sum/event conservation. Local CPython proves only this bounded mathematical equivalence. GitHub CI/full `scripts/check_all.py` and native producer/consumer suite are not claimed as executed here.

## Next required tests and admission

1. In an exact-HEAD checkout execute the native OpenCatastrophe synthetic producer → existing NextGen importer → 10,000-world financial prototype, with event/world/asset source hashes, explicit simulated terms and no double-counted multi-peril event components.
2. Perform provider-authenticated OpenQuake or Oasis hazard, exposure, vulnerability and asset-by-event exports, separately reviewed under existing rights/scientific admission controls. An accepted model needs an actual model version, calibrated physical event catalogue and source-reproducible run evidence.
3. Supply original coverage, attachment, limit, occurrence/hours, reinstatement and retro terms **independently** of exposure values before producing insured/ceded/net or capital results.
4. Only after these prerequisites, create registered `model.simulation_run` and loss artifacts on a separately reviewed branch. Do not promote synthetic toy outcomes to production.
