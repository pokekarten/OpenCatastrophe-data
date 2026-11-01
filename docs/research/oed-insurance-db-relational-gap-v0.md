<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# OED 5.0 relational DB gap and next schema cut (2026-11-01)

**State:** read-only Neon schema audit and **proposed** next database design; no DDL applied to production or the validation branch. This is not a claim that actual insurer-level policy/exposure records exist.

## Live database anchor

Neon project `insurance-risk-core`, PostgreSQL 17, database `insurance`.
On production `main`, `exposure.portfolio`, `exposure.portfolio_version`, `exposure.exposure_unit`, `insurance.contract`, and `insurance.portfolio_contract` exist. Read-only live counts: **0** production portfolio rows, **0** exposure-unit rows, and **0** treaty/contract rows. The isolated `validation-schema-20261031` branch has **1** synthetic portfolio, **12** invented exposure units, **1** invented CAT-XL contract, and **1** portfolio-contract association. The synthetic OED bridge currently invents an account, policy, peril scope, and 100%-Building TIV allocation **only at CSV projection time**. Neither DB branch has an authoritative normalized primary insurance account/policy layer.

The existing `insurance.contract` table covers treaty concepts such as `cat_xl`, `quota_share`, and `retrocession`. **Do not repurpose it as the primary-policy table**; treaty rights and financial loss ordering differ from property-policy limits and deductibles.

## Minimum additive target (separate follow-on migration, validation branch first)

1. `insurance.account_v1`: internal account ID, `portfolio_version_id`, scoped `account_key`, currency, synthetic/observed status, `source_key`, valid-as-of date. Stable composite uniqueness on `(portfolio_version_id, account_key)`. An external insurance customer name is *not* required and must never be committed to this public repository.
2. `insurance.policy_v1`: scoped `account_id`, `portfolio_version_id`, internal `policy_key`, effective/expiry dates, explicit **OED 5.0** policy peril codes, status, provenance, and versioned policy financial terms. A policy is not inferred from a company registration, building footprint, aggregate report, or the current treaty table.
3. `insurance.policy_location_v1`: insured `policy_id` to physical `exposure.exposure_unit.unit_id` links. The database must enforce **same portfolio version on both sides** (composite foreign keys or an equivalent invariant). This allows multiple policies per building without inventing a unique insurer for any existing footprint.
4. `insurance.policy_tiv_component_v1`: link to `policy_location_id`, enum component `building / contents / bi / other`, nonnegative monetary amount, ISO currency, valuation/coverage date, observed-versus-modelled-versus-synthetic value basis, source/artifact identity, and an explicit uncertainty/attribution field where needed. Permit the distinction between **unknown / unreported** (`NULL`) and **verified zero**; never silently fill missing values with zero.

**Keep a distinct physical asset/reconstruction valuation** (replacement-cost model, survey, building area, material assumptions) separate from the *insured* sums above. `exposure.exposure_unit.insured_value` is presently only one scalar with a free-text `value_basis`; it cannot carry an auditable per-policy, per-coverage TIV breakdown by itself. A reported company-level aggregate or modeled building value must not be disaggregated into invented actual policies.

## Minimum migration acceptance tests

- Run on an **explicitly identified isolated validation branch**. Never apply the proposal directly to production `main`.
- Enforce composite cross-version FK integrity; reject links across portfolio versions and duplicate policy-location-component identities.
- Enforce ISO currency, nonnegative finite monetary values, valid dates, synthetically declared OED peril mappings, and exact TIV sum conservation.
- Reject `observed_insured` unless original provider/asset identity, licence/admission and audit evidence exist. A `landscape` candidate or metadata-only manifest does not meet this gate.
- Keep `reins_info` / `reins_scope` a **separate export stage**. The current invented CAT-XL treaty lacks complete financial semantics (reinstatement premium and event ordering); no valid reinsurance contract export follows from an OED 5.0 account/location pass.
- Use the official pinned ODS Tools validation in CI and an independently checked consumer read under a pinned compatible OasisLMF release; a format-valid CSV alone does not produce a CAT simulation.

## Source prioritization

First: preserve the existing 12-row wholly synthetic fixture and **test** normalized account/policy/TIV inserts, with no claim of real insurance coverage. Second: obtain exact legal/scientific admission and reproducible building/valuation inputs for one named, bounded regional exposure pilot. EUBUCCO/Microsoft/Overture/official cadastres inform **physical building geometry**; EFEHR/METEOR modelled values are **proxies** with their own rights and vintage limits; EIOPA/Florida/Texas aggregates provide *aggregate* calibration checks, not property-level insurer policies. No external source is auto-promoted by an OED projection.

**Scope gate:** this note proposes the next schema cut but does **not** alter Neon schema or claim permission to use externally sourced exposure. A separate reviewed DB migration and isolated synthetic integration proof are needed.
