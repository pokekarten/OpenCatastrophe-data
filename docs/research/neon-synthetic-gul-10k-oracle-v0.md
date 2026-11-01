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

## 2026-11-01 exact-branch follow-up: CI and fixture-gate hardening

The initial PR-head GitHub workflow run 41352241351 failed **only** because the newly authored SQL and Python test lacked SPDX headers. In the Python 3.11 run, the repository executed **4,620 tests: OK (298 skipped)** before its own licence metadata gate rejected the two files. Both files now have Apache-2.0 SPDX headers; the later CI check must be judged against the **latest** PR head, not that obsolete run.

The original `gate HAVING` silently returned no annual rows when the fixture was missing. Replaced with an identity-specific expected table (all 12 expected `external_unit_id` → EUR values), FULL JOIN mismatch count and a **division-by-zero fail-closed guard**. This is intentionally a SQL error, not an empty/NULL statistical receipt.

Live **read-only PostgreSQL 17** validation on explicit Neon branch `br-summer-sky-bawujqu8`:
- Positive original database SQL: unchanged 10,000-world results and all numeric outputs.
- Positive all-12 synthetic VALUES fixture: 1 valid gate.
- Negative missing 12th location: rejected `division by zero`.
- Negative no locations: rejected `division by zero`.
- Negative same aggregate EUR 3,150,000 with two asset identities' values swapped: rejected `division by zero`.

Latest independent Python suite: **7/7 PASS**, including checks for fixture-value swaps, empty/missing synthetic data and SQL guard source structure. Both local tested files were compared using Git blob hashes with the exact GitHub versions. This is **not** a signed native CAT receipt or a live Neon mutation/rollback test; all queries are read-only.

## Next required tests and admission

1. In an exact-HEAD checkout execute the native OpenCatastrophe synthetic producer → existing NextGen importer → 10,000-world financial prototype, with event/world/asset source hashes, explicit simulated terms and no double-counted multi-peril event components.
2. Perform provider-authenticated OpenQuake or Oasis hazard, exposure, vulnerability and asset-by-event exports, separately reviewed under existing rights/scientific admission controls. An accepted model needs an actual model version, calibrated physical event catalogue and source-reproducible run evidence.
3. Supply original coverage, attachment, limit, occurrence/hours, reinstatement and retro terms **independently** of exposure values before producing insured/ceded/net or capital results.
4. Only after these prerequisites, create registered `model.simulation_run` and loss artifacts on a separately reviewed branch. Do not promote synthetic toy outcomes to production.

## 2026-11-01: same-source identity gate for the synthetic Oasis OED fixture

The initial 10k SQL accepted 12 synthetic asset IDs and exact EUR 3.15m,
but did **not** pin the same portfolio-version identity and valuation metadata
used by the separate Oasis OED snapshot in PR #1070. A different version or
non-EUR value with identical numeric EUR amount could otherwise be mistaken for
the intended proxy input. This is a **research-fixture provenance** defect,
not evidence that a real portfolio was present.

The guarded query now additionally requires:
- Exactly one version for the named synthetic portfolio, the original
  `version_label=v0`, seed `20261101`, generation method, and no source key.
- Explicit `synthetic=true`, `real_insurer=false`,
  `model_input_approved=false`, and `external_source_rows_used=0`.
- Exactly 12 **total** exposure-unit rows in that version, not just 12
  filtered valid ones; each of the 12 IDs must have its exact amount,
  synthetic assumption status, EUR currency, the original invented-value
  basis, and a non-null EPSG:4326 location.
- The existing fail-closed division-by-zero condition; invalid input must
  raise an error, not silently emit NULL or zero loss quantiles.

**Direct live read-only Neon PG17 validation on the isolated branch
`br-summer-sky-bawujqu8`, database `insurance`:**
- Positive amended SQL: PASS, unchanged exact 10,000-world, 12-asset,
  EUR 3.15m result; loss total EUR 285,494,000, AAL EUR 28,549.40,
  99.5% AEP EUR 366,250, wind/flood 1,008/533 events.
- Negative swapped `pv.seed=20261102`: expected `division by zero` PASS.
- Negative forced `insured_value_currency=USD`: expected `division by zero` PASS.
- Two additional offline SQL structural regression tests added to ensure the
  source-version, raw-unit count and valuation guards stay pinned.

**Scientific nonclaim:** This is still a deliberately invented GUL proxy with
fictional annual event frequencies, intensities, locations and amounts.
A real covered policy, Oasis financial module, CAT-XL, retro, calibrated
hazard-vulnerability model and genuine 10k NextGen run remain absent.
No source or database writes were made.

## 2026-11-02: preserve exact synthetic exposure geometry and taxonomy

The OED/GUL identity comparison in this branch previously pinned version,
value, currency, unit count and SRID, but not the actual `location` coordinates
or the selected building taxonomy. A valid but shifted coordinate or changed
occupancy/construction code could therefore have produced the **same**
10,000-year numerical toy loss output while masquerading as the original
fixture. This is a research-lineage defect, not evidence of a real insurer risk.

The read-only SQL now checks:
- the exact fictional portfolio country, ordered peril/LoB scope, as-of
  date, no-real-buildings metadata and fixed version;
- the original `SYNTH-01..12` point grid in EPSG:4326 at the binary
  PostGIS EWKB level (not only non-null point geometry / SRID);
- each location's region/country, occupancy, construction and
  single-building count against the canonical synthetic SQL recipe.

All checks remain within the original 12-unit unfiltered fixture and the
fail-closed division-by-zero gate; no raw source, real exposure or model
admission is introduced.

**Actual read-only Neon validation** on the explicit isolated branch
`br-summer-sky-bawujqu8`, DB `insurance`:
- Positive full 10,000-year SQL still returned exactly 12 assets,
  EUR 3,150,000 invented values, 1,541 invented events and
  EUR 285,494,000 aggregate invented annual losses (AAL EUR 28,549.40).
- Negative **changed longitude by 0.01 degrees**: rejected with
  `division by zero`.
- Negative **as-of date 2026-11-02**: rejected with `division by zero`.
- Negative **changed expected occupancy code**: rejected with
  `division by zero`.

These negative probes altered only the **read-only SQL's expected fixture**,
not Neon data. The static offline test also asserts the new spatial/taxonomy
gates are present. Exact-head GitHub CI must still independently pass before
integration. This is deliberately not a native OpenCatastrophe/NextGen/Oasis/
OpenQuake model or production model-input qualification.
